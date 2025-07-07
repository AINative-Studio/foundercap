# LinkedIn Service

This service provides functionality to scrape and interact with LinkedIn data using Playwright.

## Features

- Company information lookup by name
- Caching of responses to reduce API calls
- Rate limiting and error handling
- Support for both logged-in and anonymous scraping
- Headless browser automation

## Requirements

- Python 3.8+
- Playwright
- Redis (for caching)

## Installation

1. Install the required dependencies:

```bash
pip install playwright httpx redis
playwright install
```

2. Configure your environment variables (see `.env.example` for reference):

```bash
# LinkedIn credentials (required for full access)
LINKEDIN_EMAIL=your-email@example.com
LINKEDIN_PASSWORD=your-password

# LinkedIn scraper settings
LINKEDIN_HEADLESS=True
LINKEDIN_SKIP_LOGIN=False
LINKEDIN_TIMEOUT=30000
LINKEDIN_SLOW_MO=100
LINKEDIN_CACHE_TTL=86400

# Redis settings
REDIS_HOST=localhost
REDIS_PORT=6379
```

## Usage

### Basic Usage

```python
from app.services.linkedin import LinkedInService
import asyncio

async def main():
    async with LinkedInService() as service:
        # Get company information
        company_info = await service.get_company_info("Google")
        print(company_info)

if __name__ == "__main__":
    asyncio.run(main())
```

### Batch Processing

```python
from app.services.linkedin import LinkedInService
import asyncio

async def main():
    companies = ["Google", "Microsoft", "Apple"]
    
    async with LinkedInService() as service:
        async for company_name, company_info in service.batch_get_company_info(companies):
            if company_info:
                print(f"Found: {company_name} - {company_info.get('website')}")
            else:
                print(f"Not found: {company_name}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Rate Limiting

The service includes built-in rate limiting to avoid being blocked by LinkedIn:

- A small delay (`LINKEDIN_SLOW_MO`) is added between actions
- Failed requests are automatically retried with exponential backoff
- Caching is used to minimize repeated requests

## Caching

Responses are cached in Redis with a configurable TTL (default: 24 hours). This helps to:

- Reduce the number of requests to LinkedIn
- Improve response times for repeated lookups
- Stay within rate limits

## Error Handling

The service handles various error conditions:

- Network timeouts
- Login failures
- Rate limiting
- Page load errors

## Testing

Run the test script to verify the scraper is working:

```bash
python test_linkedin_scraper.py
```

## Notes

- LinkedIn may block automated access. Use responsibly and consider adding delays between requests.
- For production use, consider using a proxy service to avoid IP-based rate limiting.
- The service works best with a valid LinkedIn account. Some features may be limited in anonymous mode.
