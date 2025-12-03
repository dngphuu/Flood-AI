"""
Image retrieval module for fetching camera snapshots.
"""
import requests
import time
from .logger import logger
from . import config

def create_session():
    """
    Create a session with appropriate headers for camera API.
    
    Returns:
        requests.Session: Configured session object
    """
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://giaothong.hochiminhcity.gov.vn/"
    }
    session.headers.update(headers)
    
    # Initialize session by visiting homepage
    try:
        logger.debug("Initializing camera API session")
        session.get("https://giaothong.hochiminhcity.gov.vn/", timeout=5, verify=False)
    except Exception as e:
        logger.warning(f"Session initialization warning: {e}")
    
    return session

def get_image_by_id(session, camera_id):
    """
    Get camera image by ID.
    
    Args:
        session: requests.Session object
        camera_id: Camera ID string
        
    Returns:
        bytes: Image data if successful, None otherwise
    """
    try:
        ts = int(time.time() * 1000)  # Timestamp
        url = f"{config.CAMERA_BASE_URL}?id={camera_id}&bg=black&w=300&h=230&t={ts}"
        
        response = session.get(url, timeout=config.CAMERA_IMAGE_TIMEOUT, verify=False)
        
        if response.status_code == 200:
            logger.debug(f"Successfully fetched image for camera {camera_id}")
            return response.content
        else:
            logger.warning(f"Failed to fetch image for camera {camera_id}: Status {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Error fetching image for camera {camera_id}: {e}")
        return None