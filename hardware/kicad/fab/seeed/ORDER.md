# Ordering WaveHat rev A from Seeed Fusion

Files in this folder (regenerate with `run_pipeline.sh`, then `python3 -I gen_seeed.py`):

| File | Use it for |
|---|---|
| `wavehat-seeed-gerbers.zip` | **Bare boards** (Fusion PCB), and the Gerber upload for assembled boards |
| `wavehat-seeed-bom-c3.csv` / `-c6.csv` / `-s3.csv` | Assembled boards **with the XIAO placed by Seeed**, from its Open Parts Library (C3 113991054, C6 113991254, S3 113991114) |
| `wavehat-seeed-bom-noxiao.csv` | Assembled boards **without the XIAO** (you solder it on yourself: 14 large castellated pads) |
| `wavehat-seeed-cpl.csv` | Pick and place, both sides (Designator, Mid X, Mid Y, Layer, Rotation; mm from the board's lower-left corner) |
| `wavehat-assembly-top.pdf`, `wavehat-assembly-bottom.pdf` | Assembly drawings; the bottom one is seen from below |
| `wavehat-seeed-assembly.zip` | For the **Upload Assembly Instructions** box: pick and place, both assembly drawings, 3D renders, these notes |
| `wavehat-seeed-pcba-<option>.zip` | Everything for one option in one flat archive (Gerber files at the top level), if Seeed asks for the full set |

**On the order page** (https://www.seeedstudio.com/fusion_pcb.html), box by box:

| Form box | What to give it |
|---|---|
| Add Gerber Files (ZIP or RAR) | `wavehat-seeed-gerbers.zip` |
| PCB options | As in the table below: 2 layers, 21 × 54 mm, 1.6 mm, ENIG, 1 oz, 6/6 mil, 0.3 mm holes, no castellated holes |
| PCB Assembly | Switch on, then sign in |
| Upload Assembly Instructions (ZIP or RAR) | `wavehat-seeed-assembly.zip`: pick and place, assembly drawings (top, and bottom seen from below), 3D renders, these notes |
| PCBA Qty | 5 for the first run |
| Conformal Coating | **No** for the first boards. A coating would have to keep off the XIAO, USB-C, J2, J3, the J4 pads and the solder jumpers; reconsider it for a production run, with masking instructions |
| Add BOM File (CSV, XLS, XLSX) | `wavehat-seeed-bom-c3.csv` (or `-c6` / `-s3`, or `-noxiao` to fit the XIAO yourself). Its columns match Seeed's template, and the XIAO line carries the Seeed SKU, as the form asks |
| MCU model used in the project | `113991054` (Seeed Studio XIAO ESP32C3); or `113991254` for the C6, `113991114` for the S3 |
| Testing Services | None (no test procedure yet) |

Seeed gives a 30 % coupon on PCBA orders that include a XIAO. `wavehat-seeed-pcba-<option>.zip` holds everything for one option in one flat archive, if Seeed asks for it by email.

## Fusion PCB (bare boards)

| Option | Choose |
|---|---|
| Base material | FR-4 TG130 (or TG150) |
| Layers | 2 |
| Dimensions | 21 × 54 mm |
| Quantity | 5 or 10 |
| Thickness | 1.6 mm |
| Surface finish | **ENIG** (flat pads for the two LGA parts; about US$30 extra on Seeed's form). Cheaper flat option: **OSP**. Avoid HASL: its uneven solder on the pads is a risk under the two LGAs |
| Copper | 1 oz |
| Min. track / space | 6 / 6 mil (the design uses 0.15 mm) |
| Minimum solder mask dam | **0.1 mm** (about US$25 extra): keeps mask between the IMU's 0.5 mm-pitch pads; 0.4 mm removes those dams |
| Min. hole | 0.3 mm (vias 0.3 mm drill, 0.6 mm pad, tented) |
| Solder mask / silkscreen | Green / white (any colour works) |
| Castellated holes, gold fingers, V-cut | No |
| Order number on the board | Ask for a specified location if offered: the bottom face under the XIAO, near the J4 pads, has room |

## Fusion PCBA (assembled)

| Item | Value |
|---|---|
| Assembly | **SMT, both sides.** Bottom: U5 (SD NAND), C8, C9, R9–R12 (7 parts). Top: everything else (24 parts, plus the XIAO if ordered) |
| Unique parts | 21 lines, plus 1 if the XIAO is ordered |
| Fiducials | 3 on the top (FID1–FID3), 2 on the bottom (FID4, FID5) |
| Through-hole parts | None |
| Fine-pitch / hidden joints | U1 LSM6DSO (LGA-14, 0.5 mm pitch) and U5 SD NAND (LGA-8): ask for X-ray inspection on the first batch |
| Not fitted | Nothing in the BOM is DNP. Solder jumpers JP1–JP7, test pads TP1/TP2, the J4 NMEA 2000 pads and the mounting holes are bare copper, not parts |
| Process order | Bottom side first (7 small parts), then the top side with the XIAO |

Order notes to paste:

> 2-layer, both sides SMT. Bottom: U5 (LGA-8 SD NAND, pin 1 marked by the dot on the bottom silkscreen and assembly drawing), C8, C9, R9, R10, R11, R12. Top: all other BOM parts; U4 is a Seeed XIAO module (castellated, from the OPL) if listed in the BOM. Please X-ray U1 and U5 on the first boards. Please confirm the rotation of U1, U2, U3, U5 and the diodes D1, D2, D3, TVS1 in your placement preview: the CPL comes from KiCad and rotation conventions differ.

## Parts to check against Seeed's sourcing

| Ref | Part | Note |
|---|---|---|
| U5 | Zetta **ZDSD02GLGEAG** (2 Gbit = 256 MB SLC SD NAND, LGA-8 6 × 8 mm, LCSC C2875853) | The land pattern also takes MK MKDV4GCL-ABB or CS-Creative CSNP4GCR01-BOW (4 Gbit, 512 MB) and MK MKDV1GCL-ABA (1 Gbit): same pinout and package |
| U2 | TI **LMR51606YDBVR** | 4–65 V buck, the 1.1 MHz PFM version (the Y suffix) that R3/R4 and L1 are sized for. Not the X (400 kHz) or F (forced PWM) versions |
| L1 | Changjiang **FNR4020S150MT**, 15 µH, 4 × 4 mm (LCSC C167837) | Shielded, Isat 1.5 A, rated 1.1 A. Another 4020-size shielded 15 µH part with Isat ≥ 1.4 A on the same pads will do |
| U1 | ST **LSM6DSOTR** | |
| R3 | Yageo **RC0402FR-07120KL** (120 kΩ) | Sets the 5 V output with R4; 120 kΩ is a stocked standard value |
| U3 | TI **SN65HVD230DR** | |
| TVS1 | **SMBJ30A** (SMB, unidirectional) | 30 V standoff for the 5–30 V input; clamps at 48.4 V, inside U2's 70 V and C4's 100 V ratings. Any maker |
| C4 | Murata **GRM31CR72A225KA73L**, 2.2 µF 100 V X7R 1206 | Input capacitor; keep the 100 V rating |
| D1, D2, D3 | SS14 (SMA, 40 V 1 A) | Generic Schottky; any maker |
| F1 | Littelfuse **1812L050/60MR** (LCSC C87383) | 1812 PTC, 0.5 A hold, 60 V; BHFUSE BSMD1812-050-60V (LCSC C883142) is an equivalent |
| J2, J3 | JST SM04B-SRSS-TB(LF)(SN) (Qwiic, LCSC C160404), SM04B-GHS-TB(LF)(SN) (VESC CAN) | Genuine JST; J3 link: DigiKey 455-1566-1-ND, LCSC C189895 |

## After the boards arrive

1. Before powering: check that U5's pin 1 matches the silkscreen dot, and that JP7 is bridged (a thin copper trace links its pads as built).
2. Power from USB-C first, then the 12 V pads.
3. Flash either the WaveHat firmware (`../../firmware/`, PlatformIO) or VESC Express built with `HW_NAME="WaveHat C3"` (or C6 / S3; board files in `../../firmware/vesc_express/`). Both mount the SD NAND at boot and format it the first time.
