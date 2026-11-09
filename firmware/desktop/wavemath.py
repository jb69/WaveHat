"""WaveHat wave maths, desktop reference implementation.

This is the algorithm the firmware runs, written sample by sample in plain
Python + numpy so that it can be tested against synthetic sea states and the
C++ port (lib/wavemath/) can be checked against it number for number.

Pipeline, per IMU sample (LSM6DSO, ~26 Hz):

  accel + gyro (body frame: X starboard, Y bow, Z up, as on the silkscreen)
    -> lever-arm correction: the IMU's acceleration moved to the hull's
       roll/pitch centre, a = f - alpha x r - w x (w x r), r = Config.r_imu
       (one sample of delay for a central-difference alpha)
    -> Mahony 6-DOF attitude filter (no magnetometer; yaw drifts, which is fine)
    -> earth-frame vertical acceleration a_up = (R f)_z - g
    -> heave filter (4th-order high-pass folded into a double integrator)
       -> instantaneous heave, the Signal K path environment.heave
    -> anti-alias low-pass, decimate by 8 (26 Hz -> 3.25 Hz)
    -> Welch segments of 512 samples (157.5 s, df = 0.0063 Hz), 50 % overlap,
       Hann window, kept as band-limited displacement spectra
       S_eta(f) = S_a(f) / (2 pi f)^4 for 0.04 <= f <= 0.5 Hz
    -> every hop (78.8 s) the last K segments (K = 14 is ~20 min) are averaged:
       Hs = 4 sqrt(m0), Tp = 1 / f_peak, Tz = sqrt(m0 / m2), heave RMS.
    -> quality gate: the periods only mean something when there is a sea and
       a peak inside the band (see WaveStats.periods_valid).

Decimating before the FFT is the reason the firmware is cheap: the wave band
stops at 0.5 Hz, so a 512-point FFT at 3.25 Hz has the same resolution as a
4096-point FFT at 26 Hz for one eighth of the work.

IIR filters run in double precision (their poles sit very close to the unit
circle at 0.02 Hz / 26 Hz); everything else, as in the firmware, would be fine
in single precision.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

G = 9.80665  # m/s^2, standard gravity (the LSM6DSO is calibrated in g)

# Butterworth 4th order = two biquads with these Q values.
BUTTER4_Q = (0.5411961001461970, 1.3065629648763766)


@dataclass
class Config:
    fs: float = 26.0              # IMU output data rate, Hz (measured in firmware)
    decimation: int = 8           # 26 Hz -> 3.25 Hz before the FFT
    aa_cutoff: float = 1.2        # Hz, anti-alias low-pass before decimation
    nfft: int = 512               # samples per Welch segment (after decimation)
    hop: int = 256                # 50 % overlap
    window_segments: int = 14     # segments averaged: 14 -> ~20 min of data
    min_segments: int = 6         # first result after ~10 min
    f_lo: float = 0.04            # Hz, wave band (25 s)
    f_hi: float = 0.5             # Hz, wave band (2 s)
    heave_cutoff: float = 0.02    # Hz, high-pass corner of the heave integrator
    mahony_kp: float = 0.05       # 1/s, attitude correction (time constant ~20 s)
    mahony_ki: float = 0.0006     # 1/s^2, gyro bias estimation (~Kp^2/4)
    accel_gate: float = 0.25      # skip attitude correction if | |f| - g | > this * g
    attitude: bool = True         # False: take body Z as vertical (comparison only)
    # IMU position from the hull's roll/pitch centre, m, body frame (X starboard,
    # Y bow, Z up). Roll about a centre the IMU is not on reads as heave.
    r_imu: tuple = (0.0, 0.0, 0.0)
    # Periods are only reported (periods_valid) with Hs at least this, the
    # smoothed peak away from the band edges and this many times the band median.
    min_hs_periods: float = 0.05  # m
    min_peak_ratio: float = 2.0   # broad 3 s chop cut off at 0.5 Hz has ~2.9


# --------------------------------------------------------------------------
# Filters


class Biquad:
    """Direct form I biquad, double precision (RBJ cookbook designs)."""

    def __init__(self, b, a):
        self.b0, self.b1, self.b2 = b
        self.a1, self.a2 = a
        self.x1 = self.x2 = self.y1 = self.y2 = 0.0

    @staticmethod
    def _common(f0, fs, q):
        w0 = 2.0 * math.pi * f0 / fs
        alpha = math.sin(w0) / (2.0 * q)
        return w0, alpha, math.cos(w0), 1.0 + alpha

    @classmethod
    def lowpass(cls, f0, fs, q, scale=1.0):
        _, alpha, c, a0 = cls._common(f0, fs, q)
        k = scale * (1.0 - c) / 2.0 / a0
        return cls((k, 2.0 * k, k), (-2.0 * c / a0, (1.0 - alpha) / a0))

    @classmethod
    def highpass(cls, f0, fs, q):
        _, alpha, c, a0 = cls._common(f0, fs, q)
        k = (1.0 + c) / 2.0 / a0
        return cls((k, -2.0 * k, k), (-2.0 * c / a0, (1.0 - alpha) / a0))

    def reset(self, x):
        """Set the state as if x had been the input forever (DC steady state)."""
        gain = (self.b0 + self.b1 + self.b2) / (1.0 + self.a1 + self.a2)
        self.x1 = self.x2 = x
        self.y1 = self.y2 = gain * x

    def step(self, x):
        y = (self.b0 * x + self.b1 * self.x1 + self.b2 * self.x2
             - self.a1 * self.y1 - self.a2 * self.y2)
        self.x2, self.x1 = self.x1, x
        self.y2, self.y1 = self.y1, y
        return y


def heave_filter(fs, fc):
    """Acceleration -> displacement, high-passed at fc.

    H(s) = HP4(s) / s^2 = s^2 / (B1(s) B2(s)): one high-pass biquad times one
    low-pass biquad divided by Omega^2. Above fc it is a double integrator
    (trapezoidal, accurate to 0.1 % at 0.5 Hz with fs = 26 Hz); below fc it
    rolls off so gravity residue, bias and drift never integrate up.
    """
    omega = 2.0 * fs * math.tan(math.pi * fc / fs)  # prewarped, rad/s
    return [Biquad.highpass(fc, fs, BUTTER4_Q[0]),
            Biquad.lowpass(fc, fs, BUTTER4_Q[1], scale=1.0 / omega ** 2)]


def butter4_lowpass(fs, fc):
    return [Biquad.lowpass(fc, fs, q) for q in BUTTER4_Q]


# --------------------------------------------------------------------------
# Attitude


class Mahony:
    """Mahony complementary filter, 6-DOF (accel + gyro), quaternion body->earth.

    Earth frame is z up; the accelerometer reads +1 g on Z when the board lies
    flat, component side up.
    """

    def __init__(self, kp, ki, gate):
        self.kp, self.ki, self.gate = kp, ki, gate
        self.q = np.array([1.0, 0.0, 0.0, 0.0])
        self.bias = np.zeros(3)  # integral term, rad/s
        self.ready = False

    def init_from_accel(self, a):
        ax, ay, az = a / np.linalg.norm(a)
        # Shortest-arc rotation taking the measured "up" a onto earth Z:
        # q = [1 + a.z, a x z], yaw left at zero.
        w = 1.0 + az
        if w < 1e-6:  # upside down
            self.q = np.array([0.0, 1.0, 0.0, 0.0])
        else:
            q = np.array([w, ay, -ax, 0.0])
            self.q = q / np.linalg.norm(q)
        self.ready = True

    def up_in_body(self):
        """Earth 'up' (0,0,1) expressed in body coordinates: third row of R."""
        w, x, y, z = self.q
        return np.array([2.0 * (x * z - w * y),
                         2.0 * (y * z + w * x),
                         w * w - x * x - y * y + z * z])

    def update(self, gyro, accel, dt):
        if not self.ready:
            self.init_from_accel(accel)
            return
        g = np.array(gyro, dtype=float)
        n = np.linalg.norm(accel)
        if abs(n - G) < self.gate * G:
            a = accel / n
            v = self.up_in_body()
            e = np.cross(a, v)
            self.bias += self.ki * e * dt
            g = g + self.kp * e + self.bias
        else:
            g = g + self.bias
        w, x, y, z = self.q
        gx, gy, gz = g
        dq = 0.5 * np.array([-x * gx - y * gy - z * gz,
                             w * gx + y * gz - z * gy,
                             w * gy - x * gz + z * gx,
                             w * gz + x * gy - y * gx])
        q = self.q + dq * dt
        self.q = q / np.linalg.norm(q)

    def vertical_accel(self, accel):
        """Earth-frame vertical acceleration (m/s^2, up positive), gravity removed."""
        return float(np.dot(self.up_in_body(), accel)) - G


# --------------------------------------------------------------------------
# Spectrum


def hann(n):
    """Periodic Hann window (the right one for Welch)."""
    k = np.arange(n)
    return 0.5 - 0.5 * np.cos(2.0 * np.pi * k / n)


@dataclass
class WaveStats:
    hs: float          # m, significant wave height 4 sqrt(m0)
    tp: float          # s, peak period
    tz: float          # s, mean zero-crossing period sqrt(m0/m2)
    heave_rms: float   # m, sqrt(m0) (spectral, band-limited)
    heave_rms_td: float  # m, RMS of the heave filter output over the same window
    segments: int      # Welch segments averaged
    fs: float          # Hz, sample rate used
    periods_valid: bool = True  # False: flat calm, or no peak inside the band
    peak_ratio: float = 0.0     # smoothed peak / band median of the spectrum
    freqs: np.ndarray = field(repr=False, default=None)
    spectrum: np.ndarray = field(repr=False, default=None)  # m^2/Hz


def band_bins(fs_dec, nfft, f_lo, f_hi):
    df = fs_dec / nfft
    k_lo = max(1, math.ceil(f_lo / df - 1e-9))
    k_hi = min(nfft // 2 - 1, math.floor(f_hi / df + 1e-9))
    return k_lo, k_hi, df


def segment_spectrum(x, fs_dec, k_lo, k_hi):
    """One Welch segment: displacement PSD (m^2/Hz) on bins k_lo..k_hi."""
    n = len(x)
    w = hann(n)
    xw = (x - np.mean(x)) * w
    X = np.fft.rfft(xw)
    p = 2.0 * np.abs(X[k_lo:k_hi + 1]) ** 2 / (fs_dec * np.sum(w * w))
    f = np.arange(k_lo, k_hi + 1) * fs_dec / n
    return p / (2.0 * np.pi * f) ** 4


def spectral_stats(S, k_lo, df, detail=False):
    """Hs, Tp, Tz, sqrt(m0) from a band-limited displacement spectrum.

    detail=True also returns the peak's bin and the smoothed peak / median
    ratio, for the quality gate."""
    f = (np.arange(len(S)) + k_lo) * df
    m0 = float(np.sum(S) * df)
    m2 = float(np.sum(S * f * f) * df)
    # Peak: 3-bin running mean (steadies a broad, flat-topped peak), then
    # Gaussian (log-parabolic) interpolation between bins, which suits Hann.
    n = len(S)
    Ss = np.empty(n)
    for k in range(n):
        lo, hi = max(0, k - 1), min(n, k + 2)
        Ss[k] = np.mean(S[lo:hi])
    i = int(np.argmax(Ss))
    fp = f[i]
    if 0 < i < n - 1 and min(Ss[i - 1], Ss[i], Ss[i + 1]) > 0:
        l0, l1, l2 = math.log(Ss[i - 1]), math.log(Ss[i]), math.log(Ss[i + 1])
        den = l0 - 2.0 * l1 + l2
        if den < 0:
            fp = f[i] + 0.5 * (l0 - l2) / den * df
    hs = 4.0 * math.sqrt(max(m0, 0.0))
    tp = 1.0 / fp if fp > 0 else float("nan")
    tz = math.sqrt(m0 / m2) if m2 > 0 else float("nan")
    if detail:
        med = float(np.median(Ss))
        ratio = float(Ss[i] / med) if med > 0 else float("inf")
        return hs, tp, tz, math.sqrt(max(m0, 0.0)), i, ratio
    return hs, tp, tz, math.sqrt(max(m0, 0.0))


def periods_valid(cfg, hs, peak_bin, nbins, ratio):
    """Tp and Tz mean nothing in flat calm (the spectrum is sensor noise, red
    after the 1/(2 pi f)^4) or when the peak sits on a band edge (the sea's
    peak is outside the band, e.g. swell longer than 22.5 s)."""
    return (hs >= cfg.min_hs_periods and 0 < peak_bin < nbins - 1
            and ratio >= cfg.min_peak_ratio)


# --------------------------------------------------------------------------
# The streaming processor (what the firmware runs)


class WaveProcessor:
    def __init__(self, cfg: Config | None = None):
        self.cfg = cfg or Config()
        c = self.cfg
        self.ahrs = Mahony(c.mahony_kp, c.mahony_ki, c.accel_gate)
        self.heave_f = heave_filter(c.fs, c.heave_cutoff)
        self.aa_f = butter4_lowpass(c.fs, c.aa_cutoff)
        self.fs_dec = c.fs / c.decimation
        self.k_lo, self.k_hi, self.df = band_bins(self.fs_dec, c.nfft, c.f_lo, c.f_hi)
        self.n = 0                # IMU samples seen
        self.buf = []             # decimated vertical acceleration, last nfft
        self.heave_sq = []        # decimated heave^2 since the last segment
        self.new_since_seg = 0
        self.segs = []            # band displacement spectra, last K
        self.seg_heave_ms = []    # mean heave^2 per hop block, last K
        self.heave = 0.0
        self.latest: WaveStats | None = None
        self.primed = False
        self.r = np.asarray(c.r_imu, dtype=float)
        self.g_before = self.g_mid = self.a_mid = None  # lever-arm delay line

    def push(self, gyro, accel):
        """One IMU sample: gyro in rad/s, accel in m/s^2 (body frame).

        Returns a new WaveStats when a Welch segment completes and enough
        segments are available, else None.
        """
        c = self.cfg
        # Lever arm: the chain runs one sample (38 ms) behind, so the angular
        # acceleration of the middle sample is a central difference.
        gyro = np.asarray(gyro, dtype=float)
        accel = np.asarray(accel, dtype=float)
        before, w, a = self.g_before, self.g_mid, self.a_mid
        self.g_before, self.g_mid, self.a_mid = w, gyro, accel
        if before is None:
            return None
        alpha = (gyro - before) * (c.fs / 2.0)
        accel = a - np.cross(alpha, self.r) - np.cross(w, np.cross(w, self.r))
        gyro = w
        self.ahrs.update(gyro, accel, 1.0 / c.fs)
        a_up = self.ahrs.vertical_accel(accel) if c.attitude else accel[2] - G
        if not self.primed:
            for f in self.aa_f:
                f.reset(a_up)
            self.primed = True
        h = a_up
        for f in self.heave_f:
            h = f.step(h)
        self.heave = h
        y = a_up
        for f in self.aa_f:
            y = f.step(y)
        self.n += 1
        if self.n % c.decimation:
            return None
        self.buf.append(y)
        self.heave_sq.append(h * h)
        if len(self.buf) > c.nfft:
            self.buf.pop(0)
        self.new_since_seg += 1
        if len(self.buf) < c.nfft or self.new_since_seg < c.hop:
            return None
        self.new_since_seg = 0
        self.segs.append(segment_spectrum(np.array(self.buf), self.fs_dec,
                                          self.k_lo, self.k_hi))
        self.seg_heave_ms.append(float(np.mean(self.heave_sq)))  # since last segment
        self.heave_sq = []
        if len(self.segs) > c.window_segments:
            self.segs.pop(0)
            self.seg_heave_ms.pop(0)
        if len(self.segs) < c.min_segments:
            return None
        S = np.mean(self.segs, axis=0)
        hs, tp, tz, rms, peak_bin, ratio = spectral_stats(S, self.k_lo, self.df, detail=True)
        f = (np.arange(len(S)) + self.k_lo) * self.df
        self.latest = WaveStats(hs, tp, tz, rms, math.sqrt(np.mean(self.seg_heave_ms)),
                                len(self.segs), c.fs,
                                periods_valid(c, hs, peak_bin, len(S), ratio), ratio, f, S)
        return self.latest

    def run(self, gyro, accel):
        """Feed arrays of samples (N x 3); return every WaveStats produced and
        the heave time series (one value per IMU sample)."""
        out, heave = [], np.empty(len(accel))
        for i in range(len(accel)):
            s = self.push(gyro[i], accel[i])
            heave[i] = self.heave
            if s is not None:
                out.append(s)
        return out, heave
