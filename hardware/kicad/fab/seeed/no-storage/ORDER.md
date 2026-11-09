# WaveHat rev A, no-storage build: assembly instructions (Seeed Fusion)

The same board, assembled on the **top side only**. The log storage on the bottom side is left off:

| Left off (bottom side) | What it is |
|---|---|
| U5 | SD NAND log storage (Zetta ZDSD02GLGEAG) |
| C8, C9 | Its decoupling capacitors |
| R9, R10, R11, R12 | Its 10 kΩ pull-ups on D3, D8, D9, D10 |

That leaves **one stencil and one assembly pass**. It also takes US$45.59 of storage chips off a 5-board quote, plus Seeed's second-side setup.

**The board works without them.** Everything except logging works: the IMU, CAN, power and Wi-Fi. The WaveHat firmware shows "Log storage: not found" on its status page and carries on. VESC Express runs without storage, as tested on a bare XIAO C3. The C3 still boots normally, because its D9 boot pin has its own internal pull-up and D8 only matters for flashing. The bottom pads stay, ENIG-plated, so the storage can be fitted later (see the end).

## Files (this folder)

| File | Use it for |
|---|---|
| `wavehat-seeed-gerbers.zip` | **Add Gerber Files.** The same Gerbers as the full build: the board is identical, only what is placed differs. Includes the drill file and the fab notes |
| `wavehat-seeed-assembly-nostorage.zip` | **Upload Assembly Instructions.** Top-side pick and place, the top assembly drawing, 3D renders, a detailed BOM, the fab notes, and this file |
| `wavehat-seeed-bom-nostorage-c3.csv` / `-c6.csv` / `-s3.csv` | **Add BOM File**, with the XIAO placed by Seeed (C3 113991054, C6 113991254, S3 113991114) |
| `wavehat-seeed-bom-nostorage-noxiao.csv` | **Add BOM File**, if you solder your own XIAO on afterwards (14 large castellated pads, easy with an iron) |
| `wavehat-seeed-pcba-nostorage-<option>.zip` | Everything for one option in one flat archive, if Seeed asks for the full set |

## On the order page

https://www.seeedstudio.com/fusion_pcb.html

| Form box | Choose or upload |
|---|---|
| Add Gerber Files | `wavehat-seeed-gerbers.zip` |
| Base material / layers | FR-4 TG130, 2 layers |
| Dimensions / thickness | 21 × 54 mm, 1.6 mm |
| Surface finish | **ENIG** (the IMU is a 0.5 mm-pitch LGA) |
| Copper / track / hole | 1 oz, 6/6 mil, 0.3 mm; no castellated holes, no impedance control |
| Minimum solder mask dam | **0.1 mm** (about US$25 extra): keeps solder mask between the IMU's 0.5 mm-pitch pads, against solder bridges under it. 0.4 mm removes those dams |
| PCB Assembly | On (sign in) |
| Upload Assembly Instructions | `wavehat-seeed-assembly-nostorage.zip` |
| PCB Quantity / PCBA Qty | Bare boards are cheap, so order 10 boards and have 5 assembled: the other 5 come bare, for spares or a later batch. Make the PCBA quantity 5 |
| Conformal Coating | No |
| Add BOM File | **`wavehat-seeed-bom-nostorage-noxiao.csv`** if you fit your own XIAOs (the plan: 10 XIAO ESP32C6 on order). Otherwise `-c3`, `-c6` or `-s3` for a XIAO placed by Seeed |
| MCU model used in the project | `113991254` (Seeed Studio XIAO ESP32C6), fitted by the customer after delivery |
| Testing Services | None |

Order notes to paste:

> Single-sided SMT: top side only. Do NOT assemble the bottom side: U5, C8, C9, R9, R10, R11, R12 are intentionally left unfitted (pads stay empty; no bottom stencil needed, although the Gerbers include the bottom paste layer). Top: all BOM parts; U4 is a Seeed XIAO module (castellated, from the OPL) if listed in the BOM. Please X-ray U1 (LGA-14, 0.5 mm pitch) on the first boards, and confirm the rotation of U1, U2, U3 and the diodes D1, D2, D3, TVS1 in your placement preview.

## What gets assembled (top side, 24 parts plus the optional XIAO)

| Ref | Part | Note |
|---|---|---|
| U1 | ST **LSM6DSOTR** IMU, LGA-14 | The fine-pitch part; ask for X-ray |
| U2 | TI **LMR51606YDBVR** buck, 4–65 V | The 1.1 MHz PFM version (Y suffix) |
| U3 | TI **SN65HVD230DR** CAN transceiver | |
| L1 | Changjiang **FNR4020S150MT**, 15 µH (LCSC C167837) | |
| TVS1 | **SMBJ30A** | 30 V standoff |
| F1 | Littelfuse **1812L050/60MR** (LCSC C87383) | 0.5 A, 60 V PTC |
| C4 | Murata **GRM31CR72A225KA73L**, 2.2 µF 100 V 1206 | |
| D1, D2, D3 | SS14 | |
| J2, J3 | JST SM04B-SRSS-TB(LF)(SN) (Qwiic), SM04B-GHS-TB(LF)(SN) (VESC CAN) | |
| C1, C2, C3, C5, C6, C7, R1–R6 | Passives, 0402–0805 | As in the BOM |
| U4 | Seeed XIAO (optional) | Or fit your own afterwards |

Fiducials: FID1–FID3 on the top. The bottom fiducials (FID4, FID5) are not needed.

## Fitting your own XIAO ESP32C6

With the no-XIAO BOM, the boards arrive with the U4 footprint empty: 14 castellated pads on the top side, nothing underneath.
1. Flash and test each XIAO on USB first; it is harder to swap once soldered.
2. Tin one corner pad on the board. Place the XIAO with its USB-C over the board's USB end (the silkscreen outline shows it), tack that pad, check it sits flat and square, then solder the other 13 with an iron and flux.
3. The C6's antenna switch: the WaveHat firmware (through the Arduino core's XIAO C6 variant) and the VESC Express `WaveHat C6` board file both select the on-board ceramic antenna at boot.

Firmware for the C6: `pio run -e xiao_c6` (WaveHat sea-state firmware), or VESC Express built with `HW_NAME="WaveHat C6"` (`../../firmware/vesc_express/`).

## Supply and behaviour (unchanged)

5–30 V on the J4 pads (NMEA 2000 or a supply lead), or 5 V on J3 or USB-C. Solder jumpers as built: JP1, JP2 (I²C pull-ups) and JP7 (D3 to the storage CS) bridged, JP3 at 0x6B, JP4–JP6 open. With no storage fitted, D3 is free if you cut JP7.

## Fitting the storage later

Parts, per board: U5 Zetta ZDSD02GLGEAG (or MK MKDV4GCL-ABB for 512 MB, same pads), C8 100 nF 0402, C9 10 µF 0603, R9–R12 10 kΩ 0402. They all go on the bottom face, under the XIAO.

U5 is a leadless LGA, so it needs solder paste and hot air (or a reflow hotplate with the board supported clear of the XIAO). An iron alone won't do it. Fit the six passives the same way, then check pin 1 against the silkscreen dot. The firmware and the VESC Express board files find the storage at the next boot and format it.
