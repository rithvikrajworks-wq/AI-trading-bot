'''Compatibility shim to allow imports using 'app.*' when the actual package lives under the 'backend' directory.

This file creates an alias so that ``import app.settings`` (and similar imports) resolve to the
``backend.app`` package without having to modify every import throughout the codebase.
'''
import importlib
import sys

# Import the real package that lives under ``backend``.
_backend_app = importlib.import_module('backend.app')

# Register it under the name ``app`` so existing imports succeed.
# ``setdefault`` ensures we don’t overwrite an existing entry if someone already
# defined a true top‑level ``app`` package.
sys.modules['app'] = _backend_app
