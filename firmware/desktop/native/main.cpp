// Desktop harness for lib/wavemath: feeds a recorded or simulated IMU stream
// through WaveProcessor and prints the last result. Used by test_wavemath.py.
//
//   c++ -std=c++17 -O2 -I ../../lib/wavemath/src main.cpp ../../lib/wavemath/src/*.cpp -o wavemath_native
//   ./wavemath_native imu.bin 26 [rx ry rz]   # imu.bin: float32 rows gx gy gz ax ay az
//                                             # r: IMU position from the roll/pitch centre, m
//
// Output: hs tp tz heave_rms heave_rms_td segments periods_valid peak_ratio,
// then the time per segment computation in microseconds on this machine.

#include <chrono>
#include <cstdio>
#include <cstdlib>

#include "wavemath.h"

int main(int argc, char** argv) {
  if (argc < 2) {
    std::fprintf(stderr, "usage: %s imu.bin [fs]\n", argv[0]);
    return 2;
  }
  FILE* f = std::fopen(argv[1], "rb");
  if (!f) {
    std::perror(argv[1]);
    return 1;
  }
  wavemath::Config cfg;
  if (argc > 2) cfg.fs = static_cast<float>(std::atof(argv[2]));
  for (int i = 0; i < 3 && argc > 3 + i; i++) cfg.r_imu[i] = static_cast<float>(std::atof(argv[3 + i]));
  wavemath::WaveProcessor p(cfg);
  float row[6];
  double seg_us = 0;
  int segs = 0;
  bool any = false;
  while (std::fread(row, sizeof(float), 6, f) == 6) {
    auto t0 = std::chrono::steady_clock::now();
    bool ready = p.push(row, row + 3);
    if (ready) {
      auto t1 = std::chrono::steady_clock::now();
      seg_us += std::chrono::duration<double, std::micro>(t1 - t0).count();
      segs++;
      any = true;
    }
  }
  std::fclose(f);
  if (!any) {
    std::fprintf(stderr, "not enough data for a result\n");
    return 1;
  }
  const auto& s = p.stats();
  std::printf("%.6f %.6f %.6f %.6f %.6f %d %d %.4f\n", s.hs, s.tp, s.tz, s.heave_rms,
              s.heave_rms_td, s.segments, s.periods_valid ? 1 : 0, s.peak_ratio);
  std::printf("%.1f\n", seg_us / segs);
  return 0;
}
