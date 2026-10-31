"""Root pytest configuration and path setup."""

import os
import sys
from pathlib import Path

# Force fake LLM provider during test runs to guarantee isolated offline execution
os.environ["LLM_PROVIDER"] = "fake"

# Ensure backend root is on sys.path regardless of execution working directory
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
