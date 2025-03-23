from firebase_admin import auth, credentials, initialize_app
import os
from dotenv import load_dotenv
from fastapi import HTTPException, Request
from functools import wraps
from pathlib import Path

# Load environment variables
load_dotenv()

# Get the service account path and convert relative to absolute
service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY_PATH')
if not service_account_path:
    raise ValueError("FIREBASE_SERVICE_ACCOUNT_KEY_PATH not found in environment variables")

# Convert relative path to absolute using the project root
project_root = Path(__file__).parent.parent.parent  # Go up three levels from auth/firebase_auth.py
absolute_path = project_root / service_account_path.lstrip("./")

if not absolute_path.exists():
    raise FileNotFoundError(f"Service account file not found at: {absolute_path}")

print(f"Looking for service account at: {os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY_PATH')}")

cred = credentials.Certificate(str(absolute_path))
firebase_app = initialize_app(cred)

async def verify_firebase_token(request: Request):
    """Verify Firebase JWT token from request headers"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="No token provided")
    
    token = auth_header.split(' ')[1]
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        print(f"Token verification error: {str(e)}")  # Add debugging
        raise HTTPException(status_code=401, detail="Invalid token")

def require_auth(func):
    """Decorator to protect routes with Firebase Authentication"""
    @wraps(func)
    async def wrapper(*args, request: Request, **kwargs):
        user_token = await verify_firebase_token(request)
        request.state.user = user_token
        return await func(*args, request=request, **kwargs)
    return wrapper 