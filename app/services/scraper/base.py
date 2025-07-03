"""Base scraper interface."""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from app.core.service import Service


class BaseScraper(Service, ABC):
    """Base class for all scrapers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of the scraper."""
        raise NotImplementedError

    @abstractmethod
    async def scrape(self, company_name: str, **kwargs: Any) -> Dict[str, Any]:
        """Scrape data for a company.

        Args:
            company_name: The name of the company to scrape data for.
            **kwargs: Additional arguments specific to the scraper implementation.

        Returns:
            A dictionary containing the scraped data.
        """
        raise NotImplementedError

    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the scraper.

        Returns:
            A dictionary containing health check information.
        """
        return {
            **await super().health_check(),
            "name": self.name,
            "status": "healthy" if self._is_initialized else "not_initialized",
        }
