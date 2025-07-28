from __future__ import annotations

# Set User-Agent environment variable early to prevent warnings
import os

os.environ.setdefault(
    "USER_AGENT", "FoodSave-AI/1.0.0 (https://github.com/foodsave-ai)"
)

# Import all API modules
from . import agents, analytics, chat, health, monitoring, pantry, settings, upload
