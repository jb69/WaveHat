"""WaveHat rev A: the one description of parts and nets that the schematic and PCB generators both read.

Edit here, then run:
    python3 -I gen_schematic.py                     (any Python 3)
    <KiCad python> gen_pcb.py                       (needs KiCad's pcbnew module)

Origin of the circuit: the Takuma project's XIAO node (XIAO ESP32-C3 + LSM6DSO at 0x6B + SN65HVD230 on D0/D1).
Pin numbers: LSM6DSO from ST AN5192; LMR51606 from TI SLUSEY1B; XIAO pads from Seeed's OPL KiCad library
(pads 1-14 identical on the C3, C6 and S3 SMD footprints).
Python 3.9 compatible (KiCad bundles 3.9).
"""

BOARD_W = 21.0
BOARD_L = 54.0          # mounting end at y = 0, XIAO USB-C at y = BOARD_L
XIAO_TOP = 33.0         # XIAO body occupies y = XIAO_TOP .. BOARD_L

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
     {"1": "CAN_RX", "2": "CAN_TX", "3": "LED_R", "4": "LED_B", "5": "SDA", "6": "SCL", "7": None,
      "8": None, "9": "SD_SCK", "10": "SD_MISO", "11": "SD_MOSI", "12": "3V3", "13": "GND", "14": "XIAO_5V"},
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
     {"1": "SDA", "2": "SDA_PU"}, (170.0, 140.0), (4.0, 14.0, 0, "B"))
part("JP2", "Jumper:SolderJumper_2_Bridged", "SCL pull-up", "Jumper:SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm",
     {"1": "SCL", "2": "SCL_PU"}, (170.0, 155.0), (4.0, 17.0, 0, "B"))
part("JP3", "Jumper:SolderJumper_3_Bridged12", "I2C addr 0x6B/0x6A", "Jumper:SolderJumper-3_P1.3mm_Bridged12_RoundedPad1.0x1.5mm",
     {"1": "3V3", "2": "SA0", "3": "GND"}, (130.0, 195.0), (10.5, 11.0, 0, "B"))
part("JP4", "Jumper:SolderJumper_2_Open", "INT1 to D2", "Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm",
     {"1": "IMU_INT1", "2": "LED_R"}, (200.0, 170.0), (17.0, 14.0, 0, "B"))
part("JP5", "Jumper:SolderJumper_2_Open", "INT2 to D3", "Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm",
     {"1": "IMU_INT2", "2": "LED_B"}, (200.0, 185.0), (17.0, 17.0, 0, "B"))
part("J2", "Connector_Generic:Conn_01x04", "Qwiic", "Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal",
     {"1": "GND", "2": "3V3", "3": "SDA", "4": "SCL"}, (60.0, 175.0), (3.33, 12.95, 270, "F"), "SM04B-SRSS-TB(LF)(SN)")
part("TP1", "Connector:TestPoint", "LED_R (D2)", "TestPoint:TestPoint_Pad_D1.5mm", {"1": "LED_R"}, (230.0, 170.0), (7.0, 18.2, 0, "B"))
part("TP2", "Connector:TestPoint", "LED_B (D3)", "TestPoint:TestPoint_Pad_D1.5mm", {"1": "LED_B"}, (230.0, 185.0), (10.5, 18.2, 0, "B"))

# --- CAN
part("U3", "Interface_CAN_LIN:SN65HVD230", "SN65HVD230", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
     {"1": "CAN_TX", "2": "GND", "3": "3V3", "4": "CAN_RX", "5": None, "6": "CANL", "7": "CANH", "8": "RS"},
     (300.0, 225.0), (10.5, 13.25, 90, "F"), "SN65HVD230DR")
part("C7", "Device:C", "100nF", C0402, {"1": "3V3", "2": "GND"}, (270.0, 205.0), (8.5, 17.9, 0, "F"), "GRM155R71C104KA88D")
part("R5", "Device:R", "120", R0402, {"1": "CANH", "2": "TERM"}, (340.0, 205.0), (13.4, 17.9, 0, "F"), "RC0402FR-07120RL")
part("JP6", "Jumper:SolderJumper_2_Open", "CAN termination", "Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm",
     {"1": "TERM", "2": "CANL"}, (340.0, 240.0), (10.5, 14.5, 0, "B"))
part("R6", "Device:R", "10k", R0402, {"1": "RS", "2": "GND"}, (270.0, 245.0), (11.0, 17.9, 0, "F"), "RC0402FR-0710KL")
part("J3", "Connector_Generic:Conn_01x04", "VESC CAN", "Connector_JST:JST_GH_SM04B-GHS-TB_1x04-1MP_P1.25mm_Horizontal",
     {"1": "GND", "2": "CANL", "3": "CANH", "4": "5V_CAN"}, (380.0, 225.0), (17.75, 13.8, 90, "F"), "SM04B-GHS-TB(LF)(SN)")
part("J4", "Connector_Generic:Conn_01x05", "NMEA 2000 pads", "wavehat:N2K_Pads_1x05_P3.0mm",
     {"1": None, "2": "VIN_RAW", "3": "GND", "4": "CANH", "5": "CANL"}, (380.0, 260.0), (10.5, 26.0, 0, "B"))

# --- power
# Supply lead (no NMEA 2000): solder to J4 pads 2 (NET-S, +) and 3 (NET-C, GND). Input range 5-30 V: 12 V and 24 V
# systems and NMEA 2000; 5 V works too (the buck runs at full duty and about 4.3 V reaches the XIAO's 5V pin).
part("F1", "Device:Polyfuse", "0.5A 60V", "Fuse:Fuse_1812_4532Metric", {"1": "VIN_RAW", "2": "VIN_FUSED"},
     (60.0, 45.0), (3.3, 21.4, 0, "F"), "1812L050/60MR")
# SS14 (40 V, 1 A), the same part as D2/D3: F1 holds the input to about 0.5 A
part("D1", "Device:D_Schottky", "SS14", "Diode_SMD:D_SMA", {"1": "VIN", "2": "VIN_FUSED"},
     (85.0, 45.0), (10.4, 21.4, 0, "F"), "SS14")
# SMBJ30A: 30 V standoff (the top of the input range), 48.4 V clamp at its full 600 W pulse, under the LMR51606's
# 70 V absolute maximum and C4's 100 V rating.
part("TVS1", "Device:D_Zener", "SMBJ30A", "Diode_SMD:D_SMB", {"1": "VIN", "2": "GND"},
     (110.0, 60.0), (4.0, 26.1, 0, "F"), "SMBJ30A")
part("C4", "Device:C", "2.2uF 100V", "Capacitor_SMD:C_1206_3216Metric", {"1": "VIN", "2": "GND"}, (125.0, 60.0), (9.0, 26.1, 90, "F"),
     "GRM31CR72A225KA73L")
# LMR51606Y: 4-65 V (70 V absolute), 0.6 A, 1.1 MHz, PFM; pin-for-pin with the TPS560430 (TI SLUSEY1B). 0.8 V reference.
part("U2", "wavehat:LMR51606", "LMR51606Y", "Package_TO_SOT_SMD:SOT-23-6",
     {"1": "CB", "2": "GND", "3": "FB", "4": "VIN", "5": "VIN", "6": "SW"},
     (160.0, 55.0), (12.6, 26.1, 0, "F"), "LMR51606YDBVR")
# bootstrap: TI asks for 100 nF rated 16 V or more (it sees about 5 V); the same part as C1/C3/C7/C8
part("C6", "Device:C", "100nF", C0402, {"1": "CB", "2": "SW"}, (180.0, 35.0), (14.9, 21.4, 90, "F"), "GRM155R71C104KA88D")
# 15 uH: TI's minimum for 0.6 A at 30 V in and 1.1 MHz is 15.8 uH at 40 % ripple (SLUSEY1B eq. 9), so 42 % here.
# Changjiang FNR4020S150MT (LCSC C167837): 4 x 4 x 2 mm shielded, Isat 1.5 A (above the 0.8-1.4 A current limit,
# as TI's design example asks), rated 1.1 A, DCR 0.3 ohm.
part("L1", "Device:L", "15uH", "Inductor_SMD:L_Changjiang_FNR4020S", {"1": "SW", "2": "5V_BUCK"},
     (200.0, 45.0), (17.7, 26.1, 0, "F"), "FNR4020S150MT")
# 120k / 22.1k with the 0.8 V reference: 5.14 V (TI's table has 118k for 5.07 V; 120k is the stocked standard value)
part("R3", "Device:R", "120k", R0402, {"1": "5V_BUCK", "2": "FB"}, (220.0, 60.0), (16.3, 21.4, 90, "F"), "RC0402FR-07120KL")
part("R4", "Device:R", "22.1k", R0402, {"1": "FB", "2": "GND"}, (220.0, 80.0), (17.6, 21.4, 90, "F"), "RC0402FR-0722K1L")
part("C5", "Device:C", "22uF 10V", C0805, {"1": "5V_BUCK", "2": "GND"}, (240.0, 60.0), (19.6, 21.4, 90, "F"), "GRM21BR61A226ME51L")
part("D2", "Device:D_Schottky", "SS14", "Diode_SMD:D_SMA", {"1": "XIAO_5V", "2": "5V_BUCK"},
     (260.0, 45.0), (4.4, 30.6, 0, "F"), "SS14")
part("D3", "Device:D_Schottky", "SS14", "Diode_SMD:D_SMA", {"1": "XIAO_5V", "2": "5V_CAN"},
     (260.0, 75.0), (11.9, 30.6, 0, "F"), "SS14")

# --- log storage: SD NAND (an SD card in a soldered LGA-8) on the XIAO's SPI pins, bottom side under the XIAO.
# SPI mode: D8 = SCK, D9 = MISO, D10 = MOSI, D3 = /CS through JP7 (cut JP7 to free D3; R9 then keeps the
# chip deselected). VESC Express mounts it like a card: (f-connect 10 9 8 5) on the C3 (MOSI MISO SCK CS GPIOs).
# The 10k pull-ups are the SD spec's on CMD/DAT, and hold the C3's strapping pins GPIO8 (D8) and GPIO9 (D9)
# high at reset. Zetta ZDSD02GLGEAG (LCSC C2875853, 2 Gbit = 256 MB, SLC). The land pattern also takes 4 Gbit parts
# (MK MKDV4GCL-ABB, CS-Creative CSNP4GCR01) and XTX XTSD (same pinout, LGA-8 6 x 8 mm).
part("U5", "wavehat:SD_NAND", "SD NAND 2Gb (256 MB)", "wavehat:SD_NAND_LGA-8_8x6mm_P1.27mm",
     {"1": None, "2": "SD_CS", "3": "SD_SCK", "4": "GND", "5": "SD_MOSI", "6": "SD_MISO", "7": None, "8": "3V3"},
     (215.0, 252.0), (10.5, 39.5, 0, "BA"), "ZDSD02GLGEAG")
part("C8", "Device:C", "100nF", C0402, {"1": "3V3", "2": "GND"}, (160.0, 268.0), (5.6, 37.4, 90, "BA"), "GRM155R71C104KA88D")
part("C9", "Device:C", "10uF", C0603, {"1": "3V3", "2": "GND"}, (172.0, 268.0), (4.2, 37.4, 90, "BA"), "GRM188R61A106KE69D")
part("R9", "Device:R", "10k", R0402, {"1": "3V3", "2": "SD_CS"}, (150.0, 232.0), (3.0, 44.6, 90, "BA"), "RC0402FR-0710KL")
part("R10", "Device:R", "10k", R0402, {"1": "3V3", "2": "SD_SCK"}, (162.0, 232.0), (4.3, 44.6, 90, "BA"), "RC0402FR-0710KL")
part("R11", "Device:R", "10k", R0402, {"1": "3V3", "2": "SD_MISO"}, (174.0, 232.0), (5.6, 44.6, 90, "BA"), "RC0402FR-0710KL")
part("R12", "Device:R", "10k", R0402, {"1": "3V3", "2": "SD_MOSI"}, (186.0, 232.0), (6.9, 44.6, 90, "BA"), "RC0402FR-0710KL")
part("JP7", "Jumper:SolderJumper_2_Bridged", "SD CS on D3", "Jumper:SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm",
     {"1": "LED_B", "2": "SD_CS"}, (190.0, 272.0), (16.6, 40.0, 0, "B"))

# --- mechanical
part("H1", "Mechanical:MountingHole_Pad", "M2", "MountingHole:MountingHole_2.2mm_M2_Pad", {"1": "GND"}, (30.0, 260.0), (2.7, 2.7, 0, "F"))
part("H2", "Mechanical:MountingHole_Pad", "M2", "MountingHole:MountingHole_2.2mm_M2_Pad", {"1": "GND"}, (45.0, 260.0), (18.3, 2.7, 0, "F"))
part("FID1", "Mechanical:Fiducial", "Fiducial", "Fiducial:Fiducial_1mm_Mask2mm", {}, (65.0, 260.0), (5.0, 7.0, 0, "F"))
part("FID2", "Mechanical:Fiducial", "Fiducial", "Fiducial:Fiducial_1mm_Mask2mm", {}, (80.0, 260.0), (18.6, 7.0, 0, "F"))
part("FID3", "Mechanical:Fiducial", "Fiducial", "Fiducial:Fiducial_1mm_Mask2mm", {}, (95.0, 260.0), (19.8, 30.6, 0, "F"))
part("FID4", "Mechanical:Fiducial", "Fiducial", "Fiducial:Fiducial_1mm_Mask2mm", {}, (110.0, 260.0), (2.2, 34.4, 0, "BA"))
part("FID5", "Mechanical:Fiducial", "Fiducial", "Fiducial:Fiducial_1mm_Mask2mm", {}, (125.0, 260.0), (18.8, 47.6, 0, "BA"))

# nets that need a power flag for ERC (driven only through passive parts)
PWR_FLAGS = {"GND": (30.0, 285.0), "VIN": (50.0, 285.0), "XIAO_5V": (70.0, 285.0)}

# net classes for routing
POWER_NETS = {"VIN_RAW", "VIN_FUSED", "VIN", "SW", "5V_BUCK", "XIAO_5V", "5V_CAN"}   # GND is the pours; 3V3 is low current

SECTIONS = [  # schematic text labels (x, y, text)
    (25.0, 25.0, "Power: NMEA 2000 NET-S or a 5-30 V lead on the J4 pads -> fuse -> reverse diode -> TVS -> LMR51606 buck 5 V -> diode-OR into the XIAO 5V pin"),
    (60.0, 100.0, "IMU: LSM6DSO on I2C, address 0x6B by default (JP3), as on the Takuma node"),
    (240.0, 100.0, "Controller: Seeed XIAO ESP32-C3 / C6 / S3 (pads 1-14 are common to all three)"),
    (240.0, 192.0, "CAN: SN65HVD230 on D0 (RX) / D1 (TX), the VESC Express pins. J3 VESC, J4 NMEA 2000. JP6 termination open"),
    (140.0, 218.0, "Log storage: SD NAND on SPI, under the XIAO"),
    (25.0, 250.0, "Mechanical"),
]
