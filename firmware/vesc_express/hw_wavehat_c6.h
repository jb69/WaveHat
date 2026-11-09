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

// WaveHat (sea-state sensor and CAN node) carrying a Seeed XIAO ESP32-C6.
// Board files kept in raspberry-pi-boat-computer/projects/wavehat/firmware/vesc_express; pin map in hardware/DESIGN.md section 4.
//   D0 / D1   CAN RX / TX to the on-board SN65HVD230 (J3 VESC CAN, J4 NMEA 2000)
//   D2        status LED, red (external, on pad TP1)
//   D3        SD NAND chip select through JP7 (bridged as built); LED_B / IMU INT2 otherwise
//   D4 / D5   I2C SDA / SCL: LSM6DSO at 0x6B, start it from Lisp: (imu-start-lsm6 'rate-400k 22 23)
//   D6 / D7   UART TX / RX (GNSS)
//   D8 D9 D10 SD NAND SCK / MISO / MOSI: 256 MB soldered log storage, mounted at boot like a card
// The XIAO C6 has 4 MB of flash (esp32c6_fh4). Its RF switch: GPIO 3 low enables it, GPIO 14 picks the
// antenna (low = on-board ceramic, high = U.FL); set below to the ceramic one (Seeed wiki).

#ifndef MAIN_HWCONF_SEEED_HW_WAVEHAT_C6_H_
#define MAIN_HWCONF_SEEED_HW_WAVEHAT_C6_H_

#include "driver/gpio.h"

#define HW_NAME						"WaveHat C6"
#define HW_TARGET					"esp32c6_fh4"

#ifndef CONF_BLE_NAME
#define CONF_BLE_NAME				"WaveHat"
#endif

#define HW_INIT_HOOK()				hw_init()

// LED: red on D2 only; D3 is the storage chip select
#define LED_RED_PIN					2
#define LED_RED_ON()				gpio_set_level(LED_RED_PIN, 1)
#define LED_RED_OFF()				gpio_set_level(LED_RED_PIN, 0)

// CAN
#define CAN_TX_GPIO_NUM				1 // D1
#define CAN_RX_GPIO_NUM				0 // D0

// SD NAND (SD protocol, SPI mode)
#define SD_PIN_MOSI					18 // D10
#define SD_PIN_MISO					20 // D9
#define SD_PIN_SCK					19 // D8
#define SD_PIN_CS					21 // D3

// XIAO C6 RF switch (Seeed wiki): GPIO 3 low enables it; GPIO 14 low = on-board antenna, high = U.FL
#define RF_SWITCH_EN_PIN			3
#define RF_ANT_SELECT_PIN			14
#ifndef RF_ANT_EXTERNAL
#define RF_ANT_EXTERNAL				0
#endif

// UART
#define UART_NUM					0
#define UART_BAUDRATE				115200
#define UART_TX						16 // D6
#define UART_RX						17 // D7

// Functions
void hw_init(void);

#endif /* MAIN_HWCONF_SEEED_HW_WAVEHAT_C6_H_ */
