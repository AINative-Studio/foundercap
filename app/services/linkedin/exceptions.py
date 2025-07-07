"""LinkedIn scraping exceptions."""


class LinkedInScrapingError(Exception):
    """Base exception for LinkedIn scraping errors."""
    pass


class LinkedInRateLimitError(LinkedInScrapingError):
    """Exception raised when LinkedIn rate limits are hit."""
    pass


class LinkedInAuthError(LinkedInScrapingError):
    """Exception raised when LinkedIn authentication fails."""
    pass


class LinkedInNotFoundError(LinkedInScrapingError):
    """Exception raised when a LinkedIn resource is not found."""
    pass


class LinkedInPrivateProfileError(LinkedInScrapingError):
    """Exception raised when trying to access a private LinkedIn profile."""
    pass


class LinkedInBlockedError(LinkedInScrapingError):
    """Exception raised when LinkedIn blocks the scraper."""
    pass


class LinkedInTimeoutError(LinkedInScrapingError):
    """Exception raised when LinkedIn requests timeout."""
    pass


class LinkedInCaptchaError(LinkedInScrapingError):
    """Exception raised when LinkedIn presents a CAPTCHA."""
    pass