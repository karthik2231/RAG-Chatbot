from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.security import get_current_user
from app.database import get_db
from app.models import User
from app.schemas import DocumentResponse
from app.services.documents import DocumentService

router = APIRouter(prefix="/documents", tags=["Documents"])
settings = get_settings()
document_service = DocumentService(settings)


@router.get("", response_model=list[DocumentResponse])
def list_documents(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[DocumentResponse]:
    return document_service.list_documents(db, current_user)


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    file: UploadFile = File(...),
) -> DocumentResponse:
    return await document_service.upload_document(db, current_user, file)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    document_service.delete_document(db, current_user, document_id)
