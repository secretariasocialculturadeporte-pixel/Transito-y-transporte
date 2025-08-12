from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from .... import crud, models_db, schemas
from .auth import get_current_user, get_db

router = APIRouter()

class ApiKeyCreate(schemas.BaseModel):
    provider: str # e.g., "openai", "google"
    api_key: str

@router.post("/", status_code=status.HTTP_201_CREATED)
def set_api_key(
    key_data: ApiKeyCreate,
    db: Session = Depends(get_db),
    current_user: models_db.User = Depends(get_current_user)
):
    if current_user.role != "SuperAdmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    db_key = crud.create_or_update_api_key(
        db=db,
        entidad_id=current_user.entidad_id,
        provider=key_data.provider,
        key=key_data.api_key
    )
    return {"message": "API key set successfully"}

@router.get("/", response_model=Optional[schemas.BaseModel])
def get_api_key_info(
    db: Session = Depends(get_db),
    current_user: models_db.User = Depends(get_current_user)
):
    if current_user.role != "SuperAdmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    db_key = crud.get_api_key(db, entidad_id=current_user.entidad_id)
    if not db_key:
        return None

    # Return a schema that doesn't expose the key
    return {"provider": db_key.provider, "entidad_id": db_key.entidad_id}
