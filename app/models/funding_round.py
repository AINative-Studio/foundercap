"""Funding round and investment participant models."""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    Column, Date, DateTime, Enum, ForeignKey, Numeric, String, Text
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.session import Base


class FundingRound(Base):
    """Funding round model representing a single investment round for a company."""
    __tablename__ = 'funding_rounds'

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    company_id: Mapped[str] = mapped_column(
        String, ForeignKey('companies.id', ondelete='CASCADE'), index=True
    )
    round_type: Mapped[Optional[str]] = mapped_column(
        Enum(
            'PRE_SEED', 'SEED', 'SERIES_A', 'SERIES_B', 'SERIES_C', 'SERIES_D', 
            'SERIES_E', 'SERIES_F', 'SERIES_G', 'SERIES_H', 'SERIES_I', 'SERIES_J',
            'GRANT', 'ANGEL', 'PRIVATE_EQUITY', 'DEBT_FINANCING', 'POST_IPO_DEBT',
            'POST_IPO_EQUITY', 'NON_EQUITY_ASSISTANCE', 'SECONDARY_MARKET',
            'CONVERTIBLE_NOTE', 'CORPORATE_ROUND', 'UNDISCLOSED',
            name='funding_round_type'
        ),
        nullable=True,
        index=True
    )
    announced_date: Mapped[Optional[date]] = mapped_column(Date, index=True, nullable=True)
    raised_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2), nullable=True
    )
    news_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    company: Mapped['Company'] = relationship('Company', back_populates='funding_rounds')
    participants: Mapped[List['InvestmentParticipant']] = relationship(
        'InvestmentParticipant', back_populates='funding_round', cascade='all, delete-orphan'
    )

    def __repr__(self) -> str:
        return f"<FundingRound(id={self.id}, company_id={self.company_id}, type={self.round_type})>"


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
