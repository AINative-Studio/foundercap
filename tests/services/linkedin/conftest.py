"""Pytest configuration for LinkedIn service tests."""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.linkedin import LinkedInScraper, get_linkedin_service

@pytest.fixture
def mock_redis():
    """Fixture for a mock Redis client."""
    mock = AsyncMock()
    mock.get.return_value = None
    mock.setex.return_value = True
    return mock

@pytest.fixture
def mock_scraper():
    """Fixture for a mock LinkedInScraper."""
    mock = AsyncMock(spec=LinkedInScraper)
    mock.get_company_info.return_value = {
        "name": "Test Company",
        "website": "https://testcompany.com",
        "company_size": "1001-5000 employees",
        "industry": "Information Technology"
    }
    return mock

@pytest.fixture
def mock_playwright():
    """Fixture for mocking Playwright components."""
    with patch('app.services.linkedin.scraper.async_playwright') as mock_async_playwright:
        mock_playwright_instance = AsyncMock()
        mock_playwright_instance.chromium.launch.return_value = AsyncMock()
        mock_playwright_instance.chromium.launch.return_value.__aenter__.return_value = AsyncMock()
        mock_playwright_instance.chromium.launch.return_value.__aexit__.return_value = None
        mock_playwright_instance.chromium.launch.return_value.new_context.return_value = AsyncMock()
        mock_playwright_instance.chromium.launch.return_value.new_context.return_value.__aenter__.return_value = AsyncMock()
        mock_playwright_instance.chromium.launch.return_value.new_context.return_value.__aexit__.return_value = None
        mock_playwright_instance.chromium.launch.return_value.new_context.return_value.new_page.return_value = AsyncMock()
        mock_playwright_instance.chromium.launch.return_value.new_context.return_value.new_page.return_value.set_default_timeout.return_value = None
        mock_playwright_instance.chromium.launch.return_value.new_context.return_value.new_page.return_value.goto.return_value = None
        mock_playwright_instance.chromium.launch.return_value.new_context.return_value.new_page.return_value.wait_for_selector.return_value = AsyncMock()
        mock_playwright_instance.chromium.launch.return_value.new_context.return_value.new_page.return_value.query_selector.return_value = AsyncMock()
        mock_playwright_instance.chromium.launch.return_value.new_context.return_value.new_page.return_value.evaluate.return_value = None
        mock_playwright_instance.chromium.launch.return_value.new_context.return_value.new_page.return_value.fill.return_value = None
        mock_playwright_instance.chromium.launch.return_value.new_context.return_value.new_page.return_value.click.return_value = None
        mock_playwright_instance.chromium.launch.return_value.new_context.return_value.new_page.return_value.wait_for_load_state.return_value = None
        mock_playwright_instance.chromium.launch.return_value.new_context.return_value.new_page.return_value.url = "https://www.linkedin.com/feed/"
        mock_playwright_instance.chromium.launch.return_value.new_context.return_value.new_page.return_value.get_attribute.return_value = "test-company"
        mock_playwright_instance.chromium.launch.return_value.new_context.return_value.new_page.return_value.text_content.return_value = "Test Text"
        mock_playwright_instance.chromium.launch.return_value.new_context.return_value.pages.return_value = []

        mock_async_playwright.return_value = mock_playwright_instance
        mock_async_playwright.return_value.start.return_value = mock_playwright_instance

        yield mock_async_playwright, mock_playwright_instance.chromium.launch.return_value.new_context.return_value.new_page.return_value
