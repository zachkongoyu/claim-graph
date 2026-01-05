"""Main FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import os

from app.config import settings
from app.database.db import init_db
from app.api import ingest, analyze, generate_claim

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting Claim Graph RCM Agent")
    
    # Create data directory if it doesn't exist
    os.makedirs("./data", exist_ok=True)
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Claim Graph RCM Agent")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Autonomous RCM agent using LangGraph and FastAPI",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ingest.router, prefix="/api/v1", tags=["ingest"])
app.include_router(analyze.router, prefix="/api/v1", tags=["analyze"])
app.include_router(generate_claim.router, prefix="/api/v1", tags=["claims"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "endpoints": {
            "ingest": "/api/v1/ingest",
            "analyze": "/api/v1/analyze",
            "generate_claim": "/api/v1/generate-claim",
        },
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
