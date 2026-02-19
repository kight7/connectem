from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "ConnectEm"
    ENVIRONMENT: str = "development"
    
    DATABASE_URL: str
    REDIS_URL: str  # <--- THIS WAS MISSING!
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    
    FRONTEND_URL: str
    ALLOWED_ORIGINS: List[str]
    # Development helpers
    DEV_AUTH_BYPASS: bool = False  # when true, allow a dev-only auth bypass for local testing
    DEV_AUTH_BYPASS_USER_EMAIL: str | None = None  # optionally specify which user to return

    class Config:
        env_file = ".env"

settings = Settings()