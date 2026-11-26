"""Vercel entry point for the Flask application in webapp/."""

import os
import sys


PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
WEBAPP_DIR = os.path.join(PROJECT_ROOT, "webapp")
if WEBAPP_DIR not in sys.path:
    sys.path.insert(0, WEBAPP_DIR)

from webapp.app import create_app  # noqa: E402


app = create_app()
