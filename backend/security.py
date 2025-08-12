from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt

# --- Configuration ---
# In a real application, this should be loaded from environment variables
SECRET_KEY = "a_very_secret_key_that_should_be_changed"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# --- Password Hashing ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# --- JWT Token Creation ---
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- API Key "Encryption" (Simulated) ---
# In a real production environment, use a robust encryption library like `cryptography`
# with a securely managed key. For this simulation, we'll use base64 as a placeholder.
import base64

def encrypt_api_key(key: str) -> str:
    return base64.b64encode(key.encode('utf-8')).decode('utf-8')

def decrypt_api_key(encrypted_key: str) -> str:
    return base64.b64decode(encrypted_key.encode('utf-8')).decode('utf-8')
