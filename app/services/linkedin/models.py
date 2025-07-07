"""
Data models for LinkedIn company data.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl, validator
from enum import Enum

class CompanySize(str, Enum):
    SELF_EMPLOYED = "SELF_EMPLOYED"
    ONE_TO_10_EMPLOYEES = "1-10_EMPLOYEES"
    ELEVEN_TO_50_EMPLOYEES = "11-50_EMPLOYEES"
    FIFTY_ONE_TO_200_EMPLOYEES = "51-200_EMPLOYEES"
    TWO_HUNDRED_ONE_TO_500_EMPLOYEES = "201-500_EMPLOYEES"
    FIVE_HUNDRED_ONE_TO_1000_EMPLOYEES = "501-1000_EMPLOYEES"
    ONE_THOUSAND_ONE_TO_5000_EMPLOYEES = "1001-5000_EMPLOYEES"
    FIVE_THOUSAND_ONE_PLUS_EMPLOYEES = "5001+_EMPLOYEES"

class CompanyType(str, Enum):
    PUBLIC_COMPANY = "PUBLIC_COMPANY"
    PRIVATELY_HELD = "PRIVATELY_HELD"
    NON_PROFIT = "NON_PROFIT"
    SELF_EMPLOYED = "SELF_EMPLOYED"
    GOVERNMENT_AGENCY = "GOVERNMENT_AGENCY"
    SELF_OWNED = "SELF_OWNED"
    PARTNERSHIP = "PARTNERSHIP"
    EDUCATIONAL = "EDUCATIONAL"

class LinkedInCompany(BaseModel):
    """Represents a company profile from LinkedIn."""
    # Basic Information
    company_id: Optional[str] = Field(
        None, 
        description="Internal company ID (not the LinkedIn ID)"
    )
    linkedin_id: Optional[str] = Field(
        None, 
        description="LinkedIn's internal company ID"
    )
    universal_name: Optional[str] = Field(
        None,
        description="The company's unique LinkedIn URL identifier"
    )
    name: str = Field(..., description="Company name")
    
    # Company Details
    website: Optional[HttpUrl] = Field(None, description="Company website URL")
    description: Optional[str] = Field(None, description="Company description")
    tagline: Optional[str] = Field(None, description="Company tagline or headline")
    
    # Company Size and Type
    company_size: Optional[CompanySize] = Field(
        None, 
        description="Number of employees range"
    )
    company_type: Optional[CompanyType] = Field(
        None, 
        description="Type of company (public, private, etc.)"
    )
    employee_count: Optional[int] = Field(
        None, 
        description="Exact number of employees if available"
    )
    
    # Location
    headquarters: Optional[str] = Field(
        None, 
        description="Company headquarters location"
    )
    locations: List[Dict[str, str]] = Field(
        default_factory=list,
        description="List of company locations"
    )
    
    # Social and Contact
    linkedin_url: Optional[HttpUrl] = Field(
        None, 
        description="Full LinkedIn URL"
    )
    founded_year: Optional[int] = Field(
        None, 
        description="Year the company was founded"
    )
    
    # Timestamps
    last_updated: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this data was last updated"
    )
    
    # Additional Metadata
    raw_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Raw data from LinkedIn API"
    )
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
    
    @validator('founded_year', pre=True)
    def validate_founded_year(cls, v):
        if v is not None and (v < 1800 or v > datetime.now().year + 1):
            raise ValueError("Invalid founded year")
        return v

class LinkedInCompanyUpdate(LinkedInCompany):
    """
    Represents an update to a company's LinkedIn profile.
    Used for diffing and change detection.
    """
    changed_fields: List[str] = Field(
        default_factory=list,
        description="List of fields that have changed"
    )
    
    @classmethod
    def from_company(
        cls, 
        company: 'LinkedInCompany', 
        changed_fields: List[str]
    ) -> 'LinkedInCompanyUpdate':
        """Create an update from a company and list of changed fields."""
        return cls(
            **company.dict(),
            changed_fields=changed_fields
        )
