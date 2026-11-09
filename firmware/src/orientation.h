// How the board is mounted, editable in the SensESP web UI: maps the chip's axes to the body
// frame the wave maths uses (X starboard, Y bow, Z up).
//
// The silkscreen arrows on the WaveHat are the LSM6DSO's own axes (checked on rev A board 2,
// 29 Oct 2026: raising the "Y bow" end gives +Y, raising the X end gives +X, Z is up out of the
// component side). Mounted the way the yacht enclosure holds it, bow arrow forward and component
// side up, the chip frame is the body frame and nothing changes. Any other mounting is a rotation
// of the board about its vertical, with or without a flip, so two settings cover it:
//   bow_arrow       which way the silkscreen "Y bow" arrow points: forward, aft, port, starboard
//   component_side  up (parts on top) or down (parts underneath)
// The lever arm (mounting.h) is entered in the body frame and is not affected.
//
// Applied after the accelerometer calibration (which is per chip axis) and before the wave maths;
// a change restarts the analysis. The "Raw accel" status line stays in the chip frame, which is
// what the six-face calibration procedure reads.

#pragma once

#include <ArduinoJson.h>

#include "sensesp/system/saveable.h"

class Orientation : public sensesp::FileSystemSaveable {
 public:
  explicit Orientation(const String& config_path) : sensesp::FileSystemSaveable(config_path) {
    load();
    rebuild();
    loaded_ = true;
  }

  // v: chip frame in, body frame out (gyro or accel alike).
  void apply(float v[3]) const {
    float x = v[0], y = v[1], z = v[2];
    for (int i = 0; i < 3; i++) v[i] = x * s_[i] + y * f_[i] + z * u_[i];
  }

  bool take_changed() {
    bool c = changed_;
    changed_ = false;
    return c;
  }

  String describe() const {
    return String("bow arrow ") + kDir[bow_] + ", component side " + (down_ ? "down" : "up") +
           (bow_ == 0 && !down_ ? " (chip frame = body frame)" : "");
  }

  bool to_json(JsonObject& root) override {
    root["bow_arrow"] = kDir[bow_];
    root["component_side"] = down_ ? "down" : "up";
    return true;
  }

  bool from_json(const JsonObject& config) override {
    int bow = bow_;
    bool down = down_;
    if (config["bow_arrow"].is<const char*>()) {
      const char* d = config["bow_arrow"];
      for (int i = 0; i < 4; i++)
        if (strcmp(d, kDir[i]) == 0) bow = i;
    }
    if (config["component_side"].is<const char*>()) down = strcmp(config["component_side"], "down") == 0;
    if (bow != bow_ || down != down_) {
      bow_ = bow;
      down_ = down;
      rebuild();
      changed_ = loaded_;
    }
    return true;
  }

 private:
  static constexpr const char* kDir[4] = {"forward", "aft", "port", "starboard"};

  // Body-frame vectors of the chip's Y (f_, the bow arrow), Z (u_) and X (s_ = f x u).
  void rebuild() {
    const float dirs[4][3] = {{0, 1, 0}, {0, -1, 0}, {-1, 0, 0}, {1, 0, 0}};
    for (int i = 0; i < 3; i++) {
      f_[i] = dirs[bow_][i];
      u_[i] = 0;
    }
    u_[2] = down_ ? -1.0f : 1.0f;
    s_[0] = f_[1] * u_[2] - f_[2] * u_[1];
    s_[1] = f_[2] * u_[0] - f_[0] * u_[2];
    s_[2] = f_[0] * u_[1] - f_[1] * u_[0];
  }

  int bow_ = 0;         // forward: the yacht enclosure's bow end
  bool down_ = false;
  float f_[3], u_[3], s_[3];
  bool loaded_ = false;
  bool changed_ = false;
};

inline const String ConfigSchema(const Orientation&) {
  return R"json({"type":"object","properties":{
    "bow_arrow":{"title":"The silkscreen 'Y bow' arrow points","type":"string","enum":["forward","aft","port","starboard"]},
    "component_side":{"title":"Component side","type":"string","enum":["up","down"]}}})json";
}
