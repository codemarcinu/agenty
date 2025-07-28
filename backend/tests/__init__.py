from __future__ import annotations

from collections.abc import AsyncGenerator, Callable, Coroutine
from typing import Any, Dict, List, Optional, Union

"""
Test package for the backend application.
"""

import os

# Set User-Agent environment variable early to prevent warnings
os.environ.setdefault(
    "USER_AGENT", "FoodSave-AI/1.0.0 (https://github.com/foodsave-ai)"
)
