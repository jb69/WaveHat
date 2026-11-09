// Minimal LSM6DSO driver for WaveHat: accel + gyro at 26 Hz batched in the
// FIFO, read over I2C. Register addresses and bit fields checked against ST's
// lsm6dso-pid driver (lsm6dso_reg.h) and datasheet DS12140.
//
// Not yet run on hardware: the WaveHat boards have not been built.

#pragma once

#include <Arduino.h>
#include <Wire.h>

#include <functional>

class Lsm6dso {
 public:
  static constexpr uint8_t kDefaultAddress = 0x6B;  // SA0 high (WaveHat JP3)

  // One paired sample: gyro in rad/s, accel in m/s^2, chip frame.
  using SampleFn = std::function<void(const float gyro[3], const float accel[3])>;

  // Resets the chip and starts accel + gyro at 26 Hz, +-4 g / +-500 dps,
  // high-performance mode, both batched into the FIFO in continuous mode.
  bool begin(TwoWire& wire, uint8_t address = kDefaultAddress);

  // Drains the FIFO, calling fn for every accel/gyro pair. Returns the
  // number of samples delivered, or -1 on an I2C error.
  int read_fifo(const SampleFn& fn);

  // Battery mode's sleep: stops the gyro and the FIFO, puts the accelerometer in its 12.5 Hz
  // low-power mode (about 10 uA) and routes the wake-up interrupt to INT1, active high, for
  // motion above threshold_lsb x 31.25 mg (at +-2 g; 2 = about 62 mg) on any axis after the
  // slope filter. The caller then deep-sleeps with INT1 (WaveHat JP4 -> D2) as the wake pin.
  // begin() undoes all of it on the next boot. Register values from DS12140 and ST's
  // lsm6dso_wake_up.c example; not yet tried on a board (7 Nov 2026).
  bool enable_wake_on_motion(uint8_t threshold_lsb = 2);

  uint8_t who_am_i();
  // True if the FIFO overran since the last read (samples were lost).
  bool overrun() const { return overrun_; }
  uint32_t overruns() const { return overrun_count_; }

 private:
  bool write_reg(uint8_t reg, uint8_t value);
  bool read_regs(uint8_t reg, uint8_t* buf, size_t len);

  TwoWire* wire_ = nullptr;
  uint8_t addr_ = kDefaultAddress;
  float gyro_[3] = {0, 0, 0};
  float accel_[3] = {0, 0, 0};
  bool have_gyro_ = false;
  bool have_accel_ = false;
  bool overrun_ = false;
  uint32_t overrun_count_ = 0;
};
