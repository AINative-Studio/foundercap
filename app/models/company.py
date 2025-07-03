"""Company and related models."""
from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import Column, Date, DateTime, Enum, ForeignKey, Numeric, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.session import Base


class Company(Base):
    """Company model representing a startup or company."""
    __tablename__ = 'companies'

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    founded_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(
        Enum('ACTIVE', 'ACQUIRED', 'CLOSED', 'IPO', name='company_status'),
        nullable=True,
        index=True
    )
    total_funding: Mapped[Optional[float]] = mapped_column(
        Numeric(15, 2), nullable=True
    )
    last_funding_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    employee_count: Mapped[Optional[int]] = mapped_column(nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    founders: Mapped[List['CompanyFounder']] = relationship(
        'CompanyFounder', back_populates='company', cascade='all, delete-orphan'
    )
    funding_rounds: Mapped[List['FundingRound']] = relationship(
        'FundingRound', back_populates='company', cascade='all, delete-orphan'
    )

    def __repr__(self) -> str:
        return f"<Company(id={self.id}, name='{self.name}')>"


class CompanyFounder(Base):
    """Association table between Company and Founder with additional attributes."""
    __tablename__ = 'company_founders'

    company_id: Mapped[str] = mapped_column(
        String, ForeignKey('companies.id', ondelete='CASCADE'), primary_key=True
    )
    founder_id: Mapped[str] = mapped_column(
        String, ForeignKey('founders.id', ondelete='CASCADE'), primary_key=True
    )
    title: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_current: Mapped[Optional[bool]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    company: Mapped['Company'] = relationship('Company', back_populates='founders')
    founder: Mapped['Founder'] = relationship('Founder', back_populates='companies')

    def __repr__(self) -> str:
        return f"<CompanyFounder(company_id={self.company_id}, founder_id={self.founder_id})>"
