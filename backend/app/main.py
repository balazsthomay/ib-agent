"""
FastAPI application entry point.
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan context manager.
    Handles startup and shutdown events.
    """
    # Startup: Initialize services
    print("🚀 Starting IB Agent API...")
    print(f"Environment: {settings.environment}")
    print(f"Debug mode: {settings.debug}")

    # TODO: Initialize database connections
    # TODO: Initialize Redis connection
    # TODO: Initialize LLM clients

    yield

    # Shutdown: Cleanup resources
    print("👋 Shutting down IB Agent API...")
    # TODO: Close database connections
    # TODO: Close Redis connection


app = FastAPI(
    title="IB Agent API",
    description="AI Platform for Small-Mid Cap Investment Banks",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from app.api.routes import chat, health, projects

app.include_router(health.router)
app.include_router(projects.router, prefix="/api")
app.include_router(chat.router, prefix="/api")


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": "IB Agent API", "version": "0.1.0"}
