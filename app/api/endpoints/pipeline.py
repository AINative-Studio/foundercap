"""API endpoints for the data pipeline."""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field

from app.services.pipeline import get_pipeline
from app.api.dependencies.auth import get_current_user

router = APIRouter()


class CompanyProcessRequest(BaseModel):
    """Request model for processing a single company."""
    name: str = Field(..., description="Company name")
    domain: Optional[str] = Field(None, description="Company domain (optional)")
    force_update: bool = Field(False, description="Force fresh data fetch, bypassing cache")


class BatchProcessRequest(BaseModel):
    """Request model for batch processing companies."""
    companies: List[Dict[str, str]] = Field(..., description="List of companies with 'name' and optional 'domain'")
    max_concurrent: int = Field(3, ge=1, le=10, description="Maximum concurrent processes")


@router.post("/process-company")
async def process_company(
    request: CompanyProcessRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Process a single company through the data pipeline.
    
    This endpoint triggers the complete data pipeline for a company:
    1. Collects data from LinkedIn and Crunchbase
    2. Detects changes from previous snapshots
    3. Updates Airtable and ZeroDB
    4. Saves new snapshot
    """
    try:
        pipeline = get_pipeline()
        await pipeline.initialize()
        
        result = await pipeline.process_company(
            company_name=request.name,
            company_domain=request.domain,
            force_update=request.force_update
        )
        
        return {
            "success": True,
            "message": f"Company '{request.name}' processed successfully",
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing company: {str(e)}"
        )


@router.post("/process-batch")
async def process_companies_batch(
    request: BatchProcessRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Process multiple companies through the data pipeline concurrently."""
    try:
        pipeline = get_pipeline()
        await pipeline.initialize()
        
        results = await pipeline.process_companies_batch(
            companies=request.companies,
            max_concurrent=request.max_concurrent
        )
        
        # Count successes and errors
        success_count = sum(1 for r in results if r.get("status") == "success")
        error_count = len(results) - success_count
        
        return {
            "success": True,
            "message": f"Batch processing completed",
            "summary": {
                "total_companies": len(request.companies),
                "successful": success_count,
                "failed": error_count
            },
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing batch: {str(e)}"
        )


@router.get("/status")
async def get_pipeline_status() -> Dict[str, Any]:
    """Get the current status of the data pipeline."""
    try:
        pipeline = get_pipeline()
        status = await pipeline.get_pipeline_status()
        
        return {
            "success": True,
            "status": status
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting pipeline status: {str(e)}"
        )


@router.post("/initialize")
async def initialize_pipeline(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Initialize the data pipeline services."""
    try:
        pipeline = get_pipeline()
        await pipeline.initialize()
        
        return {
            "success": True,
            "message": "Pipeline initialized successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error initializing pipeline: {str(e)}"
        )


@router.post("/shutdown")
async def shutdown_pipeline(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Shutdown the data pipeline services."""
    try:
        pipeline = get_pipeline()
        await pipeline.shutdown()
        
        return {
            "success": True,
            "message": "Pipeline shut down successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error shutting down pipeline: {str(e)}"
        )