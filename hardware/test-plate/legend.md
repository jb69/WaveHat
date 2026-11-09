# Test jig legend (WaveHat rev A)

The board lies component side down on the base, bow end at BOW, pegs through its mounting holes; the plate lies on the bottom face. Plate holes are numbered 1-21 on the plate; base holes T1-T29 go up through the base to the component side and are numbered on the base's underside. Every reading below is between two pads whose only connection runs through vias, so 0 Ω (or the resistor stated) means those vias conduct and nothing needs its solder mask scraped. Work through the three tables; a fail names the net and the vias in question (`../kicad/reports/vias.md` has their positions).

## Plate to plate (both probes from above)

| Net | Probe A | Probe B | Expect | Covers |
|---|---|---|---|---|
| 3V3 | 17 (C9 pad 1) | 1 (JP3 pad 1) | 0 Ω | both 3V3 vias in series: board 2's fault |
| CANL | 16 (J4 pad 5) | 5 (JP6 pad 2) | 0 Ω | all four CANL vias |
| SDA_PU | 7 (JP1 pad 2) | 1 (JP3 pad 1) | 4.7 kΩ | the SDA_PU via, through R1 on top |
| SCL_PU | 12 (JP2 pad 2) | 1 (JP3 pad 1) | 4.7 kΩ | the SCL_PU via, through R2 on top |
| TERM | 4 (JP6 pad 1) | 15 (J4 pad 4) | 120 Ω | the TERM via and J4's CANH via, through R5 |

## Base to base (both probes from below, up through the base)

| Net | Probe A | Probe B | Expect | Covers |
|---|---|---|---|---|
| CAN_TX | T27 (U4 pad 2) | T6 (U3 pad 1) | 0 Ω | all four CAN_TX vias |
| CAN_RX | T29 (U4 pad 1) | T7 (U3 pad 4) | 0 Ω | both CAN_RX vias |
| CANL | T8 (J3 pad 2) | T2 (U3 pad 6) | 0 Ω | the two CANL vias between J3 and U3 |
| 5V_CAN | T17 (D3 pad 2) | T4 (J3 pad 4) | 0 Ω | both 5V_CAN vias |
| XIAO_5V | T28 (U4 pad 14) | T15 (D2 pad 1) | 0 Ω | both XIAO_5V vias |
| 5V_BUCK | T11 (C5 pad 1) | T16 (D2 pad 2) | 0 Ω | both 5V_BUCK vias |
| CB | T10 (C6 pad 1) | T12 (U2 pad 1) | 0 Ω | both CB vias |
| VIN | T14 (C4 pad 1) | T13 (TVS1 pad 1) | 0 Ω | both VIN vias |
| SDA | T23 (U4 pad 5) | T1 (J2 pad 3) | 0 Ω | the SDA vias between the XIAO and J2 (not the one at the IMU) |
| SCL | T19 (U4 pad 6) | T5 (J2 pad 4) | 0 Ω | the SCL vias between the XIAO and J2 (not the one at the IMU) |

## Plate to base (one probe each side)

| Net | Plate hole | Base hole | Expect | Covers |
|---|---|---|---|---|
| SD_SCK | 20 (R10 pad 2) | T18 (U4 pad 9) | 0 Ω | its single via |
| SD_MISO | 19 (R11 pad 2) | T20 (U4 pad 10) | 0 Ω | its single via |
| SD_MOSI | 18 (R12 pad 2) | T21 (U4 pad 11) | 0 Ω | its single via |
| LED_B / SD CS | 9 (TP2 pad 1) | T22 (U4 pad 4) | 0 Ω | its single via: board 2's second fault |
| LED_R | 10 (TP1 pad 1) | T25 (U4 pad 3) | 0 Ω | its single via |
| VIN_RAW | 13 (J4 pad 2) | T9 (F1 pad 1) | 0 Ω | its single via |
| CANH | 15 (J4 pad 4) | T3 (J3 pad 3) | 0 Ω | the CANH vias between J4 and J3 |
| 3V3 island | 17 (C9 pad 1) | T24 (U4 pad 12) | 0 Ω | the island's via alone |
| SDA | 6 (JP1 pad 1) | T23 (U4 pad 5) | 0 Ω | the SDA vias to the pull-up jumper |
| SCL | 11 (JP2 pad 1) | T19 (U4 pad 6) | 0 Ω | the SCL vias to the pull-up jumper |
| GND | 14 (J4 pad 3) | T26 (U4 pad 13) | 0 Ω | reference (the pours carry GND) |

**Not testable with a meter:** SA0 (JP3 pin 2), IMU_INT1 (JP4 pin 1) and IMU_INT2 (JP5 pin 1) end at the IMU's LGA pads under the chip: no meter check. SA0 passes if the IMU answers at 0x6B with JP3 at 3V3; the INT lines are unused unless JP4/JP5 are bridged.

## Plate holes (bottom view, x mirrored)

| No. | Over | Net |
|---|---|---|
| 1 | JP3 pad 1 (9.2, 43.0) | 3V3 (JP3) |
| 2 | JP3 pad 2 (10.5, 43.0) | SA0 |
| 3 | JP4 pad 1 (3.3, 40.0) | IMU_INT1 |
| 4 | JP6 pad 1 (9.8, 39.5) | TERM |
| 5 | JP6 pad 2 (11.2, 39.5) | CANL (JP6) |
| 6 | JP1 pad 1 (16.3, 40.0) | SDA |
| 7 | JP1 pad 2 (17.7, 40.0) | SDA_PU |
| 8 | JP5 pad 1 (3.3, 37.0) | IMU_INT2 |
| 9 | TP2 pad 1 (10.5, 35.8) | LED_B (D3, NAND CS) |
| 10 | TP1 pad 1 (14.0, 35.8) | LED_R (D2) |
| 11 | JP2 pad 1 (16.3, 37.0) | SCL |
| 12 | JP2 pad 2 (17.7, 37.0) | SCL_PU |
| 13 | J4 pad 2 (7.5, 28.0) | VIN_RAW |
| 14 | J4 pad 3 (10.5, 28.0) | GND |
| 15 | J4 pad 4 (13.5, 28.0) | CANH |
| 16 | J4 pad 5 (16.5, 28.0) | CANL |
| 17 | C9 pad 1 (16.8, 15.8) | 3V3 (NAND island) |
| 18 | R12 pad 2 (14.1, 9.9) | SD_MOSI (D10) |
| 19 | R11 pad 2 (15.4, 9.9) | SD_MISO (D9) |
| 20 | R10 pad 2 (16.7, 9.9) | SD_SCK (D8) |
| 21 | R9 pad 2 (18.0, 9.9) | SD_CS (D3 through JP7) |

## Base holes (top view)

| No. | Over | Net |
|---|---|---|
| T1 | J2 pad 3 (5.3, 40.5) | SDA, J2 tail |
| T2 | U3 pad 6 (11.1, 43.2) | CANL, transceiver |
| T3 | J3 pad 3 (15.9, 40.8) | CANH, J3 tail |
| T4 | J3 pad 4 (15.9, 42.1) | 5V_CAN, J3 tail |
| T5 | J2 pad 4 (5.3, 39.5) | SCL, J2 tail |
| T6 | U3 pad 1 (8.6, 38.3) | CAN_TX, transceiver TXD |
| T7 | U3 pad 4 (12.4, 38.3) | CAN_RX, transceiver RXD |
| T8 | J3 pad 2 (15.9, 39.6) | CANL, J3 tail |
| T9 | F1 pad 1 (1.2, 32.6) | VIN_RAW, fuse |
| T10 | C6 pad 1 (14.9, 32.1) | CB, bootstrap |
| T11 | C5 pad 1 (19.6, 31.7) | 5V_BUCK, buck output |
| T12 | U2 pad 1 (11.5, 28.8) | CB, buck BST |
| T13 | TVS1 pad 1 (1.8, 27.9) | VIN, TVS |
| T14 | C4 pad 1 (9.0, 26.4) | VIN, input capacitor |
| T15 | D2 pad 1 (2.4, 23.4) | XIAO_5V, D2 anode |
| T16 | D2 pad 2 (6.4, 23.4) | 5V_BUCK, D2 cathode |
| T17 | D3 pad 2 (13.9, 23.4) | 5V_CAN, D3 cathode |
| T18 | U4 pad 9 (2.4, 15.6) | SD_SCK, XIAO D8 |
| T19 | U4 pad 6 (18.6, 15.6) | SCL, XIAO D5 |
| T20 | U4 pad 10 (2.4, 13.0) | SD_MISO, XIAO D9 |
| T21 | U4 pad 11 (2.4, 10.5) | SD_MOSI, XIAO D10 |
| T22 | U4 pad 4 (18.6, 10.5) | LED_B, XIAO D3 |
| T23 | U4 pad 5 (18.6, 13.0) | SDA, XIAO D4 |
| T24 | U4 pad 12 (2.4, 8.0) | 3V3, XIAO 3V3 |
| T25 | U4 pad 3 (18.6, 8.0) | LED_R, XIAO D2 |
| T26 | U4 pad 13 (2.4, 5.4) | GND, XIAO GND |
| T27 | U4 pad 2 (18.6, 5.4) | CAN_TX, XIAO D1 |
| T28 | U4 pad 14 (2.4, 2.9) | XIAO_5V, XIAO 5V |
| T29 | U4 pad 1 (18.6, 2.9) | CAN_RX, XIAO D0 |

XIAO pads: the castellation lands of the unfitted XIAO; with a XIAO fitted the jig no longer fits (no pocket for it).
