from pydantic import BaseModel
from typing import Optional

# Pydantic models for API data validation (schemas)

class UserBase(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str
    role: str
    entidad_id: str

class User(UserBase):
    id: int
    is_active: bool
    role: str
    entidad_id: str

    class Config:
        orm_mode = True


# --- User Document Schemas ---

class UserDocumentBase(BaseModel):
    document_type: str
    file_path: str
    upload_date: datetime

class UserDocument(UserDocumentBase):
    id: int
    user_id: int

    class Config:
        orm_mode = True


# --- Audit Log Schemas ---
from typing import Dict, Any

class AuditLogBase(BaseModel):
    action: str
    username: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class AuditLog(AuditLogBase):
    id: int
    timestamp: datetime

    class Config:
        orm_mode = True


# --- Procedure and Appointment Schemas ---
from datetime import datetime

class ProcedureBase(BaseModel):
    name: str
    description: Optional[str] = None
    duration_minutes: int = 30

class ProcedureCreate(ProcedureBase):
    pass

class Procedure(ProcedureBase):
    id: int
    is_active: bool

    class Config:
        orm_mode = True

class AppointmentBase(BaseModel):
    procedure_id: int
    appointment_time: datetime

class AppointmentCreate(AppointmentBase):
    pass

class Appointment(AppointmentBase):
    id: int
    user_id: int
    status: str

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# --- Notification Preferences Schemas ---

class NotificationPreferenceBase(BaseModel):
    on_new_fine: bool = True
    on_document_expiration: bool = True
    on_appointment_reminder: bool = True

class NotificationPreferenceCreate(NotificationPreferenceBase):
    user_id: int

class NotificationPreferenceUpdate(BaseModel):
    on_new_fine: Optional[bool] = None
    on_document_expiration: Optional[bool] = None
    on_appointment_reminder: Optional[bool] = None

class NotificationPreference(NotificationPreferenceBase):
    id: int
    user_id: int

    class Config:
        orm_mode = True
