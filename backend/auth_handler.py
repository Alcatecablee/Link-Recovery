import jwt
from datetime import datetime, timedelta
from typing import Optional
from config import settings
from fastapi import HTTPException, Request

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generate a JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.algorithm
    )
    
    return encoded_jwt

def verify_token(token: str) -> dict:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.algorithm]
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

async def get_current_user(request: Request) -> dict:
    """Get current user from JWT token in cookie"""
    token = request.cookies.get("access_token")
    
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return payload