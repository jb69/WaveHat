#include "lsm6dso.h"

namespace {

// Registers (lsm6dso_reg.h)
constexpr uint8_t kFifoCtrl3 = 0x09;   // BDR_GY[7:4] BDR_XL[3:0]
constexpr uint8_t kFifoCtrl4 = 0x0A;   // ODR_TS_BATCH ODR_T_BATCH FIFO_MODE[2:0]
constexpr uint8_t kWhoAmI = 0x0F;      // reads 0x6C
constexpr uint8_t kCtrl1Xl = 0x10;     // ODR_XL[7:4] FS_XL[3:2] LPF2_XL_EN
constexpr uint8_t kCtrl2G = 0x11;      // ODR_G[7:4] FS_G[3:2] FS_125
constexpr uint8_t kCtrl3C = 0x12;      // BOOT BDU H_LACTIVE PP_OD SIM IF_INC 0 SW_RESET
constexpr uint8_t kCtrl6C = 0x15;      // TRIG_EN LVL1_EN LVL2_EN XL_HM_MODE USR_OFF_W FTYPE[2:0]
constexpr uint8_t kTapCfg2 = 0x58;     // INTERRUPTS_ENABLE INACT_EN[1:0] TAP_THS_Y[4:0]
constexpr uint8_t kWakeUpThs = 0x5B;   // SINGLE_DOUBLE_TAP USR_OFF_ON_WU WK_THS[5:0]
constexpr uint8_t kWakeUpDur = 0x5C;   // FF_DUR5 WAKE_DUR[1:0] WAKE_THS_W SLEEP_DUR[3:0]
constexpr uint8_t kMd1Cfg = 0x5E;      // INT1_SLEEP_CHANGE INT1_SINGLE_TAP INT1_WU INT1_FF ...
constexpr uint8_t kFifoStatus1 = 0x3A; // DIFF_FIFO[7:0]
constexpr uint8_t kFifoDataOutTag = 0x78;
constexpr uint8_t kFifoDataOutXL = 0x79;

constexpr uint8_t kId = 0x6C;
constexpr uint8_t kOdr26Hz = 0x2;
constexpr uint8_t kFsXl4g = 0x2;       // FS_XL = 10b: +-4 g
constexpr uint8_t kFsG500dps = 0x1;    // FS_G = 01b: +-500 dps
constexpr uint8_t kFifoContinuous = 0x6;
constexpr uint8_t kTagGyro = 0x01;     // gyroscope, not compressed
constexpr uint8_t kTagAccel = 0x02;    // accelerometer, not compressed

constexpr float kG = 9.80665f;
constexpr float kAccelScale = 0.122e-3f * kG;                    // m/s^2 per LSB
constexpr float kGyroScale = 17.50e-3f * 3.14159265f / 180.0f;   // rad/s per LSB

int16_t le16(const uint8_t* p) {
  return static_cast<int16_t>(p[0] | (p[1] << 8));
}

}  // namespace

bool Lsm6dso::write_reg(uint8_t reg, uint8_t value) {
  wire_->beginTransmission(addr_);
  wire_->write(reg);
  wire_->write(value);
  return wire_->endTransmission() == 0;
}

bool Lsm6dso::read_regs(uint8_t reg, uint8_t* buf, size_t len) {
  wire_->beginTransmission(addr_);
  wire_->write(reg);
  if (wire_->endTransmission(false) != 0) return false;
  if (wire_->requestFrom(addr_, static_cast<uint8_t>(len)) != len) return false;
  for (size_t i = 0; i < len; i++) buf[i] = wire_->read();
  return true;
}

uint8_t Lsm6dso::who_am_i() {
  uint8_t id = 0;
  read_regs(kWhoAmI, &id, 1);
  return id;
}

bool Lsm6dso::begin(TwoWire& wire, uint8_t address) {
  wire_ = &wire;
  addr_ = address;
  if (who_am_i() != kId) return false;
  // Software reset, then wait for it to clear (datasheet: ~50 us).
  if (!write_reg(kCtrl3C, 0x01)) return false;
  for (int i = 0; i < 20; i++) {
    delay(1);
    uint8_t c3 = 0;
    if (read_regs(kCtrl3C, &c3, 1) && !(c3 & 0x01)) break;
  }
  bool ok = true;
  ok &= write_reg(kCtrl3C, 0x44);  // BDU | IF_INC (register auto-increment)
  ok &= write_reg(kFifoCtrl4, 0x00);  // bypass: clears the FIFO
  ok &= write_reg(kCtrl1Xl, (kOdr26Hz << 4) | (kFsXl4g << 2));
  ok &= write_reg(kCtrl2G, (kOdr26Hz << 4) | (kFsG500dps << 2));
  ok &= write_reg(kFifoCtrl3, (kOdr26Hz << 4) | kOdr26Hz);
  ok &= write_reg(kFifoCtrl4, kFifoContinuous);
  have_gyro_ = have_accel_ = false;
  return ok;
}

bool Lsm6dso::enable_wake_on_motion(uint8_t threshold_lsb) {
  if (!wire_) return false;
  bool ok = true;
  ok &= write_reg(kFifoCtrl4, 0x00);               // FIFO bypass: nothing batched
  ok &= write_reg(kCtrl2G, 0x00);                  // gyro power-down
  ok &= write_reg(kCtrl6C, 0x10);                  // XL_HM_MODE: accel low-power modes
  ok &= write_reg(kCtrl1Xl, 0x1 << 4);             // 12.5 Hz, +-2 g
  ok &= write_reg(kWakeUpDur, 0x00);               // wake on the first sample over threshold
  ok &= write_reg(kWakeUpThs, threshold_lsb & 0x3F);
  ok &= write_reg(kTapCfg2, 0x80);                 // INTERRUPTS_ENABLE
  ok &= write_reg(kMd1Cfg, 0x20);                  // INT1_WU
  return ok;
}

int Lsm6dso::read_fifo(const SampleFn& fn) {
  uint8_t st[2];
  if (!read_regs(kFifoStatus1, st, 2)) return -1;
  int words = st[0] | ((st[1] & 0x03) << 8);
  overrun_ = (st[1] & 0x40) != 0;  // FIFO_OVR_IA
  if (overrun_) overrun_count_++;
  int samples = 0;
  for (int i = 0; i < words; i++) {
    uint8_t tag;
    uint8_t d[6];
    // Same sequence as ST's driver: tag first, then the six data bytes.
    if (!read_regs(kFifoDataOutTag, &tag, 1)) return -1;
    if (!read_regs(kFifoDataOutXL, d, 6)) return -1;
    switch (tag >> 3) {
      case kTagGyro:
        for (int k = 0; k < 3; k++) gyro_[k] = le16(d + 2 * k) * kGyroScale;
        have_gyro_ = true;
        break;
      case kTagAccel:
        for (int k = 0; k < 3; k++) accel_[k] = le16(d + 2 * k) * kAccelScale;
        have_accel_ = true;
        break;
      default:
        break;  // timestamps, temperature: not batched, ignore if present
    }
    if (have_gyro_ && have_accel_) {
      fn(gyro_, accel_);
      have_gyro_ = have_accel_ = false;
      samples++;
    }
  }
  return samples;
}
