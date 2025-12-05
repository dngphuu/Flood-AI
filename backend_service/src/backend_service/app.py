"""
FastAPI application factory and startup configuration.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from .routes import router
from .logger import logger, setup_logging
from .routing_service import load_or_download_graph
from .camera_service import get_camera_service
from .flood_state import get_flood_state_manager
from .scheduler import init_scheduler, start_scheduler, stop_scheduler, trigger_immediate_flood_check
import asyncio


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager for startup and shutdown events.
    """
    # Startup
    setup_logging()
    logger.info("Starting backend service")
    
    try:
        # Pre-load camera dataset
        logger.info("Pre-loading camera dataset...")
        camera_service = get_camera_service()
        logger.info(f"Loaded {len(camera_service.cameras)} cameras")
        
        # Initialize flood state manager with camera data
        logger.info("Initializing flood state manager...")
        flood_manager = get_flood_state_manager()
        flood_manager.initialize_cameras(camera_service.cameras)
        
        # Pre-load map graph
        logger.info("Pre-loading map graph...")
        load_or_download_graph()
        logger.info("Map graph loaded successfully")
        
        # Initialize and start scheduler
        logger.info("Starting background scheduler...")
        init_scheduler()
        start_scheduler()
        logger.info("All cameras initialized as dry. First flood check will run after 60 minutes.")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}", exc_info=True)
        raise
    
    logger.info("Backend service startup complete")
    
    yield  # Application runs here
    
    # Shutdown
    logger.info("Shutting down backend service...")
    stop_scheduler()
    logger.info("Backend service shutdown complete")


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Returns:
        FastAPI: Configured FastAPI application instance
    """
    app = FastAPI(
        title="Flood AI Backend Service",
        description="Backend service for flood detection and safe routing",
        version="0.2.0",
        lifespan=lifespan
    )
    
    # Include routers
    app.include_router(router)
    
    return app


# Create the app instance
app = create_app()


def main():
    """Main entry point for the application."""
    import uvicorn
    logger.info("Starting Uvicorn server on http://0.0.0.0:5000")
    uvicorn.run(
        "backend_service:app",
        host="0.0.0.0",
        port=5000,
        reload=True
    )


if __name__ == "__main__":
    main()
