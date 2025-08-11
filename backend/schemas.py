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

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
