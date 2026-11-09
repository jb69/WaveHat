"""Lever-arm check: what an IMU mounted away from the hull's centre of rotation does to Hs.

The simulator (seasim.py) puts the IMU on the roll/pitch axis. A real box sits somewhere in the
boat, and angular acceleration about that axis then shows up as vertical acceleration at the IMU:

    a_imu = a_cg + alpha x r + w x (w x r)      (body frame; r = IMU position from the centre)

This script runs seasim with the IMU at a few positions (seasim's r_imu), and the wave maths with
and without the correction (Config.r_imu, the mounting position entered in the firmware).
Results are in results/lever_arm.md (REVIEW.md, gap G1). Run from this folder:

    python3 lever_arm.py
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seasim as ss  # noqa: E402
import wavemath as wm  # noqa: E402

def run(sea, r, seed, entered):
    """r: where the IMU really is; entered: the mounting position given to the firmware."""
    rec = ss.simulate(sea, duration=1500.0, seed=seed, r_imu=r, **ss.CALIBRATED)
    p = wm.WaveProcessor(wm.Config(r_imu=entered))
    stats, _ = p.run(rec.gyro, rec.accel)
    s = stats[-1]
    return s.hs / sea.hs - 1, s.tp / sea.tp - 1


cases = [("0.5 m 5 s roll5", ss.SeaState(0.5, 5.0)), ("1.0 m 6 s roll5", ss.SeaState(1.0, 6.0)),
         ("2.0 m 8 s roll5", ss.SeaState(2.0, 8.0)), ("1.0 m 6 s roll15", ss.SeaState(1.0, 6.0, roll_deg=15))]
# (where the IMU is, what is entered, label): the last two show a position entered 20 % short
arms = [((0, 0, 0), (0, 0, 0), "at centre"), ((0.3, 0, 0), (0.3, 0, 0), "0.3 m off centreline"),
        ((1.0, 0, 0), (1.0, 0, 0), "1 m off centreline"), ((0, 5.0, 0), (0, 5.0, 0), "5 m forward"),
        ((1.0, 5.0, 0), (1.0, 5.0, 0), "1 m off, 5 m fwd"), ((1.0, 2.0, 1.0), (1.0, 2.0, 1.0), "1 m off, 2 fwd, 1 up"),
        ((1.0, 0, 0), (0.8, 0, 0), "1 m off, 0.8 entered"), ((0, 5.0, 0), (0, 4.0, 0), "5 m fwd, 4 entered")]

if __name__ == "__main__":
    print("%-18s %-22s %21s %21s" % ("", "", "not corrected", "position entered"))
    print("%-18s %-22s %10s %10s %10s %10s" % ("sea", "IMU position", "Hs err", "Tp err", "Hs err", "Tp err"))
    for name, sea in cases:
        for r, entered, label in arms:
            row = []
            for given in ((0.0, 0.0, 0.0), entered):
                e = [run(sea, r, seed, given) for seed in (1, 2)]
                row += [100 * np.mean([x[0] for x in e]), 100 * np.mean([x[1] for x in e])]
            print("%-18s %-22s %+9.1f%% %+9.1f%% %+9.1f%% %+9.1f%%" % (name, label, *row))
