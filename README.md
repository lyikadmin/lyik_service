# Services API

This repository hosts a FastAPI-based modular server capable of handling multiple services, such as **signature extraction** and **liveness detection**. It is designed to be generic and scalable, allowing for easy addition of new services in the future.

## Current Features

### Signature Extraction Service
- **Endpoints**:
  - `POST /process`: Service name `signature_extraction` extracts the signature region from an uploaded document image and returns it as a cleaned and processed image.
  
- **Machine Learning Logic**:
  - Uses a YOLO-based object detection model to locate signatures within documents and preprocesses them (cleaning and cropping).
  - Core utilities are located under `service_handlers/signature_ml/utils`.

### Liveness Detection Service
- **Endpoints**:
  - `POST /process`: Service name `liveness` analyses an uploaded video to check for liveness.
  
- **Processing Logic**:
  - Includes support for additional metadata like geolocation (`lat`, `lng`) and CAPTCHA verification.
  - Core logic resides in `service_handlers/liveness`.

### Extensibility
This API architecture supports adding more services with minimal effort. The service logic is modular, making it easy to integrate and manage new features.

---

## Project Structure

```plaintext
.
├── app.py                 # Main FastAPI application with routing logic
├── demo/                  # Demo files for testing services
│   ├── liveness.mov       # Sample liveness video
│   └── test_liveness.py   # Test script for liveness detection
├── license.py             # Handles license validation
├── requirements.txt       # Dependencies
├── service_handlers/      # Service-specific logic and utilities
│   ├── liveness/          # Liveness detection service
│   │   └── liveness.py    # Core liveness detection logic
│   └── signature_ml/      # Signature extraction service
│       ├── SOURCE/        # Contains ML models and related files
│       ├── signature_models/
│       │   └── signature_model.py  # Signature model definitions
│       └── utils/
│           ├── signature_extract.py  # Signature extraction utilities
├── service_manager/       # Centralised service management
    └── service_manager.py # Handles service routing and interpretation
```

---

## Getting Started

### Prerequisites

- Python 3.10 
- Pip and virtual environment tools (e.g., `venv`, `conda`)

### Installation

1. Clone the repository:
   ```bash
   git clone <REPO_URL>
   cd <REPO_DIRECTORY>
   ```

2. Create and activate a virtual environment:
   ```bash
   python3.10 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## Running the Server

Start the FastAPI server using Uvicorn:

```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Access the interactive API documentation at: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## Usage

### Generic `POST /process` Endpoint

This endpoint processes requests for multiple services. Use the `service_name` parameter to specify the desired service.

**1. Signature Extraction**
- **Request**:
  - `POST /process`
  - Form data:
    - `service_name`: `signature_extraction`
    - `files`: Upload a document image (`.png`, `.jpg`, etc.)
- **Response**: The extracted signature as `image/png`.

**2. Liveness Detection**
- **Request**:
  - `POST /process`
  - Form data:
    - `service_name`: `liveness`
    - `files`: Upload a video file (`.mp4`)
    - Additional optional fields:
      - `lat`: Latitude (e.g., `12.9716`)
      - `lng`: Longitude (e.g., `77.5946`)
      - `captcha`: Comma-separated CAPTCHA values (e.g., `cat,dog,bird`)
- **Response**: A JSON object with liveness status and message:
  ```json
  {
    "status": "success",
    "message": "Liveness verified successfully."
  }
  ```

---

## Adding New Services

1. Add service-specific logic under `service_handlers/<new_service>`.
2. Update `service_manager/service_manager.py` to include the new service.
3. Test the service with a demo file.