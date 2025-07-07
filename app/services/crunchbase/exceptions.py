"""Exceptions for the Crunchbase API client."""

class CrunchbaseAPIError(Exception):
    """Base exception for Crunchbase API errors."""
    pass

class CrunchbaseRateLimitError(CrunchbaseAPIError):
    """Raised when rate limit is exceeded."""
    pass

class CrunchbaseAuthError(CrunchbaseAPIError):
    """Raised when authentication fails."""
    pass

class CrunchbaseNotFoundError(CrunchbaseAPIError):
    """Raised when a resource is not found."""
    pass

class CrunchbaseValidationError(CrunchbaseAPIError):
    """Raised when input validation fails."""
    pass
