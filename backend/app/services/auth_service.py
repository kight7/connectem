"""
AuthService — all business logic for registration, login, token refresh, and logout.
"""

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.user import RefreshToken, User
from backend.app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)
from backend.app.utils.jwt import (
    create_access_token,
    create_refresh_token,
    hash_refresh_token,
)
from backend.app.utils.security import hash_password, verify_password
from backend.app.config import settings


class AuthService:

    async def register(self, db: AsyncSession, data: RegisterRequest) -> User:
        """Register a new user. Raises 409 if email or username already exists."""

        # Check email
        result = await db.execute(select(User).where(User.email == data.email))
        if result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        # Check username
        result = await db.execute(select(User).where(User.username == data.username))
        if result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken",
            )

        user = User(
            email=data.email,
            username=data.username,
            password_hash=hash_password(data.password),
            full_name=data.full_name,
            is_active=True,
            is_verified=False,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    async def login(self, db: AsyncSession, data: LoginRequest) -> TokenResponse:
        """Authenticate user and return access + refresh tokens."""

        result = await db.execute(select(User).where(User.email == data.email))
        user = result.scalars().first()

        # Same error for wrong email OR wrong password (prevents user enumeration)
        if not user or not verify_password(data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled",
            )

        access_token = create_access_token({"sub": str(user.id)})
        raw_refresh, expires_at = create_refresh_token(str(user.id))

        db.add(RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(raw_refresh),
            expires_at=expires_at,
            is_revoked=False,
        ))
        await db.commit()

        return TokenResponse(
            access_token=access_token,
            refresh_token=raw_refresh,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def refresh(self, db: AsyncSession, refresh_token: str) -> TokenResponse:
        """Issue a new access token from a valid refresh token."""

        token_hash = hash_refresh_token(refresh_token)
        result = await db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        record = result.scalars().first()

        if not record:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Invalid refresh token")

        if record.is_revoked:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Refresh token has been revoked")

        if record.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Refresh token has expired")

        access_token = create_access_token({"sub": str(record.user_id)})

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def logout(self, db: AsyncSession, refresh_token: str) -> None:
        """Revoke a refresh token, invalidating that session."""

        token_hash = hash_refresh_token(refresh_token)
        result = await db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        record = result.scalars().first()

        if record:
            record.is_revoked = True
            await db.commit()