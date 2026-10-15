import unittest

import _support  # noqa: F401
from _support import FIXTURE_PREFIX, FIXTURES

from pm_survival import data as D
from pm_survival import landmark as L
from pm_survival import monitoring as MON


class MonitoringTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = D.load_fd(FIXTURES, "FD001", "train", prefix=FIXTURE_PREFIX)
        cls.sensors = L.informative_sensors(cls.raw, min_unique=5)
        cls.ref = MON.build_reference(cls.raw, cls.sensors)

    def test_same_data_is_ok(self):
        report = MON.drift_report(self.ref, self.raw)
        self.assertEqual(report["status"], "OK")

    def test_shifted_sensor_raises_drift_alert(self):
        s = self.sensors[0]
        shifted = self.raw.copy()
        shifted[s] = shifted[s] + 5 * self.raw[s].std()
        report = MON.drift_report(self.ref, shifted)
        self.assertEqual(report["status"], "ALERT")
        self.assertIn(s, report["psi_major"])
        self.assertIn(s, report["out_of_range"])

    def test_frozen_sensor_is_flagged(self):
        s = self.sensors[1]
        frozen = self.raw.copy()
        frozen[s] = frozen[s].median()
        report = MON.drift_report(self.ref, frozen)
        self.assertIn(s, report["frozen"])
        self.assertEqual(report["status"], "ALERT")

    def test_psi_is_zero_for_identical_distributions(self):
        self.assertEqual(MON.psi([0.5, 0.5], [0.5, 0.5]), 0.0)


if __name__ == "__main__":
    unittest.main()
