import pytest
from unittest.mock import AsyncMock, patch
import httpx

from app.services.updater.zerodb import ZeroDBUpdater
from app.core.config import settings


@pytest.fixture
def mock_settings(monkeypatch):
    """Mock settings with API key and URL."""
    monkeypatch.setattr(settings, 'ZERODB_API_KEY', 'test-api-key')
    monkeypatch.setattr(settings, 'ZERODB_API_URL', 'http://test.zerodb.com')


class TestZeroDBUpdater:
    @pytest.fixture
    async def updater(self):
        u = ZeroDBUpdater()
        yield u
        if u._is_initialized:
            await u.shutdown()

    async def test_initialization_success(self, updater, mock_settings):
        await updater.initialize()
        assert updater._is_initialized is True
        assert updater._client is not None

    async def test_initialization_without_api_key(self, updater):
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.ZERODB_API_KEY = ""
            mock_settings.ZERODB_API_URL = "http://test.zerodb.com"
            with pytest.raises(ValueError, match="ZERODB_API_KEY and ZERODB_API_URL are required"):
                await updater.initialize()

    async def test_shutdown(self, updater, mock_settings):
        await updater.initialize()
        assert updater._client is not None
        
        await updater.shutdown()
        assert updater._is_initialized is False
        assert updater._client is None

    async def test_update_success(self, updater, mock_settings):
        await updater.initialize()
        
        company_id = "company123"
        data = {"name": "Test Company", "value": 100}
        
        updater._client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": company_id, "data": data}
        updater._client.post.return_value = mock_response
        
        result = await updater.update(company_id, data)
        
        updater._client.post.assert_called_once_with(
            "/records",
            json={
                "id": company_id,
                "data": data
            }
        )
        assert result["id"] == company_id
        assert result["data"] == data

    async def test_update_http_error(self, updater, mock_settings):
        await updater.initialize()
        
        company_id = "company456"
        data = {"name": "Error Company"}
        
        updater._client = AsyncMock()
        updater._client.post.side_effect = httpx.HTTPStatusError(
            "Bad Request", request=httpx.Request("POST", "http://test.com/records"), response=httpx.Response(400)
        )
        
        with pytest.raises(httpx.HTTPStatusError):
            await updater.update(company_id, data)

    async def test_update_request_error(self, updater, mock_settings):
        await updater.initialize()
        
        company_id = "company789"
        data = {"name": "Network Error Company"}
        
        updater._client = AsyncMock()
        updater._client.post.side_effect = httpx.RequestError("Network is down")
        
        with pytest.raises(httpx.RequestError):
            await updater.update(company_id, data)

    async def test_invalidate_cache_success(self, updater, mock_settings):
        await updater.initialize()
        
        company_ids = ["company1", "company2"]
        
        updater._client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": "Cache invalidated"}
        updater._client.post.return_value = mock_response
        
        result = await updater.invalidate_cache(company_ids)
        
        updater._client.post.assert_called_once_with(
            "/cache/invalidate",
            json={
                "recordIds": company_ids
            }
        )
        assert result["message"] == "Cache invalidated"

    async def test_invalidate_cache_http_error(self, updater, mock_settings):
        await updater.initialize()
        
        company_ids = ["company1"]
        
        updater._client = AsyncMock()
        updater._client.post.side_effect = httpx.HTTPStatusError(
            "Internal Server Error", request=httpx.Request("POST", "http://test.com/cache/invalidate"), response=httpx.Response(500)
        )
        
        with pytest.raises(httpx.HTTPStatusError):
            await updater.invalidate_cache(company_ids)

    async def test_invalidate_cache_request_error(self, updater, mock_settings):
        await updater.initialize()
        
        company_ids = ["company1"]
        
        updater._client = AsyncMock()
        updater._client.post.side_effect = httpx.RequestError("Network is down")
        
        with pytest.raises(httpx.RequestError):
            await updater.invalidate_cache(company_ids)

    async def test_health_check(self, updater, mock_settings):
        health = await updater.health_check()
        assert health["name"] == "zerodb"
        assert health["status"] == "not_initialized"

        await updater.initialize()
        health = await updater.health_check()
        assert health["name"] == "zerodb"
        assert health["status"] == "healthy"
