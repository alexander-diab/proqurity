"""Configuration from .env.local and .env.

Two problems this solves, both of which broke the web UI on a fresh checkout:

1. Reading only .env.local -- a machine that has just .env got a KeyError.
   Both files are gitignored; which one exists varies per machine.
2. Reading a relative path -- dotenv_values(".env") depends on the working
   directory, so anything started from a subfolder silently found nothing.
   The path is anchored to the repo root instead.

Precedence, lowest to highest: .env, .env.local, real environment variables.
"""
from __future__ import annotations

import os

from dotenv import dotenv_values

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def cfg() -> dict[str, str]:
    """The merged configuration."""
    merged: dict[str, str] = {}
    for name in (".env", ".env.local"):
        merged.update(dotenv_values(os.path.join(ROOT, name)))
    merged.update(os.environ)
    return merged
