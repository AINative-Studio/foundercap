"""Base updater interface."""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from app.core.service import Service


class BaseUpdater(Service, ABC):
    """Base class for all data updaters."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of the updater."""
        raise NotImplementedError

    @abstractmethod
    async def update(
        self, company_id: str, data: Dict[str, Any], **kwargs: Any
    ) -> Dict[str, Any]:
        """Update data for a company.

        Args:
            company_id: The ID of the company to update.
            data: The data to update.
            **kwargs: Additional arguments specific to the updater implementation.

        Returns:
            A dictionary containing the update result.
        """
        raise NotImplementedError

    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the updater.

        Returns:
            A dictionary containing health check information.
        """
        return {
            **await super().health_check(),
            "name": self.name,
            "status": "healthy" if self._is_initialized else "not_initialized",
        }
