# models.py
# Defines the Pydantic models for the application, based on the provided example.

from pydantic import BaseModel, Field, validator, EmailStr
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date, timezone
from enum import Enum

# --- Enumerations ---

class ChatMode(Enum):
    CONVERSATIONAL = "conversacional"
    FORM_DICTATION = "dictado_de_formulario"
    DIAGNOSTIC_PROCEDURE = "procedimiento_de_diagnostico"
    APPOINTMENT_SCHEDULING = "programacion_de_cita"
    PAYMENT_PROCESSING = "procesamiento_de_pago"
    RESPONSE_REGULATION = "regulacion_de_respuesta"
    AWAITING_CONFIRMATION = "esperando_confirmacion"
    AWAITING_CLARIFICATION = "esperando_aclaracion"

# --- Conversation Context Models ---

class ActiveTask(BaseModel):
    task_type: ChatMode
    step: int = 0
    related_entity_id: Optional[str] = None
    task_data: Dict[str, Any] = {}

class ConversationContext(BaseModel):
    last_intent: Optional[str] = None
    entities: List[Tuple[str, str]] = []
    history: List[str] = []
    current_mode: ChatMode = ChatMode.CONVERSATIONAL
    pending_action: Optional[Dict] = None
    pending_confirmation_type: Optional[str] = None
    last_dictation_form_context: Optional[str] = None
    last_extracted_data: Optional[Dict] = None
    awaiting_field_correction: Optional[str] = None
    active_task: Optional[ActiveTask] = None
    confirm_retries: int = 0

    class Config:
        orm_mode = True

# --- Base API Response Models ---

class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None

class ErrorResponse(ApiResponse):
    success: bool = False
    detail: Optional[Any] = None

# --- User Models ---

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=20, pattern=r"^[a-z0-9_]{3,20}$")
    role: str
    dept: Optional[str] = Field(None, pattern=r"^\d{1,2}$")
    mun: Optional[str] = Field(None, pattern=r"^\d{3,5}$")
    status: str = Field("Active", pattern=r"^(Active|Inactive)$")
    area: Optional[str] = Field(None, max_length=100)
    full_name: Optional[str] = Field(None, max_length=150)
    email: Optional[EmailStr] = None

class UserInDB(UserBase):
    password: str  # In a real DB, this would be a hash
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None
    last_modified: Optional[datetime] = None
    soat_vigente: Optional[bool] = None
    tecno_vigente: Optional[bool] = None
    impuesto_pago: Optional[bool] = None
    paz_salvo_multas: Optional[bool] = None  # Calculated dynamically
    estar_inscrito_runt: Optional[bool] = None
    examen_medico_aprobado: Optional[bool] = None
    curso_cea_aprobado: Optional[bool] = None

    @validator('last_login', 'created_at', 'last_modified', pre=True, allow_reuse=True)
    def parse_optional_datetime(cls, value):
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        except (ValueError, TypeError):
            return None

    class Config:
        orm_mode = True

class TramiteActivo(BaseModel):
    id_tramite: str
    nombre: str
    estado: str
    fecha_inicio: date

    @validator('fecha_inicio', pre=True)
    def parse_ta_date(cls, value):
        if isinstance(value, date):
            return value
        try:
            return date.fromisoformat(str(value))
        except (ValueError, TypeError):
            return None

class UserDetail(UserBase):
    user_id_sim: int
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None
    last_modified: Optional[datetime] = None
    soat_vigente: Optional[bool] = None
    tecno_vigente: Optional[bool] = None
    impuesto_pago: Optional[bool] = None
    paz_salvo_multas: bool = False
    estar_inscrito_runt: Optional[bool] = None
    examen_medico_aprobado: Optional[bool] = None
    curso_cea_aprobado: Optional[bool] = None
    tramites_activos: List[TramiteActivo] = []

    @validator('last_login', 'created_at', 'last_modified', pre=True, allow_reuse=True)
    def parse_detail_datetime(cls, value):
        return UserInDB.parse_optional_datetime(value)

    class Config:
        orm_mode = True

class UserCreateData(BaseModel):
    username: str = Field(..., min_length=3, max_length=20, pattern=r"^[a-z0-9_]{3,20}$")
    password: str = Field(..., min_length=4)
    role: str
    dept: Optional[str] = Field(None, pattern=r"^\d{1,2}$")
    mun: Optional[str] = Field(None, pattern=r"^\d{3,5}$")
    area: Optional[str] = None

class UserUpdateData(BaseModel):
    area: Optional[str] = None
    status: Optional[str] = Field(None, pattern=r"^(Active|Inactive)$")

class PasswordChangeData(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=4)

# --- Fine Models ---

class FineBase(BaseModel):
    id: str
    date: date
    codigo_infraccion: Optional[str] = None
    description: Optional[str] = None
    value: int
    status: str = Field(..., pattern=r"^(Pendiente|Pagado|Anulado)$")
    paid_date: Optional[date] = None

    @validator('date', 'paid_date', pre=True, allow_reuse=True)
    def parse_optional_date(cls, value):
        if value is None:
            return None
        if isinstance(value, date):
            return value
        try:
            return date.fromisoformat(str(value))
        except (ValueError, TypeError):
            return None

    class Config:
        orm_mode = True

class FineUIDetail(FineBase):
    puntos: int = 0
    descuento_aplicable: bool = False
    valor_con_descuento: Optional[int] = None
    base_value_formatted: str
    final_value_formatted: str
    fine_info_tooltip: str

# --- Procedure Models ---

class ProgramInfo(BaseModel):
    id: str
    nombre: str
    categoria: str
    descripcion: str

class PrerequisiteStatus(BaseModel):
    clave: str
    descripcion: str
    met: bool

class ProcedureUIDetail(ProgramInfo):
    costo: Optional[str] = None
    pasos: List[str] = []
    documentos_requeridos: List[str] = Field([], alias="docs")
    prerrequisitos: List[PrerequisiteStatus] = []
    can_initiate: bool = False

# --- Auth Models ---

class TokenData(BaseModel):
    username: Optional[str] = None

class LoginResponseData(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_info: UserDetail

class LoginResponse(ApiResponse):
    success: bool = True
    data: Optional[LoginResponseData] = None

# --- Chat Models ---
class ChatMessageInput(BaseModel):
    message: str
    context: Optional[ConversationContext] = None

class ChatMessageOutput(BaseModel):
    response_text: str
    # Add other fields as needed, e.g., suggested_actions, new_context

class ChatResponse(ApiResponse):
    data: Optional[ChatMessageOutput] = None

class ConversationLogEntry(BaseModel):
    # Define fields for logging conversations
    pass

class StoredDictationAttempt(BaseModel):
    # Define fields for storing dictation context
    pass

# --- Dictation Models ---
class DictationInput(BaseModel):
    # Define fields for dictation input
    pass

class ExtractedFormData(BaseModel):
    # Define fields for extracted form data from dictation
    pass

class DictationResponse(ApiResponse):
    data: Optional[ExtractedFormData] = None

# --- Dashboard Models ---
class DashboardKPI(BaseModel):
    # Define fields for Key Performance Indicators
    pass

class DashboardData(BaseModel):
    # Define fields for dashboard data
    pass

# To resolve forward references like List["TramiteActivo"]
UserDetail.update_forward_refs()
