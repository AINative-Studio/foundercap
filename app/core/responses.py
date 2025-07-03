"""API response and exception utilities."""
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.requests import Request
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT

from app.schemas.base import (
    BaseResponseSchema,
    BulkOperationResponse,
    ErrorResponse,
    PaginatedResponse,
)

T = TypeVar('T')

class ApiResponse(JSONResponse):
    """Standard API response format."""
    
    def __init__(
        self,
        data: Any = None,
        status_code: int = HTTP_200_OK,
        message: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> None:
        """Initialize API response.
        
        Args:
            data: Response data
            status_code: HTTP status code
            message: Optional message
            headers: Optional headers
            **kwargs: Additional fields to include in the response
        """
        content = {
            "success": status_code < 400,
            "message": message or self._get_default_message(status_code),
            **kwargs
        }
        
        if data is not None:
            content["data"] = data
        
        super().__init__(
            content=jsonable_encoder(content),
            status_code=status_code,
            headers=headers,
        )
    
    @staticmethod
    def _get_default_message(status_code: int) -> str:
        """Get default message for status code."""
        messages = {
            status.HTTP_200_OK: "Operation successful",
            status.HTTP_201_CREATED: "Resource created successfully",
            status.HTTP_204_NO_CONTENT: "Resource deleted successfully",
            status.HTTP_400_BAD_REQUEST: "Bad request",
            status.HTTP_401_UNAUTHORIZED: "Not authenticated",
            status.HTTP_403_FORBIDDEN: "Permission denied",
            status.HTTP_404_NOT_FOUND: "Resource not found",
            status.HTTP_422_UNPROCESSABLE_ENTITY: "Validation error",
            status.HTTP_500_INTERNAL_SERVER_ERROR: "Internal server error",
        }
        return messages.get(status_code, "")


class SuccessResponse(ApiResponse):
    """Success response with 200 status code."""
    
    def __init__(
        self,
        data: Any = None,
        message: Optional[str] = None,
        **kwargs
    ) -> None:
        """Initialize success response."""
        super().__init__(
            data=data,
            status_code=HTTP_200_OK,
            message=message,
            **kwargs
        )


class CreatedResponse(ApiResponse):
    """Resource created response with 201 status code."""
    
    def __init__(
        self,
        data: Any = None,
        message: Optional[str] = None,
        location: Optional[str] = None,
        **kwargs
    ) -> None:
        """Initialize created response."""
        headers = {"Location": location} if location else None
        super().__init__(
            data=data,
            status_code=HTTP_201_CREATED,
            message=message,
            headers=headers,
            **kwargs
        )


class NoContentResponse(ApiResponse):
    """No content response with 204 status code."""
    
    def __init__(self, message: Optional[str] = None) -> None:
        """Initialize no content response."""
        super().__init__(
            data=None,
            status_code=HTTP_204_NO_CONTENT,
            message=message or "Resource deleted successfully"
        )


class PaginatedApiResponse(ApiResponse, Generic[T]):
    """Paginated API response."""
    
    def __init__(
        self,
        items: List[T],
        total: int,
        page: int = 1,
        page_size: int = 10,
        message: Optional[str] = None,
        **kwargs
    ) -> None:
        """Initialize paginated response.
        
        Args:
            items: List of items
            total: Total number of items
            page: Current page number
            page_size: Number of items per page
            message: Optional message
            **kwargs: Additional fields to include in the response
        """
        pagination = {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 1,
        }
        
        super().__init__(
            data={"items": items, "pagination": pagination},
            status_code=HTTP_200_OK,
            message=message or "Data retrieved successfully",
            **kwargs
        )


def create_response(
    data: Any = None,
    status_code: int = HTTP_200_OK,
    message: Optional[str] = None,
    **kwargs
) -> ApiResponse:
    """Create a standard API response.
    
    Args:
        data: Response data
        status_code: HTTP status code
        message: Optional message
        **kwargs: Additional fields to include in the response
        
    Returns:
        ApiResponse: Standardized API response
    """
    return ApiResponse(
        data=data,
        status_code=status_code,
        message=message,
        **kwargs
    )


def create_success_response(
    data: Any = None,
    message: Optional[str] = None,
    **kwargs
) -> SuccessResponse:
    """Create a success response.
    
    Args:
        data: Response data
        message: Optional message
        **kwargs: Additional fields to include in the response
        
    Returns:
        SuccessResponse: Success response with 200 status code
    """
    return SuccessResponse(
        data=data,
        message=message,
        **kwargs
    )


def create_created_response(
    data: Any = None,
    message: Optional[str] = None,
    location: Optional[str] = None,
    **kwargs
) -> CreatedResponse:
    """Create a resource created response.
    
    Args:
        data: Response data
        message: Optional message
        location: Optional location header value
        **kwargs: Additional fields to include in the response
        
    Returns:
        CreatedResponse: Created response with 201 status code
    """
    return CreatedResponse(
        data=data,
        message=message,
        location=location,
        **kwargs
    )


def create_no_content_response(message: Optional[str] = None) -> NoContentResponse:
    """Create a no content response.
    
    Args:
        message: Optional message
        
    Returns:
        NoContentResponse: No content response with 204 status code
    """
    return NoContentResponse(message=message)


def create_paginated_response(
    items: List[T],
    total: int,
    page: int = 1,
    page_size: int = 10,
    message: Optional[str] = None,
    **kwargs
) -> PaginatedApiResponse[T]:
    """Create a paginated response.
    
    Args:
        items: List of items
        total: Total number of items
        page: Current page number
        page_size: Number of items per page
        message: Optional message
        **kwargs: Additional fields to include in the response
        
    Returns:
        PaginatedApiResponse: Paginated API response
    """
    return PaginatedApiResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        message=message,
        **kwargs
    )


def create_error_response(
    message: str,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> ErrorResponse:
    """Create an error response.
    
    Args:
        message: Error message
        status_code: HTTP status code
        error_code: Optional error code
        details: Optional error details
        
    Returns:
        ErrorResponse: Error response object
    """
    return ErrorResponse(
        success=False,
        error=message,
        error_code=error_code,
        details=details or {},
    )


def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions and return a standardized error response.
    
    Args:
        request: Request object
        exc: HTTP exception
        
    Returns:
        JSONResponse: Standardized error response
    """
    detail = exc.detail
    if isinstance(detail, dict):
        message = detail.get("message", str(detail))
        error_code = detail.get("error_code")
        details = detail.get("details", {})
    else:
        message = str(detail)
        error_code = None
        details = {}
    
    error_response = create_error_response(
        message=message,
        status_code=exc.status_code,
        error_code=error_code,
        details=details,
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(error_response.dict()),
    )


def validation_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle validation exceptions and return a standardized error response.
    
    Args:
        request: Request object
        exc: Validation exception
        
    Returns:
        JSONResponse: Standardized error response
    """
    from fastapi.exceptions import RequestValidationError
    
    errors = []
    if isinstance(exc, RequestValidationError):
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error["loc"] if loc != "body")
            errors.append(
                {
                    "field": field,
                    "message": error["msg"],
                    "type": error["type"],
                }
            )
    
    error_response = create_error_response(
        message="Validation error",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error_code="validation_error",
        details={"errors": errors},
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder(error_response.dict()),
    )


def create_http_exception(
    status_code: int,
    message: str,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> HTTPException:
    """Create an HTTP exception with a standardized format.
    
    Args:
        status_code: HTTP status code
        message: Error message
        error_code: Optional error code
        details: Optional error details
        
    Returns:
        HTTPException: HTTP exception with standardized format
    """
    detail = {"message": message}
    if error_code:
        detail["error_code"] = error_code
    if details:
        detail["details"] = details
    
    return HTTPException(status_code=status_code, detail=detail)
