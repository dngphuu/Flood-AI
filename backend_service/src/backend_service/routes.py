"""
API routes for backend service.
"""
from flask import Blueprint, request, jsonify
import asyncio
from .logger import logger
from .ai_service import check_flood_status
from .routing_service import get_safe_route
from .camera_service import get_camera_service

main_bp = Blueprint('main', __name__)

@main_bp.route('/route_request', methods=['POST'])
def route_request():
    """
    Handle routing requests with camera IDs.
    
    Expected JSON input:
    {
      "start_coords": {"lat": float, "lng": float},
      "end_coords": {"lat": float, "lng": float},
      "camera_ids": ["cam_id_1", "cam_id_2", ...]
    }
    
    Returns:
        JSON response with route information and flooded coordinates
    """
    try:
        data = request.get_json()
        
        if not data:
            logger.warning("Received request with invalid JSON")
            return jsonify({"error": "Invalid JSON"}), 400
        
        # Extract and validate coordinates
        start_coords = data.get('start_coords')
        end_coords = data.get('end_coords')
        camera_ids = data.get('camera_ids', [])
        
        if not start_coords or not end_coords:
            logger.warning("Missing start_coords or end_coords in request")
            return jsonify({"error": "Missing start_coords or end_coords"}), 400
        
        # Validate coordinate format
        if not all(k in start_coords for k in ['lat', 'lng']):
            return jsonify({"error": "start_coords must have 'lat' and 'lng' fields"}), 400
        if not all(k in end_coords for k in ['lat', 'lng']):
            return jsonify({"error": "end_coords must have 'lat' and 'lng' fields"}), 400
        
        logger.info(f"Route request from {start_coords} to {end_coords} with {len(camera_ids)} cameras")
        
        # Validate camera IDs if provided
        flooded_coords = []
        if camera_ids:
            camera_service = get_camera_service()
            valid_ids, invalid_ids = camera_service.validate_camera_ids(camera_ids)
            
            if invalid_ids:
                logger.warning(f"Invalid camera IDs provided: {invalid_ids}")
                return jsonify({
                    "error": "Invalid camera IDs",
                    "invalid_ids": invalid_ids
                }), 400
            
            # Check flood status using AI service
            try:
                flooded_coords = asyncio.run(check_flood_status(valid_ids))
            except Exception as e:
                logger.error(f"Error calling AI service: {e}", exc_info=True)
                # Continue with empty flooded_coords (fail-safe)
                flooded_coords = []
        
        # Calculate safe route
        logger.info("Calculating safe route")
        path_coords = get_safe_route(start_coords, end_coords, flooded_coords)
        
        if not path_coords:
            logger.warning("No route found")
            return jsonify({
                "error": "No route found",
                "message": "Unable to calculate route between the given points"
            }), 404
        
        response = {
            "status": "success",
            "message": "Route calculated",
            "data": {
                "start": start_coords,
                "end": end_coords,
                "camera_count": len(camera_ids),
                "flooded_count": len(flooded_coords),
                "flooded_coords": flooded_coords,
                "path": path_coords,
                "path_length": len(path_coords)
            }
        }
        
        logger.info(f"Route calculated successfully: {len(path_coords)} waypoints, {len(flooded_coords)} flooded areas")
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Unexpected error in route_request: {e}", exc_info=True)
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500

@main_bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy"}), 200
