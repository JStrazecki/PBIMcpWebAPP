"""
Test FastMCP server locally before deployment
"""

import subprocess
import time
import requests
import sys

def test_server():
    """Test the FastMCP server"""
    print("Starting FastMCP server for testing...")
    
    # Start the server
    process = subprocess.Popen([
        sys.executable, "-m", "gunicorn",
        "--bind=0.0.0.0:8000",
        "--worker-class", "uvicorn.workers.UvicornWorker",
        "--timeout", "30",
        "asgi_simple:app"
    ])
    
    # Wait for server to start
    time.sleep(5)
    
    try:
        # Test the server
        print("\nTesting server endpoints...")
        
        # Test root
        response = requests.get("http://localhost:8000/")
        print(f"Root endpoint: {response.status_code}")
        if response.status_code == 200:
            print(response.json())
        
        # Test health (if implemented)
        try:
            response = requests.get("http://localhost:8000/health")
            print(f"\nHealth endpoint: {response.status_code}")
            if response.status_code == 200:
                print(response.json())
        except:
            print("Health endpoint not available")
        
        print("\nServer is working! You can deploy to Azure.")
        
    except Exception as e:
        print(f"Error testing server: {e}")
    finally:
        # Stop the server
        process.terminate()
        process.wait()

if __name__ == "__main__":
    test_server()