"""
Image retrieval module for fetching camera snapshots.
"""
import requests
import time
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from .logger import logger
from . import config

# Disable InsecureRequestWarning for camera API requests
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def create_session():
    """
    Create a session with appropriate headers and retry logic for camera API.
    
    Returns:
        requests.Session: Configured session object
    """
    session = requests.Session()
    
    # Configure retry strategy
    retry_strategy = Retry(
        total=3,  # Total number of retries
        backoff_factor=1,  # Wait 1s, 2s, 4s between retries
        status_forcelist=[429, 500, 502, 503, 504],  # Retry on these status codes
        allowed_methods=["GET"],  # Retry only on GET requests
        raise_on_status=False
    )
    
    # Use connection pooling with 10 connections for parallel requests
    adapter = HTTPAdapter(
        max_retries=retry_strategy,
        pool_connections=10,
        pool_maxsize=10
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://giaothong.hochiminhcity.gov.vn/"
    }
    session.headers.update(headers)
    
    # Initialize session by visiting homepage
    try:
        logger.debug("Initializing camera API session")
        session.get("https://giaothong.hochiminhcity.gov.vn/", timeout=10, verify=False)
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