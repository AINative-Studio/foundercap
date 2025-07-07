#!/usr/bin/env python3
"""
Check and fix Playwright installation.
"""
import subprocess
import sys
import os

def run_command(cmd):
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False, result.stderr
    print(result.stdout)
    return True, result.stdout

def main():
    print("=== Checking Playwright installation ===")
    
    # Check Python package version
    success, _ = run_command("pip show playwright")
    if not success:
        print("Installing Playwright Python package...")
        success, _ = run_command("pip install playwright")
        if not success:
            print("Failed to install Playwright Python package")
            return 1
    
    # Install browsers
    print("\n=== Installing Playwright browsers ===")
    success, _ = run_command("python -m playwright install")
    if not success:
        print("Failed to install browsers")
        return 1
    
    # Install dependencies
    print("\n=== Installing system dependencies ===")
    if sys.platform == "darwin":  # macOS
        success, _ = run_command("brew install --cask xquartz")
        success, _ = run_command("python -m playwright install-deps")
    elif sys.platform == "linux":
        success, _ = run_command("python -m playwright install-deps")
    
    # Verify installation
    print("\n=== Verifying Playwright installation ===")
    success, _ = run_command("python -m playwright --version")
    success, _ = run_command("python -m playwright install chromium")
    
    print("\n=== Playwright setup complete ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())
