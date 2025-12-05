"""
API routes for the flood classification service using FastAPI.

This module defines FastAPI routers and endpoints for the AI service.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
import logging
from typing import Dict, Any

from ai_service.config import AppConfig
from ai_service.core import FloodClassifier
from ai_service.utils import preprocess_image, validate_image_file

logger = logging.getLogger(__name__)

# Create routers
router = APIRouter()
health_router = APIRouter()

# Initialize model (singleton - loaded once when module is imported)
try:
    classifier = FloodClassifier()
    logger.info("Model initialized successfully in routes module")
except Exception as e:
    logger.error(f"Failed to initialize model: {e}")
    classifier = None


# ============================================================================
# Pydantic Models
# ============================================================================

class PredictionResult(BaseModel):
    """Prediction result structure."""
    class_name: str
    class_id: int
    confidence: float
    confident: bool
    threshold: float
    probabilities: Dict[str, float]


class PredictResponse(BaseModel):
    """Response for prediction endpoint."""
    success: bool
    prediction: PredictionResult = None
    error: str = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    service: str
    version: str
    model: Dict[str, Any]


# ============================================================================
# Routes
# ============================================================================

@router.post("/predict")
async def predict(file: UploadFile = File(...)):
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
    """
    # Check if model is loaded
    if classifier is None:
        logger.error("Model not initialized")
        raise HTTPException(
            status_code=500,
            detail="Model not initialized. Please check server logs."
        )
    
    # Check if filename is empty
    if not file.filename:
        logger.warning("Empty filename in request")
        raise HTTPException(
            status_code=400,
            detail="No file selected. Please select an image file."
        )
    
    # Validate file extension
    if not validate_image_file(file.filename, AppConfig.ALLOWED_EXTENSIONS):
        logger.warning(f"Invalid file type: {file.filename}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(AppConfig.ALLOWED_EXTENSIONS)}"
        )
    
    try:
        logger.info(f"Processing image: {file.filename}")
        
        # Read file content
        content = await file.read()
        
        # Preprocess the image
        from io import BytesIO
        preprocessed = preprocess_image(BytesIO(content))
        
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
        
        logger.info(f"Prediction successful for {file.filename}: {result['predicted_label']}")
        
        return response
    
    except ValueError as e:
        # Image preprocessing errors
        logger.error(f"Image preprocessing error: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to process image: {str(e)}"
        )
    
    except Exception as e:
        # Unexpected errors
        logger.error(f"Unexpected error during prediction: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred. Please try again."
        )


@health_router.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns the service status and model information.
    """
    model_loaded = classifier is not None
    
    response = {
        "status": "healthy" if model_loaded else "degraded",
        "service": "flood-classification-ai",
        "version": AppConfig.API_VERSION,
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
    
    if not model_loaded:
        raise HTTPException(status_code=503, detail=response)
    
    return response
