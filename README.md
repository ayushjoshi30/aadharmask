# Graviton Backend API - Aadhaar Masking Service

A FastAPI-based backend service for automatic Aadhaar card masking using YOLOv8 object detection and OCR.

## Features

✅ **Auto-rotation detection** - Handles Aadhaar cards at any angle (0°-345°, every 15°)  
✅ **Regex-based Aadhaar detection** - Validates Aadhaar numbers even if YOLO labels are incorrect  
✅ **Intelligent fallback** - Uses orientation detection if primary YOLO detection fails  
✅ **Smart masking** - Masks 65% of Aadhaar number (keeps last 4 digits visible)  
✅ **In-memory processing** - No files stored on disk, all processing done in RAM  
✅ **Base64 response** - Instant image return as base64 encoded string  
✅ **Secure authentication** - Time-based HMAC-SHA256 token authentication  
✅ **Network accessible** - Access from any device on your WiFi network  
✅ **RESTful API** - Clean API endpoints with automatic documentation  

## Prerequisites

- Python 3.8 or higher
- Tesseract OCR installed on your system
- YOLO model weights (see Model Setup below)

### Installing Tesseract OCR

**Windows:**
```bash
# Download and install from: https://github.com/UB-Mannheim/tesseract/wiki
# Add Tesseract to your PATH
```

**Linux:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

## Installation

1. **Clone or navigate to the project directory:**
```bash
cd aadharmaskapp
```

2. **Create a virtual environment (recommended):**
```bash
python -m venv venv

# Activate on Windows:
venv\Scripts\activate

# Activate on Linux/macOS:
source venv/bin/activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

## Model Setup

Ensure your YOLO model is available at one of these paths:
- `model/weights/best.pt` (default)
- `runs/detect/aadhar_model/weights/best.pt`
- `aadhar_model.pt`
- `../model/weights/best.pt`
- `../aadhar_model.pt`

The application will automatically search for the model in these locations.

## Running the Server

1. **Start the FastAPI server:**
```bash
python main.py
```

2. **Access the API:**
   - **Local Access:** http://localhost:8000
   - **Network Access:** http://YOUR_LOCAL_IP:8000 (displayed in console)
   - **Interactive API Docs:** http://localhost:8000/docs
   - **Alternative API Docs:** http://localhost:8000/redoc

## 🔐 Authentication

The API uses **username/password + time-based HMAC-SHA256** authentication for security.

### Quick Start

**Step 1: Login with Credentials**
```bash
curl -X POST http://localhost:8000/api/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"gravitonadmin"}'
```

**Response:**
```json
{
  "success": true,
  "token": "MTczMTQxMjgwMHw4YTJiNGM2...",
  "expires_at": "2025-11-12T11:35:00"
}
```

**Step 2: Use Token to Upload**
```bash
curl -X POST http://localhost:8000/api/aadhaar/upload \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -F "file=@aadhaar.jpg"
```

### Credentials
- **Username:** `admin`
- **Password:** `gravitonadmin`

### Token Details
- **Validity:** 5 minutes
- **Algorithm:** HMAC-SHA256
- **Format:** `Authorization: Bearer <token>`

📖 **Full Login Guide:** See [LOGIN_GUIDE.md](LOGIN_GUIDE.md)

---

## API Endpoints

### 1. Login & Get Auth Token
```
POST /api/auth/token
```
Login with username/password to get authentication token.

**Request Body:**
```json
{
  "username": "admin",
  "password": "gravitonadmin"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Authentication successful",
  "token": "MTczMTQxMjgwMHw4YTJiNGM2...",
  "expires_at": "2025-11-12T11:35:00",
  "validity_minutes": 5
}
```

### 2. Upload Aadhaar Image
```
POST /api/aadhaar/upload
```
Upload an Aadhaar card image for processing and masking. Returns masked image as base64.

**Authentication:** Required

**Request:**
- Headers: `Authorization: Bearer <token>`
- Content-Type: `multipart/form-data`
- Body: `file` (image file)

**Response:**
```json
{
  "job_id": "uuid-string",
  "status": "completed",
  "original_filename": "aadhaar.jpg",
  "extracted_info": {
    "AADHAR_NUMBER": "XXXX XXXX 1234"
  },
  "masked_image_base64": "/9j/4AAQSkZJRgABAQEAYABgAAD...",
  "image_format": "jpeg",
  "data_uri": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD...",
  "processed_at": "2025-11-12T10:30:00",
  "note": "Image processed in memory - no files stored on disk"
}
```

**📸 Image Response Formats:**
- `masked_image_base64`: Raw base64-encoded image string (decode to save)
- `image_format`: Image format (always jpeg)
- `data_uri`: Ready-to-use data URI for HTML `<img>` tags (recommended!)

### 2. Health Check
```
GET /health
```
Check if the server is running and healthy.

## Directory Structure

```
aadharmaskapp/
├── main.py                          # FastAPI application (in-memory processing)
├── aadhaar_processor.py             # YOLO + OCR processing logic
├── requirements.txt                 # Python dependencies
├── README.md                        # Documentation
├── POSTMAN_GUIDE.md                # Postman testing guide
└── model/           # YOLO model directory
    └── aadhar_model/
        └── weights/
            └── best.pt              # YOLO model weights

Note: No uploads/ or outputs/ directories - all processing done in memory!
```

## Usage Example with cURL

```bash
# Upload an Aadhaar image and get base64 response
curl -X POST "http://localhost:8000/api/aadhaar/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/aadhaar.jpg"

# Response will contain base64 encoded image in 'masked_image_base64' field
# Use the 'data_uri' field to display directly in HTML
```

## Usage Example with Python

### Example 1: Save Base64 to File (with Authentication)
```python
import requests
import base64

# Step 1: Login to get authentication token
login_url = "http://localhost:8000/api/auth/token"
credentials = {
    "username": "admin",
    "password": "gravitonadmin"
}

token_response = requests.post(login_url, json=credentials)
token = token_response.json()["token"]

print(f"✅ Login successful!")
print(f"Token expires at: {token_response.json()['expires_at']}")

# Step 2: Upload image with authentication
url = "http://localhost:8000/api/aadhaar/upload"
headers = {"Authorization": f"Bearer {token}"}

with open("aadhaar.jpg", "rb") as f:
    files = {"file": f}
    response = requests.post(url, headers=headers, files=files)

data = response.json()

print(f"Job ID: {data['job_id']}")
print(f"Masked Aadhaar: {data['extracted_info']['AADHAR_NUMBER']}")
print(f"Image Format: {data['image_format']}")

# Decode base64 and save image
base64_string = data["masked_image_base64"]
image_bytes = base64.b64decode(base64_string)

with open("masked_aadhaar.jpg", "wb") as f:
    f.write(image_bytes)

print("✅ Image saved successfully!")
```

### Example 2: Display in HTML
```python
import requests

# Login to get token
credentials = {"username": "admin", "password": "gravitonadmin"}
token = requests.post("http://localhost:8000/api/auth/token", json=credentials).json()["token"]

# Upload image with authentication
response = requests.post(
    "http://localhost:8000/api/aadhaar/upload",
    headers={"Authorization": f"Bearer {token}"},
    files={"file": open("aadhaar.jpg", "rb")}
)
data = response.json()

# Generate HTML with embedded image (no separate download needed!)
html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Masked Aadhaar</title>
    <style>
        body {{ font-family: Arial; text-align: center; padding: 50px; }}
        img {{ max-width: 600px; border: 2px solid #667eea; border-radius: 10px; }}
    </style>
</head>
<body>
    <h1>🔐 Masked Aadhaar Card</h1>
    <img src="{data['data_uri']}" alt="Masked Aadhaar">
    <p><strong>Aadhaar Number:</strong> {data['extracted_info']['AADHAR_NUMBER']}</p>
    <p><em>Processed at: {data['processed_at']}</em></p>
</body>
</html>
"""

with open("result.html", "w") as f:
    f.write(html)

print("✅ HTML file created! Open result.html in your browser.")
```

### Example 3: Use with OpenCV/NumPy
```python
import requests
import base64
import numpy as np
import cv2

# Login to get token
credentials = {"username": "admin", "password": "gravitonadmin"}
token = requests.post("http://localhost:8000/api/auth/token", json=credentials).json()["token"]

# Upload and get response
response = requests.post(
    "http://localhost:8000/api/aadhaar/upload",
    headers={"Authorization": f"Bearer {token}"},
    files={"file": open("aadhaar.jpg", "rb")}
)
data = response.json()

# Decode base64 to numpy array
base64_string = data["masked_image_base64"]
image_bytes = base64.b64decode(base64_string)
nparr = np.frombuffer(image_bytes, np.uint8)
image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

# Now you can process it further with OpenCV
cv2.imshow("Masked Aadhaar", image)
cv2.waitKey(0)
cv2.destroyAllWindows()
```

## Network Access

The server is configured to accept connections from any device on your local network:

1. Find your local IP address (displayed when server starts)
2. Connect from mobile/other devices: `http://YOUR_LOCAL_IP:8000`
3. **Windows Firewall:** Ensure port 8000 is allowed

## Troubleshooting

### YOLO Model Not Found
```
❌ YOLO model not found in expected locations.
```
**Solution:** Ensure `best.pt` is in one of the expected paths (see Model Setup)

### Tesseract Not Found
```
TesseractNotFoundError
```
**Solution:** Install Tesseract OCR and add it to your system PATH

### Port Already in Use
```
OSError: [Errno 98] Address already in use
```
**Solution:** Change port in `main.py` or kill the process using port 8000

### Image Processing Fails
- Ensure image is a valid Aadhaar card
- Check image quality and resolution
- Verify Tesseract OCR is installed correctly

## Development

To run the server in development mode with auto-reload:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## License

This project is for educational and development purposes.

## Support

For issues or questions, please check the logs in the console for detailed error messages.

