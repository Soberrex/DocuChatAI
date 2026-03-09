"""
Main FastAPI Application
Integrates all endpoints for RAG Chatbot
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from dotenv import load_dotenv
import os
import logging
import traceback

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import routers
from api.endpoints import router as api_router
from src.database import init_db

# Initialize FastAPI app
app = FastAPI(
    title="DocuChat AI - RAG Chatbot API",
    description="Enhanced RAG system with auto-summaries, source citations, and chart generation",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database tables on startup
@app.on_event("startup")
async def startup_event():
    try:
        init_db()
        logger.info("Database tables initialized")
    except Exception as e:
        logger.error(f"Database init failed: {e}")

# Include API routes
app.include_router(api_router, prefix="/api", tags=["API"])

# Health check (must be before SPA catch-all)
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Frontend serving
frontend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist")
logger.info(f"Frontend path: {frontend_path}, exists: {os.path.exists(frontend_path)}")

if os.path.exists(frontend_path):
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse

    # Read index.html into memory at startup
    index_html_content = ""
    index_path = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r") as f:
            index_html_content = f.read()
        logger.info(f"index.html loaded ({len(index_html_content)} bytes)")

    # Mount static assets
    assets_path = os.path.join(frontend_path, "assets")
    if os.path.exists(assets_path):
        app.mount("/assets", StaticFiles(directory=assets_path), name="assets")
        logger.info(f"Assets mounted from {assets_path}")

    @app.get("/", response_class=HTMLResponse)
    async def serve_index():
        return HTMLResponse(content=index_html_content)

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Let API, health, and docs routes pass through
        if full_path.startswith("api/") or full_path in ("health", "docs", "redoc", "openapi.json"):
            raise HTTPException(status_code=404, detail="Not Found")

        # Serve static files from frontend dist
        file_path = os.path.join(frontend_path, full_path)
        if full_path and os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)

        # Fallback to index.html for React routing
        return HTMLResponse(content=index_html_content)
else:
    logger.warning(f"Frontend not found at {frontend_path}")

    @app.get("/")
    async def root():
        return {"status": "online", "message": "DocuChat AI API", "docs": "/docs"}

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {traceback.format_exc()}")
    return JSONResponse(status_code=500, content={"error": str(exc)})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )
