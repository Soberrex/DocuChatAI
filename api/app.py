from fastapi import FastAPI, HTTPException, Depends, Header, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import os
from dotenv import load_dotenv
import sys
import time
from functools import lru_cache

# Add parent directory to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.indexer import HybridIndexer
from src.metrics import MetricsTracker

# Rate limiting
try:
    from slowapi import Limiter
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    limiter = Limiter(key_func=get_remote_address)
    RATE_LIMITING_ENABLED = True
except ImportError:
    RATE_LIMITING_ENABLED = False
    limiter = None

load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Enterprise RAG API",
    description="Production-grade Hybrid RAG System for Code & Document Retrieval",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add rate limiter to app state
if RATE_LIMITING_ENABLED and limiter:
    app.state.limiter = limiter

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded. Please try again later."}
        )

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple response cache (TTL-based)
_cache: Dict[str, tuple] = {}  # key -> (result, timestamp)
CACHE_TTL = 300  # 5 minutes

def get_cached(key: str):
    """Get cached result if not expired"""
    if key in _cache:
        result, ts = _cache[key]
        if time.time() - ts < CACHE_TTL:
            return result
        del _cache[key]
    return None

def set_cached(key: str, result):
    """Cache a result"""
    _cache[key] = (result, time.time())
    # Evict old entries if cache grows too large
    if len(_cache) > 100:
        oldest = min(_cache, key=lambda k: _cache[k][1])
        del _cache[oldest]

# Global instances
indexer: Optional[HybridIndexer] = None
metrics_tracker = MetricsTracker()

# Pydantic Models
class QueryRequest(BaseModel):
    query: str = Field(..., description="Search query", min_length=1, max_length=500)
    top_k: Optional[int] = Field(10, description="Number of results to return", ge=1, le=50)

class QueryResponse(BaseModel):
    success: bool
    query: str
    result_file: Optional[str]
    confidence_score: Optional[float]
    response_time_ms: float
    message: str

class StatsResponse(BaseModel):
    total_queries: int
    successful_queries: int
    success_rate: str
    avg_response_time_ms: float
    avg_confidence: float

class IndexRequest(BaseModel):
    folder_path: str = Field(..., description="Path to folder containing documents")

class IndexResponse(BaseModel):
    success: bool
    message: str
    files_indexed: int

class HealthResponse(BaseModel):
    status: str
    indexer_loaded: bool
    total_documents: int
    api_version: str

class RecentQuery(BaseModel):
    timestamp: str
    query: str
    response_time_ms: float
    result_found: bool
    confidence_score: float

# Authentication
API_KEY = os.getenv("API_KEY", "your-secret-key-change-this")

async def verify_api_key(x_api_key: str = Header(...)):
    """Verify API key from request header"""
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key"
        )
    return x_api_key

# Startup Event
@app.on_event("startup")
async def startup_event():
    """Initialize indexer on API startup"""
    global indexer
    print("🚀 Starting Enterprise RAG API...")
    try:
        indexer = HybridIndexer()
        print("✅ Indexer initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize indexer: {e}")
        indexer = None

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("👋 Shutting down Enterprise RAG API...")

# Endpoints

@app.get("/", tags=["General"])
async def root():
    """API root endpoint with basic information"""
    return {
        "message": "Enterprise RAG API",
        "status": "online",
        "version": "1.0.0",
        "endpoints": {
            "search": "POST /search",
            "stats": "GET /stats",
            "index": "POST /index",
            "health": "GET /health",
            "recent": "GET /recent-queries"
        },
        "docs": "/docs"
    }

@app.get("/health", response_model=HealthResponse, tags=["General"])
async def health_check():
    """Health check endpoint"""
    doc_count = 0
    if indexer and indexer.collection:
        try:
            doc_count = indexer.collection.count()
        except:
            doc_count = 0
    
    return HealthResponse(
        status="healthy" if indexer else "unhealthy",
        indexer_loaded=indexer is not None,
        total_documents=doc_count,
        api_version="1.0.0"
    )

@app.post("/search", response_model=QueryResponse, tags=["Search"])
async def search_documents(
    request: QueryRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Search for relevant documents using hybrid retrieval
    
    - **query**: Search query string
    - **top_k**: Number of top results to consider (default: 10)
    """
    if not indexer:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Indexer not initialized. Please contact administrator."
        )
    
    try:
        start = time.time()
        
        result_file = indexer.search(request.query, top_k=request.top_k)
        
        response_time = (time.time() - start) * 1000
        
        # Get confidence score from indexer metrics
        confidence = 0.0
        if result_file and indexer.metrics.metrics["queries_log"]:
            latest_query = indexer.metrics.metrics["queries_log"][-1]
            confidence = latest_query.get("confidence_score", 0.0)
        
        return QueryResponse(
            success=result_file is not None,
            query=request.query,
            result_file=result_file,
            confidence_score=confidence,
            response_time_ms=round(response_time, 2),
            message="Document found successfully" if result_file else "No relevant document found"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search error: {str(e)}"
        )

@app.get("/stats", response_model=StatsResponse, tags=["Metrics"])
async def get_statistics(api_key: str = Depends(verify_api_key)):
    """
    Get API usage statistics and performance metrics
    """
    stats = metrics_tracker.get_stats()
    
    if stats["total_queries"] == 0:
        return StatsResponse(
            total_queries=0,
            successful_queries=0,
            success_rate="0%",
            avg_response_time_ms=0.0,
            avg_confidence=0.0
        )
    
    return StatsResponse(**stats)

@app.get("/recent-queries", response_model=List[RecentQuery], tags=["Metrics"])
async def get_recent_queries(
    limit: int = 10,
    api_key: str = Depends(verify_api_key)
):
    """
    Get recent queries with their metrics
    
    - **limit**: Number of recent queries to return (default: 10, max: 50)
    """
    if limit > 50:
        limit = 50
    
    recent = metrics_tracker.get_recent_queries(limit)
    
    return [RecentQuery(**q) for q in recent]

@app.post("/index", response_model=IndexResponse, tags=["Admin"])
async def index_documents(
    request: IndexRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Index a new folder of documents
    
    - **folder_path**: Path to folder containing documents to index
    """
    if not os.path.exists(request.folder_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Folder not found: {request.folder_path}"
        )
    
    if not indexer:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Indexer not initialized"
        )
    
    try:
        print(f"📂 Starting indexing of: {request.folder_path}")
        
        # Count files before indexing
        initial_count = indexer.collection.count() if indexer.collection else 0
        
        indexer.build_index(request.folder_path)
        
        # Count files after indexing
        final_count = indexer.collection.count() if indexer.collection else 0
        files_indexed = final_count - initial_count
        
        return IndexResponse(
            success=True,
            message=f"Successfully indexed documents from {request.folder_path}",
            files_indexed=files_indexed
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Indexing error: {str(e)}"
        )

@app.delete("/metrics/reset", tags=["Admin"])
async def reset_metrics(api_key: str = Depends(verify_api_key)):
    """
    Reset all metrics (admin only)
    """
    metrics_tracker.reset_metrics()
    return {"success": True, "message": "Metrics reset successfully"}

# Error Handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "detail": str(exc)
        }
    )

# Run with: uvicorn api.app:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
