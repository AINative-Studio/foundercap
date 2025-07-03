import pytest
from unittest.mock import AsyncMock, patch
import httpx

from app.services.updater.airtable import AirtableUpdater
from app.core.config import settings


@pytest.fixture
def mock_settings(monkeypatch):
    """Mock settings with API key and base ID."""
    monkeypatch.setattr(settings, 'AIRTABLE_API_KEY', 'test-api-key')
    monkeypatch.setattr(settings, 'AIRTABLE_BASE_ID', 'test-base-id')
    monkeypatch.setattr(settings, 'AIRTABLE_TABLE_NAME', 'TestTable')


class TestAirtableUpdater:
    @pytest.fixture
    async def updater(self):
        u = AirtableUpdater()
        yield u
        if u._is_initialized:
            await u.shutdown()

    async def test_initialization_success(self, updater, mock_settings):
        await updater.initialize()
        assert updater._is_initialized is True
        assert updater._client is not None

    async def test_initialization_without_api_key(self, updater):
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.AIRTABLE_API_KEY = ""
            mock_settings.AIRTABLE_BASE_ID = "test-base-id"
            mock_settings.AIRTABLE_TABLE_NAME = "TestTable"
            with pytest.raises(ValueError, match="AIRTABLE_API_KEY, AIRTABLE_BASE_ID, and AIRTABLE_TABLE_NAME are required"):
                await updater.initialize()

    async def test_shutdown(self, updater, mock_settings):
        await updater.initialize()
        assert updater._client is not None
        
        await updater.shutdown()
        assert updater._is_initialized is False
        assert updater._client is None

    async def test_update_success(self, updater, mock_settings):
        await updater.initialize()
        
        company_id = "rec123"
        data = {"Name": "New Company Name", "Status": "Active"}
        
        updater._client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"records": [{"id": company_id, "fields": data}]}
        updater._client.patch.return_value = mock_response
        
        result = await updater.update(company_id, data)
        
        updater._client.patch.assert_called_once_with(
            settings.AIRTABLE_TABLE_NAME,
            json={
                "records": [
                    {
                        "id": company_id,
                        "fields": data
                    }
                ],
                "typecast": False
            }
        )
        assert result["records"][0]["id"] == company_id
        assert result["records"][0]["fields"] == data

    async def test_update_with_typecast(self, updater, mock_settings):
        await updater.initialize()
        
        company_id = "rec456"
        data = {"Funding": "1000000"}
        
        updater._client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"records": [{"id": company_id, "fields": data}]}
        updater._client.patch.return_value = mock_response
        
        result = await updater.update(company_id, data, typecast=True)
        
        updater._client.patch.assert_called_once_with(
            settings.AIRTABLE_TABLE_NAME,
            json={
                "records": [
                    {
                        "id": company_id,
                        "fields": data
                    }
                ],
                "typecast": True
            }
        )
        assert result["records"][0]["id"] == company_id

    async def test_update_http_error(self, updater, mock_settings):
        await updater.initialize()
        
        company_id = "rec789"
        data = {"Name": "Error Company"}
        
        updater._client = AsyncMock()
        updater._client.patch.side_effect = httpx.HTTPStatusError(
            "Bad Request", request=httpx.Request("PATCH", "http://test.com"), response=httpx.Response(400)
        )
        
        with pytest.raises(httpx.HTTPStatusError):
            await updater.update(company_id, data)

    async def test_update_request_error(self, updater, mock_settings):
        await updater.initialize()
        
        company_id = "rec000"
        data = {"Name": "Network Error Company"}
        
        updater._client = AsyncMock()
        updater._client.patch.side_effect = httpx.RequestError("Network is down")
        
        with pytest.raises(httpx.RequestError):
            await updater.update(company_id, data)

    async def test_health_check(self, updater, mock_settings):
        health = await updater.health_check()
        assert health["name"] == "airtable"
        assert health["status"] == "not_initialized"

        await updater.initialize()
        health = await updater.health_check()
        assert health["name"] == "airtable"
        assert health["status"] == "healthy"
