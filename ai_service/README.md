# Flood Classification AI Service

A high-performance FastAPI microservice for classifying flood images using ONNX Runtime. This service is part of the Flood-AI project and follows Clean Architecture principles.

## 🚀 Tech Stack

- **Framework**: FastAPI + Uvicorn
- **Inference Engine**: ONNX Runtime (CPU)
- **Image Processing**: NumPy & Pillow (No PyTorch dependencies)
- **Architecture**: Clean Architecture (Config, Core, Utils, Routes)

## 🏗 Architecture

The service is organized into distinct layers:

- **`config.py`**: Centralized configuration, absolute paths, and constants
- **`core.py`**: Domain logic including ONNX model loading and softmax calculation
- **`utils.py`**: Image preprocessing pipeline (Resize, ImageNet Normalization) using pure NumPy
- **`routes.py`**: FastAPI route handlers

## 🛠 Installation & Running

### Prerequisites

- **Python**: >= 3.12
- **uv**: Package manager ([Install uv](https://docs.astral.sh/uv/getting-started/installation/))

### Quick Start

From the **project root** (`flood-ai/`):

1. **Install all dependencies**:

   ```bash
   uv sync
   ```

2. **Run the AI service**:

   ```bash
   uv run ai-service
   ```

   The server will start at `http://0.0.0.0:8000`

### Alternative: Run from ai_service directory

```bash
cd ai_service
uv run ai-service
```

## 🔌 API Endpoints

### 1. Health Check

Check if the service and model are ready.

- **URL**: `/health`
- **Method**: `GET`
- **Response**:
  ```json
  {
    "model": {
      "info": {
        "class_labels": { "0": "dry_road", "1": "flood" },
        "confidence_threshold": 0.7,
        "input_name": "input",
        "input_shape": ["s77", 3, 224, 224],
        "model_path": ".../models/flood_model_final.onnx",
        "output_name": "output",
        "output_shape": [1, 2]
      },
      "loaded": true
    },
    "service": "flood-classification-ai",
    "status": "healthy",
    "version": "v1"
  }
  ```

### 2. Predict

Classify an image as "flood" or "dry_road".

- **URL**: `/api/v1/predict`
- **Method**: `POST`
- **Content-Type**: `multipart/form-data`
- **Body**:
  - `file`: Image file (jpg, png, jpeg, etc.)
- **Response**:
  ```json
  {
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
    },
    "success": true
  }
  ```

## 🧠 Model Information

- **Input Shape**: `(1, 3, 224, 224)`
- **Preprocessing**:
  - Resize to 224x224 (Bilinear)
  - Normalize (ImageNet Mean/Std)
  - Transpose to CHW
- **Labels**:
  - `0`: `dry_road`
  - `1`: `flood`
- **Confidence Threshold**: `0.7`

## 🧪 Testing

Run the included test script to verify model loading, preprocessing, and inference logic:

```bash
uv run python test_service.py
```
