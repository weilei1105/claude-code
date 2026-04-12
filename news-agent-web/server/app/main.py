"""
News Agent Web - FastAPI Backend

Production-ready FastAPI application for AI-powered report generation.
"""

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import router
from app.config import settings


# ============== Lifespan Context Manager ==============
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print("=" * 50)
    print("News Agent Web Backend Started")
    print("=" * 50)
    print(f"Server: http://{settings.server_host}:{settings.server_port}")
    print(f"Reports directory: {settings.reports_dir}")
    print(f"Claude Code: {settings.claude_code_dir}")
    print("=" * 50)
    yield
    # Shutdown
    print("News Agent Web Backend Shutdown")


# ============== FastAPI App ==============
app = FastAPI(
    title="News Agent Web - 智能报告生成器",
    description="基于 Scrapling + Claude AI 的专业报告生成系统",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ============== CORS Middleware ==============
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============== Include Routes ==============
app.include_router(router, prefix="/api")


# ============== Root Endpoint ==============
@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "News Agent Web - 智能报告生成器",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health",
    }


# ============== Main ==============
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=settings.server_host,
        port=settings.server_port,
        log_level="info",
    )
