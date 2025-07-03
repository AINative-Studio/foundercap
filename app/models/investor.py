"""Investor model."""
from datetime import datetime
from typing import List

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.session import Base


class Investor(Base):
    """Investor model representing a venture capital firm, angel investor, or other funding source."""
    __tablename__ = 'investors'

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    type: Mapped[str] = mapped_column(String, nullable=True)  # VC, Angel, Corporate, etc.
    website: Mapped[str] = mapped_column(String, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    country: Mapped[str] = mapped_column(String, nullable=True)
    city: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    investments: Mapped[List['InvestmentParticipant']] = relationship(
        'InvestmentParticipant', back_populates='investor', cascade='all, delete-orphan'
    )

    def __repr__(self) -> str:
        return f"<Investor(id={self.id}, name='{self.name}')>"
