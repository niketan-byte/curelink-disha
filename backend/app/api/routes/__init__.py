"""
Curelink Mini AI Health Coach - API Routes Package
"""
from app.api.routes.health import router as health_router
from app.api.routes.user import router as user_router
from app.api.routes.chat import router as chat_router
from app.api.routes.whatsapp_webhook import router as whatsapp_webhook_router

__all__ = [
    "health_router",
    "user_router",
    "chat_router",
    "whatsapp_webhook_router",
]
