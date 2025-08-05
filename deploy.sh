#!/bin/bash
# Azure App Service Deployment Script
# This script ensures proper deployment of the FastMCP app

echo "Starting deployment script..."

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Ensure run_fastmcp.py is executable
chmod +x run_fastmcp.py

# Create necessary directories
mkdir -p shared

echo "Deployment completed!"