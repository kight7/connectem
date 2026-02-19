from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import settings
from backend.app.routers.hangout import hangout_router
# Initialize the API
app = FastAPI(
    title="ConnectEm API",
    version="1.0.0"
)

# Setup CORS (Security for who can talk to your API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# A simple health check to see if the server is running
@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "ok", 
        "environment": settings.ENVIRONMENT
    }

# This runs when the server starts
@app.on_event("startup")
async def startup_event():
    print("ConnectEm API started")

from backend.app.routers import auth

# After creating the app, before startup event:
app.include_router(auth.router, prefix="/api/v1")
app.include_router(hangout_router, prefix="/api/v1")