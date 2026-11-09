// WaveHat wave maths: attitude, heave and sea-state statistics from a 6-DOF IMU.
//
// A port of desktop/wavemath.py, kept line for line so the desktop tests can
// check one against the other. Plain C++17, no Arduino or ESP-IDF headers, so
// it also builds on a PC (desktop/native/).
//
// Body frame: X starboard, Y bow, Z up (as on the board silkscreen). The IMU's
// acceleration is moved to the hull's roll/pitch centre (Config::r_imu) before
// anything else, which delays the whole chain by one sample (38 ms).
// Units in: gyro rad/s, accel m/s^2. Units out: m, s.
//
// Precision: IIR filters in double (their poles sit very close to the unit
// circle; software double on the C3/C6 costs little at 26 Hz). Attitude, FFT
// and spectra in float.

#pragma once

#include <cstdint>
#include <vector>

namespace wavemath {

constexpr float kG = 9.80665f;

struct Config {
  float fs = 26.0f;             // IMU output data rate, Hz
  int decimation = 8;           // 26 Hz -> 3.25 Hz before the FFT
  float aa_cutoff = 1.2f;       // Hz, anti-alias low-pass before decimation
  int nfft = 512;               // samples per Welch segment (power of two)
  int hop = 256;                // 50 % overlap
  int window_segments = 14;     // segments averaged: 14 -> ~20 min
  int min_segments = 6;         // first result after ~10 min
  float f_lo = 0.04f;           // Hz, wave band (25 s)
  float f_hi = 0.5f;            // Hz, wave band (2 s)
  float heave_cutoff = 0.02f;   // Hz, high-pass corner of the heave integrator
  float mahony_kp = 0.05f;      // 1/s
  float mahony_ki = 0.0006f;    // 1/s^2
  float accel_gate = 0.25f;     // skip attitude correction if ||f|-g| > gate*g
  // IMU position from the hull's roll/pitch centre, m, body frame. Roll about
  // a centre the IMU is not on reads as heave; this takes it out.
  float r_imu[3] = {0, 0, 0};
  // Periods are valid only with Hs at least min_hs_periods, the smoothed peak
  // off the band edges and at least min_peak_ratio times the band median.
  float min_hs_periods = 0.05f;  // m
  float min_peak_ratio = 2.0f;  // broad 3 s chop cut off at 0.5 Hz has ~2.9
};

struct Stats {
  float hs = 0;            // m, significant wave height 4 sqrt(m0)
  float tp = 0;            // s, peak period
  float tz = 0;            // s, mean zero-crossing period sqrt(m0/m2)
  float heave_rms = 0;     // m, sqrt(m0)
  float heave_rms_td = 0;  // m, RMS of the heave output over the window
  int segments = 0;        // Welch segments averaged
  float fs = 0;            // Hz, IMU rate used
  bool periods_valid = false;  // false: flat calm, or the peak is not inside the band
  float peak_ratio = 0;    // smoothed peak / band median
};

// Direct form I biquad, double precision, RBJ cookbook designs.
class Biquad {
 public:
  static Biquad lowpass(double f0, double fs, double q, double scale = 1.0);
  static Biquad highpass(double f0, double fs, double q);
  void reset(double x);  // DC steady state for a constant input x
  double step(double x) {
    double y = b0_ * x + b1_ * x1_ + b2_ * x2_ - a1_ * y1_ - a2_ * y2_;
    x2_ = x1_;
    x1_ = x;
    y2_ = y1_;
    y1_ = y;
    return y;
  }

 private:
  double b0_ = 1, b1_ = 0, b2_ = 0, a1_ = 0, a2_ = 0;
  double x1_ = 0, x2_ = 0, y1_ = 0, y2_ = 0;
};

// Mahony complementary filter, 6-DOF, quaternion body->earth (z up).
class Mahony {
 public:
  Mahony(float kp, float ki, float gate) : kp_(kp), ki_(ki), gate_(gate) {}
  void update(const float gyro[3], const float accel[3], float dt);
  // Earth "up" expressed in the body frame (third row of R).
  void up_in_body(float v[3]) const;
  // Earth-frame vertical acceleration, m/s^2, up positive, gravity removed.
  float vertical_accel(const float accel[3]) const;
  bool ready() const { return ready_; }
  const float* quaternion() const { return q_; }

 private:
  void init_from_accel(const float a[3]);
  float kp_, ki_, gate_;
  float q_[4] = {1, 0, 0, 0};
  float bias_[3] = {0, 0, 0};
  bool ready_ = false;
};

// In-place radix-2 complex FFT, float, sizes fixed at construction.
class Fft {
 public:
  explicit Fft(int n);
  void forward(float* re, float* im) const;
  int size() const { return n_; }

 private:
  int n_;
  std::vector<float> cos_, sin_;
  std::vector<uint16_t> rev_;
};

// Hs, Tp, Tz and sqrt(m0) from a band-limited displacement spectrum
// (m^2/Hz) whose first bin is k_lo, spacing df. Optionally the smoothed peak's
// bin (0..n-1) and its ratio to the median, for the quality gate.
void spectral_stats(const float* S, int n, int k_lo, float df, float* hs,
                    float* tp, float* tz, float* rms, int* peak_bin = nullptr,
                    float* peak_ratio = nullptr);

class WaveProcessor {
 public:
  explicit WaveProcessor(const Config& cfg = Config());

  // One IMU sample. Returns true when a new Stats is ready (once per hop,
  // i.e. every ~79 s, after min_segments segments).
  bool push(const float gyro[3], const float accel[3]);

  const Stats& stats() const { return stats_; }
  float heave() const { return static_cast<float>(heave_); }
  float vertical_accel() const { return a_up_; }
  const Mahony& ahrs() const { return ahrs_; }
  const Config& config() const { return cfg_; }
  // Welch segments computed so far (one FFT each, every ~79 s).
  uint32_t segments_computed() const { return segments_computed_; }

  // Averaged displacement spectrum of the last result.
  const std::vector<float>& spectrum() const { return avg_; }
  int k_lo() const { return k_lo_; }
  float df() const { return df_; }

 private:
  void compute_segment();

  Config cfg_;
  Mahony ahrs_;
  Biquad heave_f_[2];
  Biquad aa_f_[2];
  Fft fft_;
  float fs_dec_;
  int k_lo_, k_hi_, nbins_;
  float df_;
  uint32_t n_ = 0;
  bool primed_ = false;
  int delay_fill_ = 0;           // lever-arm delay line: samples held (0-2)
  float g_before_[3] = {0, 0, 0}, g_mid_[3] = {0, 0, 0}, a_mid_[3] = {0, 0, 0};
  double heave_ = 0;
  float a_up_ = 0;

  std::vector<float> ring_;      // decimated vertical accel, circular, nfft
  int ring_pos_ = 0;
  int ring_fill_ = 0;
  int since_seg_ = 0;
  double heave_sq_sum_ = 0;      // over the current hop
  int heave_sq_n_ = 0;

  std::vector<float> win_;       // Hann
  float win_ss_ = 0;             // sum of window squared
  std::vector<float> re_, im_;   // FFT work
  std::vector<float> segs_;      // window_segments x nbins, circular
  std::vector<float> seg_heave_ms_;
  int seg_next_ = 0;
  int seg_count_ = 0;
  uint32_t segments_computed_ = 0;
  std::vector<float> avg_;
  Stats stats_;
};

}  // namespace wavemath
