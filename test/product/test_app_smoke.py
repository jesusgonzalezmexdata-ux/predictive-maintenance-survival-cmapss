"""Smoke tests: the Streamlit decision app renders end to end (demo artifacts and local data)."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent / "fixtures"
APP = str(ROOT / "app" / "streamlit_app.py")


def _run(monkeypatch, raw_dir: Path) -> AppTest:
    monkeypatch.setenv("PM_RAW_DIR", str(raw_dir))
    at = AppTest.from_file(APP, default_timeout=180)
    at.run()
    assert not at.exception, at.exception
    return at


def test_app_demo_mode_without_nasa_files(tmp_path, monkeypatch):
    at = _run(monkeypatch, tmp_path / "missing")
    assert at.title[0].value
    labels = [m.label for m in at.metric]
    assert "Intervenir ahora" in labels and "Ahorro frente a reemplazo por edad" in labels
    assert any("archivos NASA" in i.value for i in at.info)


def test_app_explains_an_engine_with_local_data(tmp_path, monkeypatch):
    for name in ("train_FD001.txt", "test_FD001.txt", "RUL_FD001.txt"):
        shutil.copy(FIXTURES / f"mini_{name}", tmp_path / name)
    at = _run(monkeypatch, tmp_path)
    assert at.selectbox, "engine selector should appear when local data exist"


def test_changing_cost_ratio_rerenders(tmp_path, monkeypatch):
    at = _run(monkeypatch, tmp_path / "missing")
    at.sidebar.select_slider[0].set_value(50.0).run()
    assert not at.exception


def test_fleet_mode_runs_the_error_example(tmp_path, monkeypatch):
    at = _run(monkeypatch, tmp_path / "missing")
    at.segmented_control[0].set_value("Tu flota").run()
    at.button[0].click().run()
    assert not at.exception, at.exception
    assert any("órdenes válidas" in m.value for m in at.markdown)
    assert at.success and "Montacargas" in at.success[0].value
