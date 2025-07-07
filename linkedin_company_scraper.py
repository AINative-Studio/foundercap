"""
LinkedIn Company Scraper

This script scrapes detailed company information from LinkedIn company pages.
It handles login, verification, and extracts comprehensive company data.
"""

import os
import json
import time
import logging
import random
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('linkedin_scraper.log')
    ]
)
logger = logging.getLogger(__name__)

# Configuration
CONFIG = {
    'headless': os.getenv('LINKEDIN_HEADLESS', 'false').lower() == 'true',
    'slow_mo': int(os.getenv('LINKEDIN_SLOW_MO', '100')),  # milliseconds
    'timeout': 30000,  # milliseconds
    'screenshot_dir': 'screenshots',
    'data_dir': 'data',
    'user_agents': [
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    ],
    'wait_times': {
        'min': 2,
        'max': 5,
    },
}

# Ensure directories exist
for directory in [CONFIG['screenshot_dir'], CONFIG['data_dir']]:
    Path(directory).mkdir(exist_ok=True)

class LinkedInScraper:
    """A class to handle LinkedIn company scraping."""
    
    def __init__(self, email: str = None, password: str = None):
        """Initialize the scraper with credentials."""
        self.email = email or os.getenv('LINKEDIN_EMAIL')
        self.password = password or os.getenv('LINKEDIN_PASSWORD')
        
        if not self.email or not self.password:
            raise ValueError("LinkedIn email and password must be provided")
        
        self.playwright = sync_playwright().start()
        self.browser = None
        self.context = None
        self.page = None
        self.session_id = f"session_{int(time.time())}"
        
        # Set a random user agent
        self.user_agent = random.choice(CONFIG['user_agents'])
        
        logger.info(f"Initialized LinkedInScraper with session ID: {self.session_id}")
    
    def random_delay(self, min_seconds: float = None, max_seconds: float = None) -> None:
        """Wait for a random amount of time to mimic human behavior."""
        min_seconds = min_seconds or CONFIG['wait_times']['min']
        max_seconds = max_seconds or CONFIG['wait_times']['max']
        time.sleep(random.uniform(min_seconds, max_seconds))
    
    def take_screenshot(self, name: str) -> str:
        """Take a screenshot and save it to the screenshots directory."""
        filename = f"{self.session_id}_{int(time.time())}_{name}.png"
        path = os.path.join(CONFIG['screenshot_dir'], filename)
        self.page.screenshot(path=path)
        logger.info(f"Screenshot saved to {path}")
        return path
    
    def save_data(self, data: Dict, filename: str = None) -> str:
        """Save scraped data to a JSON file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"company_data_{timestamp}.json"
        
        path = os.path.join(CONFIG['data_dir'], filename)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Data saved to {path}")
        return path
    
    def setup_browser(self):
        """Set up the browser with appropriate options."""
        logger.info("Launching browser...")
        
        self.browser = self.playwright.chromium.launch(
            headless=CONFIG['headless'],
            slow_mo=CONFIG['slow_mo']
        )
        
        # Create a new browser context with a random viewport
        self.context = self.browser.new_context(
            viewport={
                'width': random.randint(1200, 1920),
                'height': random.randint(800, 1080),
            },
            user_agent=self.user_agent,
            locale='en-US',
            timezone_id='America/Los_Angeles',
            permissions=['geolocation'],
            ignore_https_errors=True,
            java_script_enabled=True,
            has_touch=False,
            is_mobile=False,
            color_scheme='light',
            reduced_motion='reduce',
            record_har_path=None,
            record_video_dir=None,
            record_video_size=None,
            proxy=None,
            http_credentials=None,
            device_scale_factor=1,
            offline=False,
            accept_downloads=True,
            no_viewport=False,
            bypass_csp=False,
            storage_state=None,
            screen={
                'width': 1920,
                'height': 1080,
            },
            service_workers='allow',
        )
        
        # Set default timeout
        self.context.set_default_timeout(CONFIG['timeout'])
        
        # Create a new page
        self.page = self.context.new_page()
        
        # Set extra HTTP headers
        self.page.set_extra_http_headers({
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Referer': 'https://www.google.com/',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'TE': 'Trailers',
        })
        
        # Add stealth mode
        self.page.add_init_script("""
        // Overwrite the `languages` property to use a custom getter.
        Object.defineProperty(navigator, 'languages', {
            get: function() {
                return ['en-US', 'en'];
            },
        });
        
        // Overwrite the `plugins` property to use a custom getter.
        Object.defineProperty(navigator, 'plugins', {
            get: function() {
                return [1, 2, 3, 4, 5];
            },
        });
        
        // Overwrite the `webdriver` property to make it undefined
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
        
        // Overwrite the `chrome` property to make it undefined
        window.chrome = {
            runtime: {},
        };
        
        // Set permissions to simulate a real browser
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        """)
        
        logger.info("Browser setup complete")
    
    def login(self) -> bool:
        """Log in to LinkedIn."""
        logger.info("Starting LinkedIn login process...")
        
        try:
            # Navigate to LinkedIn homepage
            self.page.goto('https://www.linkedin.com', timeout=60000)
            self.random_delay(2, 4)
            
            # Click sign in button if it exists
            sign_in_button = self.page.query_selector('a[data-tracking-control-name="guest_homepage-basic_nav-header-signin"]')
            if sign_in_button:
                sign_in_button.click()
                self.random_delay(1, 2)
            
            # Fill email
            email_field = self.page.query_selector('#username')
            if not email_field:
                logger.error("Email field not found")
                self.take_screenshot("login_email_field_not_found")
                return False
                
            # Type email with random delays between keystrokes
            email_field.click()
            for char in self.email:
                email_field.press(char)
                time.sleep(random.uniform(0.05, 0.2))
            
            self.random_delay(1, 2)
            
            # Fill password
            password_field = self.page.query_selector('#password')
            if not password_field:
                logger.error("Password field not found")
                self.take_screenshot("login_password_field_not_found")
                return False
                
            # Type password with random delays between keystrokes
            password_field.click()
            for char in self.password:
                password_field.press(char)
                time.sleep(random.uniform(0.05, 0.2))
            
            self.random_delay(1, 2)
            
            # Submit the form by pressing Enter
            password_field.press('Enter')
            
            # Wait for login to complete
            logger.info("Waiting for login to complete...")
            logger.info("PLEASE CHECK YOUR LINKEDIN APP TO COMPLETE VERIFICATION")
            logger.info("You have 3 minutes to complete the verification...")
            
            verification_complete = False
            for attempt in range(18):  # 18 * 10 seconds = 3 minutes
                try:
                    # Check for successful login (search box or home feed)
                    search_box = self.page.query_selector('input[role="combobox"][aria-label="Search"], [data-test-id="nav-search-bar"]')
                    home_feed = self.page.query_selector('div.feed-identity-module')
                    
                    if search_box or home_feed:
                        verification_complete = True
                        logger.info("Login verification successful!")
                        break
                        
                    # Check for verification prompts
                    verification_prompt = self.page.query_selector('div.challenge-dialog__container, #input__email_verification_pin, #input__phone_verification')
                    if verification_prompt:
                        logger.info("Verification prompt detected. Please complete verification in the browser...")
                        self.take_screenshot(f"verification_prompt_{attempt}")
                    
                    # Check for any error messages
                    error_message = self.page.query_selector('.error-for-username, .error-for-password, .error-for-.*')
                    if error_message:
                        error_text = error_message.inner_text().strip()
                        logger.error(f"Login error: {error_text}")
                        self.take_screenshot("login_error")
                        return False
                        
                    # Take a screenshot every 20 seconds
                    if attempt % 2 == 0:
                        self.take_screenshot(f"verification_wait_{attempt//2}")
                        logger.info(f"Waiting for verification... {attempt * 10} seconds passed")
                        
                    # Wait before next check
                    time.sleep(10)
                        
                except Exception as e:
                    logger.error(f"Error during verification: {e}")
                    self.take_screenshot(f"verification_error_{attempt}")
                    time.sleep(10)  # Wait before retry
            
            if not verification_complete:
                logger.warning("Verification not completed within 3 minutes")
                self.take_screenshot("verification_timeout")
                
                # Check if we're on a different page than expected
                current_url = self.page.url
                if "challenge" in current_url or "login-submit" in current_url:
                    logger.warning("Appears to be stuck on a verification page")
                
                # Try to proceed anyway, might be on a different page structure
                logger.info("Attempting to proceed with scraping...")
            
            logger.info("Login successful")
            self.take_screenshot("login_success")
            return True
            
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            self.take_screenshot("login_failed")
            return False
    
    def extract_company_info(self, company_url: str) -> Dict[str, Any]:
        """Extract company information from LinkedIn company page."""
        logger.info(f"Extracting company info from: {company_url}")
        
        try:
            # Navigate to company page
            self.page.goto(company_url, timeout=60000)
            self.random_delay(3, 5)
            
            # Take a screenshot of the page
            self.take_screenshot("company_page")
            
            # Initialize company info dictionary
            company_info = {
                'url': company_url,
                'scraped_at': datetime.utcnow().isoformat(),
                'source': 'linkedin',
            }
            
            # Extract basic info
            self.extract_basic_info(company_info)
            
            # Extract about section
            self.extract_about_section(company_info)
            
            # Extract overview section
            self.extract_overview_section(company_info)
            
            # Extract jobs section if available
            self.extract_jobs_section(company_info)
            
            # Extract people section if available
            self.extract_people_section(company_info)
            
            # Extract posts section if available
            self.extract_posts_section(company_info)
            
            logger.info("Company info extracted successfully")
            return company_info
            
        except Exception as e:
            logger.error(f"Error extracting company info: {str(e)}")
            self.take_screenshot("extraction_error")
            raise
    
    def extract_basic_info(self, company_info: Dict[str, Any]) -> None:
        """Extract basic company information."""
        # Get company name
        name_element = self.page.query_selector('h1.org-top-card-logo__title, h1.org-top-card-primary-content__title')
        if name_element:
            company_info['name'] = name_element.inner_text().strip()
        
        # Get company tagline
        tagline_element = self.page.query_selector('p.org-top-card-tagline, p.tagline')
        if tagline_element:
            company_info['tagline'] = tagline_element.inner_text().strip()
        
        # Get company description
        description_element = self.page.query_selector('p.break-words, p.about-us-details, div.about-us-details p')
        if description_element:
            company_info['description'] = description_element.inner_text().strip()
        
        # Get company website
        website_element = self.page.query_selector('a[data-tracking-control-name="about_website"], a.website')
        if website_element:
            company_info['website'] = website_element.get_attribute('href')
        
        # Get company logo URL
        logo_element = self.page.query_selector('img.org-top-card-primary-content__logo, img.org-top-card-logo__image')
        if logo_element:
            company_info['logo_url'] = logo_element.get_attribute('src')
        
        # Get company banner image URL
        banner_element = self.page.query_selector('img.org-top-card-banner__image')
        if banner_element:
            company_info['banner_url'] = banner_element.get_attribute('src')
    
    def extract_about_section(self, company_info: Dict[str, Any]) -> None:
        """Extract information from the About section."""
        about_section = {}
        
        # Click on the About tab if it exists
        about_tab = self.page.query_selector('a[data-control-name="page_member_main_nav_about_tab"]')
        if about_tab:
            about_tab.click()
            self.random_delay(2, 4)
            
            # Extract overview information
            overview_items = self.page.query_selector_all('section.artdeco-card.org-page-details')
            for item in overview_items:
                try:
                    title_element = item.query_selector('h2')
                    if not title_element:
                        continue
                        
                    title = title_element.inner_text().strip().lower()
                    
                    # Handle different section types
                    if 'overview' in title:
                        # Extract key-value pairs
                        items = item.query_selector_all('dl')
                        for dl in items:
                            key_elements = dl.query_selector_all('dt')
                            value_elements = dl.query_selector_all('dd')
                            
                            for key_el, value_el in zip(key_elements, value_elements):
                                key = key_el.inner_text().strip().lower()
                                value = value_el.inner_text().strip()
                                about_section[key] = value
                    
                    elif 'description' in title or 'about' in title:
                        # Get description text
                        desc = item.query_selector('p, div')
                        if desc:
                            about_section['detailed_description'] = desc.inner_text().strip()
                    
                    elif 'website' in title or 'links' in title:
                        # Get website links
                        links = item.query_selector_all('a')
                        if links:
                            about_section['websites'] = [{
                                'url': link.get_attribute('href'),
                                'label': link.inner_text().strip()
                            } for link in links]
                    
                    else:
                        # Generic section handling
                        content = item.inner_text().strip()
                        about_section[title] = content
                        
                except Exception as e:
                    logger.debug(f"Error parsing about section item: {e}")
        
        if about_section:
            company_info['about'] = about_section
    
    def extract_overview_section(self, company_info: Dict[str, Any]) -> None:
        """Extract information from the Overview section."""
        overview_section = {}
        
        # Get company size
        size_element = self.page.query_selector('div.org-about-company-module__company-size-definition-text')
        if not size_element:
            size_element = self.page.query_selector('dt:has-text("Company size") + dd')
            if not size_element:
                size_element = self.page.query_selector('dt:has-text("Size") + dd')
        
        if size_element:
            overview_section['company_size'] = size_element.inner_text().strip()
        
        # Get industry
        industry_element = self.page.query_selector('div.org-about-company-module__company-industries')
        if not industry_element:
            industry_element = self.page.query_selector('dt:has-text("Industry") + dd')
            if not industry_element:
                industry_element = self.page.query_selector('dt:has-text("Industries") + dd')
        
        if industry_element:
            overview_section['industry'] = industry_element.inner_text().strip()
        
        # Get headquarters
        hq_element = self.page.query_selector('div.org-about-company-module__headquarters')
        if not hq_element:
            hq_element = self.page.query_selector('dt:has-text("Headquarters") + dd')
            if not hq_element:
                hq_element = self.page.query_selector('dt:has-text("Location") + dd')
        
        if hq_element:
            overview_section['headquarters'] = hq_element.inner_text().strip()
        
        # Get specialties
        specialties_elements = self.page.query_selector_all('.org-about-company-module__specialities, .specialties')
        if specialties_elements:
            overview_section['specialties'] = [el.inner_text().strip() for el in specialties_elements]
        
        # Get founded year
        founded_element = self.page.query_selector('div.org-about-company-module__founded')
        if not founded_element:
            founded_element = self.page.query_selector('dt:has-text("Founded") + dd')
            if not founded_element:
                founded_element = self.page.query_selector('dt:has-text("Year founded") + dd')
        
        if founded_element:
            overview_section['founded'] = founded_element.inner_text().replace('Founded', '').strip()
        
        # Get company type
        type_element = self.page.query_selector('div.org-about-company-module__company-type')
        if not type_element:
            type_element = self.page.query_selector('dt:has-text("Type") + dd')
            if not type_element:
                type_element = self.page.query_selector('dt:has-text("Company type") + dd')
        
        if type_element:
            overview_section['company_type'] = type_element.inner_text().strip()
        
        if overview_section:
            company_info['overview'] = overview_section
    
    def extract_jobs_section(self, company_info: Dict[str, Any]) -> None:
        """Extract information from the Jobs section."""
        jobs_section = {}
        
        # Click on the Jobs tab if it exists
        jobs_tab = self.page.query_selector('a[data-control-name="page_member_main_nav_jobs_tab"]')
        if jobs_tab:
            try:
                jobs_tab.click()
                self.random_delay(2, 4)
                
                # Get number of job postings
                job_count_element = self.page.query_selector('h3.jobs-search-results-list__title')
                if job_count_element:
                    jobs_section['total_jobs'] = job_count_element.inner_text().strip()
                
                # Get job listings (first page)
                job_elements = self.page.query_selector_all('li.jobs-search-results__list-item')
                if job_elements:
                    jobs = []
                    for job_el in job_elements[:5]:  # Limit to first 5 jobs
                        try:
                            job = {}
                            
                            # Get job title
                            title_el = job_el.query_selector('h3')
                            if title_el:
                                job['title'] = title_el.inner_text().strip()
                            
                            # Get company name
                            company_el = job_el.query_selector('h4')
                            if company_el:
                                job['company'] = company_el.inner_text().strip()
                            
                            # Get location
                            location_el = job_el.query_selector('span.job-search-card__location')
                            if location_el:
                                job['location'] = location_el.inner_text().strip()
                            
                            # Get posted time
                            time_el = job_el.query_selector('time')
                            if time_el:
                                job['posted'] = time_el.get_attribute('datetime') or time_el.inner_text().strip()
                            
                            # Get job URL
                            link_el = job_el.query_selector('a')
                            if link_el:
                                job['url'] = link_el.get_attribute('href')
                            
                            if job:
                                jobs.append(job)
                                
                        except Exception as e:
                            logger.debug(f"Error parsing job listing: {e}")
                    
                    if jobs:
                        jobs_section['jobs'] = jobs
                
            except Exception as e:
                logger.debug(f"Error extracting jobs section: {e}")
        
        if jobs_section:
            company_info['jobs'] = jobs_section
    
    def extract_people_section(self, company_info: Dict[str, Any]) -> None:
        """Extract information from the People section."""
        people_section = {}
        
        # Click on the People tab if it exists
        people_tab = self.page.query_selector('a[data-control-name="page_member_main_nav_people_tab"]')
        if people_tab:
            try:
                people_tab.click()
                self.random_delay(2, 4)
                
                # Get total number of employees
                employee_count_element = self.page.query_selector('h3.org-people__headline')
                if employee_count_element:
                    people_section['total_employees'] = employee_count_element.inner_text().strip()
                
                # Get employee list (first page)
                employee_elements = self.page.query_selector_all('li.org-people-profile-card__profile-card')
                if employee_elements:
                    employees = []
                    for emp_el in employee_elements[:5]:  # Limit to first 5 employees
                        try:
                            employee = {}
                            
                            # Get name
                            name_el = emp_el.query_selector('h3')
                            if name_el:
                                employee['name'] = name_el.inner_text().strip()
                            
                            # Get title
                            title_el = emp_el.query_selector('p.org-people-profile-card__people-item-tagline')
                            if title_el:
                                employee['title'] = title_el.inner_text().strip()
                            
                            # Get profile URL
                            link_el = emp_el.query_selector('a')
                            if link_el:
                                employee['profile_url'] = link_el.get_attribute('href')
                            
                            # Get image URL
                            img_el = emp_el.query_selector('img')
                            if img_el:
                                employee['image_url'] = img_el.get_attribute('src')
                            
                            if employee:
                                employees.append(employee)
                                
                        except Exception as e:
                            logger.debug(f"Error parsing employee: {e}")
                    
                    if employees:
                        people_section['employees'] = employees
                
            except Exception as e:
                logger.debug(f"Error extracting people section: {e}")
        
        if people_section:
            company_info['people'] = people_section
    
    def extract_posts_section(self, company_info: Dict[str, Any]) -> None:
        """Extract information from the Posts section."""
        posts_section = {}
        
        # Click on the Posts tab if it exists
        posts_tab = self.page.query_selector('a[data-control-name="page_member_main_nav_posts_tab"]')
        if not posts_tab:
            return
            
        try:
            posts_tab.click()
            self.random_delay(2, 4)
            
            # Get posts (first few)
            post_elements = self.page.query_selector_all('div.feed-shared-update-v2')
            if post_elements:
                posts = []
                for post_el in post_elements[:3]:  # Limit to first 3 posts
                    try:
                        post = {}
                        
                        # Get post text
                        text_el = post_el.query_selector('div.feed-shared-update-v2__description')
                        if text_el:
                            post['text'] = text_el.inner_text().strip()
                        
                        # Get post time
                        time_el = post_el.query_selector('span.visually-hidden')
                        if time_el:
                            post['time'] = time_el.inner_text().strip()
                        
                        # Get number of reactions
                        reactions_el = post_el.query_selector('span.social-details-social-counts__reactions')
                        if reactions_el:
                            post['reactions'] = reactions_el.inner_text().strip()
                        
                        # Get number of comments
                        comments_el = post_el.query_selector('span.social-details-social-counts__comments')
                        if comments_el:
                            post['comments'] = comments_el.inner_text().strip()
                        
                        if post:
                            posts.append(post)
                            
                    except Exception as e:
                        logger.debug(f"Error parsing post: {e}")
                
                if posts:
                    posts_section['recent_posts'] = posts
            
        except Exception as e:
            logger.debug(f"Error extracting posts section: {e}")
        
        if posts_section:
            company_info['posts'] = posts_section
    
    def close(self):
        """Close the browser and release resources."""
        logger.info("Closing browser...")
        if self.browser:
            self.browser.close()
        self.playwright.stop()
        logger.info("Browser closed")


def main():
    """Main function to run the LinkedIn scraper."""
    # Load environment variables
    load_dotenv()
    
    # Initialize scraper
    scraper = LinkedInScraper()
    
    try:
        # Setup browser
        scraper.setup_browser()
        
        # Login
        if not scraper.login():
            logger.error("Login failed")
            return
        
        # List of company URLs to scrape
        company_urls = [
            'https://www.linkedin.com/company/google/about/',
            # Add more company URLs here
        ]
        
        # Scrape each company
        for url in company_urls:
            try:
                logger.info(f"Scraping company: {url}")
                company_info = scraper.extract_company_info(url)
                
                # Save the data
                if company_info:
                    filename = f"{company_info.get('name', 'company').lower().replace(' ', '_')}_{int(time.time())}.json"
                    scraper.save_data(company_info, filename)
                    
                    # Print summary
                    print("\n" + "="*50)
                    print(f"COMPANY: {company_info.get('name', 'N/A')}")
                    print("="*50)
                    print(f"Industry: {company_info.get('overview', {}).get('industry', 'N/A')}")
                    print(f"Size: {company_info.get('overview', {}).get('company_size', 'N/A')}")
                    print(f"Headquarters: {company_info.get('overview', {}).get('headquarters', 'N/A')}")
                    print(f"Website: {company_info.get('website', 'N/A')}")
                    print(f"Description: {company_info.get('description', 'N/A')[:200]}..." if company_info.get('description') else "No description")
                    print("="*50 + "\n")
                
            except Exception as e:
                logger.error(f"Error scraping {url}: {str(e)}")
                scraper.take_screenshot(f"error_{url.split('/')[-2]}")
    
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        scraper.take_screenshot("fatal_error")
    
    finally:
        # Close the browser
        scraper.close()


if __name__ == "__main__":
    main()
