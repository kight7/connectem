"""
Auth Router — REST endpoints for registration, login, token management, and profile.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database import get_db
from backend.app.dependencies import get_current_user
from backend.app.models.user import User
from backend.app.schemas.auth import (
    LoginRequest,
    MessageResponse,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UpdateProfileRequest,
    UserResponse,
)
from backend.app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])
auth_service = AuthService()


@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user account."""
    user = await auth_service.register(db, data)
    return {
        "success": True,
        "data": UserResponse.model_validate(user),
        "message": "Registration successful",
    }


@router.post("/login", response_model=dict)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login with email and password, returns access + refresh tokens."""
    tokens = await auth_service.login(db, data)
    return {
        "success": True,
        "data": tokens,
        "message": "Login successful",
    }


@router.post("/refresh", response_model=dict)
async def refresh_token(data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """Exchange a valid refresh token for a new access token."""
    tokens = await auth_service.refresh(db, data.refresh_token)
    return {
        "success": True,
        "data": tokens,
        "message": "Token refreshed successfully",
    }


@router.post("/logout", response_model=dict)
async def logout(
    data: RefreshTokenRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Revoke a refresh token, logging the user out of that session."""
    await auth_service.logout(db, data.refresh_token)
    return {
        "success": True,
        "data": MessageResponse(message="Logged out successfully"),
        "message": "Logged out successfully",
    }


@router.get("/me", response_model=dict)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Get the authenticated user's profile."""
    return {
        "success": True,
        "data": UserResponse.model_validate(current_user),
        "message": "Profile retrieved successfully",
    }


@router.patch("/me", response_model=dict)
async def update_profile(
    data: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the authenticated user's profile."""
    # Only update fields that are explicitly set (not None)
    if data.full_name is not None:
        current_user.full_name = data.full_name
    if data.bio is not None:
        current_user.bio = data.bio
    if data.city is not None:
        current_user.city = data.city
    if data.latitude is not None:
        current_user.latitude = data.latitude
    if data.longitude is not None:
        current_user.longitude = data.longitude
    if data.interests is not None:
        current_user.interests = data.interests

    await db.commit()
    await db.refresh(current_user)

    return {
        "success": True,
        "data": UserResponse.model_validate(current_user),
        "message": "Profile updated successfully",
    }