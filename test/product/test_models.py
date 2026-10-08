"""TASK-003 tests — Weibull + Cox baselines, PH assumption check, fallback (SPEC-001 §4.3).

Uses a seeded synthetic survival table (no files, no network) so that the
statistical behaviour is deterministic and quick.
"""
from __future__ import annotations

import unittest
import warnings

import numpy as np
import pandas as pd

import _support  # noqa: F401

from pm_survival import models as M


def simulate(n: int = 120, shape: float = 3.0, scale: float = 200.0, seed: int = 5, censor_frac: float = 0.2) -> pd.DataFrame:
    """Weibull durations with one covariate (x1) accelerating failure; x2 is noise."""
    rng = np.random.default_rng(seed)
    x1 = rng.normal(size=n)
    x2 = rng.normal(size=n)
    # AFT-style: scale shrinks when x1 is high
    unit_scale = scale * np.exp(-0.35 * x1)
    t = unit_scale * rng.weibull(shape, size=n)
    event = np.ones(n, dtype=int)
    k = int(censor_frac * n)
    idx = rng.choice(n, size=k, replace=False)
    t[idx] = t[idx] * rng.uniform(0.3, 0.9, size=k)
    event[idx] = 0
    return pd.DataFrame(
        {
            "unit_id": np.arange(1, n + 1),
            "duration": np.maximum(1, np.round(t)).astype(int),
            "event": event,
            "x1_early": x1,
            "x2_early": x2,
            "x3_slope": rng.normal(size=n) * 1e-3,
        }
    )


class WeibullTests(unittest.TestCase):
    def test_fit_recovers_shape_and_is_reproducible(self):
        tbl = simulate()
        a = M.fit_weibull(tbl)
        b = M.fit_weibull(tbl)
        self.assertTrue(np.isfinite(a.shape) and np.isfinite(a.scale))
        self.assertEqual((a.shape, a.scale), (b.shape, b.scale))
        self.assertGreater(a.shape, 1.5)  # wear-out regime detected
        self.assertEqual(a.regime, "wear_out")

    def test_regime_labels(self):
        self.assertEqual(M.weibull_regime(0.7), "infant_mortality")
        self.assertEqual(M.weibull_regime(1.0), "random")
        self.assertEqual(M.weibull_regime(2.5), "wear_out")

    def test_survival_function_monotone(self):
        w = M.fit_weibull(simulate())
        t = np.array([10.0, 100.0, 200.0, 400.0])
        s = w.survival(t)
        self.assertTrue(np.all(np.diff(s) <= 0))
        self.assertAlmostEqual(float(w.survival(np.array([0.0]))[0]), 1.0, places=9)


class CovariateSelectionTests(unittest.TestCase):
    def test_select_top_k_prefers_informative_covariate(self):
        tbl = simulate()
        chosen = M.select_covariates(tbl, k=2)
        self.assertEqual(len(chosen), 2)
        self.assertIn("x1_early", chosen)

    def test_k_capped_by_available_features(self):
        tbl = simulate()
        self.assertEqual(len(M.select_covariates(tbl, k=50)), 3)


class CoxTests(unittest.TestCase):
    def test_fit_cox_finds_positive_hazard_for_x1(self):
        tbl = simulate()
        cox = M.fit_cox(tbl, covariates=["x1_early", "x2_early"])
        self.assertGreater(cox.coefficients["x1_early"], 0.0)
        self.assertGreater(cox.train_concordance, 0.6)
        self.assertEqual(cox.covariates, ["x1_early", "x2_early"])

    def test_check_ph_structure(self):
        tbl = simulate()
        cox = M.fit_cox(tbl, covariates=["x1_early", "x2_early"])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            ph = M.check_ph(cox, tbl)
        self.assertEqual(set(ph.p_values), {"x1_early", "x2_early"})
        self.assertTrue(all(0.0 <= p <= 1.0 for p in ph.p_values.values()))
        self.assertIsInstance(ph.holds, bool)
        self.assertEqual(ph.alpha, 0.05)

    def test_predict_survival_shape(self):
        tbl = simulate()
        cox = M.fit_cox(tbl, covariates=["x1_early"])
        times = np.array([50.0, 150.0])
        s = cox.survival(tbl.head(4), times)
        self.assertEqual(s.shape, (2, 4))
        self.assertTrue(np.all(s[0] >= s[1]))


class SelectionTests(unittest.TestCase):
    def test_select_model_keeps_cox_when_ph_holds(self):
        tbl = simulate()
        ph = M.PHResult(p_values={"x1_early": 0.4}, holds=True, alpha=0.05, method="schoenfeld_rank")
        sel = M.select_model(tbl, ["x1_early"], ph)
        self.assertEqual(sel.kind, "cox")
        self.assertIn("PH assumption holds", sel.reason)

    def test_select_model_falls_back_to_aft_when_ph_fails(self):
        tbl = simulate()
        ph = M.PHResult(p_values={"x1_early": 0.001}, holds=False, alpha=0.05, method="schoenfeld_rank")
        sel = M.select_model(tbl, ["x1_early"], ph)
        self.assertEqual(sel.kind, "weibull_aft")
        self.assertIn("violated", sel.reason)
        s = sel.model.survival(tbl.head(3), np.array([100.0, 200.0]))
        self.assertEqual(s.shape, (2, 3))


if __name__ == "__main__":
    unittest.main()
