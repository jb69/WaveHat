// WaveHat firmware: sea state from an LSM6DSO, sent to Signal K with SensESP.
//
//   environment.heave                    m   standard Signal K path, ~4 Hz
//   environment.waves.significantHeight  m   proposed path, every ~79 s
//   environment.waves.period             s   proposed (peak period Tp)
//   environment.waves.meanPeriod         s   proposed (zero-crossing Tz)
//   environment.waves.underway           bool proposed: the boat moved (mean SOG
//                                             above 1.5 kn, or above it for a quarter
//                                             of the window); lib/underway
//
// Tp and Tz are sent as null when they mean nothing: flat calm, or the spectrum's
// peak outside the band (wavemath Stats::periods_valid). The IMU's acceleration is
// moved to the hull's roll/pitch centre with the mounting position (mounting.h).
//
// SOG comes from the boat's NMEA 2000 bus when the WaveHat is on one (listen-only,
// n2k_bus.h), else from a GNSS module on the rev B GNSS port (gnss.h), else from Signal K.
// Each result is also appended to /waves.csv on the board's SD NAND (wave_log.h), with the
// position, heading, depth and wind the bus or the module gave.
//
// Rev B (hardware/DESIGN.md section 11) adds the GNSS port J5 on D6/D7, the IO header J6, the
// jumpers JP8-JP10 that cut the CAN transceiver, and a battery option. In this firmware those
// are: board.h (the pin table), orientation.h (how the board is mounted), gnss.h, and
// power_mode.h (battery mode: no CAN, deep sleep when still, woken by the IMU on D2 via JP4).
//
// The wave maths (lib/wavemath) is the same code the desktop tests run; see README.md.
// Run on rev A boards (bench, Oct 2026); the rev B additions have not been run on a board.

#include <Arduino.h>
#include <Wire.h>

#include <memory>

#include "accel_calibration.h"
#include "board.h"
#include "esp_sleep.h"
#include "gnss.h"
#include "lsm6dso.h"
#include "mounting.h"
#include "n2k_bus.h"
#include "orientation.h"
#include "power_mode.h"
#include "soc/soc_caps.h"
#include "sensesp/signalk/signalk_output.h"
#include "sensesp/signalk/signalk_value_listener.h"
#include "sensesp/system/lambda_consumer.h"
#include "sensesp/ui/config_item.h"
#include "sensesp/ui/status_page_item.h"
#include "sensesp_app_builder.h"
#include "underway.h"
#include "wave_log.h"
#include "wavemath.h"

using namespace sensesp;

#ifndef WAVEHAT_BOOT_BUTTON
#error "Set WAVEHAT_BOOT_BUTTON for the board (platformio.ini)"
#endif

namespace {

constexpr const char* kTag = "wavehat";
constexpr uint32_t kPollMs = 250;            // FIFO holds several seconds
constexpr uint32_t kSogStaleMs = 30000;      // SOG older than this is ignored
constexpr uint32_t kRateCheckMs = 120000;    // measure the IMU's real ODR

Lsm6dso imu;
bool imu_ok = false;
wavemath::Config wave_cfg;
std::unique_ptr<wavemath::WaveProcessor> waves;

// Sample-rate measurement: the LSM6DSO's internal oscillator is only good to
// a few percent; the ESP32's crystal is far better, so count samples.
uint32_t rate_t0 = 0;
uint32_t rate_n = 0;

// Underway: SOG sampled at every poll, per hop, over the hops the spectrum spans. SOG from
// the NMEA 2000 bus is preferred; Signal K's is the fallback (a WaveHat on Wi-Fi only).
N2kBus n2k_bus;
n2k::HeaveStats bus_heave;  // the bus's own heave (PGN 127252) over the last hop
float sk_sog = NAN;
uint32_t sk_sog_ms = 0;
UnderwayTracker underway;

std::shared_ptr<SKOutputFloat> heave_out, hs_out, tp_out, tz_out;
std::shared_ptr<SKOutputBool> underway_out;

std::shared_ptr<StatusPageItem<String>> ui_waves, ui_imu, ui_fft, ui_raw;
std::shared_ptr<AccelCalibration> accel_cal;
std::shared_ptr<MountingPosition> mounting;
std::shared_ptr<StatusPageItem<String>> ui_log, ui_n2k, ui_gnss, ui_power;
WaveLog wave_log;

// Rev B: mounting orientation, the GNSS port, battery mode.
std::shared_ptr<Orientation> orientation;
std::shared_ptr<GnssConfig> gnss_cfg;
Gnss gnss;
std::shared_ptr<PowerMode> power;

// Stillness, for battery mode's sleep: the spread of |a| and the largest |gyro| seen in each
// poll. A boat afloat never gets this still; a board on a shelf or a boat on the hard does.
constexpr float kStillAccelSpread = 0.3f;    // m/s^2, about 30 mg
constexpr float kStillGyro = 0.0175f;        // rad/s, 1 deg/s
uint32_t still_since_ms = 0;                 // 0: moving
bool sleeping = false;

// Raw (uncalibrated) accelerometer mean over 10 s, for the six-face
// calibration: shown on the status page in g.
constexpr uint32_t kRawMeanMs = 10000;
double raw_sum[3] = {0, 0, 0};
uint32_t raw_n = 0;
uint32_t raw_t0 = 0;

// Measures the real compute cost on this chip (logged and shown on the
// status page): the per-sample work, one complete Welch segment, and the
// FFT alone at 512 points (what the firmware runs) and 4096 points (what it
// would need at the full 26 Hz).
String benchmark_text;

void benchmark() {
  uint32_t fft_us[2];
  int sizes[2] = {512, 4096};
  for (int k = 0; k < 2; k++) {
    int n = sizes[k];
    wavemath::Fft fft(n);
    std::vector<float> re(n), im(n, 0.0f);
    for (int i = 0; i < n; i++) re[i] = sinf(0.37f * i);
    uint32_t t0 = micros();
    fft.forward(re.data(), im.data());
    fft_us[k] = micros() - t0;
  }
  wavemath::WaveProcessor wp(wave_cfg);
  float g[3] = {0.01f, -0.02f, 0.005f};
  float a[3] = {0.3f, -0.2f, wavemath::kG};
  uint32_t total = 0, n = 0, seg_us = 0;
  while (wp.segments_computed() == 0) {
    a[2] = wavemath::kG + 0.5f * sinf(2.0f * 3.14159265f * 0.1f * n / 26.0f);
    uint32_t t0 = micros();
    wp.push(g, a);
    uint32_t dt = micros() - t0;
    if (wp.segments_computed() > 0) {
      seg_us = dt;
    } else {
      total += dt;
      n++;
    }
  }
  char buf[160];
  snprintf(buf, sizeof(buf),
           "per sample %.1f us, Welch segment %u us, FFT 512 %u us, "
           "FFT 4096 %u us",
           static_cast<float>(total) / n, static_cast<unsigned>(seg_us),
           static_cast<unsigned>(fft_us[0]), static_cast<unsigned>(fft_us[1]));
  benchmark_text = buf;
  ESP_LOGI(kTag, "benchmark: %s", buf);
  ui_fft->set(benchmark_text);
}

void new_processor(float fs) {
  wave_cfg.fs = fs;
  for (int i = 0; i < 3; i++) wave_cfg.r_imu[i] = mounting->r()[i];
  waves.reset(new wavemath::WaveProcessor(wave_cfg));
  underway = UnderwayTracker(wave_cfg.window_segments + 1);  // 14 segments span 15 hops
  ESP_LOGI(kTag, "wave processor at %.3f Hz, IMU at x %.2f y %.2f z %.2f m from the roll/pitch centre",
           fs, wave_cfg.r_imu[0], wave_cfg.r_imu[1], wave_cfg.r_imu[2]);
}

#ifdef WAVEHAT_SIM_IMU
// Simulated sea for the end-to-end test (README.md, Simulated IMU): 0.50 m amplitude heave at
// 8.0 s on a level board, so Hs = 4 x 0.5 / sqrt(2) = 1.414 m and Tp = Tz = 8.0 s, run
// WAVEHAT_SIM_IMU times faster than real time. SOG follows a fixed script in sea time:
// anchored (0.2 kn) to 25 min, motoring at 5 kn from 25 to 45 min, anchored again after.
constexpr float kSimAmp = 0.5f, kSimPeriod = 8.0f;
uint32_t sim_n = 0;  // samples generated

float sim_sog() {
  float t_min = sim_n / wave_cfg.fs / 60.0f;
  return (t_min >= 25.0f && t_min < 45.0f ? 5.0f : 0.2f) * 0.514444f;
}
#endif

// The boat's values now: the bus's, then the GNSS module's where the bus has none, then SOG from
// Signal K if neither has it.
n2k::Nav current_nav() {
  uint32_t now = millis();
  n2k::Nav nav = n2k_bus.snapshot().nav(now, kSogStaleMs);
  n2k::Nav g = gnss.nav(now, kSogStaleMs);
  if (isnan(nav.sog)) nav.sog = g.sog;
  if (isnan(nav.cog)) nav.cog = g.cog;
  if (isnan(nav.lat) || isnan(nav.lon)) {
    nav.lat = g.lat;
    nav.lon = g.lon;
  }
  if (isnan(nav.sog) && !isnan(sk_sog) && now - sk_sog_ms < kSogStaleMs) nav.sog = sk_sog;
#ifdef WAVEHAT_SIM_IMU
  nav.sog = sim_sog();
#endif
  return nav;
}

void publish(const wavemath::Stats& s, uint32_t seg_us) {
  hs_out->set(s.hs);
  // null in flat calm or with the peak outside the band: no "0.0 m at 22 s"
  tp_out->set(s.periods_valid ? s.tp : NAN);
  tz_out->set(s.periods_valid ? s.tz : NAN);
  int uw = underway.state();
  if (uw >= 0) underway_out->set(uw == 1);
  wave_log.append(s, uw, underway.mean_sog(), current_nav(), bus_heave);
  ui_log->set(wave_log.status());
  ESP_LOGI(kTag,
           "Hs %.2f m  Tp %.1f s  Tz %.1f s%s  heave RMS %.2f m (td %.2f)  %d segments  "
           "underway %s (mean SOG %.2f kn, %.0f %% above 1.5 kn)  segment %u us",
           s.hs, s.tp, s.tz, s.periods_valid ? "" : " (not sent: no clear peak)", s.heave_rms,
           s.heave_rms_td, s.segments, uw < 0 ? "unknown" : (uw ? "yes" : "no"),
           underway.mean_sog() * 1.943844f, underway.fraction_above() * 100.0f,
           static_cast<unsigned>(seg_us));
  char buf[96];
  if (s.periods_valid)
    snprintf(buf, sizeof(buf), "Hs %.2f m, Tp %.1f s, Tz %.1f s (%d segments)", s.hs, s.tp, s.tz,
             s.segments);
  else
    snprintf(buf, sizeof(buf), "Hs %.2f m, no clear wave period (%d segments)", s.hs, s.segments);
  ui_waves->set(String(buf));
}

// Battery mode: the board has been still long enough. Arm the IMU's wake-on-motion, then deep
// sleep until INT1 (JP4 -> D2) rises or the fallback timer runs out. Either is a reboot.
void go_to_sleep() {
  sleeping = true;
  bool wom = imu_ok && imu.enable_wake_on_motion();
  ESP_LOGI(kTag, "battery mode: still for %d min; sleeping (wake on motion %s, timer %d min)",
           power->sleep_after_min, wom ? "armed on D2" : "NOT armed", power->wake_timer_min);
  ui_power->set("sleeping");
  delay(200);  // let the log line out
  pinMode(board::kImuInt1Pin, INPUT);
  esp_sleep_enable_timer_wakeup(static_cast<uint64_t>(power->wake_timer_min) * 60ULL * 1000000ULL);
#if SOC_PM_SUPPORT_EXT0_WAKEUP
  // ESP32-S3: D2 = GPIO3 is an RTC pin
  if (wom) esp_sleep_enable_ext0_wakeup(static_cast<gpio_num_t>(board::kImuInt1Pin), 1);
#elif SOC_GPIO_SUPPORT_DEEPSLEEP_WAKEUP
  // ESP32-C3 (D2 = GPIO4, wake pins 0-5) and C6 (D2 = GPIO2, wake pins 0-7)
  if (wom) esp_deep_sleep_enable_gpio_wakeup(1ULL << board::kImuInt1Pin, ESP_GPIO_WAKEUP_GPIO_HIGH);
#endif
  esp_deep_sleep_start();
}

const char* wake_reason() {
  switch (esp_sleep_get_wakeup_cause()) {
    case ESP_SLEEP_WAKEUP_EXT0:
    case ESP_SLEEP_WAKEUP_GPIO:
      return "woken by motion (IMU INT1 on D2)";
    case ESP_SLEEP_WAKEUP_TIMER:
      return "woken by the timer";
    default:
      return "power-on or reset";
  }
}

// Per poll: is the board still, and for how long. Sleep when battery mode says so.
void track_stillness(float accel_spread, float gyro_max) {
  uint32_t now = millis();
  bool still = accel_spread < kStillAccelSpread && gyro_max < kStillGyro;
  if (!still) {
    still_since_ms = 0;
    return;
  }
  if (still_since_ms == 0) still_since_ms = now;
  if (power->battery && power->sleep_after_min > 0 && !sleeping &&
      now - still_since_ms >= static_cast<uint32_t>(power->sleep_after_min) * 60000UL)
    go_to_sleep();
}

String power_status() {
  if (!power->battery) return String("mains/bus power; ") + wake_reason();
  String s = String("battery mode, CAN off; ") + wake_reason();
  if (power->sleep_after_min == 0) {
    s += "; never sleeps";
  } else if (still_since_ms) {
    s += "; still for " + String((millis() - still_since_ms) / 60000UL) + " of " +
         String(power->sleep_after_min) + " min";
  } else {
    s += "; moving (sleeps after " + String(power->sleep_after_min) + " still min)";
  }
  return s;
}

void poll_imu() {
  if (mounting->take_changed() || orientation->take_changed()) new_processor(wave_cfg.fs);  // the window restarts
  gnss.poll();
#ifndef WAVEHAT_SIM_IMU
  if (!imu_ok) {
    // Probe every 5 s rather than every poll: a missing IMU should not flood
    // the log with I2C errors.
    static uint32_t last_probe = 0;
    if (millis() - last_probe < 5000) return;
    last_probe = millis();
    imu_ok = imu.begin(Wire);
    ui_imu->set(imu_ok ? "LSM6DSO running" : "LSM6DSO not found at 0x6B");
    return;
  }
#endif
  uint32_t seg_before = waves->segments_computed();
  uint32_t busy_us = 0;
  bool ready = false;
  float a_min = 1e9f, a_max = -1e9f, g_max = 0;
  auto sample = [&](const float g_raw[3], const float a_raw[3]) {
    for (int i = 0; i < 3; i++) raw_sum[i] += a_raw[i];
    raw_n++;
    float a[3] = {a_raw[0], a_raw[1], a_raw[2]};
    float g[3] = {g_raw[0], g_raw[1], g_raw[2]};
    accel_cal->apply(a);        // per chip axis
    orientation->apply(a);      // chip frame -> body frame (X starboard, Y bow, Z up)
    orientation->apply(g);
    float a_abs = sqrtf(a[0] * a[0] + a[1] * a[1] + a[2] * a[2]);
    a_min = std::min(a_min, a_abs);
    a_max = std::max(a_max, a_abs);
    g_max = std::max(g_max, fabsf(g[0]) + fabsf(g[1]) + fabsf(g[2]));
    uint32_t t0 = micros();
    ready |= waves->push(g, a);
    busy_us = std::max(busy_us, micros() - t0);
    if (waves->segments_computed() != seg_before) {
      seg_before = waves->segments_computed();
      underway.end_hop();
      bus_heave = n2k_bus.take_heave();
    }
  };
#ifdef WAVEHAT_SIM_IMU
  // Real time is 26 Hz x 0.25 s = 6.5 samples a poll; run WAVEHAT_SIM_IMU times that, with one
  // SOG sample per real-time poll's worth of samples.
  const int per_poll = static_cast<int>(wave_cfg.fs * kPollMs / 1000.0f);
  int n = static_cast<int>(wave_cfg.fs * kPollMs / 1000.0f * WAVEHAT_SIM_IMU + 0.5f);
  for (int i = 0; i < n; i++) {
    float w = 2.0f * 3.14159265f / kSimPeriod, t = sim_n / wave_cfg.fs;
    float g[3] = {0, 0, 0};
    float a[3] = {0, 0, wavemath::kG - kSimAmp * w * w * cosf(w * t)};
    if (i % per_poll == 0) underway.sample(current_nav().sog);
    sample(g, a);
    sim_n++;
  }
#else
  int n = imu.read_fifo(sample);
  if (n < 0) {
    ESP_LOGW(kTag, "I2C error reading the FIFO; re-initialising");
    imu_ok = false;
    return;
  }
  if (imu.overrun()) ESP_LOGW(kTag, "FIFO overrun: samples lost");
  if (n > 0) track_stillness(a_max - a_min, g_max);
#endif

  uint32_t now = millis();
  if (now - raw_t0 >= kRawMeanMs && raw_n > 0) {
    char buf[80];
    snprintf(buf, sizeof(buf), "x %+.4f  y %+.4f  z %+.4f g (10 s mean)",
             raw_sum[0] / raw_n / 9.80665, raw_sum[1] / raw_n / 9.80665,
             raw_sum[2] / raw_n / 9.80665);
    ui_raw->set(String(buf));
    raw_sum[0] = raw_sum[1] = raw_sum[2] = 0;
    raw_n = 0;
    raw_t0 = now;
  }
#ifndef WAVEHAT_SIM_IMU
  underway.sample(current_nav().sog);
#endif
  heave_out->set(waves->heave());

  if (ready) publish(waves->stats(), busy_us);
#ifdef WAVEHAT_SIM_IMU
  return;  // no ODR to measure
#endif

  // Measure the real output data rate and restart the analysis if the
  // nominal 26 Hz is off by more than 0.5 %.
  if (rate_n == 0) rate_t0 = now;
  rate_n += n;
  if (now - rate_t0 >= kRateCheckMs) {
    float fs = 1000.0f * rate_n / (now - rate_t0);
    if (fabsf(fs / wave_cfg.fs - 1.0f) > 0.005f) {
      ESP_LOGI(kTag, "measured ODR %.3f Hz (was %.3f)", fs, wave_cfg.fs);
      new_processor(fs);
    }
    char buf[64];
    snprintf(buf, sizeof(buf), "LSM6DSO running, %.2f Hz, %u overruns", fs,
             static_cast<unsigned>(imu.overruns()));
    ui_imu->set(String(buf));
    rate_n = 0;
  }
}

std::shared_ptr<SKOutputFloat> float_output(const char* path, const char* units,
                                            const char* name, const char* desc) {
  // SKOutputNumeric takes a raw pointer and owns it (wraps it in a shared_ptr).
  return std::make_shared<SKOutputFloat>(path, "",
                                         new SKMetadata(units, name, desc));
}

}  // namespace

void setup() {
  SetupLogging(ESP_LOG_INFO);

  SensESPAppBuilder builder;
  sensesp_app = (&builder)
                    ->set_hostname("wavehat")
                    // SensESP's default button is GPIO0, which on the C6 is
                    // D0 = CAN RX: use each XIAO's BOOT button instead.
                    ->set_button_pin(WAVEHAT_BOOT_BUTTON)
                    ->get_app();

  Wire.begin(D4, D5, 400000);  // WaveHat I2C: D4 = SDA, D5 = SCL
  wave_log.begin();            // SD NAND on D8/D9/D10, CS D3
  configTime(0, 0, "pool.ntp.org");  // UTC in the log when the boat has internet

  heave_out = float_output("environment.heave", "m", "Heave",
                           "Vertical movement of the vessel due to waves "
                           "(up positive, high-passed at 0.02 Hz)");
  hs_out = float_output("environment.waves.significantHeight", "m",
                        "Significant wave height",
                        "Hs = 4 sqrt(m0) of the boat's vertical motion, "
                        "0.04-0.5 Hz, last ~20 min");
  tp_out = float_output("environment.waves.period", "s", "Wave peak period",
                        "Tp of the boat's vertical motion, last ~20 min");
  tz_out = float_output("environment.waves.meanPeriod", "s",
                        "Wave mean period",
                        "Tz = sqrt(m0/m2), zero-crossing period, last ~20 min");
  underway_out = std::make_shared<SKOutputBool>(
      "environment.waves.underway", "",
      std::make_shared<SKMetadata>("", "Waves measured underway",
                                   "True if SOG exceeded 1.5 kn during the "
                                   "window: periods are then distorted"));

  ui_waves = std::make_shared<StatusPageItem<String>>("Sea state", "waiting for ~10 min of data", "WaveHat", 100);
  ui_imu = std::make_shared<StatusPageItem<String>>("IMU", "starting", "WaveHat", 110);
  ui_fft = std::make_shared<StatusPageItem<String>>("Compute", "", "WaveHat", 120);
  ui_raw = std::make_shared<StatusPageItem<String>>("Raw accel", "", "WaveHat", 130);
  ui_log = std::make_shared<StatusPageItem<String>>("Log storage", wave_log.status(), "WaveHat", 140);

  power = std::make_shared<PowerMode>("/wavehat/power");
  ConfigItem(power)
      ->set_title("Power")
      ->set_description(
          "Battery mode is for a WaveHat on a cell (rev B J7) with no NMEA 2000 bus: the CAN "
          "controller stays off (cut JP8-JP10 too), and after the board has been still for the "
          "given minutes it deep-sleeps until the IMU feels motion (JP4 must be bridged so INT1 "
          "reaches D2) or the fallback timer runs out. 0 still minutes = never sleep.")
      ->set_sort_order(80);
  ESP_LOGI(kTag, "%s", wake_reason());

  if (power->battery) {
    ESP_LOGI(kTag, "battery mode: CAN controller left off");
  } else {
    n2k_bus.begin();           // NMEA 2000, listen-only, on D0/D1
  }
  ui_n2k = std::make_shared<StatusPageItem<String>>(
      "NMEA 2000", power->battery ? String("off (battery mode)") : n2k_bus.status(), "WaveHat", 150);

  gnss_cfg = std::make_shared<GnssConfig>("/wavehat/gnss");
  ConfigItem(gnss_cfg)
      ->set_title("GNSS port")
      ->set_description(
          "A GNSS module on J5 (rev B) or on J6 pins 6/7 talking NMEA 0183: RX on D7, TX on D6. "
          "Gives SOG, position and the time when there is no NMEA 2000 bus and no internet. "
          "Changing this takes effect at the next restart.")
      ->set_sort_order(85);
  if (gnss_cfg->enabled) gnss.begin(gnss_cfg->baud);
  ui_gnss = std::make_shared<StatusPageItem<String>>("GNSS", gnss.status(millis()), "WaveHat", 155);
  ui_power = std::make_shared<StatusPageItem<String>>("Power", "", "WaveHat", 160);

  orientation = std::make_shared<Orientation>("/wavehat/orientation");
  ConfigItem(orientation)
      ->set_title("Mounting orientation")
      ->set_description(
          "Which way the silkscreen 'Y bow' arrow points and whether the parts face up or down. "
          "The yacht enclosure holds the board bow arrow forward, component side up: leave the "
          "defaults for it.")
      ->set_sort_order(88);

  accel_cal = std::make_shared<AccelCalibration>("/wavehat/accel_calibration");
  ConfigItem(accel_cal)
      ->set_title("Accelerometer calibration")
      ->set_description(
          "Six-face calibration (see the firmware README). Rest the box on "
          "each face and read 'Raw accel' on the status page; per axis, "
          "offset = (up + down) / 2 and scale = 2 / (up - down).")
      ->set_sort_order(100);

  mounting = std::make_shared<MountingPosition>("/wavehat/mounting");
  ConfigItem(mounting)
      ->set_title("Mounting position")
      ->set_description(
          "Where the box sits, in metres from the hull's roll/pitch centre (see the firmware "
          "README, Mounting). Rolling and pitching move a box away from the centre up and "
          "down, which reads as heave; with this entered it is taken out. 0, 0, 0 if unknown.")
      ->set_sort_order(90);

  auto sog_listener =
      std::make_shared<FloatSKListener>("navigation.speedOverGround", 1000);
  sog_listener->connect_to(std::make_shared<LambdaConsumer<float>>([](float v) {
    sk_sog = v;
    sk_sog_ms = millis();
  }));

  new_processor(26.0f);
#ifdef WAVEHAT_SIM_IMU
  imu_ok = true;
  ui_imu->set("SIMULATED: 0.50 m heave at 8.0 s, " + String(WAVEHAT_SIM_IMU) + "x real time");
  ESP_LOGW(kTag, "simulated IMU build: not for a boat");
#else
  imu_ok = imu.begin(Wire);
  if (!imu_ok) ESP_LOGE(kTag, "LSM6DSO not found at 0x6B; retrying");
  ui_imu->set(imu_ok ? "LSM6DSO running" : "LSM6DSO not found at 0x6B");
  gnss.probe_compass(Wire);  // a Pixhawk-style module's magnetometer, reported only
#endif
  ESP_LOGI(kTag, "mounting: %s", orientation->describe().c_str());
  event_loop()->onRepeat(kPollMs, poll_imu);
  // After USB has re-enumerated, so the log reaches the host.
  event_loop()->onDelay(5000, benchmark);
  event_loop()->onRepeat(2000, []() {
    if (!power->battery) ui_n2k->set(n2k_bus.status());
    ui_gnss->set(gnss.status(millis()));
    ui_power->set(power_status());
  });
  event_loop()->onRepeat(60000, []() {
    ESP_LOGI(kTag, "benchmark: %s; IMU %s; free heap %u; NMEA 2000: %s; GNSS: %s; %s",
             benchmark_text.c_str(), imu_ok ? "running" : "not found",
             static_cast<unsigned>(ESP.getFreeHeap()),
             power->battery ? "off" : n2k_bus.status().c_str(), gnss.status(millis()).c_str(),
             power_status().c_str());
  });
}

void loop() { event_loop()->tick(); }
