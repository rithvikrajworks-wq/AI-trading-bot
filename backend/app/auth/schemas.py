# backend/app/auth/schemas.py

"""Pydantic models for authentication endpoints."""

from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="Plaintext password")

class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="Plaintext password")

class UserRead(BaseModel):
    id: str = Field(..., description="User UUID")
    email: EmailStr = Field(..., description="User email")
    created_at: float = Field(..., description="Unix timestamp of creation")

class Token(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")
