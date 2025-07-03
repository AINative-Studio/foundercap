"""Unit tests for LinkedIn scraper."""
import asyncio
import pytest
from unittest.mock import AsyncMock, patch

from app.services.scraper.linkedin import LinkedInScraper, LinkedInCompanyData
from app.core.config import settings


@pytest.fixture
def mock_settings(monkeypatch):
    """Mock settings with API key."""
    monkeypatch.setattr(settings, 'LINKEDIN_EMAIL', 'test@example.com')
    monkeypatch.setattr(settings, 'LINKEDIN_PASSWORD', 'test-password')


class TestLinkedInCompanyData:
    """Test the LinkedInCompanyData model."""

    def test_default_values(self):
        """Test default values are set correctly."""
        data = LinkedInCompanyData()
        assert data.operating_status is None
        assert data.website is None
        assert data.headcount_estimate is None
        assert data.about_text is None

    def test_with_values(self):
        """Test initialization with values."""
        data = LinkedInCompanyData(
            operating_status="Active",
            website="https://example.com",
            headcount_estimate=100,
            about_text="About text here"
        )
        assert data.operating_status == "Active"
        assert data.website == "https://example.com"
        assert data.headcount_estimate == 100
        assert data.about_text == "About text here"


class TestLinkedInScraper:
    """Test the LinkedInScraper class."""

    @pytest.fixture
    async def scraper(self):
        """Create a LinkedIn scraper instance."""
        s = LinkedInScraper()
        yield s
        if s._is_initialized:
            await s.shutdown()

    def test_name_property(self, scraper):
        """Test the name property."""
        assert scraper.name == "linkedin"

    async def test_initialization_success(self, scraper, mock_settings):
        """Test successful initialization."""
        await scraper.initialize()
        assert scraper._is_initialized is True

    async def test_initialization_without_credentials(self, scraper):
        """Test initialization failure without credentials."""
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.LINKEDIN_EMAIL = ""
            mock_settings.LINKEDIN_PASSWORD = ""
            with pytest.raises(ValueError, match="LINKEDIN_EMAIL and LINKEDIN_PASSWORD are required"):
                await scraper.initialize()

    async def test_shutdown(self, scraper, mock_settings):
        """Test shutdown closes the client."""
        await scraper.initialize()
        
        await scraper.shutdown()
        assert scraper._is_initialized is False

    async def test_scrape_method(self, scraper, mock_settings):
        """Test the basic scrape method."""
        await scraper.initialize()
        
        company_name = "Test Company"
        result = await scraper.scrape(company_name)
        
        assert result["source"] == "linkedin"
        assert result["company_name"] == company_name
        assert "data" in result
        assert "scraped_at" in result
        assert isinstance(result["data"], dict)
