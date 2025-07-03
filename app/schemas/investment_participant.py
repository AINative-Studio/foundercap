"""Investment participant related schemas."""
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.schemas.base import IDSchemaMixin, TimestampMixin


class ParticipantRole(str, Enum):
    """Investment participant role enumeration."""
    LEAD = "LEAD"
    CO_INVESTOR = "CO_INVESTOR"
    SYNDICATE_LEAD = "SYNDICATE_LEAD"
    SYNDICATE_MEMBER = "SYNDICATE_MEMBER"
    ANGEL = "ANGEL"
    VENTURE_CAPITAL = "VENTURE_CAPITAL"
    PRIVATE_EQUITY = "PRIVATE_EQUITY"
    CORPORATE_VENTURE = "CORPORATE_VENTURE"
    ACCELERATOR = "ACCELERATOR"
    INCUBATOR = "INCUBATOR"
    FAMILY_OFFICE = "FAMILY_OFFICE"
    HEDGE_FUND = "HEDGE_FUND"
    OTHER = "OTHER"


# Shared properties
class InvestmentParticipantBase(BaseModel):
    """Base investment participant schema with common fields."""
    funding_round_id: int = Field(..., description="ID of the funding round")
    investor_id: int = Field(..., description="ID of the investor")
    role: ParticipantRole = Field(..., description="Role of the participant in this round")
    amount_invested: Decimal = Field(
        None, 
        gt=0, 
        max_digits=20, 
        decimal_places=2,
        description="Amount invested in USD (if known)"
    )
    is_lead: bool = Field(
        False, 
        description="Whether this participant is the lead investor"
    )
    is_lead_checked: bool = Field(
        False, 
        description="Whether the lead status has been verified"
    )
    ownership_percentage: Optional[Decimal] = Field(
        None, 
        ge=0, 
        le=100, 
        max_digits=5, 
        decimal_places=2,
        description="Ownership percentage (if known)"
    )
    shares_issued: Optional[int] = Field(
        None, 
        ge=0, 
        description="Number of shares issued (if known)"
    )
    price_per_share: Optional[Decimal] = Field(
        None, 
        gt=0, 
        max_digits=20, 
        decimal_places=10,
        description="Price per share (if known)"
    )
    participation_date: Optional[date] = Field(
        None, 
        description="Date when the investment was made"
    )
    notes: Optional[str] = Field(
        None, 
        description="Additional notes about this participation"
    )
    
    @field_validator('participation_date')
    @classmethod
    def validate_participation_date(cls, v: Optional[date]) -> Optional[date]:
        """Validate that participation date is not in the future."""
        if v is not None and v > date.today():
            raise ValueError("participation_date cannot be in the future")
        return v


# Properties to receive on investment participant creation
class InvestmentParticipantCreate(InvestmentParticipantBase):
    """Schema for creating a new investment participant."""
    pass


# Properties to receive on investment participant update
class InvestmentParticipantUpdate(BaseModel):
    """Schema for updating an existing investment participant."""
    role: Optional[ParticipantRole] = Field(
        None, 
        description="Role of the participant in this round"
    )
    amount_invested: Optional[Decimal] = Field(
        None, 
        gt=0, 
        max_digits=20, 
        decimal_places=2,
        description="Amount invested in USD (if known)"
    )
    is_lead: Optional[bool] = Field(
        None, 
        description="Whether this participant is the lead investor"
    )
    is_lead_checked: Optional[bool] = Field(
        None, 
        description="Whether the lead status has been verified"
    )
    ownership_percentage: Optional[Decimal] = Field(
        None, 
        ge=0, 
        le=100, 
        max_digits=5, 
        decimal_places=2,
        description="Ownership percentage (if known)"
    )
    shares_issued: Optional[int] = Field(
        None, 
        ge=0, 
        description="Number of shares issued (if known)"
    )
    price_per_share: Optional[Decimal] = Field(
        None, 
        gt=0, 
        max_digits=20, 
        decimal_places=10,
        description="Price per share (if known)"
    )
    participation_date: Optional[date] = Field(
        None, 
        description="Date when the investment was made"
    )
    notes: Optional[str] = Field(
        None, 
        description="Additional notes about this participation"
    )


# Properties shared by models stored in DB
class InvestmentParticipantInDBBase(IDSchemaMixin, TimestampMixin, InvestmentParticipantBase):
    """Base schema for investment participant data stored in the database."""
    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: float(v) if v is not None else None
        }


# Properties to return to client
class InvestmentParticipant(InvestmentParticipantInDBBase):
    """Investment participant schema for API responses."""
    pass


# Properties stored in DB
class InvestmentParticipantInDB(InvestmentParticipantInDBBase):
    """Investment participant schema for database operations."""
    pass


# Additional properties to return via API
class InvestmentParticipantWithRelations(InvestmentParticipant):
    """Investment participant schema with related entities."""
    investor: Optional[dict] = Field(None, description="Investor details")
    funding_round: Optional[dict] = Field(
        None, 
        description="Funding round details"
    )


# Request/Response models for investment participant operations
class InvestmentParticipantResponse(BaseModel):
    """Generic investment participant operation response."""
    success: bool = Field(..., description="Operation status")
    message: str = Field(..., description="Result message")
    participant: Optional[InvestmentParticipant] = Field(
        None, 
        description="Investment participant details"
    )


class InvestmentParticipantsResponse(BaseModel):
    """Response for listing multiple investment participants."""
    success: bool = Field(..., description="Operation status")
    count: int = Field(..., description="Number of participants")
    participants: List[InvestmentParticipant] = Field(
        ..., 
        description="List of investment participants"
    )


# Request/Response models for bulk operations
class InvestmentParticipantBulkCreate(BaseModel):
    """Schema for bulk creating investment participants."""
    participants: List[InvestmentParticipantCreate] = Field(
        ..., 
        description="List of participants to create"
    )


class InvestmentParticipantBulkUpdate(BaseModel):
    """Schema for bulk updating investment participants."""
    participants: List[dict] = Field(
        ..., 
        description="List of participant updates with IDs"
    )


# Search and filter models
class InvestmentParticipantFilters(BaseModel):
    """Filters for querying investment participants."""
    funding_round_id: Optional[int] = Field(
        None, 
        description="Filter by funding round ID"
    )
    investor_id: Optional[int] = Field(
        None, 
        description="Filter by investor ID"
    )
    role: Optional[ParticipantRole] = Field(
        None, 
        description="Filter by participant role"
    )
    is_lead: Optional[bool] = Field(
        None, 
        description="Filter by lead investor status"
    )
    min_amount: Optional[Decimal] = Field(
        None, 
        gt=0, 
        description="Minimum amount invested"
    )
    max_amount: Optional[Decimal] = Field(
        None, 
        gt=0, 
        description="Maximum amount invested"
    )
    min_ownership: Optional[Decimal] = Field(
        None, 
        ge=0, 
        le=100, 
        description="Minimum ownership percentage"
    )
    max_ownership: Optional[Decimal] = Field(
        None, 
        ge=0, 
        le=100, 
        description="Maximum ownership percentage"
    )
    
    @field_validator('max_amount')
    @classmethod
    def validate_amount_range(
        cls, 
        v: Optional[Decimal], 
        values: dict
    ) -> Optional[Decimal]:
        """Validate that max_amount is greater than min_amount if both are provided."""
        if v is not None and 'min_amount' in values and values['min_amount'] is not None:
            if v < values['min_amount']:
                raise ValueError(
                    "max_amount must be greater than or equal to min_amount"
                )
        return v
    
    @field_validator('max_ownership')
    @classmethod
    def validate_ownership_range(
        cls, 
        v: Optional[Decimal], 
        values: dict
    ) -> Optional[Decimal]:
        """Validate that max_ownership is greater than min_ownership if both are provided."""
        if v is not None and 'min_ownership' in values and values['min_ownership'] is not None:
            if v < values['min_ownership']:
                raise ValueError(
                    "max_ownership must be greater than or equal to min_ownership"
                )
        return v
