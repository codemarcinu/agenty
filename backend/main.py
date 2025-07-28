"""
Main application entry point.
"""

import os
import sys

# Ustaw PYTHONPATH na ./src jeśli nie jest ustawiony
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, "src")
if "PYTHONPATH" not in os.environ:
    os.environ["PYTHONPATH"] = src_path
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Import the app from the backend module
from app_factory import create_app

app = create_app()

# This file is just a wrapper to help with imports
