"""TASK-002 tests — survival table, right-censoring, grouped split (SPEC-001 §4.2)."""
from __future__ import annotations

import unittest

import _support  # noqa: F401
from _support import FIXTURES, FIXTURE_PREFIX

from pm_survival import data as D
from pm_survival import events as E
from pm_survival import split as S


def _load():
    train = D.load_fd(FIXTURES, "FD001", "train", prefix=FIXTURE_PREFIX)
    test = D.load_fd(FIXTURES, "FD001", "test", prefix=FIXTURE_PREFIX)
    rul = D.load_rul(FIXTURES, "FD001", prefix=FIXTURE_PREFIX)
    return train, test, rul


class SurvivalTableTests(unittest.TestCase):
    def test_train_units_are_events_at_last_cycle(self):
        train, _, _ = _load()
        tbl = E.build_survival_table(train, censored=False)
        self.assertEqual(len(tbl), 3)  # AC-3 analogue on fixture
        self.assertTrue((tbl["event"] == 1).all())
        expected = train.groupby("unit_id")["cycle"].max()
        self.assertEqual(tbl.set_index("unit_id")["duration"].to_dict(), expected.to_dict())

    def test_test_units_are_right_censored(self):
        _, test, _ = _load()
        tbl = E.build_survival_table(test, censored=True)
        self.assertTrue((tbl["event"] == 0).all())  # AC-4
        self.assertEqual(tbl.set_index("unit_id")["duration"].to_dict(), {1: 30, 2: 20})

    def test_rul_truth_never_in_features(self):
        _, test, rul = _load()
        tbl = E.build_survival_table(test, censored=True)
        feats = E.feature_columns(tbl)
        self.assertNotIn("rul_true", feats)
        self.assertNotIn("duration", feats)
        self.assertNotIn("event", feats)
        self.assertNotIn("unit_id", feats)
        # attach_rul_truth is explicit and keeps it out of feature_columns
        joined = E.attach_rul_truth(tbl, rul)
        self.assertEqual(joined.set_index("unit_id")["rul_true"].to_dict(), {1: 25, 2: 40})
        self.assertNotIn("rul_true", E.feature_columns(joined))

    def test_summary_covariates_use_early_life_window_only(self):
        train, _, _ = _load()
        tbl = E.build_survival_table(train, censored=False, early_window=10)
        # early-life mean of sensor_2 for unit 1 must equal mean over cycles 1..10 only
        u1 = train[(train.unit_id == 1) & (train.cycle <= 10)]["sensor_2"].mean()
        self.assertAlmostEqual(tbl.set_index("unit_id").loc[1, "sensor_2_early"], u1, places=9)
        # and the slope covariate exists
        self.assertIn("sensor_2_slope", tbl.columns)

    def test_constant_sensors_are_dropped_from_features(self):
        train, _, _ = _load()
        tbl = E.build_survival_table(train, censored=False)
        feats = E.feature_columns(tbl)
        # op_setting_3 is constant (100.0) in the fixture → must not be a feature
        self.assertFalse(any(f.startswith("op_setting_3") for f in feats))

    def test_long_format_counting_process(self):
        train, _, _ = _load()
        long = E.build_long_format(train)
        self.assertEqual(list(long.columns[:5]), ["unit_id", "start", "stop", "event", "cycle"])
        u1 = long[long.unit_id == 1]
        self.assertEqual(u1["event"].sum(), 1)
        self.assertEqual(int(u1["event"].iloc[-1]), 1)
        self.assertTrue((u1["stop"] - u1["start"] == 1).all())


class GroupedSplitTests(unittest.TestCase):
    def test_no_unit_in_both_partitions_and_deterministic(self):
        train, _, _ = _load()
        tbl = E.build_survival_table(train, censored=False)
        a_tr, a_va = S.grouped_unit_split(tbl, val_fraction=0.34, seed=11)
        b_tr, b_va = S.grouped_unit_split(tbl, val_fraction=0.34, seed=11)
        self.assertEqual(set(a_tr.unit_id) & set(a_va.unit_id), set())
        self.assertEqual(len(a_tr) + len(a_va), len(tbl))
        self.assertEqual(a_va.unit_id.tolist(), b_va.unit_id.tolist())
        self.assertGreaterEqual(len(a_va), 1)

    def test_split_on_raw_rows_keeps_units_intact(self):
        train, _, _ = _load()
        tr, va = S.grouped_unit_split(train, val_fraction=0.34, seed=3)
        self.assertEqual(set(tr.unit_id) & set(va.unit_id), set())
        for u in va.unit_id.unique():
            self.assertEqual(len(va[va.unit_id == u]), len(train[train.unit_id == u]))


if __name__ == "__main__":
    unittest.main()
