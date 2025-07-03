"""Base Pydantic models for the API."""
from datetime import datetime
from typing import Any, Dict, Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel

# Generic type for the ID field
T = TypeVar('T')


class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    
    model_config = ConfigDict(
        alias_generator=to_camel,
        from_attributes=True,  # Allows ORM model -> Pydantic model conversion
        populate_by_name=True,  # Allows using both aliases and original field names
        use_enum_values=True,  # Converts enums to their values
        json_encoders={
            datetime: lambda v: v.isoformat(),
        },
    )


class IDSchemaMixin(BaseModel):
    """Mixin for schemas with an ID field."""
    id: T = Field(..., description="Unique identifier")


class TimestampMixin(BaseModel):
    """Mixin for timestamps."""
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class BaseResponseSchema(BaseSchema):
    """Base response schema with success flag and message."""
    success: bool = Field(True, description="Indicates if the request was successful")
    message: Optional[str] = Field(None, description="Response message")


class ErrorResponse(BaseSchema):
    """Error response schema."""
    success: bool = Field(False, description="Always false for error responses")
    error: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class PaginatedResponse(BaseSchema, Generic[T]):
    """Paginated response schema."""
    items: list[T] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(1, description="Current page number")
    page_size: int = Field(10, description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")

    @model_validator(mode='after')
    def calculate_total_pages(self) -> 'PaginatedResponse[T]':
        """Calculate total pages based on total items and page size."""
        if self.total_pages is not None:
            return self
            
        if self.page_size <= 0:
            self.total_pages = 1
        else:
            self.total_pages = (self.total + self.page_size - 1) // self.page_size
            
        return self


class QueryParams(BaseSchema):
    """Base query parameters for listing endpoints."""
    q: Optional[str] = Field(None, description="Search query")
    skip: int = Field(0, ge=0, description="Number of items to skip")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of items to return")
    sort_by: Optional[str] = Field(None, description="Field to sort by")
    sort_order: str = Field("asc", regex="^(asc|desc)$", description="Sort order (asc or desc)")


class BulkOperationResponse(BaseSchema):
    """Response for bulk operations."""
    success: bool = Field(..., description="Indicates if the operation was successful")
    processed: int = Field(..., description="Number of items processed")
    created: int = Field(0, description="Number of items created")
    updated: int = Field(0, description="Number of items updated")
    deleted: int = Field(0, description="Number of items deleted")
    skipped: int = Field(0, description="Number of items skipped")
    errors: Optional[list[Dict[str, Any]]] = Field(None, description="List of errors encountered")


class HealthCheck(BaseSchema):
    """Health check response schema."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(..., description="Current server time")
    database: Optional[str] = Field(None, description="Database status")
    redis: Optional[str] = Field(None, description="Redis status")
    environment: str = Field(..., description="Current environment")
    uptime: Optional[float] = Field(None, description="Uptime in seconds")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")
