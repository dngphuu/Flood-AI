"""API package for AI Service."""

from ai_service.api.routes import api_bp, health_bp

__all__ = ["api_bp", "health_bp"]
