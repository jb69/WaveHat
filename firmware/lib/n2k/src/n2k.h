// NMEA 2000 decoding for the WaveHat: the boat's own instruments, read off the bus.
//
// Platform-free (the desktop tests build it natively); the CAN side is src/n2k_bus.h. Only
// single-frame PGNs so far. Each PGN is a row in the table in n2k.cpp, so adding a value
// means adding a field here and a row there. Field layouts from canboat (docs/canboat.json).
//
//   129026  COG & SOG, rapid update     sog, cog (true only)
//   129025  position, rapid update      lat, lon
//   127250  vessel heading              heading (true, or magnetic + variation)
//   128259  speed                       stw (speed through water)
//   128267  water depth                 depth (below the transducer)
//   130306  wind data                   wind (true speed; apparent is ignored)
//   127252  heave                       heave, m, up positive (a B&G/Simrad Precision-9 compass
//                                       sends it at 10 Hz); also summed between results, so the
//                                       log can set the boat's own heave against the WaveHat's
//
// A boat can have several sources for one PGN (a chartplotter's GPS and the AIS's, say). Each
// PGN follows the first source it hears, and moves to another only after that one has been
// silent for kSourceTimeoutMs, so values don't jump between two receivers.

#pragma once

#include <cmath>
#include <cstdint>

namespace n2k {

constexpr uint32_t kSourceTimeoutMs = 5000;
constexpr uint8_t kNoSource = 0xFF;

// PGN and source address from a 29-bit NMEA 2000 (J1939) CAN identifier.
uint32_t pgn_of(uint32_t id);
inline uint8_t source_of(uint32_t id) { return id & 0xFF; }

struct Value {
  double v = NAN;   // SI units: m/s, m, rad; degrees for lat/lon
  uint32_t ms = 0;  // when it arrived (the caller's clock)
  uint8_t src = kNoSource;

  bool fresh(uint32_t now_ms, uint32_t max_age_ms) const {
    return !std::isnan(v) && now_ms - ms <= max_age_ms;
  }
};

// Heave from the bus since the last take_heave(): its mean and its RMS about that mean, m.
struct HeaveStats {
  uint32_t n = 0;
  double mean = NAN, rms = NAN;
};

// The latest of each value, or NAN where none has arrived within the age limit.
struct Nav {
  double sog = NAN, cog = NAN, lat = NAN, lon = NAN, heading = NAN, stw = NAN, depth = NAN,
         wind = NAN;
};

class Decoder {
 public:
  // Feeds one received frame (29-bit identifier). Returns true if it updated a value.
  bool handle(uint32_t id, const uint8_t* data, int len, uint32_t now_ms);

  Nav nav(uint32_t now_ms, uint32_t max_age_ms) const;

  // The bus heave's statistics since the last call, then starts a new sum.
  HeaveStats take_heave();

  Value sog, cog, lat, lon, heading, stw, depth, wind, heave;
  double heave_sum = 0, heave_sumsq = 0;  // since the last take_heave()
  uint32_t heave_n = 0;
  uint32_t frames = 0;   // every frame seen
  uint32_t decoded = 0;  // frames that updated a value

  static constexpr int kPgns = 7;  // rows in the table in n2k.cpp

 private:
  uint8_t follow_src_[kPgns] = {kNoSource, kNoSource, kNoSource, kNoSource,
                                kNoSource, kNoSource, kNoSource};
  uint32_t follow_ms_[kPgns] = {};
};

}  // namespace n2k
