# backend/app/auth/jwt_handler.py

"""Utilities for creating and decoding JWT tokens.
All token operations use the secret and algorithm defined in settings.
"""

import datetime
from typing import Optional
from jose import JWTError, jwt
from pydantic import BaseModel
from app.settings import settings

class TokenData(BaseModel):
    user_id: Optional[str] = None


def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None) -> str:
    """Create a JWT access token.

    Args:
        data: Payload data to encode (e.g., {"user_id": "..."}).
        expires_delta: Optional timedelta for custom expiry.
    Returns:
        Encoded JWT string.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> TokenData:
    """Decode a JWT and return the contained payload.

    Raises JWTError if token is invalid or expired.
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id: str = payload.get("user_id")
        if user_id is None:
            raise JWTError("Missing user_id in token")
        return TokenData(user_id=user_id)
    except JWTError as e:
        raise e
