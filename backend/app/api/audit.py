from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from backend.app.core.database import get_db
from backend.app.core.deps import get_current_user, require_role
from backend.app.models.audit import AuditLog

router = APIRouter(prefix="/api/audit", tags=["Audit Logs"])

@router.get("")
def list_audit_logs(
    user_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    entity: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("GOVERNMENT", "PROCUREMENT_CENTRE"))
):
    query = db.query(AuditLog)
    
    # If centre role, only see audit logs related to centre or actions by centre
    if current_user.get("role") == "PROCUREMENT_CENTRE":
        query = query.filter((AuditLog.user_id == current_user.get("user_id")) | (AuditLog.entity_id == current_user.get("user_id")))
    else:
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if entity:
            query = query.filter(AuditLog.entity == entity)

    if action:
        query = query.filter(AuditLog.action == action)

    total = query.count()
    logs = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()

    return {
        "success": True,
        "total": total,
        "offset": offset,
        "limit": limit,
        "data": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "action": log.action,
                "entity": log.entity,
                "entity_id": log.entity_id,
                "old_value": log.old_value,
                "new_value": log.new_value,
                "ip_address": log.ip_address,
                "created_at": log.created_at.strftime("%d-%m-%Y %H:%M:%S") if log.created_at else None
            }
            for log in logs
        ]
    }
