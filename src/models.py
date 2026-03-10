"""
SQLAlchemy models for RAG Chatbot
"""
from sqlalchemy import Column, String, Integer, Text, DateTime, Float, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from src.database import Base
import uuid


class User(Base):
    """Registered User"""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")


class Session(Base):
    """User session/workspace"""
    __tablename__ = "sessions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_active = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_agent = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    documents = relationship("Document", back_populates="session", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="session", cascade="all, delete-orphan")
    charts = relationship("Chart", back_populates="session", cascade="all, delete-orphan")


class Document(Base):
    """Uploaded document metadata"""
    __tablename__ = "documents"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=True)  # Nullable for text-only extraction
    file_size = Column(Integer, nullable=False)
    file_type = Column(String(50), nullable=False)
    status = Column(String(20), default="processing", nullable=False)
    indexed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    chroma_collection_id = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)
    doc_metadata = Column(JSON, nullable=True)  # For summaries, chart suggestions, etc.
    
    # Relationships
    session = relationship("Session", back_populates="documents")


class Conversation(Base):
    """Chat conversation thread"""
    __tablename__ = "conversations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=True)
    is_favorite = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    session = relationship("Session", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    """Chat message (user or assistant)"""
    __tablename__ = "messages"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    document_ids = Column(JSON, nullable=True)
    context_used = Column(Text, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    chart_id = Column(String(36), ForeignKey("charts.id", ondelete="SET NULL"), nullable=True)
    sources = Column(JSON, nullable=True)       # Source citations from RAG
    confidence = Column(Float, nullable=True)    # Confidence score
    tokens_used = Column(Integer, nullable=True)  # Token count
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    chart = relationship("Chart", back_populates="message", foreign_keys=[chart_id])


class Chart(Base):
    """Generated chart/visualization"""
    __tablename__ = "charts"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    chart_type = Column(String(50), nullable=False)
    data = Column(JSON, nullable=False)
    image_path = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    session = relationship("Session", back_populates="charts")
    message = relationship("Message", back_populates="chart", foreign_keys=[Message.chart_id])
