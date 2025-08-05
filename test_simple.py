#!/usr/bin/env python3
"""
Simple test to verify Python is working in Azure
"""
import sys
import os

print("=== AZURE DEPLOYMENT TEST ===")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print(f"Directory contents:")
for item in os.listdir('.'):
    print(f"  - {item}")
print("=== TEST COMPLETE ===")