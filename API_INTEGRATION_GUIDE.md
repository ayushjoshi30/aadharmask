# 📚 Aadhaar Masking API - Integration Guide

## Table of Contents
- [Overview](#overview)
- [Quick Start](#quick-start)
- [Authentication](#authentication)
- [API Endpoints](#api-endpoints)
- [Request & Response Examples](#request--response-examples)
- [Integration Examples](#integration-examples)
- [Error Handling](#error-handling)
- [Rate Limits & Best Practices](#rate-limits--best-practices)
- [Security Considerations](#security-considerations)
- [Troubleshooting](#troubleshooting)

---

## Overview

The Aadhaar Masking API is a RESTful service that automatically detects and masks Aadhaar card numbers in images while preserving the last 4 digits for verification purposes.

### Key Features
- ✅ **Automatic rotation detection** - Works with images at any angle
- ✅ **Intelligent masking** - Masks 65% of Aadhaar number (keeps last 4 digits)
- ✅ **In-memory processing** - No files stored on server (GDPR compliant)
- ✅ **Base64 response** - Easy integration with web and mobile apps
- ✅ **Secure authentication** - Time-based HMAC-SHA256 tokens
- ✅ **Performance metrics** - Detailed timing information for each request
- ✅ **Flexible rotation modes** - Fast mode (90° increments) or comprehensive mode (15° increments)

### Base URL
```
Production: https://your-domain.com
Development: http://localhost:8000
```

---

## Quick Start

### 1. Get Your Credentials
Contact your administrator to receive:
- API Base URL
- Username
- Password
- Secret Key (if self-hosting)

### 2. Minimal Integration (3 Steps)

```bash
# Step 1: Login to get authentication token
curl -X POST https://your-api.com/api/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username":"your_username","password":"your_password"}'

# Step 2: Copy the token from the response
# Response: {"token": "MTczMTQxM..."}

# Step 3: Upload Aadhaar image with token
curl -X POST https://your-api.com/api/aadhaar/upload \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -F "file=@aadhaar.jpg"
```

---

## Authentication

The API uses a two-step authentication process for security:

### Step 1: Login with Credentials

**Endpoint:** `POST /api/auth/token`

**Request Body:**
```json
{
  "username": "your_username",
  "password": "your_password"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Authentication successful",
  "token": "MTczMTQxMjgwMHw4YTJiNGM2ZGU1ZjdhOGIzYzRkNWU2ZjdhOGI5YzBk",
  "expires_at": "2025-11-22T11:35:00",
  "validity_minutes": 5,
  "usage": {
    "header": "Authorization",
    "value": "Bearer MTczMTQxMjgwMHw4YTJiNGM2ZGU1ZjdhOGIzYzRkNWU2ZjdhOGI5YzBk",
    "example": "Authorization: Bearer <your_token_here>"
  }
}
```

### Step 2: Use Token in Requests

Include the token in the `Authorization` header of all subsequent requests:

```http
Authorization: Bearer MTczMTQxMjgwMHw4YTJiNGM2ZGU1ZjdhOGIzYzRkNWU2ZjdhOGI5YzBk
```

### Token Details
- **Validity:** 5 minutes from generation
- **Algorithm:** HMAC-SHA256 with timestamp
- **Format:** Base64-encoded `timestamp|signature`
- **Security:** Resistant to replay attacks and timing attacks

> **Note:** Tokens expire after 5 minutes. Implement automatic token refresh in your application.

---

## API Endpoints

### 1. Authentication Endpoint

#### `POST /api/auth/token`
Login with username and password to receive an authentication token.

**Authentication Required:** No

**Request:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "token": "string",
  "expires_at": "ISO 8601 datetime",
  "validity_minutes": 5
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid username or password

---

### 2. Aadhaar Upload Endpoint

#### `POST /api/aadhaar/upload`
Upload an Aadhaar card image for automatic detection and masking.

**Authentication Required:** Yes (Bearer token)

**Request:**
- **Method:** POST
- **Content-Type:** `multipart/form-data`
- **Headers:**
  - `Authorization: Bearer <token>`
- **Body Parameters:**
  - `file` (required): Image file (JPEG, PNG, etc.)
  - `include_all_rotations` (optional): Boolean, default `false`
    - `false`: Fast mode - checks only 0°, 90°, 180°, 270° (recommended)
    - `true`: Comprehensive mode - checks every 15° from 0° to 345°

**Response (200 OK - Aadhaar Detected):**
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
  "processed_at": "2025-11-22T10:30:00",
  "note": "Image processed in memory - no files stored on disk",
  "performance": {
    "1_file_read_ms": 5.2,
    "2_image_decode_ms": 12.4,
    "3a_preprocessing_ms": 0.1,
    "3b_model_forward_ms": 245.6,
    "3_model_inference_total_ms": 245.7,
    "4a_postproc_validation_ms": 8.3,
    "4b_image_encode_ms": 15.1,
    "5_total_request_ms": 286.7
  }
}
```

**Response (422 Unprocessable Entity - No Aadhaar Detected):**
```json
{
  "job_id": "uuid-string",
  "status": "no_detection",
  "original_filename": "document.jpg",
  "extracted_info": {
    "AADHAR_NUMBER": "Not detected"
  },
  "masked_image_base64": "/9j/4AAQSkZJRgABAQEAYABgAAD...",
  "image_format": "jpeg",
  "data_uri": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD...",
  "processed_at": "2025-11-22T10:30:00",
  "error": "Aadhaar card not detected or no masking applied",
  "note": "Image processed but no Aadhaar detected - original image returned",
  "performance": { /* metrics */ }
}
```

**Error Responses:**
- `400 Bad Request` - Invalid file type or corrupted image
- `401 Unauthorized` - Missing or invalid authentication token
- `500 Internal Server Error` - Processing failed

---

### 3. Health Check Endpoint

#### `GET /health`
Check if the API is running and healthy.

**Authentication Required:** No

**Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-22T10:30:00"
}
```

---

### 4. API Information Endpoint

#### `GET /`
Get API version, available endpoints, and status codes.

**Authentication Required:** No

**Response (200 OK):**
```json
{
  "message": "Graviton API is running (In-Memory Processing)",
  "version": "2.0.0",
  "description": "Secure API with username/password + time-based HMAC authentication",
  "endpoints": {
    "login": "/api/auth/token - Login with username/password to get token (POST)",
    "upload": "/api/aadhaar/upload - Upload image and get base64 result (requires auth)",
    "health": "/health - Health check (public)"
  },
  "status_codes": {
    "200": "Success - Aadhaar detected and masking applied",
    "422": "Unprocessable Entity - No Aadhaar detected or no masking applied",
    "401": "Unauthorized - Invalid or missing authentication token",
    "500": "Internal Server Error - Processing failed"
  }
}
```

---

## Request & Response Examples

### Example 1: Complete Flow with cURL

```bash
# 1. Login to get token
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"gravitonadmin"}' \
  | jq -r '.token')

echo "Token: $TOKEN"

# 2. Upload Aadhaar image (fast mode - default)
curl -X POST http://localhost:8000/api/aadhaar/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@aadhaar.jpg" \
  -o response.json

# 3. Extract base64 image and save
cat response.json | jq -r '.masked_image_base64' | base64 -d > masked_aadhaar.jpg

echo "✅ Masked image saved to masked_aadhaar.jpg"
```

### Example 2: Upload with All Rotations (Comprehensive Mode)

```bash
curl -X POST http://localhost:8000/api/aadhaar/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@aadhaar.jpg" \
  -F "include_all_rotations=true"
```

---

## Integration Examples

### Python (Recommended)

#### Simple Integration
```python
import requests
import base64

class AadhaarMaskingClient:
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.token = None
        self.token_expires_at = None
    
    def login(self):
        """Login and get authentication token"""
        url = f"{self.base_url}/api/auth/token"
        response = requests.post(url, json={
            "username": self.username,
            "password": self.password
        })
        
        if response.status_code == 200:
            data = response.json()
            self.token = data["token"]
            self.token_expires_at = data["expires_at"]
            print(f"✅ Login successful! Token expires at: {self.token_expires_at}")
            return True
        else:
            print(f"❌ Login failed: {response.json()}")
            return False
    
    def mask_aadhaar(self, image_path, include_all_rotations=False):
        """Upload and mask Aadhaar image"""
        if not self.token:
            print("⚠️  Not authenticated. Logging in...")
            if not self.login():
                return None
        
        url = f"{self.base_url}/api/aadhaar/upload"
        headers = {"Authorization": f"Bearer {self.token}"}
        
        with open(image_path, "rb") as f:
            files = {"file": f}
            data = {"include_all_rotations": str(include_all_rotations).lower()}
            response = requests.post(url, headers=headers, files=files, data=data)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 422:
            print("⚠️  No Aadhaar detected in image")
            return response.json()
        elif response.status_code == 401:
            # Token expired, retry with fresh token
            print("🔄 Token expired. Re-authenticating...")
            if self.login():
                return self.mask_aadhaar(image_path, include_all_rotations)
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return None
    
    def save_masked_image(self, result, output_path):
        """Save masked image from API response"""
        if not result or "masked_image_base64" not in result:
            print("❌ No image data in response")
            return False
        
        base64_string = result["masked_image_base64"]
        image_bytes = base64.b64decode(base64_string)
        
        with open(output_path, "wb") as f:
            f.write(image_bytes)
        
        print(f"✅ Masked image saved to: {output_path}")
        return True

# Usage
client = AadhaarMaskingClient(
    base_url="http://localhost:8000",
    username="admin",
    password="gravitonadmin"
)

# Login
client.login()

# Mask Aadhaar (fast mode)
result = client.mask_aadhaar("aadhaar.jpg")

if result:
    print(f"Job ID: {result['job_id']}")
    print(f"Status: {result['status']}")
    print(f"Masked Aadhaar: {result['extracted_info']['AADHAR_NUMBER']}")
    print(f"Processing time: {result['performance']['5_total_request_ms']:.2f}ms")
    
    # Save masked image
    client.save_masked_image(result, "masked_aadhaar.jpg")
```

---

### JavaScript/Node.js

```javascript
const axios = require('axios');
const fs = require('fs');
const FormData = require('form-data');

class AadhaarMaskingClient {
    constructor(baseUrl, username, password) {
        this.baseUrl = baseUrl;
        this.username = username;
        this.password = password;
        this.token = null;
    }

    async login() {
        try {
            const response = await axios.post(`${this.baseUrl}/api/auth/token`, {
                username: this.username,
                password: this.password
            });
            
            this.token = response.data.token;
            console.log(`✅ Login successful! Token expires at: ${response.data.expires_at}`);
            return true;
        } catch (error) {
            console.error('❌ Login failed:', error.response?.data || error.message);
            return false;
        }
    }

    async maskAadhaar(imagePath, includeAllRotations = false) {
        if (!this.token) {
            console.log('⚠️  Not authenticated. Logging in...');
            const loginSuccess = await this.login();
            if (!loginSuccess) return null;
        }

        try {
            const formData = new FormData();
            formData.append('file', fs.createReadStream(imagePath));
            formData.append('include_all_rotations', includeAllRotations.toString());

            const response = await axios.post(
                `${this.baseUrl}/api/aadhaar/upload`,
                formData,
                {
                    headers: {
                        ...formData.getHeaders(),
                        'Authorization': `Bearer ${this.token}`
                    }
                }
            );

            return response.data;
        } catch (error) {
            if (error.response?.status === 401) {
                // Token expired, retry
                console.log('🔄 Token expired. Re-authenticating...');
                await this.login();
                return this.maskAadhaar(imagePath, includeAllRotations);
            } else if (error.response?.status === 422) {
                console.log('⚠️  No Aadhaar detected in image');
                return error.response.data;
            } else {
                console.error('❌ Error:', error.response?.data || error.message);
                return null;
            }
        }
    }

    saveMaskedImage(result, outputPath) {
        if (!result || !result.masked_image_base64) {
            console.error('❌ No image data in response');
            return false;
        }

        const imageBuffer = Buffer.from(result.masked_image_base64, 'base64');
        fs.writeFileSync(outputPath, imageBuffer);
        
        console.log(`✅ Masked image saved to: ${outputPath}`);
        return true;
    }
}

// Usage
(async () => {
    const client = new AadhaarMaskingClient(
        'http://localhost:8000',
        'admin',
        'gravitonadmin'
    );

    // Login
    await client.login();

    // Mask Aadhaar
    const result = await client.maskAadhaar('aadhaar.jpg');

    if (result) {
        console.log('Job ID:', result.job_id);
        console.log('Status:', result.status);
        console.log('Masked Aadhaar:', result.extracted_info.AADHAR_NUMBER);
        console.log('Processing time:', result.performance['5_total_request_ms'].toFixed(2), 'ms');

        // Save masked image
        client.saveMaskedImage(result, 'masked_aadhaar.jpg');
    }
})();
```

---

### PHP

```php
<?php

class AadhaarMaskingClient {
    private $baseUrl;
    private $username;
    private $password;
    private $token;

    public function __construct($baseUrl, $username, $password) {
        $this->baseUrl = $baseUrl;
        $this->username = $username;
        $this->password = $password;
    }

    public function login() {
        $ch = curl_init($this->baseUrl . '/api/auth/token');
        
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode([
            'username' => $this->username,
            'password' => $this->password
        ]));
        curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        
        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        
        if ($httpCode === 200) {
            $data = json_decode($response, true);
            $this->token = $data['token'];
            echo "✅ Login successful! Token expires at: " . $data['expires_at'] . "\n";
            return true;
        } else {
            echo "❌ Login failed: $response\n";
            return false;
        }
    }

    public function maskAadhaar($imagePath, $includeAllRotations = false) {
        if (!$this->token) {
            echo "⚠️  Not authenticated. Logging in...\n";
            if (!$this->login()) {
                return null;
            }
        }

        $ch = curl_init($this->baseUrl . '/api/aadhaar/upload');
        
        $postFields = [
            'file' => new CURLFile($imagePath),
            'include_all_rotations' => $includeAllRotations ? 'true' : 'false'
        ];
        
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, $postFields);
        curl_setopt($ch, CURLOPT_HTTPHEADER, [
            'Authorization: Bearer ' . $this->token
        ]);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        
        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        
        if ($httpCode === 200) {
            return json_decode($response, true);
        } elseif ($httpCode === 422) {
            echo "⚠️  No Aadhaar detected in image\n";
            return json_decode($response, true);
        } elseif ($httpCode === 401) {
            echo "🔄 Token expired. Re-authenticating...\n";
            $this->login();
            return $this->maskAadhaar($imagePath, $includeAllRotations);
        } else {
            echo "❌ Error: $httpCode - $response\n";
            return null;
        }
    }

    public function saveMaskedImage($result, $outputPath) {
        if (!isset($result['masked_image_base64'])) {
            echo "❌ No image data in response\n";
            return false;
        }

        $imageData = base64_decode($result['masked_image_base64']);
        file_put_contents($outputPath, $imageData);
        
        echo "✅ Masked image saved to: $outputPath\n";
        return true;
    }
}

// Usage
$client = new AadhaarMaskingClient(
    'http://localhost:8000',
    'admin',
    'gravitonadmin'
);

// Login
$client->login();

// Mask Aadhaar
$result = $client->maskAadhaar('aadhaar.jpg');

if ($result) {
    echo "Job ID: " . $result['job_id'] . "\n";
    echo "Status: " . $result['status'] . "\n";
    echo "Masked Aadhaar: " . $result['extracted_info']['AADHAR_NUMBER'] . "\n";
    echo "Processing time: " . number_format($result['performance']['5_total_request_ms'], 2) . "ms\n";

    // Save masked image
    $client->saveMaskedImage($result, 'masked_aadhaar.jpg');
}
```

---

### Java

```java
import java.io.*;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.file.Files;
import java.util.Base64;
import org.json.JSONObject;

public class AadhaarMaskingClient {
    private String baseUrl;
    private String username;
    private String password;
    private String token;

    public AadhaarMaskingClient(String baseUrl, String username, String password) {
        this.baseUrl = baseUrl;
        this.username = username;
        this.password = password;
    }

    public boolean login() throws IOException {
        URL url = new URL(baseUrl + "/api/auth/token");
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        
        conn.setRequestMethod("POST");
        conn.setRequestProperty("Content-Type", "application/json");
        conn.setDoOutput(true);

        String jsonBody = String.format("{\"username\":\"%s\",\"password\":\"%s\"}", 
                                       username, password);
        
        try (OutputStream os = conn.getOutputStream()) {
            os.write(jsonBody.getBytes());
        }

        int responseCode = conn.getResponseCode();
        if (responseCode == 200) {
            BufferedReader in = new BufferedReader(new InputStreamReader(conn.getInputStream()));
            String response = in.readLine();
            in.close();

            JSONObject json = new JSONObject(response);
            this.token = json.getString("token");
            System.out.println("✅ Login successful! Token expires at: " + json.getString("expires_at"));
            return true;
        } else {
            System.out.println("❌ Login failed: " + responseCode);
            return false;
        }
    }

    public JSONObject maskAadhaar(String imagePath, boolean includeAllRotations) throws IOException {
        if (token == null) {
            System.out.println("⚠️  Not authenticated. Logging in...");
            if (!login()) {
                return null;
            }
        }

        String boundary = "----Boundary" + System.currentTimeMillis();
        URL url = new URL(baseUrl + "/api/aadhaar/upload");
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        
        conn.setRequestMethod("POST");
        conn.setRequestProperty("Content-Type", "multipart/form-data; boundary=" + boundary);
        conn.setRequestProperty("Authorization", "Bearer " + token);
        conn.setDoOutput(true);

        try (OutputStream os = conn.getOutputStream();
             PrintWriter writer = new PrintWriter(new OutputStreamWriter(os, "UTF-8"), true)) {

            // Add image file
            writer.append("--" + boundary).append("\r\n");
            writer.append("Content-Disposition: form-data; name=\"file\"; filename=\"" + 
                         new File(imagePath).getName() + "\"").append("\r\n");
            writer.append("Content-Type: image/jpeg").append("\r\n\r\n");
            writer.flush();

            Files.copy(new File(imagePath).toPath(), os);
            os.flush();
            writer.append("\r\n");

            // Add rotation parameter
            writer.append("--" + boundary).append("\r\n");
            writer.append("Content-Disposition: form-data; name=\"include_all_rotations\"").append("\r\n\r\n");
            writer.append(String.valueOf(includeAllRotations)).append("\r\n");
            writer.append("--" + boundary + "--").append("\r\n");
            writer.flush();
        }

        int responseCode = conn.getResponseCode();
        BufferedReader in = new BufferedReader(new InputStreamReader(
            responseCode == 200 || responseCode == 422 ? conn.getInputStream() : conn.getErrorStream()
        ));
        
        StringBuilder response = new StringBuilder();
        String line;
        while ((line = in.readLine()) != null) {
            response.append(line);
        }
        in.close();

        if (responseCode == 200 || responseCode == 422) {
            return new JSONObject(response.toString());
        } else if (responseCode == 401) {
            System.out.println("🔄 Token expired. Re-authenticating...");
            login();
            return maskAadhaar(imagePath, includeAllRotations);
        } else {
            System.out.println("❌ Error: " + responseCode + " - " + response);
            return null;
        }
    }

    public boolean saveMaskedImage(JSONObject result, String outputPath) throws IOException {
        if (!result.has("masked_image_base64")) {
            System.out.println("❌ No image data in response");
            return false;
        }

        String base64Image = result.getString("masked_image_base64");
        byte[] imageBytes = Base64.getDecoder().decode(base64Image);
        
        try (FileOutputStream fos = new FileOutputStream(outputPath)) {
            fos.write(imageBytes);
        }

        System.out.println("✅ Masked image saved to: " + outputPath);
        return true;
    }

    // Usage example
    public static void main(String[] args) {
        try {
            AadhaarMaskingClient client = new AadhaarMaskingClient(
                "http://localhost:8000",
                "admin",
                "gravitonadmin"
            );

            // Login
            client.login();

            // Mask Aadhaar
            JSONObject result = client.maskAadhaar("aadhaar.jpg", false);

            if (result != null) {
                System.out.println("Job ID: " + result.getString("job_id"));
                System.out.println("Status: " + result.getString("status"));
                System.out.println("Masked Aadhaar: " + 
                    result.getJSONObject("extracted_info").getString("AADHAR_NUMBER"));
                
                // Save masked image
                client.saveMaskedImage(result, "masked_aadhaar.jpg");
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
```

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | Action Required |
|------|---------|-----------------|
| `200` | Success - Aadhaar detected and masked | Process the masked image |
| `422` | No Aadhaar detected | Inform user or retry with different image |
| `400` | Bad Request - Invalid file or parameters | Check file type and parameters |
| `401` | Unauthorized - Invalid/expired token | Refresh token and retry |
| `500` | Internal Server Error | Retry or contact support |

### Common Error Scenarios

#### 1. Token Expiration
```python
def make_api_call_with_retry(client, image_path):
    """Automatically retry with fresh token on 401"""
    try:
        return client.mask_aadhaar(image_path)
    except requests.HTTPError as e:
        if e.response.status_code == 401:
            # Re-authenticate and retry
            client.login()
            return client.mask_aadhaar(image_path)
        raise
```

#### 2. No Aadhaar Detected (422)
```python
result = client.mask_aadhaar("image.jpg")
if result and result.get("status") == "no_detection":
    print("⚠️  No Aadhaar card detected in this image")
    # Option 1: Try with comprehensive rotation mode
    result = client.mask_aadhaar("image.jpg", include_all_rotations=True)
    # Option 2: Inform user to provide clearer image
```

#### 3. Network Errors
```python
import time

def upload_with_retry(client, image_path, max_retries=3):
    """Retry logic for network failures"""
    for attempt in range(max_retries):
        try:
            return client.mask_aadhaar(image_path)
        except requests.exceptions.ConnectionError:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"🔄 Connection failed. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise
```

---

## Rate Limits & Best Practices

### Performance Optimization

#### 1. Rotation Mode Selection
```python
# Fast mode (recommended for most cases) - ~250ms
result = client.mask_aadhaar("aadhaar.jpg", include_all_rotations=False)

# Comprehensive mode (for difficult images) - ~2-3 seconds
result = client.mask_aadhaar("aadhaar.jpg", include_all_rotations=True)
```

**When to use comprehensive mode:**
- Image is rotated at unusual angles (not 0°, 90°, 180°, 270°)
- Fast mode returns no detection
- Image quality is poor or skewed

#### 2. Token Reuse
```python
class AadhaarMaskingClient:
    def __init__(self, base_url, username, password):
        # ... initialization ...
        self.token_expires_at = None
    
    def is_token_valid(self):
        """Check if current token is still valid"""
        if not self.token or not self.token_expires_at:
            return False
        
        from datetime import datetime
        expires = datetime.fromisoformat(self.token_expires_at.replace('Z', '+00:00'))
        # Add 30-second buffer before expiration
        return datetime.now() < expires - timedelta(seconds=30)
    
    def ensure_authenticated(self):
        """Login only if token is expired"""
        if not self.is_token_valid():
            self.login()
```

#### 3. Batch Processing
```python
def process_multiple_images(client, image_paths):
    """Process multiple images efficiently"""
    client.login()  # Login once
    
    results = []
    for image_path in image_paths:
        result = client.mask_aadhaar(image_path)
        results.append(result)
        
        # Optional: Add small delay to avoid overwhelming server
        # time.sleep(0.1)
    
    return results
```

### Best Practices

1. **Reuse Tokens:** Don't login for every request - tokens are valid for 5 minutes
2. **Handle Expiration:** Implement automatic token refresh on 401 errors
3. **Use Fast Mode:** Set `include_all_rotations=false` for 90% of cases
4. **Error Handling:** Always check status codes and handle 422 gracefully
5. **Connection Pooling:** Use session objects for multiple requests
6. **Timeout Configuration:** Set reasonable timeouts (30-60 seconds)
7. **Secure Storage:** Never hardcode credentials - use environment variables

---

## Security Considerations

### 1. Credential Management

```python
import os
from dotenv import load_dotenv

# Load from environment variables
load_dotenv()

client = AadhaarMaskingClient(
    base_url=os.getenv("AADHAAR_API_URL"),
    username=os.getenv("AADHAAR_API_USERNAME"),
    password=os.getenv("AADHAAR_API_PASSWORD")
)
```

**Never:**
- Hardcode credentials in source code
- Commit credentials to version control
- Log tokens or credentials
- Share tokens between different applications

### 2. HTTPS in Production

```python
# ✅ Production (HTTPS)
client = AadhaarMaskingClient(
    base_url="https://api.yourdomain.com",
    username=username,
    password=password
)

# ⚠️  Development only (HTTP)
client = AadhaarMaskingClient(
    base_url="http://localhost:8000",
    username=username,
    password=password
)
```

### 3. Data Privacy

The API is designed for GDPR compliance:
- ✅ **No disk storage:** All processing done in memory
- ✅ **No logging:** Uploaded images are not logged
- ✅ **No retention:** Images are discarded after response
- ✅ **Secure transport:** Use HTTPS in production

### 4. Token Security

```python
# Store tokens securely in memory (not on disk)
class SecureTokenStorage:
    def __init__(self):
        self._token = None
    
    def set_token(self, token):
        self._token = token
    
    def get_token(self):
        return self._token
    
    def clear_token(self):
        self._token = None
```

---

## Troubleshooting

### Common Issues

#### 1. "Invalid or expired authorization token"
**Cause:** Token has expired (5-minute validity)  
**Solution:** Implement automatic token refresh
```python
if response.status_code == 401:
    client.login()
    # Retry the request
```

#### 2. "No Aadhaar detected" (Status 422)
**Cause:** Image doesn't contain Aadhaar card or is of poor quality  
**Solutions:**
1. Try with `include_all_rotations=true`
2. Ensure image is clear and well-lit
3. Check if image actually contains an Aadhaar card

#### 3. Slow Processing Times
**Cause:** Using comprehensive rotation mode  
**Solution:** Use fast mode (default) for 90% of cases
```python
# Fast: ~250ms
result = client.mask_aadhaar("image.jpg", include_all_rotations=False)

# Slow: ~2-3 seconds
result = client.mask_aadhaar("image.jpg", include_all_rotations=True)
```

#### 4. Connection Timeout
**Cause:** Network issues or server overload  
**Solution:** Increase timeout and implement retry logic
```python
import requests

response = requests.post(
    url,
    headers=headers,
    files=files,
    timeout=60  # 60 seconds timeout
)
```

#### 5. "File must be an image" Error
**Cause:** Wrong file type or corrupted file  
**Solution:** Validate file before uploading
```python
import mimetypes

def validate_image(file_path):
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type and mime_type.startswith('image/')

if validate_image("file.jpg"):
    result = client.mask_aadhaar("file.jpg")
```

---

## Performance Metrics

The API returns detailed performance metrics in every response:

```json
{
  "performance": {
    "1_file_read_ms": 5.2,           // Time to read uploaded file
    "2_image_decode_ms": 12.4,        // Time to decode image
    "3a_preprocessing_ms": 0.1,       // Preprocessing time
    "3b_model_forward_ms": 245.6,     // AI model inference time
    "3_model_inference_total_ms": 245.7,  // Total model time
    "4a_postproc_validation_ms": 8.3, // Validation and masking
    "4b_image_encode_ms": 15.1,       // Encoding masked image
    "5_total_request_ms": 286.7       // Total end-to-end time
  }
}
```

### Performance Benchmarks

| Mode | Average Time | Use Case |
|------|--------------|----------|
| Fast (4 rotations) | ~250-300ms | Most Aadhaar cards |
| Comprehensive (24 rotations) | ~2-3 seconds | Unusual angles |

---

## Support & Feedback

### Getting Help

1. **Check API Status:** `GET /health`
2. **Review Error Messages:** All errors include descriptive messages
3. **Check Performance Metrics:** Use timing data to identify bottlenecks
4. **Contact Support:** Provide `job_id` from response for faster resolution

### API Versioning

Current version: **2.0.0**

Check version: `GET /` returns `"version": "2.0.0"`

---

## Appendix

### Response Field Reference

| Field | Type | Description |
|-------|------|-------------|
| `job_id` | string | Unique identifier for this request |
| `status` | string | `"completed"` or `"no_detection"` |
| `original_filename` | string | Name of uploaded file |
| `extracted_info.AADHAR_NUMBER` | string | Masked Aadhaar (e.g., "XXXX XXXX 1234") |
| `masked_image_base64` | string | Base64-encoded masked image |
| `image_format` | string | Image format (always "jpeg") |
| `data_uri` | string | Ready-to-use data URI for HTML |
| `processed_at` | string | ISO 8601 timestamp |
| `performance` | object | Detailed performance metrics |

### Environment Variables (Self-Hosting)

```bash
# Required for authentication
SECRET_KEY=your-secret-key-here

# Optional (defaults shown)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=gravitonadmin
```

### System Requirements (Self-Hosting)

- Python 3.8+
- 2GB RAM minimum (4GB recommended)
- Tesseract OCR
- YOLO model weights

---

## Quick Reference Card

```bash
# 1. Login
POST /api/auth/token
Body: {"username": "admin", "password": "gravitonadmin"}

# 2. Upload (Fast Mode)
POST /api/aadhaar/upload
Header: Authorization: Bearer <token>
Body: file=@aadhaar.jpg, include_all_rotations=false

# 3. Upload (Comprehensive Mode)
POST /api/aadhaar/upload
Header: Authorization: Bearer <token>
Body: file=@aadhaar.jpg, include_all_rotations=true

# 4. Health Check
GET /health
```

---

**Last Updated:** 2025-11-22  
**API Version:** 2.0.0  
**Documentation Version:** 1.0
