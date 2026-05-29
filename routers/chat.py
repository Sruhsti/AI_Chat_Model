from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Annotated
from database import get_db
from models import Conversation, Message
from schemas import ChatRequest, MessagePublic
from dependencies import get_conversation, CurrentUser
from services.ai_service import get_ai_response


router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/stream")
async def stream_chat(
    chat_request : ChatRequest,
    current_user : CurrentUser,
    db : Annotated[Session, Depends(get_db)]
):
    conversation = db.query(Conversation).filter(chat_request.conversation_id == Conversation.id).first()
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    if conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )

    user_message = Message(
        conversation_id = chat_request.conversation_id,
        role = "user",
        content = chat_request.message
    )

    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    all_messages = db.query(Message).filter(Message.conversation_id == chat_request.conversation_id).order_by(Message.created_at).all()

    messages_list = [ {"role": msg.role, "content": msg.content} for msg in all_messages ]

    async def event_generator():
        full_response = ""

        async for text in get_ai_response(messages_list):
            full_response += text
            yield f"event: token\ndata: {text}\n\n"

        assistant_message = Message(
            conversation_id = chat_request.conversation_id,
            role = "assistant",
            content = full_response
        )
        db.add(assistant_message)
        db.commit()

        yield "event: done\ndata: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/{conversation_id}/history", response_model=list[MessagePublic])
def get_chat_history(
    conversation_id: int,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)]
):
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    if conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    messages = db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at).all()
    return messages
    

        


