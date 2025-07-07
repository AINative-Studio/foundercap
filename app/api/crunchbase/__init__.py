"""Crunchbase API endpoints."""
from fastapi import APIRouter
from app.api.endpoints import crunchbase as crunchbase_endpoints

router = APIRouter()
router.include_router(
    crunchbase_endpoints.router,
    prefix="",
    tags=["crunchbase"],
)
