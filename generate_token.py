#!/usr/bin/env python3
"""
Token Generator for Graviton Aadhaar API
Generates time-based HMAC-SHA256 authentication tokens
"""

import hmac
import hashlib
import base64
import time
from datetime import datetime, timedelta

# ==================== CONFIGURATION ====================
SECRET_KEY = "GRAVITON_AADHAAR_SECURE_2024"  # Must match server secret
VALIDITY_MINUTES = 5  # Token validity period

def generate_token(timestamp=None):
    """
    Generate authentication token using HMAC-SHA256
    
    Args:
        timestamp: Optional custom timestamp (for testing)
    
    Returns:
        str: Base64 encoded authentication token
    """
    if timestamp is None:
        timestamp = int(time.time())
    
    # Create message from timestamp
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

def decode_token(token):
    """
    Decode and display token information (for debugging)
    
    Args:
        token: Base64 encoded token
    
    Returns:
        dict: Token information
    """
    try:
        decoded = base64.b64decode(token.encode('utf-8')).decode('utf-8')
        parts = decoded.split('|')
        
        if len(parts) == 2:
            timestamp, signature = parts
            created_at = datetime.fromtimestamp(int(timestamp))
            expires_at = created_at + timedelta(minutes=VALIDITY_MINUTES)
            current_time = datetime.now()
            is_expired = current_time > expires_at
            time_remaining = (expires_at - current_time).total_seconds()
            
            return {
                "timestamp": timestamp,
                "signature": signature,
                "created_at": created_at,
                "expires_at": expires_at,
                "is_expired": is_expired,
                "time_remaining_seconds": max(0, time_remaining)
            }
        else:
            return {"error": "Invalid token format"}
    except Exception as e:
        return {"error": str(e)}

def main():
    """Main function to generate and display token"""
    print("\n" + "="*70)
    print("🔑 GRAVITON AADHAAR API - TOKEN GENERATOR")
    print("="*70)
    
    # Generate token
    token = generate_token()
    timestamp = int(time.time())
    created_at = datetime.now()
    expires_at = created_at + timedelta(minutes=VALIDITY_MINUTES)
    
    # Display token information
    print(f"\n📅 Generated at: {created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏰ Expires at:   {expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏱️  Valid for:    {VALIDITY_MINUTES} minutes")
    print(f"🔢 Timestamp:    {timestamp}")
    
    print("\n" + "-"*70)
    print("🎫 YOUR TOKEN:")
    print("-"*70)
    print(f"\n{token}\n")
    
    print("-"*70)
    print("📋 USAGE EXAMPLES:")
    print("-"*70)
    
    # cURL example
    print("\n1️⃣  cURL:")
    print(f"""
curl -X POST http://localhost:8000/api/aadhaar/upload \\
  -H "Authorization: Bearer {token}" \\
  -F "file=@aadhaar.jpg"
""")
    
    # Python example
    print("2️⃣  Python (requests):")
    print(f"""
import requests

headers = {{"Authorization": "Bearer {token}"}}
files = {{"file": open("aadhaar.jpg", "rb")}}
response = requests.post(
    "http://localhost:8000/api/aadhaar/upload",
    headers=headers,
    files=files
)
print(response.json())
""")
    
    # Postman example
    print("3️⃣  Postman:")
    print(f"""
Headers:
  Key: Authorization
  Value: Bearer {token}

Body:
  form-data
  Key: file (type: File)
  Value: Select your image
""")
    
    print("="*70)
    print("✅ Token generated successfully!")
    print("⚠️  Note: This token will expire in {} minutes".format(VALIDITY_MINUTES))
    print("="*70 + "\n")

if __name__ == "__main__":
    import sys
    
    # Check for decode mode
    if len(sys.argv) > 1:
        if sys.argv[1] == "--decode" and len(sys.argv) > 2:
            token = sys.argv[2]
            print("\n" + "="*70)
            print("🔍 TOKEN DECODER")
            print("="*70)
            info = decode_token(token)
            
            if "error" in info:
                print(f"\n❌ Error: {info['error']}\n")
            else:
                print(f"\n📅 Created at:     {info['created_at'].strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"⏰ Expires at:     {info['expires_at'].strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"⏱️  Time remaining: {int(info['time_remaining_seconds'])} seconds")
                print(f"🔢 Timestamp:      {info['timestamp']}")
                print(f"🔐 Signature:      {info['signature'][:32]}...")
                print(f"❓ Is expired:     {'YES ❌' if info['is_expired'] else 'NO ✅'}")
            
            print("="*70 + "\n")
        elif sys.argv[1] == "--help":
            print("""
Usage:
  python generate_token.py              Generate a new token
  python generate_token.py --decode <token>    Decode and verify a token
  python generate_token.py --help              Show this help message
            """)
        else:
            print("Unknown option. Use --help for usage information.")
    else:
        main()

