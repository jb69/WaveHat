# VESC Express board files for the WaveHat

These files let Vedder's [VESC Express](https://github.com/vedderb/vesc_express) firmware run on a WaveHat with its I/O already set up. VESC Tool then sees a "WaveHat C3" (or C6 / S3), CAN works through the on-board transceiver, and the 256 MB SD NAND is mounted at boot for logging, with no Lisp needed.

| | C3 | C6 | S3 |
|---|---|---|---|
| `HW_NAME` | `WaveHat C3` | `WaveHat C6` | `WaveHat S3` |
| `HW_TARGET` | `esp32c3` | `esp32c6_fh4` (XIAO C6: 4 MB flash) | `esp32s3_fh4` (uses 4 MB of the XIAO S3's 8 MB, no PSRAM) |
| CAN RX / TX (D0 / D1) | GPIO 2 / 3 | 0 / 1 | 1 / 2 |
| SD NAND SCK / MISO / MOSI / CS (D8 / D9 / D10 / D3) | 8 / 9 / 10 / 5 | 19 / 20 / 18 / 21 | 7 / 8 / 9 / 4 |
| UART TX / RX (D6 / D7), e.g. a GNSS | 21 / 20 | 16 / 17 | 43 / 44 |
| Red status LED (D2, pad TP1) | 4 | 2 | 3 |
| IMU (LSM6DSO, D4 / D5) from Lisp | `(imu-start-lsm6 'rate-400k 6 7)` | `… 22 23` | `… 5 6` |
| Other | | RF switch: GPIO 3 low enables it, GPIO 14 low selects the on-board antenna (`-DRF_ANT_EXTERNAL=1` for the U.FL) | |

The C3's CAN pins are the same as VESC Express's own `Seeed ESP32-C3` target, so a WaveHat C3 works on that stock build too. Only the storage needs these files, or one Lisp line: `(f-connect 10 9 8 5)`.

There's no blue LED: D3 is the storage's chip select (JP7, bridged as built). The IMU isn't started from the board file, because VESC Express starts the LSM6 from Lisp, as on the Takuma node.

## Build

The files go into VESC Express's `main/hwconf/seeed/` folder, which is already on its include path. The build finds a board by its `HW_NAME`.

```bash
cp hw_wavehat_* ~/esp/vesc_express/main/hwconf/seeed/
```

```bash
cd ~/esp/vesc_express && source ~/esp/esp-idf/export.sh && idf.py -B build_wavehat_c3 -DSDKCONFIG=build_wavehat_c3/sdkconfig -DHW_NAME="WaveHat C3" build
```

Use ESP-IDF 5.5.4 for VESC Express up to the September 2026 commits; current master has moved to IDF 6.1. A separate build folder and sdkconfig per board keep the three targets from clashing. The S3 needs the Xtensa compiler (`~/esp/esp-idf/install.sh esp32s3`); PlatformIO's `toolchain-xtensa-esp-elf` is the same version and works on the PATH.

**Checked (20 Oct 2026),** against VESC Express `c085911` (17 Sep 2026) and ESP-IDF 5.5.4: all three build with their own board file compiled in (`HW_HEADER="hw_wavehat_c3.h"` etc., and the name in the binary). App sizes against the 1.56 MB OTA slot:

| Board | App size | Free |
|---|---|---|
| WaveHat C3 | 1.42 MB | 9 % |
| WaveHat C6 | 1.49 MB | 4 % |
| WaveHat S3 | 1.31 MB | 16 % |

**Boot-tested (20 Oct 2026)** on a bare XIAO C3: it boots, and answers VESC Tool's firmware-version request as "WaveHat C3", firmware 7.0. With no SD NAND fitted, the storage mount fails and the app carries on. CAN and the storage itself need a WaveHat board.

## Logging

With the storage mounted, logging works as on Trampa's VESC Express or the VESC Nanolog. Install the LogUI package on the ESC from VESC Tool, tick the values to log, and set the logger's CAN ID to the WaveHat's (default 2). Logs are read back in desktop VESC Tool's Log Analysis, or over Wi-Fi from the file manager. A new chip is formatted (FAT) the first time it is mounted. 256 MB holds about 10 hours at 20 Hz with forty fields.

The files are GPL-3.0, like the rest of VESC Express, so they can be offered upstream next to `hw_seeed_esp32c3`.
