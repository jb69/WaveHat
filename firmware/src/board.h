// WaveHat rev B: what each XIAO pin does, and which GPIO sits behind each pin name on each XIAO.
//
// The hat uses the XIAO's pin NAMES (D0-D10); Arduino's XIAO variants define them, so the code
// below uses D0 etc. and this table is the reference (hardware/DESIGN.md section 11, netlist-revB.md).
//
//   Pin  Net        Job in this firmware                                  C3    C6    S3
//   D0   CAN_RX     CAN RXD from U3 through JP9 (bridged as built)        GPIO2 GPIO0 GPIO1
//   D1   CAN_TX     CAN TXD to U3 through JP10 (bridged as built)         3     1     2
//   D2   LED_R      status LED pad TP1; IMU INT1 when JP4 is bridged       4     2     3
//                   (the wake-on-motion input for battery mode)
//   D3   LED_B      SD NAND chip select through JP7 (bridged as built)    5     21    4
//   D4   SDA        I2C: LSM6DSO at 0x6B (JP3), J2 Qwiic, J5's compass     6     22    5
//   D5   SCL                                                              7     23    6
//   D6   UART_TX    GNSS UART, XIAO TX -> J5 pin 2 / J6 pin 6              21    16    43
//   D7   UART_RX    GNSS UART, XIAO RX <- J5 pin 3 / J6 pin 7              20    17    44
//   D8   SD_SCK     SD NAND SPI                                            8     19    7
//   D9   SD_MISO    SD NAND SPI (the C3's BOOT strap, held high by R11)    9     20    8
//   D10  SD_MOSI    SD NAND SPI                                            10    18    9
//
// J6, the 10-pin IO header: 1 5V, 2 3V3, 3 GND, 4 D2, 5 D3, 6 D6, 7 D7, 8 D0, 9 D1, 10 GND.
// Pins 4-9 are the same nets as above, so what a lead on J6 can do depends on the build:
//   D2  free (an LED, a signal) unless JP4 is bridged for the IMU interrupt;
//   D3  the NAND's chip select: free only with JP7 cut and no log storage;
//   D6/D7  the GNSS UART (this firmware drives them when GNSS is enabled; otherwise idle);
//   D0/D1  the CAN lines: free only with JP8, JP9 and JP10 cut (U3 off) and JP6 open, which
//          is the no-CAN build; this firmware then leaves the CAN controller off (battery mode).
//
// The BOOT button pin (WAVEHAT_BOOT_BUTTON in platformio.ini) is the XIAO's own: GPIO 9 on the
// C3 and C6, GPIO 0 on the S3.

#pragma once

#include <Arduino.h>

namespace board {

constexpr int kImuInt1Pin = D2;   // LSM6DSO INT1 through JP4 (open as built: bridge it for sleep)
constexpr int kGnssTxPin = D6;    // XIAO TX -> GNSS RX
constexpr int kGnssRxPin = D7;    // XIAO RX <- GNSS TX

}  // namespace board
