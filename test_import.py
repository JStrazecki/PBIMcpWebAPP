#!/usr/bin/env python3
"""
Test script to verify main_simple.py can be imported correctly
"""

try:
    print("Testing import of main_simple...")
    from main_simple import app
    print("✅ Successfully imported app from main_simple")
    print(f"App type: {type(app)}")
    print(f"App name: {app.name if hasattr(app, 'name') else 'Unknown'}")
    
    # Test basic app functionality
    with app.test_client() as client:
        response = client.get('/')
        print(f"✅ Test request to / returned status: {response.status_code}")
        
except Exception as e:
    print(f"❌ Import/test failed: {e}")
    import traceback
    traceback.print_exc()