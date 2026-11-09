"""Tests for the wave maths (desktop reference and the C++ port).

    python3 -m unittest -v test_wavemath

Every simulation uses a fixed seed, so results are repeatable. Tolerances are
the accuracy stated in the README, measured by evaluate.py over the full
matrix; these tests check a representative subset against them.
"""

import math
import os
import shutil
import subprocess
import tempfile
import unittest

import numpy as np

import seasim as ss
import wavemath as wm

HERE = os.path.dirname(os.path.abspath(__file__))


def run(sea, seed=1, ideal=False, cfg=None, duration=1500.0, cal=ss.CALIBRATED, r_imu=(0.0, 0.0, 0.0)):
    rec = ss.simulate(sea, duration=duration, seed=seed, ideal=ideal, r_imu=r_imu, **cal)
    p = wm.WaveProcessor(cfg)
    stats, heave = p.run(rec.gyro, rec.accel)
    return rec, p, stats, heave


class Filters(unittest.TestCase):
    def test_heave_filter_double_integrates_in_band(self):
        fs = 26.0
        for f0 in (0.07, 0.1, 0.2, 0.5):
            t = np.arange(int(600 * fs)) / fs
            w = 2 * math.pi * f0
            acc = -w * w * np.cos(w * t)          # displacement cos(w t), 1 m
            chain = wm.heave_filter(fs, 0.02)
            y = np.empty_like(acc)
            for i, a in enumerate(acc):
                for b in chain:
                    a = b.step(a)
                y[i] = a
            amp = np.sqrt(2) * np.std(y[len(y) // 2:])
            self.assertAlmostEqual(amp, 1.0, delta=0.03, msg=f"{f0} Hz")

    def test_heave_filter_ignores_constant_offset(self):
        chain = wm.heave_filter(26.0, 0.02)
        y = 0.0
        for _ in range(int(1200 * 26)):
            y = 0.05
            for b in chain:
                y = b.step(y)
        self.assertLess(abs(y), 1e-3)

    def test_antialias_passes_wave_band(self):
        fs = 26.0
        for f0, want in ((0.1, 1.0), (0.5, 1.0), (3.0, 0.025)):
            t = np.arange(int(300 * fs)) / fs
            x = np.sin(2 * math.pi * f0 * t)
            chain = wm.butter4_lowpass(fs, 1.2)
            y = np.empty_like(x)
            for i, v in enumerate(x):
                for b in chain:
                    v = b.step(v)
                y[i] = v
            gain = np.sqrt(2) * np.std(y[len(y) // 2:])
            self.assertAlmostEqual(gain, want, delta=0.02, msg=f"{f0} Hz")


class Attitude(unittest.TestCase):
    def test_static_tilt_with_gyro_bias(self):
        roll, pitch = math.radians(12), math.radians(-7)
        # Board tilted: "up" in body = R^T z for R = Rx(pitch) Ry(roll)
        Rx = np.array([[1, 0, 0], [0, math.cos(pitch), -math.sin(pitch)], [0, math.sin(pitch), math.cos(pitch)]])
        Ry = np.array([[math.cos(roll), 0, math.sin(roll)], [0, 1, 0], [-math.sin(roll), 0, math.cos(roll)]])
        up = (Rx @ Ry).T @ np.array([0, 0, 1.0])
        accel = up * wm.G
        m = wm.Mahony(0.05, 0.0006, 0.25)
        bias = np.radians([0.8, -0.6, 0.3])
        for _ in range(int(600 * 26)):
            m.update(bias, accel, 1 / 26)
        self.assertLess(abs(m.vertical_accel(accel)), 1e-3)
        self.assertLess(np.linalg.norm(m.up_in_body() - up), 2e-3)

    def test_sim_gyro_is_consistent_with_its_accel(self):
        # Integrating the simulated gyro must reproduce the simulated attitude,
        # or the simulator itself is wrong.
        sea = ss.SeaState(2.0, 8.0, roll_deg=15, pitch_deg=5)
        rec = ss.simulate(sea, duration=120, seed=3, ideal=True)
        m = wm.Mahony(0.0, 0.0, 0.25)  # pure gyro integration after the first sample
        err = []
        for g, a in zip(rec.gyro, rec.accel):
            m.update(g, a, 1 / rec.fs)
            err.append(m.vertical_accel(a))
        true_av = np.gradient(np.gradient(rec.heave, 1 / rec.fs), 1 / rec.fs)
        e = np.array(err)[50:-50] - true_av[50:-50]
        self.assertLess(np.sqrt(np.mean(e ** 2)), 0.02 * np.std(true_av) + 0.01)


class Spectrum(unittest.TestCase):
    def test_single_sinusoid(self):
        # 1 m amplitude heave at 10 s on a level board: Hs = 4 sqrt(0.5) = 2.83 m
        fs = 26.0
        t = np.arange(int(1500 * fs)) / fs
        w = 2 * math.pi * 0.1
        acc = np.zeros((len(t), 3))
        acc[:, 2] = wm.G - w * w * np.cos(w * t)
        p = wm.WaveProcessor()
        stats, _ = p.run(np.zeros_like(acc), acc)
        s = stats[-1]
        self.assertAlmostEqual(s.hs, 4 * math.sqrt(0.5), delta=0.03)
        self.assertAlmostEqual(s.tp, 10.0, delta=0.15)
        self.assertAlmostEqual(s.tz, 10.0, delta=0.15)
        self.assertEqual(s.segments, 14)

    def test_window_timing(self):
        p = wm.WaveProcessor()
        self.assertAlmostEqual(p.fs_dec, 3.25)
        seg_s = p.cfg.nfft / p.fs_dec
        hop_s = p.cfg.hop / p.fs_dec
        span = seg_s + (p.cfg.window_segments - 1) * hop_s
        self.assertTrue(1150 < span < 1250, span)  # ~20 min
        self.assertAlmostEqual(p.k_lo * p.df, 0.0444, places=3)
        self.assertLessEqual(p.k_hi * p.df, 0.5)


class SeaStates(unittest.TestCase):
    """Hs within 10 %, Tp within 12 % (JONSWAP) / 20 % (broad PM) of truth."""

    CASES = [
        (ss.SeaState(1.0, 6.0), 0.10, 0.12),
        (ss.SeaState(2.5, 9.0, roll_deg=15, pitch_deg=5), 0.10, 0.12),
        (ss.SeaState(1.5, 7.0, gamma=1.0), 0.10, 0.20),
        (ss.SeaState(1.5, 14.0), 0.10, 0.12),
        (ss.SeaState(0.5, 4.0, gamma=1.0), 0.10, 0.20),
    ]

    def test_cases(self):
        for sea, hs_tol, tp_tol in self.CASES:
            with self.subTest(hs=sea.hs, tp=sea.tp, gamma=sea.gamma):
                rec, p, stats, heave = run(sea, seed=2)
                s = stats[-1]
                self.assertLess(abs(s.hs / rec.hs_true - 1), hs_tol, f"Hs {s.hs:.3f} vs {rec.hs_true:.3f}")
                self.assertLess(abs(s.tp / rec.tp_true - 1), tp_tol, f"Tp {s.tp:.2f} vs {rec.tp_true:.2f}")
                self.assertLess(abs(s.tz / rec.tz_band - 1), 0.05, f"Tz {s.tz:.2f} vs {rec.tz_band:.2f}")
                n = int(s.segments * p.cfg.hop * p.cfg.decimation)
                self.assertLess(abs(s.heave_rms_td / np.std(rec.heave[-n:]) - 1), 0.05)

    def test_instantaneous_heave_tracks_truth(self):
        # The high-pass makes heave lead the truth a little (about 20 deg at
        # 8 s), so check correlation and amplitude rather than sample error.
        rec, p, stats, heave = run(ss.SeaState(2.0, 8.0), seed=4)
        a, b = heave[13000:], rec.heave[13000:]
        self.assertGreater(np.corrcoef(a, b)[0, 1], 0.9)
        self.assertLess(abs(np.std(a) / np.std(b) - 1), 0.05)

    def test_uncalibrated_sensor_under_heavy_roll(self):
        # The worst case evaluate.py found: offset and scale error seen
        # through 15 deg RMS roll. Hs stays within 15 %.
        sea = ss.SeaState(1.0, 6.0, roll_deg=15, pitch_deg=5)
        rec, _, stats, _ = run(sea, seed=3, cal={})
        self.assertLess(abs(stats[-1].hs / rec.hs_true - 1), 0.15)

    def test_flat_calm_reads_near_zero(self):
        rec, p, stats, heave = run(ss.SeaState(0.0, 8.0, roll_deg=0, pitch_deg=0), seed=1)
        self.assertLess(stats[-1].hs, 0.02)
        # and the periods of sensor noise are not reported
        self.assertFalse(any(s.periods_valid for s in stats))

    def test_periods_valid_in_real_seas(self):
        for sea in (ss.SeaState(0.3, 3.0), ss.SeaState(0.3, 3.0, gamma=1.0), ss.SeaState(1.0, 6.0),
                    ss.SeaState(1.5, 7.0, gamma=1.0),
                    ss.SeaState(1.5, 14.0)):
            with self.subTest(hs=sea.hs, tp=sea.tp, gamma=sea.gamma):
                _, _, stats, _ = run(sea, seed=2)
                self.assertTrue(all(s.periods_valid for s in stats), [round(s.peak_ratio, 1) for s in stats])

    def test_swell_longer_than_the_band_has_no_period(self):
        # A 25 s swell peaks below the band (22.5 s): Tp would pin to the edge bin.
        _, _, stats, _ = run(ss.SeaState(1.0, 25.0), seed=1)
        self.assertFalse(stats[-1].periods_valid)

    def test_lever_arm_correction(self):
        # IMU 1 m off the centreline and 2 m forward: without the mounting
        # position Hs reads ~+30 % (lever_arm.py); with it, as at the centre.
        sea = ss.SeaState(1.0, 6.0, roll_deg=15, pitch_deg=5)
        r = (1.0, 2.0, 0.5)
        rec, _, raw, _ = run(sea, seed=3, r_imu=r)
        _, _, fixed, _ = run(sea, seed=3, r_imu=r, cfg=wm.Config(r_imu=r))
        self.assertGreater(raw[-1].hs / rec.hs_true - 1, 0.25)
        self.assertLess(abs(fixed[-1].hs / rec.hs_true - 1), 0.05)

    def test_tilt_correction_matters(self):
        sea = ss.SeaState(1.0, 6.0, roll_deg=15, pitch_deg=5)
        _, _, good, _ = run(sea, seed=1)
        _, _, bad, _ = run(sea, seed=1, cfg=wm.Config(attitude=False))
        self.assertGreater(abs(bad[-1].hs - 1.0), 3 * abs(good[-1].hs - 1.0))


@unittest.skipUnless(shutil.which("c++"), "no host C++ compiler")
class CppPort(unittest.TestCase):
    """Build lib/wavemath natively and check it against this module."""

    def test_cpp_matches_python(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = os.path.join(tmp, "wavemath_native")
            src = [os.path.join(HERE, "native", "main.cpp")]
            libdir = os.path.join(HERE, "..", "lib", "wavemath", "src")
            src += [os.path.join(libdir, f) for f in os.listdir(libdir) if f.endswith(".cpp")]
            subprocess.run(["c++", "-std=c++17", "-O2", "-Wall", "-Wextra", "-Werror", "-I", libdir,
                            "-o", exe] + src, check=True)
            for sea, seed, r in ((ss.SeaState(1.0, 6.0), 1, (0.0, 0.0, 0.0)),
                                 (ss.SeaState(2.5, 9.0, roll_deg=15, pitch_deg=5), 2, (0.8, -1.5, 0.4)),
                                 (ss.SeaState(1.5, 7.0, gamma=1.0), 3, (0.0, 0.0, 0.0)),
                                 (ss.SeaState(0.0, 8.0, roll_deg=0, pitch_deg=0), 4, (0.0, 0.0, 0.0))):
                rec = ss.simulate(sea, duration=1500.0, seed=seed, r_imu=r)
                data = os.path.join(tmp, "imu.bin")
                np.hstack([rec.gyro, rec.accel]).astype("<f4").tofile(data)
                out = subprocess.run([exe, data, str(rec.fs)] + [str(v) for v in r], check=True,
                                     capture_output=True, text=True).stdout.split()
                hs_c, tp_c, tz_c, rms_c, td_c, segs_c, valid_c, ratio_c = (float(v) for v in out[:8])
                p = wm.WaveProcessor(wm.Config(r_imu=r))
                # same float32 input as the C++ side
                stats, _ = p.run(rec.gyro.astype("<f4").astype(float),
                                 rec.accel.astype("<f4").astype(float))
                s = stats[-1]
                with self.subTest(hs=sea.hs, tp=sea.tp):
                    self.assertEqual(int(segs_c), s.segments)
                    self.assertEqual(bool(valid_c), s.periods_valid)
                    if sea.hs == 0:  # flat calm: only Hs and validity are meaningful
                        self.assertAlmostEqual(hs_c, s.hs, delta=0.002)
                        continue
                    self.assertAlmostEqual(ratio_c / s.peak_ratio, 1.0, delta=0.01)
                    self.assertAlmostEqual(hs_c / s.hs, 1.0, delta=0.002)
                    self.assertAlmostEqual(tp_c / s.tp, 1.0, delta=0.002)
                    self.assertAlmostEqual(tz_c / s.tz, 1.0, delta=0.002)
                    self.assertAlmostEqual(td_c / s.heave_rms_td, 1.0, delta=0.002)


if __name__ == "__main__":
    unittest.main()
