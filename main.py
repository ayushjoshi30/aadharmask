"""
Graviton Backend API
FastAPI server for Aadhaar masking and document management
In-memory processing - no files stored on disk
With time-based HMAC authentication
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uuid
from datetime import datetime, timedelta
import base64
import cv2
import numpy as np
import hmac
import hashlib
import time

# Import the Aadhaar processor
from aadhaar_processor import process_single_image

# ==================== AUTH CONFIGURATION ====================
import os

SECRET_KEY = os.getenv("SECRET_KEY", "GRAVITON_AADHAAR_SECURE_2024")  # Change this to your secret key
TOKEN_VALIDITY_MINUTES = 5  # Token valid for 5 minutes

# Fixed credentials (can be overridden via environment variables)
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "gravitonadmin")

# ==================== REQUEST MODELS ====================
class LoginRequest(BaseModel):
    username: str
    password: str

# ==================== AUTH FUNCTIONS ====================
def generate_auth_token(timestamp: int = None) -> str:
    """
    Generate authentication token using HMAC-SHA256
    Format: timestamp|hmac_signature
    """
    if timestamp is None:
        timestamp = int(time.time())
    
    # Create message: timestamp
    message = str(timestamp).encode('utf-8')
    
    # Generate HMAC signature
    signature = hmac.new(
        SECRET_KEY.encode('utf-8'),
        message,
        hashlib.sha256
    ).hexdigest()
    
    # Combine timestamp and signature
    token = f"{timestamp}|{signature}"
    
    # Base64 encode for clean header value
    return base64.b64encode(token.encode('utf-8')).decode('utf-8')

def verify_auth_token(token: str) -> bool:
    """
    Verify the authentication token
    Returns True if valid, False otherwise
    """
    try:
        # Decode base64
        decoded = base64.b64decode(token.encode('utf-8')).decode('utf-8')
        
        # Split timestamp and signature
        parts = decoded.split('|')
        if len(parts) != 2:
            return False
        
        timestamp_str, received_signature = parts
        timestamp = int(timestamp_str)
        
        # Check if token is expired (within validity window)
        current_time = int(time.time())
        time_diff = current_time - timestamp
        
        if time_diff < 0 or time_diff > (TOKEN_VALIDITY_MINUTES * 60):
            return False
        
        # Regenerate signature and compare
        message = timestamp_str.encode('utf-8')
        expected_signature = hmac.new(
            SECRET_KEY.encode('utf-8'),
            message,
            hashlib.sha256
        ).hexdigest()
        
        # Secure comparison to prevent timing attacks
        return hmac.compare_digest(received_signature, expected_signature)
    
    except Exception:
        return False

async def verify_authorization(authorization: str = Header(None)):
    """
    Dependency to verify authorization header
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header"
        )
    
    # Extract token (support both "Bearer <token>" and direct token)
    token = authorization
    if authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
    
    if not verify_auth_token(token):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired authorization token"
        )
    
    return True

app = FastAPI(title="Graviton API", version="2.0.0")

# CORS Configuration - Allow access from any device on the network
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for local network access
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== STARTUP EVENT ====================
@app.on_event("startup")
async def startup_event():
    """
    Runs once when the server starts
    Model is loaded at this point (via module import)
    """
    from aadhaar_processor import model, MODEL_PATH
    
    print("\n" + "="*60)
    print("🎬 SERVER STARTUP")
    print("="*60)
    
    if model is not None:
        print(f"✅ YOLO Model loaded successfully")
        print(f"📁 Model path: {MODEL_PATH}")
        print(f"🔄 Model will be REUSED for all requests (no reload)")
    else:
        print("⚠️  WARNING: YOLO Model not loaded!")
        print("   Image processing will fail.")
    
    print("="*60 + "\n")

@app.get("/")
async def root():
    return {
        "message": "Graviton API is running (In-Memory Processing)",
        "version": "2.0.0",
        "description": "Secure API with username/password + time-based HMAC authentication",
        "endpoints": {
            "login": "/api/auth/token - Login with username/password to get token (POST)",
            "upload": "/api/aadhaar/upload - Upload image and get base64 result (requires auth). Returns 200 if masking applied, 422 if no masking applied.",
            "health": "/health - Health check (public)"
        },
        "status_codes": {
            "200": "Success - Aadhaar detected and masking applied",
            "422": "Unprocessable Entity - No Aadhaar detected or no masking applied",
            "401": "Unauthorized - Invalid or missing authentication token",
            "500": "Internal Server Error - Processing failed"
        },
        "authentication": {
            "type": "Username/Password + Time-based HMAC-SHA256",
            "login_endpoint": "POST /api/auth/token",
            "credentials": {
                "username": "Required in request body",
                "password": "Required in request body"
            },
            "token_header": "Authorization: Bearer <token>",
            "validity": f"{TOKEN_VALIDITY_MINUTES} minutes"
        }
    }

@app.post("/api/auth/token")
async def login_and_get_token(credentials: LoginRequest):
    """
    Authenticate with username/password and get authentication token
    
    Request body:
    {
        "username": "admin",
        "password": "gravitonadmin"
    }
    
    Returns a time-based HMAC token valid for 5 minutes
    """
    # Verify credentials
    if credentials.username != ADMIN_USERNAME or credentials.password != ADMIN_PASSWORD:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )
    
    # Generate token after successful authentication
    token = generate_auth_token()
    expires_at = datetime.now() + timedelta(minutes=TOKEN_VALIDITY_MINUTES)
    
    return {
        "success": True,
        "message": "Authentication successful",
        "token": token,
        "expires_at": expires_at.isoformat(),
        "validity_minutes": TOKEN_VALIDITY_MINUTES,
        "usage": {
            "header": "Authorization",
            "value": f"Bearer {token}",
            "example": "Authorization: Bearer <your_token_here>"
        }
    }

@app.post("/api/aadhaar/upload")
async def upload_aadhaar(
    file: UploadFile = File(...),
    authorized: bool = Depends(verify_authorization)
):
    """
    Upload an Aadhaar card image for masking
    Returns the masked image as base64 encoded string
    All processing done in memory - no files stored on disk
    
    Requires: Authorization header with valid token
    """
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Generate unique job ID for tracking
        job_id = str(uuid.uuid4())
        
        # Read file directly into memory
        image_bytes = await file.read()
        
        # Convert bytes to numpy array for OpenCV
        nparr = np.frombuffer(image_bytes, np.uint8)
        image_array = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image_array is None:
            raise HTTPException(status_code=400, detail="Invalid image file")
        
        # Process the image (in memory)
        try:
            result = process_single_image(image_array=image_array)
            
            if result is None:
                raise HTTPException(status_code=500, detail="Image processing failed")
            
            extracted_info, masked_image_array = result
            
            # Check if masking was actually applied
            # Method 1: Check extracted info
            aadhaar_number = extracted_info.get("AADHAR_NUMBER", "")
            info_has_detection = (
                aadhaar_number and 
                aadhaar_number != "Not detected" and 
                aadhaar_number != "XXXX XXXX XXXX"
            )
            
            # Method 2: Check if image was actually masked (has black pixels from masking)
            # Resize original image to match masked image dimensions for comparison
            original_resized = cv2.resize(image_array, (masked_image_array.shape[1], masked_image_array.shape[0]))
            
            # Check for black pixels (0,0,0) that indicate masking was applied
            # Masking uses (0,0,0) black color, so check if masked image has black pixels not in original
            # OpenCV uses BGR format, so check for [0, 0, 0] in BGR
            masked_black = np.all(masked_image_array == [0, 0, 0], axis=2)
            original_black = np.all(original_resized == [0, 0, 0], axis=2)
            
            # New black pixels = masking was applied (black pixels in masked but not in original)
            new_black_pixels = np.sum(masked_black & ~original_black)
            image_was_masked = new_black_pixels > 100  # Threshold: at least 100 pixels masked
            
            # Masking is applied if: (1) Aadhaar was detected OR (2) Black masking pixels are present
            masking_applied = info_has_detection or image_was_masked
            
            # Convert masked image array to base64
            # Encode as JPEG
            success, buffer = cv2.imencode('.jpg', masked_image_array)
            if not success:
                raise HTTPException(status_code=500, detail="Failed to encode masked image")
            
            image_bytes = buffer.tobytes()
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
            
            image_format = 'jpeg'
            
            # Prepare response with base64 image
            if masking_applied:
                # Masking was successfully applied
                response_data = {
                    "job_id": job_id,
                    "status": "completed",
                    "original_filename": file.filename,
                    "extracted_info": extracted_info,
                    "masked_image_base64": base64_image,
                    "image_format": image_format,
                    "data_uri": f"data:image/{image_format};base64,{base64_image}",
                    "processed_at": datetime.now().isoformat(),
                    "note": "Image processed in memory - no files stored on disk"
                }
                return JSONResponse(content=response_data, status_code=200)
            else:
                # No masking was applied - Aadhaar not detected
                response_data = {
                    "job_id": job_id,
                    "status": "no_detection",
                    "original_filename": file.filename,
                    "extracted_info": extracted_info,
                    "masked_image_base64": base64_image,
                    "image_format": image_format,
                    "data_uri": f"data:image/{image_format};base64,{base64_image}",
                    "processed_at": datetime.now().isoformat(),
                    "error": "Aadhaar card not detected or no masking applied",
                    "note": "Image processed but no Aadhaar detected - original image returned"
                }
                return JSONResponse(content=response_data, status_code=422)  # 422 Unprocessable Entity
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    import socket
    
    # Get local IP address
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    print("\n" + "="*60)
    print("🚀 Graviton Backend Server Starting...")
    print("="*60)
    print(f"📍 Local Access:    http://localhost:8000")
    print(f"🌐 Network Access:  http://{local_ip}:8000")
    print(f"📖 API Docs:        http://localhost:8000/docs")
    print("="*60)
    print("✨ In-Memory Processing - No files stored on disk")
    print("🔒 All images processed and returned as base64")
    print(f"🔐 Authentication:  Username/Password + HMAC-SHA256")
    print("="*60)
    print("\n🔑 Authentication Steps:")
    print("1. POST /api/auth/token with credentials:")
    print(f"   {{\"username\": \"{ADMIN_USERNAME}\", \"password\": \"***\"}}")
    print("2. Receive token (valid for 5 minutes)")
    print("3. Add header: Authorization: Bearer <token>")
    print("4. POST /api/aadhaar/upload - Upload with auth")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)

