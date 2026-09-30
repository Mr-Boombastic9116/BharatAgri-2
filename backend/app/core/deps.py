from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.core.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

def get_current_user_optional(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        return None
    user_id = payload["sub"]
    # Query user directly from DB
    from backend.app.models.user import User
    user = db.query(User).filter(User.user_id == user_id).first()
    return user

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided."
        )
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token."
        )
    user_id = payload["sub"]
    from backend.app.models.user import User
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Authenticated user no longer exists."
        )
    return user

def require_role(*allowed_roles: str):
    def role_checker(current_user = Depends(get_current_user)):
        user_role = (current_user.role or "").lower()
        allowed = set(r.lower() for r in allowed_roles)
        if "procurement_centre" in allowed or "centre" in allowed:
            allowed.add("centre")
            allowed.add("procurement_centre")
        if "government" in allowed or "admin" in allowed:
            allowed.add("government")
            allowed.add("admin")

        if user_role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. User role '{user_role}' is not authorized to access this resource."
            )
        return current_user
    return role_checker

