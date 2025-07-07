"""Crunchbase API integration for fetching company and funding data."""
from .client import CrunchbaseClient
from .models import Company, FundingRound, Investor, CrunchbaseResponse
from .service import CrunchbaseService
from .exceptions import (
    CrunchbaseAPIError,
    CrunchbaseRateLimitError,
    CrunchbaseAuthError,
    CrunchbaseNotFoundError,
    CrunchbaseValidationError,
)
from .config import CrunchbaseConfig, get_crunchbase_config
from .factory import (
    get_crunchbase_client,
    close_crunchbase_client,
    get_crunchbase_service,
    close_crunchbase_service,
    with_crunchbase_service,
)

__all__ = [
    # Client and Service
    'CrunchbaseClient',
    'CrunchbaseService',
    'CrunchbaseConfig',
    'get_crunchbase_client',
    'close_crunchbase_client',
    'get_crunchbase_service',
    'close_crunchbase_service',
    'with_crunchbase_service',
    
    # Models
    'Company',
    'FundingRound',
    'Investor',
    'CrunchbaseResponse',
    
    # Exceptions
    'CrunchbaseAPIError',
    'CrunchbaseRateLimitError',
    'CrunchbaseAuthError',
    'CrunchbaseNotFoundError',
    'CrunchbaseValidationError',
]
