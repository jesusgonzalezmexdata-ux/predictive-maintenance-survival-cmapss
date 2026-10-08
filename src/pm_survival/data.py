"""Raw data boundary and offline loader for C-MAPSS (TASK-001, SPEC-001 §4.1).

The loader reads the 26-column whitespace-separated C-MAPSS text format from a
*local* directory. It never downloads anything (DEC-004: raw data lives outside
git; the canonical archive is declared in ``data/raw/MANIFEST.json``, DEC-003).

File naming follows the NASA archive: ``train_FD001.txt``, ``test_FD001.txt``,
``RUL_FD001.txt``. A ``prefix`` argument lets tests point at small fixtures
(``mini_train_FD001.txt``) without touching real data.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

import pandas as pd

SUBSETS = ("FD001", "FD002", "FD003", "FD004")
OP_SETTINGS = [f"op_setting_{i}" for i in range(1, 4)]
SENSORS = [f"sensor_{i}" for i in range(1, 22)]
COLUMNS = ["unit_id", "cycle", *OP_SETTINGS, *SENSORS]
N_COLUMNS = len(COLUMNS)  # 26

ENV_RAW_DIR = "PM_RAW_DIR"


class SchemaError(ValueError):
    """Raised when a frame does not satisfy the C-MAPSS schema contract."""


def resolve_raw_dir(raw_dir: str | os.PathLike | None = None) -> Path:
    """Resolve the raw directory from an explicit argument or ``PM_RAW_DIR``."""
    if raw_dir is not None:
        return Path(raw_dir)
    env = os.environ.get(ENV_RAW_DIR)
    if not env:
        raise FileNotFoundError(
            f"Raw directory not given and {ENV_RAW_DIR} is unset. "
            "Extract the DEC-003 archive locally (e.g. data/raw/cmapss/) and pass --raw-dir."
        )
    return Path(env)


def _path(raw_dir: Path, name: str) -> Path:
    p = raw_dir / name
    if not p.exists():
        raise FileNotFoundError(f"Expected C-MAPSS file not found: {p}")
    return p


def load_fd(
    raw_dir: str | os.PathLike,
    subset: str = "FD001",
    split: Literal["train", "test"] = "train",
    prefix: str = "",
) -> pd.DataFrame:
    """Load ``{prefix}{split}_{subset}.txt`` as a typed frame with ``COLUMNS``."""
    if subset not in SUBSETS:
        raise FileNotFoundError(f"Unknown subset {subset!r}; expected one of {SUBSETS}")
    if split not in ("train", "test"):
        raise ValueError(f"split must be 'train' or 'test', got {split!r}")
    path = _path(Path(raw_dir), f"{prefix}{split}_{subset}.txt")
    df = pd.read_csv(path, sep=r"\s+", header=None, engine="python")
    if df.shape[1] != N_COLUMNS:
        raise SchemaError(f"{path.name}: expected {N_COLUMNS} columns, found {df.shape[1]}")
    df.columns = COLUMNS
    df["unit_id"] = df["unit_id"].astype("int64")
    df["cycle"] = df["cycle"].astype("int64")
    for c in OP_SETTINGS + SENSORS:
        df[c] = df[c].astype("float64")
    return df


def load_rul(raw_dir: str | os.PathLike, subset: str = "FD001", prefix: str = "") -> pd.Series:
    """Load ground-truth remaining life for *test* units (evaluation only, never a feature).

    Returns a Series indexed by 1-based ``unit_id`` in file order.
    """
    path = _path(Path(raw_dir), f"{prefix}RUL_{subset}.txt")
    values = pd.read_csv(path, sep=r"\s+", header=None, engine="python")[0].astype("int64")
    values.index = pd.RangeIndex(1, len(values) + 1, name="unit_id")
    values.name = "rul_true"
    return values


def validate_schema(df: pd.DataFrame) -> dict:
    """Validate the C-MAPSS contract; return a small summary on success.

    Checks: exact column set/order, no nulls, positive cycles, and per-unit
    cycles that are contiguous ``1..n`` (required for duration semantics).
    """
    if list(df.columns) != COLUMNS:
        raise SchemaError(f"columns must be exactly {N_COLUMNS} C-MAPSS columns in order")
    if df.isna().any().any():
        raise SchemaError("null values present")
    if (df["cycle"] <= 0).any():
        raise SchemaError("cycle must be positive")
    for unit, g in df.groupby("unit_id", sort=True):
        cycles = g["cycle"].to_numpy()
        n = len(cycles)
        if cycles.min() != 1 or cycles.max() != n or len(set(cycles.tolist())) != n:
            raise SchemaError(f"unit {unit}: cycles are not contiguous 1..{n}")
    return {
        "n_rows": int(len(df)),
        "n_units": int(df["unit_id"].nunique()),
        "max_cycle": int(df["cycle"].max()),
    }
