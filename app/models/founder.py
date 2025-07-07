"""Enhanced Founder model with comprehensive fields and API integration."""
from datetime import date, datetime
from typing import List, Dict, Any, Optional
from enum import Enum as PyEnum
import re

from sqlalchemy import Column, Date, DateTime, String, Text, Boolean, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import JSONB, ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from sqlalchemy.sql import func
from pydantic import BaseModel, EmailStr, HttpUrl, validator

from app.db.session import Base


class FounderRole(str, PyEnum):
    FOUNDER = 'founder'
    CO_FOUNDER = 'co_founder'
    CEO = 'ceo'
    CTO = 'cto'
    EXECUTIVE = 'executive'
    ADVISOR = 'advisor'
    OTHER = 'other'


class Education(BaseModel):
    """Education history for a founder."""
    institution: str
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    description: Optional[str] = None


class WorkExperience(BaseModel):
    """Work experience for a founder."""
    company: str
    title: str
    location: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: bool = False
    description: Optional[str] = None


class Founder(Base):
    """Enhanced Founder model with comprehensive fields for real API integration."""
    __tablename__ = 'founders'
    __table_args__ = (
        {'comment': 'Founders and key team members of companies'},
    )

    # Core identifiers
    id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
        index=True,
        comment='Unique identifier for the founder'
    )
    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment='First name of the founder'
    )
    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment='Last name of the founder'
    )
    
    # Contact information
    email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        index=True,
        comment='Primary email address'
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment='Primary phone number'
    )
    
    # Professional information
    title: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment='Current professional title/role'
    )
    primary_role: Mapped[Optional[str]] = mapped_column(
        ENUM(FounderRole, name='founder_role'),
        nullable=True,
        comment='Primary role in companies (founder, co-founder, etc.)'
    )
    bio: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment='Professional biography or summary'
    )
    skills: Mapped[Optional[List[str]]] = mapped_column(
        JSONB,
        nullable=True,
        comment='List of skills and expertise areas'
    )
    
    # Social profiles
    linkedin_url: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        comment='LinkedIn profile URL'
    )
    twitter_url: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment='Twitter profile URL'
    )
    github_url: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment='GitHub profile URL'
    )
    personal_website: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment='Personal website or blog'
    )
    
    # Background
    education: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSONB,
        nullable=True,
        comment='Education history'
    )
    experience: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSONB,
        nullable=True,
        comment='Work experience history'
    )
    
    # Additional metadata
    external_ids: Mapped[Optional[Dict[str, str]]] = mapped_column(
        JSONB,
        nullable=True,
        comment='External system identifiers (e.g., Crunchbase, LinkedIn IDs)'
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
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment='When the founder data was last synced from external sources'
    )
    
    # Flags
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment='Whether the founder has been verified'
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment='Whether the founder is currently active'
    )

    # Relationships
    companies: Mapped[List['CompanyFounder']] = relationship(
        'CompanyFounder',
        back_populates='founder',
        cascade='all, delete-orphan',
        lazy='selectin',
        passive_deletes=True
    )
    
    # Indexes
    __table_args__ = (
        {'postgresql_using': 'gin', 'postgresql_ops': {'skills': 'gin_trgm_ops'}},
    )
    
    @property
    def name(self) -> str:
        """Get the full name of the founder."""
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def current_companies(self) -> List['CompanyFounder']:
        """Get current company associations."""
        return [cf for cf in self.companies if cf.is_current]
    
    @validates('email')
    def validate_email(self, key, email):
        """Validate email format."""
        if email is not None and not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            raise ValueError('Invalid email format')
        return email
    
    @validates('linkedin_url')
    def validate_linkedin_url(self, key, url):
        """Validate LinkedIn URL format."""
        if url and not url.startswith(('https://www.linkedin.com/', 'http://www.linkedin.com/')):
            raise ValueError('Invalid LinkedIn URL')
        return url
    
    @validates('education')
    def validate_education(self, key, education_list):
        """Validate education data."""
        if education_list is not None:
            return [Education(**ed).dict() for ed in education_list]
        return None
    
    @validates('experience')
    def validate_experience(self, key, experience_list):
        """Validate work experience data."""
        if experience_list is not None:
            return [WorkExperience(**exp).dict() for exp in experience_list]
        return None
    
    def update_from_api(self, data: Dict[str, Any]) -> None:
        """Update founder data from API response."""
        # Basic info
        if 'first_name' in data:
            self.first_name = data['first_name']
        if 'last_name' in data:
            self.last_name = data['last_name']
        
        # Contact info
        self.email = data.get('email', self.email)
        self.phone = data.get('phone', self.phone)
        
        # Professional info
        self.title = data.get('title', self.title)
        if 'primary_role' in data:
            self.primary_role = data['primary_role']
        self.bio = data.get('bio', self.bio)
        
        # Social profiles
        self.linkedin_url = data.get('linkedin_url', self.linkedin_url)
        self.twitter_url = data.get('twitter_url', self.twitter_url)
        self.github_url = data.get('github_url', self.github_url)
        self.personal_website = data.get('personal_website', self.personal_website)
        
        # Background
        if 'education' in data:
            self.education = data['education']
        if 'experience' in data:
            self.experience = data['experience']
        if 'skills' in data:
            self.skills = data['skills']
        
        # Metadata
        if 'external_ids' in data:
            if self.external_ids:
                self.external_ids.update(data['external_ids'])
            else:
                self.external_ids = data['external_ids']
        
        # Update sync timestamp
        self.last_synced_at = datetime.utcnow()
        
        # Update verification status if provided
        if 'is_verified' in data:
            self.is_verified = data['is_verified']
    
    def add_education(
        self,
        institution: str,
        degree: Optional[str] = None,
        field_of_study: Optional[str] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        description: Optional[str] = None
    ) -> None:
        """Add an education entry to the founder's profile."""
        education = Education(
            institution=institution,
            degree=degree,
            field_of_study=field_of_study,
            start_year=start_year,
            end_year=end_year,
            description=description
        )
        
        if self.education is None:
            self.education = []
        
        self.education.append(education.dict())
    
    def add_experience(
        self,
        company: str,
        title: str,
        location: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        is_current: bool = False,
        description: Optional[str] = None
    ) -> None:
        """Add a work experience entry to the founder's profile."""
        experience = WorkExperience(
            company=company,
            title=title,
            location=location,
            start_date=start_date,
            end_date=end_date,
            is_current=is_current,
            description=description
        )
        
        if self.experience is None:
            self.experience = []
        
        self.experience.append(experience.dict())
    
    def to_dict(self, include_companies: bool = False) -> Dict[str, Any]:
        """Convert founder to dictionary representation."""
        result = {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'title': self.title,
            'primary_role': self.primary_role,
            'bio': self.bio,
            'skills': self.skills,
            'linkedin_url': self.linkedin_url,
            'twitter_url': self.twitter_url,
            'github_url': self.github_url,
            'personal_website': self.personal_website,
            'education': self.education,
            'experience': self.experience,
            'external_ids': self.external_ids,
            'is_verified': self.is_verified,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_synced_at': self.last_synced_at.isoformat() if self.last_synced_at else None,
        }
        
        if include_companies:
            result['companies'] = [{
                'company_id': cf.company_id,
                'company_name': cf.company.name if cf.company else None,
                'title': cf.title,
                'is_current': cf.is_current,
                'start_date': cf.start_date.isoformat() if cf.start_date else None,
                'end_date': cf.end_date.isoformat() if cf.end_date else None,
                'ownership_percentage': float(cf.ownership_percentage) if cf.ownership_percentage is not None else None,
                'is_board_member': cf.is_board_member
            } for cf in self.companies]
        
        return result

    def __repr__(self) -> str:
        return f"<Founder(id={self.id}, name='{self.name}', email='{self.email}')>"
