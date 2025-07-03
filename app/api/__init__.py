"""API router configuration."""
from fastapi import APIRouter

from app.api import health, google_alerts, companies

api_router = APIRouter()

# Include routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(google_alerts.router, tags=["google-alerts"])
api_router.include_router(companies.router, prefix="/companies", tags=["companies"])
