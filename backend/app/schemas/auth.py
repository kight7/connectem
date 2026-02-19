"""
VibeLink Auth Schemas — Pydantic v2 request/response models for the auth system.
"""

import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# ─── REQUEST SCHEMAS ──────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    """Schema for new user registration."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    full_name: str | None = Field(default=None, max_length=100)

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("Username may only contain letters, numbers, and underscores")
        return v.lower()


class LoginRequest(BaseModel):
    """Schema for user login with email + password."""
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    """Schema for submitting a refresh token to get a new access token."""
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    """Schema for requesting a password reset email."""
    email: EmailStr


class PasswordResetRequest(BaseModel):
    """Schema for resetting password using a token from email."""
    token: str
    new_password: str = Field(..., min_length=8)


# ─── RESPONSE SCHEMAS ─────────────────────────────────────────────────────────

class UserResponse(BaseModel):
    """Schema returned to the client representing a user profile."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    email: str
    full_name: str | None
    bio: str | None
    avatar_url: str | None
    city: str | None
    interests: list[str] | None
    is_verified: bool
    created_at: datetime


class TokenResponse(BaseModel):
    """Schema returned after a successful login or token refresh."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds until access token expiry


class MessageResponse(BaseModel):
    """Generic success/failure message response."""
    message: str
    success: bool = True


# ─── PROFILE UPDATE SCHEMA ────────────────────────────────────────────────────

class UpdateProfileRequest(BaseModel):
    """Schema for partially updating a user's profile. All fields are optional."""
    full_name: str | None = Field(default=None, max_length=100)
    bio: str | None = Field(default=None, max_length=500)
    city: str | None = Field(default=None, max_length=100)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    interests: list[str] | None = Field(default=None, max_length=10)