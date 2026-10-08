"""TASK-001 tests — raw data boundary and offline loader (SPEC-001 §4.1)."""
from __future__ import annotations

import json
import unittest

import _support  # noqa: F401  (sys.path setup)
from _support import FIXTURES, FIXTURE_PREFIX, ROOT

from pm_survival import data as D


class LoaderTests(unittest.TestCase):
    def test_load_train_returns_expected_columns(self):
        df = D.load_fd(FIXTURES, subset="FD001", split="train", prefix=FIXTURE_PREFIX)
        self.assertEqual(list(df.columns), D.COLUMNS)
        self.assertEqual(len(df.columns), 26)
        self.assertEqual(len(df), 175)
        self.assertEqual(sorted(df["unit_id"].unique().tolist()), [1, 2, 3])

    def test_load_test_and_rul(self):
        df = D.load_fd(FIXTURES, subset="FD001", split="test", prefix=FIXTURE_PREFIX)
        rul = D.load_rul(FIXTURES, subset="FD001", prefix=FIXTURE_PREFIX)
        self.assertEqual(len(df), 50)
        self.assertEqual(rul.tolist(), [25, 40])
        self.assertEqual(rul.index.tolist(), [1, 2])  # unit ids, 1-based

    def test_validate_schema_rejects_wrong_column_count(self):
        df = D.load_fd(FIXTURES, subset="FD001", split="train", prefix=FIXTURE_PREFIX)
        bad = df.drop(columns=["sensor_21"])
        with self.assertRaises(D.SchemaError):
            D.validate_schema(bad)

    def test_validate_schema_rejects_non_contiguous_cycles(self):
        df = D.load_fd(FIXTURES, subset="FD001", split="train", prefix=FIXTURE_PREFIX)
        df = df.drop(index=df.index[5])  # remove cycle 6 of unit 1
        with self.assertRaises(D.SchemaError):
            D.validate_schema(df)

    def test_validate_schema_accepts_fixture(self):
        df = D.load_fd(FIXTURES, subset="FD001", split="train", prefix=FIXTURE_PREFIX)
        summary = D.validate_schema(df)
        self.assertEqual(summary["n_units"], 3)
        self.assertEqual(summary["n_rows"], 175)

    def test_loader_never_downloads(self):
        import inspect

        src = inspect.getsource(D)
        for forbidden in ("urllib", "requests", "http://", "https://"):
            self.assertNotIn(forbidden, src)

    def test_missing_file_raises_clear_error(self):
        with self.assertRaises(FileNotFoundError):
            D.load_fd(FIXTURES, subset="FD009", split="train", prefix=FIXTURE_PREFIX)


class ManifestTests(unittest.TestCase):
    def test_manifest_declares_dec003_archive(self):
        manifest = json.loads((ROOT / "data/raw/MANIFEST.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["decision"], "DEC-003")
        self.assertTrue(manifest["archive_sha256"].startswith("7109344d"))
        self.assertIn("train_FD001.txt", manifest["files"])
        self.assertEqual(manifest["files"]["train_FD001.txt"]["rows"], 20631)

    def test_no_raw_dataset_committed(self):
        # AC-7 / DEC-004: nothing > 1 MB tracked under data/
        for p in (ROOT / "data").rglob("*"):
            if p.is_file() and not any(part == "cmapss" for part in p.parts):
                self.assertLess(p.stat().st_size, 1_000_000, p)


if __name__ == "__main__":
    unittest.main()
