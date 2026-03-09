"""
Main FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import sys

load_dotenv()

print(f"Python: {sys.version}", flush=True)
print(f"PORT: {os.getenv('PORT', 'not set')}", flush=True)

app = FastAPI(title="DocuChat AI", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/health")
async def health():
    return {"status": "healthy"}

# Import API router
try:
    from api.endpoints import router as api_router
    app.include_router(api_router, prefix="/api", tags=["API"])
    print("✅ API router loaded", flush=True)
except Exception as e:
    print(f"❌ API router error: {e}", flush=True)

# Frontend serving
frontend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist")
print(f"Frontend: {frontend_path}, exists: {os.path.exists(frontend_path)}", flush=True)

if os.path.exists(frontend_path):
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse, HTMLResponse

    assets_path = os.path.join(frontend_path, "assets")
    if os.path.exists(assets_path):
        app.mount("/assets", StaticFiles(directory=assets_path), name="assets")
        print(f"✅ Assets mounted", flush=True)

    # Read index.html into memory once at startup (avoid file I/O on every request)
    index_html_content = ""
    index_path = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r") as f:
            index_html_content = f.read()
        print(f"✅ index.html loaded ({len(index_html_content)} bytes)", flush=True)

    @app.get("/", response_class=HTMLResponse)
    async def serve_index():
        return HTMLResponse(content=index_html_content)

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/") or full_path in ("health", "docs", "redoc", "openapi.json"):
            from fastapi import HTTPException
            raise HTTPException(status_code=404)
        
        file_path = os.path.join(frontend_path, full_path)
        if full_path and os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        
        return HTMLResponse(content=index_html_content)
else:
    @app.get("/")
    async def root():
        return {"status": "online", "message": "DocuChat AI API", "docs": "/docs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
