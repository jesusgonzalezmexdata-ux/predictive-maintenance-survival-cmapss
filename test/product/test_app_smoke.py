"""Smoke test: the Streamlit decision app renders end to end on the mini fixtures."""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def test_app_renders_with_local_data(tmp_path, monkeypatch):
    for name in ("train_FD001.txt", "test_FD001.txt", "RUL_FD001.txt"):
        shutil.copy(FIXTURES / f"mini_{name}", tmp_path / name)
    monkeypatch.setenv("PM_RAW_DIR", str(tmp_path))
    at = AppTest.from_file(str(ROOT / "app" / "streamlit_app.py"), default_timeout=120)
    at.run()
    assert not at.exception, at.exception
    assert at.title[0].value
    assert len(at.metric) >= 3
