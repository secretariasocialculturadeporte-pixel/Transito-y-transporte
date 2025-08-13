import shutil
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
import os
import uuid

from .... import crud, models_db, schemas
from ..auth import get_current_user, get_db

router = APIRouter()

# Define the storage path
STORAGE_PATH = "storage/user_documents/"

@router.post("/upload", response_model=schemas.UserDocument, summary="Upload a user document")
async def upload_document(
    document_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models_db.User = Depends(get_current_user)
):
    """
    Handles the upload of a document for the current user.
    The file is saved to the server's file system, and a record is created in the database.
    """
    # Create a unique filename to avoid collisions
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(STORAGE_PATH, unique_filename)

    try:
        # Save the file to the storage directory
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"There was an error uploading the file: {e}",
        )
    finally:
        file.file.close()

    # Create the database record
    db_document = crud.create_user_document(
        db=db,
        user_id=current_user.id,
        document_type=document_type,
        file_path=f"/storage/user_documents/{unique_filename}" # Store the public URL path
    )

    return db_document

@router.get("/me", response_model=List[schemas.UserDocument], summary="Get my uploaded documents")
def get_my_documents(
    db: Session = Depends(get_db),
    current_user: models_db.User = Depends(get_current_user)
):
    """
    Retrieves a list of all documents uploaded by the currently authenticated user.
    """
    return crud.get_user_documents(db=db, user_id=current_user.id)
