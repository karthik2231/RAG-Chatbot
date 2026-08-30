from sqlalchemy.orm import Session

from app.models import Conversation, Message, User
from app.schemas import ChatRequest
from app.services.rag import RAGService, serialize_sources


class ChatService:
    def __init__(self, rag_service: RAGService) -> None:
        self.rag_service = rag_service

    def list_conversations(self, db: Session, user: User) -> list[Conversation]:
        return (
            db.query(Conversation)
            .filter(Conversation.user_id == user.id)
            .order_by(Conversation.updated_at.desc())
            .all()
        )

    def get_conversation(self, db: Session, user: User, conversation_id: int) -> Conversation | None:
        return (
            db.query(Conversation)
            .filter(Conversation.id == conversation_id, Conversation.user_id == user.id)
            .first()
        )

    def create_conversation(self, db: Session, user: User, title: str = "New Conversation") -> Conversation:
        conversation = Conversation(user_id=user.id, title=title)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        return conversation

    def delete_conversation(self, db: Session, user: User, conversation_id: int) -> None:
        conversation = self.get_conversation(db, user, conversation_id)
        if conversation:
            db.delete(conversation)
            db.commit()

    async def send_message(
        self,
        db: Session,
        user: User,
        conversation_id: int | None,
        payload: ChatRequest,
    ) -> tuple[Conversation, Message]:
        if conversation_id:
            conversation = self.get_conversation(db, user, conversation_id)
            if not conversation:
                raise ValueError("Conversation not found")
        else:
            title = payload.message[:50] + ("..." if len(payload.message) > 50 else "")
            conversation = Conversation(user_id=user.id, title=title)
            db.add(conversation)
            db.flush()

        history = [
            {"role": msg.role, "content": msg.content}
            for msg in conversation.messages
        ]

        user_message = Message(conversation_id=conversation.id, role="user", content=payload.message)
        db.add(user_message)
        db.flush()

        try:
            answer, sources = await self.rag_service.query(
                user_id=user.id,
                query=payload.message,
                document_ids=payload.document_ids,
                history=history,
            )
        except BaseException:
            db.rollback()
            raise

        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=answer,
            sources=serialize_sources(sources),
        )
        db.add(assistant_message)
        db.commit()
        db.refresh(assistant_message)
        db.refresh(conversation)

        return conversation, assistant_message
