# Flood-AI Backend Service

Production-ready backend service for the Flood-AI project, providing intelligent routing with real-time flood detection using camera data and AI-powered image analysis.

## 🌟 Features

- **Smart Routing**: Dynamic route calculation avoiding flooded areas using OSMnx and NetworkX
- **Camera Integration**: 696 cameras from Ho Chi Minh City traffic system
- **AI-Powered Detection**: Real-time flood detection via AI service integration
- **High Performance**: Map caching for 10-20x faster startup (15s vs 2-5 minutes)
- **Production Ready**: Environment-based configuration, comprehensive logging, error handling
- **Robust Architecture**: Retry logic, graceful degradation, efficient resource usage

## 📋 Requirements

- Python >= 3.12
- [uv](https://github.com/astral-sh/uv) (Package manager)
- AI Service running on port 8000 (optional but recommended)

## 🚀 Quick Start

### Installation

```bash
cd backend_service
uv sync
```

### Configuration

Copy the example environment file and customize:

```bash
cp .env.example .env
```

Available configuration options:

```env
# AI Service
AI_SERVICE_URL=http://localhost:8000/api/v1/predict
AI_SERVICE_TIMEOUT=30
AI_SERVICE_MAX_RETRIES=2

# Map Configuration
MAP_CACHE_DIR=./cache
CITY_NAME=Ho Chi Minh City, Vietnam

# Camera Dataset
CAMERA_DATASET_PATH=../dataset/dataset_camera_day_du.csv

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/backend_service.log

# Camera Image API
CAMERA_BASE_URL=https://giaothong.hochiminhcity.gov.vn:8007/Render/CameraHandler.ashx
CAMERA_IMAGE_TIMEOUT=5
```

### Running the Service

Development server:

```bash
uv run backend-service
```

Server will start at `http://0.0.0.0:5000`

**First startup**: Downloads and caches Ho Chi Minh City map (~2-5 minutes, 146K nodes)  
**Subsequent startups**: Loads from cache (~15 seconds)

## 📡 API Documentation

### Health Check

**Endpoint:** `GET /health`

**Response:**

```json
{
  "status": "healthy"
}
```

### Route Request

**Endpoint:** `POST /route_request`

Calculate a safe route avoiding flooded areas detected by cameras.

**Request Body:**

```json
{
  "start_coords": {
    "lat": 10.762622,
    "lng": 106.660172
  },
  "end_coords": {
    "lat": 10.773163,
    "lng": 106.654367
  },
  "camera_ids": ["59d3524f02eb490011a0a61b", "5a6065c58576340017d06615"]
}
```

**Response (200 OK):**

```json
{
  "status": "success",
  "message": "Route calculated",
  "data": {
    "start": {"lat": 10.762622, "lng": 106.660172},
    "end": {"lat": 10.773163, "lng": 106.654367},
    "camera_count": 2,
    "flooded_count": 2,
    "flooded_coords": [
      {"lat": 10.8655019, "lng": 106.7931067},
      {"lat": 10.8797100, "lng": 106.6779863}
    ],
    "path": [
      {"lat": 10.7629203, "lng": 106.6602362},
      {"lat": 10.7634029, "lng": 106.6600961},
      ...
    ],
    "path_length": 24
  }
}
```

**Error Responses:**

- `400 Bad Request`: Missing/invalid coordinates or camera IDs
- `404 Not Found`: No route found between points
- `500 Internal Server Error`: Server error

## 🧪 Testing

### Unit Tests

```bash
cd backend_service
uv run pytest tests/unit
```

Tests include:

- API endpoint validation
- Routing logic
- Camera service
- Configuration loading

### Integration Tests

Requires AI service running on port 8000:

```bash
cd backend_service
uv run python tests/integration/verify_integration.py
```

### Manual Testing

```bash
# Test health check
curl http://localhost:5000/health

# Test routing (PowerShell)
$body = @{
  start_coords = @{lat = 10.762622; lng = 106.660172}
  end_coords = @{lat = 10.773163; lng = 106.654367}
  camera_ids = @('59d3524f02eb490011a0a61b', '5a6065c58576340017d06615')
} | ConvertTo-Json

Invoke-WebRequest -Uri http://localhost:5000/route_request `
  -Method POST -Body $body -ContentType 'application/json'
```

## 🏗️ Architecture

### Project Structure

```
backend_service/
├── src/backend_service/
│   ├── app.py              # Flask application factory
│   ├── routes.py           # API endpoints
│   ├── config.py           # Configuration management
│   ├── logger.py           # Logging setup
│   ├── camera_service.py   # Camera dataset management
│   ├── ai_service.py       # AI service integration
│   ├── get_image.py        # Camera image fetching
│   └── routing_service.py  # Map and routing logic
├── tests/
│   ├── unit/              # Unit tests
│   └── integration/       # Integration tests
├── cache/                 # Cached map data (auto-generated)
├── logs/                  # Log files (auto-generated)
├── .env.example          # Example configuration
└── pyproject.toml        # Dependencies
```

### Key Components

**Camera Service** (`camera_service.py`)

- Loads 696 cameras from CSV on startup
- O(1) lookup by camera ID
- Validates camera IDs before processing

**Routing Service** (`routing_service.py`)

- Downloads Ho Chi Minh City map from OpenStreetMap
- Caches map to disk (146,179 nodes)
- Uses edge weight modification (no graph copying) for 10x performance
- Smart flood avoidance with fallback to normal routing

**AI Service Integration** (`ai_service.py`)

- Fetches camera images from traffic API
- Sends to AI service for flood detection
- Configurable retry logic (default: 2 retries)
- Graceful degradation if AI service unavailable

**Image Fetching** (`get_image.py`)

- Connects to Ho Chi Minh City traffic camera API
- Session-based with proper headers
- Configurable timeouts

## 🔄 Complete Pipeline

1. **Request received** with start/end coordinates and camera IDs
2. **Camera validation** against dataset (696 cameras)
3. **Image fetching** from traffic camera API (concurrent)
4. **AI detection** - send images to AI service
5. **Flood identification** - cameras with flood confidence > 0.7
6. **Route calculation** - shortest path avoiding flooded nodes
7. **Response** with path coordinates and flood locations

**Performance**: ~4 seconds end-to-end (2s images + 1s AI + 1s routing)

## 🔌 AI Service Integration

Backend service expects AI service at `http://localhost:8000/api/v1/predict`

**Request Format:**

- Method: `POST`
- Content-Type: `multipart/form-data`
- Field: `file` (image data)

**Response Format:**

```json
{
  "success": true,
  "prediction": {
    "class": "flood",
    "class_id": 1,
    "confidence": 0.9854,
    "confident": true,
    "probabilities": {
      "dry_road": 0.0146,
      "flood": 0.9854
    },
    "threshold": 0.7
  }
}
```

Backend checks: `success == true` and `prediction.class == "flood"`

## 📊 Performance Optimizations

| Feature          | Before            | After                    | Improvement   |
| ---------------- | ----------------- | ------------------------ | ------------- |
| Map Loading      | Every request     | Cached to disk           | 100x faster   |
| Graph Operations | Copy entire graph | Edge weight modification | 10x faster    |
| Startup Time     | 2-5 minutes       | 15 seconds               | 10-20x faster |
| AI Calls         | Sequential        | Concurrent               | 2x faster     |

## 🔍 Logging

Logs are written to:

- **Console**: INFO level, human-readable
- **File**: DEBUG level with full details (`logs/backend_service.log`)

Format includes timestamp, level, module, line number, and message.

## 🐛 Error Handling

- **Invalid Camera IDs**: Validated before processing, returns 400 with specific IDs
- **AI Service Down**: Continues with routing, logs warnings
- **No Route Found**: Returns 404 with clear message
- **Network Errors**: Retry logic with exponential backoff
- **All Errors**: Comprehensive logging with stack traces

## 🚧 Production Deployment

For production deployment:

1. **Use production WSGI server**:

   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 backend_service.app:create_app()
   ```

2. **Set up reverse proxy** (Nginx recommended)
3. **Configure SSL/TLS** certificates
4. **Enable log rotation**
5. **Set up monitoring** and alerting
6. **Use production `.env`** with appropriate values

## 📝 Camera Dataset

Dataset includes 696 cameras from Ho Chi Minh City:

- Location: `../dataset/dataset_camera_day_du.csv`
- Format: `CamId,Street_Name,Latitude,Longitude`
- Source: Ho Chi Minh City traffic system

Example cameras:

- `59d3524f02eb490011a0a61b`: Trần Quang Khải - Trần Khắc Chân
- `5a6065c58576340017d06615`: Tô Ngọc Vân - TX25

## 🤝 Contributing

When contributing:

1. Follow existing code structure
2. Add tests for new features
3. Update documentation
4. Use type hints
5. Follow PEP 8 style guide

## 📄 License

[Your License Here]

## 🆘 Troubleshooting

**Problem**: Map download fails  
**Solution**: Check internet connection, OSM might be temporarily unavailable

**Problem**: AI service connection refused  
**Solution**: Ensure AI service is running on port 8000

**Problem**: Camera images not loading  
**Solution**: Check camera API availability, verify SSL settings

**Problem**: Slow startup  
**Solution**: First run downloads map (~2-5 min), subsequent runs use cache (~15s)

For more issues, check logs at `logs/backend_service.log`
