"""Compatibility launcher for local development.

The canonical application entry point is ``backend.app.main:app``.
"""

from backend.app.main import app

__all__ = ["app"]
