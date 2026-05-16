from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.health import router as health_router

# This router serves as the entry point for all API endpoints and 
# aggregates specific domain-based routers (auth, health, etc.).
api_router = APIRouter()


# Authentication: Endpoints for user login, registration, and token management.
api_router.include_router(router=auth_router)

# Health Checks: Endpoints for monitoring application status and connectivity.
api_router.include_router(router=health_router)