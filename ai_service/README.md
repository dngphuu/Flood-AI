# Flood Classification AI Service

A high-performance Flask microservice for classifying flood images using ONNX Runtime. This service is part of the Flood AI project and follows Clean Architecture principles.

## 🚀 Tech Stack

- **Framework**: Flask 3.x
- **Inference Engine**: ONNX Runtime (CPU)
- **Image Processing**: NumPy & Pillow (No Torch/Torchvision dependencies)
- **Architecture**: Modular Clean Architecture (Config, Core, Utils, API)

## 🏗 Architecture

The service is organized into distinct layers:

- **`config.py`**: Centralized configuration, absolute paths, and constants.
- **`core/`**: Domain logic including ONNX model loading (with external weights) and softmax calculation.
- **`utils/`**: Manual image preprocessing pipeline (Resize, ImageNet Normalization) using pure NumPy.
- **`api/`**: Flask Blueprints and route handlers.

## 🛠 Installation & Running

### Prerequisites

- Python 3.12+
- `uv` package manager (recommended)

### Setup

1. **Install dependencies**:

   ```bash
   cd ai_service
   uv pip install -e .
   ```

2. **Run the service**:

   ```bash
   # Using the CLI command
   uv run ai-service

   # OR directly via Python
   python -m ai_service.app
   ```

   The server will start at `http://0.0.0.0:5000`.

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
