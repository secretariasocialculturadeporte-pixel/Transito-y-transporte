from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import date

from .... import crud, models_db, notifications
from ..auth import get_current_user, get_db

router = APIRouter()

# --- Pydantic Schemas for Fines ---

class FineCreate(BaseModel):
    target_username: str
    infraction_code: str
    placa: str
    date: date
    tipo: str

# --- Fine Endpoints ---

@router.post("/", status_code=status.HTTP_201_CREATED, summary="Issue a new fine")
def issue_fine(
    fine_data: FineCreate,
    db: Session = Depends(get_db),
    current_user: models_db.User = Depends(get_current_user)
):
    """
    Allows an admin to issue a new fine to a citizen.
    After creating the fine, it triggers a notification if the user has opted in.
    """
    # Authorization: Only admins can issue fines
    if current_user.role not in ["Admin Municipal", "SuperAdmin", "Técnico"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to issue fines."
        )

    # Find the target user to issue the fine to
    target_user = crud.get_user_by_username(db, username=fine_data.target_username)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{fine_data.target_username}' not found."
        )

    # Create the fine in the database
    db_fine = crud.create_fine(
        db=db,
        fine_data=fine_data.dict(),
        user_id=target_user.id,
        entidad_id=current_user.entidad_id # The fine is issued by the admin's entity
    )

    # --- Notification Trigger ---
    # Check user's notification preferences
    prefs = crud.get_or_create_notification_preferences(db, user_id=target_user.id)
    if prefs.on_new_fine and target_user.email:
        print(f"Triggering new fine notification for user {target_user.username}")
        notifications.send_new_fine_notification(
            user_email=target_user.email,
            fine_details=fine_data.dict()
        )

    return {"message": "Fine issued successfully", "fine_id": db_fine.id}
