# backend/app/auth/auth.py

"""FastAPI router handling user registration, login, and profile retrieval.
All operations are async and use the shared SQLite DB (settings.MEMORY_DB_PATH).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
import aiosqlite
import uuid
import time

from app.settings import settings
from .schemas import UserCreate, UserRead, Token
from .password_utils import hash_password, verify_password
from .jwt_handler import create_access_token
from .dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    async with aiosqlite.connect(settings.MEMORY_DB_PATH) as db:
        # Ensure email is unique
        cursor = await db.execute("SELECT id FROM users WHERE email = ?", (user.email,))
        existing = await cursor.fetchone()
        await cursor.close()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        hashed = hash_password(user.password)
        user_id = uuid.uuid4().hex
        created_at = time.time()
        await db.execute(
            "INSERT INTO users (id, email, hashed_password, created_at) VALUES (?, ?, ?, ?)",
            (user_id, user.email, hashed, created_at),
        )
        await db.commit()
        return UserRead(id=user_id, email=user.email, created_at=created_at)

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    async with aiosqlite.connect(settings.MEMORY_DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, hashed_password FROM users WHERE email = ?",
            (form_data.username,),
        )
        row = await cursor.fetchone()
        await cursor.close()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )
        user_id, hashed = row
        if not verify_password(form_data.password, hashed):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )
        access_token = create_access_token({"user_id": user_id})
        return Token(access_token=access_token, token_type="bearer")

@router.get("/me", response_model=UserRead)
async def read_current_user(current_user: UserRead = Depends(get_current_user)):
    return current_user
