"""Investor related schemas."""
from datetime import date
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, HttpUrl, field_validator

from app.schemas.base import IDSchemaMixin, TimestampMixin


class InvestorType(str, Enum):
    """Investor type enumeration."""
    VENTURE_CAPITAL = "VENTURE_CAPITAL"
    ANGEL = "ANGEL"
    PRIVATE_EQUITY = "PRIVATE_EQUITY"
    ACCELERATOR = "ACCELERATOR"
    CORPORATE_VC = "CORPORATE_VC"
    MICRO_VC = "MICRO_VC"
    FAMILY_OFFICE = "FAMILY_OFFICE"
    HEDGE_FUND = "HEDGE_FUND"
    GOVERNMENT = "GOVERNMENT"
    UNIVERSITY = "UNIVERSITY"


class InvestmentStage(str, Enum):
    """Investment stage enumeration."""
    PRE_SEED = "PRE_SEED"
    SEED = "SEED"
    SERIES_A = "SERIES_A"
    SERIES_B = "SERIES_B"
    SERIES_C = "SERIES_C"
    SERIES_D = "SERIES_D"
    SERIES_E = "SERIES_E"
    SERIES_F = "SERIES_F"
    GROWTH = "GROWTH"
    LATE_STAGE = "LATE_STAGE"
    PRIVATE_EQUITY = "PRIVATE_EQUITY"
    ICO = "ICO"
    ACCELERATOR = "ACCELERATOR"
    ANGEL = "ANGEL"
    CONVERTIBLE_NOTE = "CONVERTIBLE_NOTE"
    DEBT_FINANCING = "DEBT_FINANCING"
    EQUITY_CROWDFUNDING = "EQUITY_CROWDFUNDING"
    GRANT = "GRANT"
    INITIAL_COIN_OFFERING = "INITIAL_COIN_OFFERING"
    NON_EQUITY_ASSISTANCE = "NON_EQUITY_ASSISTANCE"
    POST_IPO_DEBT = "POST_IPO_DEBT"
    POST_IPO_EQUITY = "POST_IPO_EQUITY"
    POST_IPO_SECONDARY = "POST_IPO_SECONDARY"
    PRE_SEED = "PRE_SEED"
    SECONDARY_MARKET = "SECONDARY_MARKET"
    SEED = "SEED"
    VENTURE = "VENTURE"


# Shared properties
class InvestorBase(BaseModel):
    """Base investor schema with common fields."""
    name: str = Field(..., max_length=255, description="Investor name")
    investor_type: InvestorType = Field(..., description="Type of investor")
    description: Optional[str] = Field(None, description="Investor description")
    website: Optional[HttpUrl] = Field(None, description="Investor website URL")
    founded_year: Optional[int] = Field(
        None, 
        ge=1800, 
        le=date.today().year,
        description="Year the investor was founded"
    )
    headquarters: Optional[str] = Field(
        None, 
        max_length=255, 
        description="Investor headquarters location"
    )
    contact_email: Optional[EmailStr] = Field(
        None, 
        description="Contact email address"
    )
    linkedin_url: Optional[HttpUrl] = Field(
        None, 
        description="LinkedIn profile URL"
    )
    twitter_handle: Optional[str] = Field(
        None, 
        max_length=50, 
        description="Twitter username (without @)"
    )
    total_investments: Optional[int] = Field(
        None, 
        ge=0, 
        description="Total number of investments made"
    )
    total_funding: Optional[float] = Field(
        None, 
        ge=0, 
        description="Total funding amount in USD"
    )
    investment_stages: Optional[List[InvestmentStage]] = Field(
        None, 
        description="List of investment stages"
    )
    preferred_industries: Optional[List[str]] = Field(
        None, 
        description="List of preferred industries"
    )
    
    @field_validator('twitter_handle')
    @classmethod
    def clean_twitter_handle(cls, v: Optional[str]) -> Optional[str]:
        """Clean and validate Twitter handle."""
        if not v:
            return v
        # Remove @ symbol if present
        return v.lstrip('@')
    
    @field_validator('founded_year')
    @classmethod
    def validate_founded_year(cls, v: Optional[int]) -> Optional[int]:
        """Validate that founded year is not in the future."""
        if v is not None and v > date.today().year:
            raise ValueError("founded_year cannot be in the future")
        return v


# Properties to receive on investor creation
class InvestorCreate(InvestorBase):
    """Schema for creating a new investor."""
    pass


# Properties to receive on investor update
class InvestorUpdate(BaseModel):
    """Schema for updating an existing investor."""
    name: Optional[str] = Field(None, max_length=255, description="Investor name")
    investor_type: Optional[InvestorType] = Field(None, description="Type of investor")
    description: Optional[str] = Field(None, description="Investor description")
    website: Optional[HttpUrl] = Field(None, description="Investor website URL")
    founded_year: Optional[int] = Field(
        None, 
        ge=1800, 
        le=date.today().year,
        description="Year the investor was founded"
    )
    headquarters: Optional[str] = Field(
        None, 
        max_length=255, 
        description="Investor headquarters location"
    )
    contact_email: Optional[EmailStr] = Field(
        None, 
        description="Contact email address"
    )
    linkedin_url: Optional[HttpUrl] = Field(
        None, 
        description="LinkedIn profile URL"
    )
    twitter_handle: Optional[str] = Field(
        None, 
        max_length=50, 
        description="Twitter username (without @)"
    )
    total_investments: Optional[int] = Field(
        None, 
        ge=0, 
        description="Total number of investments made"
    )
    total_funding: Optional[float] = Field(
        None, 
        ge=0, 
        description="Total funding amount in USD"
    )
    investment_stages: Optional[List[InvestmentStage]] = Field(
        None, 
        description="List of investment stages"
    )
    preferred_industries: Optional[List[str]] = Field(
        None, 
        description="List of preferred industries"
    )


# Properties shared by models stored in DB
class InvestorInDBBase(IDSchemaMixin, TimestampMixin, InvestorBase):
    """Base schema for investor data stored in the database."""
    class Config:
        from_attributes = True


# Properties to return to client
class Investor(InvestorInDBBase):
    """Investor schema for API responses."""
    pass


# Properties stored in DB
class InvestorInDB(InvestorInDBBase):
    """Investor schema for database operations."""
    pass


# Additional properties to return via API
class InvestorWithRelations(Investor):
    """Investor schema with related entities."""
    investments: List[dict] = Field(
        default_factory=list, 
        description="List of investments made by this investor"
    )
    portfolio_companies: List[dict] = Field(
        default_factory=list, 
        description="List of portfolio companies"
    )


# Request/Response models for investor operations
class InvestorResponse(BaseModel):
    """Generic investor operation response."""
    success: bool = Field(..., description="Operation status")
    message: str = Field(..., description="Result message")
    investor: Optional[Investor] = Field(None, description="Investor details")


class InvestorsResponse(BaseModel):
    """Response for listing multiple investors."""
    success: bool = Field(..., description="Operation status")
    count: int = Field(..., description="Number of investors")
    investors: List[Investor] = Field(..., description="List of investors")


# Request/Response models for bulk operations
class InvestorBulkCreate(BaseModel):
    """Schema for bulk creating investors."""
    investors: List[InvestorCreate] = Field(..., description="List of investors to create")


class InvestorBulkUpdate(BaseModel):
    """Schema for bulk updating investors."""
    investors: List[dict] = Field(..., description="List of investor updates with IDs")


# Search and filter models
class InvestorFilters(BaseModel):
    """Filters for querying investors."""
    investor_type: Optional[InvestorType] = Field(
        None, 
        description="Filter by investor type"
    )
    min_investments: Optional[int] = Field(
        None, 
        ge=0, 
        description="Minimum number of investments"
    )
    max_investments: Optional[int] = Field(
        None, 
        ge=0, 
        description="Maximum number of investments"
    )
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
    investment_stage: Optional[InvestmentStage] = Field(
        None, 
        description="Filter by investment stage"
    )
    industry: Optional[str] = Field(
        None, 
        description="Filter by preferred industry"
    )
    
    @field_validator('max_investments')
    @classmethod
    def validate_investments_range(
        cls, 
        v: Optional[int], 
        values: dict
    ) -> Optional[int]:
        """Validate that max_investments is greater than min_investments if both are provided."""
        if v is not None and 'min_investments' in values and values['min_investments'] is not None:
            if v < values['min_investments']:
                raise ValueError(
                    "max_investments must be greater than or equal to min_investments"
                )
        return v
    
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
