"""Shared test support: puts ``src`` on sys.path and exposes fixture paths.

Tests under ``test/product`` are deterministic and offline (SPEC-001 §4.6).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
FIXTURES = Path(__file__).resolve().parent / "fixtures"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# Fixture layout mirrors the C-MAPSS archive naming so the loader is exercised
# with ``subset="FD001"`` against ``mini_`` prefixed files.
FIXTURE_PREFIX = "mini_"
