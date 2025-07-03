"""FastAPI application entry point."""
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import api_router
from app.core.config import settings
from app.core.scheduler import get_scheduler
from app.core.snapshot import SnapshotService
from app.services.updater.airtable import AirtableUpdater
from app.services.updater.zerodb import ZeroDBUpdater

snapshot_service = SnapshotService()
airtable_updater = AirtableUpdater()
zerodb_updater = ZeroDBUpdater()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Startup Funding Tracker & Dashboard Automation",
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Set up CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

# API v1 router
@app.get(f"{settings.API_V1_STR}/health")
async def api_v1_health_check():
    """API v1 health check."""
    return {"status": "ok"}

# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )

# Application startup event
@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    logger.info("Starting up application...")
    
    # Initialize scheduler
    scheduler = await get_scheduler()
    await scheduler.start()
    logger.info("Scheduler started")

    # Initialize snapshot service
    await snapshot_service.initialize()
    logger.info("Snapshot service initialized")

    # Initialize updaters
    await airtable_updater.initialize()
    logger.info("Airtable updater initialized")
    await zerodb_updater.initialize()
    logger.info("ZeroDB updater initialized")

# Application shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    logger.info("Shutting down application...")
    
    # Shutdown scheduler
    scheduler = await get_scheduler()
    await scheduler.stop()
    logger.info("Scheduler stopped")

    # Shutdown snapshot service
    await snapshot_service.shutdown()
    logger.info("Snapshot service shut down")

    # Shutdown updaters
    await airtable_updater.shutdown()
    logger.info("Airtable updater shut down")
    await zerodb_updater.shutdown()
    logger.info("ZeroDB updater shut down")
