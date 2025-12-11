"""
OpenRouteService-based routing service with dynamic flood avoidance.
Uses avoid_polygons parameter to route around flooded areas.
"""
import requests
import math
from typing import List, Dict
from .logger import logger
from . import config


def _create_circle_polygon(lat: float, lon: float, radius_meters: int, num_points: int = 16) -> List[List[float]]:
    """
    Create a GeoJSON polygon representing a circle.
    
    Args:
        lat: Center latitude
        lon: Center longitude
        radius_meters: Radius in meters
        num_points: Number of points to approximate the circle (default 16)
        
    Returns:
        List of [lon, lat] coordinates forming a polygon (GeoJSON format uses lon,lat order)
    """
    # Earth radius in meters
    R = 6378137
    
    # Convert radius to angular distance
    angular_distance = radius_meters / R
    
    coordinates = []
    for i in range(num_points + 1):  # +1 to close the polygon
        angle = 2 * math.pi * i / num_points
        
        # Calculate point on circle
        lat_offset = angular_distance * math.cos(angle)
        lon_offset = angular_distance * math.sin(angle) / math.cos(math.radians(lat))
        
        point_lat = lat + math.degrees(lat_offset)
        point_lon = lon + math.degrees(lon_offset)
        
        # GeoJSON uses [lon, lat] order!
        coordinates.append([point_lon, point_lat])
    
    return coordinates


def get_safe_route(start_point: List[float], end_point: List[float], flooded_points: List[List[float]] = None) -> List[List[float]]:
    """
    Calculate a safe route avoiding flooded areas using OpenRouteService API.
    
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
        if not config.OPENROUTE_API_KEY:
            logger.error("OpenRouteService API key is not configured. Please set OPENROUTE_API_KEY in .env file")
            logger.error("Sign up at https://openrouteservice.org/dev/#/signup to get a free API key")
            return []
        
        # Validate input coordinates
        if not _validate_coords(start_point) or not _validate_coords(end_point):
            logger.error("Invalid start or end coordinates")
            return []
        
        # Build request body (OpenRouteService uses POST with JSON body)
        body = {
            "coordinates": [
                [start_point[1], start_point[0]],  # ORS uses [lon, lat] format
                [end_point[1], end_point[0]]
            ],
            "language": "vi",
            "instructions": False,  # We don't need turn-by-turn instructions
            "geometry_simplify": False,  # Get full geometry, not simplified
            "elevation": False  # No elevation data needed
        }
        
        # Add avoid_polygons for flooded areas
        if flooded_points:
            block_radius = config.FLOOD_BLOCK_RADIUS_METERS
            logger.info(f"Creating avoid polygons for {len(flooded_points)} flooded areas with {block_radius}m radius")
            
            # Convert flooded points to GeoJSON circle polygons
            polygons = []
            for flood_point in flooded_points:
                if _validate_coords(flood_point):
                    circle_coords = _create_circle_polygon(
                        lat=flood_point[0],
                        lon=flood_point[1],
                        radius_meters=block_radius
                    )
                    polygons.append(circle_coords)
            
            if polygons:
                # Create GeoJSON MultiPolygon for avoid_polygons parameter
                # Format: {"type": "MultiPolygon", "coordinates": [[[[lon,lat],...]]]}
                body["options"] = {
                    "avoid_polygons": {
                        "type": "MultiPolygon",
                        "coordinates": [[polygon] for polygon in polygons]
                    }
                }
        else:
            logger.info("No flooded areas to avoid, calculating normal route")
        
        # Make API request to OpenRouteService
        headers = {
            "Authorization": config.OPENROUTE_API_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        logger.info(f"Requesting route from {start_point} to {end_point}")
        
        response = requests.post(
            config.OPENROUTE_BASE_URL,
            json=body,
            headers=headers,
            timeout=30
        )
        
        # Check response status
        if response.status_code != 200:
            error_detail = response.text
            try:
                error_json = response.json()
                error_detail = error_json.get("error", {}).get("message", error_detail)
            except:
                pass
            logger.error(f"OpenRouteService API error ({response.status_code}): {error_detail}")
            return []
        
        # Parse response
        data = response.json()
        
        # Check for errors in response
        if "error" in data:
            logger.error(f"OpenRouteService returned error: {data['error']}")
            return []
        
        # OpenRouteService returns 'routes' array
        if "routes" not in data or len(data["routes"]) == 0:
            logger.error("No routes found in OpenRouteService response")
            return []
        
        # Get first route from routes array  
        route = data["routes"][0]
        
        # Extract geometry from route
        if "geometry" not in route:
            logger.error("Invalid response structure from OpenRouteService - no geometry")
            logger.error(f"Route keys: {list(route.keys())}")
            return []
        
        geometry = route["geometry"]
        
        # OpenRouteService can return geometry in different formats:
        # 1. Encoded polyline string (default)
        # 2. GeoJSON geometry object with coordinates array
        # 3. Direct coordinates array (when geometry_simplify=false)
        
        if isinstance(geometry, str):
            # Encoded polyline - need to decode it
            # Install: pip install polyline
            try:
                import polyline
                # Decode polyline to get [(lat, lon), ...] pairs
                decoded = polyline.decode(geometry)
                # Convert to [[lat, lon], ...] format
                route_coords = [[lat, lon] for lat, lon in decoded]
                logger.info(f"Decoded polyline to {len(route_coords)} coordinates")
            except ImportError:
                logger.error("polyline library not installed. Install with: pip install polyline")
                logger.error("Alternatively, request full coordinates from API")
                return []
            except Exception as e:
                logger.error(f"Failed to decode polyline: {e}")
                return []
        elif isinstance(geometry, dict) and "coordinates" in geometry:
            # GeoJSON geometry object
            coordinates = geometry["coordinates"]
            # Convert from [lon, lat] to [lat, lon] for Leaflet
            route_coords = [[coord[1], coord[0]] for coord in coordinates]
        elif isinstance(geometry, list):
            # Direct coordinates array
            # Check if first element is a coordinate pair
            if len(geometry) > 0 and isinstance(geometry[0], list) and len(geometry[0]) == 2:
                # Convert from [lon, lat] to [lat, lon]
                route_coords = [[coord[1], coord[0]] for coord in geometry]
            else:
                logger.error(f"Invalid coordinates format in geometry array")
                return []
        else:
            logger.error(f"Unexpected geometry format: {type(geometry)}")
            return []
        
        # Validate we got valid coordinates
        if not route_coords or len(route_coords) == 0:
            logger.error("No valid coordinates extracted from geometry")
            return []
        
        # Get route metadata from summary
        summary = route.get("summary", {})
        distance = summary.get("distance", 0)  # in meters
        duration = summary.get("duration", 0)  # in seconds
        
        logger.info(f"✓ Route calculated successfully with {len(route_coords)} waypoints")
        logger.info(f"  Distance: {distance:.2f}m ({distance/1000:.2f}km), Duration: {duration:.0f}s ({duration/60:.1f}min)")
        
        if flooded_points and len(polygons) > 0:
            logger.info(f"  Successfully avoided {len(polygons)} flood areas (radius: {block_radius}m each)")
        
        return route_coords
        
    except requests.exceptions.Timeout:
        logger.error("OpenRouteService API request timed out")
        return []
    except requests.exceptions.ConnectionError:
        logger.error("Failed to connect to OpenRouteService API. Check your internet connection")
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"OpenRouteService API request failed: {e}")
        return []
    except ValueError as e:
        logger.error(f"Failed to parse OpenRouteService API response: {e}")
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
