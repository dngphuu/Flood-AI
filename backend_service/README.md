# Flood-AI Backend Service

Dịch vụ backend cho dự án Flood-AI, chịu trách nhiệm xử lý định tuyến và tích hợp với hệ thống AI Vision.

## Yêu cầu hệ thống

- Python >= 3.12
- [uv](https://github.com/astral-sh/uv) (Trình quản lý gói)

## Cài đặt

1. Clone repository.
2. Cài đặt dependencies:

```bash
uv sync
```

## Chạy ứng dụng

Để chạy server phát triển:

```bash
uv run backend-service
```

Server sẽ khởi động tại `http://0.0.0.0:5000`.

## Chạy kiểm thử

Dự án sử dụng `pytest`. Để chạy toàn bộ test:

```bash
uv run pytest
```

## API Documentation

### 1. Route Request

**Endpoint:** `POST /route_request`

**Mô tả:** Nhận yêu cầu tìm đường, danh sách camera (hoặc dữ liệu ảnh), và trả về thông tin lộ trình (hiện tại là placeholder).

**Body (JSON):**

```json
{
  "start_coords": {
    "lat": 21.0,
    "lng": 105.8
  },
  "end_coords": {
    "lat": 21.1,
    "lng": 105.9
  },
  "camera_data": [
    {
      "id": "cam_001",
      "coords": {
        "lat": 21.05,
        "lng": 105.85
      }
    }
  ]
}
```

**Response (200 OK):**

```json
{
  "status": "success",
  "message": "Route request received",
  "data": {
    "start": {
      "lat": 21.0,
      "lng": 105.8
    },
    "end": {
      "lat": 21.1,
      "lng": 105.9
    },
    "camera_count": 1
  }
}
```

**Response (400 Bad Request):**

- Thiếu `start_coords` hoặc `end_coords`.
- Sai định dạng JSON.

## Cấu trúc dự án

- `src/backend_service/`: Mã nguồn chính.
  - `app.py`: Khởi tạo Flask app.
  - `routes.py`: Định nghĩa các API endpoints.
- `tests/`: Các test case.
