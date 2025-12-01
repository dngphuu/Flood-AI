"""
AI Service for Flood Image Classification.

This package provides a Flask-based microservice for classifying images
as flooded or non-flooded using an ONNX model.
"""

from flask import Flask
import logging.config

from ai_service.config import FlaskConfig, LOGGING_CONFIG
from ai_service.api import api_bp, health_bp

__version__ = "0.1.0"


def create_app() -> Flask:
    """
    Flask application factory.
    
    Creates and configures the Flask application with all blueprints
    and error handlers.
    
    Returns:
        Flask: Configured Flask application instance
    
    Example:
        >>> from ai_service import create_app
        >>> app = create_app()
        >>> app.run(host="0.0.0.0", port=5000)
    """
    # Configure logging
    logging.config.dictConfig(LOGGING_CONFIG)
    logger = logging.getLogger(__name__)
    
    # Create Flask app
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(FlaskConfig)
    
    logger.info("Initializing AI Service application")
    logger.info(f"API Version: {FlaskConfig.API_VERSION}")
    logger.info(f"Debug Mode: {FlaskConfig.DEBUG}")
    
    # Register blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint(api_bp)
    
    logger.info("Blueprints registered")
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        return {
            "success": False,
            "error": "Endpoint not found",
            "status_code": 404
        }, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        logger.error(f"Internal server error: {error}")
        return {
            "success": False,
            "error": "Internal server error",
            "status_code": 500
        }, 500
    
    @app.errorhandler(413)
    def request_entity_too_large(error):
        """Handle file too large errors."""
        return {
            "success": False,
            "error": f"File too large. Maximum size: {FlaskConfig.MAX_CONTENT_LENGTH // (1024 * 1024)} MB",
            "status_code": 413
        }, 413
    
    # Root route for basic info
    @app.route("/")
    def index():
        """Root endpoint with service information."""
        return {
            "service": "Flood Classification AI Service",
            "version": __version__,
            "api_version": FlaskConfig.API_VERSION,
            "endpoints": {
                "health": "/health",
                "predict": f"{FlaskConfig.API_PREFIX}/predict"
            }
        }, 200
    
    logger.info("Application initialized successfully")
    
    return app


def main():
    """
    Main entry point for running the service.
    
    This function is called when running via the CLI command 'ai-service'.
    """
    app = create_app()
    
    print(f"\n{'='*60}")
    print(f"🌊 Flood Classification AI Service")
    print(f"{'='*60}")
    print(f"Server starting on http://{FlaskConfig.HOST}:{FlaskConfig.PORT}")
    print(f"API Version: {FlaskConfig.API_VERSION}")
    print(f"Debug Mode: {FlaskConfig.DEBUG}")
    print(f"\nEndpoints:")
    print(f"  - Health Check: http://{FlaskConfig.HOST}:{FlaskConfig.PORT}/health")
    print(f"  - Prediction:   http://{FlaskConfig.HOST}:{FlaskConfig.PORT}{FlaskConfig.API_PREFIX}/predict")
    print(f"{'='*60}\n")
    
    app.run(
        host=FlaskConfig.HOST,
        port=FlaskConfig.PORT,
        debug=FlaskConfig.DEBUG
    )


if __name__ == "__main__":
    main()
