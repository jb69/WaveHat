// Battery mode, editable in the SensESP web UI: a WaveHat running from a 1S LiPo on the XIAO's own
// charger (rev B: the cell on the J7 holes, through the carrier pads under the module).
//
// What it changes:
//   - The CAN controller stays off. A battery build has no bus, and usually has JP8-JP10 cut (the
//     transceiver unpowered), so D0 would float; listening to it would only count error frames.
//   - Sleep. After the board has been still for sleep_after_min minutes (no motion above about
//     30 mg or 1 deg/s in any poll), the firmware logs a line, puts the LSM6DSO into its 12.5 Hz
//     low-power mode with wake-on-motion on INT1, and deep-sleeps the ESP32 until INT1 rises
//     (JP4 must be bridged so INT1 reaches D2) or, as a fallback if it never does, until a timer.
//     A wake is a reboot: SensESP starts again and the 20-minute window starts from nothing, which
//     is right, since the sea state before a sleep says nothing about the sea state after it.
//     0 minutes = never sleep.
// Every result is in /waves.csv on the NAND whatever the mode (wave_log.h), so a battery board with
// no Wi-Fi still keeps its record.
//
// Draw: the XIAO, the IMU and NAND writes come to roughly 40-60 mA with Wi-Fi on, so a 1000 mAh
// cell is about a day awake; the deep-sleep floor is the XIAO's own (tens of uA) plus the board's
// pull-ups. Not yet measured on a rev B board (7 Nov 2026).

#pragma once

#include <ArduinoJson.h>

#include "sensesp/system/saveable.h"

class PowerMode : public sensesp::FileSystemSaveable {
 public:
  explicit PowerMode(const String& config_path) : sensesp::FileSystemSaveable(config_path) { load(); }

  bool battery = false;
  int sleep_after_min = 0;       // 0: never
  int wake_timer_min = 360;      // fallback wake if INT1 never rises (JP4 open)

  bool to_json(JsonObject& root) override {
    root["battery"] = battery;
    root["sleep_after_min"] = sleep_after_min;
    root["wake_timer_min"] = wake_timer_min;
    return true;
  }
  bool from_json(const JsonObject& config) override {
    if (config["battery"].is<bool>()) battery = config["battery"];
    if (config["sleep_after_min"].is<int>()) sleep_after_min = constrain(static_cast<int>(config["sleep_after_min"]), 0, 1440);
    if (config["wake_timer_min"].is<int>()) wake_timer_min = constrain(static_cast<int>(config["wake_timer_min"]), 1, 1440);
    return true;
  }
};

inline const String ConfigSchema(const PowerMode&) {
  return R"json({"type":"object","properties":{
    "battery":{"title":"Battery mode (no CAN; sleep when still)","type":"boolean"},
    "sleep_after_min":{"title":"Sleep after this many still minutes (0 = never)","type":"integer"},
    "wake_timer_min":{"title":"Wake anyway after this many minutes asleep","type":"integer"}}})json";
}
