from flask import Blueprint, request, jsonify

main_bp = Blueprint('main', __name__)

@main_bp.route('/route_request', methods=['POST'])
def route_request():
    """
    Handle routing requests.
    Expected JSON input:
    {
      "start_coords": {"lat": float, "lng": float},
      "end_coords": {"lat": float, "lng": float},
      "camera_data": [
        {"id": "cam_001", "coords": {"lat": float, "lng": float}}
      ]
    }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400
        
    start_coords = data.get('start_coords')
    end_coords = data.get('end_coords')
    camera_data = data.get('camera_data', [])
    
    if not start_coords or not end_coords:
        return jsonify({"error": "Missing start_coords or end_coords"}), 400

    # Integrate AI Logic
    from .ai_service import check_flood_status
    import asyncio
    
    # Run async function in sync Flask route
    try:
        flooded_coords = asyncio.run(check_flood_status(camera_data))
    except Exception as e:
        print(f"Error calling AI service: {e}")
        flooded_coords = []
        
    # Calculate Safe Route
    from .routing_service import get_safe_route
    
    # Note: get_safe_route might take time to download graph on first run
    path_coords = get_safe_route(start_coords, end_coords, flooded_coords)
    
    response = {
        "status": "success",
        "message": "Route calculated",
        "data": {
            "start": start_coords,
            "end": end_coords,
            "camera_count": len(camera_data),
            "flooded_coords": flooded_coords,
            "path": path_coords
        }
    }
    
    return jsonify(response), 200
