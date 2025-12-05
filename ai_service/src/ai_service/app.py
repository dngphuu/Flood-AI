"""
Development server entry point.

Run this script directly for development:
    python -m ai_service.app
    
Or use the CLI command:
    ai-service
"""

from ai_service import app

if __name__ == "__main__":
    import uvicorn
    from ai_service.config import AppConfig
    
    uvicorn.run(
        "ai_service:app",
        host=AppConfig.HOST,
        port=AppConfig.PORT,
        reload=AppConfig.DEBUG,
        workers=AppConfig.WORKERS
    )
