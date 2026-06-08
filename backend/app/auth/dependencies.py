# backend/app/auth/dependencies.py

"""FastAPI dependency utilities for JWT based authentication.

Provides:
- `get_current_user` – validates the JWT from the Authorization header and returns a `UserRead`.
- Helper `get_user_by_id` for DB lookup.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
import aiosqlite

from app.settings import settings
from .jwt_handler import decode_token, TokenData
from .schemas import UserRead

# OAuth2 scheme expects a Bearer token in the Authorization header.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_user_by_id(user_id: str) -> UserRead | None:
    async with aiosqlite.connect(settings.MEMORY_DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, email, created_at FROM users WHERE id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
        await cursor.close()
        if row:
            return UserRead(id=row[0], email=row[1], created_at=row[2])
    return None

async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserRead:
    """Validate JWT and return the associated user.
    Raises 401 if token is missing, malformed, or user does not exist.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token_data: TokenData = decode_token(token)
        if token_data.user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = await get_user_by_id(token_data.user_id)
    if user is None:
        raise credentials_exception
    return user
