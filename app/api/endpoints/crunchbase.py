"""FastAPI router for Crunchbase API integration."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional, List
import logging

from app.services.crunchbase import (
    CrunchbaseService,
    CrunchbaseAPIError,
    CrunchbaseAuthError,
    CrunchbaseRateLimitError,
    CrunchbaseNotFoundError,
)
from app.api.dependencies.crunchbase import CrunchbaseDep
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/company/{domain}", response_model=Dict[str, Any])
async def get_company(
    domain: str,
    include_funding: bool = True,
    use_cache: bool = True,
    service: CrunchbaseService = CrunchbaseDep,
) -> Dict[str, Any]:
    """
    Get company data from Crunchbase by domain.
    
    Args:
        domain: Company domain (e.g., 'airbnb.com')
        include_funding: Whether to include funding information
        use_cache: Whether to use cached data if available
        
    Returns:
        Company data with optional funding information
    """
    try:
        if not include_funding:
            # For now, we always include funding as it's part of the same API call
            logger.warning("Basic company lookup without funding is not yet implemented")
            
        # Get company data with funding
        result = await service.get_company_by_domain(domain, use_cache=use_cache)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Company with domain '{domain}' not found on Crunchbase"
            )
            
        return {
            "success": True,
            "data": result,
            "source": "crunchbase",
            "cached": use_cache,
        }
        
    except HTTPException:
        raise
        
    except CrunchbaseAuthError as e:
        logger.error(f"Authentication error with Crunchbase API: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication with Crunchbase API failed"
        )
        
    except CrunchbaseRateLimitError as e:
        logger.warning(f"Rate limit exceeded with Crunchbase API: {e}")
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "success": False,
                "error": "Rate limit exceeded for Crunchbase API",
                "retry_after": 60  # seconds
            }
        )
        
    except CrunchbaseAPIError as e:
        logger.error(f"Error fetching data from Crunchbase: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error fetching data from Crunchbase: {str(e)}"
        )
        
    except Exception as e:
        logger.exception(f"Unexpected error in Crunchbase endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

@router.get("/search", response_model=Dict[str, Any])
async def search_companies(
    query: str = Query(..., min_length=2, max_length=100),
    limit: int = Query(10, ge=1, le=100),
    page: int = Query(1, ge=1),
    use_cache: bool = True,
    service: CrunchbaseService = CrunchbaseDep,
) -> Dict[str, Any]:
    """
    Search for companies on Crunchbase.
    
    Args:
        query: Search query (2-100 characters)
        limit: Maximum number of results per page (1-100)
        page: Page number (1-based)
        use_cache: Whether to use cached data if available
        
    Returns:
        Search results with pagination
    """
    try:
        results = await service.search_companies(
            query=query,
            limit=limit,
            page=page,
            use_cache=use_cache
        )
        
        return {
            "success": True,
            "query": query,
            "page": page,
            "limit": limit,
            "total": results.get("total_results", 0),
            "results": results.get("results", []),
            "source": "crunchbase",
            "cached": use_cache,
        }
        
    except HTTPException:
        raise
        
    except Exception as e:
        logger.exception(f"Error searching companies: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while searching for companies"
        )

@router.get("/funding/{company_id}", response_model=Dict[str, Any])
async def get_company_funding(
    company_id: str,
    refresh_cache: bool = False,
    service: CrunchbaseService = CrunchbaseDep,
) -> Dict[str, Any]:
    """
    Get funding information for a company by Crunchbase ID.
    
    Args:
        company_id: Crunchbase company ID
        refresh_cache: Whether to force a refresh of cached data
        
    Returns:
        Company funding information including all rounds
    """
    try:
        if refresh_cache:
            result = await service.refresh_company_cache(company_id)
        else:
            result = await service.get_company_funding(company_id)
            
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Funding information for company ID '{company_id}' not found"
            )
            
        return {
            "success": True,
            "data": result,
            "source": "crunchbase",
            "cached": not refresh_cache,
        }
        
    except HTTPException:
        raise
        
    except Exception as e:
        logger.exception(f"Error fetching funding data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching funding data"
        )

@router.post("/refresh/{company_id}", response_model=Dict[str, Any])
async def refresh_company_data(
    company_id: str,
    service: CrunchbaseService = CrunchbaseDep,
) -> Dict[str, Any]:
    """
    Force refresh of cached company data from Crunchbase.
    
    Args:
        company_id: Crunchbase company ID
        
    Returns:
        Refreshed company data
    """
    return await get_company_funding(company_id, refresh_cache=True, service=service)
