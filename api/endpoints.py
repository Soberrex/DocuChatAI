"""
API Endpoints for Document Upload, Chat, and Data Management
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Optional, Dict
from sqlalchemy.orm import Session as DBSession
from datetime import datetime
import uuid
import traceback

from src.database import get_db
from src.models import Document as DBDocument, Conversation, Message, Session as SessionModel, User
from src.auth import get_password_hash, verify_password, create_access_token, get_current_user_id
from sqlalchemy.exc import IntegrityError
from src.document_processor import DocumentProcessor
from src.session_manager import SessionManager, ConversationManager

router = APIRouter()


# ─── Pydantic Models ───────────────────────────────

class UserCreate(BaseModel):
    email: str
    password: str

class AuthResponse(BaseModel):
    token: str
    user: Dict

class UploadResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    message: str
    file_kept: bool
    summary: Optional[Dict] = None

class ChatRequest(BaseModel):
    message: str
    conversation_id: str
    session_id: str

class ChatResponse(BaseModel):
    message: Dict
    sources: Optional[List[Dict]] = None
    chart_data: Optional[Dict] = None

class DeleteResponse(BaseModel):
    success: bool
    message: str

# ─── Auth Endpoints ────────────────────────────────

@router.post("/auth/register")
async def register(user_data: UserCreate, db: DBSession = Depends(get_db)):
    try:
        new_user = User(
            email=user_data.email,
            password_hash=get_password_hash(user_data.password)
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        token = create_access_token({"sub": new_user.id})
        return {"token": token, "user": {"id": new_user.id, "email": new_user.email}}
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email already registered")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/auth/login")
async def login(user_data: UserCreate, db: DBSession = Depends(get_db)):
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token({"sub": user.id})
    return {"token": token, "user": {"id": user.id, "email": user.email}}

# ─── Upload Endpoint ───────────────────────────────

@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    db: DBSession = Depends(get_db)
):
    """Upload and process document with text extraction, indexing, and auto-summary"""
    try:
        from src.page_index import get_page_index
        from src.rag_engine import get_rag_engine

        # Ensure session exists
        sid = session_id or str(uuid.uuid4())
        SessionManager.get_or_create_session(sid, db)

        # Stream file to persistent data directory to avoid memory spike
        import os
        import aiofiles
        
        # Ensure temp directory exists on the persistent disk
        temp_dir = "/app/data/temp"
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, f"{sid}_{file.filename}")
        
        file_size = 0
        async with aiofiles.open(temp_path, 'wb') as out_file:
            while content := await file.read(1024 * 1024):  # 1MB chunks
                await out_file.write(content)
                file_size += len(content)

        # Create document record with initial metadata
        doc_id = str(uuid.uuid4())
        document = DBDocument(
            id=doc_id,
            session_id=sid,
            filename=f"{doc_id}_{file.filename}",
            original_filename=file.filename,
            file_size=file_size,
            file_type=DocumentProcessor.detect_file_type(file.filename),
            status='processing',
            doc_metadata={
                'chunk_count': 0,
                'file_kept': True
            }
        )
        db.add(document)
        db.commit()

        # Define background task for heavy extraction
        import asyncio
        async def _process_upload_background(file_path: str, bg_doc_id: str, original_name: str, file_size_bg: int):
            try:
                print(f"🔄 Starting background extraction for {original_name}...")
                
                # 1. Heavy extraction (takes >100s for large PDFs, safe in background)
                processor = DocumentProcessor()
                result = await processor.process_document(
                    file_path=file_path,
                    filename=original_name,
                    file_size=file_size_bg
                )
                
                # 2. Add chunks to memory index and persist to disk
                from src.page_index import get_page_index
                page_index = get_page_index()
                chunks_added = page_index.add_document_chunks(
                    chunks=result['chunks'],
                    document_id=bg_doc_id,
                    filename=original_name,
                    file_type=result['file_type']
                )
                page_index.persist()
                print(f"✅ Indexed {chunks_added} chunks for {original_name}")

                # 3. Generate initial summary
                from src.database import SessionLocal
                from src.rag_engine import get_rag_engine
                bg_db = SessionLocal()
                try:
                    doc = bg_db.query(DBDocument).filter(DBDocument.id == bg_doc_id).first()
                    if not doc:
                        return

                    rag_engine = get_rag_engine()
                    summary_result = await rag_engine.generate_document_summary(
                        document_id=bg_doc_id,
                        document_text=result['text'][:10000],
                        file_type=result['file_type']
                    )

                    # 4. Finalize document save
                    doc.doc_metadata = {
                        **(doc.doc_metadata or {}),
                        'chunk_count': chunks_added,
                        'file_kept': result['should_keep_file'],
                        'summary': summary_result.get('summary'),
                        'suggested_charts': summary_result.get('suggested_charts', [])
                    }
                    doc.status = 'ready'
                    doc.indexed_at = datetime.utcnow()
                    bg_db.commit()
                    print(f"✅ Completed processing for {original_name}")
                except Exception as inner_e:
                    print(f"❌ Error in background db update: {inner_e}")
                    if doc:
                        doc.status = 'failed'
                        doc.error_message = str(inner_e)
                        bg_db.commit()
                finally:
                    bg_db.close()
            except Exception as e:
                print(f"⚠️ Background processing failed completely: {e}")

        # Start background task
        import asyncio
        asyncio.create_task(_process_upload_background(temp_path, doc_id, file.filename, file_size))

        return {
            "document_id": doc_id,
            "filename": file.filename,
            "status": "processing",
            "message": "Upload accepted. Processing in background to prevent timeout.",
            "file_kept": True
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


# ─── Chat Endpoint ─────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: DBSession = Depends(get_db)
):
    """Send message and get AI response with sources and charts"""
    try:
        from src.rag_engine import get_rag_engine

        # Save user message
        user_msg_id = str(uuid.uuid4())
        user_message = Message(
            id=user_msg_id,
            conversation_id=request.conversation_id,
            role='user',
            content=request.message,
            created_at=datetime.utcnow()
        )
        db.add(user_message)
        db.commit()

        # Get conversation history
        history_messages = db.query(Message).filter(
            Message.conversation_id == request.conversation_id
        ).order_by(Message.created_at.desc()).limit(6).all()

        conversation_history = [
            {"role": msg.role, "content": msg.content}
            for msg in reversed(history_messages)
        ]

        # UX IMPROVEMENT: Check if session has documents
        doc_count = db.query(DBDocument).filter(
            DBDocument.session_id == request.session_id
        ).count()

        if doc_count == 0:
            assistant_msg_id = str(uuid.uuid4())
            response_text = "I don't see any documents uploaded yet. Please upload a document so I can answer your questions."
            
            assistant_message = Message(
                id=assistant_msg_id,
                conversation_id=request.conversation_id,
                role='assistant',
                content=response_text,
                created_at=datetime.utcnow(),
                confidence=1.0
            )
            db.add(assistant_message)
            db.commit()
            
            return ChatResponse(
                message={
                    "id": assistant_msg_id,
                    "role": "assistant",
                    "content": response_text,
                    "created_at": assistant_message.created_at.isoformat(),
                    "confidence": 1.0
                },
                sources=[]
            )

        # Process query with RAG
        rag_engine = get_rag_engine()
        rag_response = await rag_engine.process_query(
            query=request.message,
            session_id=request.session_id,
            conversation_history=conversation_history,
            top_k=3,
            has_documents=(doc_count > 0)
        )

        # Save assistant message
        assistant_msg_id = str(uuid.uuid4())
        assistant_message = Message(
            id=assistant_msg_id,
            conversation_id=request.conversation_id,
            role='assistant',
            content=rag_response['response'],
            created_at=datetime.utcnow(),
            sources=rag_response.get('sources', []),
            confidence=rag_response.get('confidence', 0.0),
            tokens_used=rag_response.get('tokens_used', 0)
        )
        db.add(assistant_message)

        # Update conversation title if first message
        conversation = db.query(Conversation).filter(
            Conversation.id == request.conversation_id
        ).first()

        if conversation and conversation.title == "New Conversation":
            conversation.title = ConversationManager.generate_title(request.message)
            conversation.updated_at = datetime.utcnow()

        db.commit()

        return ChatResponse(
            message={
                "id": assistant_msg_id,
                "role": "assistant",
                "content": assistant_message.content,
                "created_at": assistant_message.created_at.isoformat(),
                "confidence": rag_response.get('confidence', 0.0)
            },
            sources=rag_response.get('sources', []),
            chart_data=rag_response.get('chart_data')
        )

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


# ─── Deletion Endpoints ───────────────────────────

@router.delete("/conversations/{conversation_id}", response_model=DeleteResponse)
async def delete_conversation(
    conversation_id: str,
    db: DBSession = Depends(get_db)
):
    """Delete conversation and all associated messages and charts"""
    success = SessionManager.delete_conversation(conversation_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return DeleteResponse(success=True, message="Conversation deleted successfully")


@router.delete("/documents/{document_id}", response_model=DeleteResponse)
async def delete_document(
    document_id: str,
    db: DBSession = Depends(get_db)
):
    """Delete document and associated index entries"""
    try:
        from src.page_index import get_page_index
        page_index = get_page_index()
        page_index.delete_document(document_id)
        page_index.persist()
    except Exception as e:
        print(f"⚠️ Page index cleanup: {e}")

    success = SessionManager.delete_document(document_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return DeleteResponse(success=True, message="Document deleted successfully")


@router.delete("/sessions/{session_id}", response_model=DeleteResponse)
async def delete_session(
    session_id: str,
    db: DBSession = Depends(get_db)
):
    """Delete entire session and all associated data"""
    try:
        from src.page_index import get_page_index
        page_index = get_page_index()
        page_index.delete_session(session_id)
        page_index.persist()
    except Exception as e:
        print(f"⚠️ Page index cleanup: {e}")

    success = SessionManager.delete_session(session_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return DeleteResponse(success=True, message="Session and all data deleted successfully")


@router.post("/cleanup")
async def cleanup_old_data(
    days: int = 30,
    db: DBSession = Depends(get_db)
):
    """Auto-cleanup data older than specified days"""
    result = SessionManager.cleanup_old_data(days, db)
    return {"success": True, "message": "Cleanup completed", "deleted": result}


# ─── Session & Conversation Endpoints ──────────────

@router.get("/sessions/{session_id}/conversations")
async def get_session_conversations(
    session_id: str,
    db: DBSession = Depends(get_db),
    user_id: str | None = Depends(get_current_user_id)
):
    """Get all conversations for a session or user"""
    return SessionManager.get_session_conversations(session_id, db, user_id)


@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: str,
    db: DBSession = Depends(get_db)
):
    """Get all messages in a conversation"""
    return SessionManager.get_conversation_messages(conversation_id, db)


@router.get("/documents/{session_id}")
async def get_documents(
    session_id: str,
    db: DBSession = Depends(get_db)
):
    """Get all documents for a session"""
    documents = db.query(DBDocument).filter(
        DBDocument.session_id == session_id
    ).all()
    return [
        {
            "id": doc.id,
            "filename": doc.original_filename,
            "file_size": doc.file_size,
            "file_type": doc.file_type,
            "status": doc.status,
            "created_at": doc.created_at.isoformat() if doc.created_at else None,
            "metadata": doc.doc_metadata
        }
        for doc in documents
    ]


@router.post("/conversations")
async def create_conversation(
    session_id: str = Query(...),
    db: DBSession = Depends(get_db),
    user_id: str | None = Depends(get_current_user_id)
):
    """Create new conversation"""
    SessionManager.get_or_create_session(session_id, db, user_id)

    conv_id = str(uuid.uuid4())
    conversation = Conversation(
        id=conv_id,
        session_id=session_id,
        title="New Conversation",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(conversation)
    db.commit()

    return {
        "id": conv_id,
        "title": conversation.title,
        "is_favorite": conversation.is_favorite,
        "created_at": conversation.created_at.isoformat()
    }

@router.patch("/conversations/{conversation_id}/favorite")
async def toggle_favorite(
    conversation_id: str,
    db: DBSession = Depends(get_db)
):
    try:
        convo = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not convo:
            raise HTTPException(status_code=404, detail="Conversation not found")
            
        convo.is_favorite = not convo.is_favorite
        db.commit()
        return {"is_favorite": convo.is_favorite}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
