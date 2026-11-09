#include "n2k.h"

namespace n2k {

namespace {

// Little-endian fields. The top values of each width mean "not available", "error" or reserved.
uint16_t u16(const uint8_t* d) { return d[0] | d[1] << 8; }
int16_t s16(const uint8_t* d) { return static_cast<int16_t>(u16(d)); }
uint32_t u32(const uint8_t* d) { return u16(d) | static_cast<uint32_t>(u16(d + 2)) << 16; }
int32_t s32(const uint8_t* d) { return static_cast<int32_t>(u32(d)); }
bool ok(uint16_t v) { return v < 0xFFFD; }
bool ok(int16_t v) { return v < 0x7FFD; }
bool ok(uint32_t v) { return v < 0xFFFFFFFDu; }
bool ok(int32_t v) { return v < 0x7FFFFFFD; }

void set(Value& out, double v, uint32_t now_ms, uint8_t src) {
  out.v = v;
  out.ms = now_ms;
  out.src = src;
}

constexpr double kTwoPi = 6.283185307179586;

// Each returns true if it set a value.
bool cog_sog(Decoder& d, const uint8_t* b, uint32_t now, uint8_t src) {
  uint16_t cog = u16(b + 2), sog = u16(b + 4);
  bool cog_ok = (b[1] & 3) == 0 && ok(cog);  // true COG only
  if (ok(sog)) set(d.sog, sog * 0.01, now, src);
  if (cog_ok) set(d.cog, cog * 1e-4, now, src);
  return ok(sog) || cog_ok;
}

bool position(Decoder& d, const uint8_t* b, uint32_t now, uint8_t src) {
  int32_t lat = s32(b), lon = s32(b + 4);
  if (!ok(lat) || !ok(lon)) return false;
  set(d.lat, lat * 1e-7, now, src);
  set(d.lon, lon * 1e-7, now, src);
  return true;
}

bool heading(Decoder& d, const uint8_t* b, uint32_t now, uint8_t src) {
  uint16_t hdg = u16(b + 1);
  int16_t var = s16(b + 5);
  int ref = b[7] & 3;
  if (!ok(hdg)) return false;
  double h = hdg * 1e-4;
  if (ref == 1) {  // magnetic: true needs the variation, sent in the same PGN
    if (!ok(var)) return false;
    h = std::fmod(h + var * 1e-4 + kTwoPi, kTwoPi);
  } else if (ref != 0) {
    return false;
  }
  set(d.heading, h, now, src);
  return true;
}

bool speed(Decoder& d, const uint8_t* b, uint32_t now, uint8_t src) {
  uint16_t stw = u16(b + 1);
  if (!ok(stw)) return false;
  set(d.stw, stw * 0.01, now, src);
  return true;
}

bool depth(Decoder& d, const uint8_t* b, uint32_t now, uint8_t src) {
  uint32_t dep = u32(b + 1);
  if (!ok(dep)) return false;
  set(d.depth, dep * 0.01, now, src);
  return true;
}

bool wind(Decoder& d, const uint8_t* b, uint32_t now, uint8_t src) {
  uint16_t spd = u16(b + 1);
  int ref = b[5] & 7;  // 0 true (north), 1 magnetic, 2 apparent, 3 true (boat), 4 true (water)
  if (ref == 2 || ref > 4 || !ok(spd)) return false;
  set(d.wind, spd * 0.01, now, src);
  return true;
}

// 127252: SID, heave int16 in 0.01 m (up positive), delay uint16 in 0.01 s, delay source.
bool heave(Decoder& d, const uint8_t* b, uint32_t now, uint8_t src) {
  int16_t h = s16(b + 1);
  if (!ok(h)) return false;
  double v = h * 0.01;
  set(d.heave, v, now, src);
  d.heave_sum += v;
  d.heave_sumsq += v * v;
  d.heave_n++;
  return true;
}

struct Row {
  uint32_t pgn;
  bool (*decode)(Decoder&, const uint8_t*, uint32_t, uint8_t);
};

constexpr Row kTable[] = {
    {129026, cog_sog}, {129025, position}, {127250, heading},
    {128259, speed},   {128267, depth},    {130306, wind},
    {127252, heave},
};
static_assert(sizeof(kTable) / sizeof(kTable[0]) == Decoder::kPgns, "update Decoder::kPgns");

}  // namespace

uint32_t pgn_of(uint32_t id) {
  uint32_t pgn = (id >> 8) & 0x3FFFF;    // EDP, DP, PF, PS
  if (((pgn >> 8) & 0xFF) < 240) pgn &= 0x3FF00;  // PDU1: PS is the destination address
  return pgn;
}

bool Decoder::handle(uint32_t id, const uint8_t* data, int len, uint32_t now_ms) {
  frames++;
  if (len < 8) return false;  // every PGN here is a full 8-byte frame
  uint32_t pgn = pgn_of(id);
  uint8_t src = source_of(id);
  for (int i = 0; i < kPgns; i++) {
    if (kTable[i].pgn != pgn) continue;
    // Follow one source per PGN; move on only once it has gone quiet.
    if (follow_src_[i] != src && follow_src_[i] != kNoSource &&
        now_ms - follow_ms_[i] < kSourceTimeoutMs)
      return false;
    if (!kTable[i].decode(*this, data, now_ms, src)) return false;
    follow_src_[i] = src;
    follow_ms_[i] = now_ms;
    decoded++;
    return true;
  }
  return false;
}

HeaveStats Decoder::take_heave() {
  HeaveStats s;
  s.n = heave_n;
  if (heave_n > 0) {
    s.mean = heave_sum / heave_n;
    double var = heave_sumsq / heave_n - s.mean * s.mean;
    s.rms = var > 0 ? std::sqrt(var) : 0.0;
  }
  heave_sum = heave_sumsq = 0;
  heave_n = 0;
  return s;
}

Nav Decoder::nav(uint32_t now_ms, uint32_t max_age_ms) const {
  auto get = [&](const Value& v) { return v.fresh(now_ms, max_age_ms) ? v.v : NAN; };
  Nav n;
  n.sog = get(sog);
  n.cog = get(cog);
  n.lat = get(lat);
  n.lon = get(lon);
  n.heading = get(heading);
  n.stw = get(stw);
  n.depth = get(depth);
  n.wind = get(wind);
  return n;
}

}  // namespace n2k
