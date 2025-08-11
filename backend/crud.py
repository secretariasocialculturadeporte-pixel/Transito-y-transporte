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
