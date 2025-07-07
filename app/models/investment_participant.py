"""Investment Participant model for tracking investors in funding rounds."""
from datetime import date, datetime
from decimal import Decimal
from enum import Enum as PyEnum
from typing import Optional, Dict, Any, List

from sqlalchemy import Column, DateTime, ForeignKey, Numeric, String, Boolean, Text, JSON
from sqlalchemy.dialects.postgresql import JSONB, ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from sqlalchemy.sql import func
from pydantic import BaseModel, validator, Field

from app.db.session import Base


class InvestorType(str, PyEnum):
    """Types of investors that can participate in funding rounds."""
    ANGEL = 'angel'
    VENTURE_CAPITAL = 'venture_capital'
    PRIVATE_EQUITY = 'private_equity'
    CORPORATE_VC = 'corporate_vc'
    ACCELERATOR = 'accelerator'
    INCUBATOR = 'incubator'
    GOVERNMENT = 'government'
    FAMILY_OFFICE = 'family_office'
    HEDGE_FUND = 'hedge_fund'
    MICRO_VC = 'micro_vc'
    CROWDFUNDING = 'crowdfunding'
    INDIVIDUAL = 'individual'
    OTHER = 'other'


class InvestmentType(str, PyEnum):
    """Types of investments that can be made."""
    PRIMARY = 'primary'
    SECONDARY = 'secondary'
    FOLLOW_ON = 'follow_on'
    BRIDGE = 'bridge'
    CONVERTIBLE_NOTE = 'convertible_note'
    SAFE = 'safe'
    KISS = 'kiss'
    LOAN = 'loan'
    WARRANT = 'warrant'
    OPTION = 'option'
    OTHER = 'other'


class InvestmentParticipant(Base):
    """
    Enhanced InvestmentParticipant model for tracking investor participation in funding rounds.
    
    This model represents the many-to-many relationship between investors and funding rounds,
    with additional attributes specific to each investment.
    """
    __tablename__ = 'investment_participants'
    __table_args__ = (
        {'comment': 'Investor participation in funding rounds'},
    )
    
    # Composite primary key
    round_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey('funding_rounds.id', ondelete='CASCADE'),
        primary_key=True,
        index=True,
        comment='Reference to the funding round'
    )
    investor_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey('investors.id', ondelete='CASCADE'),
        primary_key=True,
        index=True,
        comment='Reference to the investor'
    )
    
    # Investment details
    investment_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment='Type of investment (e.g., primary, secondary, follow-on)'
    )
    amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment='Amount invested by this participant'
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        default='USD',
        nullable=False,
        comment='Currency of the investment (ISO 4217)'
    )
    shares_issued: Mapped[Optional[int]] = mapped_column(
        nullable=True,
        comment='Number of shares issued to this investor'
    )
    share_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 10),
        nullable=True,
        comment='Price per share for this investment'
    )
    ownership_percentage: Mapped[Optional[float]] = mapped_column(
        Numeric(7, 5),
        nullable=True,
        comment='Percentage ownership acquired (0-100)'
    )
    
    # Investment status and role
    is_lead: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment='Whether this investor is the lead investor'
    )
    is_board_seat: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment='Whether this investor received a board seat'
    )
    is_board_observer: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment='Whether this investor has board observer rights'
    )
    is_pro_rata: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment='Whether this investor has pro-rata rights'
    )
    
    # Additional metadata
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment='Additional notes about this investment'
    )
    external_ids: Mapped[Optional[Dict[str, str]]] = mapped_column(
        JSONB,
        nullable=True,
        comment='External system identifiers (e.g., Crunchbase, PitchBook IDs)'
    )
    metadata_: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        'metadata',
        JSONB,
        nullable=True,
        comment='Additional metadata and attributes'
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment='Record creation timestamp'
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment='Record last update timestamp'
    )
    last_verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment='When this investment was last verified from a trusted source'
    )

    # Relationships
    funding_round: Mapped['FundingRound'] = relationship(
        'FundingRound',
        back_populates='participants',
        lazy='joined'
    )
    investor: Mapped['Investor'] = relationship(
        'Investor',
        back_populates='investments',
        lazy='joined',
        passive_deletes=True
    )
    
    # Indexes
    __table_args__ = (
        {'postgresql_using': 'btree', 'postgresql_ops': {'amount': 'DESC NULLS LAST'}},
        {'postgresql_using': 'btree', 'postgresql_ops': {'is_lead': 'DESC'}},
    )
    
    @property
    def investment_value(self) -> Optional[Decimal]:
        """Calculate the investment value based on shares and price."""
        if self.amount is not None:
            return self.amount
        if self.shares_issued is not None and self.share_price is not None:
            return Decimal(self.shares_issued) * self.share_price
        return None
    
    @validates('ownership_percentage')
    def validate_ownership_percentage(self, key, value):
        """Validate ownership percentage is between 0 and 100."""
        if value is not None and (value < 0 or value > 100):
            raise ValueError('Ownership percentage must be between 0 and 100')
        return value
    
    @validates('currency')
    def validate_currency(self, key, currency):
        """Validate currency code format."""
        if currency and len(currency) != 3:
            raise ValueError('Currency code must be 3 characters')
        return currency.upper() if currency else 'USD'
    
    def update_from_api(self, data: Dict[str, Any]) -> None:
        """Update participant data from API response."""
        # Investment details
        if 'investment_type' in data:
            self.investment_type = data['investment_type']
        if 'amount' in data:
            self.amount = Decimal(str(data['amount'])) if data['amount'] is not None else None
        if 'currency' in data:
            self.currency = data['currency']
        if 'shares_issued' in data:
            self.shares_issued = int(data['shares_issued']) if data['shares_issued'] is not None else None
        if 'share_price' in data:
            self.share_price = Decimal(str(data['share_price'])) if data['share_price'] is not None else None
        if 'ownership_percentage' in data:
            self.ownership_percentage = float(data['ownership_percentage']) if data['ownership_percentage'] is not None else None
        
        # Status and role
        if 'is_lead' in data:
            self.is_lead = data['is_lead']
        if 'is_board_seat' in data:
            self.is_board_seat = data['is_board_seat']
        if 'is_board_observer' in data:
            self.is_board_observer = data['is_board_observer']
        if 'is_pro_rata' in data:
            self.is_pro_rata = data['is_pro_rata']
        
        # Additional metadata
        self.notes = data.get('notes', self.notes)
        
        if 'external_ids' in data:
            if self.external_ids:
                self.external_ids.update(data['external_ids'])
            else:
                self.external_ids = data['external_ids']
        
        # Update verification timestamp
        self.last_verified_at = datetime.utcnow()
    
    def to_dict(self, include_related: bool = True) -> Dict[str, Any]:
        """Convert investment participant to dictionary representation."""
        result = {
            'round_id': self.round_id,
            'investor_id': self.investor_id,
            'investment_type': self.investment_type,
            'amount': float(self.amount) if self.amount is not None else None,
            'currency': self.currency,
            'shares_issued': self.shares_issued,
            'share_price': float(self.share_price) if self.share_price is not None else None,
            'ownership_percentage': float(self.ownership_percentage) if self.ownership_percentage is not None else None,
            'investment_value': float(self.investment_value) if self.investment_value is not None else None,
            'is_lead': self.is_lead,
            'is_board_seat': self.is_board_seat,
            'is_board_observer': self.is_board_observer,
            'is_pro_rata': self.is_pro_rata,
            'notes': self.notes,
            'external_ids': self.external_ids,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_verified_at': self.last_verified_at.isoformat() if self.last_verified_at else None,
        }
        
        if include_related:
            if self.investor:
                result['investor'] = {
                    'id': self.investor.id,
                    'name': self.investor.name,
                    'type': self.investor.investor_type.value if self.investor.investor_type else None,
                    'website': self.investor.website,
                    'linkedin_url': self.investor.linkedin_url,
                }
            if self.funding_round:
                result['funding_round'] = {
                    'id': self.funding_round.id,
                    'name': self.funding_round.name,
                    'round_type': self.funding_round.round_type.value if self.funding_round.round_type else None,
                    'announced_date': self.funding_round.announced_date.isoformat() if self.funding_round.announced_date else None,
                    'company_id': self.funding_round.company_id,
                }
        
        return result

    def __repr__(self) -> str:
        return (
            f"<InvestmentParticipant(round_id={self.round_id}, "
            f"investor_id={self.investor_id}, "
            f"amount={self.amount} {self.currency}, "
            f"shares={self.shares_issued}@{self.share_price})"
        )
