// Accelerometer six-face calibration, editable in the SensESP web UI.
//
// Why it matters: an accelerometer offset (up to ~20 mg) or a per-axis scale
// mismatch (~1 %) is harmless on a level boat, but when the boat rolls it
// turns into false vertical acceleration at wave-group frequencies, which the
// double integration amplifies. On the desktop simulation, 15 degrees of RMS
// roll with an uncalibrated sensor can add ~10 % to Hs and much more to the
// instantaneous heave; after calibration the error is back to ~2 %.
//
// Procedure (README.md): rest the box on each of its six faces, note the
// "Raw accel" line on the status page for each, then per axis
//   offset = (reading_up + reading_down) / 2        [g]
//   scale  = 2 / (reading_up - reading_down)
// where reading_up is the axis value with that axis pointing up (about +1 g).

#pragma once

#include <ArduinoJson.h>

#include "sensesp/system/saveable.h"

class AccelCalibration : public sensesp::FileSystemSaveable {
 public:
  explicit AccelCalibration(const String& config_path)
      : sensesp::FileSystemSaveable(config_path) {
    load();
  }

  // a: m/s^2, chip frame, corrected in place
  void apply(float a[3]) const {
    for (int i = 0; i < 3; i++) a[i] = (a[i] - offset_g_[i] * kG) * scale_[i];
  }

  bool to_json(JsonObject& root) override {
    for (int i = 0; i < 3; i++) {
      root[String("offset_") + kAxis[i]] = offset_g_[i];
      root[String("scale_") + kAxis[i]] = scale_[i];
    }
    return true;
  }

  bool from_json(const JsonObject& config) override {
    for (int i = 0; i < 3; i++) {
      String o = String("offset_") + kAxis[i], s = String("scale_") + kAxis[i];
      if (config[o].is<float>()) offset_g_[i] = config[o];
      if (config[s].is<float>()) scale_[i] = config[s];
    }
    return true;
  }

 private:
  static constexpr float kG = 9.80665f;
  static constexpr const char* kAxis[3] = {"x", "y", "z"};
  float offset_g_[3] = {0, 0, 0};
  float scale_[3] = {1, 1, 1};
};

inline const String ConfigSchema(const AccelCalibration&) {
  return R"json({"type":"object","properties":{
    "offset_x":{"title":"X offset (g)","type":"number"},
    "offset_y":{"title":"Y offset (g)","type":"number"},
    "offset_z":{"title":"Z offset (g)","type":"number"},
    "scale_x":{"title":"X scale","type":"number"},
    "scale_y":{"title":"Y scale","type":"number"},
    "scale_z":{"title":"Z scale","type":"number"}}})json";
}
