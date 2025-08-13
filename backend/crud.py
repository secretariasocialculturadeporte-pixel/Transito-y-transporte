from sqlalchemy.orm import Session

from . import models_db, schemas, security

def get_user_by_username(db: Session, username: str):
    return db.query(models_db.User).filter(models_db.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = security.get_password_hash(user.password)
    db_user = models_db.User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password,
        role=user.role,
        entidad_id=user.entidad_id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# --- API Key CRUD ---

def get_api_key(db: Session, entidad_id: str):
    return db.query(models_db.ApiKey).filter(models_db.ApiKey.entidad_id == entidad_id).first()

def create_or_update_api_key(db: Session, entidad_id: str, provider: str, key: str):
    db_api_key = get_api_key(db, entidad_id=entidad_id)
    encrypted_key = security.encrypt_api_key(key)

    if db_api_key:
        db_api_key.provider = provider
        db_api_key.encrypted_key = encrypted_key
    else:
        db_api_key = models_db.ApiKey(
            entidad_id=entidad_id,
            provider=provider,
            encrypted_key=encrypted_key
        )
        db.add(db_api_key)

    db.commit()
    db.refresh(db_api_key)
    return db_api_key

# --- Subscription CRUD ---

from datetime import date

def create_subscription(db: Session, entidad_id: str, plan_name: str, start_date: date, end_date: date):
    """
    Creates a new subscription for a transit entity.
    If a subscription already exists, it could be updated or handled as per business logic.
    For now, we create a new one.
    """
    db_subscription = models_db.Subscription(
        entidad_id=entidad_id,
        plan_name=plan_name,
        start_date=start_date,
        end_date=end_date,
        status="active"
    )
    db.add(db_subscription)
    db.commit()
    db.refresh(db_subscription)
    return db_subscription

def get_subscription_by_entity(db: Session, entidad_id: str):
    """
    Retrieves the current active subscription for an entity.
    """
    return db.query(models_db.Subscription).filter(
        models_db.Subscription.entidad_id == entidad_id,
        models_db.Subscription.status == "active"
    ).first()

# --- Notification Preferences CRUD ---

def get_or_create_notification_preferences(db: Session, user_id: int) -> models_db.NotificationPreference:
    """
    Retrieves a user's notification preferences.
    If they don't exist, creates a default entry for them.
    """
    db_prefs = db.query(models_db.NotificationPreference).filter(models_db.NotificationPreference.user_id == user_id).first()

    if not db_prefs:
        db_prefs = models_db.NotificationPreference(user_id=user_id)
        db.add(db_prefs)
        db.commit()
        db.refresh(db_prefs)

    return db_prefs

def update_notification_preferences(db: Session, user_id: int, prefs_data: schemas.NotificationPreferenceUpdate):
    """
    Updates a user's notification preferences.
    """
    db_prefs = get_or_create_notification_preferences(db, user_id=user_id)

    # Update fields from the Pydantic model
    for var, value in vars(prefs_data).items():
        if value is not None:
            setattr(db_prefs, var, value)

    db.commit()
    db.refresh(db_prefs)
    return db_prefs

# --- Fine CRUD ---

def create_fine(db: Session, fine_data: dict, user_id: int, entidad_id: str):
    """
    Creates a new fine in the database.
    """
    db_fine = models_db.Fine(
        user_id=user_id,
        entidad_id=entidad_id,
        infraction_code=fine_data.get('infraction_code'),
        placa=fine_data.get('placa'),
        date=fine_data.get('date'),
        tipo=fine_data.get('tipo'),
        latitude=fine_data.get('latitude'),
        longitude=fine_data.get('longitude')
    )
    db.add(db_fine)
    db.commit()
    db.refresh(db_fine)
    return db_fine

def get_fine_by_id(db: Session, fine_id: int):
    """
    Retrieves a single fine by its ID.
    """
    return db.query(models_db.Fine).filter(models_db.Fine.id == fine_id).first()

def update_fine_status(db: Session, fine_id: int, new_status: str):
    """
    Updates the status of a specific fine.
    """
    db_fine = get_fine_by_id(db, fine_id=fine_id)
    if db_fine:
        db_fine.status = new_status
        db.commit()
        db.refresh(db_fine)
    return db_fine

# --- Procedure and Appointment CRUD ---

def get_procedures(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models_db.Procedure).filter(models_db.Procedure.is_active == True).offset(skip).limit(limit).all()

def create_procedure(db: Session, procedure: schemas.ProcedureCreate):
    db_procedure = models_db.Procedure(**procedure.dict())
    db.add(db_procedure)
    db.commit()
    db.refresh(db_procedure)
    return db_procedure

def get_appointments_by_user(db: Session, user_id: int):
    return db.query(models_db.Appointment).filter(models_db.Appointment.user_id == user_id).all()

def create_appointment(db: Session, user_id: int, appointment: schemas.AppointmentCreate):
    db_appointment = models_db.Appointment(
        **appointment.dict(),
        user_id=user_id
    )
    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)
    return db_appointment

# --- Audit Log CRUD ---

from typing import Optional, Dict, Any

def create_audit_log(
    db: Session,
    action: str,
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
):
    """
    Creates a new entry in the audit log.
    """
    db_log = models_db.AuditLog(
        user_id=user_id,
        username=username,
        action=action,
        details=details
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

def get_audit_logs(db: Session, skip: int = 0, limit: int = 100):
    """
    Retrieves a paginated list of audit logs, most recent first.
    """
    return db.query(models_db.AuditLog).order_by(models_db.AuditLog.timestamp.desc()).offset(skip).limit(limit).all()

# --- User Document CRUD ---

def create_user_document(db: Session, user_id: int, document_type: str, file_path: str):
    """
    Creates a new user document record in the database.
    """
    db_document = models_db.UserDocument(
        user_id=user_id,
        document_type=document_type,
        file_path=file_path
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document

def get_user_documents(db: Session, user_id: int):
    """
    Retrieves all documents for a specific user.
    """
    return db.query(models_db.UserDocument).filter(models_db.UserDocument.user_id == user_id).all()
