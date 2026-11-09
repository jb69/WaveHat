// Sea-state statistics from a heave signal: the WaveHat wave maths (firmware/desktop/wavemath.py,
// firmware/lib/wavemath) cut down to the part that starts from displacement.
//
// In:  heave samples in metres, up positive, at whatever rate and jitter the source has (a B&G /
//      Simrad Precision-9 compass sends NMEA 2000 PGN 127252 at 10 Hz).
// Out: Hs = 4 sqrt(m0), Tp (spectral peak), Tz = sqrt(m0/m2), over the last ~20 minutes, band
//      0.04-0.5 Hz (25 s to 2 s), with the same "is there a clear peak" gate as the firmware.
//
// How: samples are averaged into fixed 0.4 s bins on the caller's clock (2.5 Hz; the box-car's
// roll-off, 6.5 % in amplitude at 0.5 Hz, is divided back out of the spectrum), then Welch:
// 512-point Hann segments (205 s), 50 % overlap, the last 11 averaged (~20 min), first result
// after 5 (~10 min). A gap of more than 5 s in the input starts the window again.
//
// No dependencies; runs in Node or a browser.

'use strict'

const DEFAULTS = {
  fs: 2.5, // Hz, after binning
  nfft: 512, // samples per Welch segment (power of two)
  hop: 256, // 50 % overlap
  windowSegments: 11, // segments averaged: ~20 min
  minSegments: 5, // first result after ~10 min
  fLo: 0.04, // Hz
  fHi: 0.5, // Hz
  minHsPeriods: 0.05, // m: below this Tp and Tz mean nothing
  minPeakRatio: 2.0, // smoothed peak / band median
  maxGapMs: 5000 // a longer silence restarts the window
}

// In-place radix-2 complex FFT.
function fft (re, im) {
  const n = re.length
  for (let i = 1, j = 0; i < n; i++) {
    let bit = n >> 1
    for (; j & bit; bit >>= 1) j ^= bit
    j ^= bit
    if (i < j) {
      let t = re[i]; re[i] = re[j]; re[j] = t
      t = im[i]; im[i] = im[j]; im[j] = t
    }
  }
  for (let len = 2; len <= n; len <<= 1) {
    const ang = -2 * Math.PI / len
    const wr = Math.cos(ang); const wi = Math.sin(ang)
    for (let i = 0; i < n; i += len) {
      let cr = 1; let ci = 0
      for (let k = 0; k < len / 2; k++) {
        const a = i + k; const b = a + len / 2
        const xr = re[b] * cr - im[b] * ci
        const xi = re[b] * ci + im[b] * cr
        re[b] = re[a] - xr; im[b] = im[a] - xi
        re[a] += xr; im[a] += xi
        const t = cr * wr - ci * wi
        ci = cr * wi + ci * wr
        cr = t
      }
    }
  }
}

// Hs, Tp, Tz and the peak's quality from a band-limited displacement spectrum S (m^2/Hz), first
// bin kLo, spacing df. The same steps as wavemath.py spectral_stats().
function spectralStats (S, kLo, df) {
  const n = S.length
  let m0 = 0; let m2 = 0
  for (let k = 0; k < n; k++) {
    const f = (k + kLo) * df
    m0 += S[k] * df
    m2 += S[k] * f * f * df
  }
  // Peak: 3-bin running mean, then log-parabolic interpolation between bins (suits Hann).
  const Ss = new Float64Array(n)
  for (let k = 0; k < n; k++) {
    const lo = Math.max(0, k - 1); const hi = Math.min(n, k + 2)
    let sum = 0
    for (let j = lo; j < hi; j++) sum += S[j]
    Ss[k] = sum / (hi - lo)
  }
  let i = 0
  for (let k = 1; k < n; k++) if (Ss[k] > Ss[i]) i = k
  let fp = (i + kLo) * df
  if (i > 0 && i < n - 1 && Math.min(Ss[i - 1], Ss[i], Ss[i + 1]) > 0) {
    const l0 = Math.log(Ss[i - 1]); const l1 = Math.log(Ss[i]); const l2 = Math.log(Ss[i + 1])
    const den = l0 - 2 * l1 + l2
    if (den < 0) fp += 0.5 * (l0 - l2) / den * df
  }
  const sorted = Array.from(Ss).sort((a, b) => a - b)
  const med = n % 2 ? sorted[(n - 1) / 2] : 0.5 * (sorted[n / 2 - 1] + sorted[n / 2])
  return {
    hs: 4 * Math.sqrt(Math.max(m0, 0)),
    tp: fp > 0 ? 1 / fp : NaN,
    tz: m2 > 0 ? Math.sqrt(m0 / m2) : NaN,
    rms: Math.sqrt(Math.max(m0, 0)),
    peakBin: i,
    peakRatio: med > 0 ? Ss[i] / med : Infinity
  }
}

class SeaState {
  constructor (options = {}) {
    this.cfg = Object.assign({}, DEFAULTS, options)
    const c = this.cfg
    if (c.nfft & (c.nfft - 1)) throw new Error('nfft must be a power of two')
    this.dtMs = 1000 / c.fs
    this.df = c.fs / c.nfft
    this.kLo = Math.max(1, Math.ceil(c.fLo / this.df - 1e-9))
    this.kHi = Math.min(c.nfft / 2 - 1, Math.floor(c.fHi / this.df + 1e-9))
    this.window = new Float64Array(c.nfft)
    let w2 = 0
    for (let k = 0; k < c.nfft; k++) {
      this.window[k] = 0.5 - 0.5 * Math.cos(2 * Math.PI * k / c.nfft) // periodic Hann
      w2 += this.window[k] * this.window[k]
    }
    this.w2 = w2
    // The 0.4 s box-car average's power response at each band bin, to divide back out.
    this.boxcar = new Float64Array(this.kHi - this.kLo + 1)
    for (let k = this.kLo; k <= this.kHi; k++) {
      const x = Math.PI * k * this.df / c.fs
      const s = x > 0 ? Math.sin(x) / x : 1
      this.boxcar[k - this.kLo] = s * s
    }
    this.reset()
  }

  reset () {
    this.buf = [] // binned samples not yet consumed by a hop
    this.segments = [] // the last windowSegments band spectra
    this.bin = null // {index, sum, n}
    this.lastMs = null
    this.last = 0
    this.stats = null
    this.samples = 0
    this.resets = (this.resets || 0)
  }

  // One heave sample, metres, at tMs on a monotonic-enough clock. Returns a new result object
  // when one is ready (once per hop, ~102 s, after minSegments), else null.
  push (tMs, heave) {
    if (!Number.isFinite(heave) || !Number.isFinite(tMs)) return null
    if (this.lastMs !== null && (tMs - this.lastMs > this.cfg.maxGapMs || tMs < this.lastMs - 1000)) {
      this.reset()
      this.resets++
    }
    this.lastMs = tMs
    this.samples++
    const index = Math.floor(tMs / this.dtMs)
    let result = null
    if (this.bin === null) {
      this.bin = { index, sum: heave, n: 1 }
      return null
    }
    if (index === this.bin.index) {
      this.bin.sum += heave
      this.bin.n++
      return null
    }
    // Close the bin; a short hole (a sample or two late) is filled with the last value.
    this.last = this.bin.sum / this.bin.n
    for (let i = this.bin.index; i < index; i++) result = this._binned(this.last) || result
    this.bin = { index, sum: heave, n: 1 }
    return result
  }

  _binned (x) {
    const c = this.cfg
    this.buf.push(x)
    if (this.buf.length < c.nfft) return null
    const re = new Float64Array(c.nfft); const im = new Float64Array(c.nfft)
    let mean = 0
    for (let k = 0; k < c.nfft; k++) mean += this.buf[k]
    mean /= c.nfft
    for (let k = 0; k < c.nfft; k++) re[k] = (this.buf[k] - mean) * this.window[k]
    fft(re, im)
    const S = new Float64Array(this.kHi - this.kLo + 1)
    for (let k = this.kLo; k <= this.kHi; k++) {
      S[k - this.kLo] = 2 * (re[k] * re[k] + im[k] * im[k]) / (c.fs * this.w2) / this.boxcar[k - this.kLo]
    }
    this.segments.push(S)
    if (this.segments.length > c.windowSegments) this.segments.shift()
    this.buf.splice(0, c.hop)
    if (this.segments.length < c.minSegments) return null
    const avg = new Float64Array(S.length)
    for (const s of this.segments) for (let k = 0; k < avg.length; k++) avg[k] += s[k] / this.segments.length
    const st = spectralStats(avg, this.kLo, this.df)
    st.segments = this.segments.length
    st.periodsValid = st.hs >= c.minHsPeriods && st.peakBin > 0 && st.peakBin < avg.length - 1 &&
      st.peakRatio >= c.minPeakRatio
    st.spectrum = avg
    st.kLo = this.kLo
    st.df = this.df
    this.stats = st
    return st
  }

  // Seconds of data still needed before the first result.
  secondsToFirst () {
    if (this.stats) return 0
    const c = this.cfg
    const need = c.nfft + (c.minSegments - 1) * c.hop
    const have = this.segments.length ? c.nfft + (this.segments.length - 1) * c.hop + (this.buf.length - (c.nfft - c.hop)) : this.buf.length
    return Math.max(0, (need - have) / c.fs)
  }
}

module.exports = { SeaState, spectralStats, fft, DEFAULTS }
