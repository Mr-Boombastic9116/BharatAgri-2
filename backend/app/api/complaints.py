from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
import uuid

from backend.app.core.database import get_db
from backend.app.core.deps import get_current_user, require_role
from backend.app.models.complaint import Complaint, ComplaintMessage, ComplaintStatusHistory
from backend.app.models.audit import AuditLog

router = APIRouter(prefix="/api/complaints", tags=["Grievance & Complaints"])

class ComplaintCreate(BaseModel):
    centre_id: str
    category: str
    priority: str = "MEDIUM"
    subject: str
    description: str

class ComplaintMessageCreate(BaseModel):
    message: str

class ComplaintStatusUpdate(BaseModel):
    status: str
    resolution: Optional[str] = None
    notes: Optional[str] = None

@router.get("")
def list_complaints(
    user_id: Optional[str] = Query(None),
    centre_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    query = db.query(Complaint)
    role = current_user.get("role")

    # If farmer or agent, restrict to their own complaints unless government/centre
    if role in ("FARMER", "AGENT"):
        query = query.filter(Complaint.user_id == current_user.get("user_id"))
    elif role == "PROCUREMENT_CENTRE":
        # Can view complaints for their centre
        query = query.filter(Complaint.centre_id == current_user.get("user_id"))
    else:
        # Government can filter by anything
        if user_id:
            query = query.filter(Complaint.user_id == user_id)
        if centre_id:
            query = query.filter(Complaint.centre_id == centre_id)

    if status:
        query = query.filter(Complaint.status == status)
    if category:
        query = query.filter(Complaint.category == category)

    complaints = query.order_by(Complaint.created_at.desc()).all()
    return {
        "success": True,
        "count": len(complaints),
        "data": [
            {
                "id": c.id,
                "complaint_code": c.complaint_code,
                "user_id": c.user_id,
                "user_role": c.user_role,
                "centre_id": c.centre_id,
                "category": c.category,
                "priority": c.priority,
                "subject": c.subject,
                "description": c.description,
                "status": c.status,
                "resolution": c.resolution,
                "created_at": c.created_at.strftime("%d-%m-%Y %H:%M") if c.created_at else None,
                "resolved_at": c.resolved_at.strftime("%d-%m-%Y %H:%M") if c.resolved_at else None
            }
            for c in complaints
        ]
    }

@router.post("")
def file_complaint(
    payload: ComplaintCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    code = f"CMP-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    complaint = Complaint(
        complaint_code=code,
        user_id=current_user.get("user_id", "ANONYMOUS"),
        user_role=current_user.get("role", "FARMER"),
        centre_id=payload.centre_id,
        category=payload.category,
        priority=payload.priority,
        subject=payload.subject,
        description=payload.description,
        status="OPEN"
    )
    db.add(complaint)
    db.flush()

    # Initial message
    init_msg = ComplaintMessage(
        complaint_id=complaint.id,
        sender_id=current_user.get("user_id", "SYSTEM"),
        sender_role=current_user.get("role", "FARMER"),
        message=payload.description
    )
    db.add(init_msg)

    # Initial history
    history = ComplaintStatusHistory(
        complaint_id=complaint.id,
        old_status=None,
        new_status="OPEN",
        changed_by=current_user.get("user_id", "SYSTEM"),
        notes="Complaint submitted"
    )
    db.add(history)

    audit = AuditLog(
        user_id=current_user.get("user_id", "SYSTEM"),
        action="FILE_COMPLAINT",
        entity="complaints",
        entity_id=str(complaint.id),
        new_value=f"Code: {complaint.complaint_code}, Category: {complaint.category}"
    )
    db.add(audit)
    db.commit()
    db.refresh(complaint)

    return {
        "success": True,
        "message": "Complaint filed successfully",
        "data": {
            "id": complaint.id,
            "complaint_code": complaint.complaint_code,
            "status": complaint.status
        }
    }

@router.get("/{complaint_id}")
def get_complaint(
    complaint_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail={"code": "COMPLAINT_NOT_FOUND", "message": "Complaint not found"})

    messages = db.query(ComplaintMessage).filter(ComplaintMessage.complaint_id == complaint_id).order_by(ComplaintMessage.created_at.asc()).all()
    history = db.query(ComplaintStatusHistory).filter(ComplaintStatusHistory.complaint_id == complaint_id).order_by(ComplaintStatusHistory.created_at.asc()).all()

    return {
        "success": True,
        "data": {
            "id": complaint.id,
            "complaint_code": complaint.complaint_code,
            "user_id": complaint.user_id,
            "user_role": complaint.user_role,
            "centre_id": complaint.centre_id,
            "category": complaint.category,
            "priority": complaint.priority,
            "subject": complaint.subject,
            "description": complaint.description,
            "status": complaint.status,
            "resolution": complaint.resolution,
            "created_at": complaint.created_at.strftime("%d-%m-%Y %H:%M") if complaint.created_at else None,
            "resolved_at": complaint.resolved_at.strftime("%d-%m-%Y %H:%M") if complaint.resolved_at else None,
            "messages": [
                {
                    "id": m.id,
                    "sender_id": m.sender_id,
                    "sender_role": m.sender_role,
                    "message": m.message,
                    "created_at": m.created_at.strftime("%d-%m-%Y %H:%M") if m.created_at else None
                }
                for m in messages
            ],
            "history": [
                {
                    "old_status": h.old_status,
                    "new_status": h.new_status,
                    "changed_by": h.changed_by,
                    "notes": h.notes,
                    "created_at": h.created_at.strftime("%d-%m-%Y %H:%M") if h.created_at else None
                }
                for h in history
            ]
        }
    }

@router.post("/{complaint_id}/messages")
def add_complaint_message(
    complaint_id: int,
    payload: ComplaintMessageCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail={"code": "COMPLAINT_NOT_FOUND", "message": "Complaint not found"})

    msg = ComplaintMessage(
        complaint_id=complaint.id,
        sender_id=current_user.get("user_id", "SYSTEM"),
        sender_role=current_user.get("role", "FARMER"),
        message=payload.message
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    return {
        "success": True,
        "message": "Message sent",
        "data": {
            "id": msg.id,
            "sender_id": msg.sender_id,
            "message": msg.message,
            "created_at": msg.created_at.strftime("%d-%m-%Y %H:%M") if msg.created_at else None
        }
    }

@router.put("/{complaint_id}/status")
def update_complaint_status(
    complaint_id: int,
    payload: ComplaintStatusUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("PROCUREMENT_CENTRE", "GOVERNMENT"))
):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail={"code": "COMPLAINT_NOT_FOUND", "message": "Complaint not found"})

    old_status = complaint.status
    complaint.status = payload.status
    if payload.resolution:
        complaint.resolution = payload.resolution
    if payload.status in ("RESOLVED", "CLOSED"):
        complaint.resolved_at = datetime.now()

    history = ComplaintStatusHistory(
        complaint_id=complaint.id,
        old_status=old_status,
        new_status=payload.status,
        changed_by=current_user.get("user_id", "SYSTEM"),
        notes=payload.notes or f"Status changed to {payload.status}"
    )
    db.add(history)

    audit = AuditLog(
        user_id=current_user.get("user_id", "SYSTEM"),
        action="UPDATE_COMPLAINT_STATUS",
        entity="complaints",
        entity_id=str(complaint.id),
        old_value=old_status,
        new_value=f"New status: {payload.status}, Res: {payload.resolution or 'N/A'}"
    )
    db.add(audit)
    db.commit()

    return {
        "success": True,
        "message": "Complaint status updated",
        "data": {
            "id": complaint.id,
            "status": complaint.status,
            "resolution": complaint.resolution
        }
    }
