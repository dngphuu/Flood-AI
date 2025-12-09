"""
GraphHopper-based routing service with dynamic flood avoidance.
"""
import requests
from typing import List
from .logger import logger
from . import config


def get_safe_route(start_point: List[float], end_point: List[float], flooded_points: List[List[float]] = None) -> List[List[float]]:
    """
    Calculate a safe route avoiding flooded areas using GraphHopper API.
    
    Args:
        start_point: Starting coordinates as [lat, lon]
        end_point: Ending coordinates as [lat, lon]
        flooded_points: List of flooded coordinates [[lat, lon], ...]. Defaults to empty list.
        
    Returns:
        List of coordinates [[lat, lon], ...] representing the route path for Leaflet rendering.
        Returns empty list on error.
    """
    if flooded_points is None:
        flooded_points = []
    
    try:
        # Validate API key
        if not config.GRAPHHOPPER_API_KEY:
            logger.error("GraphHopper API key is not configured. Please set GRAPHHOPPER_API_KEY in .env file")
            return []
        
        # Validate input coordinates
        if not _validate_coords(start_point) or not _validate_coords(end_point):
            logger.error("Invalid start or end coordinates")
            return []
        
        for flood_point in flooded_points:
            if not _validate_coords(flood_point):
                logger.warning(f"Invalid flooded point: {flood_point}, skipping")
        
        # Build request parameters
        params = {
            "key": config.GRAPHHOPPER_API_KEY,
            "profile": "car",
            "locale": "vi",
            "points_encoded": "false"
        }
        
        # Add route points (GraphHopper expects [lat, lon] format in the point parameter)
        params["point"] = [
            f"{start_point[0]},{start_point[1]}",
            f"{end_point[0]},{end_point[1]}"
        ]
        
        # Add blocked areas for flooded points (block 50m radius around each point)
        # Note: block_area works with both free and paid tiers
        if flooded_points:
            logger.info(f"Blocking {len(flooded_points)} flooded areas with 50m radius")
            block_areas = []
            for flood_point in flooded_points:
                if _validate_coords(flood_point):
                    # Format: lat,lon,radius_in_meters
                    block_areas.append(f"{flood_point[0]},{flood_point[1]},50")
            
            if block_areas:
                params["block_area"] = block_areas
        else:
            logger.info("No flooded areas to avoid, calculating normal route")
        
        # Make API request
        logger.debug(f"Requesting route from {start_point} to {end_point}")
        response = requests.get(config.GRAPHHOPPER_BASE_URL, params=params, timeout=30)
        
        # Check response status
        if response.status_code != 200:
            logger.error(f"GraphHopper API error: {response.status_code} - {response.text}")
            return []
        
        # Parse response
        data = response.json()
        
        # Check for API errors
        if "message" in data:
            logger.error(f"GraphHopper API returned error: {data['message']}")
            return []
        
        # Extract coordinates from the first path
        if "paths" not in data or len(data["paths"]) == 0:
            logger.error("No paths found in GraphHopper response")
            return []
        
        path = data["paths"][0]
        
        # GraphHopper returns coordinates as [lon, lat] in points.coordinates
        # We need to convert to [lat, lon] for Leaflet
        if "points" not in path or "coordinates" not in path["points"]:
            logger.error("Invalid response structure from GraphHopper")
            return []
        
        coordinates = path["points"]["coordinates"]
        
        # Convert from [lon, lat] to [lat, lon]
        route_coords = [[coord[1], coord[0]] for coord in coordinates]
        
        logger.info(f"Route calculated successfully with {len(route_coords)} waypoints")
        logger.debug(f"Route distance: {path.get('distance', 0):.2f}m, time: {path.get('time', 0)/1000:.2f}s")
        
        return route_coords
        
    except requests.exceptions.Timeout:
        logger.error("GraphHopper API request timed out")
        return []
    except requests.exceptions.ConnectionError:
        logger.error("Failed to connect to GraphHopper API. Check your internet connection")
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"GraphHopper API request failed: {e}")
        return []
    except ValueError as e:
        logger.error(f"Failed to parse GraphHopper API response: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error in routing: {e}", exc_info=True)
        return []


def _validate_coords(coords: List[float]) -> bool:
    """
    Validate coordinates format and values.
    
    Args:
        coords: Coordinates as [lat, lon]
        
    Returns:
        True if valid, False otherwise
    """
    if not isinstance(coords, list) or len(coords) != 2:
        return False
    
    lat, lon = coords
    
    # Check if values are numbers
    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
        return False
    
    # Check valid ranges
    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        return False
    
    return True
