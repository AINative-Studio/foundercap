#!/usr/bin/env python3
"""
Direct test of the LinkedIn scraper using synchronous Playwright.

This script tests the LinkedIn scraper directly without the service layer.
"""
import logging
import os
import json
import sys
import time
from datetime import datetime
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # More verbose logging for debugging
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_linkedin_scraper():
    """Test the LinkedIn scraper using synchronous Playwright."""
    logger.info("Starting LinkedIn scraper test...")
    
    # Configure scraper
    headless = os.getenv("LINKEDIN_HEADLESS", "true").lower() == "true"
    slow_mo = int(os.getenv("LINKEDIN_SLOW_MO", "100"))
    timeout = int(os.getenv("LINKEDIN_TIMEOUT", "30000"))
    
    logger.info(f"Scraper configuration - headless: {headless}, slow_mo: {slow_mo}, timeout: {timeout}")
    
    with sync_playwright() as p:
        try:
            # Launch browser
            logger.info("Launching browser...")
            browser = p.chromium.launch(headless=headless, slow_mo=slow_mo)
            
            # Create a new browser context
            logger.info("Creating browser context...")
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                locale="en-US"
            )
            
            # Create a new page
            logger.info("Creating new page...")
            page = context.new_page()
            page.set_default_timeout(timeout)
            
            # Test navigation
            logger.info("Navigating to Google...")
            page.goto("https://www.google.com")
            logger.info(f"Page title: {page.title()}")
            
            # Take a screenshot
            screenshot_path = "test_screenshot.png"
            page.screenshot(path=screenshot_path)
            logger.info(f"Screenshot saved to {screenshot_path}")
            
            # First, navigate to LinkedIn's homepage to ensure we're on the right domain
            logger.info("Navigating to LinkedIn homepage...")
            page.goto("https://www.linkedin.com", timeout=30000)
            
            # Check if we're on the login page or if we need to click 'Sign In'
            login_form = page.query_selector('form[action*="login"]')
            sign_in_button = page.query_selector('a[data-tracking-control-name="guest_homepage-basic_nav-header-signin"]')
            
            if sign_in_button:
                logger.info("Clicking sign in button...")
                sign_in_button.click()
                page.wait_for_selector('input[name="session_key"], input[name="username"]', timeout=10000)
            
            # Fill in login form with debug info and slower interactions
            logger.info("Attempting to log in...")
            email = "toby@luvmart.co"
            password = "Ellamae2015!"
            
            try:
                # Take a screenshot before filling the form
                page.screenshot(path="before_login.png")
                
                # Wait for and fill email field with delay
                logger.info("Filling email...")
                email_field = page.wait_for_selector('input[name="session_key"], input[name="username"]', timeout=10000)
                for char in email:
                    email_field.press(char)
                    page.wait_for_timeout(100)  # 100ms delay between key presses
                
                # Add a small delay before password
                page.wait_for_timeout(1000)
                
                # Fill password field with delay
                logger.info("Filling password...")
                password_field = page.wait_for_selector('input[name="session_password"], input[name="password"]', timeout=5000)
                for char in password:
                    password_field.press(char)
                    page.wait_for_timeout(100)  # 100ms delay between key presses
                
                # Add a small delay before submitting
                page.wait_for_timeout(2000)  # 2 second delay
                
                # Submit using Enter key
                logger.info("Pressing Enter to submit login form...")
                page.keyboard.press("Enter")
                
                # Wait for either the home feed or a security challenge
                logger.info("Waiting for login to complete...")
                logger.info("PLEASE CHECK YOUR LINKEDIN APP TO COMPLETE VERIFICATION")
                logger.info("You have 3 minutes to complete the verification...")
                
                try:
                    # Wait for verification to complete (up to 3 minutes)
                    verification_complete = False
                    for attempt in range(18):  # 18 * 10 seconds = 3 minutes
                        try:
                            # Check for successful login (search box or home feed)
                            search_box = page.query_selector('input[role="combobox"][aria-label="Search"], [data-test-id="nav-search-bar"]')
                            home_feed = page.query_selector('div.feed-identity-module')
                            
                            if search_box or home_feed:
                                verification_complete = True
                                logger.info("Login verification successful!")
                                break
                                
                            # Check for verification prompts
                            verification_prompt = page.query_selector('div.challenge-dialog__container, #input__email_verification_pin, #input__phone_verification')
                            if verification_prompt:
                                logger.info("Verification prompt detected. Please complete verification in the browser...")
                                page.screenshot(path=f"verification_prompt_{attempt}.png")
                            
                            # Check for any error messages
                            error_message = page.query_selector('.error-for-username, .error-for-password, .error-for-.*')
                            if error_message:
                                error_text = error_message.inner_text().strip()
                                logger.error(f"Login error: {error_text}")
                                page.screenshot(path="login_error.png")
                                return
                                
                            # Take a screenshot every 10 seconds
                            if attempt % 2 == 0:  # Every 20 seconds
                                page.screenshot(path=f"verification_wait_{attempt//2}.png")
                                logger.info(f"Waiting for verification... {attempt * 10} seconds passed")
                                
                            # Wait before next check
                            page.wait_for_timeout(10000)  # 10 seconds
                                
                        except Exception as e:
                            logger.error(f"Error during verification: {e}")
                            page.screenshot(path=f"verification_error_{attempt}.png")
                            page.wait_for_timeout(10000)  # 10 seconds before retry
                
                    if not verification_complete:
                        logger.warning("Verification not completed within 3 minutes")
                        page.screenshot(path="verification_timeout.png")
                        logger.info("Screenshot saved to verification_timeout.png")
                        
                        # Check if we're on a different page than expected
                        current_url = page.url
                        if "challenge" in current_url or "login-submit" in current_url:
                            logger.warning("Appears to be stuck on a verification page")
                        
                        # Try to proceed anyway, might be on a different page structure
                        logger.info("Attempting to proceed with scraping...")
                            
                    logger.info("Login successful")
                    page.screenshot(path="login_success.png")
                    
                except Exception as e:
                    logger.error(f"Login verification failed: {e}")
                    page.screenshot(path="login_verification_failed.png")
                    logger.info("Screenshot saved to login_verification_failed.png")
                    return
                
            except Exception as e:
                logger.error(f"Error during login form submission: {e}")
                page.screenshot(path="login_form_error.png")
                logger.info("Screenshot saved to login_form_error.png")
                return
            
            # Now proceed with company search
            company_name = "google"  # Using lowercase for URL
            logger.info(f"Searching for company: {company_name}")
            
            try:
                # Navigate to company page
                company_url = f"https://www.linkedin.com/company/{company_name}/about/"
                logger.info(f"Navigating to: {company_url}")
                page.goto(company_url, timeout=60000)  # 60 second timeout
                
                # Wait for the company page to load
                try:
                    # Wait for the main content to load
                    page.wait_for_selector('.org-top-card, [data-test-id="about-us"], .error-container', timeout=15000)
                    
                    # Check if we got a 404 or error page
                    error_element = page.query_selector('.error-container, .error-code, .error-content')
                    if error_element:
                        error_text = error_element.inner_text()
                        logger.error(f"Error page encountered: {error_text}")
                        return
                    
                    # Initialize company info dictionary
                    company_info = {}
                    
                    # Get company name
                    name_element = page.query_selector('h1.org-top-card-logo__title, h1.org-top-card-primary-content__title')
                    if name_element:
                        company_info['name'] = name_element.inner_text().strip()
                    
                    # Get company tagline
                    tagline_element = page.query_selector('p.org-top-card-tagline, p.tagline')
                    if tagline_element:
                        company_info['tagline'] = tagline_element.inner_text().strip()
                    
                    # Get company description (try multiple possible selectors)
                    description_element = page.query_selector('p.break-words, p.about-us-details, div.about-us-details p')
                    if description_element:
                        company_info['description'] = description_element.inner_text().strip()
                    
                    # Get company website
                    website_element = page.query_selector('a[data-tracking-control-name="about_website"], a.website')
                    if website_element:
                        company_info['website'] = website_element.get_attribute('href')
                    
                    # Get company size
                    size_element = page.query_selector('div.org-about-company-module__company-size-definition-text')
                    if not size_element:
                        # Try alternative selectors for size
                        size_element = page.query_selector('dt:has-text("Company size") + dd')
                        if not size_element:
                            size_element = page.query_selector('dt:has-text("Size") + dd')
                    
                    if size_element:
                        company_info['company_size'] = size_element.inner_text().strip()
                    
                    # Get industry
                    industry_element = page.query_selector('div.org-about-company-module__company-industries')
                    if not industry_element:
                        industry_element = page.query_selector('dt:has-text("Industry") + dd')
                        if not industry_element:
                            industry_element = page.query_selector('dt:has-text("Industries") + dd')
                    
                    if industry_element:
                        company_info['industry'] = industry_element.inner_text().strip()
                    
                    # Get headquarters
                    hq_element = page.query_selector('div.org-about-company-module__headquarters')
                    if not hq_element:
                        hq_element = page.query_selector('dt:has-text("Headquarters") + dd')
                        if not hq_element:
                            hq_element = page.query_selector('dt:has-text("Location") + dd')
                    
                    if hq_element:
                        company_info['headquarters'] = hq_element.inner_text().strip()
                    
                    # Get specialties
                    specialties_elements = page.query_selector_all('.org-about-company-module__specialities, .specialties')
                    if specialties_elements:
                        company_info['specialties'] = [el.inner_text().strip() for el in specialties_elements]
                    
                    # Get founded year
                    founded_element = page.query_selector('div.org-about-company-module__founded')
                    if not founded_element:
                        founded_element = page.query_selector('dt:has-text("Founded") + dd')
                        if not founded_element:
                            founded_element = page.query_selector('dt:has-text("Year founded") + dd')
                    
                    if founded_element:
                        company_info['founded'] = founded_element.inner_text().replace('Founded', '').strip()
                    
                    # Get company type
                    type_element = page.query_selector('div.org-about-company-module__company-type')
                    if not type_element:
                        type_element = page.query_selector('dt:has-text("Type") + dd')
                        if not type_element:
                            type_element = page.query_selector('dt:has-text("Company type") + dd')
                    
                    if type_element:
                        company_info['company_type'] = type_element.inner_text().strip()
                    
                    # Get all "About" section data
                    about_section = {}
                    about_sections = page.query_selector_all('section.artdeco-card.org-page-details')
                    
                    for section in about_sections:
                        try:
                            section_title = section.query_selector('h2')
                            if section_title:
                                section_title = section_title.inner_text().strip().lower()
                                
                                # Handle different section types
                                if 'overview' in section_title:
                                    # Get key-value pairs
                                    items = section.query_selector_all('dl')
                                    for item in items:
                                        key = item.query_selector('dt')
                                        value = item.query_selector('dd')
                                        if key and value:
                                            about_section[key.inner_text().strip().lower()] = value.inner_text().strip()
                                
                                elif 'description' in section_title:
                                    # Get description text
                                    desc = section.query_selector('p, div')
                                    if desc:
                                        about_section['detailed_description'] = desc.inner_text().strip()
                                
                                elif 'website' in section_title:
                                    # Get website links
                                    links = section.query_selector_all('a')
                                    if links:
                                        about_section['websites'] = [{
                                            'url': link.get_attribute('href'),
                                            'label': link.inner_text().strip()
                                        } for link in links]
                                
                                else:
                                    # Generic section handling
                                    content = section.inner_text().strip()
                                    about_section[section_title] = content
                                    
                        except Exception as e:
                            logger.debug(f"Error parsing section: {e}")
                    
                    if about_section:
                        company_info['about'] = about_section
                    
                    # Get employee count on LinkedIn
                    employee_count = page.query_selector('a[href*="employeeCount"]')
                    if employee_count:
                        company_info['linkedin_employee_count'] = employee_count.inner_text().strip()
                    
                    # Get company logo URL
                    logo_element = page.query_selector('img.org-top-card-primary-content__logo, img.org-top-card-logo__image')
                    if logo_element:
                        company_info['logo_url'] = logo_element.get_attribute('src')
                    
                    # Get company banner image URL
                    banner_element = page.query_selector('img.org-top-card-banner__image')
                    if banner_element:
                        company_info['banner_url'] = banner_element.get_attribute('src')
                    
                    # Save the extracted data to a JSON file
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_file = f"company_data_{timestamp}.json"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(company_info, f, indent=2, ensure_ascii=False)
                    
                    logger.info("Company info extracted successfully")
                    logger.info(f"Data saved to {output_file}")
                    
                    # Print the extracted data
                    print("\n" + "="*50)
                    print("EXTRACTED COMPANY INFORMATION:")
                    print("="*50)
                    for key, value in company_info.items():
                        if isinstance(value, (str, int, float, bool)) or value is None:
                            print(f"{key.upper()}: {value}")
                        elif isinstance(value, list):
                            print(f"{key.upper()}: {', '.join(map(str, value))}")
                        elif isinstance(value, dict):
                            print(f"\n{key.upper()}:")
                            for k, v in value.items():
                                print(f"  {k}: {v}")
                    print("="*50 + "\n")
                    
                    logger.info(f"Company info: {company_info}")
                    
                    # Get employee count
                    employee_element = page.query_selector('div.org-about-company-module__company-size-definition-text')
                    if employee_element:
                        company_info["employees"] = employee_element.inner_text().strip()
                    
                    # Get company description
                    desc_element = page.query_selector('section[data-test-id="about-us"], .about-us__description')
                    if desc_element:
                        company_info["description"] = desc_element.inner_text().strip()
                    
                    logger.info(f"Company info: {company_info}")
                    
                    # Take a screenshot of the company page
                    page.screenshot(path="company_page.png")
                    logger.info("Screenshot saved to company_page.png")
                    
                except Exception as e:
                    logger.error(f"Error extracting company info: {e}")
                    page.screenshot(path="extraction_error.png")
                    logger.info("Screenshot saved to extraction_error.png")
                    raise
                
            except Exception as e:
                logger.error(f"Error navigating to company page: {e}")
                page.screenshot(path="navigation_error.png")
                logger.info("Screenshot saved to navigation_error.png")
                raise
            
            logger.info("Tests completed successfully")
            
        except Exception as e:
            logger.error(f"Test failed with error: {e}", exc_info=True)
            raise
            
        finally:
            # Close browser
            if 'browser' in locals():
                logger.info("Closing browser...")
                browser.close()

if __name__ == "__main__":
    try:
        logger.info("Starting LinkedIn scraper test script")
        test_linkedin_scraper()
    except Exception as e:
        logger.critical(f"Test script failed: {e}", exc_info=True)
        sys.exit(1)
