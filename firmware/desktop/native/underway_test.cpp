// Checks lib/underway (environment.waves.underway). Run by test_native_libs.py.

#include <cmath>
#include <cstdio>

#include "underway.h"

static int failures = 0;

#define CHECK(cond)                                               \
  do {                                                            \
    if (!(cond)) {                                                \
      std::printf("FAIL %s:%d: %s\n", __FILE__, __LINE__, #cond); \
      failures++;                                                 \
    }                                                             \
  } while (0)

constexpr int kPerHop = 315;  // 4 Hz SOG samples in one 78.8 s hop
constexpr float kKn = 0.514444f;

// Feeds `hops` hops of SOG from f(sample index within the run).
template <typename F>
static void feed(UnderwayTracker& u, int hops, F f) {
  static int k = 0;
  for (int h = 0; h < hops; h++) {
    for (int i = 0; i < kPerHop; i++) u.sample(f(k++));
    u.end_hop();
  }
}

int main() {
  // No SOG at all: unknown
  UnderwayTracker none;
  feed(none, 15, [](int) { return NAN; });
  CHECK(none.state() == -1 && std::isnan(none.mean_sog()));

  // At anchor, 0.3 kn of swinging, with one 3 kn spike (a GPS jump): not underway.
  // (The old rule, any sample above 1.5 kn in the window, latched for 20 minutes.)
  UnderwayTracker anchor;
  feed(anchor, 15, [](int k) { return (k == 1000 ? 3.0f : 0.3f) * kKn; });
  CHECK(anchor.state() == 0);

  // Sheering in gusts: 1.8 kn for 20 s every 2 minutes (17 % of the time): not underway
  UnderwayTracker sheer;
  feed(sheer, 15, [](int k) { return ((k % 480) < 80 ? 1.8f : 0.4f) * kKn; });
  CHECK(sheer.state() == 0);
  CHECK(sheer.fraction_above() > 0.15f && sheer.fraction_above() < 0.2f);

  // Motoring at 5 kn: underway from the first hop
  UnderwayTracker motor;
  feed(motor, 1, [](int) { return 5.0f * kKn; });
  CHECK(motor.state() == 1);

  // ...then anchored: still underway while more than a quarter of the window was moving,
  // clear once the moving hops are mostly out (15 hops after arrival at the latest)
  feed(motor, 14, [](int) { return 5.0f * kKn; });
  int hops_to_clear = 0;
  while (motor.state() == 1 && hops_to_clear < 20) {
    feed(motor, 1, [](int) { return 0.2f * kKn; });
    hops_to_clear++;
  }
  CHECK(hops_to_clear == 12);  // 3 moving hops of 15 left = 20 %

  // Motoring for 5 minutes (4 hops) in an otherwise anchored window: flagged
  UnderwayTracker brief;
  feed(brief, 11, [](int) { return 0.2f * kKn; });
  feed(brief, 4, [](int) { return 2.0f * kKn; });
  CHECK(brief.state() == 1);

  // Drifting at 1 kn with the tide: below the threshold, not underway
  UnderwayTracker drift;
  feed(drift, 15, [](int) { return 1.0f * kKn; });
  CHECK(drift.state() == 0);

  // The window holds 15 hops, and reset() forgets everything
  UnderwayTracker w;
  feed(w, 15, [](int) { return 3.0f * kKn; });
  feed(w, 15, [](int) { return 0.0f; });
  CHECK(w.state() == 0 && w.mean_sog() == 0.0f);
  w.reset();
  CHECK(w.state() == -1);

  std::printf("%s\n", failures ? "FAILED" : "ok");
  return failures ? 1 : 0;
}
