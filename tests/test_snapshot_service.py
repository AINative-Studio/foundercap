import pytest
from app.core.snapshot import SnapshotService


class TestSnapshotService:
    @pytest.fixture
    async def snapshot_service(self):
        service = SnapshotService()
        await service.initialize()
        yield service
        await service.shutdown()

    async def test_initialization_and_shutdown(self, snapshot_service):
        assert snapshot_service._is_initialized is True
        assert snapshot_service.name == "snapshot_service"

        await snapshot_service.shutdown()
        assert snapshot_service._is_initialized is False

    async def test_save_and_get_snapshot(self, snapshot_service):
        company_id = "test_company_1"
        data = {"name": "Test Company", "funding": 1000000}

        await snapshot_service.save_snapshot(company_id, data)
        retrieved_data = await snapshot_service.get_latest_snapshot(company_id)

        assert retrieved_data == data

    async def test_get_nonexistent_snapshot(self, snapshot_service):
        company_id = "nonexistent_company"
        retrieved_data = await snapshot_service.get_latest_snapshot(company_id)
        assert retrieved_data is None

    async def test_update_snapshot(self, snapshot_service):
        company_id = "test_company_2"
        initial_data = {"name": "Test Company 2", "status": "Active"}
        updated_data = {"name": "Test Company 2", "status": "Inactive", "funding": 500000}

        await snapshot_service.save_snapshot(company_id, initial_data)
        await snapshot_service.save_snapshot(company_id, updated_data)

        retrieved_data = await snapshot_service.get_latest_snapshot(company_id)
        assert retrieved_data == updated_data

    async def test_health_check(self, snapshot_service):
        health = await snapshot_service.health_check()
        assert health["name"] == "snapshot_service"
        assert health["status"] == "healthy"
        assert health["store_size"] == 0

        await snapshot_service.save_snapshot("test_company_health", {"data": "some_data"})
        health = await snapshot_service.health_check()
        assert health["store_size"] == 1
