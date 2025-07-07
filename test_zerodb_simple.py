#!/usr/bin/env python3
"""Simple test script to validate ZeroDB API access."""

import asyncio
import httpx
import os
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

ZERODB_API_URL = os.getenv("ZERODB_API_URL", "https://api.ainative.studio/api/v1")
ZERODB_EMAIL = os.getenv("ZERODB_EMAIL")
ZERODB_PASSWORD = os.getenv("ZERODB_PASSWORD")

async def test_zerodb_authentication():
    """Test ZeroDB authentication flow."""
    print("🔐 Testing ZeroDB Authentication...")
    print(f"   API URL: {ZERODB_API_URL}")
    print(f"   Email: {ZERODB_EMAIL}")
    print(f"   Password: {'*' * len(ZERODB_PASSWORD) if ZERODB_PASSWORD else 'NOT SET'}")
    
    if not ZERODB_EMAIL or not ZERODB_PASSWORD:
        print("❌ ZeroDB credentials not set in environment")
        return None
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Step 1: Authenticate
            auth_response = await client.post(
                f"{ZERODB_API_URL}/auth/",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={
                    "username": ZERODB_EMAIL,
                    "password": ZERODB_PASSWORD,
                }
            )
            auth_response.raise_for_status()
            auth_data = auth_response.json()
            token = auth_data["access_token"]
            print(f"✅ Authentication successful, token length: {len(token)}")
            return token
            
        except httpx.HTTPStatusError as e:
            print(f"❌ Authentication failed: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return None

async def test_zerodb_project_operations(token):
    """Test ZeroDB project operations."""
    print("\n🏗️ Testing ZeroDB Project Operations...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Step 1: List existing projects
            projects_response = await client.get(
                f"{ZERODB_API_URL}/projects/",
                headers=headers
            )
            projects_response.raise_for_status()
            projects = projects_response.json()
            print(f"✅ Found {len(projects)} existing projects")
            
            # Look for existing FounderCap project
            foundercap_project = None
            for project in projects:
                if project.get("name") == "FounderCap":
                    foundercap_project = project
                    print(f"   Found existing FounderCap project: {project['id']}")
                    break
            
            # Step 2: Create project if needed
            if not foundercap_project:
                create_response = await client.post(
                    f"{ZERODB_API_URL}/projects/",
                    headers=headers,
                    json={
                        "name": "FounderCap",
                        "description": "Startup Funding Tracker & Dashboard Automation"
                    }
                )
                create_response.raise_for_status()
                foundercap_project = create_response.json()
                print(f"✅ Created new FounderCap project: {foundercap_project['id']}")
            
            project_id = foundercap_project["id"]
            
            # Step 3: Check database status
            db_status_response = await client.get(
                f"{ZERODB_API_URL}/projects/{project_id}/database",
                headers=headers
            )
            db_status_response.raise_for_status()
            db_status = db_status_response.json()
            print(f"✅ Database status: enabled={db_status.get('enabled', False)}")
            
            # Step 4: Enable database if needed
            if not db_status.get("enabled"):
                enable_response = await client.post(
                    f"{ZERODB_API_URL}/projects/{project_id}/database",
                    headers=headers
                )
                enable_response.raise_for_status()
                print("✅ Database enabled successfully")
            
            return project_id
            
        except httpx.HTTPStatusError as e:
            print(f"❌ Project operations failed: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return None

async def test_zerodb_memory_operations(token, project_id):
    """Test ZeroDB memory operations."""
    print("\n🧠 Testing ZeroDB Memory Operations...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Step 1: Store a memory record
            memory_data = {
                "content": "Company: Test Startup Inc - A revolutionary AI startup focused on quantum computing solutions",
                "agent_id": "foundercap-system",
                "session_id": "company-test-123",
                "role": "system",
                "metadata": {
                    "company_id": "test-123",
                    "name": "Test Startup Inc",
                    "industry": "Technology",
                    "funding_stage": "Series A"
                }
            }
            
            store_response = await client.post(
                f"{ZERODB_API_URL}/projects/{project_id}/database/memory/store",
                headers=headers,
                json=memory_data
            )
            store_response.raise_for_status()
            store_result = store_response.json()
            print(f"✅ Memory stored successfully: {store_result.get('id', 'No ID')}")
            
            # Step 2: Search memories
            search_response = await client.post(
                f"{ZERODB_API_URL}/projects/{project_id}/database/memory/search",
                headers=headers,
                json={
                    "query": "AI startup quantum computing",
                    "agent_id": "foundercap-system",
                    "limit": 5
                }
            )
            search_response.raise_for_status()
            search_results = search_response.json()
            print(f"✅ Memory search successful: found {len(search_results)} results")
            
            if search_results:
                print(f"   Top result: {search_results[0].get('content', 'No content')[:80]}...")
            
            return True
            
        except httpx.HTTPStatusError as e:
            print(f"❌ Memory operations failed: {e.response.status_code} - {e.response.text}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False

async def main():
    """Run all ZeroDB tests."""
    print("ZeroDB Integration Test")
    print("=" * 50)
    
    # Test 1: Authentication
    token = await test_zerodb_authentication()
    if not token:
        print("\n❌ Authentication failed - stopping tests")
        return False
    
    # Test 2: Project Operations
    project_id = await test_zerodb_project_operations(token)
    if not project_id:
        print("\n❌ Project operations failed - stopping tests")
        return False
    
    # Test 3: Memory Operations
    memory_success = await test_zerodb_memory_operations(token, project_id)
    if not memory_success:
        print("\n❌ Memory operations failed")
        return False
    
    print("\n🎉 All ZeroDB tests passed! Integration is working correctly.")
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    if not success:
        exit(1)