// NMEA 2000 in, listen-only, on the WaveHat's CAN transceiver (D0 = RX, D1 = TX).
//
// The ESP32's TWAI controller runs in listen-only mode: it never transmits, not even an
// acknowledge or an error frame, so the WaveHat cannot disturb the boat's bus. D1 is still
// assigned so the controller holds the transceiver's D input recessive. 250 kbit/s, every frame
// accepted, decoded by lib/n2k in a task of its own so a slow Welch segment can't drop frames.
//
// Build with -D WAVEHAT_N2K_SELFTEST for a bench check without a bus: the controller then
// runs in no-ack mode with TX and RX on the same pin (looped back inside the chip) and sends
// itself made-up frames: SOG ramping 0-6 m/s, a position, a true heading, depth and a 0.50 m
// heave at 8 s.

#pragma once

#include <Arduino.h>
#include <driver/twai.h>

#include "n2k.h"

class N2kBus {
 public:
  bool begin() {
#ifdef WAVEHAT_N2K_SELFTEST
    twai_general_config_t g =
        TWAI_GENERAL_CONFIG_DEFAULT(static_cast<gpio_num_t>(D1), static_cast<gpio_num_t>(D1), TWAI_MODE_NO_ACK);
#else
    twai_general_config_t g =
        TWAI_GENERAL_CONFIG_DEFAULT(static_cast<gpio_num_t>(D1), static_cast<gpio_num_t>(D0), TWAI_MODE_LISTEN_ONLY);
#endif
    g.rx_queue_len = 64;
    twai_timing_config_t t = TWAI_TIMING_CONFIG_250KBITS();
    twai_filter_config_t f = TWAI_FILTER_CONFIG_ACCEPT_ALL();
    esp_err_t err = twai_driver_install(&g, &t, &f);
    if (err == ESP_OK) err = twai_start();
    if (err != ESP_OK) {
      error_ = esp_err_to_name(err);
      return false;
    }
    ok_ = true;
    xTaskCreate(rx_task, "n2k_rx", 3072, this, 5, nullptr);
#ifdef WAVEHAT_N2K_SELFTEST
    xTaskCreate(selftest_task, "n2k_selftest", 2048, this, 4, nullptr);
#endif
    return true;
  }

  // A copy of the decoder's state, taken under the lock.
  n2k::Decoder snapshot() {
    portENTER_CRITICAL(&lock_);
    n2k::Decoder d = decoder_;
    portEXIT_CRITICAL(&lock_);
    return d;
  }

  // The bus heave's statistics (PGN 127252) since the last call; n = 0 if none arrived.
  n2k::HeaveStats take_heave() {
    portENTER_CRITICAL(&lock_);
    n2k::HeaveStats s = decoder_.take_heave();
    portEXIT_CRITICAL(&lock_);
    return s;
  }

  String status() {
    if (!ok_) return String("CAN not started: ") + error_;
    n2k::Decoder d = snapshot();
    uint32_t now = millis();
    twai_status_info_t s = {};
    twai_get_status_info(&s);
    char buf[240];
    int n = snprintf(buf, sizeof(buf), "%u frames, %u used, %u missed",
                     static_cast<unsigned>(d.frames), static_cast<unsigned>(d.decoded),
                     static_cast<unsigned>(s.rx_missed_count + s.rx_overrun_count));
    if (d.sog.fresh(now, 5000))
      n += snprintf(buf + n, sizeof(buf) - n, "; SOG %.2f kn from %u", d.sog.v * 1.943844,
                    static_cast<unsigned>(d.sog.src));
    if (d.lat.fresh(now, 5000) && n < static_cast<int>(sizeof(buf)))
      n += snprintf(buf + n, sizeof(buf) - n, "; %.5f, %.5f", d.lat.v, d.lon.v);
    if (d.heading.fresh(now, 5000) && n < static_cast<int>(sizeof(buf)))
      n += snprintf(buf + n, sizeof(buf) - n, "; heading %.0f T", d.heading.v * 57.29578);
    if (d.heave.fresh(now, 5000) && n < static_cast<int>(sizeof(buf)))
      snprintf(buf + n, sizeof(buf) - n, "; heave %+.2f m from %u", d.heave.v,
               static_cast<unsigned>(d.heave.src));
    return String(buf);
  }

 private:
  static void rx_task(void* arg) {
    auto* self = static_cast<N2kBus*>(arg);
    twai_message_t m;
    for (;;) {
      if (twai_receive(&m, portMAX_DELAY) != ESP_OK) continue;
      if (!m.extd || m.rtr) continue;  // NMEA 2000 is 29-bit data frames only
      portENTER_CRITICAL(&self->lock_);
      self->decoder_.handle(m.identifier, m.data, m.data_length_code, millis());
      portEXIT_CRITICAL(&self->lock_);
    }
  }

#ifdef WAVEHAT_N2K_SELFTEST
  static void send(uint32_t pgn, const uint8_t* data) {
    twai_message_t m = {};
    m.extd = 1;
    m.self = 1;  // receive our own frame
    m.identifier = 2u << 26 | pgn << 8 | 0x42;
    m.data_length_code = 8;
    memcpy(m.data, data, 8);
    twai_transmit(&m, pdMS_TO_TICKS(50));
  }

  static void selftest_task(void*) {
    for (uint32_t i = 0;; i++) {
      uint16_t sog = (i * 7) % 600;  // 0-6 m/s in 0.01 m/s, not in step with the 60 s log
      uint8_t cogsog[8] = {0, 0xFC, 0x10, 0x27, static_cast<uint8_t>(sog), static_cast<uint8_t>(sog >> 8),
                           0xFF, 0xFF};
      send(129026, cogsog);
      int32_t lat = -338568000, lon = 1512153000;
      uint8_t pos[8];
      for (int k = 0; k < 4; k++) {
        pos[k] = static_cast<uint32_t>(lat) >> (8 * k);
        pos[4 + k] = static_cast<uint32_t>(lon) >> (8 * k);
      }
      send(129025, pos);
      uint8_t hdg[8] = {0, 0x10, 0x27, 0xFF, 0x7F, 0xFF, 0x7F, 0xFC};  // 1.0 rad true
      send(127250, hdg);
      uint8_t dep[8] = {0, 0xD2, 0x04, 0, 0, 0, 0, 0xFF};  // 12.34 m
      send(128267, dep);
      int16_t hv = static_cast<int16_t>(50.0f * sinf(i * 0.25f * 6.2831853f / 8.0f));  // 0.50 m at 8 s
      uint8_t heave[8] = {0, static_cast<uint8_t>(hv), static_cast<uint8_t>(hv >> 8), 0, 0, 0xF0, 0xFF, 0xFF};
      send(127252, heave);
      vTaskDelay(pdMS_TO_TICKS(250));
    }
  }
#endif

  bool ok_ = false;
  const char* error_ = "";
  n2k::Decoder decoder_;
  portMUX_TYPE lock_ = portMUX_INITIALIZER_UNLOCKED;
};
