"""Tests for the LinkedIn scraper."""
import pytest
from app.services.linkedin.scraper import LinkedInScraper

class TestLinkedInScraper:
    """Test cases for LinkedInScraper."""
    
    @pytest.mark.asyncio
    async def test_scraper_initialization(self):
        """Test LinkedInScraper initialization."""
        async with LinkedInScraper(headless=True, slow_mo=100) as scraper:
            assert scraper is not None
            assert scraper.headless is True
            assert scraper.slow_mo == 100

    @pytest.mark.asyncio
    async def test_scraper_login(self, mock_playwright):
        """Test LinkedIn login."""
        mock_playwright, mock_page = mock_playwright
        
        async with LinkedInScraper() as scraper:
            logged_in = await scraper.login("test@example.com", "password123")
            
            # Assertions
            assert logged_in is True
            mock_page.goto.assert_called()
            mock_page.fill.assert_any_call('#username', 'test@example.com')
            mock_page.fill.assert_any_call('#password', 'password123')
            mock_page.click.assert_called()

    @pytest.mark.asyncio
    async def test_scraper_company_info(self, mock_playwright):
        """Test scraping company info."""
        mock_playwright, mock_page = mock_playwright
        
        # Configure the page to return mock data
        mock_page.evaluate.return_value = {
            "name": "Test Company",
            "website": "https://testcompany.com",
            "company_size": "1001-5000 employees",
            "industry": "Information Technology"
        }
        
        async with LinkedInScraper() as scraper:
            scraper.page = mock_page
            company_info = await scraper.get_company_info("Test Company")
            
            # Assertions
            assert company_info is not None
            assert company_info["name"] == "Test Company"
            mock_page.goto.assert_called()
            mock_page.wait_for_selector.assert_called()
            mock_page.query_selector.assert_called()
            
    @pytest.mark.asyncio
    async def test_scraper_company_not_found(self, mock_playwright):
        """Test handling when company is not found."""
        mock_playwright, mock_page = mock_playwright
        mock_page.query_selector.return_value = None  # Simulate company not found
        
        async with LinkedInScraper() as scraper:
            scraper.page = mock_page
            company_info = await scraper.get_company_info("Nonexistent Company")
            
            # Assertions
            assert company_info is None
            mock_page.goto.assert_called()
            mock_page.wait_for_selector.assert_called()
            mock_page.query_selector.assert_called()
