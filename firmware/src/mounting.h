// Where the WaveHat sits in the boat, editable in the SensESP web UI.
//
// Why it matters: the IMU measures the motion of the point it is bolted to. When the boat
// rolls and pitches, a point away from the hull's roll/pitch centre also moves up and down,
// and that reads as heave: 1 m off the centreline adds about +10 % to Hs in a 2 m / 8 s sea
// and +30 to +90 % in a 1 m / 6 s sea with 5-15 degrees of roll (desktop/lever_arm.py). With
// the position entered, the wave maths moves the measured acceleration back to the centre.
//
// Measure from the hull's roll/pitch centre, in metres, with the box mounted bow forward:
//   x  to starboard of the centreline (port is negative)
//   y  forward of the pitch centre (about the centre of the waterplane: near midships on most
//      yachts, a little aft of it on many; aft is negative)
//   z  above the waterline (it barely affects heave)
// An error of 20 % in the entry leaves about 20 % of the effect. See README.md, Mounting.

#pragma once

#include <ArduinoJson.h>

#include "sensesp/system/saveable.h"

class MountingPosition : public sensesp::FileSystemSaveable {
 public:
  explicit MountingPosition(const String& config_path) : sensesp::FileSystemSaveable(config_path) {
    load();
    loaded_ = true;  // from here on, a change comes from the web UI
  }

  const float* r() const { return r_; }

  // True once after the position was changed in the web UI (the analysis restarts).
  bool take_changed() {
    bool c = changed_;
    changed_ = false;
    return c;
  }

  bool to_json(JsonObject& root) override {
    for (int i = 0; i < 3; i++) root[kKey[i]] = r_[i];
    return true;
  }

  bool from_json(const JsonObject& config) override {
    for (int i = 0; i < 3; i++) {
      if (config[kKey[i]].is<float>()) {
        float v = config[kKey[i]];
        if (fabsf(v) <= 30.0f && v != r_[i]) {  // metres; anything bigger is a typo
          r_[i] = v;
          changed_ = loaded_;
        }
      }
    }
    return true;
  }

 private:
  static constexpr const char* kKey[3] = {"x_m", "y_m", "z_m"};
  float r_[3] = {0, 0, 0};
  bool loaded_ = false;
  bool changed_ = false;
};

inline const String ConfigSchema(const MountingPosition&) {
  return R"json({"type":"object","properties":{
    "x_m":{"title":"Starboard of the centreline (m, port negative)","type":"number"},
    "y_m":{"title":"Forward of the pitch centre (m, aft negative)","type":"number"},
    "z_m":{"title":"Above the waterline (m)","type":"number"}}})json";
}
