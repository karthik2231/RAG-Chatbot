import json
import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.security import get_current_user
from app.database import get_db
from app.models import User
from app.schemas import ChatRequest, ChatResponse, ConversationResponse, ConversationSummary, MessageResponse
from app.services.chat import ChatService
from app.services.rag import RAGService

router = APIRouter(prefix="/chat", tags=["Chat"])
settings = get_settings()
rag_service = RAGService(settings)
chat_service = ChatService(rag_service)


async def run_chat_request(
    request: Request,
    db: Session,
    current_user: User,
    conversation_id: int | None,
    payload: ChatRequest,
) -> ChatResponse:
    task = asyncio.create_task(
        chat_service.send_message(db, current_user, conversation_id, payload)
    )
    try:
        while not task.done():
            await asyncio.wait({task}, timeout=0.25)
            if await request.is_disconnected():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                raise HTTPException(status_code=499, detail="Generation stopped")

        conversation, message = task.result()
    except ValueError as exc:
        detail = str(exc)
        if "not found" in detail.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail) from exc
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=detail) from exc

    sources = json.loads(message.sources) if message.sources else []
    return ChatResponse(
        answer=message.content,
        sources=sources,
        conversation_id=conversation.id,
        message_id=message.id,
    )


@router.get("/conversations", response_model=list[ConversationSummary])
def list_conversations(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[ConversationSummary]:
    return chat_service.list_conversations(db, current_user)


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
def get_conversation(
    conversation_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ConversationResponse:
    conversation = chat_service.get_conversation(db, current_user, conversation_id)
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return conversation


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    chat_service.delete_conversation(db, current_user, conversation_id)


@router.post("/conversations/{conversation_id}/messages", response_model=ChatResponse)
async def send_message_to_conversation(
    request: Request,
    conversation_id: int,
    payload: ChatRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ChatResponse:
    return await run_chat_request(request, db, current_user, conversation_id, payload)


@router.post("/messages", response_model=ChatResponse)
async def send_message(
    request: Request,
    payload: ChatRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ChatResponse:
    return await run_chat_request(request, db, current_user, None, payload)
