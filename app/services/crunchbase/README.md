# Crunchbase API Integration

This module provides a Python client for interacting with the Crunchbase API, with built-in rate limiting, retries, and error handling.

## Features

- **Rate Limiting**: Automatic rate limiting to stay within API quotas
- **Retry Logic**: Exponential backoff for failed requests
- **Type Hints**: Full type annotations for better IDE support
- **Pydantic Models**: Strongly-typed data models for API responses
- **Async Support**: Built on `httpx` for async/await support

## Installation

Add the following to your `requirements.txt`:

```
httpx>=0.27.0
tenacity>=8.2.0
pydantic>=2.0.0
```

## Configuration

Configure the client using environment variables:

```bash
# Required
CRUNCHBASE_API_KEY=your_api_key_here

# Optional (with defaults shown)
CRUNCHBASE_REQUESTS_PER_SECOND=2.5
CRUNCHBASE_MAX_RETRIES=3
CRUNCHBASE_REQUEST_TIMEOUT=30
CRUNCHBASE_CONNECT_TIMEOUT=10
```

Or configure programmatically:

```python
from app.services.crunchbase import CrunchbaseConfig, CrunchbaseClient

config = CrunchbaseConfig(
    api_key="your_api_key_here",
    requests_per_second=2.5,
    max_retries=3,
    request_timeout=30,
    connect_timeout=10,
)

client = CrunchbaseClient(config=config)
```

## Usage

### Basic Usage

```python
import asyncio
from app.services.crunchbase import get_crunchbase_client

async def main():
    # Get a client (automatically configured from environment)
    client = get_crunchbase_client()
    
    try:
        # Look up a company by domain
        company = await client.get_company_by_domain("airbnb.com")
        if company:
            print(f"Found company: {company.name}")
            print(f"Total funding: ${company.total_funding_usd:,.2f}")
            
            # Get funding rounds
            rounds = await client.get_company_funding_rounds(company.uuid)
            for round in rounds:
                print(f"- {round.name}: ${round.money_raised:,.0f} {round.money_raised_currency}")
    finally:
        # Close the client when done
        await client.close()

# Run the async function
asyncio.run(main())
```

### Using the Factory

The module provides a factory for managing a shared client instance:

```python
from app.services.crunchbase import get_crunchbase_client, close_crunchbase_client

async def process_company(domain: str):
    client = get_crunchbase_client()
    try:
        company = await client.get_company_by_domain(domain)
        # Process company...
        return company
    finally:
        # Don't close the client if you're using the global instance
        pass

# When your application shuts down:
async def shutdown():
    await close_crunchbase_client()
```

## Error Handling

The client raises specific exceptions for different error conditions:

```python
from app.services.crunchbase import (
    CrunchbaseAuthError,
    CrunchbaseRateLimitError,
    CrunchbaseNotFoundError,
    CrunchbaseAPIError
)

try:
    company = await client.get_company("invalid-company")
except CrunchbaseAuthError as e:
    print(f"Authentication failed: {e}")
except CrunchbaseRateLimitError as e:
    print(f"Rate limit exceeded: {e}")
    # The client will automatically retry after the rate limit resets
except CrunchbaseNotFoundError:
    print("Company not found")
except CrunchbaseAPIError as e:
    print(f"API error: {e}")
```

## Testing

Run the tests with pytest:

```bash
pytest tests/test_crunchbase_client.py -v
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
