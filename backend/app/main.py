"""
Curelink Mini AI Health Coach - FastAPI Application

Main entry point for the backend API.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import connect_to_mongodb, close_mongodb_connection
from app.api.routes import health_router, user_router, chat_router, whatsapp_webhook_router
from app.api.routes.websocket import router as websocket_router
from app.middleware.error_handler import ErrorHandlerMiddleware
from app.middleware.rate_limiter import RateLimiterMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting Curelink Mini AI Health Coach...")
    
    try:
        await connect_to_mongodb()
        logger.info("MongoDB connected successfully")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    await close_mongodb_connection()


# Create FastAPI app
app = FastAPI(
    title="Curelink Mini AI Health Coach",
    description="WhatsApp-like AI health coach powered by LLM with long-term memory",
    version="1.0.0",
    lifespan=lifespan,
)

# Get settings
settings = get_settings()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list + ["*"],  # Allow all for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(RateLimiterMiddleware, rate_limit_paths=["/api/messages"])

# Include routers
app.include_router(health_router)
app.include_router(user_router)
app.include_router(chat_router)
app.include_router(websocket_router)
app.include_router(whatsapp_webhook_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Curelink Mini AI Health Coach API",
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
