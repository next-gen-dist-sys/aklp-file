"""API v1 package."""

from fastapi import APIRouter

from app.api.v1.endpoints import files

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(files.router, prefix="/files", tags=["files"])
