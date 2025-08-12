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
