"""Unit tests for Crunchbase scraper."""
import asyncio
import pytest
from unittest.mock import AsyncMock, Mock, patch
import httpx

from app.services.scraper.crunchbase import CrunchbaseScraper, CrunchbaseCompanyData
from app.core.config import settings


@pytest.fixture
def mock_settings(monkeypatch):
    """Mock settings with API key."""
    monkeypatch.setattr(settings, 'CRUNCHBASE_API_KEY', 'test-api-key')


class TestCrunchbaseCompanyData:
    """Test the CrunchbaseCompanyData model."""

    def test_default_values(self):
        """Test default values are set correctly."""
        data = CrunchbaseCompanyData()
        assert data.total_funding is None
        assert data.funding_stage is None
        assert data.investors == []

    def test_with_values(self):
        """Test initialization with values."""
        data = CrunchbaseCompanyData(
            total_funding=1000000,
            funding_stage="Series A",
            investors=["VC 1", "VC 2"]
        )
        assert data.total_funding == 1000000
        assert data.funding_stage == "Series A"
        assert data.investors == ["VC 1", "VC 2"]


class TestCrunchbaseScraper:
    """Test the CrunchbaseScraper class."""

    @pytest.fixture
    async def scraper(self):
        """Create a Crunchbase scraper instance."""
        s = CrunchbaseScraper()
        # We don't want to actually sleep in tests
        with patch('asyncio.sleep', new_callable=AsyncMock):
            yield s
        if s._is_initialized:
            await s.shutdown()

    def test_name_property(self, scraper):
        """Test the name property."""
        assert scraper.name == "crunchbase"

    async def test_initialization_success(self, scraper, mock_settings):
        """Test successful initialization."""
        await scraper.initialize()
        assert scraper._is_initialized is True
        assert scraper._client is not None

    async def test_initialization_without_api_key(self, scraper):
        """Test initialization failure without API key."""
        with pytest.raises(ValueError, match="CRUNCHBASE_API_KEY is required"):
            await scraper.initialize()

    async def test_shutdown(self, scraper, mock_settings):
        """Test shutdown closes the client."""
        await scraper.initialize()
        assert scraper._client is not None
        
        await scraper.shutdown()
        assert scraper._is_initialized is False
        assert scraper._client is None

    async def test_fetch_crunchbase_empty_permalink(self, scraper, mock_settings):
        """Test fetch with empty permalink raises ValueError."""
        await scraper.initialize()
        
        with pytest.raises(ValueError, match="Permalink cannot be empty"):
            await scraper.fetch_crunchbase("")

    async def test_fetch_crunchbase_not_initialized(self, scraper):
        """Test fetch without initialization raises RuntimeError."""
        with pytest.raises(RuntimeError, match="Scraper not initialized"):
            await scraper.fetch_crunchbase("test-company")

    async def test_fetch_crunchbase_success(self, scraper, mock_settings):
        """Test successful API fetch."""
        await scraper.initialize()
        
        # Mock successful API response
        mock_response_data = {
            "properties": {
                "funding_total": {"value_usd": 5000000},
                "funding_stage": "Series B",
                "investors": [
                    {"name": "Sequoia Capital"},
                    {"identifier": {"value": "Andreessen Horowitz"}}
                ]
            }
        }
        
        scraper._client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        scraper._client.get.return_value = mock_response
        
        result = await scraper.fetch_crunchbase("test-company")
        
        assert isinstance(result, CrunchbaseCompanyData)
        assert result.total_funding == 5000000
        assert result.funding_stage == "Series B"
        assert "Sequoia Capital" in result.investors
        assert "Andreessen Horowitz" in result.investors

    async def test_fetch_crunchbase_404(self, scraper, mock_settings):
        """Test handling of 404 (company not found)."""
        await scraper.initialize()
        
        scraper._client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 404
        scraper._client.get.return_value = mock_response
        
        result = await scraper.fetch_crunchbase("nonexistent-company")
        
        assert isinstance(result, CrunchbaseCompanyData)
        assert result.total_funding is None
        assert result.funding_stage is None
        assert result.investors == []

    async def test_fetch_crunchbase_rate_limit_retry(self, scraper, mock_settings):
        """Test rate limit handling with retry."""
        await scraper.initialize()
        
        scraper._client = AsyncMock()
        # First call returns 429, second call succeeds
        mock_response_429 = AsyncMock()
        mock_response_429.status_code = 429
        mock_response_429.headers = {"Retry-After": "1"}
        
        mock_response_200 = AsyncMock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {
            "properties": {
                "funding_total": {"value_usd": 1000000},
                "funding_stage": "Seed",
                "investors": []
            }
        }
        
        scraper._client.get.side_effect = [mock_response_429, mock_response_200]
        
        result = await scraper.fetch_crunchbase("test-company")
        
        assert result.total_funding == 1000000
        assert result.funding_stage == "Seed"
        assert asyncio.sleep.call_count == 2

    async def test_fetch_crunchbase_http_error(self, scraper, mock_settings):
        """Test handling of HTTP errors."""
        await scraper.initialize()
        
        scraper._client = AsyncMock()
        scraper._client.get.side_effect = httpx.HTTPStatusError(
            "Server Error", request=Mock(), response=Mock(status_code=500)
        )
        
        with pytest.raises(httpx.HTTPStatusError):
            await scraper.fetch_crunchbase("test-company")

    async def test_fetch_crunchbase_request_error_retry(self, scraper, mock_settings):
        """Test handling of request errors with retry."""
        await scraper.initialize()
        
        scraper._client = AsyncMock()
        # First calls raise RequestError, final call succeeds
        scraper._client.get.side_effect = [
            httpx.RequestError("Network error"),
            httpx.RequestError("Network error"),
                                    AsyncMock(status_code=200, json=AsyncMock(return_value={
                "properties": {
                    "funding_total": {"value_usd": 2000000},
                    "funding_stage": "Series A",
                    "investors": []
                }
            }))
        ]
        
        result = await scraper.fetch_crunchbase("test-company")
        
        assert result.total_funding == 2000000
        assert asyncio.sleep.call_count == 4  # Two retries, plus two rate limit waits

    async def test_fetch_crunchbase_max_retries_exceeded(self, scraper, mock_settings):
        """Test failure after max retries exceeded."""
        await scraper.initialize()
        
        scraper._client = AsyncMock()
        scraper._client.get.side_effect = [httpx.RequestError("Persistent network error")] * (scraper._max_retries + 1)

        with pytest.raises(RuntimeError, match=f"Failed to fetch data after {scraper._max_retries} attempts"):
            await scraper.fetch_crunchbase("test-company")

    async def test_fetch_crunchbase_caching(self, scraper, mock_settings):
        """Test that results are cached."""
        await scraper.initialize()
        
        mock_response_data = {
            "properties": {
                "funding_total": {"value": 3000000},
                "funding_stage": "Series A",
                "investors": []
            }
        }
        
        scraper._client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        scraper._client.get.return_value = mock_response
        
        # First call should hit API
        result1 = await scraper.fetch_crunchbase("test-company")
        assert scraper._client.get.call_count == 1
        
        # Second call should use cache
        result2 = await scraper.fetch_crunchbase("test-company")
        assert scraper._client.get.call_count == 1  # No additional API call
        
        assert result1.total_funding == result2.total_funding

    def test_parse_company_data_complete(self, scraper):
        """Test parsing complete company data."""
        data = {
            "properties": {
                "funding_total": {"value": 10000000},
                "funding_stage": "Series C",
                "investors": [
                    {"name": "Tiger Global"},
                    {"identifier": {"value": "Accel Partners"}},
                    {"name": "GV"}
                ]
            }
        }
        
        result = scraper._parse_company_data(data)
        
        assert result.total_funding == 10000000
        assert result.funding_stage == "Series C"
        assert "Tiger Global" in result.investors
        assert "Accel Partners" in result.investors
        assert "GV" in result.investors

    def test_parse_company_data_minimal(self, scraper):
        """Test parsing minimal company data."""
        data = {"properties": {}}
        
        result = scraper._parse_company_data(data)
        
        assert result.total_funding is None
        assert result.funding_stage is None
        assert result.investors == []

    def test_parse_company_data_malformed(self, scraper):
        """Test parsing malformed data returns empty result."""
        data = {"invalid": "structure"}
        
        result = scraper._parse_company_data(data)
        
        assert result.total_funding is None
        assert result.funding_stage is None
        assert result.investors == []

    async def test_scrape_success(self, scraper, mock_settings):
        """Test the scrape method with successful result."""
        await scraper.initialize()
        
        with patch.object(scraper, "fetch_crunchbase", new_callable=AsyncMock) as mock_fetch:
            mock_data = CrunchbaseCompanyData(
                total_funding=1500000,
                funding_stage="Seed",
                investors=["Y Combinator"]
            )
            mock_fetch.return_value = mock_data
            
            result = await scraper.scrape("Test Company")
            
            assert result["source"] == "crunchbase"
            assert result["company_name"] == "Test Company"
            assert result["permalink"] == "test-company"
            assert result["data"]["total_funding"] == 1500000
            assert "scraped_at" in result

    async def test_scrape_with_custom_permalink(self, scraper, mock_settings):
        """Test the scrape method with custom permalink."""
        await scraper.initialize()
        
        with patch.object(scraper, "fetch_crunchbase", new_callable=AsyncMock) as mock_fetch:
            mock_data = CrunchbaseCompanyData()
            mock_fetch.return_value = mock_data
            
            result = await scraper.scrape("Test Company", permalink="custom-permalink")
            
            assert result["permalink"] == "custom-permalink"
            mock_fetch.assert_called_once_with("custom-permalink")

    async def test_scrape_error_handling(self, scraper, mock_settings):
        """Test the scrape method error handling."""
        await scraper.initialize()
        
        with patch.object(scraper, "fetch_crunchbase", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = Exception("API Error")
            
            result = await scraper.scrape("Test Company")
            
            assert result["source"] == "crunchbase"
            assert result["company_name"] == "Test Company"
            assert "error" in result
            assert result["error"] == "API Error"

    def test_cache_management(self, scraper):
        """Test cache management methods."""
        # Add some dummy data to cache
        scraper._cache["test1"] = {"total_funding": 1000}
        scraper._cache["test2"] = {"total_funding": 2000}
        
        assert scraper.get_cache_size() == 2
        
        scraper.clear_cache()
        assert scraper.get_cache_size() == 0

    async def test_health_check(self, scraper, mock_settings):
        """Test health check functionality."""
        # Before initialization
        health = await scraper.health_check()
        assert health["name"] == "crunchbase"
        assert health["status"] == "not_initialized"
        
        # After initialization
        await scraper.initialize()
        health = await scraper.health_check()
        assert health["name"] == "crunchbase"
        assert health["status"] == "healthy"
