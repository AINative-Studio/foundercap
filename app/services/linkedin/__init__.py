"""
LinkedIn Service

This module provides functionality to scrape and interact with LinkedIn data.
"""
from .service import LinkedInService, get_linkedin_service
from .scraper import LinkedInScraper

__all__ = [
    'LinkedInService',
    'LinkedInScraper',
    'get_linkedin_service'
]
