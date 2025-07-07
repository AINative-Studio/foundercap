#!/usr/bin/env python3
"""
Test runner for Crunchbase service tests.
This script sets up a clean environment and runs the Crunchbase service tests.
"""
import os
import sys
import pytest
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent)
sys.path.insert(0, project_root)

def main():
    """Run the Crunchbase service tests."""
    # Set test environment variables
    os.environ["TESTING"] = "true"
    os.environ["CRUNCHBASE_API_KEY"] = "test_api_key"
    
    # Run the tests
    test_path = os.path.join(project_root, "tests/test_crunchbase_service.py")
    return pytest.main([
        test_path,
        "-v",
        "--tb=short",
        "--no-header",
        "--no-summary"
    ])

if __name__ == "__main__":
    sys.exit(main())
