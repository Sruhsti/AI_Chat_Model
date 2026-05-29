from typing import Annotated
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from database import get_db
from auth import decode_access_token
from models import User, Conversation

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Annotated[Session,Depends(get_db)]):
    token_data = decode_access_token(token)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail =  "Could not validate credentials",
           headers = {"WWW-Authenticate": "Bearer"}
        )
    user = db.query(User).filter(User.username == token_data.username).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail = "User not found"
        )
    if user.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail = "Inactive user"
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]



def get_conversation(conversation_id: int, current_user: CurrentUser, db: Annotated[Session,Depends(get_db)]):
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail = "Conversation not found"
        )
    if conversation.user_id != current_user.id: # this is to check if the conversation belongs to the current user or not. If not, then we raise an exception.
        raise HTTPException(
           status_code=status.HTTP_403_FORBIDDEN,
            detail = "Not authorized to access this conversation"
        )
    return conversation


