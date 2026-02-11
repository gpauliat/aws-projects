"""
Pytest configuration for Lambda tests.

Adds the src directory to Python path so tests can import Lambda functions and shared modules.
"""

import sys
import os

# Add src directory to Python path
src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
sys.path.insert(0, os.path.abspath(src_path))
