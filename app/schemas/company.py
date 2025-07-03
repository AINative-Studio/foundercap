"""Company related schemas."""
from datetime import date, datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator

from app.schemas.base import IDSchemaMixin, TimestampMixin


class CompanyStatus(str, Enum):
    """Company status enumeration."""
    ACTIVE = "ACTIVE"
    ACQUIRED = "ACQUIRED"
    CLOSED = "CLOSED"
    IPO = "IPO"


# Shared properties
class CompanyBase(BaseModel):
    """Base company schema with common fields."""
    name: str = Field(..., max_length=255, description="Company name")
    description: Optional[str] = Field(None, description="Company description")
    website: Optional[HttpUrl] = Field(None, description="Company website URL")
    founded_date: Optional[date] = Field(None, description="Date when the company was founded")
    status: Optional[CompanyStatus] = Field(None, description="Company status")
    total_funding: Optional[float] = Field(
        None, 
        ge=0, 
        description="Total funding raised in USD"
    )
    last_funding_date: Optional[date] = Field(
        None, 
        description="Date of the last funding round"
    )
    employee_count: Optional[int] = Field(
        None, 
        ge=0, 
        description="Number of employees"
    )
    country: Optional[str] = Field(
        None, 
        max_length=100, 
        description="Headquarters country"
    )
    city: Optional[str] = Field(
        None, 
        max_length=100, 
        description="Headquarters city"
    )
    
    @field_validator('name')
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        """Ensure name is not empty."""
        if not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()


# Properties to receive on company creation
class CompanyCreate(CompanyBase):
    """Schema for creating a new company."""
    pass


# Properties to receive on company update
class CompanyUpdate(BaseModel):
    """Schema for updating an existing company."""
    name: Optional[str] = Field(None, max_length=255, description="Company name")
    description: Optional[str] = Field(None, description="Company description")
    website: Optional[HttpUrl] = Field(None, description="Company website URL")
    founded_date: Optional[date] = Field(None, description="Date when the company was founded")
    status: Optional[CompanyStatus] = Field(None, description="Company status")
    total_funding: Optional[float] = Field(
        None, 
        ge=0, 
        description="Total funding raised in USD"
    )
    last_funding_date: Optional[date] = Field(
        None, 
        description="Date of the last funding round"
    )
    employee_count: Optional[int] = Field(
        None, 
        ge=0, 
        description="Number of employees"
    )
    country: Optional[str] = Field(
        None, 
        max_length=100, 
        description="Headquarters country"
    )
    city: Optional[str] = Field(
        None, 
        max_length=100, 
        description="Headquarters city"
    )


# Properties shared by models stored in DB
class CompanyInDBBase(IDSchemaMixin, TimestampMixin, CompanyBase):
    """Base schema for company data stored in the database."""
    class Config:
        from_attributes = True


# Properties to return to client
class Company(CompanyInDBBase):
    """Company schema for API responses."""
    pass


# Properties stored in DB
class CompanyInDB(CompanyInDBBase):
    """Company schema for database operations."""
    pass


# Additional properties to return via API
class CompanyWithRelations(Company):
    """Company schema with related entities."""
    founders: List[dict] = Field(
        default_factory=list, 
        description="List of company founders"
    )
    funding_rounds: List[dict] = Field(
        default_factory=list, 
        description="List of funding rounds"
    )


# Request/Response models for company operations
class CompanyResponse(BaseModel):
    """Generic company operation response."""
    success: bool = Field(..., description="Operation status")
    message: str = Field(..., description="Result message")
    company: Optional[Company] = Field(None, description="Company details")


class CompaniesResponse(BaseModel):
    """Response for listing multiple companies."""
    success: bool = Field(..., description="Operation status")
    count: int = Field(..., description="Number of companies")
    companies: List[Company] = Field(..., description="List of companies")


# Request/Response models for bulk operations
class CompanyBulkCreate(BaseModel):
    """Schema for bulk creating companies."""
    companies: List[CompanyCreate] = Field(..., description="List of companies to create")


class CompanyBulkUpdate(BaseModel):
    """Schema for bulk updating companies."""
    companies: List[dict] = Field(..., description="List of company updates with IDs")


# Search and filter models
class CompanyFilters(BaseModel):
    """Filters for querying companies."""
    status: Optional[CompanyStatus] = Field(None, description="Filter by company status")
    min_funding: Optional[float] = Field(
        None, 
        ge=0, 
        description="Minimum total funding"
    )
    max_funding: Optional[float] = Field(
        None, 
        ge=0, 
        description="Maximum total funding"
    )
    min_employees: Optional[int] = Field(
        None, 
        ge=0, 
        description="Minimum number of employees"
    )
    max_employees: Optional[int] = Field(
        None, 
        ge=0, 
        description="Maximum number of employees"
    )
    country: Optional[str] = Field(
        None, 
        description="Filter by country"
    )
    city: Optional[str] = Field(
        None, 
        description="Filter by city"
    )
    founded_after: Optional[date] = Field(
        None, 
        description="Filter companies founded after this date"
    )
    founded_before: Optional[date] = Field(
        None, 
        description="Filter companies founded before this date"
    )
    has_funding: Optional[bool] = Field(
        None, 
        description="Filter companies that have received funding"
    )
    
    @field_validator('max_funding')
    @classmethod
    def validate_funding_range(
        cls, 
        v: Optional[float], 
        values: dict
    ) -> Optional[float]:
        """Validate that max_funding is greater than min_funding if both are provided."""
        if v is not None and 'min_funding' in values and values['min_funding'] is not None:
            if v < values['min_funding']:
                raise ValueError(
                    "max_funding must be greater than or equal to min_funding"
                )
        return v
    
    @field_validator('max_employees')
    @classmethod
    def validate_employees_range(
        cls, 
        v: Optional[int], 
        values: dict
    ) -> Optional[int]:
        """Validate that max_employees is greater than min_employees if both are provided."""
        if v is not None and 'min_employees' in values and values['min_employees'] is not None:
            if v < values['min_employees']:
                raise ValueError(
                    "max_employees must be greater than or equal to min_employees"
                )
        return v
    
    @field_validator('founded_before')
    @classmethod
    def validate_founded_dates(
        cls, 
        v: Optional[date], 
        values: dict
    ) -> Optional[date]:
        """Validate that founded_before is after founded_after if both are provided."""
        if v is not None and 'founded_after' in values and values['founded_after'] is not None:
            if v < values['founded_after']:
                raise ValueError(
                    "founded_before must be after founded_after"
                )
        return v
