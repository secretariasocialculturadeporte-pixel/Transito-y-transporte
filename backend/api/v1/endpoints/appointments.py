from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .... import crud, models_db, schemas
from ..auth import get_current_user, get_db

router = APIRouter()

# --- Endpoints for Procedures (Appointment Types) ---

@router.post("/procedures/", response_model=schemas.Procedure, status_code=status.HTTP_201_CREATED, summary="Create a new procedure type")
def create_procedure(
    procedure: schemas.ProcedureCreate,
    db: Session = Depends(get_db),
    current_user: models_db.User = Depends(get_current_user)
):
    """
    Admin-only endpoint to create a new type of procedure that citizens can book.
    """
    if current_user.role not in ["Admin Municipal", "SuperAdmin"]:
        raise HTTPException(status_code=403, detail="Not authorized to create procedures.")

    return crud.create_procedure(db=db, procedure=procedure)

@router.get("/procedures/", response_model=List[schemas.Procedure], summary="List all available procedures")
def list_procedures(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Lists all active, bookable procedures for citizens.
    """
    procedures = crud.get_procedures(db, skip=skip, limit=limit)
    return procedures

# --- Endpoints for Appointments ---

@router.post("/appointments/", response_model=schemas.Appointment, status_code=status.HTTP_201_CREATED, summary="Book a new appointment")
def book_appointment(
    appointment: schemas.AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: models_db.User = Depends(get_current_user)
):
    """
    Allows the current user to book a new appointment for a specific procedure.

    A real implementation would include complex availability/slot checking logic here.
    """
    # Basic validation: Check if procedure exists
    procedure = db.query(models_db.Procedure).filter(models_db.Procedure.id == appointment.procedure_id).first()
    if not procedure or not procedure.is_active:
        raise HTTPException(status_code=404, detail="Procedure not found or is not active.")

    db_appointment = crud.create_appointment(db=db, user_id=current_user.id, appointment=appointment)

    # --- Audit Log ---
    crud.create_audit_log(
        db=db,
        action="APPOINTMENT_BOOKED",
        user_id=current_user.id,
        username=current_user.username,
        details={
            "appointment_id": db_appointment.id,
            "procedure_id": db_appointment.procedure_id,
            "appointment_time": db_appointment.appointment_time.isoformat()
        }
    )
    # -----------------

    return db_appointment

@router.get("/appointments/me", response_model=List[schemas.Appointment], summary="Get my appointments")
def get_my_appointments(
    db: Session = Depends(get_db),
    current_user: models_db.User = Depends(get_current_user)
):
    """
    Retrieves a list of all appointments booked by the current user.
    """
    return crud.get_appointments_by_user(db=db, user_id=current_user.id)
