from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .... import crud, models_db, schemas
from ..auth import get_current_user, get_db

router = APIRouter()

@router.get(
    "/me/notification-preferences",
    response_model=schemas.NotificationPreference,
    summary="Get current user's notification preferences"
)
def get_my_notification_preferences(
    db: Session = Depends(get_db),
    current_user: models_db.User = Depends(get_current_user)
):
    """
    Retrieves the notification preferences for the currently authenticated user.
    If no preferences exist, default ones will be created and returned.
    """
    prefs = crud.get_or_create_notification_preferences(db, user_id=current_user.id)
    return prefs

@router.put(
    "/me/notification-preferences",
    response_model=schemas.NotificationPreference,
    summary="Update current user's notification preferences"
)
def update_my_notification_preferences(
    prefs_data: schemas.NotificationPreferenceUpdate,
    db: Session = Depends(get_db),
    current_user: models_db.User = Depends(get_current_user)
):
    """
    Updates one or more notification preferences for the currently authenticated user.
    """
    prefs = crud.update_notification_preferences(db, user_id=current_user.id, prefs_data=prefs_data)

    # --- Audit Log ---
    crud.create_audit_log(
        db=db,
        action="NOTIFICATION_PREFERENCES_UPDATED",
        user_id=current_user.id,
        username=current_user.username,
        details=prefs_data.dict()
    )
    # -----------------

    return prefs
