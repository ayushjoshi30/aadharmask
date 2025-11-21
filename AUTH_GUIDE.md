# 🔐 Authentication Guide - Graviton Aadhaar API

Complete guide for using the time-based HMAC authentication system.

---

## 🔑 Overview

The API uses **HMAC-SHA256** time-based authentication to secure all endpoints.

### Key Features:
- ⏱️ **Time-based tokens** - Tokens expire after 5 minutes
- 🔒 **HMAC-SHA256** - Industry-standard cryptographic signing
- 🚀 **Easy to use** - Generate token via API or script
- 🛡️ **Secure** - Prevents replay attacks and tampering

---

## 🚀 Quick Start

### Method 1: Get Token from API (Easiest)

```bash
# 1. Generate token
curl http://localhost:8000/api/auth/token

# Response:
{
  "token": "MTczMTQxMjgwMHw4YTJiNGM2ZDhlZjEyMzQ1Njc4OWFiY2RlZjEyMzQ1Njc4OWFiY2RlZjEyMzQ1Njc4OQ==",
  "expires_at": "2025-11-12T11:35:00",
  "validity_minutes": 5,
  "usage": {
    "header": "Authorization",
    "value": "Bearer MTczMTQxMjgwMHw4YTJiNGM2ZDhlZjEyMzQ1Njc4OWFiY2RlZjEyMzQ1Njc4OWFiY2RlZjEyMzQ1Njc4OQ=="
  }
}

# 2. Use token in upload request
curl -X POST http://localhost:8000/api/aadhaar/upload \
  -H "Authorization: Bearer MTczMTQxMjgwMHw4YTJiNGM2ZDhlZjEyMzQ1Njc4OWFiY2RlZjEyMzQ1Njc4OWFiY2RlZjEyMzQ1Njc4OQ==" \
  -F "file=@aadhaar.jpg"
```

---

## 📝 How It Works

### Token Structure
```
timestamp|hmac_signature
```

1. **Timestamp**: Current Unix timestamp (seconds since epoch)
2. **HMAC Signature**: SHA-256 hash of timestamp with secret key
3. **Encoding**: Base64 encoded for clean HTTP header

### Token Generation Process
```python
# 1. Get current timestamp
timestamp = int(time.time())

# 2. Generate HMAC signature
signature = hmac.new(
    SECRET_KEY.encode('utf-8'),
    str(timestamp).encode('utf-8'),
    hashlib.sha256
).hexdigest()

# 3. Combine and encode
token = base64.b64encode(f"{timestamp}|{signature}".encode()).decode()
```

### Token Verification
1. Decode base64 token
2. Extract timestamp and signature
3. Check if timestamp is within validity window (5 minutes)
4. Regenerate signature and compare with received signature
5. Use constant-time comparison to prevent timing attacks

---

## 🔧 Implementation Examples

### Python (Requests Library)

```python
import requests
import hmac
import hashlib
import base64
import time

SECRET_KEY = "GRAVITON_AADHAAR_SECURE_2024"

def generate_token():
    """Generate authentication token"""
    timestamp = int(time.time())
    message = str(timestamp).encode('utf-8')
    signature = hmac.new(
        SECRET_KEY.encode('utf-8'),
        message,
        hashlib.sha256
    ).hexdigest()
    token = f"{timestamp}|{signature}"
    return base64.b64encode(token.encode('utf-8')).decode('utf-8')

# Generate token
token = generate_token()

# Make authenticated request
response = requests.post(
    "http://localhost:8000/api/aadhaar/upload",
    headers={"Authorization": f"Bearer {token}"},
    files={"file": open("aadhaar.jpg", "rb")}
)

print(response.json())
```

### Python (Using API to get token)

```python
import requests

# Step 1: Get token from API
token_response = requests.get("http://localhost:8000/api/auth/token")
token_data = token_response.json()
token = token_data["token"]

print(f"Token expires at: {token_data['expires_at']}")

# Step 2: Use token for upload
upload_response = requests.post(
    "http://localhost:8000/api/aadhaar/upload",
    headers={"Authorization": f"Bearer {token}"},
    files={"file": open("aadhaar.jpg", "rb")}
)

print(upload_response.json())
```

### JavaScript (Node.js)

```javascript
const crypto = require('crypto');
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

const SECRET_KEY = 'GRAVITON_AADHAAR_SECURE_2024';

function generateToken() {
    const timestamp = Math.floor(Date.now() / 1000);
    const signature = crypto
        .createHmac('sha256', SECRET_KEY)
        .update(timestamp.toString())
        .digest('hex');
    
    const token = `${timestamp}|${signature}`;
    return Buffer.from(token).toString('base64');
}

// Generate token
const token = generateToken();

// Upload with authentication
const formData = new FormData();
formData.append('file', fs.createReadStream('aadhaar.jpg'));

axios.post('http://localhost:8000/api/aadhaar/upload', formData, {
    headers: {
        ...formData.getHeaders(),
        'Authorization': `Bearer ${token}`
    }
})
.then(response => console.log(response.data))
.catch(error => console.error(error.response.data));
```

### cURL

```bash
# Method 1: Get token from API
TOKEN=$(curl -s http://localhost:8000/api/auth/token | jq -r '.token')

# Use token
curl -X POST http://localhost:8000/api/aadhaar/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@aadhaar.jpg"
```

---

## 🧪 Testing in Postman

### Step 1: Generate Token

**Request 1: Get Token**
- Method: `GET`
- URL: `http://localhost:8000/api/auth/token`
- Response will contain the token

**Save Token to Variable:**
Go to "Tests" tab and add:
```javascript
var jsonData = pm.response.json();
pm.environment.set("auth_token", jsonData.token);
console.log("Token:", jsonData.token);
console.log("Expires:", jsonData.expires_at);
```

### Step 2: Upload with Token

**Request 2: Upload Aadhaar**
- Method: `POST`
- URL: `http://localhost:8000/api/aadhaar/upload`
- Headers:
  - Key: `Authorization`
  - Value: `Bearer {{auth_token}}`
- Body: `form-data`
  - Key: `file` (type: File)
  - Value: Select your image

---

## ⚙️ Configuration

### Change Secret Key

Edit `main.py`:
```python
SECRET_KEY = "YOUR_CUSTOM_SECRET_KEY_HERE"
```

**⚠️ Important:** Keep this secret secure! Don't commit to public repositories.

### Change Token Validity

Edit `main.py`:
```python
TOKEN_VALIDITY_MINUTES = 10  # Change from 5 to 10 minutes
```

---

## 🛡️ Security Features

### 1. Time-based Validation
- Tokens are only valid for 5 minutes
- Prevents old tokens from being reused
- Mitigates replay attacks

### 2. HMAC Signing
- Cryptographically secure signature
- Impossible to forge without secret key
- Verifies data integrity

### 3. Constant-time Comparison
- Uses `hmac.compare_digest()` for signature verification
- Prevents timing attacks
- Industry best practice

### 4. Base64 Encoding
- Clean representation in HTTP headers
- No special characters to escape
- Standard encoding format

---

## ❌ Common Errors

### 401: Missing Authorization header
```json
{
  "detail": "Missing Authorization header"
}
```
**Solution:** Add `Authorization: Bearer <token>` header

### 401: Invalid or expired authorization token
```json
{
  "detail": "Invalid or expired authorization token"
}
```
**Solutions:**
- Generate a new token (old one expired)
- Check secret key matches between client and server
- Ensure timestamp is synchronized

### 400: File must be an image
```json
{
  "detail": "File must be an image"
}
```
**Solution:** Upload a valid image file (JPG, PNG, etc.)

---

## 📊 API Endpoints

| Endpoint | Auth Required | Description |
|----------|---------------|-------------|
| `GET /` | ❌ No | API information |
| `GET /health` | ❌ No | Health check |
| `GET /api/auth/token` | ❌ No | Generate auth token |
| `POST /api/aadhaar/upload` | ✅ Yes | Upload & process image |

---

## 🔄 Token Lifecycle

```
┌─────────────────────────────────────────────────┐
│ 1. Client generates or requests token          │
│    GET /api/auth/token                         │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│ 2. Server generates token with timestamp       │
│    Token valid for 5 minutes                   │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│ 3. Client includes token in Authorization      │
│    Authorization: Bearer <token>               │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│ 4. Server verifies token                       │
│    - Decode base64                             │
│    - Check timestamp (not expired)             │
│    - Verify HMAC signature                     │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
         ┌─────────┴─────────┐
         │                   │
    Valid Token          Invalid Token
         │                   │
         ▼                   ▼
   Process Request      401 Unauthorized
```

---

## 🧰 Helper Scripts

### Token Generator Script

Save as `generate_token.py`:
```python
#!/usr/bin/env python3
import hmac
import hashlib
import base64
import time
from datetime import datetime, timedelta

SECRET_KEY = "GRAVITON_AADHAAR_SECURE_2024"
VALIDITY_MINUTES = 5

def generate_token():
    timestamp = int(time.time())
    message = str(timestamp).encode('utf-8')
    signature = hmac.new(
        SECRET_KEY.encode('utf-8'),
        message,
        hashlib.sha256
    ).hexdigest()
    token = f"{timestamp}|{signature}"
    return base64.b64encode(token.encode('utf-8')).decode('utf-8')

if __name__ == "__main__":
    token = generate_token()
    expires = datetime.now() + timedelta(minutes=VALIDITY_MINUTES)
    
    print("="*60)
    print("🔑 Authentication Token Generated")
    print("="*60)
    print(f"\nToken:\n{token}\n")
    print(f"Expires at: {expires.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Validity: {VALIDITY_MINUTES} minutes\n")
    print("="*60)
    print("Usage in cURL:")
    print(f'curl -H "Authorization: Bearer {token}" ...')
    print("="*60)
```

Run with:
```bash
python generate_token.py
```

---

## 💡 Best Practices

1. **🔄 Regenerate tokens regularly**
   - Don't reuse expired tokens
   - Generate new token for each session

2. **🔒 Keep SECRET_KEY private**
   - Use environment variables
   - Don't commit to version control
   - Rotate periodically

3. **⏰ Handle expiration gracefully**
   - Check token expiry before use
   - Implement auto-refresh logic
   - Show user-friendly error messages

4. **🌐 Use HTTPS in production**
   - Encrypt tokens in transit
   - Prevent man-in-the-middle attacks

5. **📝 Log authentication failures**
   - Monitor for suspicious activity
   - Track failed authentication attempts

---

## 🎯 Quick Reference

### Generate Token (API)
```bash
curl http://localhost:8000/api/auth/token
```

### Upload with Auth
```bash
curl -X POST http://localhost:8000/api/aadhaar/upload \
  -H "Authorization: Bearer <YOUR_TOKEN>" \
  -F "file=@image.jpg"
```

### Token Format
```
Authorization: Bearer <base64_encoded_token>
```

### Token Validity
- **Duration:** 5 minutes
- **Algorithm:** HMAC-SHA256
- **Format:** `timestamp|signature` (base64 encoded)

---

## 🆘 Support

If you encounter issues:
1. Check token hasn't expired (5 minute limit)
2. Verify SECRET_KEY matches on client and server
3. Ensure Authorization header is properly formatted
4. Check server logs for detailed error messages

---

**Ready to authenticate!** 🚀

Generate your first token: `GET http://localhost:8000/api/auth/token`

