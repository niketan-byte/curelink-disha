"""
Health Check Route
"""
from fastapi import APIRouter, HTTPException
from app.database import get_database
from app.schemas.chat import HealthCheckResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    Health check endpoint.
    Returns status of the application and database connection.
    """
    try:
        # Check database connection
        db = get_database()
        await db.command("ping")
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    
    status = "healthy" if db_status == "connected" else "unhealthy"
    
    if status == "unhealthy":
        raise HTTPException(status_code=503, detail="Database connection failed")
    
    return HealthCheckResponse(
        status=status,
        database=db_status,
        version="1.0.0",
    )
