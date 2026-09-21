import os
import sys
from pathlib import Path

# Resolve absolute path to the backend directory and ensure it is on sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Import the existing FastAPI application from backend/app/main.py
from app.main import app  # noqa: E402

# Export the application for Vercel Serverless Function runtime
__all__ = ["app"]
