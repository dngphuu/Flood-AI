"""API package for AI Service."""

from ai_service.api.routes import router, health_router

__all__ = ["router", "health_router"]
