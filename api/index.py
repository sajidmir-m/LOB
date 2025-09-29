"""Vercel entrypoint for Python serverless function.

Loads the FastAPI `app` object from the project root `api.py` without
relying on Python package imports that could conflict with the `api/` folder.
"""

import os
import sys
import importlib.util

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Ensure project root is importable
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Load api.py as a module by file location
api_module_path = os.path.join(PROJECT_ROOT, "api.py")
spec = importlib.util.spec_from_file_location("root_api", api_module_path)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

# Expose FastAPI app for Vercel
app = module.app

