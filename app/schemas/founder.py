"""Founder related schemas."""
from datetime import date, datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, HttpUrl, field_validator

from app.schemas.base import IDSchemaMixin, TimestampMixin


class FounderRole(str, Enum):
    """Founder role enumeration."""
    FOUNDER = "FOUNDER"
    CO_FOUNDER = "CO_FOUNDER"
    TECHNICAL_CO_FOUNDER = "TECHNICAL_CO_FOUNDER"
    NON_TECHNICAL_CO_FOUNDER = "NON_TECHNICAL_CO_FOUNDER"
    SOLO_FOUNDER = "SOLO_FOUNDER"


# Shared properties
class FounderBase(BaseModel):
    """Base founder schema with common fields."""
    first_name: str = Field(..., max_length=100, description="Founder's first name")
    last_name: str = Field(..., max_length=100, description="Founder's last name")
    email: Optional[EmailStr] = Field(None, description="Founder's email address")
    linkedin_url: Optional[HttpUrl] = Field(None, description="LinkedIn profile URL")
    twitter_handle: Optional[str] = Field(
        None, 
        max_length=50, 
        description="Twitter username (without @)"
    )
    bio: Optional[str] = Field(None, description="Short biography")
    photo_url: Optional[HttpUrl] = Field(None, description="URL to founder's photo")
    is_current: bool = Field(
        True, 
        description="Whether the founder is currently with the company"
    )
    role: Optional[FounderRole] = Field(
        None, 
        description="Founder's role in the company"
    )
    title: Optional[str] = Field(
        None, 
        max_length=100, 
        description="Founder's title at the company"
    )
    start_date: Optional[date] = Field(
        None, 
        description="Date when the founder joined the company"
    )
    end_date: Optional[date] = Field(
        None, 
        description="Date when the founder left the company (if applicable)"
    )
    
    @field_validator('twitter_handle')
    @classmethod
    def clean_twitter_handle(cls, v: Optional[str]) -> Optional[str]:
        """Clean and validate Twitter handle."""
        if not v:
            return v
        # Remove @ symbol if present
        return v.lstrip('@')
    
    @field_validator('end_date')
    @classmethod
    def validate_dates(
        cls, 
        v: Optional[date], 
        values: dict
    ) -> Optional[date]:
        """Validate that end_date is after start_date if both are provided."""
        if v is not None and 'start_date' in values and values['start_date'] is not None:
            if v < values['start_date']:
                raise ValueError("end_date must be after start_date")
        return v


# Properties to receive on founder creation
class FounderCreate(FounderBase):
    """Schema for creating a new founder."""
    company_id: int = Field(..., description="ID of the company")


# Properties to receive on founder update
class FounderUpdate(BaseModel):
    """Schema for updating an existing founder."""
    first_name: Optional[str] = Field(
        None, 
        max_length=100, 
        description="Founder's first name"
    )
    last_name: Optional[str] = Field(
        None, 
        max_length=100, 
        description="Founder's last name"
    )
    email: Optional[EmailStr] = Field(None, description="Founder's email address")
    linkedin_url: Optional[HttpUrl] = Field(None, description="LinkedIn profile URL")
    twitter_handle: Optional[str] = Field(
        None, 
        max_length=50, 
        description="Twitter username (without @)"
    )
    bio: Optional[str] = Field(None, description="Short biography")
    photo_url: Optional[HttpUrl] = Field(None, description="URL to founder's photo")
    is_current: Optional[bool] = Field(
        None, 
        description="Whether the founder is currently with the company"
    )
    role: Optional[FounderRole] = Field(
        None, 
        description="Founder's role in the company"
    )
    title: Optional[str] = Field(
        None, 
        max_length=100, 
        description="Founder's title at the company"
    )
    start_date: Optional[date] = Field(
        None, 
        description="Date when the founder joined the company"
    )
    end_date: Optional[date] = Field(
        None, 
        description="Date when the founder left the company (if applicable)"
    )
    company_id: Optional[int] = Field(None, description="ID of the company")


# Properties shared by models stored in DB
class FounderInDBBase(IDSchemaMixin, TimestampMixin, FounderBase):
    """Base schema for founder data stored in the database."""
    company_id: int = Field(..., description="ID of the company")
    
    class Config:
        from_attributes = True


# Properties to return to client
class Founder(FounderInDBBase):
    """Founder schema for API responses."""
    pass


# Properties stored in DB
class FounderInDB(FounderInDBBase):
    """Founder schema for database operations."""
    pass


# Additional properties to return via API
class FounderWithRelations(Founder):
    """Founder schema with related entities."""
    company: Optional[dict] = Field(None, description="Company details")
    previous_companies: List[dict] = Field(
        default_factory=list, 
        description="List of previous companies"
    )


# Request/Response models for founder operations
class FounderResponse(BaseModel):
    """Generic founder operation response."""
    success: bool = Field(..., description="Operation status")
    message: str = Field(..., description="Result message")
    founder: Optional[Founder] = Field(None, description="Founder details")


class FoundersResponse(BaseModel):
    """Response for listing multiple founders."""
    success: bool = Field(..., description="Operation status")
    count: int = Field(..., description="Number of founders")
    founders: List[Founder] = Field(..., description="List of founders")


# Request/Response models for bulk operations
class FounderBulkCreate(BaseModel):
    """Schema for bulk creating founders."""
    founders: List[FounderCreate] = Field(..., description="List of founders to create")


class FounderBulkUpdate(BaseModel):
    """Schema for bulk updating founders."""
    founders: List[dict] = Field(..., description="List of founder updates with IDs")


# Search and filter models
class FounderFilters(BaseModel):
    """Filters for querying founders."""
    company_id: Optional[int] = Field(None, description="Filter by company ID")
    is_current: Optional[bool] = Field(
        None, 
        description="Filter by current status"
    )
    role: Optional[FounderRole] = Field(
        None, 
        description="Filter by founder role"
    )
    min_experience: Optional[int] = Field(
        None, 
        ge=0, 
        description="Minimum years of experience"
    )
    has_linkedin: Optional[bool] = Field(
        None, 
        description="Filter by presence of LinkedIn URL"
    )
    has_twitter: Optional[bool] = Field(
        None, 
        description="Filter by presence of Twitter handle"
    )
    
    @field_validator('min_experience')
    @classmethod
    def validate_experience(cls, v: Optional[int]) -> Optional[int]:
        """Validate that experience is non-negative."""
        if v is not None and v < 0:
            raise ValueError("min_experience cannot be negative")
        return v
