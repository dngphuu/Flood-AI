"""
API routes for the flood classification service.

This module defines Flask blueprints and endpoints for the AI service.
"""

from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import logging
from typing import Dict, Any

from ai_service.config import FlaskConfig
from ai_service.core import FloodClassifier
from ai_service.utils import preprocess_image, validate_image_file

logger = logging.getLogger(__name__)

# Create blueprint
api_bp = Blueprint("api", __name__, url_prefix=FlaskConfig.API_PREFIX)

# Initialize model (singleton - loaded once when module is imported)
try:
    classifier = FloodClassifier()
    logger.info("Model initialized successfully in routes module")
except Exception as e:
    logger.error(f"Failed to initialize model: {e}")
    classifier = None


@api_bp.route("/predict", methods=["POST"])
def predict():
    """
    Image classification endpoint.
    
    Accepts an image file via multipart/form-data and returns classification results.
    
    Request:
        POST /api/v1/predict
        Content-Type: multipart/form-data
        Body: file=<image_file>
    
    Response:
        {
            "success": true,
            "prediction": {
                "class": "flood",
                "class_id": 1,
                "confidence": 0.87,
                "confident": true,
                "threshold": 0.7,
                "probabilities": {
                    "dry_road": 0.13,
                    "flood": 0.87
                }
            }
        }
    
    Error Responses:
        400: Bad request (no file, invalid file type)
        500: Server error (model not loaded, inference failed)
    """
    # Check if model is loaded
    if classifier is None:
        logger.error("Model not initialized")
        return jsonify({
            "success": False,
            "error": "Model not initialized. Please check server logs."
        }), 500
    
    # Check if file is present in request
    if "file" not in request.files:
        logger.warning("No file provided in request")
        return jsonify({
            "success": False,
            "error": "No file provided. Please upload an image file."
        }), 400
    
    file = request.files["file"]
    
    # Check if filename is empty
    if file.filename == "":
        logger.warning("Empty filename in request")
        return jsonify({
            "success": False,
            "error": "No file selected. Please select an image file."
        }), 400
    
    # Validate file extension
    if not validate_image_file(file.filename, FlaskConfig.ALLOWED_EXTENSIONS):
        logger.warning(f"Invalid file type: {file.filename}")
        return jsonify({
            "success": False,
            "error": f"Invalid file type. Allowed types: {', '.join(FlaskConfig.ALLOWED_EXTENSIONS)}"
        }), 400
    
    try:
        # Secure the filename
        filename = secure_filename(file.filename)
        logger.info(f"Processing image: {filename}")
        
        # Preprocess the image
        # file.stream is a file-like object that can be passed directly
        preprocessed = preprocess_image(file.stream)
        
        # Run prediction
        result = classifier.predict(preprocessed)
        
        # Build response
        response = {
            "success": True,
            "prediction": {
                "class": result["predicted_label"],
                "class_id": result["predicted_class"],
                "confidence": round(result["confidence"], 4),
                "confident": result["confident"],
                "threshold": result["threshold"],
                "probabilities": {
                    label: round(prob, 4)
                    for label, prob in result["probabilities"].items()
                }
            }
        }
        
        logger.info(f"Prediction successful for {filename}: {result['predicted_label']}")
        
        return jsonify(response), 200
    
    except ValueError as e:
        # Image preprocessing errors
        logger.error(f"Image preprocessing error: {e}")
        return jsonify({
            "success": False,
            "error": f"Failed to process image: {str(e)}"
        }), 400
    
    except Exception as e:
        # Unexpected errors
        logger.error(f"Unexpected error during prediction: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": "An unexpected error occurred. Please try again."
        }), 500


# Health check endpoint (not under /api/v1 prefix)
health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health_check():
    """
    Health check endpoint.
    
    Returns the service status and model information.
    
    Response:
        {
            "status": "healthy",
            "service": "flood-classification-ai",
            "model": {
                "loaded": true,
                "model_info": {...}
            }
        }
    """
    model_loaded = classifier is not None
    
    response = {
        "status": "healthy" if model_loaded else "degraded",
        "service": "flood-classification-ai",
        "version": FlaskConfig.API_VERSION,
        "model": {
            "loaded": model_loaded
        }
    }
    
    # Add model info if available
    if model_loaded:
        try:
            response["model"]["info"] = classifier.get_model_info()
        except Exception as e:
            logger.error(f"Failed to get model info: {e}")
            response["model"]["info_error"] = str(e)
    
    status_code = 200 if model_loaded else 503
    
    return jsonify(response), status_code
