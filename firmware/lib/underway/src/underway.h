// Was the boat underway while the waves were measured? (environment.waves.underway)
//
// Underway, waves are met at the encounter frequency, so the periods are distorted; Hs is not.
// SOG is sampled at every IMU poll (4 Hz) and summed per hop (one Welch segment, ~79 s); the
// window covers the hops the spectrum spans (15 for 14 segments). The window counts as underway
// when its mean SOG is above the threshold, or when more than a quarter of its samples are:
// a boat sheering at anchor, or a GPS jump, is a few samples and doesn't flag a 20-minute window,
// while motoring for a quarter of it does.
//
// Platform-free; tested natively by desktop/test_native_libs.py.

#pragma once

#include <cmath>
#include <vector>

class UnderwayTracker {
 public:
  explicit UnderwayTracker(int window_hops = 15, float threshold = 0.77f /* m/s, 1.5 kn */,
                           float fraction = 0.25f)
      : hops_(window_hops), threshold_(threshold), fraction_(fraction) {}

  // One SOG sample, m/s. NaN (no fresh SOG) is skipped.
  void sample(float sog) {
    if (std::isnan(sog)) return;
    cur_.n++;
    cur_.sum += sog;
    if (sog > threshold_) cur_.above++;
  }

  // At the end of each hop (each Welch segment).
  void end_hop() {
    window_.push_back(cur_);
    if (static_cast<int>(window_.size()) > hops_) window_.erase(window_.begin());
    cur_ = Hop();
  }

  void reset() {
    window_.clear();
    cur_ = Hop();
  }

  // 1 underway, 0 not, -1 unknown (no SOG at all in the window).
  int state() const {
    Hop t = total();
    if (t.n == 0) return -1;
    return (t.sum / t.n > threshold_ || static_cast<float>(t.above) / t.n > fraction_) ? 1 : 0;
  }

  // Mean SOG over the window, m/s (NaN if unknown), and the share of samples above the threshold.
  float mean_sog() const {
    Hop t = total();
    return t.n ? static_cast<float>(t.sum / t.n) : NAN;
  }
  float fraction_above() const {
    Hop t = total();
    return t.n ? static_cast<float>(t.above) / t.n : NAN;
  }

 private:
  struct Hop {
    unsigned n = 0, above = 0;
    double sum = 0;
  };

  Hop total() const {
    Hop t;
    for (const Hop& h : window_) {
      t.n += h.n;
      t.above += h.above;
      t.sum += h.sum;
    }
    return t;
  }

  int hops_;
  float threshold_, fraction_;
  std::vector<Hop> window_;
  Hop cur_;
};
