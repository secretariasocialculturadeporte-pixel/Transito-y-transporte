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


# We would continue to define tables for Vehicle, Fine, Course, etc.
# For this phase, starting with User and TransitAuthority is sufficient to establish the pattern.
