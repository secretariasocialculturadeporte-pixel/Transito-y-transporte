from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .... import crud, models_db, schemas
from ..auth import get_current_user, get_db

router = APIRouter()

@router.get("/audit-logs/", response_model=List[schemas.AuditLog], summary="Get audit log entries")
def get_audit_logs(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models_db.User = Depends(get_current_user)
):
    """
    Admin-only endpoint to retrieve a paginated list of audit log entries.
    """
    if current_user.role not in ["SuperAdmin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view audit logs."
        )

    logs = crud.get_audit_logs(db, skip=skip, limit=limit)
    return logs
