"""SPEC-003 tests: landmark features (no leakage), policy arithmetic, Holm, end-to-end study."""

from __future__ import annotations

import _support  # noqa: F401  (puts src/ on sys.path)
import numpy as np
import pandas as pd
import pytest

from pm_survival import landmark as L
from pm_survival import policies as P
from pm_survival import study as St
from pm_survival.data import COLUMNS, SENSORS


def synthetic_fleet(n_units: int = 24, seed: int = 0, truncate: bool = False) -> tuple[pd.DataFrame, np.ndarray]:
    """C-MAPSS-shaped engines whose sensors drift as failure approaches."""
    rng = np.random.default_rng(seed)
    rows, rul = [], []
    for u in range(1, n_units + 1):
        life = int(rng.integers(120, 260))
        last = int(rng.integers(40, life - 5)) if truncate else life
        rul.append(life - last)
        for c in range(1, last + 1):
            wear = np.exp((c - life) / 25.0)
            row = [u, c, 0.0, 0.0, 100.0]
            for i, _ in enumerate(SENSORS):
                base = 500.0 + 10 * i
                row.append(base + (5.0 * wear if i % 2 == 0 else 0.0) + rng.normal(0, 0.3))
            rows.append(row)
    return pd.DataFrame(rows, columns=COLUMNS), np.array(rul)


def _write_raw(tmp_path, n_train=24, n_test=12):
    train, _ = synthetic_fleet(n_train, seed=1)
    test, rul = synthetic_fleet(n_test, seed=2, truncate=True)
    for name, df in (("train_FD001.txt", train), ("test_FD001.txt", test)):
        df.to_csv(tmp_path / name, sep=" ", header=False, index=False)
    pd.Series(rul).to_csv(tmp_path / "RUL_FD001.txt", header=False, index=False)
    return tmp_path


# ------------------------------------------------------------------ landmark features
def test_features_at_c_ignore_future_cycles():
    raw, _ = synthetic_fleet(3, seed=3)
    sensors = L.informative_sensors(raw)
    before = L.rolling_features(raw, sensors).set_index(["unit_id", "cycle"])
    tampered = raw.copy()
    tampered.loc[tampered["cycle"] > 60, sensors] += 1e6  # rewrite the future
    after = L.rolling_features(tampered, sensors).set_index(["unit_id", "cycle"])
    idx = before.index[before.index.get_level_values("cycle") <= 60]
    pd.testing.assert_frame_equal(before.loc[idx], after.loc[idx])


def test_rolling_slope_and_mean_on_a_line():
    cycles = np.arange(1, 41)
    raw = pd.DataFrame({"unit_id": 1, "cycle": cycles, "sensor_2": 3.0 + 0.5 * cycles})
    f = L.rolling_features(raw, ["sensor_2"], window=10).set_index("cycle")
    assert f.loc[30, "sensor_2_slope"] == pytest.approx(0.5)
    assert f.loc[30, "sensor_2_mean"] == pytest.approx(3.0 + 0.5 * np.mean(np.arange(21, 31)))


def test_landmark_table_targets_and_weights():
    raw, _ = synthetic_fleet(4, seed=4)
    sensors = L.informative_sensors(raw)
    tbl = L.landmark_table(raw, sensors, window=20, step=5, start=20)
    life = raw.groupby("unit_id")["cycle"].max()
    assert (tbl["cycle"] < tbl["unit_id"].map(life)).all()
    assert np.allclose(tbl["residual"], tbl["unit_id"].map(life) - tbl["cycle"])
    assert ((tbl["cycle"] - 20) % 5 == 0).all()
    assert np.allclose(tbl.groupby("unit_id")["weight"].sum(), 1.0)


def test_landmark_model_ranks_closer_failures_higher():
    raw, _ = synthetic_fleet(20, seed=5)
    sensors = L.informative_sensors(raw)
    tbl = L.landmark_table(raw, sensors)
    model = L.fit_landmark(tbl, L.feature_names(sensors))
    from lifelines.utils import concordance_index

    assert concordance_index(tbl["residual"], model.median_residual(tbl)) > 0.8


def test_age_only_baseline_is_conditional_median():
    lives = np.array([100, 200, 300])
    assert L.age_only_median_residual(lives, np.array([150]))[0] == pytest.approx(100.0)  # alive: 200, 300 → 50, 150


# ------------------------------------------------------------------ policies
def test_outcomes_and_cost_rate():
    out = P.outcomes(np.array([100, 200]), np.array([80, np.inf]), ratio=10)
    assert out["cost"].tolist() == [1.0, 10.0]
    assert out["length"].tolist() == [80.0, 200.0]
    s = P.summarise("x", out)
    assert s.cost_per_1000_cycles == pytest.approx(1000 * 11 / 280)
    assert s.failures == 1 and s.preventive == 1
    assert s.mean_wasted_cycles == pytest.approx(20.0)


def test_condition_replacement_takes_first_alarm():
    pred = pd.DataFrame({"unit_id": [1, 1, 1, 2, 2], "cycle": [20, 25, 30, 20, 25], "p_fail": [0.1, 0.6, 0.9, 0.1, 0.2]})
    rep = P.condition_replacement(pred, 0.5)
    assert rep.loc[1] == 25 and np.isinf(rep.loc[2])


def test_tuned_threshold_avoids_failures_when_failure_is_expensive():
    pred = pd.DataFrame(
        {"unit_id": [1, 1, 1, 2, 2, 2], "cycle": [20, 25, 30, 20, 25, 30], "p_fail": [0.05, 0.2, 0.7, 0.05, 0.3, 0.8]}
    )
    life = pd.Series({1: 33.0, 2: 34.0})
    thr = P.tune_threshold(pred, life, ratio=100)
    rep = P.condition_replacement(pred, thr)
    assert (rep < life).all()


def test_bootstrap_difference_sign():
    a = pd.DataFrame({"cost": [1.0] * 30, "length": [100.0] * 30})
    b = pd.DataFrame({"cost": [10.0] * 30, "length": [150.0] * 30})
    r = P.bootstrap_difference(a, b, n_boot=200)
    assert r["diff"] < 0 and r["ci_high"] < 0 and r["p_a_better"] == 1.0


def test_holm_adjustment():
    h = St.holm({"a": 0.01, "b": 0.04, "c": 0.5})
    assert h["adjusted"]["a"] == pytest.approx(0.03)
    assert h["adjusted"]["b"] == pytest.approx(0.08)
    assert h["adjusted"]["c"] == pytest.approx(0.5)
    assert h["holds"] is False


# ------------------------------------------------------------------ end to end
def test_study_runs_end_to_end_on_synthetic_engines(tmp_path):
    raw_dir = _write_raw(tmp_path)
    res = St.run_study(raw_dir, St.StudyConfig(n_folds=3, n_repeats=1, inner_folds=2, n_boot=50))
    assert set(res["test"]["metrics"]) >= {"landmark", "age_only"}
    pol = pd.DataFrame(res["policies"])
    assert set(pol["policy"]) == {"run_to_failure", "age", "condition", "oracle"}
    rtf = pol[pol["policy"] == "run_to_failure"]
    assert (rtf["failures"] == rtf["n_engines"]).all()
    paths = St.write_outputs(res, tmp_path / "reports", tmp_path / "demo")
    assert (tmp_path / "reports" / "landmark_FD001.md").exists()
    assert {"policy_by_ratio.csv", "fleet_now.csv", "thresholds.json"} <= {p.name for p in (tmp_path / "demo").iterdir()}
    assert paths["demo"]
