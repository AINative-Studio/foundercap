"""Funding round related schemas."""
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator

from app.schemas.base import IDSchemaMixin, TimestampMixin


class RoundType(str, Enum):
    """Funding round type enumeration."""
    PRE_SEED = "PRE_SEED"
    SEED = "SEED"
    SERIES_A = "SERIES_A"
    SERIES_B = "SERIES_B"
    SERIES_C = "SERIES_C"
    SERIES_D = "SERIES_D"
    SERIES_E = "SERIES_E"
    SERIES_F = "SERIES_F"
    SERIES_G = "SERIES_G"
    SERIES_H = "SERIES_H"
    SERIES_I = "SERIES_I"
    SERIES_J = "SERIES_J"
    GROWTH = "GROWTH"
    LATE_STAGE = "LATE_STAGE"
    VENTURE = "VENTURE"
    PRIVATE_EQUITY = "PRIVATE_EQUITY"
    DEBT_FINANCING = "DEBT_FINANCING"
    CONVERTIBLE_NOTE = "CONVERTIBLE_NOTE"
    ANGEL = "ANGEL"
    GRANT = "GRANT"
    POST_IPO_DEBT = "POST_IPO_DEBT"
    POST_IPO_EQUITY = "POST_IPO_EQUITY"
    POST_IPO_SECONDARY = "POST_IPO_SECONDARY"
    SECONDARY_MARKET = "SECONDARY_MARKET"
    EQUITY_CROWDFUNDING = "EQUITY_CROWDFUNDING"
    NON_EQUITY_ASSISTANCE = "NON_EQUITY_ASSISTANCE"
    INITIAL_COIN_OFFERING = "INITIAL_COIN_OFFERING"
    UNDISCLOSED = "UNDISCLOSED"
    OTHER = "OTHER"


class InvestmentType(str, Enum):
    """Investment type enumeration."""
    EQUITY = "EQUITY"
    DEBT = "DEBT"
    CONVERTIBLE_NOTE = "CONVERTIBLE_NOTE"
    SAFE = "SAFE"
    KISS = "KISS"
    CONVERTIBLE_EQUITY = "CONVERTIBLE_EQUITY"
    GRANT = "GRANT"
    LOAN = "LOAN"
    OTHER = "OTHER"


# Shared properties
class FundingRoundBase(BaseModel):
    """Base funding round schema with common fields."""
    company_id: int = Field(..., description="ID of the company that raised the round")
    round_type: RoundType = Field(..., description="Type of funding round")
    investment_type: InvestmentType = Field(..., description="Type of investment")
    announced_date: date = Field(..., description="Date the round was announced")
    raised_amount: Decimal = Field(
        ..., 
        gt=0, 
        max_digits=20, 
        decimal_places=2,
        description="Amount raised in USD"
    )    
    valuation: Optional[Decimal] = Field(
        None, 
        gt=0, 
        max_digits=20, 
        decimal_places=2,
        description="Valuation in USD (if available)"
    )
    pre_money_valuation: Optional[Decimal] = Field(
        None, 
        gt=0, 
        max_digits=20, 
        decimal_places=2,
        description="Pre-money valuation in USD (if available)"
    )
    post_money_valuation: Optional[Decimal] = Field(
        None, 
        gt=0, 
        max_digits=20, 
        decimal_places=2,
        description="Post-money valuation in USD (if available)"
    )
    is_equity: bool = Field(
        True, 
        description="Whether this is an equity round"
    )
    is_debt: bool = Field(
        False, 
        description="Whether this is a debt round"
    )
    is_convertible: bool = Field(
        False, 
        description="Whether this is a convertible note/SAFE"
    )
    is_announced: bool = Field(
        True, 
        description="Whether this round has been publicly announced"
    )
    source_url: Optional[HttpUrl] = Field(
        None, 
        description="URL of the announcement or source"
    )
    source_name: Optional[str] = Field(
        None, 
        max_length=255, 
        description="Name of the source"
    )
    notes: Optional[str] = Field(
        None, 
        description="Additional notes about the round"
    )
    
    @model_validator(mode='after')
    def validate_valuations(self) -> 'FundingRoundBase':
        """Validate that post_money_valuation >= pre_money_valuation + raised_amount."""
        if self.pre_money_valuation is not None and self.post_money_valuation is not None:
            if self.post_money_valuation < self.pre_money_valuation + self.raised_amount:
                raise ValueError(
                    "post_money_valuation must be >= pre_money_valuation + raised_amount"
                )
        return self
    
    @field_validator('announced_date')
    @classmethod
    def validate_announced_date(cls, v: date) -> date:
        """Validate that announced date is not in the future."""
        if v > date.today():
            raise ValueError("announced_date cannot be in the future")
        return v


# Properties to receive on funding round creation
class FundingRoundCreate(FundingRoundBase):
    """Schema for creating a new funding round."""
    investor_ids: List[int] = Field(
        default_factory=list,
        description="List of investor IDs participating in this round"
    )


# Properties to receive on funding round update
class FundingRoundUpdate(BaseModel):
    """Schema for updating an existing funding round."""
    round_type: Optional[RoundType] = Field(None, description="Type of funding round")
    investment_type: Optional[InvestmentType] = Field(
        None, 
        description="Type of investment"
    )
    announced_date: Optional[date] = Field(
        None, 
        description="Date the round was announced"
    )
    raised_amount: Optional[Decimal] = Field(
        None, 
        gt=0, 
        max_digits=20, 
        decimal_places=2,
        description="Amount raised in USD"
    )
    valuation: Optional[Decimal] = Field(
        None, 
        gt=0, 
        max_digits=20, 
        decimal_places=2,
        description="Valuation in USD (if available)"
    )
    pre_money_valuation: Optional[Decimal] = Field(
        None, 
        gt=0, 
        max_digits=20, 
        decimal_places=2,
        description="Pre-money valuation in USD (if available)"
    )
    post_money_valuation: Optional[Decimal] = Field(
        None, 
        gt=0, 
        max_digits=20, 
        decimal_places=2,
        description="Post-money valuation in USD (if available)"
    )
    is_equity: Optional[bool] = Field(
        None, 
        description="Whether this is an equity round"
    )
    is_debt: Optional[bool] = Field(
        None, 
        description="Whether this is a debt round"
    )
    is_convertible: Optional[bool] = Field(
        None, 
        description="Whether this is a convertible note/SAFE"
    )
    is_announced: Optional[bool] = Field(
        None, 
        description="Whether this round has been publicly announced"
    )
    source_url: Optional[HttpUrl] = Field(
        None, 
        description="URL of the announcement or source"
    )
    source_name: Optional[str] = Field(
        None, 
        max_length=255, 
        description="Name of the source"
    )
    notes: Optional[str] = Field(
        None, 
        description="Additional notes about the round"
    )
    investor_ids: Optional[List[int]] = Field(
        None,
        description="List of investor IDs participating in this round"
    )


# Properties shared by models stored in DB
class FundingRoundInDBBase(IDSchemaMixin, TimestampMixin, FundingRoundBase):
    """Base schema for funding round data stored in the database."""
    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: float(v) if v is not None else None
        }


# Properties to return to client
class FundingRound(FundingRoundInDBBase):
    """Funding round schema for API responses."""
    pass


# Properties stored in DB
class FundingRoundInDB(FundingRoundInDBBase):
    """Funding round schema for database operations."""
    pass


# Additional properties to return via API
class FundingRoundWithRelations(FundingRound):
    """Funding round schema with related entities."""
    company: Optional[dict] = Field(None, description="Company details")
    investors: List[dict] = Field(
        default_factory=list, 
        description="List of investors in this round"
    )


# Request/Response models for funding round operations
class FundingRoundResponse(BaseModel):
    """Generic funding round operation response."""
    success: bool = Field(..., description="Operation status")
    message: str = Field(..., description="Result message")
    funding_round: Optional[FundingRound] = Field(
        None, 
        description="Funding round details"
    )


class FundingRoundsResponse(BaseModel):
    """Response for listing multiple funding rounds."""
    success: bool = Field(..., description="Operation status")
    count: int = Field(..., description="Number of funding rounds")
    funding_rounds: List[FundingRound] = Field(
        ..., 
        description="List of funding rounds"
    )


# Request/Response models for bulk operations
class FundingRoundBulkCreate(BaseModel):
    """Schema for bulk creating funding rounds."""
    funding_rounds: List[FundingRoundCreate] = Field(
        ..., 
        description="List of funding rounds to create"
    )


class FundingRoundBulkUpdate(BaseModel):
    """Schema for bulk updating funding rounds."""
    funding_rounds: List[dict] = Field(
        ..., 
        description="List of funding round updates with IDs"
    )


# Search and filter models
class FundingRoundFilters(BaseModel):
    """Filters for querying funding rounds."""
    company_id: Optional[int] = Field(
        None, 
        description="Filter by company ID"
    )
    investor_id: Optional[int] = Field(
        None, 
        description="Filter by investor ID"
    )
    round_type: Optional[RoundType] = Field(
        None, 
        description="Filter by round type"
    )
    investment_type: Optional[InvestmentType] = Field(
        None, 
        description="Filter by investment type"
    )
    min_raised: Optional[Decimal] = Field(
        None, 
        gt=0, 
        description="Minimum amount raised"
    )
    max_raised: Optional[Decimal] = Field(
        None, 
        gt=0, 
        description="Maximum amount raised"
    )
    min_valuation: Optional[Decimal] = Field(
        None, 
        gt=0, 
        description="Minimum valuation"
    )
    max_valuation: Optional[Decimal] = Field(
        None, 
        gt=0, 
        description="Maximum valuation"
    )
    start_date: Optional[date] = Field(
        None, 
        description="Filter rounds announced on or after this date"
    )
    end_date: Optional[date] = Field(
        None, 
        description="Filter rounds announced on or before this date"
    )
    is_equity: Optional[bool] = Field(
        None, 
        description="Filter by equity rounds"
    )
    is_debt: Optional[bool] = Field(
        None, 
        description="Filter by debt rounds"
    )
    is_convertible: Optional[bool] = Field(
        None, 
        description="Filter by convertible notes/SAFEs"
    )
    is_announced: Optional[bool] = Field(
        None, 
        description="Filter by announcement status"
    )
    
    @field_validator('max_raised')
    @classmethod
    def validate_raised_range(
        cls, 
        v: Optional[Decimal], 
        values: dict
    ) -> Optional[Decimal]:
        """Validate that max_raised is greater than min_raised if both are provided."""
        if v is not None and 'min_raised' in values and values['min_raised'] is not None:
            if v < values['min_raised']:
                raise ValueError(
                    "max_raised must be greater than or equal to min_raised"
                )
        return v
    
    @field_validator('max_valuation')
    @classmethod
    def validate_valuation_range(
        cls, 
        v: Optional[Decimal], 
        values: dict
    ) -> Optional[Decimal]:
        """Validate that max_valuation is greater than min_valuation if both are provided."""
        if v is not None and 'min_valuation' in values and values['min_valuation'] is not None:
            if v < values['min_valuation']:
                raise ValueError(
                    "max_valuation must be greater than or equal to min_valuation"
                )
        return v
    
    @field_validator('end_date')
    @classmethod
    def validate_date_range(
        cls, 
        v: Optional[date], 
        values: dict
    ) -> Optional[date]:
        """Validate that end_date is after start_date if both are provided."""
        if v is not None and 'start_date' in values and values['start_date'] is not None:
            if v < values['start_date']:
                raise ValueError("end_date must be after start_date")
        return v
