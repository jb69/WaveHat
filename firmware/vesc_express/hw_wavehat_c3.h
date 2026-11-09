/*
	Copyright 2026 WaveHat project

	This file is part of the VESC firmware.

	The VESC firmware is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    The VESC firmware is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
    */

// WaveHat (sea-state sensor and CAN node) carrying a Seeed XIAO ESP32-C3.
// Board files kept in raspberry-pi-boat-computer/projects/wavehat/firmware/vesc_express; pin map in hardware/DESIGN.md section 4.
//   D0 / D1   CAN RX / TX to the on-board SN65HVD230 (J3 VESC CAN, J4 NMEA 2000)
//   D2        status LED, red (external, on pad TP1)
//   D3        SD NAND chip select through JP7 (bridged as built); LED_B / IMU INT2 otherwise
//   D4 / D5   I2C SDA / SCL: LSM6DSO at 0x6B, start it from Lisp: (imu-start-lsm6 'rate-400k 6 7)
//   D6 / D7   UART TX / RX (GNSS)
//   D8 D9 D10 SD NAND SCK / MISO / MOSI: 256 MB soldered log storage, mounted at boot like a card
// GPIO 8 and 9 are the C3's strapping pins: the board's 10k pull-ups hold them high at reset, as on
// the Nanolog (SD MISO on GPIO 8) and the Scope / Link (SD CS on GPIO 9).

#ifndef MAIN_HWCONF_SEEED_HW_WAVEHAT_C3_H_
#define MAIN_HWCONF_SEEED_HW_WAVEHAT_C3_H_

#include "driver/gpio.h"

#define HW_NAME						"WaveHat C3"
#define HW_TARGET					"esp32c3"

#ifndef CONF_BLE_NAME
#define CONF_BLE_NAME				"WaveHat"
#endif

#define HW_INIT_HOOK()				hw_init()

// LED: red on D2 only; D3 is the storage chip select
#define LED_RED_PIN					4
#define LED_RED_ON()				gpio_set_level(LED_RED_PIN, 1)
#define LED_RED_OFF()				gpio_set_level(LED_RED_PIN, 0)

// CAN
#define CAN_TX_GPIO_NUM				3 // D1
#define CAN_RX_GPIO_NUM				2 // D0

// SD NAND (SD protocol, SPI mode)
#define SD_PIN_MOSI					10 // D10
#define SD_PIN_MISO					9 // D9
#define SD_PIN_SCK					8 // D8
#define SD_PIN_CS					5 // D3

// UART
#define UART_NUM					0
#define UART_BAUDRATE				115200
#define UART_TX						21 // D6
#define UART_RX						20 // D7

// Functions
void hw_init(void);

#endif /* MAIN_HWCONF_SEEED_HW_WAVEHAT_C3_H_ */
