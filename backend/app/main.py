"""
FastAPI Application Entry Point
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.logging import log
from app.api.routes import search, chat, subscriptions, health, agentos


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Reject requests without a valid X-API-Key header."""

    OPEN_PATHS = {"/", "/docs", "/openapi.json", "/redoc"}

    async def dispatch(self, request: Request, call_next):
        if not settings.api_key:
            return await call_next(request)
        if request.url.path in self.OPEN_PATHS:
            return await call_next(request)
        key = request.headers.get("x-api-key")
        if key != settings.api_key:
            return Response(content='{"detail":"Forbidden"}', status_code=403, media_type="application/json")
        return await call_next(request)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    log.info("Starting TED Bot API")
    log.info(f"Environment: {settings.environment}")
    log.info(f"TED API: {settings.ted_api_url}")
    log.info(f"Ollama API: {settings.ollama_api_url}")
    log.info(f"Supabase: {settings.supabase_url}")
    
    yield
    
    log.info("Shutting down TED Bot API")


# Create FastAPI app
app = FastAPI(
    title="TED Bot API",
    description="AI-powered agent for discovering and analyzing TED tender notices",
    version="0.1.0",
    lifespan=lifespan,
)

# API key middleware (must be added before CORS so CORS preflight still works)
app.add_middleware(APIKeyMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(search.router, prefix="/api/v1", tags=["search"])
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
app.include_router(subscriptions.router, prefix="/api/v1", tags=["subscriptions"])

# AgentOS API for agent-ui frontend
app.include_router(agentos.router, tags=["agentos"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "TED Bot API",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
    }
