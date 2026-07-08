from fastapi import APIRouter, Depends, HTTPException, status
# from fastapi.responses import StreamingResponse
from fastapi.sse import EventSourceResponse, format_sse_event
from sqlalchemy.orm import Session
from typing import Annotated
from database import get_db
from models import Conversation, Message
from schemas import ChatRequest, MessagePublic
from dependencies import get_conversation, CurrentUser
from services.ai_service import get_ai_response
from models import Document, DocumentChunk
from services.embedding_service import find_similar_chunks


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

    print(f"Source selected: {chat_request.source}")
    print(f"Query: {chat_request.message}")

    # RAG flow — internal source
    if chat_request.source == "internal":
        if not chat_request.document_id:
            raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="document_id is required for internal source"
        )

        document = db.query(Document).filter(Document.id == chat_request.document_id).first()
        if not document:
            raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

        if document.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized"
            )

        print(f"Document used: {document.filename}")

        # get chunks and find similar ones
        chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == chat_request.document_id).all()
        chunks_with_embeddings = [(chunk.chunk_text, chunk.embedding) for chunk in chunks if chunk.embedding is not None]
        related_chunks = find_similar_chunks(chat_request.message, chunks_with_embeddings, top_k=3)
        if not related_chunks:
            print("No related chunks found — answering with empty context")
        else:
            print(f"Related chunks: {related_chunks}")
        context = "\n\n".join(related_chunks)
        messages_list[-1]["content"] = f"""Use the following context to answer the question.

            Context:
            {context}

            Question: {chat_request.message}"""
            
    # SSE streaming       
    async def event_generator():
        full_response = ""

        async for text in get_ai_response(messages_list):
            full_response += text
            yield format_sse_event(data_str=text, event="token")

        print(f"LLM answer: {full_response}")

        assistant_message = Message(
            conversation_id = chat_request.conversation_id,
            role = "assistant",
            content = full_response
        )
        db.add(assistant_message)
        db.commit()

        yield format_sse_event(data_str="[DONE]", event="done")

    return EventSourceResponse(event_generator())

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
    

        


