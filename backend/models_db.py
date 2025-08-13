from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, Date
from sqlalchemy.orm import relationship

from .database import Base

# Note: We are creating new SQLAlchemy models here.
# These are distinct from the Pydantic models in the root `models.py`,
# but they correspond to them. Pydantic models are used for API data validation,
# while these SQLAlchemy models define the database schema.

class TransitAuthority(Base):
    __tablename__ = "transit_authorities"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, unique=True)
    city = Column(String)
    address = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    users = relationship("User", back_populates="authority")
    api_keys = relationship("ApiKey", back_populates="authority")
    subscriptions = relationship("Subscription", back_populates="authority")


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    entidad_id = Column(String, ForeignKey("transit_authorities.id"), unique=True) # Each entity has one set of keys
    provider = Column(String) # e.g., "openai", "google"
    encrypted_key = Column(String)

    authority = relationship("TransitAuthority", back_populates="api_keys")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True, nullable=True)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    role = Column(String)
    entidad_id = Column(String, ForeignKey("transit_authorities.id"), nullable=True)

    authority = relationship("TransitAuthority", back_populates="users")
    notification_preferences = relationship(
        "NotificationPreference",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    fines = relationship("Fine", back_populates="user")
    appointments = relationship("Appointment", back_populates="user")
    documents = relationship("UserDocument", back_populates="user")


class Fine(Base):
    __tablename__ = "fines"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    entidad_id = Column(String, ForeignKey("transit_authorities.id"))

    infraction_code = Column(String, index=True)
    placa = Column(String, index=True)
    date = Column(Date)
    status = Column(String, default="Pendiente")
    tipo = Column(String, default="Económico")

    # Geolocation of the fine
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    user = relationship("User", back_populates="fines")


class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    placa = Column(String, unique=True, index=True)
    marca = Column(String)
    modelo = Column(String)
    ano = Column(Integer)
    tipo = Column(String)

    propietario_id = Column(Integer, ForeignKey("users.id"))
    entidad_id = Column(String, ForeignKey("transit_authorities.id"))

    # Fields for expiration tracking
    soat_vence = Column(Date, nullable=True)
    tecno_vence = Column(Date, nullable=True)

    propietario = relationship("User")


# We would continue to define tables for Vehicle, Fine, Course, etc.
# For this phase, starting with User and TransitAuthority is sufficient to establish the pattern.

from sqlalchemy import DateTime
from sqlalchemy.sql import func

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    entidad_id = Column(String, ForeignKey("transit_authorities.id"))
    plan_name = Column(String, nullable=False) # e.g., "Profesional Mensual", "Profesional Anual"
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(String, default="active") # active, expired, cancelled

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    authority = relationship("TransitAuthority", back_populates="subscriptions")


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    on_new_fine = Column(Boolean, default=True)
    on_document_expiration = Column(Boolean, default=True)
    on_appointment_reminder = Column(Boolean, default=True)

    user = relationship("User", back_populates="notification_preferences")


class Procedure(Base):
    __tablename__ = "procedures"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)
    duration_minutes = Column(Integer, default=30)
    is_active = Column(Boolean, default=True)


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    procedure_id = Column(Integer, ForeignKey("procedures.id"), nullable=False)
    appointment_time = Column(DateTime(timezone=True), nullable=False)
    status = Column(String, default="Scheduled") # Scheduled, Completed, Cancelled

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="appointments")
    procedure = relationship("Procedure")


from sqlalchemy.dialects.sqlite import JSON

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Nullable for system actions
    username = Column(String, index=True) # Denormalized for easy lookup
    action = Column(String, index=True) # e.g., "USER_LOGIN", "FINE_ISSUED"
    details = Column(JSON, nullable=True) # e.g., {"fine_id": 123, "target_user": "citizen1"}
