"""Tests for the snapshot service functionality."""
import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.core.snapshot import SnapshotService


@pytest.fixture
def snapshot_service():
    """Create a snapshot service instance for testing."""
    return SnapshotService()


@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    mock = AsyncMock()
    mock.ping.return_value = True
    mock.get.return_value = None
    mock.setex.return_value = True
    mock.delete.return_value = 1
    mock.keys.return_value = []
    return mock


class TestSnapshotService:
    """Test the snapshot service functionality."""
    
    @pytest.mark.asyncio
    async def test_initialization_with_redis(self, snapshot_service, mock_redis):
        """Test successful initialization with Redis."""
        with patch('app.core.snapshot.get_redis', return_value=mock_redis):
            await snapshot_service._initialize()
            
            assert snapshot_service.use_redis is True
            mock_redis.ping.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_initialization_without_redis(self, snapshot_service):
        """Test initialization fallback when Redis is unavailable."""
        mock_redis = AsyncMock()
        mock_redis.ping.side_effect = Exception("Redis unavailable")
        
        with patch('app.core.snapshot.get_redis', return_value=mock_redis):
            await snapshot_service._initialize()
            
            assert snapshot_service.use_redis is False
    
    @pytest.mark.asyncio
    async def test_save_snapshot_with_redis(self, snapshot_service, mock_redis):
        """Test saving snapshot with Redis available."""
        with patch('app.core.snapshot.get_redis', return_value=mock_redis):
            snapshot_service.use_redis = True
            
            test_data = {"name": "Test Company", "employees": 100}
            await snapshot_service.save_snapshot("test-company", test_data)
            
            # Verify Redis call
            mock_redis.setex.assert_called_once()
            call_args = mock_redis.setex.call_args
            assert call_args[0][0] == "snapshot:test-company"
            assert call_args[0][1] == 30 * 24 * 3600  # 30 days TTL
            
            # Verify data structure
            saved_data = json.loads(call_args[0][2])
            assert saved_data["name"] == "Test Company"
            assert saved_data["employees"] == 100
            assert "snapshot_metadata" in saved_data
            assert "company_id" in saved_data["snapshot_metadata"]
            assert "saved_at" in saved_data["snapshot_metadata"]
            
            # Verify in-memory fallback also works
            assert "test-company" in snapshot_service._snapshots
    
    @pytest.mark.asyncio
    async def test_save_snapshot_memory_only(self, snapshot_service):
        """Test saving snapshot with only in-memory storage."""
        snapshot_service.use_redis = False
        
        test_data = {"name": "Test Company", "employees": 100}
        await snapshot_service.save_snapshot("test-company", test_data)
        
        # Verify in-memory storage
        assert "test-company" in snapshot_service._snapshots
        saved_data = snapshot_service._snapshots["test-company"]
        assert saved_data["name"] == "Test Company"
        assert saved_data["employees"] == 100
        assert "snapshot_metadata" in saved_data
    
    @pytest.mark.asyncio
    async def test_get_latest_snapshot_from_redis(self, snapshot_service, mock_redis):
        """Test retrieving snapshot from Redis."""
        test_data = {
            "name": "Test Company",
            "employees": 100,
            "snapshot_metadata": {
                "company_id": "test-company",
                "saved_at": datetime.utcnow().isoformat(),
                "version": "1.0"
            }
        }
        mock_redis.get.return_value = json.dumps(test_data)
        
        with patch('app.core.snapshot.get_redis', return_value=mock_redis):
            snapshot_service.use_redis = True
            
            result = await snapshot_service.get_latest_snapshot("test-company")
            
            mock_redis.get.assert_called_once_with("snapshot:test-company")
            assert result == test_data
    
    @pytest.mark.asyncio
    async def test_get_latest_snapshot_fallback_to_memory(self, snapshot_service, mock_redis):
        """Test fallback to memory when Redis fails."""
        mock_redis.get.side_effect = Exception("Redis error")
        
        # Add data to memory store
        test_data = {"name": "Test Company", "employees": 100}
        snapshot_service._snapshots["test-company"] = test_data
        
        with patch('app.core.snapshot.get_redis', return_value=mock_redis):
            snapshot_service.use_redis = True
            
            result = await snapshot_service.get_latest_snapshot("test-company")
            
            assert result == test_data
            assert snapshot_service.use_redis is False  # Should disable Redis after error
    
    @pytest.mark.asyncio
    async def test_get_snapshot_not_found(self, snapshot_service):
        """Test retrieving non-existent snapshot."""
        snapshot_service.use_redis = False
        
        result = await snapshot_service.get_latest_snapshot("nonexistent")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_delete_snapshot(self, snapshot_service, mock_redis):
        """Test deleting a snapshot."""
        # Add data to both Redis and memory
        snapshot_service._snapshots["test-company"] = {"name": "Test"}
        
        with patch('app.core.snapshot.get_redis', return_value=mock_redis):
            snapshot_service.use_redis = True
            
            result = await snapshot_service.delete_snapshot("test-company")
            
            assert result is True
            mock_redis.delete.assert_called_once_with("snapshot:test-company")
            assert "test-company" not in snapshot_service._snapshots
    
    @pytest.mark.asyncio
    async def test_delete_snapshot_not_found(self, snapshot_service):
        """Test deleting non-existent snapshot."""
        snapshot_service.use_redis = False
        
        result = await snapshot_service.delete_snapshot("nonexistent")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_list_snapshots_with_redis(self, snapshot_service, mock_redis):
        """Test listing snapshots from Redis."""
        mock_keys = [b"snapshot:company1", b"snapshot:company2"]
        mock_redis.keys.return_value = mock_keys
        
        test_data1 = {
            "name": "Company 1",
            "sources": ["linkedin"],
            "snapshot_metadata": {
                "saved_at": "2023-01-01T00:00:00"
            }
        }
        test_data2 = {
            "name": "Company 2", 
            "sources": ["crunchbase"],
            "snapshot_metadata": {
                "saved_at": "2023-01-02T00:00:00"
            }
        }
        
        mock_redis.get.side_effect = [
            json.dumps(test_data1),
            json.dumps(test_data2)
        ]
        
        with patch('app.core.snapshot.get_redis', return_value=mock_redis):
            snapshot_service.use_redis = True
            
            result = await snapshot_service.list_snapshots()
            
            assert result["total"] == 2
            assert result["storage_type"] == "redis"
            assert len(result["snapshots"]) == 2
            
            # Check snapshot metadata
            snapshots = result["snapshots"]
            assert snapshots[0]["company_id"] == "company1"
            assert snapshots[0]["sources"] == ["linkedin"]
            assert snapshots[1]["company_id"] == "company2"
            assert snapshots[1]["sources"] == ["crunchbase"]
    
    @pytest.mark.asyncio
    async def test_list_snapshots_memory_only(self, snapshot_service):
        """Test listing snapshots from memory only."""
        snapshot_service.use_redis = False
        snapshot_service._snapshots = {
            "company1": {
                "name": "Company 1",
                "sources": ["linkedin"],
                "snapshot_metadata": {
                    "saved_at": "2023-01-01T00:00:00"
                }
            },
            "company2": {
                "name": "Company 2",
                "sources": ["crunchbase"],
                "snapshot_metadata": {
                    "saved_at": "2023-01-02T00:00:00"
                }
            }
        }
        
        result = await snapshot_service.list_snapshots()
        
        assert result["total"] == 2
        assert result["storage_type"] == "memory"
        assert len(result["snapshots"]) == 2
    
    @pytest.mark.asyncio
    async def test_health_check(self, snapshot_service, mock_redis):
        """Test health check functionality."""
        with patch('app.core.snapshot.get_redis', return_value=mock_redis):
            snapshot_service.use_redis = True
            snapshot_service._is_initialized = True
            snapshot_service._snapshots = {"test": {}}
            
            health = await snapshot_service.health_check()
            
            assert health["name"] == "snapshot_service"
            assert health["status"] == "healthy"
            assert health["memory_store_size"] == 1
            assert health["redis_status"] == "connected"
            assert health["storage_type"] == "redis"
    
    @pytest.mark.asyncio
    async def test_health_check_redis_error(self, snapshot_service, mock_redis):
        """Test health check when Redis has errors."""
        mock_redis.ping.side_effect = Exception("Redis down")
        
        with patch('app.core.snapshot.get_redis', return_value=mock_redis):
            snapshot_service.use_redis = True
            snapshot_service._is_initialized = True
            
            health = await snapshot_service.health_check()
            
            assert health["redis_status"] == "error"