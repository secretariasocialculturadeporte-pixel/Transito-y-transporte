from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date, timedelta

from .... import crud, models_db, notifications
from ..auth import get_current_user, get_db

router = APIRouter()

@router.post("/check-expirations", summary="Check for and notify about expiring documents")
def check_document_expirations(
    db: Session = Depends(get_db),
    current_user: models_db.User = Depends(get_current_user)
):
    """
    An administrative task that scans for vehicles with documents (SOAT, Tecnomecánica)
    expiring within the next 30 days and sends notifications to the owners.

    In a real production app, this would be a scheduled background job (e.g., a cron job)
    rather than a manually triggered API endpoint.
    """
    # Authorization: Only admins can run this task
    if current_user.role not in ["Admin Municipal", "SuperAdmin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to run this task."
        )

    today = date.today()
    reminder_threshold = today + timedelta(days=30)

    # Find vehicles with SOAT or Tecnomecánica expiring soon
    expiring_vehicles = db.query(models_db.Vehicle).filter(
        (models_db.Vehicle.soat_vence.isnot(None) & (models_db.Vehicle.soat_vence <= reminder_threshold)) |
        (models_db.Vehicle.tecno_vence.isnot(None) & (models_db.Vehicle.tecno_vence <= reminder_threshold))
    ).all()

    notifications_sent = 0
    for vehicle in expiring_vehicles:
        owner = vehicle.propietario
        if not owner or not owner.email:
            continue

        # Check owner's notification preferences
        prefs = crud.get_or_create_notification_preferences(db, user_id=owner.id)
        if not prefs.on_document_expiration:
            continue

        # Simple logic to check which document is expiring
        if vehicle.soat_vence and vehicle.soat_vence <= reminder_threshold:
            subject = f"Alerta de Vencimiento: SOAT del vehículo {vehicle.placa}"
            body = f"Hola {owner.full_name},\n\nLe informamos que el SOAT de su vehículo con placa {vehicle.placa} está próximo a vencer el {vehicle.soat_vence}.\n\nAtentamente,\nPortal de Movilidad."
            notifications.send_email(to=owner.email, subject=subject, body=body)
            notifications_sent += 1

        if vehicle.tecno_vence and vehicle.tecno_vence <= reminder_threshold:
            subject = f"Alerta de Vencimiento: Revisión Tecnomecánica del vehículo {vehicle.placa}"
            body = f"Hola {owner.full_name},\n\nLe informamos que la Revisión Tecnomecánica de su vehículo con placa {vehicle.placa} está próxima a vencer el {vehicle.tecno_vence}.\n\nAtentamente,\nPortal de Movilidad."
            notifications.send_email(to=owner.email, subject=subject, body=body)
            notifications_sent += 1

    return {
        "message": "Expiration check completed.",
        "vehicles_found": len(expiring_vehicles),
        "notifications_sent": notifications_sent
    }
