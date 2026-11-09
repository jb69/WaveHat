// Checks lib/n2k against hand-built NMEA 2000 frames (layouts from canboat). Run by test_n2k.py.

#include <cmath>
#include <cstdio>
#include <cstdlib>

#include "n2k.h"

static int failures = 0;

#define CHECK(cond)                                           \
  do {                                                        \
    if (!(cond)) {                                            \
      std::printf("FAIL %s:%d: %s\n", __FILE__, __LINE__, #cond); \
      failures++;                                             \
    }                                                         \
  } while (0)

static bool near(double a, double b, double tol) { return std::fabs(a - b) <= tol; }

// 29-bit identifier for priority, PGN and source (PDU2 PGNs carry PS in the PGN).
static uint32_t id(uint32_t pgn, uint8_t src, uint32_t prio = 2) {
  return prio << 26 | pgn << 8 | src;
}

int main() {
  // PGN extraction: PDU2 keeps PS, PDU1 drops the destination address
  CHECK(n2k::pgn_of(id(129026, 7)) == 129026);
  CHECK(n2k::pgn_of(id(130306, 0x23, 3)) == 130306);
  CHECK(n2k::pgn_of(6u << 26 | 0xEA << 16 | 0x42 << 8 | 0x10) == 59904);  // ISO request to 0x42
  CHECK(n2k::source_of(id(129026, 0x7C)) == 0x7C);

  n2k::Decoder d;
  uint32_t t = 1000;

  // 129026: SOG 5.14 m/s (514), COG 1.5708 rad (15708), true reference
  uint8_t cogsog[8] = {0x01, 0xFC, 0x5C, 0x3D, 0x02, 0x02, 0xFF, 0xFF};
  CHECK(d.handle(id(129026, 10), cogsog, 8, t));
  CHECK(near(d.sog.v, 5.14, 1e-9));
  CHECK(near(d.cog.v, 1.5708, 1e-9));
  CHECK(d.sog.src == 10);

  // a second GPS on the bus is ignored while the first keeps talking...
  uint8_t other[8] = {0x01, 0xFC, 0x00, 0x00, 0xE8, 0x03, 0xFF, 0xFF};  // SOG 10 m/s
  CHECK(!d.handle(id(129026, 20), other, 8, t + 100));
  CHECK(near(d.sog.v, 5.14, 1e-9));
  // ...and taken over once the first has been silent for 5 s
  CHECK(d.handle(id(129026, 20), other, 8, t + 100 + n2k::kSourceTimeoutMs));
  CHECK(near(d.sog.v, 10.0, 1e-9) && d.sog.src == 20);

  // magnetic COG is not stored as COG; SOG still is
  n2k::Decoder m;
  uint8_t magcog[8] = {0x02, 0xFD, 0x5C, 0x3D, 0x64, 0x00, 0xFF, 0xFF};  // ref 1, SOG 1.00
  CHECK(m.handle(id(129026, 10), magcog, 8, t));
  CHECK(std::isnan(m.cog.v) && near(m.sog.v, 1.0, 1e-9));

  // SOG "not available" (0xFFFF) and no true COG: nothing set
  n2k::Decoder na;
  uint8_t nodata[8] = {0x01, 0xFD, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
  CHECK(!na.handle(id(129026, 10), nodata, 8, t));
  CHECK(std::isnan(na.sog.v));

  // 129025: -33.8568, 151.2153 (Sydney)
  int32_t lat = -338568000, lon = 1512153000;
  uint8_t pos[8];
  for (int i = 0; i < 4; i++) {
    pos[i] = static_cast<uint32_t>(lat) >> (8 * i);
    pos[4 + i] = static_cast<uint32_t>(lon) >> (8 * i);
  }
  CHECK(d.handle(id(129025, 10), pos, 8, t));
  CHECK(near(d.lat.v, -33.8568, 1e-9) && near(d.lon.v, 151.2153, 1e-9));

  // 127250: magnetic heading 6.2 rad (62000) + variation 0.2 rad (2000) wraps to ~0.1168 rad true
  uint8_t hdg[8] = {0x00, 0x30, 0xF2, 0xFF, 0x7F, 0xD0, 0x07, 0xFD};
  CHECK(d.handle(id(127250, 11), hdg, 8, t));
  CHECK(near(d.heading.v, 6.2 + 0.2 - 6.283185307179586, 1e-6));
  // magnetic without variation: not usable as true
  n2k::Decoder h2;
  uint8_t hdg_novar[8] = {0x00, 0x30, 0xF2, 0xFF, 0x7F, 0xFF, 0x7F, 0xFD};
  CHECK(!h2.handle(id(127250, 11), hdg_novar, 8, t));
  // true heading 1.0 rad
  uint8_t hdg_true[8] = {0x00, 0x10, 0x27, 0xFF, 0x7F, 0xFF, 0x7F, 0xFC};
  CHECK(h2.handle(id(127250, 11), hdg_true, 8, t));
  CHECK(near(h2.heading.v, 1.0, 1e-9));

  // 128259: STW 3.21 m/s (321)
  uint8_t spd[8] = {0x00, 0x41, 0x01, 0xFF, 0xFF, 0x00, 0xFF, 0xFF};
  CHECK(d.handle(id(128259, 12), spd, 8, t));
  CHECK(near(d.stw.v, 3.21, 1e-9));

  // 128267: depth 12.34 m (1234)
  uint8_t dep[8] = {0x00, 0xD2, 0x04, 0x00, 0x00, 0x00, 0x00, 0xFF};
  CHECK(d.handle(id(128267, 13), dep, 8, t));
  CHECK(near(d.depth.v, 12.34, 1e-9));

  // 130306: apparent wind ignored, true (boat-referenced) 7.5 m/s kept
  uint8_t awind[8] = {0x00, 0x20, 0x03, 0x00, 0x00, 0xFA, 0xFF, 0xFF};  // ref 2
  CHECK(!d.handle(id(130306, 14), awind, 8, t));
  uint8_t twind[8] = {0x00, 0xEE, 0x02, 0x00, 0x00, 0xFB, 0xFF, 0xFF};  // ref 3, 750
  CHECK(d.handle(id(130306, 14), twind, 8, t));
  CHECK(near(d.wind.v, 7.5, 1e-9));

  // 127252 heave: 0.01 m signed, "not available" skipped, and the sum between results
  n2k::Decoder hd;
  CHECK(hd.take_heave().n == 0 && std::isnan(hd.take_heave().rms));
  auto heave_frame = [&](int16_t cm, uint32_t when) {
    uint8_t f[8] = {0x05, static_cast<uint8_t>(cm), static_cast<uint8_t>(cm >> 8), 0x00, 0x00, 0xF0, 0xFF, 0xFF};
    return hd.handle(id(127252, 0x30, 3), f, 8, when);
  };
  CHECK(heave_frame(-123, t));
  CHECK(near(hd.heave.v, -1.23, 1e-9) && hd.heave.src == 0x30);
  uint8_t noheave[8] = {0x05, 0xFF, 0x7F, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
  CHECK(!hd.handle(id(127252, 0x30, 3), noheave, 8, t));
  hd.take_heave();
  // 0.50 m amplitude at 8 s, 10 Hz for 80 s, riding on a 0.20 m offset: RMS 0.3536 about 0.20
  for (int i = 0; i < 800; i++)
    heave_frame(static_cast<int16_t>(std::lround(20.0 + 50.0 * std::sin(2 * M_PI * i / 80.0))), t + 100 * i);
  n2k::HeaveStats hs = hd.take_heave();
  CHECK(hs.n == 800 && near(hs.mean, 0.20, 0.002) && near(hs.rms, 0.5 / std::sqrt(2.0), 0.003));
  CHECK(hd.take_heave().n == 0);

  // short frames and other PGNs are counted but not decoded
  CHECK(!d.handle(id(129026, 10), cogsog, 6, t));
  CHECK(!d.handle(id(127245, 10), cogsog, 8, t));  // rudder

  // nav(): stale values come back NAN
  n2k::Nav fresh = d.nav(t + 1000, 30000);
  CHECK(near(fresh.depth, 12.34, 1e-9) && near(fresh.wind, 7.5, 1e-9));
  n2k::Nav stale = d.nav(t + 31000, 30000);
  CHECK(std::isnan(stale.depth) && std::isnan(stale.lat));
  CHECK(near(stale.sog, 10.0, 1e-9));  // arrived at t + 5100

  std::printf("%s: %u frames, %u decoded\n", failures ? "FAILED" : "ok",
              static_cast<unsigned>(d.frames), static_cast<unsigned>(d.decoded));
  return failures ? 1 : 0;
}
