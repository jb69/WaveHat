# Vias in rev A (as ordered 20 Oct 2026)

**Found open so far (29–30 Oct 2026):** board 2, 3V3 at (4.25, 7.50) and LED_B at (16.20, 11.74), both bodged with wire (the NAND then mounts; bring-up notes in the eFoil workspace, `designs/ranges/takuma/firmware/wavehat_c6/README.md`). Board 2's CAN fault turned out to be the JST-GH lead, not the board. Check every bare board with the table below before fitting a XIAO.

104 vias, all through-hole F.Cu to B.Cu, tented both sides: 95 at 0.6 mm pad / 0.3 mm drill (signals, 3V3, GND stitching) and 9 at 0.8 mm pad / 0.4 mm drill (VIN, 5 V rails). Drill file `fab/wavehat-gerbers.zip: wavehat.drl` declares them `Plated,PTH,ViaDrill`. JLCPCB order spec: 1 oz, tented, min via 0.3 mm/(0.4/0.45 mm), via plating method *Not specified*. The design is inside the spec with margin (0.15 mm annular ring against a 0.075 mm minimum; aspect ratio 5.3:1 on 1.6 mm).

56 vias are GND stitching: an open one of those costs nothing electrically. The 48 below carry signals or power; an open one breaks a net. Coordinates are mm from the board's lower-left corner, component side up, the same origin as the Gerbers and the pick-and-place files. To check a board without the XIAO fitted, measure continuity between the via's two ends with the mask scraped, or more simply between the two parts the net joins (the schematic PDF).

| Net | x | y | pad/drill | Net | x | y | pad/drill |
|---|---|---|---|---|---|---|---|
| 3V3 | 4.25 | 7.50 | 0.6/0.3 | IMU_INT2 | 12.46 | 50.25 | 0.6/0.3 |
| 3V3 | 13.18 | 43.44 | 0.6/0.3 | LED_B | 16.20 | 11.74 | 0.6/0.3 |
| 5V_BUCK | 7.83 | 24.83 | 0.8/0.4 | LED_R | 16.59 | 6.57 | 0.6/0.3 |
| 5V_BUCK | 15.78 | 22.83 | 0.8/0.4 | SA0 | 11.96 | 52.45 | 0.6/0.3 |
| 5V_CAN | 14.61 | 41.44 | 0.8/0.4 | SA0 | 15.91 | 43.79 | 0.6/0.3 |
| 5V_CAN | 14.66 | 25.22 | 0.8/0.4 | SA0 | 16.27 | 49.01 | 0.6/0.3 |
| CANH | 7.61 | 29.90 | 0.6/0.3 | SCL | 5.33 | 37.96 | 0.6/0.3 |
| CANH | 9.11 | 31.21 | 0.6/0.3 | SCL | 11.00 | 52.46 | 0.6/0.3 |
| CANH | 12.97 | 35.15 | 0.6/0.3 | SCL | 17.75 | 24.01 | 0.6/0.3 |
| CANL | 6.67 | 30.02 | 0.6/0.3 | SCL_PU | 12.51 | 48.22 | 0.6/0.3 |
| CANL | 6.67 | 32.36 | 0.6/0.3 | SDA | 3.94 | 26.09 | 0.6/0.3 |
| CANL | 11.56 | 41.11 | 0.6/0.3 | SDA | 4.16 | 38.71 | 0.6/0.3 |
| CANL | 14.39 | 39.50 | 0.6/0.3 | SDA | 9.43 | 52.08 | 0.6/0.3 |
| CAN_RX | 12.20 | 35.02 | 0.6/0.3 | SDA | 16.65 | 22.65 | 0.6/0.3 |
| CAN_RX | 13.11 | 25.53 | 0.6/0.3 | SDA_PU | 9.50 | 46.49 | 0.6/0.3 |
| CAN_TX | 3.39 | 35.49 | 0.6/0.3 | SD_MISO | 4.52 | 11.19 | 0.6/0.3 |
| CAN_TX | 4.27 | 14.87 | 0.6/0.3 | SD_MOSI | 4.77 | 8.16 | 0.6/0.3 |
| CAN_TX | 8.64 | 39.73 | 0.6/0.3 | SD_SCK | 4.25 | 13.73 | 0.6/0.3 |
| CAN_TX | 15.17 | 15.43 | 0.6/0.3 | TERM | 13.91 | 37.22 | 0.6/0.3 |
| CB | 11.46 | 30.84 | 0.6/0.3 | VIN | 1.85 | 26.17 | 0.8/0.4 |
| CB | 14.90 | 30.29 | 0.6/0.3 | VIN | 9.38 | 25.23 | 0.8/0.4 |
| IMU_INT1 | 8.46 | 48.17 | 0.6/0.3 | VIN_RAW | 1.16 | 30.33 | 0.8/0.4 |
| IMU_INT1 | 12.94 | 46.46 | 0.6/0.3 | XIAO_5V | 2.40 | 21.91 | 0.8/0.4 |
| IMU_INT1 | 17.65 | 41.23 | 0.6/0.3 | XIAO_5V | 9.90 | 21.87 | 0.8/0.4 |

Nets with a single via (SDA_PU, SCL_PU, IMU_INT2, VIN_RAW, TERM, LED_R, LED_B, SD_SCK, SD_MISO, SD_MOSI) have no redundancy; SD_SCK/MISO/MOSI opens would show as the log storage not mounting, VIN_RAW as no power from J4, TERM as the 120 Ω termination missing even with JP6 bridged.

Repair of an open via: scrape the mask off both ends, push a strand of 0.25 mm wire (or a component lead offcut) through the hole, solder both sides, trim. The 0.3 mm drill takes 0.25 mm wire; the 0.4 mm ones take 0.3 mm.

## Continuity checklist for a bare board (no XIAO fitted)

A 3D-printed jig with a numbered hole over each of these probe points is in `../../test-plate/` (its `legend.md` is the same list, numbered by hole).

One meter reading per net, 0 Ω expected, between two pads the vias sit between. U4 is the XIAO footprint: probe its castellation pad on the top side. Where both probes are on the top, the copper path still goes through the vias listed. A net with one via has no spare: a fail there is that via.

| Net | Vias | Probe A | Probe B | Via positions (x, y mm) |
|---|---|---|---|---|
| 3V3 (to the NAND island) | 1 of 2 | U4 pin 12 (top) | C9 pin 1 or R10 pin 1 (bottom) | (4.25, 7.50) |
| 3V3 (to JP3) | 1 of 2 | U4 pin 12 (top) | JP3 pin 1 (bottom) | (13.18, 43.44) |
| 5V_BUCK | 2 | R3 pin 1 (top) | C5 pin 1 (top) | (7.83, 24.83), (15.78, 22.83) |
| 5V_CAN | 2 | J3 pin 4 (top) | D3 pin 2 (top) | (14.61, 41.44), (14.66, 25.22) |
| CANH | 3 | J3 pin 3 (top) | J4 pin 4 (bottom) | (7.61, 29.90), (9.11, 31.21), (12.97, 35.15) |
| CANL | 4 | J3 pin 2 (top) | JP6 pin 2 (bottom) | (6.67, 30.02), (6.67, 32.36), (11.56, 41.11), (14.39, 39.50) |
| CAN_RX | 2 | U4 pin 1 (top) | U3 pin 4 (top) | (12.20, 35.02), (13.11, 25.53) |
| CAN_TX | 4 | U4 pin 2 (top) | U3 pin 1 (top) | (3.39, 35.49), (4.27, 14.87), (8.64, 39.73), (15.17, 15.43) |
| CB | 2 | C6 pin 1 (top) | U2 pin 1 (top) | (11.46, 30.84), (14.90, 30.29) |
| IMU_INT1 | 3 | U1 pin 4 (top) | JP4 pin 1 (bottom) | (8.46, 48.17), (12.94, 46.46), (17.65, 41.23) |
| IMU_INT2 | 1 | U1 pin 9 (top) | JP5 pin 1 (bottom) | (12.46, 50.25) |
| LED_B (D3, NAND CS) | 1 | U4 pin 4 (top) | JP7 pin 1 or R9 pin 2 (bottom) | (16.20, 11.74) |
| LED_R | 1 | U4 pin 3 (top) | JP4 pin 2 (bottom) | (16.59, 6.57) |
| SA0 | 3 | U1 pin 1 (top) | JP3 pin 2 (bottom) | (11.96, 52.45), (15.91, 43.79), (16.27, 49.01) |
| SCL | 3 | U4 pin 6 (top) | JP2 pin 1 (bottom) | (5.33, 37.96), (11.00, 52.46), (17.75, 24.01) |
| SCL_PU | 1 | R2 pin 2 (top) | JP2 pin 2 (bottom) | (12.51, 48.22) |
| SDA | 4 | U4 pin 5 (top) | JP1 pin 1 (bottom) | (3.94, 26.09), (4.16, 38.71), (9.43, 52.08), (16.65, 22.65) |
| SDA_PU | 1 | R1 pin 2 (top) | JP1 pin 2 (bottom) | (9.50, 46.49) |
| SD_MISO (D9) | 1 | U4 pin 10 (top) | R11 pin 2 (bottom) | (4.52, 11.19) |
| SD_MOSI (D10) | 1 | U4 pin 11 (top) | R12 pin 2 (bottom) | (4.77, 8.16) |
| SD_SCK (D8) | 1 | U4 pin 9 (top) | R10 pin 2 (bottom) | (4.25, 13.73) |
| TERM | 1 | R5 pin 2 (top) | JP6 pin 1 (bottom) | (13.91, 37.22) |
| VIN | 2 | C4 pin 1 (top) | D1 pin 1 (top) | (1.85, 26.17), (9.38, 25.23) |
| VIN_RAW | 1 | F1 pin 1 (top) | J4 pin 2 (bottom) | (1.16, 30.33) |
| XIAO_5V | 2 | U4 pin 14 (top) | D3 pin 1 (top) | (2.40, 21.91), (9.90, 21.87) |

Nets with several vias in series (CAN_TX, SDA, SCL, CANL) fail if any one of them is open; a fail there needs the individual vias probed, mask scraped, to find which. The 56 GND vias are not listed: the pours carry GND without them.
