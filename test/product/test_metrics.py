"""TASK-004 tests — metrics, deterministic report, model card (SPEC-001 §4.4)."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

import _support  # noqa: F401

from pm_survival import metrics as X
from pm_survival import report as R


class ConcordanceTests(unittest.TestCase):
    def test_perfect_and_reversed_ordering(self):
        dur = np.array([10, 20, 30, 40], dtype=float)
        ev = np.ones(4, dtype=int)
        risk_good = np.array([4.0, 3.0, 2.0, 1.0])  # higher risk ⇒ earlier failure
        self.assertAlmostEqual(X.concordance(dur, risk_good, ev), 1.0)
        self.assertAlmostEqual(X.concordance(dur, -risk_good, ev), 0.0)

    def test_censored_pairs_handled(self):
        dur = np.array([10, 20, 30], dtype=float)
        ev = np.array([1, 0, 1])
        c = X.concordance(dur, np.array([3.0, 2.0, 1.0]), ev)
        self.assertTrue(0.0 <= c <= 1.0)


class BrierTests(unittest.TestCase):
    def test_brier_without_censoring_is_mse_of_indicator(self):
        dur = np.array([10, 20, 30, 40], dtype=float)
        ev = np.ones(4, dtype=int)
        t = 25.0
        # predicted survival at t for each subject
        s = np.array([0.2, 0.4, 0.9, 0.8])
        alive = (dur > t).astype(float)  # [0,0,1,1]
        expected = float(np.mean((alive - s) ** 2))
        self.assertAlmostEqual(X.brier_score(dur, ev, s, t), expected, places=9)

    def test_brier_perfect_prediction_is_zero(self):
        dur = np.array([10, 20, 30, 40], dtype=float)
        ev = np.ones(4, dtype=int)
        t = 25.0
        s = (dur > t).astype(float)
        self.assertAlmostEqual(X.brier_score(dur, ev, s, t), 0.0, places=12)

    def test_integrated_brier_in_unit_interval_and_grid_respected(self):
        rng = np.random.default_rng(0)
        dur = rng.integers(5, 300, size=40).astype(float)
        ev = rng.integers(0, 2, size=40)
        grid = np.array([50.0, 100.0, 150.0, 200.0, 250.0])
        surv = np.clip(1 - grid[:, None] / 320.0 + rng.normal(0, 0.02, size=(5, 40)), 0, 1)
        res = X.integrated_brier(dur, ev, surv, grid)
        self.assertEqual(list(res["times"]), grid.tolist())
        self.assertEqual(len(res["brier"]), 5)
        self.assertTrue(0.0 <= res["ibs"] <= 1.0)

    def test_default_grid_is_dec012(self):
        self.assertEqual(X.DEFAULT_HORIZONS, [50, 100, 150, 200, 250])


class ReportTests(unittest.TestCase):
    def _payload(self):
        return {
            "subset": "FD001",
            "split": {"val_fraction": 0.2, "seed": 42, "n_train_units": 80, "n_val_units": 20},
            "weibull": {"shape": 4.6012345678, "scale": 222.98, "regime": "wear_out"},
            "cox": {"covariates": ["sensor_4_slope"], "coefficients": {"sensor_4_slope": 0.81}, "train_concordance": 0.765},
            "ph_test": {"holds": True, "alpha": 0.05, "p_values": {"sensor_4_slope": 0.588}, "method": "schoenfeld_rank"},
            "selected_model": {"kind": "cox", "reason": "PH assumption holds"},
            "validation": {"concordance": 0.778, "ibs": 0.12, "brier": {"50": 0.01, "100": 0.05}},
        }

    def test_eval_json_is_deterministic_and_sorted(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "eval.json"
            R.write_eval_json(p, self._payload())
            first = p.read_bytes()
            R.write_eval_json(p, self._payload())
            self.assertEqual(first, p.read_bytes())
            data = json.loads(first)
            self.assertEqual(list(data.keys()), sorted(data.keys()))
            self.assertEqual(data["weibull"]["shape"], 4.601235)  # rounded to 6 dp

    def test_eval_markdown_contains_required_sections(self):
        md = R.render_eval_markdown(self._payload())
        for needle in ("C-index", "Schoenfeld", "shape", "scale", "Selected model", "cox"):
            self.assertIn(needle, md)

    def test_model_card_lists_open_decisions_and_limitations(self):
        decisions = ["DEC-009 kernel tests assume MASTER_TEMPLATE", "DEC-007 exclude intake/sources from discover()"]
        md = R.render_model_card(self._payload(), open_decisions=decisions, limitations=["slope covariates confounded with duration"])
        for d in decisions:
            self.assertIn(d, md)  # AC-8 verbatim
        self.assertIn("slope covariates confounded", md)
        self.assertIn("not a production recommendation", md.lower())


if __name__ == "__main__":
    unittest.main()
