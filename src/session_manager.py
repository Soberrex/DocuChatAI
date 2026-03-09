"""
Session and data management utilities
Handles session persistence, conversation history, and data cleanup
"""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timedelta
from src.models import Session as DBSession, Conversation, Message, Document, Chart
from src.database import get_db


class SessionManager:
    """Manage user sessions and conversation history"""
    
    @staticmethod
    def get_or_create_session(session_id: str, db: Session) -> DBSession:
        """Get existing session or create new one"""
        session = db.query(DBSession).filter(DBSession.id == session_id).first()
        
        if not session:
            session = DBSession(
                id=session_id,
                created_at=datetime.utcnow(),
                last_active=datetime.utcnow()
            )
            db.add(session)
            db.commit()
            db.refresh(session)
        else:
            # Update last active
            session.last_active = datetime.utcnow()
            db.commit()
        
        return session
    
    @staticmethod
    def get_session_conversations(session_id: str, db: Session) -> List[Dict]:
        """Get all conversations for a session"""
        conversations = db.query(Conversation).filter(
            Conversation.session_id == session_id
        ).order_by(desc(Conversation.updated_at)).all()
        
        return [
            {
                "id": conv.id,
                "title": conv.title,
                "created_at": conv.created_at.isoformat(),
                "updated_at": conv.updated_at.isoformat(),
                "message_count": len(conv.messages)
            }
            for conv in conversations
        ]
    
    @staticmethod
    def get_conversation_messages(conversation_id: str, db: Session) -> List[Dict]:
        """Get all messages in a conversation"""
        messages = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at).all()
        
        return [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at.isoformat(),
                "sources": msg.sources if hasattr(msg, 'sources') else None,
                "chart_id": msg.chart_id,
                "chart_data": msg.chart.data if msg.chart else None,
                "confidence": msg.confidence if hasattr(msg, 'confidence') else None
            }
            for msg in messages
        ]
    
    @staticmethod
    def delete_conversation(conversation_id: str, db: Session) -> bool:
        """Delete conversation and all associated messages and charts"""
        try:
            conversation = db.query(Conversation).filter(
                Conversation.id == conversation_id
            ).first()
            
            if not conversation:
                return False
            
            # Delete associated charts
            for message in conversation.messages:
                if message.chart_id:
                    db.query(Chart).filter(Chart.id == message.chart_id).delete()
            
            # Delete messages (cascade should handle this, but being explicit)
            db.query(Message).filter(
                Message.conversation_id == conversation_id
            ).delete()
            
            # Delete conversation
            db.delete(conversation)
            db.commit()
            
            return True
        except Exception as e:
            db.rollback()
            print(f"Error deleting conversation: {e}")
            return False
    
    @staticmethod
    def delete_document(document_id: str, db: Session) -> bool:
        """Delete document and associated data"""
        try:
            document = db.query(Document).filter(
                Document.id == document_id
            ).first()
            
            if not document:
                return False
            
            # Delete physical file from persistent storage
            import os
            try:
                # Based on the naming convention in api/endpoints.py: {session_id}_{filename}
                # But document.filename already contains the doc_id prefix: f"{doc_id}_{file.filename}"
                # So we check if temp_path uses the document.session_id or document.id prefix
                temp_path = os.path.join("/app/data/temp", f"{document.session_id}_{document.original_filename}")
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception as file_e:
                print(f"⚠️ Warning: Could not delete physical file: {file_e}")
            
            db.delete(document)
            db.commit()
            
            return True
        except Exception as e:
            db.rollback()
            print(f"Error deleting document: {e}")
            return False
    
    @staticmethod
    def delete_session(session_id: str, db: Session) -> bool:
        """Delete entire session and all associated data"""
        try:
            session = db.query(DBSession).filter(
                DBSession.id == session_id
            ).first()
            
            if not session:
                return False
            
            # Delete all conversations (cascade will handle messages and charts)
            for conversation in session.conversations:
                SessionManager.delete_conversation(conversation.id, db)
            
            # Delete all documents
            for document in session.documents:
                SessionManager.delete_document(document.id, db)
            
            # Delete session
            db.delete(session)
            db.commit()
            
            return True
        except Exception as e:
            db.rollback()
            print(f"Error deleting session: {e}")
            return False
    
    @staticmethod
    def cleanup_old_data(days: int = 30, db: Session = None) -> Dict[str, int]:
        """Auto-cleanup data older than specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        deleted_count = {
            "sessions": 0,
            "conversations": 0,
            "documents": 0
        }
        
        try:
            # Find old sessions
            old_sessions = db.query(DBSession).filter(
                DBSession.last_active < cutoff_date
            ).all()
            
            for session in old_sessions:
                if SessionManager.delete_session(session.id, db):
                    deleted_count["sessions"] += 1
            
            return deleted_count
        except Exception as e:
            print(f"Error in cleanup: {e}")
            return deleted_count


class ConversationManager:
    """Manage conversation titles and metadata"""
    
    @staticmethod
    def generate_title(first_message: str) -> str:
        """Generate conversation title from first message"""
        # Truncate to first 50 chars
        title = first_message[:50]
        if len(first_message) > 50:
            title += "..."
        return title
    
    @staticmethod
    def update_conversation_title(
        conversation_id: str, 
        title: str, 
        db: Session
    ) -> bool:
        """Update conversation title"""
        try:
            conversation = db.query(Conversation).filter(
                Conversation.id == conversation_id
            ).first()
            
            if conversation:
                conversation.title = title
                db.commit()
                return True
            return False
        except Exception as e:
            db.rollback()
            print(f"Error updating title: {e}")
            return False
