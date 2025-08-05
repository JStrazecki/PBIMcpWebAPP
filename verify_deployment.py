#!/usr/bin/env python3
"""
Deployment Verification Script
Run this to verify all required files are present for deployment
"""

import os
import sys
from pathlib import Path

def check_file_exists(filepath, description):
    """Check if a file exists and report status"""
    exists = os.path.exists(filepath)
    status = "[OK]" if exists else "[MISSING]"
    print(f"{status} {description}: {filepath}")
    if exists:
        size = os.path.getsize(filepath)
        print(f"  Size: {size} bytes")
    return exists

def main():
    print("Power BI MCP Server - Deployment Verification")
    print("=" * 50)
    
    # Get current directory
    current_dir = Path.cwd()
    print(f"Current directory: {current_dir}")
    print(f"Python version: {sys.version}")
    print()
    
    # Check critical files
    print("Critical Files:")
    critical_files = [
        ("run_fastmcp.py", "Main entry point"),
        ("requirements.txt", "Python dependencies"),
        ("Procfile", "Heroku/Azure process file"),
        ("runtime.txt", "Python runtime specification"),
        (".deployment", "Azure deployment config")
    ]
    
    all_present = True
    for filename, description in critical_files:
        if not check_file_exists(filename, description):
            all_present = False
    
    print()
    print("Application Structure:")
    app_files = [
        ("pbi_mcp_finance/__init__.py", "Package init"),
        ("pbi_mcp_finance/main.py", "Main MCP server"),
        ("pbi_mcp_finance/powerbi/client.py", "Power BI client"),
        ("pbi_mcp_finance/auth/oauth_manager.py", "OAuth manager"),
        ("pbi_mcp_finance/config/settings.py", "Settings")
    ]
    
    for filename, description in app_files:
        if not check_file_exists(filename, description):
            all_present = False
    
    print()
    print("Deployment Status:")
    if all_present:
        print("[OK] All critical files present - deployment should work")
    else:
        print("[FAILED] Missing critical files - deployment will fail")
        print("\nTroubleshooting:")
        print("1. Ensure all files are committed to git")
        print("2. Check .gitignore is not excluding critical files")
        print("3. Verify Azure deployment is pulling from correct branch")
    
    # List all Python files
    print("\nPython files in project:")
    for root, dirs, files in os.walk("."):
        # Skip hidden directories and __pycache__
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                print(f"  {filepath}")

if __name__ == "__main__":
    main()