import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .api.routes import router
from .config import FRONTEND_DIST_DIR
from .db.session import init_db


@asynccontextmanager
async def lifespan(_app: FastAPI):
    print("=" * 60)
    print("  EnterpriseFlow AI — Multi-Agent Onboarding Platform")
    print("=" * 60)
    init_db()
    print("[System] Ready on port 8000")
    yield
    print("[System] Shutting down.")


app = FastAPI(
    title="EnterpriseFlow AI — Multi-Agent Onboarding Platform",
    description="Unified LangGraph Multi-Agent Orchestrator for Employee Onboarding",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS configuration for seamless frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include core multi-agent API endpoints
app.include_router(router)

# Mount static files and SPA if frontend has been built
if FRONTEND_DIST_DIR.exists() and (FRONTEND_DIST_DIR / "index.html").exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST_DIR / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Allow API requests through
        if full_path.startswith("api"):
            return None
        file_path = FRONTEND_DIST_DIR / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(FRONTEND_DIST_DIR / "index.html"))
else:
    @app.get("/")
    def root():
        return {
            "platform": "EnterpriseFlow AI",
            "version": "2.0.0",
            "status": "Online",
            "agents": [
                "Supervisor Orchestrator",
                "Document Verification Agent",
                "IT Provisioning Agent",
                "Team Allocation Agent",
                "Training & Orientation Agent",
                "Monitoring & Audit Agent",
            ],
            "api_documentation": "/docs",
        }
