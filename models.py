from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime, timezone

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    conversations = relationship("Conversation", back_populates="user", cascade="all, delete") # this means one user can have many conversations, and if the user is deleted, all their conversations will also be deleted.
    documents = relationship("Document", back_populates="user", cascade="all, delete") # this means one user can have many documents, and if the user is deleted, all their documents will also be deleted.
    

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    #sharing fields
    share_id = Column(String(255), unique=True, nullable=True)
    is_public = Column(Boolean, default=False)

    user = relationship("User", back_populates="conversations") # this means one conversation belongs to one user only
    messages = relationship("Message", back_populates="conversation", cascade="all, delete") # this means one conversation can have many messages, and if the conversation is deleted, all its messages will also be deleted.


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    role = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    conversation = relationship("Conversation", back_populates="messages") # this means one message belongs to one conversation, and if the conversation is deleted, all its messages will also be deleted.


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    content = Column(LONGTEXT, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="documents") # this means one document belongs to one user only
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete") # this means one document can have many chunks, and if the document is deleted, all its chunks will also be deleted.


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    embedding = Column(Text, nullable=True)  # Store the embedding as a string (you can convert it to a list when needed)

    document = relationship("Document", back_populates="chunks") # this means one chunk belongs to one document only
