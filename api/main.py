"""
Main FastAPI Application
Integrates all endpoints for RAG Chatbot
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Import routers
from api.endpoints import router as api_router

load_dotenv()

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
    allow_origins=["*"],  # In production, specify allowed origins
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

# Serve frontend static files (only if directory exists - for production)
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")

if os.path.exists(frontend_path):
    # Mount static assets (JS, CSS, images) - only if assets dir exists
    assets_path = os.path.join(frontend_path, "assets")
    if os.path.exists(assets_path):
        app.mount("/assets", StaticFiles(directory=assets_path), name="assets")
    
    # Catch-all route for SPA (client-side routing)
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Allow API and health requests to pass through
        if full_path.startswith("api/") or full_path == "health":
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )
