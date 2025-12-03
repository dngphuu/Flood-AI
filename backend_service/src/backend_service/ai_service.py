"""
AI service integration module.
Handles flood detection by sending camera images to AI service.
"""
import httpx
import asyncio
from typing import List, Dict, Optional
from .logger import logger
from . import config
from .camera_service import get_camera_service
from .get_image import create_session, get_image_by_id

async def check_flood_status(camera_ids: List[str]) -> List[Dict]:
    """
    Check flood status for a list of cameras by ID.
    
    Args:
        camera_ids: List of camera IDs to check
        
    Returns:
        List of coordinates that are flooded: [{"lat": float, "lng": float}, ...]
    """
    if not camera_ids:
        logger.info("No cameras to check")
        return []
    
    logger.info(f"Checking flood status for {len(camera_ids)} cameras")
    flooded_coords = []
    
    # Get camera service
    camera_service = get_camera_service()
    
    # Validate camera IDs
    valid_ids, invalid_ids = camera_service.validate_camera_ids(camera_ids)
    if invalid_ids:
        logger.warning(f"Invalid camera IDs: {invalid_ids}")
    
    if not valid_ids:
        logger.warning("No valid camera IDs to process")
        return []
    
    # Create session for image fetching (synchronous)
    image_session = create_session()
    
    async with httpx.AsyncClient(timeout=config.AI_SERVICE_TIMEOUT) as client:
        tasks = []
        for cam_id in valid_ids:
            tasks.append(_process_camera(client, image_session, cam_id))
        
        # Run requests concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error processing camera: {result}")
                continue
            
            if result:
                flooded_coords.append(result)
    
    logger.info(f"Found {len(flooded_coords)} flooded locations")
    return flooded_coords

async def _process_camera(client: httpx.AsyncClient, image_session, cam_id: str) -> Optional[Dict]:
    """
    Process a single camera: fetch image and classify.
    
    Args:
        client: httpx.AsyncClient for AI service requests
        image_session: requests.Session for image fetching
        cam_id: Camera ID
        
    Returns:
        Camera coordinates if flooded, None otherwise
    """
    camera_service = get_camera_service()
    camera = camera_service.get_camera(cam_id)
    
    if not camera:
        logger.warning(f"Camera {cam_id} not found in dataset")
        return None
    
    try:
        # Fetch image from camera
        logger.debug(f"Fetching image for camera {cam_id}")
        image_bytes = get_image_by_id(image_session, cam_id)
        
        if not image_bytes:
            logger.warning(f"Failed to fetch image for camera {cam_id}")
            return None
        
        # Send image to AI Service
        logger.debug(f"Sending image for camera {cam_id} to AI service")
        files = {'file': ('snapshot.jpg', image_bytes, 'image/jpeg')}
        
        for attempt in range(config.AI_SERVICE_MAX_RETRIES):
            try:
                response = await client.post(config.AI_SERVICE_URL, files=files)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("success") and result.get("prediction", {}).get("class") == "flood":
                        confidence = result.get("prediction", {}).get("confidence", 0)
                        logger.info(f"Camera {cam_id} detected flood (confidence: {confidence:.2f})")
                        return camera["coords"]
                    else:
                        logger.debug(f"Camera {cam_id} prediction: {result.get('prediction', {}).get('class', 'unknown')}")
                        return None
                else:
                    logger.warning(f"AI Service returned {response.status_code} for camera {cam_id}: {response.text}")
                    if attempt < config.AI_SERVICE_MAX_RETRIES - 1:
                        await asyncio.sleep(0.5)  # Brief delay before retry
                        continue
                    return None
                    
            except httpx.TimeoutException:
                logger.warning(f"Timeout calling AI service for camera {cam_id} (attempt {attempt + 1}/{config.AI_SERVICE_MAX_RETRIES})")
                if attempt < config.AI_SERVICE_MAX_RETRIES - 1:
                    await asyncio.sleep(0.5)
                    continue
                return None
            except httpx.RequestError as e:
                logger.warning(f"Request error calling AI service for camera {cam_id}: {e}")
                if attempt < config.AI_SERVICE_MAX_RETRIES - 1:
                    await asyncio.sleep(0.5)
                    continue
                return None
        
        return None
            
    except Exception as e:
        logger.error(f"Exception processing camera {cam_id}: {e}", exc_info=True)
        return None
