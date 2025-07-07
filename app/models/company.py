"""Company and related models with enhanced fields for real API integration."""
from datetime import date, datetime
from typing import List, Optional, Dict, Any
from enum import Enum as PyEnum
import json

from sqlalchemy import Column, Date, DateTime, Enum as SQLEnum, ForeignKey, Numeric, String, Text, JSON, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from sqlalchemy.sql import func
from pydantic import BaseModel, Field, HttpUrl

from app.db.session import Base


class CompanyStatus(str, PyEnum):
    ACTIVE = 'ACTIVE'
    ACQUIRED = 'ACQUIRED'
    CLOSED = 'CLOSED'
    IPO = 'IPO'
    UNKNOWN = 'UNKNOWN'


class CompanyIndustry(BaseModel):
    """Industry classification for companies."""
    name: str
    code: Optional[str] = None
    category: Optional[str] = None


class CompanyMetrics(BaseModel):
    """Key metrics for a company."""
    alexa_rank: Optional[int] = None
    employees: Optional[int] = None
    employees_range: Optional[str] = None
    estimated_revenue: Optional[float] = None
    funding_total: Optional[float] = None
    last_funding_at: Optional[date] = None
    market_cap: Optional[float] = None
    valuation: Optional[float] = None


class Company(Base):
    """Enhanced Company model with comprehensive fields for real API integration."""
    __tablename__ = 'companies'

    # Core identifiers
    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    legal_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    short_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Contact information
    website: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    blog_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    twitter_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    linkedin_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    facebook_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    crunchbase_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Company details
    founded_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    status: Mapped[Optional[str]] = mapped_column(
        SQLEnum(CompanyStatus, name='company_status'),
        nullable=True,
        index=True
    )
    
    # Financial information
    total_funding: Mapped[Optional[float]] = mapped_column(Numeric(20, 2), nullable=True)
    last_funding_amount: Mapped[Optional[float]] = mapped_column(Numeric(20, 2), nullable=True)
    last_funding_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    last_funding_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Location
    country: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    region: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Employee information
    employee_count: Mapped[Optional[int]] = mapped_column(nullable=True, index=True)
    employee_range: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Additional metadata
    industries: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    tags: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    metrics: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    external_ids: Mapped[Optional[Dict[str, str]]] = mapped_column(JSONB, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Flags
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_actively_tracking: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    # Relationships
    founders: Mapped[List['CompanyFounder']] = relationship(
        'CompanyFounder', back_populates='company', cascade='all, delete-orphan', lazy='selectin'
    )
    funding_rounds: Mapped[List['FundingRound']] = relationship(
        'FundingRound', back_populates='company', cascade='all, delete-orphan', lazy='selectin'
    )
    investors: Mapped[List['InvestmentParticipant']] = relationship(
        'InvestmentParticipant', back_populates='company', cascade='all, delete-orphan', lazy='selectin'
    )
    
    # Indexes
    __table_args__ = (
        {'postgresql_using': 'gin', 'postgresql_ops': {'tags': 'gin_trgm_ops'}},
    )
    
    @validates('metrics')
    def validate_metrics(self, key, value):
        if value is not None:
            return CompanyMetrics(**value).dict()
        return None
    
    @validates('industries')
    def validate_industries(self, key, value):
        if value is not None:
            if isinstance(value, list):
                return [CompanyIndustry(**item).dict() for item in value]
            return value
        return None
    
    def update_from_api(self, data: Dict[str, Any]) -> None:
        """Update company data from API response."""
        from .founder import Founder
        from .funding_round import FundingRound, InvestmentParticipant
        
        # Basic info
        self.name = data.get('name', self.name)
        self.legal_name = data.get('legal_name', self.legal_name)
        self.description = data.get('description', self.description)
        self.short_description = data.get('short_description', self.short_description)
        
        # Contact info
        self.website = data.get('website', self.website)
        self.blog_url = data.get('blog_url', self.blog_url)
        self.twitter_url = data.get('twitter_url', self.twitter_url)
        self.linkedin_url = data.get('linkedin_url', self.linkedin_url)
        self.facebook_url = data.get('facebook_url', self.facebook_url)
        self.crunchbase_url = data.get('crunchbase_url', self.crunchbase_url)
        
        # Company details
        if 'founded_date' in data:
            self.founded_date = data['founded_date']
        self.status = data.get('status', self.status)
        
        # Financial info
        if 'total_funding' in data:
            self.total_funding = float(data['total_funding']) if data['total_funding'] is not None else None
        if 'last_funding_amount' in data:
            self.last_funding_amount = float(data['last_funding_amount']) if data['last_funding_amount'] is not None else None
        if 'last_funding_date' in data:
            self.last_funding_date = data['last_funding_date']
        self.last_funding_type = data.get('last_funding_type', self.last_funding_type)
        
        # Location
        self.country = data.get('country', self.country)
        self.region = data.get('region', self.region)
        self.city = data.get('city', self.city)
        self.address = data.get('address', self.address)
        self.postal_code = data.get('postal_code', self.postal_code)
        
        # Employee info
        if 'employee_count' in data:
            self.employee_count = int(data['employee_count']) if data['employee_count'] is not None else None
        self.employee_range = data.get('employee_range', self.employee_range)
        
        # Additional metadata
        if 'industries' in data:
            self.industries = data['industries']
        if 'tags' in data:
            self.tags = data['tags']
        if 'metrics' in data:
            self.metrics = data['metrics']
        if 'external_ids' in data:
            self.external_ids = data['external_ids']
        
        # Update sync timestamp
        self.last_synced_at = datetime.utcnow()
        
        # Process founders
        if 'founders' in data:
            self._process_founders(data['founders'])
        
        # Process funding rounds
        if 'funding_rounds' in data:
            self._process_funding_rounds(data['funding_rounds'])
    
    def _process_founders(self, founders_data: List[Dict[str, Any]]) -> None:
        """Process and update founders from API data."""
        from .founder import Founder
        
        existing_founders = {f.founder_id: f for f in self.founders}
        
        for founder_data in founders_data:
            founder_id = founder_data.get('id')
            if not founder_id:
                continue
                
            if founder_id in existing_founders:
                # Update existing founder
                founder = existing_founders[founder_id].founder
                founder.update_from_api(founder_data)
            else:
                # Create new founder
                founder = Founder(id=founder_id)
                founder.update_from_api(founder_data)
                
                # Add to company
                company_founder = CompanyFounder(
                    company_id=self.id,
                    founder_id=founder_id,
                    title=founder_data.get('title'),
                    is_current=founder_data.get('is_current', True)
                )
                company_founder.founder = founder
                self.founders.append(company_founder)
    
    def _process_funding_rounds(self, rounds_data: List[Dict[str, Any]]) -> None:
        """Process and update funding rounds from API data."""
        from .funding_round import FundingRound, InvestmentParticipant
        
        existing_rounds = {r.id: r for r in self.funding_rounds}
        
        for round_data in rounds_data:
            round_id = round_data.get('id')
            if not round_id:
                continue
                
            if round_id in existing_rounds:
                # Update existing round
                funding_round = existing_rounds[round_id]
                funding_round.update_from_api(round_data)
            else:
                # Create new funding round
                funding_round = FundingRound(
                    id=round_id,
                    company_id=self.id,
                    name=round_data.get('name'),
                    round_type=round_data.get('round_type'),
                    amount=float(round_data['amount']) if round_data.get('amount') is not None else None,
                    currency=round_data.get('currency', 'USD'),
                    pre_valuation=float(round_data['pre_valuation']) if round_data.get('pre_valuation') is not None else None,
                    post_valuation=float(round_data['post_valuation']) if round_data.get('post_valuation') is not None else None,
                    announced_date=round_data.get('announced_date'),
                    closed_date=round_data.get('closed_date'),
                    is_equity=round_data.get('is_equity', True),
                    source=round_data.get('source')
                )
                self.funding_rounds.append(funding_round)
            
            # Process investors for this round
            if 'investors' in round_data:
                funding_round._process_investors(round_data['investors'])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert company to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'legal_name': self.legal_name,
            'description': self.description,
            'short_description': self.short_description,
            'website': self.website,
            'founded_date': self.founded_date.isoformat() if self.founded_date else None,
            'status': self.status,
            'total_funding': float(self.total_funding) if self.total_funding is not None else None,
            'last_funding_amount': float(self.last_funding_amount) if self.last_funding_amount is not None else None,
            'last_funding_date': self.last_funding_date.isoformat() if self.last_funding_date else None,
            'last_funding_type': self.last_funding_type,
            'employee_count': self.employee_count,
            'employee_range': self.employee_range,
            'country': self.country,
            'region': self.region,
            'city': self.city,
            'address': self.address,
            'postal_code': self.postal_code,
            'industries': self.industries,
            'tags': self.tags,
            'metrics': self.metrics,
            'external_ids': self.external_ids,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_synced_at': self.last_synced_at.isoformat() if self.last_synced_at else None,
            'is_verified': self.is_verified,
            'is_actively_tracking': self.is_actively_tracking,
            'founders': [{
                'id': f.founder_id,
                'name': f.founder.name,
                'title': f.title,
                'is_current': f.is_current
            } for f in self.founders],
            'funding_rounds': [{
                'id': r.id,
                'name': r.name,
                'round_type': r.round_type,
                'amount': float(r.amount) if r.amount is not None else None,
                'currency': r.currency,
                'announced_date': r.announced_date.isoformat() if r.announced_date else None,
                'investors': [{
                    'investor_id': i.investor_id,
                    'name': i.investor.name if i.investor else None,
                    'amount': float(i.amount) if i.amount is not None else None,
                    'is_lead': i.is_lead
                } for i in r.investors]
            } for r in self.funding_rounds]
        }

    def __repr__(self) -> str:
        return f"<Company(id={self.id}, name='{self.name}', status={self.status})>"


class CompanyFounder(Base):
    """Enhanced association table between Company and Founder with additional attributes."""
    __tablename__ = 'company_founders'
    __table_args__ = (
        {'comment': 'Association table between companies and their founders with role information'},
    )

    # Composite primary key
    company_id: Mapped[str] = mapped_column(
        String(50), 
        ForeignKey('companies.id', ondelete='CASCADE'), 
        primary_key=True,
        comment='Reference to the company'
    )
    founder_id: Mapped[str] = mapped_column(
        String(50), 
        ForeignKey('founders.id', ondelete='CASCADE'), 
        primary_key=True,
        comment='Reference to the founder'
    )
    
    # Role information
    title: Mapped[Optional[str]] = mapped_column(
        String(100), 
        nullable=True,
        comment='Founder\'s title/role at the company (e.g., CEO, CTO)'
    )
    is_current: Mapped[Optional[bool]] = mapped_column(
        nullable=True,
        default=True,
        comment='Whether the founder is currently with the company'
    )
    start_date: Mapped[Optional[date]] = mapped_column(
        Date, 
        nullable=True,
        comment='Date when the founder joined the company'
    )
    end_date: Mapped[Optional[date]] = mapped_column(
        Date, 
        nullable=True,
        comment='Date when the founder left the company (if applicable)'
    )
    
    # Additional metadata
    ownership_percentage: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2), 
        nullable=True,
        comment='Founder\'s ownership percentage in the company'
    )
    is_board_member: Mapped[Optional[bool]] = mapped_column(
        nullable=True,
        default=False,
        comment='Whether the founder is a board member'
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
    last_verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment='When this relationship was last verified from a trusted source'
    )

    # Relationships
    company: Mapped['Company'] = relationship(
        'Company', 
        back_populates='founders',
        lazy='joined'
    )
    founder: Mapped['Founder'] = relationship(
        'Founder', 
        back_populates='companies',
        lazy='joined'
    )
    
    def update_from_api(self, data: Dict[str, Any]) -> None:
        """Update founder relationship from API data."""
        self.title = data.get('title', self.title)
        self.is_current = data.get('is_current', self.is_current)
        
        if 'start_date' in data:
            self.start_date = data['start_date']
        if 'end_date' in data:
            self.end_date = data['end_date']
            
        if 'ownership_percentage' in data:
            self.ownership_percentage = float(data['ownership_percentage']) if data['ownership_percentage'] is not None else None
            
        if 'is_board_member' in data:
            self.is_board_member = data['is_board_member']
            
        self.last_verified_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'company_id': self.company_id,
            'founder_id': self.founder_id,
            'title': self.title,
            'is_current': self.is_current,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'ownership_percentage': float(self.ownership_percentage) if self.ownership_percentage is not None else None,
            'is_board_member': self.is_board_member,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_verified_at': self.last_verified_at.isoformat() if self.last_verified_at else None,
            'founder': self.founder.to_dict() if self.founder else None
        }

    def __repr__(self) -> str:
        return (f"<CompanyFounder(company_id={self.company_id}, "
                f"founder_id={self.founder_id}, "
                f"title='{self.title}', "
                f"is_current={self.is_current})>")
