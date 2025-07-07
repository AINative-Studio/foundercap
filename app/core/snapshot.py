import json
import logging
from typing import Any, Dict, Optional
from datetime import datetime

from app.core.service import Service as BaseService
from app.core.redis import get_redis

logger = logging.getLogger(__name__)


class SnapshotService(BaseService):
    """Service for managing company data snapshots with Redis caching."""

    def __init__(self):
        super().__init__()
        self.redis = get_redis()
        self._snapshots: Dict[str, Dict[str, Any]] = {}  # Fallback in-memory store
        self.use_redis = True

    @property
    def name(self) -> str:
        """Return the name of the service."""
        return "snapshot_service"

    async def _initialize(self) -> None:
        """Initialize the snapshot service."""
        try:
            # Test Redis connection
            await self.redis.ping()
            logger.info("Snapshot service initialized with Redis")
        except Exception as e:
            logger.warning(f"Redis not available, using in-memory storage: {e}")
            self.use_redis = False

    async def _shutdown(self) -> None:
        """Shut down the snapshot service."""
        logger.info("Snapshot service shut down.")

    async def get_latest_snapshot(self, company_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve the latest snapshot for a given company ID.

        Args:
            company_id: The unique identifier for the company.

        Returns:
            The latest snapshot data as a dictionary, or None if not found.
        """
        logger.debug(f"Retrieving latest snapshot for company_id: {company_id}")
        
        cache_key = f"snapshot:{company_id}"
        
        if self.use_redis:
            try:
                cached_data = await self.redis.get(cache_key)
                if cached_data:
                    return json.loads(cached_data)
            except Exception as e:
                logger.warning(f"Error retrieving from Redis: {e}")
                self.use_redis = False
        
        # Fallback to in-memory store
        return self._snapshots.get(company_id)

    async def save_snapshot(self, company_id: str, data: Dict[str, Any]) -> None:
        """Save a new snapshot for a company.

        Args:
            company_id: The unique identifier for the company.
            data: The company data to save as a snapshot.
        """
        logger.info(f"Saving snapshot for company_id: {company_id}")
        
        # Add metadata
        snapshot_data = {
            **data,
            "snapshot_metadata": {
                "company_id": company_id,
                "saved_at": datetime.utcnow().isoformat(),
                "version": "1.0"
            }
        }
        
        cache_key = f"snapshot:{company_id}"
        
        if self.use_redis:
            try:
                # Save to Redis with 30-day TTL
                await self.redis.setex(
                    cache_key, 
                    30 * 24 * 3600,  # 30 days
                    json.dumps(snapshot_data)
                )
                logger.debug(f"Snapshot saved to Redis for {company_id}")
            except Exception as e:
                logger.warning(f"Error saving to Redis: {e}")
                self.use_redis = False
        
        # Always save to in-memory as fallback
        self._snapshots[company_id] = snapshot_data

    async def list_snapshots(self, limit: int = 100) -> Dict[str, Any]:
        """List all available snapshots.
        
        Args:
            limit: Maximum number of snapshots to return
            
        Returns:
            Dictionary with snapshot metadata
        """
        snapshots = []
        
        if self.use_redis:
            try:
                # Get all snapshot keys from Redis
                keys = await self.redis.keys("snapshot:*")
                for key in keys[:limit]:
                    company_id = key.decode('utf-8').replace("snapshot:", "")
                    cached_data = await self.redis.get(key)
                    if cached_data:
                        data = json.loads(cached_data)
                        snapshots.append({
                            "company_id": company_id,
                            "saved_at": data.get("snapshot_metadata", {}).get("saved_at"),
                            "has_data": bool(data),
                            "sources": data.get("sources", [])
                        })
            except Exception as e:
                logger.warning(f"Error listing Redis snapshots: {e}")
        
        # Add in-memory snapshots
        for company_id, data in list(self._snapshots.items())[:limit]:
            snapshots.append({
                "company_id": company_id,
                "saved_at": data.get("snapshot_metadata", {}).get("saved_at"),
                "has_data": bool(data),
                "sources": data.get("sources", []),
                "storage": "memory"
            })
        
        return {
            "snapshots": snapshots,
            "total": len(snapshots),
            "storage_type": "redis" if self.use_redis else "memory"
        }

    async def delete_snapshot(self, company_id: str) -> bool:
        """Delete a snapshot for a company.
        
        Args:
            company_id: The unique identifier for the company.
            
        Returns:
            True if deleted, False if not found
        """
        cache_key = f"snapshot:{company_id}"
        deleted = False
        
        if self.use_redis:
            try:
                result = await self.redis.delete(cache_key)
                deleted = bool(result)
            except Exception as e:
                logger.warning(f"Error deleting from Redis: {e}")
        
        # Also remove from in-memory store
        if company_id in self._snapshots:
            del self._snapshots[company_id]
            deleted = True
        
        return deleted

    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check of the snapshot service.

        Returns:
            A dictionary indicating the health status.
        """
        status = "healthy" if self._is_initialized else "not_initialized"
        
        redis_status = "disconnected"
        if self.use_redis:
            try:
                await self.redis.ping()
                redis_status = "connected"
            except Exception:
                redis_status = "error"
        
        return {
            "name": self.name, 
            "status": status, 
            "memory_store_size": len(self._snapshots),
            "redis_status": redis_status,
            "storage_type": "redis" if self.use_redis else "memory"
        }
