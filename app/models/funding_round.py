"""Funding round and investment participant models with comprehensive fields and validation."""
from datetime import date, datetime
from decimal import Decimal
from enum import Enum as PyEnum
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from pydantic import BaseModel, Field, validator
from sqlalchemy import (
    Boolean, Column, Date, DateTime, Enum as SQLEnum, ForeignKey, Index,
    JSON, Numeric, String, Text
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from sqlalchemy.sql import func

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.investor import Investor


class RoundType(str, PyEnum):
    """Types of funding rounds, from pre-seed to IPO."""
    PRE_SEED = "pre_seed"
    SEED = "seed"
    SEED_EXTENSION = "seed_extension"
    SERIES_A = "series_a"
    SERIES_B = "series_b"
    SERIES_C = "series_c"
    SERIES_D = "series_d"
    SERIES_E = "series_e"
    SERIES_F = "series_f"
    SERIES_G = "series_g"
    SERIES_H = "series_h"
    SERIES_I = "series_i"
    SERIES_J = "series_j"
    ANGEL = "angel"
    CONVERTIBLE_NOTE = "convertible_note"
    SAFE = "safe"
    EQUITY_CROWDFUNDING = "equity_crowdfunding"
    DEBT_FINANCING = "debt_financing"
    GRANT = "grant"
    POST_IPO_DEBT = "post_ipo_debt"
    POST_IPO_EQUITY = "post_ipo_equity"
    PRIVATE_EQUITY = "private_equity"
    SECONDARY_MARKET = "secondary_market"
    VENTURE_SERIES_UNKNOWN = "venture_series_unknown"
    CORPORATE_ROUND = "corporate_round"
    NON_EQUITY_ASSISTANCE = "non_equity_assistance"
    UNDISCLOSED = "undisclosed"
    OTHER = "other"


class InvestmentStage(str, PyEnum):
    """Stages of company development for investment purposes."""
    IDEA_AND_CONCEPT = "idea_and_concept"
    PROTOTYPE = "prototype"
    PRE_SEED = "pre_seed"
    SEED = "seed"
    SERIES_A = "series_a"
    SERIES_B = "series_b"
    SERIES_C_PLUS = "series_c_plus"
    GROWTH = "growth"
    EXPANSION = "expansion"
    MEZZANINE = "mezzanine"
    IPO = "ipo"
    ACQUISITION = "acquisition"
    MERGER = "merger"
    BRIDGE = "bridge"
    DEBT_RESTRUCTURING = "debt_restructuring"
    TURNAROUND = "turnaround"
    RECAPITALIZATION = "recapitalization"
    OTHER = "other"


class InvestmentTerms(BaseModel):
    """Pydantic model for validating investment terms JSONB field."""
    valuation: Optional[Decimal] = Field(None, description="Pre-money valuation in the specified currency")
    valuation_cap: Optional[Decimal] = Field(None, description="Valuation cap for convertible notes/SAFEs")
    discount_rate: Optional[Decimal] = Field(None, description="Discount rate (0-1) for convertible notes/SAFEs")
    interest_rate: Optional[Decimal] = Field(None, description="Interest rate for debt financing (0-1)")
    maturity_date: Optional[date] = Field(None, description="Maturity date for debt instruments")
    liquidation_preference: Optional[str] = Field(None, description="Liquidation preference terms")
    participation_rights: Optional[bool] = Field(None, description="Whether investors have participation rights")
    anti_dilution: Optional[str] = Field(None, description="Type of anti-dilution protection")
    board_seats: Optional[int] = Field(None, description="Number of board seats granted to investors")
    pro_rata_rights: Optional[bool] = Field(None, description="Whether investors have pro-rata rights")
    information_rights: Optional[bool] = Field(None, description="Whether investors have information rights")
    drag_along: Optional[bool] = Field(None, description="Whether drag-along rights apply")
    tag_along: Optional[bool] = Field(None, description="Whether tag-along rights apply")
    first_refusal: Optional[bool] = Field(None, description="Whether right of first refusal applies")
    pay_to_play: Optional[bool] = Field(None, description="Whether pay-to-play provisions apply")
    conversion_terms: Optional[Dict[str, Any]] = Field(None, description="Specific conversion terms")
    other_terms: Optional[Dict[str, Any]] = Field(None, description="Any other terms not covered above")

    class Config:
        json_encoders = {
            Decimal: lambda v: str(v),
            date: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "valuation": 10000000.00,
                "valuation_cap": 15000000.00,
                "discount_rate": 0.20,
                "liquidation_preference": "1x non-participating",
                "board_seats": 1,
                "pro_rata_rights": True
            }
        }


class FundingRound(Base):
    """Model representing a funding round for a company."""
    __tablename__ = 'funding_rounds'
    __table_args__ = (
        Index('idx_funding_rounds_company_id', 'company_id'),
        Index('idx_funding_rounds_announced_date', 'announced_date'),
        Index('idx_funding_rounds_round_type', 'round_type'),
    )
    
    # Primary key and company relationship
    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    company_id: Mapped[str] = mapped_column(
        String, 
        ForeignKey('companies.id', ondelete='CASCADE'), 
        nullable=False,
        index=True,
        comment="Reference to the company that raised this funding round"
    )
    
    # Round identification and type
    name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Official name of the funding round (e.g., 'Series A', 'Seed Round')"
    )
    round_type: Mapped[RoundType] = mapped_column(
        SQLEnum(RoundType, name="round_type_enum"),
        nullable=False,
        index=True,
        comment="Type of funding round from the RoundType enum"
    )
    investment_stage: Mapped[Optional[InvestmentStage]] = mapped_column(
        SQLEnum(InvestmentStage, name="investment_stage_enum"),
        nullable=True,
        index=True,
        comment="Company's development stage at time of investment"
    )
    
    # Flags for round characteristics
    is_equity: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether this is an equity-based funding round"
    )
    is_debt: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether this is a debt-based funding round"
    )
    is_convertible: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether this involves convertible instruments"
    )
    is_crowdfunding: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether this is a crowdfunding round"
    )
    is_confidential: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether the round details are confidential"
    )
    is_cancelled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether the round was cancelled"
    )
    
    # Financial details
    target_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Target amount the company aims to raise in this round"
    )
    raised_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Actual amount raised in this round"
    )
    minimum_investment: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Minimum investment amount for this round"
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
        comment="ISO 4217 currency code (e.g., USD, EUR)"
    )
    pre_money_valuation: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Pre-money valuation in the specified currency"
    )
    post_money_valuation: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Post-money valuation in the specified currency"
    )
    price_per_share: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 10),
        nullable=True,
        comment="Price per share in this round"
    )
    shares_issued: Mapped[Optional[int]] = mapped_column(
        nullable=True,
        comment="Number of shares issued in this round"
    )
    
    # Date fields
    announced_date: Mapped[Optional[date]] = mapped_column(
        Date,
        index=True,
        nullable=True,
        comment="Date the funding round was publicly announced"
    )
    closed_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Date the funding round was officially closed"
    )
    expected_close_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Expected closing date at the time of announcement"
    )
    first_investment_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Date of the first investment in this round"
    )
    last_funding_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Date of the most recent investment in this round"
    )
    
    # Relationships
    participants: Mapped[List["InvestmentParticipant"]] = relationship(
        "InvestmentParticipant",
        back_populates="funding_round",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    # Metadata and external references
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Detailed description of the funding round"
    )
    investment_terms: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Structured terms of the investment (validated by InvestmentTerms Pydantic model)"
    )
    source_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="URL of the source where this funding round was announced"
    )
    source_description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Description of the source (e.g., 'SEC Filing', 'Press Release')"
    )
    external_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        unique=True,
        comment="External ID from data providers (e.g., Crunchbase, PitchBook)"
    )
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Additional unstructured metadata"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Properties
    @property
    def total_raised(self) -> Optional[Decimal]:
        """Calculate total amount raised from all participants if not explicitly set."""
        if self.raised_amount is not None:
            return self.raised_amount
        if self.participants:
            return sum(p.amount for p in self.participants if p.amount is not None)
        return None

    @property
    def lead_investors(self) -> List["InvestmentParticipant"]:
        """Get list of lead investors in this round."""
        return [p for p in self.participants if p.is_lead_investor]

    @property
    def participant_count(self) -> int:
        """Get total number of participants in this round."""
        return len(self.participants)

    @property
    def is_closed(self) -> bool:
        """Check if the funding round is closed."""
        return self.closed_date is not None

    @property
    def duration_days(self) -> Optional[int]:
        """Calculate duration of the funding round in days."""
        if self.announced_date and self.closed_date:
            return (self.closed_date - self.announced_date).days
        return None

    # Validation methods
    @validates('currency')
    def validate_currency(self, key: str, currency: str) -> str:
        """Validate currency code is 3 uppercase letters."""
        if not isinstance(currency, str) or len(currency) != 3 or not currency.isalpha():
            raise ValueError("Currency must be a 3-letter ISO 4217 code")
        return currency.upper()

    @validates('investment_terms')
    def validate_investment_terms(self, key: str, terms: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Validate investment terms against Pydantic model."""
        if terms is None:
            return None
        try:
            return InvestmentTerms(**terms).dict(exclude_unset=True)
        except Exception as e:
            raise ValueError(f"Invalid investment terms: {e}")

    # API integration methods
    def update_from_api(self, data: Dict[str, Any], update_relationships: bool = True) -> None:
        """
        Update funding round from API data.
        
        Args:
            data: Dictionary containing funding round data
            update_relationships: Whether to update related objects (e.g., participants)
        """
        # Update simple fields
        for field in [
            'name', 'round_type', 'investment_stage', 'is_equity', 'is_debt',
            'is_convertible', 'is_crowdfunding', 'is_confidential', 'is_cancelled', 
            'target_amount', 'raised_amount', 'minimum_investment', 'currency', 
            'pre_money_valuation', 'post_money_valuation', 'price_per_share', 
            'shares_issued', 'description', 'source_url', 'source_description', 
            'external_id', 'metadata'
        ]:
            if field in data:
                setattr(self, field, data[field])

        # Update date fields
        for date_field in [
            'announced_date', 'closed_date', 'expected_close_date',
            'first_investment_date', 'last_funding_date'
        ]:
            if date_field in data and data[date_field] is not None:
                if isinstance(data[date_field], str):
                    setattr(self, date_field, date.fromisoformat(data[date_field]))
                else:
                    setattr(self, date_field, data[date_field])

        # Update investment terms
        if 'investment_terms' in data:
            self.investment_terms = data['investment_terms']

        # Update participants if requested
        if update_relationships and 'participants' in data:
            self._update_participants(data['participants'])

    def _update_participants(self, participants_data: List[Dict[str, Any]]) -> None:
        """Update participants from API data."""
        # Create lookup of existing participants by investor_id
        existing_participants = {p.investor_id: p for p in self.participants}
        updated_ids = set()
        
        for participant_data in participants_data:
            investor_id = participant_data.get('investor_id')
            if not investor_id:
                continue
                
            if investor_id in existing_participants:
                # Update existing participant
                participant = existing_participants[investor_id]
                participant.update_from_api(participant_data)
            else:
                # Create new participant
                participant = InvestmentParticipant(
                    funding_round_id=self.id,
                    **{k: v for k, v in participant_data.items() if k != 'id'}
                )
                self.participants.append(participant)
            
            updated_ids.add(investor_id)
        
        # Remove participants not in the updated data
        for participant in list(self.participants):
            if participant.investor_id not in updated_ids:
                self.participants.remove(participant)

    def to_dict(self, include_relationships: bool = True) -> Dict[str, Any]:
        """Convert funding round to dictionary representation."""
        result = {
            'id': self.id,
            'company_id': self.company_id,
            'name': self.name,
            'round_type': self.round_type.value if self.round_type else None,
            'investment_stage': self.investment_stage.value if self.investment_stage else None,
            'is_equity': self.is_equity,
            'is_debt': self.is_debt,
            'is_convertible': self.is_convertible,
            'is_crowdfunding': self.is_crowdfunding,
            'is_confidential': self.is_confidential,
            'is_cancelled': self.is_cancelled,
            'target_amount': float(self.target_amount) if self.target_amount is not None else None,
            'raised_amount': float(self.raised_amount) if self.raised_amount is not None else None,
            'minimum_investment': float(self.minimum_investment) if self.minimum_investment is not None else None,
            'currency': self.currency,
            'pre_money_valuation': float(self.pre_money_valuation) if self.pre_money_valuation is not None else None,
            'post_money_valuation': float(self.post_money_valuation) if self.post_money_valuation is not None else None,
            'price_per_share': float(self.price_per_share) if self.price_per_share is not None else None,
            'shares_issued': self.shares_issued,
            'announced_date': self.announced_date.isoformat() if self.announced_date else None,
            'closed_date': self.closed_date.isoformat() if self.closed_date else None,
            'expected_close_date': self.expected_close_date.isoformat() if self.expected_close_date else None,
            'first_investment_date': self.first_investment_date.isoformat() if self.first_investment_date else None,
            'last_funding_date': self.last_funding_date.isoformat() if self.last_funding_date else None,
            'description': self.description,
            'investment_terms': self.investment_terms,
            'source_url': self.source_url,
            'source_description': self.source_description,
            'external_id': self.external_id,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'total_raised': float(self.total_raised) if self.total_raised is not None else None,
            'participant_count': self.participant_count,
            'is_closed': self.is_closed,
            'duration_days': self.duration_days
        }
        
        if include_relationships and self.participants:
            result['participants'] = [p.to_dict() for p in self.participants]
            
        return result

    def __repr__(self) -> str:
        return (
            f"<FundingRound(id={self.id}, company_id={self.company_id}, "
            f"round_type={self.round_type}, raised_amount={self.raised_amount} {self.currency})>"
        )


class InvestmentParticipant(Base):
    """Association table between FundingRound and Investor with participation details."""
    __tablename__ = 'investment_participants'

    round_id: Mapped[str] = mapped_column(
        String, ForeignKey('funding_rounds.id', ondelete='CASCADE'), primary_key=True
    )
    investor_id: Mapped[str] = mapped_column(
        String, ForeignKey('investors.id', ondelete='CASCADE'), primary_key=True
    )
    amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    is_lead: Mapped[Optional[bool]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    funding_round: Mapped['FundingRound'] = relationship(
        'FundingRound', back_populates='participants'
    )
    investor: Mapped['Investor'] = relationship(
        'Investor', back_populates='investments'
    )

    def __repr__(self) -> str:
        return (
            f"<InvestmentParticipant(round_id={self.round_id}, "
            f"investor_id={self.investor_id})>"
        )
