"""API router configuration."""
from fastapi import APIRouter

from app.api.endpoints import health, google_alerts, companies, crunchbase, pipeline

api_router = APIRouter()

# Include routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(google_alerts.router, tags=["google-alerts"])
api_router.include_router(companies.router, prefix="/companies", tags=["companies"])
api_router.include_router(crunchbase.router, prefix="/crunchbase", tags=["crunchbase"])
api_router.include_router(pipeline.router, prefix="/pipeline", tags=["pipeline"])
