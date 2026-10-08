"""TASK-006 tests — end-to-end pipeline, determinism, CLI extract (SPEC-001 §4.4/§5)."""
from __future__ import annotations

import json
import tempfile
import unittest
import warnings
import zipfile
from pathlib import Path

import _support  # noqa: F401
import numpy as np

from pm_survival import cli, pipeline


def write_synthetic_cmapss(raw_dir: Path, n_train: int = 40, n_test: int = 12, seed: int = 9) -> None:
    """Small C-MAPSS-format files (26 cols) with a degradation signal tied to lifetime."""
    rng = np.random.default_rng(seed)

    def unit_rows(unit: int, n: int, rate: float) -> list[str]:
        out = []
        for c in range(1, n + 1):
            ops = [rng.normal(0, 1e-3), rng.normal(0, 3e-4), 100.0]
            s = 500 + np.arange(21) * 10.0 + rng.normal(0, 0.05, 21)
            s[3] += rate * c  # sensor_4 drifts with a unit-specific rate
            s[10] += 0.5 * rate * c
            out.append(" ".join([str(unit), str(c)] + [f"{v:.4f}" for v in ops] + [f"{v:.2f}" for v in s]) + "  ")
        return out

    train, test, rul = [], [], []
    for u in range(1, n_train + 1):
        rate = rng.uniform(0.2, 1.0)
        life = int(np.clip(round(60 / rate + rng.normal(0, 4)), 25, 400))
        train += unit_rows(u, life, rate)
    for u in range(1, n_test + 1):
        rate = rng.uniform(0.2, 1.0)
        life = int(np.clip(round(60 / rate + rng.normal(0, 4)), 25, 400))
        observed = int(rng.integers(22, life))
        test += unit_rows(u, observed, rate)
        rul.append(str(life - observed))
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / "train_FD001.txt").write_text("\n".join(train) + "\n", encoding="ascii")
    (raw_dir / "test_FD001.txt").write_text("\n".join(test) + "\n", encoding="ascii")
    (raw_dir / "RUL_FD001.txt").write_text("\n".join(rul) + "\n", encoding="ascii")


class PipelineTests(unittest.TestCase):
    def test_end_to_end_outputs_and_determinism(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            raw = td / "raw"
            write_synthetic_cmapss(raw)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                p1 = pipeline.run_pipeline(raw, reports_dir=td / "r1", models_dir=td / "m1", subset="FD001", n_covariates=4)
                p2 = pipeline.run_pipeline(raw, reports_dir=td / "r2", models_dir=td / "m2", subset="FD001", n_covariates=4)
            # artifacts exist
            for name in ("eval_FD001.json", "eval_FD001.md"):
                self.assertTrue((td / "r1" / name).exists(), name)
            self.assertTrue((td / "m1" / "MODEL_CARD_FD001.md").exists())
            # byte-identical across runs (AC determinism)
            self.assertEqual((td / "r1" / "eval_FD001.json").read_bytes(), (td / "r2" / "eval_FD001.json").read_bytes())
            self.assertEqual(p1["validation"]["concordance"], p2["validation"]["concordance"])
            # payload contract (AC-5)
            data = json.loads((td / "r1" / "eval_FD001.json").read_text())
            for key in ("weibull", "cox", "ph_test", "selected_model", "validation", "cost_policy", "censored_scoring", "provenance"):
                self.assertIn(key, data)
            self.assertIn(data["selected_model"]["kind"], ("cox", "weibull_aft"))
            self.assertEqual(data["validation"]["horizons"], [50, 100, 150, 200, 250])
            self.assertEqual(data["cost_policy"]["cost_ratio"], 10.0)
            # censored test units scored without using RUL as a feature; truth used only for evaluation
            self.assertEqual(data["censored_scoring"]["n_units"], 12)
            self.assertIn("concordance_vs_rul_truth", data["censored_scoring"])
            # size guard AC-7
            for p in list((td / "r1").rglob("*")) + list((td / "m1").rglob("*")):
                if p.is_file():
                    self.assertLess(p.stat().st_size, 1_000_000)

    def test_signal_recovered_on_synthetic_data(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            raw = td / "raw"
            write_synthetic_cmapss(raw)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                p = pipeline.run_pipeline(raw, reports_dir=td / "r", models_dir=td / "m", subset="FD001", n_covariates=4)
            self.assertGreater(p["validation"]["concordance"], 0.6)


class CliTests(unittest.TestCase):
    def test_extract_only_txt_files(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            z = td / "a.zip"
            with zipfile.ZipFile(z, "w") as zf:
                zf.writestr("train_FD001.txt", "1 1 0 0 100 " + " ".join(["1"] * 21) + "\n")
                zf.writestr("Damage.pdf", b"%PDF-1.4 binary")
            out = td / "out"
            rc = cli.main(["extract", "--archive", str(z), "--out", str(out)])
            self.assertEqual(rc, 0)
            self.assertTrue((out / "train_FD001.txt").exists())
            self.assertFalse((out / "Damage.pdf").exists())

    def test_run_requires_raw_dir(self):
        import os

        os.environ.pop("PM_RAW_DIR", None)
        rc = cli.main(["run"])
        self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
