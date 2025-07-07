"""Factory for creating Crunchbase API clients and services."""
from typing import Optional, TypeVar, Type, Any
from .client import CrunchbaseClient
from .config import CrunchbaseConfig
from .service import CrunchbaseService

# Type variable for generic factory functions
T = TypeVar('T')

# Global instances
_client: Optional[CrunchbaseClient] = None
_service: Optional[CrunchbaseService] = None

def get_crunchbase_client(config: Optional[CrunchbaseConfig] = None) -> CrunchbaseClient:
    """Get or create a Crunchbase API client.
    
    Args:
        config: Optional configuration. If not provided, will use default config.
        
    Returns:
        CrunchbaseClient: Configured client instance
    """
    global _client
    
    if _client is None:
        _client = CrunchbaseClient(config=config)
        
    return _client

async def close_crunchbase_client() -> None:
    """Close the global Crunchbase client if it exists."""
    global _client
    
    if _client is not None:
        await _client.close()
        _client = None

def get_crunchbase_service(
    config: Optional[CrunchbaseConfig] = None,
    client: Optional[CrunchbaseClient] = None
) -> CrunchbaseService:
    """Get or create a Crunchbase service instance.
    
    Args:
        config: Optional configuration for the client.
        client: Optional client instance. If not provided, a new one will be created.
        
    Returns:
        CrunchbaseService: Configured service instance
    """
    global _service
    
    if _service is None:
        if client is None:
            client = get_crunchbase_client(config)
        _service = CrunchbaseService(client=client)
        
    return _service

async def close_crunchbase_service() -> None:
    """Close the global Crunchbase service if it exists."""
    global _service
    
    if _service is not None:
        await _service.close()
        _service = None

async def with_crunchbase_service(config: Optional[CrunchbaseConfig] = None):
    """Context manager for using a Crunchbase service.
    
    Example:
        async with with_crunchbase_service() as service:
            company = await service.get_company_by_domain("example.com")
    """
    service = get_crunchbase_service(config)
    try:
        yield service
    finally:
        await service.close()
