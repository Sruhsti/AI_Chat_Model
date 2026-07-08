from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Literal


class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserPublic(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}

class UserProfile(BaseModel):
    id: int
    username: str
    email: str
    model_config = {"from_attributes": True}


class ConversationCreate(BaseModel):
    title: str | None = None


class ConversationPublic(BaseModel):
    id: int
    title: str | None = None
    created_at: datetime
    share_id: str | None = None
    is_public: bool = False
    model_config = {"from_attributes": True}

class ConversationUpdate(BaseModel):
    title: str

class ConversationShare(BaseModel):
    share_url: str
    

class MessagePublic(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime
    model_config = {"from_attributes": True}


class ConversationWithMessages(ConversationPublic):
    messages: list[MessagePublic] = []


class ChatRequest(BaseModel):
    conversation_id: int
    message: str
    source: Literal["internal", "external"] | None = "external"  # default to "external" if not provided
    document_id : int | None = None  # optional field for document ID

class DocumentPublic(BaseModel):
    id: int
    filename: str
    created_at: datetime
    model_config = {"from_attributes": True}

class DocumentUploadResponse(BaseModel):
    document_id: int    
    message: str
    filename: str   

class DocumentChunkPublic(BaseModel):
    id: int
    chunk_index: int
    chunk_text: str
    model_config = {"from_attributes": True}

