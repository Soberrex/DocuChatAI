"""
Main FastAPI Application
Integrates all endpoints for RAG Chatbot
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import os
import logging
import traceback

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import routers
from api.endpoints import router as api_router

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

# Include API routes
app.include_router(api_router, prefix="/api", tags=["API"])

# Health check (must be before SPA catch-all)
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Root route (explicit, before catch-all)
@app.get("/")
async def root():
    """Serve frontend index.html or API info"""
    try:
        from fastapi.responses import FileResponse
        frontend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist")
        index_path = os.path.join(frontend_path, "index.html")
        logger.info(f"Root route - frontend_path: {frontend_path}, exists: {os.path.exists(frontend_path)}")
        logger.info(f"Root route - index.html: {index_path}, exists: {os.path.exists(index_path)}")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return JSONResponse(content={
            "message": "DocuChat AI API",
            "status": "online",
            "frontend_built": False,
            "frontend_path": frontend_path,
            "docs": "/docs"
        })
    except Exception as e:
        logger.error(f"Root route error: {traceback.format_exc()}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

# Serve frontend static files (only if directory exists - for production)
frontend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist")
logger.info(f"Frontend path: {frontend_path}, exists: {os.path.exists(frontend_path)}")

if os.path.exists(frontend_path):
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse

    # Mount static assets (JS, CSS, images) - only if assets dir exists
    assets_path = os.path.join(frontend_path, "assets")
    if os.path.exists(assets_path):
        app.mount("/assets", StaticFiles(directory=assets_path), name="assets")
        logger.info(f"Mounted /assets from {assets_path}")
    else:
        logger.warning(f"Assets directory not found: {assets_path}")
    
    # Catch-all route for SPA (client-side routing)
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        try:
            # Allow API and health requests to pass through
            if full_path.startswith("api/") or full_path in ("health", "docs", "redoc", "openapi.json"):
                raise HTTPException(status_code=404, detail="Not Found")
                
            # Check if file exists in root (e.g. favicon.ico, robots.txt)
            file_path = os.path.join(frontend_path, full_path)
            if os.path.exists(file_path) and os.path.isfile(file_path):
                return FileResponse(file_path)
                
            # Fallback to index.html for React routing
            index_path = os.path.join(frontend_path, "index.html")
            if os.path.exists(index_path):
                return FileResponse(index_path)
            raise HTTPException(status_code=404, detail="Frontend not built")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"SPA route error for '{full_path}': {traceback.format_exc()}")
            return JSONResponse(content={"error": str(e)}, status_code=500)
else:
    logger.warning(f"Frontend dist not found at {frontend_path}")
    
    @app.get("/{full_path:path}")
    async def no_frontend(full_path: str):
        return JSONResponse(content={
            "message": "DocuChat AI API",
            "status": "online",
            "frontend_built": False,
            "docs": "/docs"
        })

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "detail": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )
