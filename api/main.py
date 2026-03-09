"""
Main FastAPI Application - Minimal test version to debug Railway 502
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import sys

print(f"Python version: {sys.version}", flush=True)
print(f"Working directory: {os.getcwd()}", flush=True)
print(f"PORT env: {os.getenv('PORT', 'not set')}", flush=True)

app = FastAPI(title="DocuChat AI", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple test routes - no file serving, no imports
@app.get("/")
async def root():
    return {"status": "online", "message": "DocuChat AI API"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

# Try importing the API router - catch errors
try:
    from api.endpoints import router as api_router
    app.include_router(api_router, prefix="/api", tags=["API"])
    print("✅ API router loaded", flush=True)
except Exception as e:
    print(f"❌ Failed to load API router: {e}", flush=True)

# Try serving frontend - catch errors  
try:
    frontend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist")
    if os.path.exists(frontend_path):
        from fastapi.staticfiles import StaticFiles
        from fastapi.responses import FileResponse
        
        assets_path = os.path.join(frontend_path, "assets")
        if os.path.exists(assets_path):
            app.mount("/assets", StaticFiles(directory=assets_path), name="assets")
        
        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            if full_path.startswith("api/") or full_path in ("health", "docs", "redoc"):
                from fastapi import HTTPException
                raise HTTPException(status_code=404)
            file_path = os.path.join(frontend_path, full_path)
            if full_path and os.path.exists(file_path) and os.path.isfile(file_path):
                return FileResponse(file_path)
            index_path = os.path.join(frontend_path, "index.html")
            if os.path.exists(index_path):
                return FileResponse(index_path)
            return {"error": "Frontend not built"}
        print(f"✅ Frontend serving enabled from {frontend_path}", flush=True)
    else:
        print(f"⚠️ Frontend not found at {frontend_path}", flush=True)
except Exception as e:
    print(f"❌ Frontend setup error: {e}", flush=True)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
