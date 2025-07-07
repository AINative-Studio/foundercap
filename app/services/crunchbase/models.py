"""Pydantic models for Crunchbase API responses."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, HttpUrl, Field, validator
from datetime import date

class Investor(BaseModel):
    """Model representing an investor in a funding round."""
    name: str
    uuid: str
    permalink: Optional[str] = None
    type: Optional[str] = None  # e.g., "financial_investor", "angel", "incubator"
    location: Optional[str] = None
    website: Optional[HttpUrl] = None
    description: Optional[str] = None
    short_description: Optional[str] = None
    created_at: Optional[date] = None
    updated_at: Optional[date] = None
    
    class Config:
        extra = "ignore"  # Ignore extra fields from API

class FundingRound(BaseModel):
    """Model representing a funding round from Crunchbase."""
    uuid: str
    name: str
    announced_on: Optional[date] = None
    investment_type: Optional[str] = None  # e.g., "seed", "series_a", "series_b"
    money_raised: Optional[float] = None
    money_raised_currency: str = "USD"
    investor_count: Optional[int] = None
    investors: List[Investor] = []
    source_url: Optional[HttpUrl] = None
    source_description: Optional[str] = None
    created_at: Optional[date] = None
    updated_at: Optional[date] = None
    
    class Config:
        extra = "ignore"  # Ignore extra fields from API
    
    @validator('announced_on', 'created_at', 'updated_at', pre=True)
    def parse_date(cls, v):
        if isinstance(v, str):
            try:
                return date.fromisoformat(v.split('T')[0])
            except (ValueError, AttributeError):
                return None
        return v

class Company(BaseModel):
    """Model representing a company from Crunchbase."""
    uuid: str
    name: str
    permalink: Optional[str] = None
    description: Optional[str] = None
    short_description: Optional[str] = None
    homepage_url: Optional[HttpUrl] = None
    founded_on: Optional[date] = None
    total_funding_usd: Optional[float] = None
    last_funding_type: Optional[str] = None
    last_funding_at: Optional[date] = None
    funding_rounds: List[FundingRound] = []
    created_at: Optional[date] = None
    updated_at: Optional[date] = None
    
    class Config:
        extra = "ignore"  # Ignore extra fields from API
    
    @validator('founded_on', 'last_funding_at', 'created_at', 'updated_at', pre=True)
    def parse_dates(cls, v):
        if isinstance(v, str):
            try:
                return date.fromisoformat(v.split('T')[0])
            except (ValueError, AttributeError):
                return None
        return v

class CrunchbaseResponse(BaseModel):
    """Base response model for Crunchbase API."""
    data: Dict[str, Any]
    error: Optional[Dict[str, Any]] = None
