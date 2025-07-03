from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional

from app.worker.tasks import process_company_data

router = APIRouter()

class ProcessCompanyDataRequest(BaseModel):
    company_id: str = Field(..., description="Unique identifier for the company.")
    permalink: Optional[str] = Field(None, description="Crunchbase permalink for the company, if available.")

class ProcessCompanyDataResponse(BaseModel):
    message: str
    task_id: str

@router.post(
    "/process-data",
    response_model=ProcessCompanyDataResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger company data processing",
    description="Triggers an asynchronous task to scrape, diff, and update company data."
)
async def trigger_process_company_data(request: ProcessCompanyDataRequest):
    """Trigger company data processing.

    The task will run in the background.
    """
    task = process_company_data.apply_async(args=(request.company_id, request.permalink))
    return {"message": "Company data processing task initiated.", "task_id": task.id}
