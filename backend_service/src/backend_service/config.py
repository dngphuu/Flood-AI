"""
Configuration module for backend service.
Loads settings from environment variables with sensible defaults.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()

# AI Service Configuration
AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:8000/api/v1/predict")
AI_SERVICE_TIMEOUT = int(os.getenv("AI_SERVICE_TIMEOUT", "30"))
AI_SERVICE_MAX_RETRIES = int(os.getenv("AI_SERVICE_MAX_RETRIES", "2"))

# Map Configuration
MAP_CACHE_DIR = Path(os.getenv("MAP_CACHE_DIR", "cache"))
CITY_NAME = os.getenv("CITY_NAME", "Ho Chi Minh City, Vietnam")

# Camera Dataset Configuration
CAMERA_DATASET_PATH = Path(os.getenv("CAMERA_DATASET_PATH", "../dataset/dataset_camera_day_du.csv"))

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "logs/backend_service.log")

# Camera Image Configuration
CAMERA_BASE_URL = os.getenv("CAMERA_BASE_URL", "https://giaothong.hochiminhcity.gov.vn:8007/Render/CameraHandler.ashx")
CAMERA_IMAGE_TIMEOUT = int(os.getenv("CAMERA_IMAGE_TIMEOUT", "5"))

# Ensure directories exist
MAP_CACHE_DIR.mkdir(parents=True, exist_ok=True)
Path(LOG_FILE).parent.mkdir(parents=True, exist_ok=True)
