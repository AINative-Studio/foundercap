"""Founder model."""
from datetime import datetime
from typing import List

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.session import Base


class Founder(Base):
    """Founder model representing a company founder or key team member."""
    __tablename__ = 'founders'

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String, nullable=True, unique=True)
    linkedin_url: Mapped[str] = mapped_column(String, nullable=True, unique=True)
    bio: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    companies: Mapped[List['CompanyFounder']] = relationship(
        'CompanyFounder', back_populates='founder', cascade='all, delete-orphan'
    )

    def __repr__(self) -> str:
        return f"<Founder(id={self.id}, name='{self.name}')>"
