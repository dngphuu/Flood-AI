"""
Development server entry point.

Run this script directly for development:
    python -m ai_service.app
    
Or use the CLI command:
    ai-service
"""

from ai_service import create_app

# Create the Flask application
app = create_app()

if __name__ == "__main__":
    from ai_service.config import FlaskConfig
    
    app.run(
        host=FlaskConfig.HOST,
        port=FlaskConfig.PORT,
        debug=FlaskConfig.DEBUG
    )
