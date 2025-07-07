#!/usr/bin/env python3
"""
Isolated test runner for Crunchbase service tests.
This script runs tests without loading the main application.
"""
import sys
import os
import importlib.util
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent)
sys.path.insert(0, project_root)

# Mock the environment variables before importing any app code
os.environ["TESTING"] = "true"
os.environ["CRUNCHBASE_API_KEY"] = "test_api_key"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379/1"
os.environ["LINKEDIN_API_KEY"] = "test_linkedin_key"
os.environ["ALGORITHM"] = "HS256"

def run_tests():
    """Run the tests."""
    # Import pytest here after setting up the environment
    import pytest
    
    # Run the tests
    test_path = os.path.join(project_root, "tests/crunchbase/test_service.py")
    return pytest.main([
        test_path,
        "-v",
        "--tb=short",
        "--no-header",
        "--no-summary"
    ])

if __name__ == "__main__":
    sys.exit(run_tests())
