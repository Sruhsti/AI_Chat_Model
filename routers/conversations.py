from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import Annotated
from database import get_db
from models import Conversation
from schemas import ConversationCreate, ConversationPublic, ConversationWithMessages, ConversationUpdate, ConversationShare
from dependencies import get_conversation, CurrentUser
import uuid

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("/", response_model=ConversationPublic)
def create_conversations(
    conversation: ConversationCreate, 
    current_user: CurrentUser, 
    db: Annotated[Session, Depends(get_db)]
):
    new_conversation = Conversation(
        title = conversation.title,
        user_id = current_user.id
    )
    db.add(new_conversation)
    db.commit()
    db.refresh(new_conversation)
    return new_conversation


@router.get("/", response_model=list[ConversationPublic])
def get_all_conversations(
    current_user: CurrentUser, 
    db: Annotated[Session, Depends(get_db)]
):
    conversations = db.query(Conversation).filter(Conversation.user_id == current_user.id).all()
    return conversations


@router.get("/{conversation_id}", response_model=ConversationWithMessages)
def get_one_conversation(
    conversation_id:int,
    current_user: CurrentUser, 
    db: Annotated[Session, Depends(get_db)]
):
    conversation = db.query(Conversation)\
            .options(joinedload(Conversation.messages))\
            .filter(Conversation.id == conversation_id)\
            .first()
    

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
    
    return conversation


@router.patch("/{conversation_id}", response_model=ConversationUpdate)
def rename_conversation(
    conversation_id:int,
    conversation_data: ConversationUpdate, 
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
    
    conversation.title = conversation_data.title
    db.commit()
    db.refresh(conversation)

    return conversation


@router.post("/{conversation_id}/share", response_model=ConversationShare)
def share_conversation(
    conversation_id:int,
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
    if not conversation.share_id:
        conversation.share_id = str(uuid.uuid4())  # Generate a unique share ID

    conversation.is_public = True  # Mark the conversation as public when shared
    db.commit()
    db.refresh(conversation)

    share_url = f"http://127.0.0.1:8000/conversations/share/{conversation.share_id}"

    return ConversationShare(share_url=share_url)


@router.get("/share/{share_id}", response_model=ConversationWithMessages)
def get_shared_conversation(
    share_id: str,
    db: Annotated[Session, Depends(get_db)]
):
    conversation = db.query(Conversation).options(joinedload(Conversation.messages)).filter(Conversation.share_id == share_id,Conversation.is_public == True).first()  
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or not public"
        )
    
    return conversation


@router.delete("/{conversation_id}")
def delete_conversation(
    conversation: Annotated[Conversation,Depends(get_conversation)], 
    db: Annotated[Session, Depends(get_db)]
):
    db.delete(conversation)
    db.commit()
    return {"message": "Conversation deleted successfully"}






