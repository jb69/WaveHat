// Sea-state log on the WaveHat's SD NAND (256 MB, soldered under the XIAO).
//
// The chip speaks the SD protocol, so Arduino's SD library mounts it like a card, in SPI mode on the
// XIAO's SPI pins: D8 = SCK, D9 = MISO, D10 = MOSI, D3 = CS (through JP7, bridged as built). The first
// mount formats it (FAT). One line per result (every ~79 s), about 130 bytes with the NMEA 2000 columns:
// about 50 MB a year, so the 256 MB lasts about five years.
//
// The same chip is what VESC Express logs to when the board runs that firmware instead
// (firmware/vesc_express/).

#pragma once

#include <Arduino.h>
#include <SD.h>
#include <SPI.h>
#include <time.h>

#include "n2k.h"
#include "wavemath.h"

class WaveLog {
 public:
  static constexpr const char* kPath = "/waves.csv";

  bool begin() {
    SPI.begin(D8, D9, D10, D3);
    ok_ = SD.begin(D3, SPI, 20000000, "/sd", 5, true);
    // A log from before the bus-heave columns keeps its own header: set it aside, start anew.
    if (ok_ && SD.exists(kPath)) {
      File old = SD.open(kPath, FILE_READ);
      String header = old ? old.readStringUntil('\n') : String();
      if (old) old.close();
      if (header.indexOf("bus_heave_rms_m") < 0) {
        char name[32];
        for (int i = 1; i < 100; i++) {
          snprintf(name, sizeof(name), "/waves-old-%d.csv", i);
          if (!SD.exists(name)) break;
        }
        SD.rename(kPath, name);
      }
    }
    if (ok_ && !SD.exists(kPath)) {
      File f = SD.open(kPath, FILE_WRITE);
      if (f) {
        f.println("uptime_s,utc,hs_m,tp_s,tz_s,heave_rms_m,heave_rms_td_m,segments,fs_hz,underway,"
                  "lat,lon,sog_mps,cog_deg,heading_deg,stw_mps,depth_m,wind_mps,"
                  "periods_valid,peak_ratio,window_sog_mps,"
                  "bus_heave_rms_m,bus_heave_mean_m,bus_heave_n");
        f.close();
      }
    }
    return ok_;
  }

  bool ok() const { return ok_; }

  // underway: 1, 0, or -1 when unknown (no SOG from the bus or Signal K); window_sog: the
  // window's mean SOG, m/s. nav: the boat's values at the time of the result, empty columns
  // where unknown (COG and heading true). Tp and Tz are logged even when periods_valid is 0
  // (Signal K gets null then), so the gate can be revisited. bus_heave: the heave another
  // instrument put on the NMEA 2000 bus (PGN 127252) over the last hop (~79 s), RMS about its
  // mean; the hops of a window combine as sqrt(mean of rms^2), to set against heave_rms_td_m.
  void append(const wavemath::Stats& s, int underway, float window_sog, const n2k::Nav& nav,
              const n2k::HeaveStats& bus_heave = n2k::HeaveStats()) {
    if (!ok_) return;
    File f = SD.open(kPath, FILE_APPEND);
    if (!f) {
      ok_ = false;  // card gone or failed: stop trying until the next boot
      return;
    }
    char utc[24] = "";
    time_t now = time(nullptr);
    if (now > 1700000000) {  // clock set (NTP); otherwise leave the column empty
      struct tm t;
      gmtime_r(&now, &t);
      strftime(utc, sizeof(utc), "%Y-%m-%dT%H:%M:%SZ", &t);
    }
    f.printf("%lu,%s,%.3f,%.2f,%.2f,%.3f,%.3f,%d,%.3f,%s",
             static_cast<unsigned long>(millis() / 1000), utc, s.hs, s.tp, s.tz, s.heave_rms,
             s.heave_rms_td, s.segments, s.fs, underway < 0 ? "" : (underway ? "1" : "0"));
    constexpr double kDeg = 57.29577951308232;
    const double cols[11] = {nav.lat,   nav.lon,   nav.sog, nav.cog * kDeg, nav.heading * kDeg,
                             nav.stw,   nav.depth, nav.wind, s.periods_valid ? 1.0 : 0.0,
                             s.peak_ratio, window_sog};
    const char* fmt[11] = {",%.6f", ",%.6f", ",%.2f", ",%.1f", ",%.1f", ",%.2f",
                           ",%.2f", ",%.2f", ",%.0f", ",%.1f", ",%.2f"};
    for (int i = 0; i < 11; i++) {
      if (isnan(cols[i]))
        f.print(",");
      else
        f.printf(fmt[i], cols[i]);
    }
    if (bus_heave.n > 0)
      f.printf(",%.3f,%.3f,%lu", bus_heave.rms, bus_heave.mean, static_cast<unsigned long>(bus_heave.n));
    else
      f.print(",,,0");
    f.print("\n");
    f.close();
  }

  String status() const {
    if (!ok_) return "not found (SD NAND on D8/D9/D10, CS D3 via JP7)";
    char buf[96];
    snprintf(buf, sizeof(buf), "%llu MB, %llu MB used, %s",
             SD.totalBytes() / (1024ULL * 1024ULL), SD.usedBytes() / (1024ULL * 1024ULL), kPath);
    return String(buf);
  }

 private:
  bool ok_ = false;
};
