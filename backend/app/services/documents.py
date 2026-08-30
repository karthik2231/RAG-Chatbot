from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import Document, User
from app.services.rag import DocumentProcessor, EmbeddingService, VectorStore


class DocumentService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.processor = DocumentProcessor(settings)
        self.embedding_service = EmbeddingService(settings)
        self.vector_store = VectorStore(settings)
        self.upload_dir = settings.upload_dir
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def list_documents(self, db: Session, user: User) -> list[Document]:
        return db.query(Document).filter(Document.user_id == user.id).order_by(Document.created_at.desc()).all()

    def get_document(self, db: Session, user: User, document_id: int) -> Document:
        document = (
            db.query(Document)
            .filter(Document.id == document_id, Document.user_id == user.id)
            .first()
        )
        if not document:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        return document

    async def upload_document(self, db: Session, user: User, file: UploadFile) -> Document:
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are supported")

        content = await file.read()
        max_bytes = self.settings.max_upload_size_mb * 1024 * 1024
        if len(content) > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File exceeds {self.settings.max_upload_size_mb}MB limit",
            )

        user_dir = self.upload_dir / str(user.id)
        user_dir.mkdir(parents=True, exist_ok=True)

        stored_name = f"{uuid.uuid4().hex}.pdf"
        file_path = user_dir / stored_name
        file_path.write_bytes(content)

        document = Document(
            user_id=user.id,
            filename=stored_name,
            original_filename=file.filename,
            file_path=str(file_path),
            file_size=len(content),
            status="processing",
        )
        db.add(document)
        db.commit()
        db.refresh(document)

        try:
            pages = self.processor.extract_text_from_pdf(file_path)
            chunks = self.processor.create_chunks(pages, document.id, document.original_filename)

            if chunks:
                texts = [chunk.text for chunk in chunks]
                embeddings = self.embedding_service.embed_texts(texts)
                self.vector_store.add_chunks(user.id, chunks, embeddings)

            document.page_count = len(pages)
            document.chunk_count = len(chunks)
            document.status = "ready"
        except Exception as exc:
            document.status = "failed"
            file_path.unlink(missing_ok=True)
            if isinstance(exc, HTTPException):
                raise
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="The uploaded file is not a readable PDF",
            ) from exc
        finally:
            db.commit()
            db.refresh(document)

        if document.chunk_count == 0:
            document.status = "failed"
            db.commit()
            db.refresh(document)
            file_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="The PDF does not contain extractable text",
            )

        return document

    def delete_document(self, db: Session, user: User, document_id: int) -> None:
        document = self.get_document(db, user, document_id)
        file_path = Path(document.file_path)
        if file_path.exists():
            file_path.unlink()

        self.vector_store.remove_document(user.id, document.id)
        db.delete(document)
        db.commit()
