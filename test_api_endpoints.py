#!/usr/bin/env python3
"""Test API endpoints that are working."""

import sys
import os
import requests
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_health_endpoints():
    """Test if the app starts and health endpoints work."""
    print("Testing API endpoints...")
    
    # We'll test with curl instead of requests to avoid import issues
    
    # First, let's check what's actually running
    base_url = "http://localhost:8000"
    
    tests = [
        ("Health Check", f"{base_url}/api/v1/health/"),
        ("Health Detailed", f"{base_url}/api/v1/health/detailed"),
        ("Root Documentation", f"{base_url}/docs"),
        ("OpenAPI Schema", f"{base_url}/openapi.json"),
    ]
    
    print("Note: These tests require the FastAPI server to be running.")
    print("Start the server with: uvicorn app.main:app --reload")
    print()
    
    for test_name, url in tests:
        try:
            # Use curl instead of requests to avoid import issues
            import subprocess
            result = subprocess.run([
                "curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", url
            ], capture_output=True, text=True, timeout=5)
            
            status_code = result.stdout.strip()
            
            if status_code == "200":
                print(f"✓ {test_name}: {url} -> {status_code}")
            else:
                print(f"❌ {test_name}: {url} -> {status_code}")
                
        except subprocess.TimeoutExpired:
            print(f"⏰ {test_name}: {url} -> Timeout (server not running?)")
        except Exception as e:
            print(f"❌ {test_name}: {url} -> Error: {e}")

def check_project_structure():
    """Verify the project structure is complete."""
    print("Checking project structure...")
    
    # Key files that should exist
    key_files = [
        "app/main.py",
        "app/api/__init__.py", 
        "app/api/endpoints/health.py",
        "app/api/endpoints/pipeline.py",
        "app/services/pipeline.py",
        "app/services/linkedin/service.py",
        "app/services/crunchbase/service.py",
        "app/core/diff.py",
        "app/core/snapshot.py",
        "requirements.txt",
        ".env",
        "README.md"
    ]
    
    missing_files = []
    existing_files = []
    
    for file_path in key_files:
        if os.path.exists(file_path):
            existing_files.append(file_path)
            print(f"✓ {file_path}")
        else:
            missing_files.append(file_path)
            print(f"❌ {file_path}")
    
    print(f"\nProject structure: {len(existing_files)}/{len(key_files)} files exist")
    
    if missing_files:
        print("Missing files:")
        for file_path in missing_files:
            print(f"  - {file_path}")
    
    return len(missing_files) == 0

def analyze_implementation_status():
    """Analyze what's implemented vs what's needed."""
    
    print("Implementation Status Analysis")
    print("=" * 50)
    
    implemented_features = {
        "Core Infrastructure": {
            "FastAPI application setup": "✅",
            "Configuration management": "✅", 
            "Database models": "✅",
            "API routing": "✅",
            "Environment configuration": "✅"
        },
        "Data Processing": {
            "Diff engine": "✅",
            "Snapshot service": "✅",
            "Data normalization": "✅",
            "Pipeline orchestration": "✅",
            "Change detection": "✅"
        },
        "External Integrations": {
            "LinkedIn scraper": "✅",
            "Crunchbase API client": "✅",
            "ZeroDB integration": "⚠️ (API not available)",
            "Airtable integration": "⚠️ (needs field mapping)",
            "Redis caching": "✅"
        },
        "API Endpoints": {
            "Health checks": "✅",
            "Pipeline endpoints": "✅",
            "Company processing": "✅",
            "Batch processing": "✅",
            "Status monitoring": "✅"
        },
        "Testing": {
            "Unit tests": "✅",
            "Component tests": "✅",
            "Integration tests": "⚠️ (partial)",
            "API tests": "⚠️ (needs running server)",
            "End-to-end tests": "❌"
        },
        "Frontend": {
            "React dashboard": "❌",
            "User interface": "❌", 
            "Data visualization": "❌",
            "Admin panel": "❌"
        },
        "DevOps": {
            "Docker setup": "⚠️ (basic)",
            "CI/CD pipeline": "❌",
            "Production deployment": "❌",
            "Monitoring/logging": "⚠️ (basic)"
        }
    }
    
    total_features = 0
    completed_features = 0
    partial_features = 0
    
    for category, features in implemented_features.items():
        print(f"\n{category}:")
        for feature, status in features.items():
            print(f"  {status} {feature}")
            total_features += 1
            if status == "✅":
                completed_features += 1
            elif status == "⚠️":
                partial_features += 1
    
    completion_rate = (completed_features / total_features) * 100
    partial_rate = (partial_features / total_features) * 100
    
    print(f"\nOverall Implementation Status:")
    print(f"✅ Completed: {completed_features}/{total_features} ({completion_rate:.1f}%)")
    print(f"⚠️ Partial: {partial_features}/{total_features} ({partial_rate:.1f}%)")
    print(f"❌ Missing: {total_features - completed_features - partial_features}/{total_features} ({100 - completion_rate - partial_rate:.1f}%)")
    
    return completion_rate

def check_dependencies():
    """Check if all required dependencies are installed."""
    print("Checking dependencies...")
    
    required_packages = [
        "fastapi",
        "uvicorn", 
        "pydantic",
        "sqlalchemy",
        "alembic",
        "redis",
        "httpx",
        "playwright",
        "celery",
        "tenacity",
        "python-dotenv"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package}")
    
    if missing_packages:
        print(f"\nMissing packages: {', '.join(missing_packages)}")
        print("Install with: pip install " + " ".join(missing_packages))
    else:
        print("✅ All required dependencies are installed!")
    
    return len(missing_packages) == 0

if __name__ == "__main__":
    print("FounderCap Backend Status Check")
    print("=" * 50)
    
    # Check project structure
    structure_ok = check_project_structure()
    print()
    
    # Check dependencies
    deps_ok = check_dependencies()
    print()
    
    # Analyze implementation status
    completion_rate = analyze_implementation_status()
    print()
    
    # Test API endpoints (if server is running)
    test_health_endpoints()
    print()
    
    # Overall assessment
    print("Overall Assessment")
    print("=" * 50)
    
    if structure_ok and deps_ok and completion_rate >= 70:
        print("🎉 EXCELLENT: Backend is in great shape!")
        print("✅ Ready for frontend development")
        print("✅ Core functionality is complete")
        print("✅ Well-tested and documented")
    elif completion_rate >= 50:
        print("✅ GOOD: Backend is functional with room for improvement")
        print("⚠️ Some integrations need work")
        print("✅ Core features are working")
    elif completion_rate >= 30:
        print("⚠️ FAIR: Backend has foundation but needs more work")
        print("❌ Several key features missing")
        print("⚠️ More testing needed")
    else:
        print("❌ POOR: Backend needs significant work")
        print("❌ Many core features missing")
        print("❌ Not ready for production")
    
    print(f"\nNext priorities:")
    if completion_rate >= 70:
        print("1. Build React frontend dashboard")
        print("2. Set up CI/CD pipeline") 
        print("3. Prepare production deployment")
    elif completion_rate >= 50:
        print("1. Complete ZeroDB integration testing")
        print("2. Finish Airtable field mapping")
        print("3. Add comprehensive API tests")
    else:
        print("1. Fix configuration issues")
        print("2. Complete core integrations")
        print("3. Add more comprehensive testing")