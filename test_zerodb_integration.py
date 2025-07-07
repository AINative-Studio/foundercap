#!/usr/bin/env python3
"""Test script to validate ZeroDB integration."""

import asyncio
import json
import sys
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.services.updater.zerodb import ZeroDBUpdater
from app.core.config import settings

async def test_zerodb_integration():
    """Test the complete ZeroDB integration flow."""
    print("🚀 Testing ZeroDB Integration...")
    
    # Check configuration
    print(f"📋 Configuration:")
    print(f"   API URL: {settings.ZERODB_API_URL}")
    print(f"   Email: {settings.ZERODB_EMAIL}")
    print(f"   Password: {'*' * len(settings.ZERODB_PASSWORD) if settings.ZERODB_PASSWORD else 'NOT SET'}")
    
    if not settings.ZERODB_EMAIL or not settings.ZERODB_PASSWORD:
        print("❌ ZeroDB credentials not configured in .env file")
        return False
    
    updater = ZeroDBUpdater()
    
    try:
        # Test 1: Initialize ZeroDB updater
        print("\n🔄 Step 1: Initializing ZeroDB updater...")
        await updater._initialize()
        print("✅ ZeroDB updater initialized successfully")
        
        # Test 2: Store sample company data
        print("\n🔄 Step 2: Storing sample company data...")
        sample_company = {
            "id": "test-company-123",
            "name": "Test Startup Inc",
            "description": "A revolutionary AI startup focused on quantum computing solutions",
            "website": "https://teststartup.com",
            "linkedin_url": "https://linkedin.com/company/teststartup",
            "city": "San Francisco",
            "state": "CA",
            "country": "USA",
            "industry": "Technology",
            "funding_stage": "Series A",
            "valuation": 10000000,
            "employee_count": 25,
            "founded_year": 2023
        }
        
        result = await updater.update("test-company-123", sample_company)
        print(f"✅ Company stored successfully: {result.get('id', 'No ID returned')}")
        
        # Test 3: Search for the company
        print("\n🔄 Step 3: Testing semantic search...")
        search_results = await updater.search_companies("AI startup quantum computing", limit=5)
        print(f"✅ Found {len(search_results)} companies matching search")
        
        if search_results:
            print(f"   Top result: {search_results[0].get('content', 'No content')[:100]}...")
        
        # Test 4: Store another company for variety
        print("\n🔄 Step 4: Storing second company...")
        sample_company_2 = {
            "id": "test-company-456", 
            "name": "FinTech Solutions Ltd",
            "description": "Financial technology company providing blockchain banking solutions",
            "website": "https://fintechsolutions.com",
            "city": "New York",
            "state": "NY",
            "industry": "Financial Services",
            "funding_stage": "Seed",
            "employee_count": 12
        }
        
        result2 = await updater.update("test-company-456", sample_company_2)
        print(f"✅ Second company stored: {result2.get('id', 'No ID returned')}")
        
        # Test 5: Search with different query
        print("\n🔄 Step 5: Testing different search query...")
        fintech_results = await updater.search_companies("financial technology blockchain", limit=3)
        print(f"✅ Found {len(fintech_results)} fintech companies")
        
        print("\n🎉 All tests passed! ZeroDB integration is working correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        try:
            await updater._shutdown()
            print("🧹 ZeroDB updater shut down")
        except Exception as e:
            print(f"⚠️ Warning during shutdown: {e}")

async def test_authentication_only():
    """Test just the authentication flow."""
    print("🔐 Testing ZeroDB Authentication Only...")
    
    updater = ZeroDBUpdater()
    
    try:
        token = await updater._authenticate()
        print(f"✅ Authentication successful, token length: {len(token)}")
        return True
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return False

if __name__ == "__main__":
    print("ZeroDB Integration Test")
    print("=" * 50)
    
    # First test just authentication
    auth_success = asyncio.run(test_authentication_only())
    
    if auth_success:
        print("\n" + "=" * 50)
        # Then test full integration
        success = asyncio.run(test_zerodb_integration())
        
        if success:
            print("\n🎉 ZeroDB integration is fully functional!")
        else:
            print("\n❌ ZeroDB integration has issues")
            sys.exit(1)
    else:
        print("\n❌ Authentication failed - check credentials")
        sys.exit(1)