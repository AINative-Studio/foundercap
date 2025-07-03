"""Base service class for application services."""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TypeVar, Type


class Service(ABC):
    """Abstract base class for all services."""

    def __init__(self):
        """Initialize the service."""
        self._is_initialized = False

    async def initialize(self) -> None:
        """Initialize the service.

        This method should be overridden by subclasses to perform any
        necessary initialization.
        """
        if self._is_initialized:
            return
        
        await self._initialize()
        self._is_initialized = True

    @abstractmethod
    async def _initialize(self) -> None:
        """Initialize the service.

        This method should be implemented by subclasses to perform any
        necessary initialization.
        """
        raise NotImplementedError

    async def shutdown(self) -> None:
        """Shut down the service.

        This method should be overridden by subclasses to perform any
        necessary cleanup.
        """
        if not self._is_initialized:
            return
        
        await self._shutdown()
        self._is_initialized = False

    async def _shutdown(self) -> None:
        """Shut down the service.

        This method should be implemented by subclasses to perform any
        necessary cleanup.
        """
        pass

    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the health of the service.

        Returns:
            A dictionary containing health check information.
        """
        return {
            "status": "healthy" if self._is_initialized else "not_initialized",
            "service": self.__class__.__name__,
        }

    def __str__(self) -> str:
        """Return a string representation of the service."""
        return f"{self.__class__.__name__}(initialized={self._is_initialized})"


_service_instances: Dict[Type["Service"], "Service"] = {}
T = TypeVar('T', bound=Service)

def get_service_instance(service_class: Type[T]) -> T:
    """Returns a singleton instance of the specified service class.

    Args:
        service_class: The class of the service to retrieve.

    Returns:
        A singleton instance of the service.
    """
    if service_class not in _service_instances:
        _service_instances[service_class] = service_class()
    return _service_instances[service_class]