// GNSS on the rev B GNSS port J5 (or a lead on J6 pins 6/7): NMEA 0183 over the XIAO's UART,
// D7 = RX from the module, D6 = TX to it (nothing is sent; the module runs at its own defaults).
//
// Reads RMC (fix, position, SOG, COG, date and time) and GGA (fix quality, satellites) from any
// talker (GP, GN, GA...), with the checksum checked. What the rest of the firmware uses:
//   - SOG for the underway flag, when the NMEA 2000 bus gives none (main.cpp current_nav());
//   - position, SOG and COG in the log's columns, likewise when the bus has none;
//   - the date and time to set the clock when there is no internet for NTP, so the log's UTC
//     column is filled at anchor with no Wi-Fi.
// A Pixhawk-style module also carries a compass on the I2C bus (J5 pins 4/5). This firmware only
// reports whether one answers at a known address (0x0C AK09916, 0x0D QMC5883L, 0x1E HMC5883L or
// LIS3MDL, 0x30 MMC5983) on the status page; it does not read a heading. One IMU and no compass
// still gives no wave direction.
//
// Enabled and the baud rate are web-UI settings (GnssConfig): u-blox modules default to 9600.
// Not yet run with a module: the rev B boards have not been built (7 Nov 2026).

#pragma once

#include <Arduino.h>
#include <ArduinoJson.h>
#include <HardwareSerial.h>
#include <Wire.h>
#include <sys/time.h>

#include "board.h"
#include "n2k.h"
#include "sensesp/system/saveable.h"

class GnssConfig : public sensesp::FileSystemSaveable {
 public:
  explicit GnssConfig(const String& config_path) : sensesp::FileSystemSaveable(config_path) { load(); }
  bool enabled = false;
  int baud = 9600;

  bool to_json(JsonObject& root) override {
    root["enabled"] = enabled;
    root["baud"] = baud;
    return true;
  }
  bool from_json(const JsonObject& config) override {
    if (config["enabled"].is<bool>()) enabled = config["enabled"];
    if (config["baud"].is<int>()) {
      int b = config["baud"];
      if (b == 4800 || b == 9600 || b == 19200 || b == 38400 || b == 57600 || b == 115200) baud = b;
    }
    return true;
  }
};

inline const String ConfigSchema(const GnssConfig&) {
  return R"json({"type":"object","properties":{
    "enabled":{"title":"GNSS module on J5 (or J6 pins 6/7)","type":"boolean"},
    "baud":{"title":"Baud rate (u-blox default 9600)","type":"integer","enum":[4800,9600,19200,38400,57600,115200]}}})json";
}

class Gnss {
 public:
  bool begin(int baud) {
    serial_.begin(baud, SERIAL_8N1, board::kGnssRxPin, board::kGnssTxPin);
    serial_.setRxBufferSize(1024);
    baud_ = baud;
    ok_ = true;
    return true;
  }

  // Drain the UART; call often (every IMU poll is fine: 250 ms is under a second of NMEA at 9600).
  void poll() {
    if (!ok_) return;
    while (serial_.available()) {
      char c = serial_.read();
      if (c == '$') {
        n_ = 0;
        in_ = true;
      } else if (in_ && (c == '\r' || c == '\n')) {
        if (n_ > 0) {
          line_[n_] = 0;
          handle(line_);
        }
        in_ = false;
      } else if (in_ && n_ < sizeof(line_) - 1) {
        line_[n_++] = c;
      }
    }
  }

  // The module's values, NAN where none is fresh. Same shape as the bus's.
  n2k::Nav nav(uint32_t now_ms, uint32_t max_age_ms) const {
    n2k::Nav v;
    if (fix_ && now_ms - fix_ms_ <= max_age_ms) {
      v.lat = lat_;
      v.lon = lon_;
      v.sog = sog_;
      v.cog = cog_;
    }
    return v;
  }

  String status(uint32_t now_ms) const {
    if (!ok_) return "off";
    char buf[160];
    if (sentences_ == 0) {
      snprintf(buf, sizeof(buf), "no NMEA yet at %d baud on D7 (RX)", baud_);
    } else if (!fix_ || now_ms - fix_ms_ > 5000) {
      snprintf(buf, sizeof(buf), "%u sentences, no fix (%d satellites)", static_cast<unsigned>(sentences_), sats_);
    } else {
      snprintf(buf, sizeof(buf), "fix, %d satellites, %.5f %.5f, SOG %.1f kn, COG %.0f", sats_, lat_, lon_,
               sog_ * 1.943844, cog_ * 57.29578);
    }
    String s(buf);
    if (compass_addr_) s += String("; compass answers at 0x") + String(compass_addr_, HEX) + " (not read)";
    return s;
  }

  // Looks for a magnetometer on the I2C bus once; call after the IMU is up.
  void probe_compass(TwoWire& wire) {
    const uint8_t addrs[] = {0x0C, 0x0D, 0x1E, 0x30};
    for (uint8_t a : addrs) {
      wire.beginTransmission(a);
      if (wire.endTransmission() == 0) {
        compass_addr_ = a;
        return;
      }
    }
  }

  bool clock_set() const { return clock_set_; }

 private:
  // One sentence without the '$', with its "*hh" checksum.
  void handle(char* s) {
    char* star = strchr(s, '*');
    if (!star) return;
    uint8_t sum = 0;
    for (char* p = s; p < star; p++) sum ^= static_cast<uint8_t>(*p);
    if (static_cast<uint8_t>(strtol(star + 1, nullptr, 16)) != sum) return;
    *star = 0;
    sentences_++;
    // split on commas (empty fields stay empty)
    char* f[20];
    int nf = 0;
    f[nf++] = s;
    for (char* p = s; *p && nf < 20; p++)
      if (*p == ',') {
        *p = 0;
        f[nf++] = p + 1;
      }
    if (nf < 7 || strlen(f[0]) < 5) return;
    const char* type = f[0] + 2;  // after the two-letter talker
    if (strcmp(type, "RMC") == 0 && nf >= 10) {
      bool valid = f[2][0] == 'A';
      if (valid) {
        lat_ = coord(f[3], f[4][0]);
        lon_ = coord(f[5], f[6][0]);
        sog_ = f[7][0] ? atof(f[7]) * 0.514444 : NAN;
        cog_ = f[8][0] ? atof(f[8]) * 0.01745329 : NAN;
        fix_ = true;
        fix_ms_ = millis();
        if (!clock_set_ && strlen(f[1]) >= 6 && strlen(f[9]) == 6) set_clock(f[9], f[1]);
      } else {
        fix_ = false;
      }
    } else if (strcmp(type, "GGA") == 0 && nf >= 8) {
      sats_ = atoi(f[7]);
    }
  }

  // "ddmm.mmmm" with a hemisphere letter to signed degrees.
  static double coord(const char* s, char hemi) {
    if (!s[0]) return NAN;
    double v = atof(s);
    double deg = floor(v / 100.0);
    double d = deg + (v - deg * 100.0) / 60.0;
    return (hemi == 'S' || hemi == 'W') ? -d : d;
  }

  // RMC date ddmmyy and time hhmmss[.sss]: set the clock only if nothing (NTP) has.
  void set_clock(const char* date, const char* t) {
    time_t now = time(nullptr);
    if (now > 1700000000) {  // already set
      clock_set_ = true;
      return;
    }
    int dd = (date[0] - '0') * 10 + (date[1] - '0');
    int mm = (date[2] - '0') * 10 + (date[3] - '0');
    int yy = 2000 + (date[4] - '0') * 10 + (date[5] - '0');
    int hh = (t[0] - '0') * 10 + (t[1] - '0');
    int mi = (t[2] - '0') * 10 + (t[3] - '0');
    int ss = (t[4] - '0') * 10 + (t[5] - '0');
    if (mm < 1 || mm > 12 || dd < 1 || dd > 31 || hh > 23 || mi > 59 || ss > 60) return;
    // days from civil (Howard Hinnant), so no time-zone library is involved
    int y = yy - (mm <= 2);
    int era = (y >= 0 ? y : y - 399) / 400;
    unsigned yoe = static_cast<unsigned>(y - era * 400);
    unsigned doy = (153 * (mm + (mm > 2 ? -3 : 9)) + 2) / 5 + dd - 1;
    unsigned doe = yoe * 365 + yoe / 4 - yoe / 100 + doy;
    long days = era * 146097L + static_cast<long>(doe) - 719468L;
    struct timeval tv = {static_cast<time_t>(days * 86400L + hh * 3600 + mi * 60 + ss), 0};
    settimeofday(&tv, nullptr);
    clock_set_ = true;
  }

  HardwareSerial serial_{1};
  bool ok_ = false;
  int baud_ = 9600;
  char line_[96];
  size_t n_ = 0;
  bool in_ = false;
  uint32_t sentences_ = 0;
  bool fix_ = false;
  uint32_t fix_ms_ = 0;
  double lat_ = NAN, lon_ = NAN, sog_ = NAN, cog_ = NAN;
  int sats_ = 0;
  bool clock_set_ = false;
  uint8_t compass_addr_ = 0;
};
