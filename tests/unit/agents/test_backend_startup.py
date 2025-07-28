#!/usr/bin/env python3
"""
Test script to check if backend can start correctly
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

def test_backend_imports():
    """Test if backend imports work correctly"""
    try:

        # Test basic imports



        # Test FastAPI app import

        return True

    except Exception:
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""

    success = test_backend_imports()

    if success:
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())
