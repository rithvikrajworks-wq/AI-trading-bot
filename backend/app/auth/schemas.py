# backend/app/auth/schemas.py

"""Pydantic models for authentication endpoints."""

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    email: str = Field(..., description="Username or email")
    password: str = Field(..., min_length=8, description="Plaintext password")


class UserLogin(BaseModel):
    email: str = Field(..., description="Username or email")
    password: str = Field(..., description="Plaintext password")


class UserRead(BaseModel):
    id: str = Field(..., description="User UUID")
    email: str = Field(..., description="Username or email")
    created_at: float = Field(..., description="Unix timestamp of creation")


class Token(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")