# Aadhaar Masking API

Professional-grade FastAPI service for automated Aadhaar card detection and privacy-preserving masking using YOLOv8.

## Features

- 🔒 **Secure Authentication** - HMAC-SHA256 token-based auth + session management
- 🎯 **Auto-Detection** - YOLOv8-powered Aadhaar card detection
- 🔐 **Privacy-First** - Only stores failed requests for debugging
- 📊 **Admin Dashboard** - Professional web UI for request monitoring
- 📥 **Excel Export** - Download audit logs as spreadsheets
- 💾 **Persistent Logging** - 7-day automatic cleanup
- 🐳 **Docker Ready** - Production-ready containerization
- ⚡ **In-Memory Processing** - No files stored on disk

## Quick Start

### Using Docker (Recommended)

```bash
# Build image
docker build -t aadhaar-api .

# Run container
docker run -d -p 8000:8000 \
  -e SECRET_KEY="your-secret-key" \
  -e ADMIN_USERNAME="admin" \
  -e ADMIN_PASSWORD="your-password" \
  --name aadhaar-api \
  aadhaar-api
```

### Manual Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run server
python main.py
```

Server runs on `http://localhost:8000`

## Authentication System

### API Authentication (HMAC-SHA256)

For programmatic access to `/api/aadhaar/upload`:

**1. Get Token:**
```bash
curl -X POST http://localhost:8000/api/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "gravitonadmin"}'
```

**Response:**
```json
{
  "success": true,
  "token": "base64_encoded_token",
  "validity_minutes": 5
}
```

**2. Use Token:**
```bash
curl -X POST http://localhost:8000/api/aadhaar/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@aadhaar.jpg"
```

**Token Details:**
- Format: `timestamp|hmac_signature` (base64 encoded)
- Validity: 5 minutes
- Algorithm: HMAC-SHA256
- Secure: Constant-time comparison to prevent timing attacks

### Admin Authentication (Session-Based)

For web dashboard access at `/admin/login`:

1. Navigate to `http://localhost:8000/admin/login`
2. Enter credentials (default: `admin` / `gravitonadmin`)
3. Secure cookie created with 1-hour validity
4. Access admin panel at `/admin/logs`

**Session Features:**
- HttpOnly cookies (XSS protection)
- SameSite protection (CSRF prevention)
- Automatic expiry after 1 hour
- Logout endpoint: `/admin/logout`

## API Endpoints

### Public Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API information |
| `/health` | GET | Health check |
| `/api/auth/token` | POST | Get authentication token |

### Protected Endpoints (Requirestoken)

| Endpoint | Method | Description | Auth Type |
|----------|--------|-------------|-----------|
| `/api/aadhaar/upload` | POST | Upload & process image | Bearer Token |
| `/admin/login` | GET/POST | Admin login page/process | None (public) |
| `/admin/logs` | GET | View request logs | Session Cookie |
| `/admin/logs/download` | GET | Download logs as Excel | Session Cookie |
| `/admin/logout` | GET | Logout from admin | Session Cookie |

### Upload Endpoint Details

**Request:**
```bash
POST /api/aadhaar/upload
Content-Type: multipart/form-data
Authorization: Bearer <token>

Form Data:
  file: <image_file>
  include_all_rotations: false (optional)
```

**Response (Success - 200):**
```json
{
  "masked_output": "base64_encoded_masked_image",
  "details": {
    "already_masked_count": 0,
    "masking_done_count": 1
  }
}
```

**Response (No Detection - 422):**
```json
{
  "masked_output": "base64_encoded_original_image",
  "details": {
    "already_masked_count": 0,
    "masking_done_count": 0
  }
}
```

## Admin Logging System

### Storage Strategy

**Success (200):**
- ✅ Masking applied successfully
- ❌ No images stored (privacy/storage optimization)
- ✅ Only status + response logged

**Failed (422):**
- ❌ No Aadhaar detected
- ✅ Input image stored for debugging
- ✅ Full request details logged

### Log Structure

```json
{
  "timestamp": "2025-11-24T15:00:00.123456",
  "status_code": 422,
  "input_base64": "...", // Only for failed requests
  "response_body": {
    "masked_output": "...",
    "details": {
      "already_masked_count": 0,
      "masking_done_count": 0
    }
  }
}
```

### Auto-Cleanup

- **Retention:** 7 days
- **Cleanup runs:** On startup + after each request
- **Max logs:** 1000 entries
- **Storage:** `request_logs.json` file
- **Persistence:** Survives server restarts

### Configuration

```python
# In main.py
LOG_RETENTION_DAYS = 7     # Change retention period
MAX_LOGS = 1000             # Change max log count
```

## Admin Dashboard

Access at `http://localhost:8000/admin/login`

**Features:**
- 📊 Statistics cards (Total, Success, Failed)
- 📋 Request log table
- 🖼️ Image preview (click to enlarge) - failed requests only
- 📥 Excel export button
- 🎨 Minimalist professional UI
- 🔐 Session-based authentication

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | `GRAVITON_AADHAAR_SECURE_2024` | HMAC signing key |
| `ADMIN_USERNAME` | `admin` | Admin username |
| `ADMIN_PASSWORD` | `gravitonadmin` | Admin password |

**⚠️ Change defaults in production!**

## Docker Deployment

### Build & Run

```bash
docker build -t aadhaar-api .
docker run -d -p 8000:8000 \
  -v $(pwd)/request_logs.json:/app/request_logs.json \
  -e SECRET_KEY="production-secret-key" \
  -e ADMIN_USERNAME="admin" \
  -e ADMIN_PASSWORD="secure-password" \
  aadhaar-api
```

### Volume Mount (Optional)

Mount `request_logs.json` to persist logs:
```bash
-v /path/to/logs:/app/request_logs.json
```

### Health Check

```bash
curl http://localhost:8000/health
```

## Project Structure

```
aadharmask/
├── main.py                   # FastAPI application
├── aadhaar_processor.py      # YOLO processing logic
├── requirements.txt          # Python dependencies
├── Dockerfile               # Container definition
├── .dockerignore            # Docker build exclusions
├── request_logs.json        # Persistent log storage (auto-created)
└── model/
    └── weights/
        └── best.pt          # YOLOv8 model
```

## Security Best Practices

1. **Change default credentials** immediately
2. **Use strong SECRET_KEY** in production
3. **Enable HTTPS** (reverse proxy recommended)
4. **Restrict admin access** (IP whitelist/VPN)
5. **Monitor logs** regularly
6. **Rotate credentials** periodically
7. **Use environment variables** (never hardcode)

## Technology Stack

- **Framework:** FastAPI 0.109.0
- **Server:** Uvicorn
- **ML Model:** YOLOv8 (Ultralytics)
- **OCR:** Tesseract via pytesseract
- **Image Processing:** OpenCV, Pillow
- **Excel Export:** openpyxl
- **Authentication:** HMAC-SHA256, sessions

## API Performance

- **Model Loading:** Once on startup (reused)
- **Processing:** In-memory (no disk I/O)
- **Response:** Base64 encoded images
- **Rotation:** Smart detection (0°, 90°, 180°, 270°)

## Troubleshooting

### Model Not Found
```
ERROR: YOLO model not found
```
**Solution:** Ensure `model/weights/best.pt` exists

### Tesseract Error
```
ERROR: pytesseract not installed
```
**Solution:** `apt-get install tesseract-ocr` (Linux) or `brew install tesseract` (Mac)

### Permission Denied (Logs)
```
ERROR: Could not save logs
```
**Solution:** Check write permissions for `request_logs.json`

### Docker Build Fails
```
ERROR: COPY failed
```
**Solution:** Check `.dockerignore` - ensure required files not excluded

## License

Proprietary - Internal Use Only

## Support

For issues or questions, contact your system administrator.

---

**Version:** 2.0.0  
**Last Updated:** 2025-11-24
