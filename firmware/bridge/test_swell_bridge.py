"""python3 -m unittest -v test_swell_bridge"""
import json
import os
import tempfile
import unittest
from datetime import datetime, timezone

import swell_bridge as sb


def ts(t):
    return datetime.fromtimestamp(t, timezone.utc).isoformat().replace("+00:00", "Z")


class SwellBridge(unittest.TestCase):
    now = 1_790_000_000.0

    def waves(self, age=60, underway=False, underway_age=None, period=8.04):
        t = ts(self.now - age)
        w = {"significantHeight": {"value": 1.2, "timestamp": t},
             "period": {"value": period, "timestamp": t},
             "meanPeriod": {"value": 6.1, "timestamp": t}}
        if underway is not None:
            w["underway"] = {"value": underway,
                             "timestamp": ts(self.now - (age if underway_age is None else underway_age))}
        return w

    def test_fresh_at_anchor(self):
        swell, why = sb.swell_from_waves(self.waves(), self.now)
        # t is when the WaveHat measured it, so the radar's 10 min count from there
        self.assertEqual(swell, {"t": int(self.now - 60), "hs_ft": 3.9, "period_s": 8.0})
        self.assertNotIn("from_true_deg", swell)

    def test_stale(self):
        # a WaveHat that stopped: not re-stamped as fresh
        self.assertIsNone(sb.swell_from_waves(self.waves(age=3600), self.now)[0])
        self.assertIsNone(sb.swell_from_waves(self.waves(age=11 * 60), self.now)[0])
        self.assertIsNotNone(sb.swell_from_waves(self.waves(age=9 * 60), self.now)[0])

    def test_underway(self):
        self.assertIsNone(sb.swell_from_waves(self.waves(underway=True), self.now)[0])

    def test_underway_absent(self):
        # no SOG reached the WaveHat: unknown is not "at anchor"
        self.assertIsNone(sb.swell_from_waves(self.waves(underway=None), self.now)[0])
        self.assertIsNotNone(sb.swell_from_waves(self.waves(underway=None), self.now, assume_anchored=True)[0])

    def test_underway_stale(self):
        # an old flag belongs to an earlier result: neither a stale "false" nor a stale "true" counts
        self.assertIsNone(sb.swell_from_waves(self.waves(underway=False, underway_age=3600), self.now)[0])
        self.assertIsNone(sb.swell_from_waves(self.waves(underway=True, underway_age=3600), self.now)[0])
        self.assertIsNotNone(sb.swell_from_waves(self.waves(underway=True, underway_age=3600), self.now,
                                                 assume_anchored=True)[0])

    def test_no_period(self):
        # flat calm: the WaveHat sends Tp as null; no "SWELL 0.0 ft 22 s"
        swell, why = sb.swell_from_waves(self.waves(period=None), self.now)
        self.assertIsNone(swell)
        self.assertIn("no wave period", why)

    def test_http_reasons(self):
        self.assertIn("SIGNALK_TOKEN", sb.http_reason(401))
        self.assertIn("10 minutes", sb.http_reason(404))

    def test_missing(self):
        self.assertIsNone(sb.swell_from_waves({}, self.now)[0])

    def test_atomic_write(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, ".swell.json")
            sb.write_atomic(p, {"t": 1, "hs_ft": 2.0, "period_s": 6})
            with open(p) as f:
                self.assertEqual(json.load(f)["hs_ft"], 2.0)
            self.assertEqual(os.listdir(d), [".swell.json"])


if __name__ == "__main__":
    unittest.main()
