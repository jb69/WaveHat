// WaveHat wave maths. See wavemath.h and desktop/wavemath.py.

#include "wavemath.h"

#include <algorithm>
#include <cmath>

namespace wavemath {

namespace {

constexpr double kPi = 3.14159265358979323846;
// Butterworth 4th order = two biquads with these Q values.
constexpr double kButter4Q[2] = {0.5411961001461970, 1.3065629648763766};

}  // namespace

// ---------------------------------------------------------------- Biquad

Biquad Biquad::lowpass(double f0, double fs, double q, double scale) {
  double w0 = 2.0 * kPi * f0 / fs;
  double alpha = std::sin(w0) / (2.0 * q);
  double c = std::cos(w0);
  double a0 = 1.0 + alpha;
  Biquad b;
  double k = scale * (1.0 - c) / 2.0 / a0;
  b.b0_ = k;
  b.b1_ = 2.0 * k;
  b.b2_ = k;
  b.a1_ = -2.0 * c / a0;
  b.a2_ = (1.0 - alpha) / a0;
  return b;
}

Biquad Biquad::highpass(double f0, double fs, double q) {
  double w0 = 2.0 * kPi * f0 / fs;
  double alpha = std::sin(w0) / (2.0 * q);
  double c = std::cos(w0);
  double a0 = 1.0 + alpha;
  Biquad b;
  double k = (1.0 + c) / 2.0 / a0;
  b.b0_ = k;
  b.b1_ = -2.0 * k;
  b.b2_ = k;
  b.a1_ = -2.0 * c / a0;
  b.a2_ = (1.0 - alpha) / a0;
  return b;
}

void Biquad::reset(double x) {
  double gain = (b0_ + b1_ + b2_) / (1.0 + a1_ + a2_);
  x1_ = x2_ = x;
  y1_ = y2_ = gain * x;
}

// ---------------------------------------------------------------- Mahony

void Mahony::init_from_accel(const float a[3]) {
  float n = std::sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2]);
  float ax = a[0] / n, ay = a[1] / n, az = a[2] / n;
  // Shortest-arc rotation taking the measured "up" onto earth Z, yaw zero.
  float w = 1.0f + az;
  if (w < 1e-6f) {
    q_[0] = 0;
    q_[1] = 1;
    q_[2] = 0;
    q_[3] = 0;
  } else {
    float qn = std::sqrt(w * w + ay * ay + ax * ax);
    q_[0] = w / qn;
    q_[1] = ay / qn;
    q_[2] = -ax / qn;
    q_[3] = 0;
  }
  ready_ = true;
}

void Mahony::up_in_body(float v[3]) const {
  float w = q_[0], x = q_[1], y = q_[2], z = q_[3];
  v[0] = 2.0f * (x * z - w * y);
  v[1] = 2.0f * (y * z + w * x);
  v[2] = w * w - x * x - y * y + z * z;
}

void Mahony::update(const float gyro[3], const float accel[3], float dt) {
  if (!ready_) {
    init_from_accel(accel);
    return;
  }
  float g[3] = {gyro[0], gyro[1], gyro[2]};
  float n = std::sqrt(accel[0] * accel[0] + accel[1] * accel[1] +
                      accel[2] * accel[2]);
  if (std::fabs(n - kG) < gate_ * kG) {
    float a[3] = {accel[0] / n, accel[1] / n, accel[2] / n};
    float v[3];
    up_in_body(v);
    float e[3] = {a[1] * v[2] - a[2] * v[1], a[2] * v[0] - a[0] * v[2],
                  a[0] * v[1] - a[1] * v[0]};
    for (int i = 0; i < 3; i++) {
      bias_[i] += ki_ * e[i] * dt;
      g[i] += kp_ * e[i] + bias_[i];
    }
  } else {
    for (int i = 0; i < 3; i++) g[i] += bias_[i];
  }
  float w = q_[0], x = q_[1], y = q_[2], z = q_[3];
  float h = 0.5f * dt;
  float q0 = w + h * (-x * g[0] - y * g[1] - z * g[2]);
  float q1 = x + h * (w * g[0] + y * g[2] - z * g[1]);
  float q2 = y + h * (w * g[1] - x * g[2] + z * g[0]);
  float q3 = z + h * (w * g[2] + x * g[1] - y * g[0]);
  float qn = std::sqrt(q0 * q0 + q1 * q1 + q2 * q2 + q3 * q3);
  q_[0] = q0 / qn;
  q_[1] = q1 / qn;
  q_[2] = q2 / qn;
  q_[3] = q3 / qn;
}

float Mahony::vertical_accel(const float accel[3]) const {
  float v[3];
  up_in_body(v);
  return v[0] * accel[0] + v[1] * accel[1] + v[2] * accel[2] - kG;
}

// ---------------------------------------------------------------- FFT

Fft::Fft(int n) : n_(n), cos_(n / 2), sin_(n / 2), rev_(n) {
  for (int k = 0; k < n / 2; k++) {
    cos_[k] = static_cast<float>(std::cos(2.0 * kPi * k / n));
    sin_[k] = static_cast<float>(std::sin(2.0 * kPi * k / n));
  }
  int bits = 0;
  while ((1 << bits) < n) bits++;
  for (int i = 0; i < n; i++) {
    int r = 0;
    for (int b = 0; b < bits; b++) r |= ((i >> b) & 1) << (bits - 1 - b);
    rev_[i] = static_cast<uint16_t>(r);
  }
}

void Fft::forward(float* re, float* im) const {
  for (int i = 0; i < n_; i++) {
    int j = rev_[i];
    if (j > i) {
      std::swap(re[i], re[j]);
      std::swap(im[i], im[j]);
    }
  }
  for (int len = 2; len <= n_; len <<= 1) {
    int half = len / 2, step = n_ / len;
    for (int i = 0; i < n_; i += len) {
      for (int k = 0; k < half; k++) {
        // twiddle e^{-2 pi i k / len}
        float wr = cos_[k * step], wi = -sin_[k * step];
        int a = i + k, b = a + half;
        float tr = re[b] * wr - im[b] * wi;
        float ti = re[b] * wi + im[b] * wr;
        re[b] = re[a] - tr;
        im[b] = im[a] - ti;
        re[a] += tr;
        im[a] += ti;
      }
    }
  }
}

// ---------------------------------------------------------------- Stats

void spectral_stats(const float* S, int n, int k_lo, float df, float* hs,
                    float* tp, float* tz, float* rms, int* peak_bin,
                    float* peak_ratio) {
  double m0 = 0, m2 = 0;
  for (int k = 0; k < n; k++) {
    double f = (k + k_lo) * static_cast<double>(df);
    m0 += S[k];
    m2 += S[k] * f * f;
  }
  m0 *= df;
  m2 *= df;
  // Peak: 3-bin running mean, then Gaussian (log-parabolic) interpolation.
  int i = 0;
  float best = -1;
  std::vector<float> Ss(n);
  for (int k = 0; k < n; k++) {
    int lo = std::max(0, k - 1), hi = std::min(n, k + 2);
    float s = 0;
    for (int j = lo; j < hi; j++) s += S[j];
    Ss[k] = s / (hi - lo);
    if (Ss[k] > best) {
      best = Ss[k];
      i = k;
    }
  }
  double fp = (i + k_lo) * static_cast<double>(df);
  if (i > 0 && i < n - 1 && Ss[i - 1] > 0 && Ss[i] > 0 && Ss[i + 1] > 0) {
    double l0 = std::log(Ss[i - 1]), l1 = std::log(Ss[i]),
           l2 = std::log(Ss[i + 1]);
    double den = l0 - 2.0 * l1 + l2;
    if (den < 0) fp += 0.5 * (l0 - l2) / den * df;
  }
  m0 = std::max(m0, 0.0);
  *hs = static_cast<float>(4.0 * std::sqrt(m0));
  *tp = fp > 0 ? static_cast<float>(1.0 / fp) : NAN;
  *tz = m2 > 0 ? static_cast<float>(std::sqrt(m0 / m2)) : NAN;
  *rms = static_cast<float>(std::sqrt(m0));
  if (peak_bin) *peak_bin = i;
  if (peak_ratio) {
    // Median as numpy takes it: the mean of the two middle values for even n.
    std::vector<float> sorted(Ss);
    std::sort(sorted.begin(), sorted.end());
    float med = n % 2 ? sorted[n / 2] : 0.5f * (sorted[n / 2 - 1] + sorted[n / 2]);
    *peak_ratio = med > 0 ? Ss[i] / med : INFINITY;
  }
}

// ---------------------------------------------------------------- Processor

WaveProcessor::WaveProcessor(const Config& cfg)
    : cfg_(cfg),
      ahrs_(cfg.mahony_kp, cfg.mahony_ki, cfg.accel_gate),
      fft_(cfg.nfft) {
  double fs = cfg_.fs;
  // Acceleration -> displacement: HP4(s)/s^2 = HP biquad x LP biquad / Omega^2
  double omega = 2.0 * fs * std::tan(kPi * cfg_.heave_cutoff / fs);
  heave_f_[0] = Biquad::highpass(cfg_.heave_cutoff, fs, kButter4Q[0]);
  heave_f_[1] =
      Biquad::lowpass(cfg_.heave_cutoff, fs, kButter4Q[1], 1.0 / (omega * omega));
  aa_f_[0] = Biquad::lowpass(cfg_.aa_cutoff, fs, kButter4Q[0]);
  aa_f_[1] = Biquad::lowpass(cfg_.aa_cutoff, fs, kButter4Q[1]);

  fs_dec_ = cfg_.fs / cfg_.decimation;
  df_ = fs_dec_ / cfg_.nfft;
  k_lo_ = std::max(1, static_cast<int>(std::ceil(cfg_.f_lo / df_ - 1e-6f)));
  k_hi_ = std::min(cfg_.nfft / 2 - 1,
                   static_cast<int>(std::floor(cfg_.f_hi / df_ + 1e-6f)));
  nbins_ = k_hi_ - k_lo_ + 1;

  ring_.assign(cfg_.nfft, 0.0f);
  win_.resize(cfg_.nfft);
  win_ss_ = 0;
  for (int i = 0; i < cfg_.nfft; i++) {
    win_[i] = static_cast<float>(0.5 - 0.5 * std::cos(2.0 * kPi * i / cfg_.nfft));
    win_ss_ += win_[i] * win_[i];
  }
  re_.resize(cfg_.nfft);
  im_.resize(cfg_.nfft);
  segs_.assign(static_cast<size_t>(cfg_.window_segments) * nbins_, 0.0f);
  seg_heave_ms_.assign(cfg_.window_segments, 0.0f);
  avg_.assign(nbins_, 0.0f);
}

bool WaveProcessor::push(const float gyro_in[3], const float accel_in[3]) {
  // Lever arm: process the middle of the last three samples, with a central-
  // difference angular acceleration, and move its acceleration to the centre:
  // a = f - alpha x r - w x (w x r).
  float gyro[3], accel[3];
  bool have = delay_fill_ == 2;
  if (have) {
    const float* r = cfg_.r_imu;
    float al[3], wr[3];
    for (int i = 0; i < 3; i++) al[i] = (gyro_in[i] - g_before_[i]) * (cfg_.fs * 0.5f);
    const float* w = g_mid_;
    wr[0] = w[1] * r[2] - w[2] * r[1];
    wr[1] = w[2] * r[0] - w[0] * r[2];
    wr[2] = w[0] * r[1] - w[1] * r[0];
    accel[0] = a_mid_[0] - (al[1] * r[2] - al[2] * r[1]) - (w[1] * wr[2] - w[2] * wr[1]);
    accel[1] = a_mid_[1] - (al[2] * r[0] - al[0] * r[2]) - (w[2] * wr[0] - w[0] * wr[2]);
    accel[2] = a_mid_[2] - (al[0] * r[1] - al[1] * r[0]) - (w[0] * wr[1] - w[1] * wr[0]);
    for (int i = 0; i < 3; i++) gyro[i] = g_mid_[i];
  } else {
    delay_fill_++;
  }
  for (int i = 0; i < 3; i++) {
    g_before_[i] = g_mid_[i];
    g_mid_[i] = gyro_in[i];
    a_mid_[i] = accel_in[i];
  }
  if (!have) return false;

  ahrs_.update(gyro, accel, 1.0f / cfg_.fs);
  a_up_ = ahrs_.vertical_accel(accel);
  if (!primed_) {
    for (auto& f : aa_f_) f.reset(a_up_);
    primed_ = true;
  }
  double h = a_up_;
  for (auto& f : heave_f_) h = f.step(h);
  heave_ = h;
  double y = a_up_;
  for (auto& f : aa_f_) y = f.step(y);
  n_++;
  if (n_ % cfg_.decimation) return false;

  ring_[ring_pos_] = static_cast<float>(y);
  ring_pos_ = (ring_pos_ + 1) % cfg_.nfft;
  if (ring_fill_ < cfg_.nfft) ring_fill_++;
  heave_sq_sum_ += h * h;
  heave_sq_n_++;
  since_seg_++;
  if (ring_fill_ < cfg_.nfft || since_seg_ < cfg_.hop) return false;
  since_seg_ = 0;
  compute_segment();
  if (seg_count_ < cfg_.min_segments) return false;

  // Average the stored segments and derive the statistics.
  std::fill(avg_.begin(), avg_.end(), 0.0f);
  double ms = 0;
  for (int s = 0; s < seg_count_; s++) {
    const float* p = &segs_[static_cast<size_t>(s) * nbins_];
    for (int k = 0; k < nbins_; k++) avg_[k] += p[k];
    ms += seg_heave_ms_[s];
  }
  for (auto& v : avg_) v /= seg_count_;
  Stats st;
  int peak = 0;
  spectral_stats(avg_.data(), nbins_, k_lo_, df_, &st.hs, &st.tp, &st.tz,
                 &st.heave_rms, &peak, &st.peak_ratio);
  st.periods_valid = st.hs >= cfg_.min_hs_periods && peak > 0 &&
                     peak < nbins_ - 1 && st.peak_ratio >= cfg_.min_peak_ratio;
  st.heave_rms_td = static_cast<float>(std::sqrt(ms / seg_count_));
  st.segments = seg_count_;
  st.fs = cfg_.fs;
  stats_ = st;
  return true;
}

void WaveProcessor::compute_segment() {
  const int n = cfg_.nfft;
  // Oldest sample is at ring_pos_ (the buffer is full).
  double mean = 0;
  for (int i = 0; i < n; i++) mean += ring_[i];
  mean /= n;
  for (int i = 0; i < n; i++) {
    re_[i] = (ring_[(ring_pos_ + i) % n] - static_cast<float>(mean)) * win_[i];
    im_[i] = 0.0f;
  }
  fft_.forward(re_.data(), im_.data());
  float* out = &segs_[static_cast<size_t>(seg_next_) * nbins_];
  const float scale = 2.0f / (fs_dec_ * win_ss_);
  for (int k = k_lo_; k <= k_hi_; k++) {
    float p = (re_[k] * re_[k] + im_[k] * im_[k]) * scale;
    float w = static_cast<float>(2.0 * kPi * k * df_);
    float w2 = w * w;
    out[k - k_lo_] = p / (w2 * w2);
  }
  seg_heave_ms_[seg_next_] =
      static_cast<float>(heave_sq_sum_ / std::max(heave_sq_n_, 1));
  heave_sq_sum_ = 0;
  heave_sq_n_ = 0;
  seg_next_ = (seg_next_ + 1) % cfg_.window_segments;
  segments_computed_++;
  if (seg_count_ < cfg_.window_segments) seg_count_++;
}

}  // namespace wavemath
