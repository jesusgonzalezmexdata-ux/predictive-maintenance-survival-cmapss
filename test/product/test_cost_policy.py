"""TASK-005 tests — cost-optimal preventive replacement (SPEC-001 §4.5, AC-6)."""
from __future__ import annotations

import unittest

import _support  # noqa: F401
import numpy as np

from pm_survival import cost_policy as C
from pm_survival.models import WeibullResult


def weibull(shape: float, scale: float = 200.0) -> WeibullResult:
    return WeibullResult(shape=shape, scale=scale, regime="x", n=0, n_events=0)


class CostRateTests(unittest.TestCase):
    def test_cost_rate_formula_matches_manual_computation(self):
        def R(t):  # Weibull β=2, λ=100
            return np.exp(-(np.asarray(t, float) / 100.0) ** 2.0)

        t = 50.0
        cp, cf = 1.0, 10.0
        grid = np.linspace(0, t, 20001)
        integral = np.trapezoid(R(grid), grid)
        expected = (cp * R(t) + cf * (1 - R(t))) / integral
        self.assertAlmostEqual(C.expected_cost_rate(t, cp, cf, R), expected, places=6)

    def test_rejects_invalid_costs(self):
        R = weibull(3.0).survival
        with self.assertRaises(ValueError):
            C.optimal_time(0.0, 10.0, R)
        with self.assertRaises(ValueError):
            C.optimal_time(10.0, 5.0, R)  # Cf must exceed Cp for preventive maintenance to make sense


class OptimalTimeTests(unittest.TestCase):
    def test_wear_out_gives_finite_interior_optimum(self):
        R = weibull(4.0, 200.0).survival
        res = C.optimal_time(1.0, 10.0, R, horizon=600.0)
        self.assertTrue(np.isfinite(res.t_star))
        self.assertGreater(res.t_star, 0.0)
        self.assertLess(res.t_star, 200.0)  # replace before characteristic life when failures are 10x costlier
        self.assertTrue(0.0 < res.reliability_at_t_star < 1.0)

    def test_higher_cost_ratio_moves_t_star_earlier(self):
        R = weibull(4.0, 200.0).survival
        t_low = C.optimal_time(1.0, 3.0, R, horizon=600.0).t_star
        t_high = C.optimal_time(1.0, 30.0, R, horizon=600.0).t_star
        self.assertLess(t_high, t_low)  # AC-6

    def test_ratio_near_one_pushes_t_star_to_horizon(self):
        R = weibull(4.0, 200.0).survival
        res = C.optimal_time(1.0, 1.0001, R, horizon=600.0)
        self.assertGreaterEqual(res.t_star, 0.95 * 600.0)  # AC-6: run-to-failure is optimal
        self.assertTrue(res.at_horizon)

    def test_random_failures_have_no_interior_optimum(self):
        # β = 1 (exponential): preventive replacement never pays off ⇒ optimum at horizon.
        R = weibull(1.0, 200.0).survival
        res = C.optimal_time(1.0, 10.0, R, horizon=1000.0)
        self.assertTrue(res.at_horizon)

    def test_tabulated_reliability_supported(self):
        t_tab = np.linspace(0, 600, 601)
        r_tab = weibull(4.0, 200.0).survival(t_tab)
        R = C.tabulated_reliability(t_tab, r_tab)
        res_tab = C.optimal_time(1.0, 10.0, R, horizon=600.0)
        res_ref = C.optimal_time(1.0, 10.0, weibull(4.0, 200.0).survival, horizon=600.0)
        self.assertAlmostEqual(res_tab.t_star, res_ref.t_star, delta=2.0)

    def test_result_is_serialisable(self):
        res = C.optimal_time(1.0, 10.0, weibull(4.0).survival, horizon=600.0)
        d = res.to_dict()
        for k in ("t_star", "cost_rate_at_t_star", "reliability_at_t_star", "cost_ratio", "at_horizon"):
            self.assertIn(k, d)
        self.assertEqual(d["cost_ratio"], 10.0)


if __name__ == "__main__":
    unittest.main()
