"""SPEC-002 — local explicability and taxonomy presence."""
from __future__ import annotations

import unittest
from pathlib import Path

import _support  # noqa: F401
from _support import FIXTURE_PREFIX, FIXTURES

from pm_survival import data as D
from pm_survival import decision as Db
from pm_survival import events as E
from pm_survival import explain as X
from pm_survival import models as M

ROOT = Path(__file__).resolve().parents[2]


class TaxonomyTests(unittest.TestCase):
    def test_taxonomy_file_exists_and_maps_l2(self):
        path = ROOT / "docs" / "taxonomy.md"
        self.assertTrue(path.exists())
        text = path.read_text(encoding="utf-8")
        for needle in ("L2-T", "C-MAPSS", "sensor_4", "censura", "etiqueta"):
            self.assertIn(needle, text)
        self.assertIn("no", text.lower())


class ExplainTests(unittest.TestCase):
    def test_contributions_sum_to_100_and_headline_in_spanish(self):
        train = D.load_fd(FIXTURES, "FD001", "train", prefix=FIXTURE_PREFIX)
        tbl = E.build_survival_table(train, censored=False, early_window=10)
        covariates = M.select_covariates(tbl, k=3)
        model = M.fit_cox(tbl, covariates)
        exp = X.explain_asset(model, tbl.head(1), top_k=3)
        self.assertEqual(exp.unit_id, int(tbl.iloc[0]["unit_id"]))
        self.assertAlmostEqual(sum(d.pct_of_abs for d in exp.drivers), 100.0, places=0)
        self.assertIn("activo", exp.headline.lower())
        self.assertIn("riesgo", exp.headline.lower())
        frame = X.explanation_frame(exp)
        self.assertIn("peso_%", frame.columns)
        self.assertIn("impacto", frame.columns)


class DecisionTests(unittest.TestCase):
    def test_intervention_message_mentions_cost_ratio(self):
        train = D.load_fd(FIXTURES, "FD001", "train", prefix=FIXTURE_PREFIX)
        tbl = E.build_survival_table(train, censored=False, early_window=10)
        weib = M.fit_weibull(tbl)
        cost = Db.recompute_cost(weib, 1.0, 10.0)
        msg = Db.intervention_message(cost)
        self.assertIn("C_f / C_p", msg)
        self.assertTrue("intervención" in msg or "operar" in msg)


if __name__ == "__main__":
    unittest.main()
