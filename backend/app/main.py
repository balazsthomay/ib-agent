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
    description="""
    ## AI Platform for Small-Mid Cap Investment Banks

    Automate target screening, trading comps, and public information books using AI.

    ### Features
    - **Project Management**: Create and manage investment banking projects
    - **AI Chat**: Natural language interface for all tasks
    - **Trading Comps**: Automated comparable company analysis
    - **Public Info Books**: Comprehensive company research reports
    - **Target Screening**: AI-powered M&A target discovery

    ### Authentication
    All protected endpoints require Bearer token authentication via Clerk.
    """,
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "health", "description": "Health check and system status endpoints"},
        {"name": "projects", "description": "Project management operations"},
        {"name": "chat", "description": "AI chat and conversation endpoints"},
    ],
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


@app.get("/", tags=["health"])
async def root() -> dict[str, str]:
    """
    Root endpoint - API welcome message.

    Returns basic API information and version.
    """
    return {"message": "IB Agent API", "version": "0.1.0"}
