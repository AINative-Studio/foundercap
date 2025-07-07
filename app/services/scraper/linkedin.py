import asyncio
import logging
import time
import random
from typing import Any, Dict, Optional, List, Tuple
from enum import Enum
from pathlib import Path

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from pydantic import BaseModel

from app.core.config import settings
from app.services.scraper.base import BaseScraper


logger = logging.getLogger(__name__)


class ScrapeStatus(str, Enum):
    SUCCESS = "success"
    TRANSIENT_ERROR = "transient_error"
    HARD_ERROR = "hard_error"


class LinkedInCompanyData(BaseModel):
    """LinkedIn company data model."""
    name: str
    linkedin_url: str
    website: Optional[str] = None
    status: str = "Unknown"
    headcount: Optional[str] = None
    industry: Optional[str] = None
    headquarters: Optional[str] = None
    description: Optional[str] = None
    specialties: List[str] = []


class LinkedInScraper(BaseScraper):
    """Scraper for LinkedIn company data using Playwright."""

    def __init__(self, headless: bool = True, max_retries: int = 3):
        """Initialize the LinkedIn scraper."""
        super().__init__()
        self.headless = headless
        self.max_retries = max_retries
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None
        self.screenshot_dir = Path("screenshots")
        self.screenshot_dir.mkdir(exist_ok=True)
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._shutdown()

    @property
    def name(self) -> str:
        """Return the name of the scraper."""
        return "linkedin"

    async def _initialize(self) -> None:
        """Initialize the LinkedIn scraper with Playwright."""
        if not settings.LINKEDIN_EMAIL or not settings.LINKEDIN_PASSWORD:
            raise ValueError("LINKEDIN_EMAIL and LINKEDIN_PASSWORD are required")
        
        logger.info("Initializing Playwright...")
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self.headless,
            args=['--no-sandbox']
        )
        self._context = await self._browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        self._page = await self._context.new_page()
        await self._page.set_default_timeout(30000)  # 30 seconds
        
        # Login to LinkedIn
        await self._login()
        logger.info("LinkedIn scraper initialized")

    async def _shutdown(self) -> None:
        """Shut down the LinkedIn scraper and clean up resources."""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info("LinkedIn scraper shut down")

    async def _take_screenshot(self, name: str) -> str:
        """Take a screenshot for debugging."""
        path = self.screenshot_dir / f"{int(time.time())}_{name}.png"
        await self._page.screenshot(path=str(path))
        return str(path)

    async def _login(self) -> bool:
        """Login to LinkedIn with retry logic."""
        logger.info("Logging in to LinkedIn...")
        
        try:
            await self._page.goto('https://www.linkedin.com/login', timeout=60000)
            
            # Fill email and password with human-like typing
            await self._page.fill('input[name="session_key"]', settings.LINKEDIN_EMAIL, delay=100)
            await asyncio.sleep(random.uniform(0.5, 1.5))
            await self._page.fill('input[name="session_password"]', settings.LINKEDIN_PASSWORD, delay=100)
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # Submit form
            await self._page.click('button[type="submit"]')
            
            # Wait for either login success or 2FA
            try:
                # Check for 2FA or verification
                verification_needed = await self._page.wait_for_selector(
                    'input[aria-label*="verification"], input[name="verificationCode"]',
                    timeout=10000
                )
                if verification_needed:
                    logger.info("2FA verification required. Please complete in browser...")
                    await self._take_screenshot("2fa_required")
                    # Wait for manual verification
                    await self._page.wait_for_selector(
                        'input[role="combobox"][aria-label*="Search"]',
                        timeout=180000  # 3 minutes for manual verification
                    )
            except PlaywrightTimeoutError:
                # No verification needed, continue with normal login flow
                pass
            
            # Verify login success
            try:
                await self._page.wait_for_selector('input[role="combobox"][aria-label*="Search"]', timeout=10000)
                logger.info("Login successful")
                return True
            except PlaywrightTimeoutError:
                error = await self._page.query_selector('.error-for-password, .error-for-username')
                if error:
                    error_msg = await error.inner_text()
                    logger.error(f"Login failed: {error_msg}")
                else:
                    logger.error("Login verification timeout")
                return False
                
        except Exception as e:
            await self._take_screenshot("login_error")
            logger.error(f"Login error: {str(e)}")
            return False

    async def _extract_company_info(self, company_name: str) -> LinkedInCompanyData:
        """Extract company information from LinkedIn page."""
        # Convert company name to LinkedIn URL format
        company_slug = company_name.lower().replace(' ', '-')
        url = f"https://www.linkedin.com/company/{company_slug}/about/"
        
        logger.info(f"Scraping company page: {url}")
        await self._page.goto(url, timeout=60000)
        
        # Take screenshot for debugging
        await self._take_screenshot(f"company_{company_slug}")
        
        # Extract company data
        company_data = LinkedInCompanyData(
            name=company_name,
            linkedin_url=url,
            website=await self._extract_attribute('a[data-tracking-control-name="about_website"]', 'href'),
            headcount=await self._extract_employee_count(),
            status=await self._extract_company_status() or "Active",  # Default to Active if not found
            industry=await self._extract_text('div.org-about-company-module__company-industries'),
            headquarters=await self._extract_text('div.org-about-company-module__headquarters'),
            description=await self._extract_text('p.break-words, p.about-us-details'),
            specialties=await self._extract_specialties()
        )
        
        return company_data
    
    async def _extract_text(self, selector: str) -> Optional[str]:
        """Helper to safely extract text from a selector."""
        try:
            element = await self._page.query_selector(selector)
            return await element.inner_text() if element else None
        except:
            return None
    
    async def _extract_attribute(self, selector: str, attribute: str) -> Optional[str]:
        """Helper to safely extract an attribute from a selector."""
        try:
            element = await self._page.query_selector(selector)
            return await element.get_attribute(attribute) if element else None
        except:
            return None
    
    async def _extract_employee_count(self) -> Optional[str]:
        """Extract employee count from various possible locations."""
        selectors = [
            'div.org-about-company-module__company-size-definition-text',
            'dt:has-text("Company size") + dd',
            'dt:has-text("Size") + dd',
            'a[href*="employeeCount"]'
        ]
        
        for selector in selectors:
            count = await self._extract_text(selector)
            if count:
                return count
        return None
    
    async def _extract_company_status(self) -> Optional[str]:
        """Extract company status (e.g., Public, Private)."""
        status = await self._extract_text('div.org-about-company-module__company-type')
        if not status:
            status = await self._extract_text('dt:has-text("Type") + dd')
        return status
    
    async def _extract_specialties(self) -> List[str]:
        """Extract company specialties."""
        try:
            # Click "Show more" if it exists
            show_more = await self._page.query_selector('button[aria-expanded="false"]:has-text("Show")')
            if show_more:
                await show_more.click()
                await asyncio.sleep(1)  # Wait for the content to load
            
            # Extract specialties
            specialty_elements = await self._page.query_selector_all('span.org-about-company-module__company-specialty')
            return [await el.inner_text() for el in specialty_elements if await el.inner_text()]
        except:
            return []

    async def scrape(self, company_name: str, **kwargs: Any) -> Dict[str, Any]:
        """Scrape data for a company from LinkedIn.
        
        Args:
            company_name: The name of the company to scrape.
            **kwargs: Additional arguments (unused).
            
        Returns:
            Dictionary containing scraped company data.
            
        Raises:
            ValueError: If company_name is not provided.
            RuntimeError: If scraping fails after max retries.
        """
        if not company_name:
            raise ValueError("company_name is required")
            
        retry_count = 0
        last_error = None
        
        while retry_count <= self.max_retries:
            try:
                # Initialize if not already done
                if not self._page:
                    await self._initialize()
                
                # Scrape company data
                company_data = await self._extract_company_info(company_name)
                
                # Validate required fields
                required_fields = ['name', 'website', 'headcount', 'status']
                missing_fields = [f for f in required_fields if not getattr(company_data, f, None)]
                
                if missing_fields:
                    logger.warning(f"Missing required fields: {', '.join(missing_fields)}"
                                 f" for company: {company_name}")
                
                logger.info(f"Successfully scraped LinkedIn data for {company_name}")
                return {
                    "source": "linkedin",
                    "company_name": company_name,
                    "data": company_data.model_dump(),
                    "scraped_at": time.time(),
                    "status": "success",
                    "missing_fields": missing_fields if missing_fields else None
                }
                
            except Exception as e:
                last_error = str(e)
                retry_count += 1
                logger.warning(f"Attempt {retry_count} failed for {company_name}: {last_error}")
                
                if retry_count <= self.max_retries:
                    wait_time = 2 ** retry_count  # Exponential backoff
                    logger.info(f"Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                
                # Take screenshot on error
                await self._take_screenshot(f"error_{company_name}_{retry_count}")
        
        # If we get here, all retries failed
        error_msg = f"Failed to scrape {company_name} after {self.max_retries} attempts. Last error: {last_error}"
        logger.error(error_msg)
        
        return {
            "source": "linkedin",
            "company_name": company_name,
            "status": "error",
            "error": error_msg,
            "scraped_at": time.time()
        }
