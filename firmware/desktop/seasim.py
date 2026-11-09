"""Synthetic sea states and a simulated LSM6DSO for testing the wave maths.

A sea surface is built as a sum of many random-phase sinusoids drawn from a
JONSWAP spectrum (gamma = 1 gives Pierson-Moskowitz) with a known Hs and Tp.
The simulated boat follows the surface vertically (heave RAO = 1, i.e. we test
the maths, not the hull), is carried by the orbital motion horizontally,
rolls and pitches on the wave slope with a roll resonance, and yaws slowly
around its anchor. The IMU then sees specific force and body rates in the
board frame (X starboard, Y bow, Z up), plus:

  * white noise at the LSM6DSO datasheet noise densities (DS12140, high-
    performance mode): 75 ug/sqrt(Hz) at +-4 g, 3.8 mdps/sqrt(Hz), over the
    ODR/2 bandwidth;
  * a fixed bias per axis, uniform within +-20 mg and +-1 dps (typical zero-g
    and zero-rate offsets);
  * a fixed scale error per accelerometer axis, uniform within +-1 % (assumed);
  * or, with CALIBRATED, what is left after the six-face calibration in the
    README: +-2 mg and +-0.2 % (the gyro bias is tracked by the filter);
  * the board mounted 3 degrees off level;
  * optionally (r_imu), the board away from the hull's roll/pitch centre, so it
    also feels alpha x r + w x (w x r);
  * quantisation to 0.122 mg and 17.5 mdps per LSB (+-4 g, +-500 dps).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

G = 9.80665

ACC_NOISE_DENSITY = 75e-6 * G            # m/s^2/sqrt(Hz)  (+-4 g range)
GYRO_NOISE_DENSITY = np.radians(3.8e-3)  # rad/s/sqrt(Hz)
ACC_BIAS = 0.020 * G                     # m/s^2, +- per axis
GYRO_BIAS = np.radians(1.0)              # rad/s, +- per axis
ACC_SCALE = 0.01                         # +- per axis
CALIBRATED = dict(acc_bias=0.002 * G, acc_scale=0.002)  # after six-face calibration
ACC_LSB = 0.122e-3 * G
GYRO_LSB = np.radians(17.5e-3)


def jonswap(f, hs, tp, gamma=3.3):
    """JONSWAP spectral shape, normalised later to the requested Hs."""
    fp = 1.0 / tp
    sigma = np.where(f <= fp, 0.07, 0.09)
    r = np.exp(-((f - fp) ** 2) / (2.0 * sigma ** 2 * fp ** 2))
    return f ** -5.0 * np.exp(-1.25 * (fp / f) ** 4) * gamma ** r


@dataclass
class SeaState:
    hs: float
    tp: float
    gamma: float = 3.3        # 1.0 = Pierson-Moskowitz
    roll_deg: float = 5.0     # RMS roll
    pitch_deg: float = 2.0    # RMS pitch
    roll_period: float = 5.0  # s, natural roll period of the hull
    wave_dir_deg: float = 60.0  # waves arrive this far off the bow
    orbital: float = 0.7      # fraction of orbital horizontal motion followed
    label: str = ""


@dataclass
class ImuRecord:
    t: np.ndarray
    accel: np.ndarray      # N x 3, m/s^2, body frame
    gyro: np.ndarray       # N x 3, rad/s, body frame
    heave: np.ndarray      # N, true vertical displacement, m
    hs_true: float         # 4 sqrt(m0) of the whole simulated spectrum
    hs_band: float         # 4 sqrt(m0) of the 0.04-0.5 Hz part only
    tz_true: float
    tz_band: float         # Tz of the 0.04-0.5 Hz part only
    tp_true: float
    fs: float


def _rot_x(a):
    c, s = np.cos(a), np.sin(a)
    o, z = np.ones_like(a), np.zeros_like(a)
    return np.stack([np.stack([o, z, z], -1),
                     np.stack([z, c, -s], -1),
                     np.stack([z, s, c], -1)], -2)


def _rot_y(a):
    c, s = np.cos(a), np.sin(a)
    o, z = np.ones_like(a), np.zeros_like(a)
    return np.stack([np.stack([c, z, s], -1),
                     np.stack([z, o, z], -1),
                     np.stack([-s, z, c], -1)], -2)


def _rot_z(a):
    c, s = np.cos(a), np.sin(a)
    o, z = np.ones_like(a), np.zeros_like(a)
    return np.stack([np.stack([c, -s, z], -1),
                     np.stack([s, c, z], -1),
                     np.stack([z, z, o], -1)], -2)


def simulate(sea: SeaState, duration=1800.0, fs=26.0, seed=0, ideal=False,
             f_min=0.02, f_max=1.0, n_comp=600, acc_bias=ACC_BIAS, acc_scale=ACC_SCALE,
             r_imu=(0.0, 0.0, 0.0)) -> ImuRecord:
    """Simulate `duration` seconds of IMU data at `fs` for one sea state.

    ideal=True switches off every sensor error (noise, bias, scale, mount
    tilt, quantisation) to separate algorithm error from sensor error.
    acc_bias / acc_scale set the +- range of the accelerometer offset (m/s^2)
    and per-axis scale error; pass **CALIBRATED for a calibrated board.
    r_imu: the IMU's position from the roll/pitch centre, m, board frame
    (X starboard, Y bow, Z up); the truth (heave, Hs) stays the centre's.
    """
    rng = np.random.default_rng(seed)
    t = np.arange(int(duration * fs)) / fs

    # Wave components: one random frequency in each of n_comp equal bins.
    edges = np.linspace(f_min, f_max, n_comp + 1)
    df = np.diff(edges)
    f = edges[:-1] + rng.uniform(0, 1, n_comp) * df
    S = jonswap(f, sea.hs, sea.tp, sea.gamma)
    S *= (sea.hs / 4.0) ** 2 / np.sum(S * df)
    amp = np.sqrt(2.0 * S * df)
    phase = rng.uniform(0, 2 * np.pi, n_comp)
    w = 2 * np.pi * f
    k = w ** 2 / G  # deep-water wavenumber

    # Roll / pitch transfer from wave slope (k a), roll has a resonance.
    beta = np.radians(sea.wave_dir_deg)
    r = f * sea.roll_period
    h_roll = np.sin(beta) / (1 - r ** 2 + 2j * 0.15 * r)
    h_pitch = np.cos(beta) / (1 + 1j * f / 0.3)
    slope = k * amp

    heave = np.zeros_like(t)
    acc_v = np.zeros_like(t)
    acc_h = np.zeros_like(t)
    roll = np.zeros_like(t)
    roll_d = np.zeros_like(t)
    pitch = np.zeros_like(t)
    pitch_d = np.zeros_like(t)
    for i in range(n_comp):
        th = w[i] * t + phase[i]
        c, s = np.cos(th), np.sin(th)
        heave += amp[i] * c
        acc_v -= amp[i] * w[i] ** 2 * c
        acc_h -= sea.orbital * amp[i] * w[i] ** 2 * s
        # slope ~ -k a sin(th); complex gain applied to e^{i th}
        zr = slope[i] * h_roll[i] * (-1j) * np.exp(1j * th)
        zp = slope[i] * h_pitch[i] * (-1j) * np.exp(1j * th)
        roll += zr.real
        roll_d += (1j * w[i] * zr).real
        pitch += zp.real
        pitch_d += (1j * w[i] * zp).real

    def scale_to(x, xd, rms_deg):
        if rms_deg <= 0 or np.std(x) == 0:
            return x * 0, xd * 0
        g = np.radians(rms_deg) / np.std(x)
        return x * g, xd * g

    roll, roll_d = scale_to(roll, roll_d, sea.roll_deg)
    pitch, pitch_d = scale_to(pitch, pitch_d, sea.pitch_deg)

    # Slow yaw around the anchor plus a little wave-frequency yaw.
    yp = rng.uniform(0, 2 * np.pi, 2)
    yaw = (np.radians(10) * np.sin(2 * np.pi * t / 90 + yp[0])
           + np.radians(1) * np.sin(2 * np.pi * t / sea.tp + yp[1]))
    yaw_d = (np.radians(10) * 2 * np.pi / 90 * np.cos(2 * np.pi * t / 90 + yp[0])
             + np.radians(1) * 2 * np.pi / sea.tp * np.cos(2 * np.pi * t / sea.tp + yp[1]))

    # Mount tilt: the board is not quite level in the hull.
    mount = np.eye(3)
    if not ideal:
        mount = (_rot_x(np.array(np.radians(2.0))) @ _rot_y(np.array(np.radians(-2.2))))

    # Orientation body->earth: R = Rz(yaw) Rx(pitch) Ry(roll) (hull), then mount.
    Rz, Rx, Ry = _rot_z(yaw), _rot_x(pitch), _rot_y(roll)
    R_hull = Rz @ Rx @ Ry
    # Body rates of the hull: w = Ry^T Rx^T [0,0,yaw'] + Ry^T [pitch',0,0] + [0,roll',0]
    z3 = np.zeros_like(t)
    w_hull = (np.einsum("nji,nj->ni", Ry, np.einsum("nji,nj->ni", Rx, np.stack([z3, z3, yaw_d], -1)))
              + np.einsum("nji,nj->ni", Ry, np.stack([pitch_d, z3, z3], -1))
              + np.stack([z3, roll_d, z3], -1))
    R = R_hull @ mount
    gyro = w_hull @ mount  # (mount^T w) for each row

    a_earth = np.stack([acc_h * np.cos(beta), acc_h * np.sin(beta), acc_v], -1)
    f_earth = a_earth + np.array([0.0, 0.0, G])
    accel = np.einsum("nji,nj->ni", R, f_earth)  # R^T f
    r = np.asarray(r_imu, dtype=float)
    if np.any(r):
        alpha = np.gradient(gyro, 1.0 / fs, axis=0)
        accel = accel + np.cross(alpha, r) + np.cross(gyro, np.cross(gyro, r))

    if not ideal:
        n = len(t)
        bw = np.sqrt(fs / 2.0)
        accel = accel * (1 + rng.uniform(-1, 1, 3) * acc_scale)
        accel = accel + rng.uniform(-1, 1, 3) * acc_bias
        accel = accel + rng.normal(0, ACC_NOISE_DENSITY * bw, (n, 3))
        gyro = gyro + rng.uniform(-GYRO_BIAS, GYRO_BIAS, 3)
        gyro = gyro + rng.normal(0, GYRO_NOISE_DENSITY * bw, (n, 3))
        accel = np.round(accel / ACC_LSB) * ACC_LSB
        gyro = np.round(gyro / GYRO_LSB) * GYRO_LSB

    band = (f >= 0.04) & (f <= 0.5)
    m0 = np.sum(amp ** 2) / 2
    m2 = np.sum(amp ** 2 * f ** 2) / 2
    return ImuRecord(t=t, accel=accel, gyro=gyro, heave=heave,
                     hs_true=4 * np.sqrt(m0),
                     hs_band=4 * np.sqrt(np.sum(amp[band] ** 2) / 2),
                     tz_true=np.sqrt(m0 / m2) if m2 > 0 else np.nan,
                     tz_band=(np.sqrt(np.sum(amp[band] ** 2) / np.sum(amp[band] ** 2 * f[band] ** 2))
                              if m2 > 0 else np.nan),
                     tp_true=sea.tp, fs=fs)
