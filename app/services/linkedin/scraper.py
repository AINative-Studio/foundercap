"""
LinkedIn Scraper using Playwright

This module provides a web scraper for LinkedIn company pages using Playwright.
"""
from playwright.async_api import async_playwright
from typing import Optional, Dict, List, Any
import logging
from urllib.parse import urljoin, quote_plus
import asyncio

logger = logging.getLogger(__name__)

class LinkedInScraper:
    """Web scraper for LinkedIn company pages using Playwright."""
    
    BASE_URL = "https://www.linkedin.com"
    LOGIN_URL = "https://www.linkedin.com/login"
    
    def __init__(
        self,
        headless: bool = True,
        slow_mo: int = 100,
        timeout: int = 30000,
        user_agent: Optional[str] = None
    ):
        """Initialize the LinkedIn scraper.
        
        Args:
            headless: Whether to run in headless mode
            slow_mo: Delay between actions in milliseconds
            timeout: Default timeout in milliseconds
            user_agent: Custom user agent string
        """
        self.headless = headless
        self.slow_mo = slow_mo
        self.timeout = timeout
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        self.browser = None
        self.context = None
        self.page = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        try:
            await self.start()
            if not self.page:
                raise RuntimeError("Failed to initialize browser page")
            return self
        except Exception as e:
            await self.close()
            logger.error(f"Failed to initialize LinkedInScraper: {str(e)}")
            raise
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with proper resource cleanup."""
        try:
            await self.close()
        except Exception as e:
            logger.error(f"Error during LinkedInScraper cleanup: {str(e)}")
            # Don't suppress the original exception if there was one
            if exc_type is None:
                raise
    
    async def start(self):
        """Start the browser and create a new page."""
        logger.info("Starting Playwright browser...")
        try:
            # Initialize Playwright
            logger.debug("Initializing Playwright...")
            playwright = async_playwright()
            logger.debug("Got Playwright instance, starting...")
            self.playwright = await playwright.start()
            
            if not self.playwright:
                raise RuntimeError("Got None from playwright.start()")
                
            logger.info("Playwright started successfully")
            
            # Launch browser with options
            logger.debug(f"Launching {'headless' if self.headless else 'headed'} browser...")
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                slow_mo=self.slow_mo,
            )
            
            if not self.browser:
                raise RuntimeError("browser.launch() returned None")
                
            logger.info("Browser launched successfully")
            
            # Create a new browser context with custom options
            logger.debug("Creating browser context...")
            self.context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                locale="en-US",
                timezone_id="America/Los_Angeles",
                permissions=["geolocation"],
                ignore_https_errors=True,
                bypass_csp=True,
                java_script_enabled=True,
                has_touch=False,
                is_mobile=False,
                reduced_motion="reduce",
                color_scheme="light"
            )
            
            if not self.context:
                raise RuntimeError("browser.new_context() returned None")
                
            logger.info("Browser context created successfully")
            
            # Block resources to improve performance
            logger.debug("Setting up route handlers...")
            try:
                await self.context.route(
                    "**/*.{png,jpg,jpeg,webp,gif,svg,woff,woff2,eot,ttf,otf}", 
                    lambda route: route.abort()
                )
                logger.debug("Route handlers set up")
            except Exception as e:
                logger.warning(f"Failed to set up route handlers: {str(e)}")
                # Continue even if route setup fails
            
            # Create a new page
            logger.debug("Creating new page...")
            try:
                # Try to create a new page
                self.page = await self.context.new_page()
                logger.info(f"New page created: {self.page}")
                
                if not self.page:
                    raise RuntimeError("context.new_page() returned None")
                
                # Verify the page is usable
                if not hasattr(self.page, 'set_default_timeout'):
                    raise RuntimeError(f"Page object is missing required method 'set_default_timeout'")
                
                logger.info("New page created successfully")
                
                # Set default timeout - use a try/except to handle potential issues
                try:
                    logger.debug(f"Setting default timeout to {self.timeout}ms")
                    # Try a simple operation first to verify the page is usable
                    await self.page.evaluate('1+1')
                    
                    # Now set the timeout
                    await self.page.set_default_timeout(self.timeout)
                    logger.info("Default timeout set successfully")
                    
                except Exception as e:
                    logger.error(f"Failed to set default timeout: {str(e)}")
                    logger.error(f"Page object type: {type(self.page)}")
                    logger.error(f"Page object attributes: {[a for a in dir(self.page) if not a.startswith('_')]}")
                    
                    # Try to get more context about the page state
                    try:
                        url = await self.page.url
                        logger.error(f"Current page URL: {url}")
                    except Exception as url_error:
                        logger.error(f"Could not get page URL: {str(url_error)}")
                    
                    raise
                
            except Exception as page_error:
                logger.error(f"Failed to create new page: {str(page_error)}")
                
                # Log context and browser state for debugging
                if self.context:
                    logger.error(f"Context type: {type(self.context)}")
                    try:
                        pages = await self.context.pages()
                        logger.error(f"Context has {len(pages)} pages")
                    except Exception as e:
                        logger.error(f"Could not get pages from context: {str(e)}")
                
                if self.browser:
                    logger.error(f"Browser type: {type(self.browser)}")
                    try:
                        contexts = self.browser.contexts
                        logger.error(f"Browser has {len(contexts)} contexts")
                    except Exception as e:
                        logger.error(f"Could not get contexts from browser: {str(e)}")
                
                raise
            
            logger.info("Playwright browser and page initialized successfully")
            
        except Exception as e:
            error_msg = f"Failed to initialize Playwright: {str(e)}"
            logger.error(error_msg, exc_info=True)
            try:
                await self.close()
            except Exception as close_error:
                logger.error(f"Error during cleanup: {str(close_error)}")
            raise RuntimeError(error_msg) from e
    
    async def close(self):
        """Close the browser and release resources."""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()
    
    async def login(self, email: str, password: str) -> bool:
        """Log in to LinkedIn.
        
        Args:
            email: LinkedIn email
            password: LinkedIn password
            
        Returns:
            bool: True if login was successful, False otherwise
        """
        try:
            logger.info("Navigating to LinkedIn login page...")
            await self.page.goto(self.LOGIN_URL, wait_until='networkidle')
            
            # Wait for login form
            logger.info("Waiting for login form...")
            await self.page.wait_for_selector('#username', state='visible', timeout=10000)
            
            # Fill in credentials
            logger.info("Filling in credentials...")
            await self.page.fill('#username', email)
            await self.page.fill('#password', password)
            
            # Click login button
            logger.info("Submitting login form...")
            await self.page.click('button[type="submit"]')
            
            # Wait for navigation after login
            logger.info("Waiting for login to complete...")
            await self.page.wait_for_load_state('networkidle')
            
            # Check if login was successful
            if 'feed' in self.page.url or 'checkpoint' in self.page.url:
                logger.info("Successfully logged in to LinkedIn")
                return True
                
            # Check for 2FA requirement
            if 'checkpoint/challenge' in self.page.url:
                logger.warning("2FA verification required. Please complete manually.")
                # Wait for manual 2FA completion
                await self.page.wait_for_url('**/feed/**', timeout=300000)  # 5 minutes timeout
                return True
                
            logger.warning("Login may not have been successful")
            return False
            
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False
    
    async def get_company_info(self, company_name: str) -> Optional[Dict[str, Any]]:
        """
        Scrape company information from LinkedIn.
        
        Args:
            company_name: Name of the company to search for
            
        Returns:
            Dictionary containing company information or None if not found
        """
        try:
            # Search for the company
            search_url = f"{self.BASE_URL}/search/results/companies/?keywords={quote_plus(company_name)}"
            logger.info(f"Searching for company: {company_name}")
            await self.page.goto(search_url, wait_until='networkidle')
            
            # Wait for search results
            logger.info("Waiting for search results...")
            try:
                await self.page.wait_for_selector('.entity-result', timeout=10000)
            except Exception as e:
                logger.warning(f"No search results found for {company_name}")
                return None
            
            # Get the first result
            first_result = await self.page.query_selector('.entity-result:first-child')
            if not first_result:
                logger.warning(f"No results found for {company_name}")
                return None
                
            # Extract company URL
            company_link = await first_result.query_selector('a.app-aware-link')
            if not company_link:
                logger.warning(f"No company link found for {company_name}")
                return None
                
            company_url = await company_link.get_attribute('href')
            if not company_url or 'linkedin.com/company/' not in company_url:
                logger.warning(f"Invalid company URL: {company_url}")
                return None
                
            # Visit company page
            logger.info(f"Visiting company page: {company_url}")
            await self.page.goto(company_url, wait_until='networkidle')
            
            # Extract company information
            company_info = {
                'name': await self._extract_text('h1'),
                'headline': await self._extract_text('.org-top-card-summary__tagline'),
                'description': await self._extract_text('.org-about-us-organization-description__text'),
                'website': await self._extract_href('a[data-test-id="about-us-organization-link"]'),
                'company_size': await self._extract_text('dd:has-text("Company size") + dd'),
                'industry': await self._extract_text('dd:has-text("Industry") + dd'),
                'headquarters': await self._extract_text('dd:has-text("Headquarters") + dd'),
                'founded': await self._extract_text('dd:has-text("Founded") + dd'),
                'specialties': await self._extract_text('dd:has-text("Specialties") + dd'),
                'linkedin_url': company_url,
                'logo_url': await self._extract_src('.org-top-card-primary-content__logo'),
            }
            
            # Clean up the data
            company_info = {k: v.strip() if isinstance(v, str) else v 
                          for k, v in company_info.items() 
                          if v is not None and v != ''}
            
            logger.info(f"Successfully scraped company info for {company_name}")
            return company_info
            
        except Exception as e:
            logger.error(f"Error scraping company {company_name}: {e}")
            return None
    
    async def _extract_text(self, selector: str) -> Optional[str]:
        """Extract text from a selector if it exists."""
        try:
            element = await self.page.query_selector(selector)
            if element:
                text = await element.text_content()
                return text.strip() if text else None
        except Exception as e:
            logger.debug(f"Error extracting text with selector {selector}: {e}")
        return None
    
    async def _extract_href(self, selector: str) -> Optional[str]:
        """Extract href from a link selector if it exists."""
        try:
            element = await self.page.query_selector(selector)
            if element:
                return await element.get_attribute('href')
        except Exception as e:
            logger.debug(f"Error extracting href with selector {selector}: {e}")
        return None
    
    async def _extract_src(self, selector: str) -> Optional[str]:
        """Extract src from an image selector if it exists."""
        try:
            element = await self.page.query_selector(selector)
            if element:
                return await element.get_attribute('src')
        except Exception as e:
            logger.debug(f"Error extracting src with selector {selector}: {e}")
        return None
