#!/usr/bin/env python3
"""
Test script to verify deployment and startup configuration
Run this to test if the app can start before deployment
"""

import sys
import os

print("=== Startup Test ===")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print(f"Files in directory: {os.listdir('.')}")

try:
    from app import APP
    print("✅ SUCCESS: app.APP imported successfully")
    print(f"App type: {type(APP)}")
    print(f"App name: {APP.name}")
    print("Routes:")
    for rule in APP.url_map.iter_rules():
        print(f"  {rule.rule}")
except ImportError as e:
    print(f"❌ FAILED: Cannot import app.APP - {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ ERROR: {e}")
    sys.exit(1)

print("=== Test completed successfully ===")