"""
Flask application factory and startup configuration.
"""
from flask import Flask
from .routes import main_bp
from .logger import logger, setup_logging
from .routing_service import load_or_download_graph
from .camera_service import get_camera_service

def create_app():
    """
    Create and configure Flask application.
    
    Returns:
        Flask: Configured Flask application instance
    """
    # Setup logging first
    setup_logging()
    logger.info("Starting backend service")
    
    app = Flask(__name__)
    
    # Register blueprints
    app.register_blueprint(main_bp)
    
    # Pre-load resources on startup
    with app.app_context():
        try:
            logger.info("Pre-loading camera dataset...")
            camera_service = get_camera_service()
            logger.info(f"Loaded {len(camera_service.cameras)} cameras")
            
            logger.info("Pre-loading map graph...")
            load_or_download_graph()
            logger.info("Map graph loaded successfully")
            
        except Exception as e:
            logger.error(f"Error during startup: {e}", exc_info=True)
            raise
    
    logger.info("Backend service startup complete")
    return app

def main():
    """Main entry point for the application."""
    app = create_app()
    logger.info("Starting Flask server on http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == "__main__":
    main()
