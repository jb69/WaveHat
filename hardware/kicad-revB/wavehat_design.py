"""WaveHat rev B: the one description of parts and nets that the schematic and PCB generators both read.

Edit here, then run:
    python3 -I gen_schematic.py                     (any Python 3)
    <KiCad python> gen_pcb.py                       (needs KiCad's pcbnew module)

Origin of the circuit: the Takuma project's XIAO node (XIAO ESP32-C3 + LSM6DSO at 0x6B + SN65HVD230 on D0/D1).
Pin numbers: LSM6DSO from ST AN5192; LMR51606 from TI SLUSEY1B; XIAO pads from Seeed's OPL KiCad library
(pads 1-14 identical on the C3, C6 and S3 SMD footprints).
Python 3.9 compatible (KiCad bundles 3.9).
"""

BOARD_W = 21.0
BOARD_L = 69.0          # mounting end at y = 0, XIAO USB-C at y = BOARD_L (rev A was 54: rev B adds 8 mm behind the IMU zone
                        # and, 7 Nov 2026, 7 mm at the J2/J6 band for the 10-pin IO header on the left-hand edge)
XIAO_TOP = 48.0         # XIAO body occupies y = XIAO_TOP .. BOARD_L
IMU_ZONE_Y = 8.6        # bow end .. here is the sensor zone: holes, IMU, its decoupling, the pull-ups; no pour crosses it
SHIFT = 8.0             # rev A y positions beyond the sensor zone, moved aft by this much
SHIFT2 = 7.0            # and everything from the fuse aft (rev A y >= 27) a further 7 mm, for J6

# ----------------------------------------------------------------------------- parts
# ref: (lib_id, value, footprint, {pin: net}, sch (x, y), pcb (x, y, rot, side), mpn, dnp)
#   pin net None = no-connect marker. pcb side "F" (top, assembled), "BA" (bottom, assembled: the log
#   storage under the XIAO) or "B" (bottom, bare copper only: jumpers, pads, test points; no assembly).
P = {}


def part(ref, lib_id, value, fp, pins, sch, pcb, mpn="", dnp=False):
    P[ref] = dict(lib_id=lib_id, value=value, fp=fp, pins=pins, sch=sch, pcb=pcb, mpn=mpn, dnp=dnp)


R0402 = "Resistor_SMD:R_0402_1005Metric"
C0402 = "Capacitor_SMD:C_0402_1005Metric"
C0603 = "Capacitor_SMD:C_0603_1608Metric"
C0805 = "Capacitor_SMD:C_0805_2012Metric"

# --- controller
part("U4", "wavehat:XIAO_ESP32_14P", "XIAO ESP32-C3/C6/S3", "wavehat:XIAO_ESP32_14P_SMD",
     {"1": "CAN_RX", "2": "CAN_TX", "3": "LED_R", "4": "LED_B", "5": "SDA", "6": "SCL", "7": "UART_TX",
      "8": "UART_RX", "9": "SD_SCK", "10": "SD_MISO", "11": "SD_MOSI", "12": "3V3", "13": "GND", "14": "XIAO_5V",
      # rev B battery option: carrier pads under the module that reflow to its own BAT pads (1S LiPo charger on the
      # module). 15/16 sit under the C3 and S3 pads (VBAT, GND), 17/18 under the C6 pads; positions from Seeed's footprints.
      "15": "VBAT", "16": "GND", "17": "VBAT", "18": "GND"},
     (280.0, 140.0), (19.4, XIAO_TOP, 180, "F"), mpn="Seeed XIAO ESP32C3 113991054 (or C6 113991254 / S3 113991114)")

# --- IMU
part("U1", "wavehat:LSM6DSO", "LSM6DSO", "Package_LGA:LGA-14_3x2.5mm_P0.5mm_LayoutBorder3x4y",
     {"1": "SA0", "2": "GND", "3": "GND", "4": "IMU_INT1", "5": "3V3", "6": "GND", "7": "GND", "8": "3V3",
      "9": "IMU_INT2", "10": None, "11": None, "12": "3V3", "13": "SCL", "14": "SDA"},
     (130.0, 150.0), (10.5, 3.4, 0, "F"), mpn="LSM6DSOTR")
part("C1", "Device:C", "100nF", C0402, {"1": "3V3", "2": "GND"}, (85.0, 120.0), (7.4, 2.6, 90, "F"), "GRM155R71C104KA88D")
part("C2", "Device:C", "10uF", C0603, {"1": "3V3", "2": "GND"}, (95.0, 120.0), (13.7, 3.4, 90, "F"), "GRM188R61A106KE69D")
part("C3", "Device:C", "100nF", C0402, {"1": "3V3", "2": "GND"}, (105.0, 120.0), (7.4, 4.8, 90, "F"), "GRM155R71C104KA88D")

# --- I2C, address, interrupts, expansion
part("R1", "Device:R", "4.7k", R0402, {"1": "3V3", "2": "SDA_PU"}, (170.0, 115.0), (9.5, 6.6, 0, "F"), "RC0402FR-074K7L")
part("R2", "Device:R", "4.7k", R0402, {"1": "3V3", "2": "SCL_PU"}, (180.0, 115.0), (12.0, 6.6, 0, "F"), "RC0402FR-074K7L")
part("JP1", "Jumper:SolderJumper_2_Bridged", "SDA pull-up", "Jumper:SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm",
     {"1": "SDA", "2": "SDA_PU"}, (170.0, 140.0), (4.0, 22, 0, "B"))
part("JP2", "Jumper:SolderJumper_2_Bridged", "SCL pull-up", "Jumper:SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm",
     {"1": "SCL", "2": "SCL_PU"}, (170.0, 155.0), (4.0, 26.0, 0, "B"))
part("JP3", "Jumper:SolderJumper_3_Bridged12", "I2C addr 0x6B/0x6A", "Jumper:SolderJumper-3_P1.3mm_Bridged12_RoundedPad1.0x1.5mm",
     {"1": "3V3", "2": "SA0", "3": "GND"}, (130.0, 195.0), (10.5, 18.5, 0, "B"))
part("JP4", "Jumper:SolderJumper_2_Open", "INT1 to D2", "Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm",
     {"1": "IMU_INT1", "2": "LED_R"}, (200.0, 170.0), (17.0, 22, 0, "B"))
part("JP5", "Jumper:SolderJumper_2_Open", "INT2 to D3", "Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm",
     {"1": "IMU_INT2", "2": "LED_B"}, (200.0, 185.0), (17.0, 26.0, 0, "B"))
# J2 moved aft of J6 on 7 Nov 2026 (J6 takes the edge from the sensor zone to y 26)
part("J2", "Connector_Generic:Conn_01x04", "Qwiic", "Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal",
     {"1": "GND", "2": "3V3", "3": "SDA", "4": "SCL"}, (60.0, 175.0), (3.33, 30.2, 270, "F"), "SM04B-SRSS-TB(LF)(SN)")
part("TP1", "Connector:TestPoint", "LED_R (D2)", "TestPoint:TestPoint_Pad_D1.5mm", {"1": "LED_R"}, (230.0, 170.0), (7.0, 27.4, 0, "B"))
part("TP2", "Connector:TestPoint", "LED_B (D3)", "TestPoint:TestPoint_Pad_D1.5mm", {"1": "LED_B"}, (230.0, 185.0), (10.5, 27.4, 0, "B"))

# --- GNSS port (rev B): the drone-standard 6-pin JST-GH, pinned as Pixhawk's GPS port so a u-blox M8N/M10
# GPS-and-compass module plugs in with its own cable: 1 5V, 2 TX (out of the XIAO, D6), 3 RX (into the XIAO, D7),
# 4 SCL, 5 SDA, 6 GND. Not fitted at the factory (DNP): hand-solder it where a GNSS is wanted. The compass shares
# the I2C bus with the IMU and J2. On the right-hand edge aft of J3 (same GH family), opening flush with the edge
# so the plug slides in from outside the board; J3 moved forward to just behind the sensor zone, by the transceiver.
part("J5", "Connector_Generic:Conn_01x06", "GNSS (Pixhawk GPS port)", "Connector_JST:JST_GH_SM06B-GHS-TB_1x06-1MP_P1.25mm_Horizontal",
     {"1": "XIAO_5V", "2": "UART_TX", "3": "UART_RX", "4": "SCL", "5": "SDA", "6": "GND"},
     (330.0, 150.0), (17.75, 24.6, 90, "F"), mpn="SM06B-GHS-TB(LF)(SN)", dnp=True)

# --- CAN
part("U3", "Interface_CAN_LIN:SN65HVD230", "SN65HVD230", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
# U3 hangs off three bridged jumpers (7 Nov 2026): JP8 its 3V3, JP9 its RXD, JP10 its TXD. Cut all three for a build with
# no CAN: the transceiver is then unpowered and off D0/D1 (so nothing back-feeds through its ESD diodes when J6 drives
# those pins), and D0/D1 are free on the IO header. C7 stays on the U3 side of JP8.
     {"1": "CAN_TXD", "2": "GND", "3": "3V3_CAN", "4": "CAN_RXD", "5": None, "6": "CANL", "7": "CANH", "8": "RS"},
     (300.0, 225.0), (10.5, 21.25, 90, "F"), "SN65HVD230DR")
part("C7", "Device:C", "100nF", C0402, {"1": "3V3_CAN", "2": "GND"}, (270.0, 205.0), (8.5, 25.9, 0, "F"), "GRM155R71C104KA88D")
part("JP8", "Jumper:SolderJumper_2_Bridged", "U3 3V3", "Jumper:SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm",
     {"1": "3V3", "2": "3V3_CAN"}, (255.0, 210.0), (7.2, 21.4, 90, "B"))
part("JP9", "Jumper:SolderJumper_2_Bridged", "U3 RXD to D0", "Jumper:SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm",
     {"1": "CAN_RX", "2": "CAN_RXD"}, (255.0, 225.0), (13.8, 21.4, 90, "B"))
part("JP10", "Jumper:SolderJumper_2_Bridged", "U3 TXD to D1", "Jumper:SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm",
     {"1": "CAN_TX", "2": "CAN_TXD"}, (255.0, 240.0), (13.8, 25.0, 90, "B"))
part("R5", "Device:R", "120", R0402, {"1": "CANH", "2": "TERM"}, (340.0, 205.0), (13.4, 25.9, 0, "F"), "RC0402FR-07120RL")
part("JP6", "Jumper:SolderJumper_2_Open", "CAN termination", "Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm",
     {"1": "TERM", "2": "CANL"}, (340.0, 240.0), (10.5, 22.5, 0, "B"))
part("R6", "Device:R", "10k", R0402, {"1": "RS", "2": "GND"}, (270.0, 245.0), (11.0, 25.9, 0, "F"), "RC0402FR-0710KL")
part("J3", "Connector_Generic:Conn_01x04", "VESC CAN", "Connector_JST:JST_GH_SM04B-GHS-TB_1x04-1MP_P1.25mm_Horizontal",
     {"1": "GND", "2": "CANL", "3": "CANH", "4": "5V_CAN"}, (380.0, 225.0), (17.75, 13.5, 90, "F"), "SM04B-GHS-TB(LF)(SN)")
part("J4", "Connector_Generic:Conn_01x05", "NMEA 2000 pads", "wavehat:N2K_Pads_1x05_P3.0mm",
     {"1": None, "2": "VIN_RAW", "3": "GND", "4": "CANH", "5": "CANL"}, (380.0, 260.0), (10.5, 41.0, 0, "B"))

# --- IO header (rev B, 7 Nov 2026): a 10-pin JST-GH that brings out the pins a build may not use on board, so leads for
# LEDs, a remote's UART, an ESC telemetry line or a mast sensor plug in instead of being soldered to the XIAO. 1 5V,
# 2 3V3, 3 GND, 4 D2 (LED_R / TP1), 5 D3 (LED_B; NAND CS when JP7 is bridged), 6 D6 (UART TX, shared with J5),
# 7 D7 (UART RX), 8 D0 and 9 D1 (CAN RX/TX: free once JP8-JP10 are cut and JP6 is open), 10 GND. Left-hand edge,
# forward of J2, opening flush with the edge like the other connectors. Fitted at the factory (JLCPCB C2683602).
part("J6", "Connector_Generic:Conn_01x10", "IO header", "Connector_JST:JST_GH_SM10B-GHS-TB_1x10-1MP_P1.25mm_Horizontal",
     {"1": "XIAO_5V", "2": "3V3", "3": "GND", "4": "LED_R", "5": "LED_B", "6": "UART_TX", "7": "UART_RX",
      "8": "CAN_RX", "9": "CAN_TX", "10": "GND"},
     (405.0, 175.0), (3.25, 17.5, 270, "F"), mpn="SM10B-GHS-TB(LF)(SN)")

# --- battery (rev B, 7 Nov 2026): two 2.54 mm through-holes for a 1S LiPo pigtail (or a 2-pin header), on the XIAO's
# own VBAT/GND through the carrier pads under the module (U4 pads 15-18). Pin 1 is +. Nothing to assemble: DNP.
part("J7", "Connector_Generic:Conn_01x02", "BAT 1S LiPo (+ pin 1)", "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
     {"1": "VBAT", "2": "GND"}, (245.0, 150.0), (9.23, 14.5, 90, "F"), dnp=True)

# --- power
# Supply lead (no NMEA 2000): solder to J4 pads 2 (NET-S, +) and 3 (NET-C, GND). Input range 5-30 V: 12 V and 24 V
# systems and NMEA 2000; 5 V works too (the buck runs at full duty and about 4.3 V reaches the XIAO's 5V pin).
part("F1", "Device:Polyfuse", "0.5A 60V", "Fuse:Fuse_1812_4532Metric", {"1": "VIN_RAW", "2": "VIN_FUSED"},
     (60.0, 45.0), (3.3, 36.4, 0, "F"), "1812L050/60MR")
# SS14 (40 V, 1 A), the same part as D2/D3: F1 holds the input to about 0.5 A
part("D1", "Device:D_Schottky", "SS14", "Diode_SMD:D_SMA", {"1": "VIN", "2": "VIN_FUSED"},
     (85.0, 45.0), (10.4, 36.4, 0, "F"), "SS14")
# SMBJ30A: 30 V standoff (the top of the input range), 48.4 V clamp at its full 600 W pulse, under the LMR51606's
# 70 V absolute maximum and C4's 100 V rating.
part("TVS1", "Device:D_Zener", "SMBJ30A", "Diode_SMD:D_SMB", {"1": "VIN", "2": "GND"},
     (110.0, 60.0), (4.0, 41.1, 0, "F"), "SMBJ30A")
part("C4", "Device:C", "2.2uF 100V", "Capacitor_SMD:C_1206_3216Metric", {"1": "VIN", "2": "GND"}, (125.0, 60.0), (9.0, 41.1, 90, "F"),
     "GRM31CR72A225KA73L")
# LMR51606Y: 4-65 V (70 V absolute), 0.6 A, 1.1 MHz, PFM; pin-for-pin with the TPS560430 (TI SLUSEY1B). 0.8 V reference.
part("U2", "wavehat:LMR51606", "LMR51606Y", "Package_TO_SOT_SMD:SOT-23-6",
     {"1": "CB", "2": "GND", "3": "FB", "4": "VIN", "5": "VIN", "6": "SW"},
     (160.0, 55.0), (12.6, 41.1, 0, "F"), "LMR51606YDBVR")
# bootstrap: TI asks for 100 nF rated 16 V or more (it sees about 5 V); the same part as C1/C3/C7/C8
part("C6", "Device:C", "100nF", C0402, {"1": "CB", "2": "SW"}, (180.0, 35.0), (14.2, 38.9, 0, "F"), "GRM155R71C104KA88D")
# 15 uH: TI's minimum for 0.6 A at 30 V in and 1.1 MHz is 15.8 uH at 40 % ripple (SLUSEY1B eq. 9), so 42 % here.
# Changjiang FNR4020S150MT (LCSC C167837): 4 x 4 x 2 mm shielded, Isat 1.5 A (above the 0.8-1.4 A current limit,
# as TI's design example asks), rated 1.1 A, DCR 0.3 ohm.
part("L1", "Device:L", "15uH", "Inductor_SMD:L_Changjiang_FNR4020S", {"1": "SW", "2": "5V_BUCK"},
     (200.0, 45.0), (17.7, 42.0, 0, "F"), "FNR4020S150MT")
# 120k / 22.1k with the 0.8 V reference: 5.14 V (TI's table has 118k for 5.07 V; 120k is the stocked standard value)
part("R3", "Device:R", "120k", R0402, {"1": "5V_BUCK", "2": "FB"}, (220.0, 60.0), (16.3, 38.9, 0, "F"), "RC0402FR-07120KL")
part("R4", "Device:R", "22.1k", R0402, {"1": "FB", "2": "GND"}, (220.0, 80.0), (18.5, 38.9, 0, "F"), "RC0402FR-0722K1L")
part("C5", "Device:C", "22uF 10V", C0805, {"1": "5V_BUCK", "2": "GND"}, (240.0, 60.0), (18.6, 45.4, 0, "F"), "GRM21BR61A226ME51L")
part("D2", "Device:D_Schottky", "SS14", "Diode_SMD:D_SMA", {"1": "XIAO_5V", "2": "5V_BUCK"},
     (260.0, 45.0), (4.4, 45.6, 0, "F"), "SS14")
part("D3", "Device:D_Schottky", "SS14", "Diode_SMD:D_SMA", {"1": "XIAO_5V", "2": "5V_CAN"},
     (260.0, 75.0), (11.9, 45.6, 0, "F"), "SS14")

# --- log storage: SD NAND (an SD card in a soldered LGA-8) on the XIAO's SPI pins, bottom side under the XIAO.
# SPI mode: D8 = SCK, D9 = MISO, D10 = MOSI, D3 = /CS through JP7 (cut JP7 to free D3; R9 then keeps the
# chip deselected). VESC Express mounts it like a card: (f-connect 10 9 8 5) on the C3 (MOSI MISO SCK CS GPIOs).
# The 10k pull-ups are the SD spec's on CMD/DAT, and hold the C3's strapping pins GPIO8 (D8) and GPIO9 (D9)
# high at reset. Zetta ZDSD02GLGEAG (LCSC C2875853, 2 Gbit = 256 MB, SLC). The land pattern also takes 4 Gbit parts
# (MK MKDV4GCL-ABB, CS-Creative CSNP4GCR01) and XTX XTSD (same pinout, LGA-8 6 x 8 mm).
part("U5", "wavehat:SD_NAND", "SD NAND 2Gb (256 MB)", "wavehat:SD_NAND_LGA-8_8x6mm_P1.27mm",
     {"1": None, "2": "SD_CS", "3": "SD_SCK", "4": "GND", "5": "SD_MOSI", "6": "SD_MISO", "7": None, "8": "3V3"},
     (215.0, 252.0), (10.5, 54.5, 0, "BA"), "ZDSD02GLGEAG")
part("C8", "Device:C", "100nF", C0402, {"1": "3V3", "2": "GND"}, (160.0, 268.0), (5.6, 52.4, 90, "BA"), "GRM155R71C104KA88D")
part("C9", "Device:C", "10uF", C0603, {"1": "3V3", "2": "GND"}, (172.0, 268.0), (4.2, 52.4, 90, "BA"), "GRM188R61A106KE69D")
part("R9", "Device:R", "10k", R0402, {"1": "3V3", "2": "SD_CS"}, (150.0, 232.0), (3.0, 59.6, 90, "BA"), "RC0402FR-0710KL")
part("R10", "Device:R", "10k", R0402, {"1": "3V3", "2": "SD_SCK"}, (162.0, 232.0), (4.3, 59.6, 90, "BA"), "RC0402FR-0710KL")
part("R11", "Device:R", "10k", R0402, {"1": "3V3", "2": "SD_MISO"}, (174.0, 232.0), (5.6, 59.6, 90, "BA"), "RC0402FR-0710KL")
part("R12", "Device:R", "10k", R0402, {"1": "3V3", "2": "SD_MOSI"}, (186.0, 232.0), (6.9, 59.6, 90, "BA"), "RC0402FR-0710KL")
part("JP7", "Jumper:SolderJumper_2_Bridged", "SD CS on D3", "Jumper:SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm",
     {"1": "LED_B", "2": "SD_CS"}, (190.0, 272.0), (16.6, 55.0, 0, "B"))

# --- test pads (rev B): one 1.0 mm pad on the bottom for every net that crosses between layers, plus GND, on a
# 2.54 mm grid in four rows (sensor/I2C, CAN, power, storage) so the rev A test plate becomes a pogo-pin bed.
# With TP1/TP2 (LED_R, LED_B) these let a bare board be checked for open vias from one side, and let the power
# stage be run from a bench supply (TP22 5V_BUCK, TP23 XIAO_5V, TP8 3V3) before a XIAO is soldered on.
TEST_PADS = [
    # row 1, behind the sensor zone (y 10.2): the I2C bus, its pull-ups, the IMU address and 3V3
    ("SDA", 4.0, 10.2), ("SCL", 6.54, 10.2), ("SDA_PU", 9.08, 10.2), ("SCL_PU", 11.62, 10.2), ("SA0", 14.16, 10.2), ("3V3", 16.7, 10.2),
    # row 2 (y 12.74): the IMU interrupts, GND, the GNSS UART
    ("IMU_INT1", 4.0, 12.74), ("IMU_INT2", 6.54, 12.74), ("GND", 9.08, 12.74), ("UART_TX", 11.62, 12.74), ("UART_RX", 14.16, 12.74),
    # row 3, between the CAN parts and the J4 pads (y 37.2): the CAN side
    ("CANH", 4.0, 37.2), ("CANL", 6.54, 37.2), ("CAN_TX", 9.08, 37.2), ("CAN_RX", 11.62, 37.2), ("TERM", 14.16, 37.2), ("5V_CAN", 16.7, 37.2),
    # row 4, under the power stage (y 47.6): the supply chain from the J4 pad to the XIAO
    ("VIN_RAW", 4.0, 47.6), ("VIN", 6.54, 47.6), ("5V_BUCK", 9.08, 47.6), ("XIAO_5V", 11.62, 47.6), ("CB", 14.16, 47.6), ("GND", 16.7, 47.6),
    # row 5, behind the SD NAND under the XIAO (y 64.0): the storage island and its SPI lines
    ("3V3", 4.0, 64.0), ("SD_CS", 6.54, 64.0), ("SD_SCK", 9.08, 64.0), ("SD_MISO", 11.62, 64.0), ("SD_MOSI", 14.16, 64.0),
]
for _i, (_net, _x, _y) in enumerate(TEST_PADS):
    part("TP%d" % (_i + 3), "Connector:TestPoint", _net, "TestPoint:TestPoint_Pad_D1.0mm", {"1": _net},
         (300.0 + 14.0 * (_i % 7), 42.0 + 16.0 * (_i // 7)), (_x, _y, 0, "B"))

# --- mechanical
part("H1", "Mechanical:MountingHole_Pad", "M2", "MountingHole:MountingHole_2.2mm_M2_Pad", {"1": "GND"}, (30.0, 260.0), (2.7, 2.7, 0, "F"))
part("H2", "Mechanical:MountingHole_Pad", "M2", "MountingHole:MountingHole_2.2mm_M2_Pad", {"1": "GND"}, (45.0, 260.0), (18.3, 2.7, 0, "F"))
part("FID1", "Mechanical:Fiducial", "Fiducial", "Fiducial:Fiducial_1mm_Mask2mm", {}, (65.0, 260.0), (5.0, 7.0, 0, "F"))
part("FID2", "Mechanical:Fiducial", "Fiducial", "Fiducial:Fiducial_1mm_Mask2mm", {}, (80.0, 260.0), (18.6, 7.0, 0, "F"))
part("FID3", "Mechanical:Fiducial", "Fiducial", "Fiducial:Fiducial_1mm_Mask2mm", {}, (95.0, 260.0), (17.5, 33.5, 0, "F"))   # rev B: the free top-side patch between J5 and the buck; the XIAO covers the stern
part("FID4", "Mechanical:Fiducial", "Fiducial", "Fiducial:Fiducial_1mm_Mask2mm", {}, (110.0, 260.0), (2.2, 49.4, 0, "BA"))
part("FID5", "Mechanical:Fiducial", "Fiducial", "Fiducial:Fiducial_1mm_Mask2mm", {}, (125.0, 260.0), (18.8, 62.6, 0, "BA"))

# nets that need a power flag for ERC (driven only through passive parts)
PWR_FLAGS = {"GND": (30.0, 285.0), "VIN": (50.0, 285.0), "XIAO_5V": (70.0, 285.0), "3V3_CAN": (90.0, 285.0)}

# net classes for routing
POWER_NETS = {"VIN_RAW", "VIN_FUSED", "VIN", "SW", "5V_BUCK", "XIAO_5V", "5V_CAN", "VBAT"}   # GND is the pours
SUPPLY_NETS = {"3V3", "3V3_CAN"}   # rev B: 0.3 mm (rev A ran the IMU, transceiver and NAND off 0.15 mm); 0.4 will not enter the LGA-14 pads

SECTIONS = [  # schematic text labels (x, y, text)
    (25.0, 25.0, "Power: NMEA 2000 NET-S or a 5-30 V lead on the J4 pads -> fuse -> reverse diode -> TVS -> LMR51606 buck 5 V -> diode-OR into the XIAO 5V pin"),
    (60.0, 100.0, "IMU: LSM6DSO on I2C, address 0x6B by default (JP3), as on the Takuma node"),
    (240.0, 100.0, "Controller: Seeed XIAO ESP32-C3 / C6 / S3 (pads 1-14 are common to all three)"),
    (318.0, 138.0, "GNSS: 6-pin JST-GH, Pixhawk GPS pinout, UART on D6/D7 + the I2C bus. DNP: fit by hand where wanted"),
    (292.0, 32.0, "Test pads (rev B): one per layer-crossing net, bottom side, 2.54 mm grid"),
    (240.0, 192.0, "CAN: SN65HVD230 on D0 (RX) / D1 (TX), the VESC Express pins. J3 VESC, J4 NMEA 2000. JP6 termination open. JP8/9/10 bridged: cut all three for a build with no CAN"),
    (395.0, 162.0, "IO header J6: 10-pin JST-GH, the spare pins on a lead (D0/D1 free once JP8-10 are cut)"),
    (232.0, 160.0, "BAT: 1S LiPo to the XIAO's own charger (carrier pads under the module)"),
    (140.0, 218.0, "Log storage: SD NAND on SPI, under the XIAO"),
    (25.0, 250.0, "Mechanical: M2 holes at the bow end"),
]
