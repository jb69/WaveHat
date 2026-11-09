#!/usr/bin/env python3
"""Generate the WaveHat KiCad project's schematic, custom symbols and custom footprints from wavehat_design.py.

    python3 -I gen_schematic.py

Every pin gets a short wire stub and a net label, so connectivity is exact and checkable with
`kicad-cli sch erc`. The drawing is a connectivity schematic (labels, not hand-drawn wires).
"""
import os
import re
import sys
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import wavehat_design as D  # noqa: E402

KICAD_SYM = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols"
SEEED = os.path.join(HERE, "lib", "seeed")
GRID = 1.27
NS = uuid.UUID("6f0c4d8e-6a1d-4f63-9a7e-7a0e5d0b2a11")   # stable UUIDs between runs


def uid(*key):
    return str(uuid.uuid5(NS, "/".join(map(str, key))))


def snap(v):
    return round(round(v / GRID) * GRID, 4)


# ----------------------------------------------------------------------------- s-expression helpers
def extract_block(text, start):
    d = 0
    for j in range(start, len(text)):
        if text[j] == "(":
            d += 1
        elif text[j] == ")":
            d -= 1
            if d == 0:
                return text[start:j + 1]
    raise ValueError("unbalanced")


def lib_symbol(lib, name):
    s = open(os.path.join(KICAD_SYM, lib + ".kicad_sym")).read()
    i = s.find('(symbol "%s"' % name)
    if i < 0:
        raise KeyError(lib + ":" + name)
    blk = extract_block(s, i)
    if "(extends " in blk:
        raise ValueError("extends not handled: " + name)
    return blk


def font(size=1.27):
    return "(effects (font (size %s %s)))" % (size, size)


def prop(name, value, x, y, hide=False, size=1.27, ang=0):
    h = " (hide yes)" if hide else ""
    return '(property "%s" "%s" (at %s %s %s) (effects (font (size %s %s))%s))' % (name, value, x, y, ang, size, size, h)


# ----------------------------------------------------------------------------- custom symbols
def pin(kind, x, y, ang, name, num, length=2.54):
    return ('(pin %s line (at %s %s %s) (length %s) (name "%s" %s) (number "%s" %s))'
            % (kind, x, y, ang, length, name, font(), num, font()))


def box_symbol(name, ref, value, fp, ds, w, h, left, right, top=(), bottom=(), desc=""):
    """left/right/top/bottom: lists of (kind, name, num); placed on a 2.54 grid."""
    hw, hh = w / 2.0, h / 2.0
    pins = []
    for i, (k, n, num) in enumerate(left):
        pins.append(pin(k, -hw - 2.54, hh - 2.54 * (i + 1), 0, n, num))
    for i, (k, n, num) in enumerate(right):
        pins.append(pin(k, hw + 2.54, hh - 2.54 * (i + 1), 180, n, num))
    for i, (k, n, num) in enumerate(top):
        pins.append(pin(k, -hw + 2.54 * (i + 1), hh + 2.54, 270, n, num))
    for i, (k, n, num) in enumerate(bottom):
        pins.append(pin(k, -hw + 2.54 * (i + 1), -hh - 2.54, 90, n, num))
    return ('(symbol "%s" (pin_names (offset 1.016)) (exclude_from_sim no) (in_bom yes) (on_board yes)\n'
            '  %s\n  %s\n  %s\n  %s\n  %s\n'
            '  (symbol "%s_0_1" (rectangle (start %s %s) (end %s %s) (stroke (width 0.254) (type default)) (fill (type background))))\n'
            '  (symbol "%s_1_1" %s)\n)'
            % (name, prop("Reference", ref, -hw, hh + 1.27), prop("Value", value, -hw, -hh - 1.27),
               prop("Footprint", fp, 0, -hh - 3.81, True), prop("Datasheet", ds, 0, -hh - 6.35, True),
               prop("Description", desc, 0, -hh - 8.89, True),
               name, -hw, hh, hw, -hh, name, " ".join(pins)))


CUSTOM = {
    "XIAO_ESP32_14P": box_symbol(
        "XIAO_ESP32_14P", "U", "XIAO ESP32-C3/C6/S3", "wavehat:XIAO_ESP32_14P_SMD",
        "https://wiki.seeedstudio.com/XIAO_ESP32C3_Getting_Started/", 15.24, 20.32,
        left=[("bidirectional", "D0", "1"), ("bidirectional", "D1", "2"), ("bidirectional", "D2", "3"),
              ("bidirectional", "D3", "4"), ("bidirectional", "D4/SDA", "5"), ("bidirectional", "D5/SCL", "6"),
              ("bidirectional", "D6/TX", "7")],
        right=[("power_in", "5V", "14"), ("power_in", "GND", "13"), ("power_out", "3V3", "12"),
               ("bidirectional", "D10", "11"), ("bidirectional", "D9", "10"), ("bidirectional", "D8", "9"),
               ("bidirectional", "D7/RX", "8")],
        desc="Seeed XIAO, castellated pads 1-14 only (common to ESP32-C3, C6 and S3). Pad map from Seeed OPL_Kicad_Library (CC BY-SA 4.0)"),
    "LSM6DSO": box_symbol(
        "LSM6DSO", "U", "LSM6DSO", "Package_LGA:LGA-14_3x2.5mm_P0.5mm_LayoutBorder3x4y",
        "https://www.st.com/resource/en/datasheet/lsm6dso.pdf", 15.24, 20.32,
        left=[("bidirectional", "SDA", "14"), ("input", "SCL", "13"), ("input", "CS", "12"),
              ("bidirectional", "SDO/SA0", "1"), ("passive", "SDx", "2"), ("passive", "SCx", "3")],
        right=[("output", "INT1", "4"), ("output", "INT2", "9"), ("passive", "OCS_Aux", "10"),
               ("passive", "SDO_Aux", "11")],
        top=[("power_in", "VDD", "8"), ("power_in", "VDDIO", "5")],
        bottom=[("power_in", "GND", "6"), ("passive", "GND", "7")],
        desc="ST LSM6DSO 6-axis IMU, LGA-14. Pin functions from ST AN5192"),
    "LMR51606": box_symbol(
        "LMR51606", "U", "LMR51606", "Package_TO_SOT_SMD:SOT-23-6",
        "https://www.ti.com/lit/gpn/LMR51606", 10.16, 10.16,
        left=[("power_in", "VIN", "5"), ("input", "EN", "4")],
        right=[("passive", "CB", "1"), ("power_out", "SW", "6"), ("input", "FB", "3")],
        bottom=[("power_in", "GND", "2")],
        desc="TI LMR51606 4-65 V 600 mA buck, SOT-23-6 (DBV), pin-compatible with the TPS560430. Pins from TI SLUSEY1B"),
    "SD_NAND": box_symbol(
        "SD_NAND", "U", "SD NAND", "wavehat:SD_NAND_LGA-8_8x6mm_P1.27mm",
        "https://atta.szlcsc.com/upload/public/pdf/source/20251121/19FA30E4538875DAFD290F874502AA32.pdf", 12.7, 12.7,
        left=[("input", "~{CS}", "2"), ("input", "SCLK", "3"), ("input", "DI", "5"), ("output", "DO", "6")],
        right=[("passive", "RSV", "1"), ("passive", "RSV", "7")],
        top=[("power_in", "VCC", "8")],
        bottom=[("power_in", "VSS", "4")],
        desc="SD NAND (SD card in LGA-8 8x6 mm), shown with its SPI-mode pin names. Pinout from the Zetta ZDSD, MK "
             "MKDV4GCL, CS-Creative CSNP4GCR01 and XTX XTSD04G datasheets (the same on all)"),
}


def custom_lib_text():
    return "(kicad_symbol_lib (version 20231120) (generator \"wavehat_gen\")\n%s\n)\n" % "\n".join(CUSTOM.values())


# ----------------------------------------------------------------------------- custom footprints
def xiao_footprint():
    src = open(os.path.join(SEEED, "XIAO-ESP32-C3-SMD.kicad_mod")).read()
    out, i = [], 0
    while True:
        j = src.find("(pad ", i)
        if j < 0:
            out.append(src[i:])
            break
        blk = extract_block(src, j)
        num = re.match(r'\(pad "?([^" ]*)"?', blk).group(1)
        out.append(src[i:j])
        if num.isdigit() and int(num) <= 14:
            out.append(blk)
        i = j + len(blk)
    fp = "".join(out)
    fp = fp.replace('(footprint "XIAO-ESP32-C3-SMD"', '(footprint "XIAO_ESP32_14P_SMD"', 1)
    fp = fp.replace('(layer "F.Cu")', '(layer "F.Cu")\n\t(descr "Seeed XIAO ESP32-C3/C6/S3, castellated pads 1-14 only. '
                    'Derived from Seeed-Studio/OPL_Kicad_Library XIAO-ESP32-C3-SMD (CC BY-SA 4.0); pads 15+ removed so one '
                    'footprint fits all three variants. Keep the area under the module free of exposed copper.")\n'
                    '\t(attr smd)', 1)
    return fp


def n2k_pads_footprint():
    pads = []
    for i in range(5):
        x = -6.0 + 3.0 * i
        pads.append('\t(pad "%d" smd roundrect (at %s 0) (size 2.0 2.6) (layers "F.Cu" "F.Mask") (roundrect_rratio 0.25))' % (i + 1, x))
    labels = ["SH", "S", "C", "H", "L"]
    silk = "\n".join('\t(fp_text user "%s" (at %s 2.4) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12))))'
                     % (labels[i], -6.0 + 3.0 * i) for i in range(5))
    return ('(footprint "N2K_Pads_1x05_P3.0mm" (version 20240108) (generator "wavehat_gen") (layer "F.Cu")\n'
            '\t(descr "Solder pads for an NMEA 2000 M12 pigtail: 1 shield, 2 NET-S, 3 NET-C, 4 CAN_H, 5 CAN_L")\n'
            '\t(attr smd exclude_from_bom exclude_from_pos_files)\n'
            '\t(property "Reference" "J4" (at 0 -2.4 0) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12))))\n'
            '\t(property "Value" "N2K_Pads" (at 0 4.0 0) (layer "F.Fab") (effects (font (size 0.8 0.8) (thickness 0.12))))\n'
            '\t(fp_rect (start -7.6 -1.9) (end 7.6 1.9) (stroke (width 0.05) (type solid)) (fill none) (layer "F.CrtYd"))\n'
            '%s\n%s\n)\n' % (silk, "\n".join(pads)))


def sdnand_footprint():
    """LGA-8 8 x 6 mm SD NAND: four lands on each 6 mm edge, 1.27 mm pitch, pin 1 top left; pins 1-4 down the
    left edge, 5-8 up the right. The makers place the package lands differently: Zetta ZDSD (b 0.40, L1 0.75,
    pitch 1.25, 3.10-3.85 mm from centre), MK MKDV4GCL (b 0.55, L 0.85, 3.00-3.85 mm) and CS-Creative CSNP4GCR01
    (b 0.70, L 0.80, 2.70-3.50 mm). PCB lands 1.35 x 0.7 mm at 2.60-3.95 mm cover them all, leaving 0.57 mm
    between lands for a 0.15 mm track; the paste openings are 0.1 mm smaller all round (1.15 x 0.5 mm) so the
    smaller package lands don't float on excess solder."""
    pads = []
    for i in range(4):
        y = -1.905 + 1.27 * i
        pads.append('\t(pad "%d" smd roundrect (at -3.275 %s) (size 1.35 0.7) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.15) (solder_paste_margin -0.1))' % (i + 1, round(y, 3)))
        pads.append('\t(pad "%d" smd roundrect (at 3.275 %s) (size 1.35 0.7) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.15) (solder_paste_margin -0.1))' % (8 - i, round(y, 3)))
    g = []
    for layer, hw, hh, w in (("F.Fab", 4.0, 3.0, 0.1), ("F.CrtYd", 4.25, 3.25, 0.05)):
        g.append('\t(fp_rect (start %s %s) (end %s %s) (stroke (width %s) (type solid)) (fill none) (layer "%s"))' % (-hw, -hh, hw, hh, w, layer))
    # silkscreen: top and bottom edges only (the lands sit inside the body), pin-1 dot outside the corner
    for y in (-3.12, 3.12):
        g.append('\t(fp_line (start -2.4 %s) (end 2.4 %s) (stroke (width 0.12) (type solid)) (layer "F.SilkS"))' % (y, y))
    g.append('\t(fp_circle (center -4.4 -2.6) (end -4.25 -2.6) (stroke (width 0.3) (type solid)) (fill solid) (layer "F.SilkS"))')
    g.append('\t(fp_line (start -4.0 -2.2) (end -3.2 -3.0) (stroke (width 0.1) (type solid)) (layer "F.Fab"))')
    return ('(footprint "SD_NAND_LGA-8_8x6mm_P1.27mm" (version 20240108) (generator "wavehat_gen") (layer "F.Cu")\n'
            '\t(descr "SD NAND, LGA-8 8x6 mm, 1.27 mm pitch (MK MKDV1G/4GCL, CS-Creative CSNP1G/4GCR01, Zetta ZDSD, XTX XTSD). '
            'Lands 1.35 x 0.7 mm covering every maker\'s package land position")\n'
            '\t(attr smd)\n'
            '\t(property "Reference" "U5" (at 0 -4.2 0) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12))))\n'
            '\t(property "Value" "SD_NAND" (at 0 4.2 0) (layer "F.Fab") (effects (font (size 0.8 0.8) (thickness 0.12))))\n'
            '%s\n%s\n)\n' % ("\n".join(g), "\n".join(pads)))


# ----------------------------------------------------------------------------- schematic
def symbol_def(lib_id):
    lib, name = lib_id.split(":")
    if lib == "wavehat":
        blk = CUSTOM[name]
    else:
        blk = lib_symbol(lib, name)
    # embedded symbols carry the library prefix on the top-level name only
    return blk.replace('(symbol "%s"' % name, '(symbol "%s"' % lib_id, 1)


def symbol_pins(lib_id):
    blk = symbol_def(lib_id)
    pins = {}
    for m in re.finditer(r'\(pin \w+ \w+\s*\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\).*?\(number "([^"]*)"', blk, re.S):
        pins[m.group(4)] = (float(m.group(1)), float(m.group(2)), float(m.group(3) or 0))
    return pins


def pin_names(lib_id):
    """{pin number: pin name} for a symbol, as KiCad uses them in "unconnected-(REF-NAME-PadN)" net names."""
    blk = symbol_def(lib_id)
    return {m.group(2): m.group(1) for m in re.finditer(r'\(pin \w+ \w+.*?\(name "([^"]*)".*?\(number "([^"]*)"', blk, re.S)}


def stub_and_label(px, py, ang, net, key):
    """Pin connection point (schematic coords) and the pin's angle (library, y-up). Returns wire + label."""
    import math
    # pin points from the connection point toward the body along `ang`; go the other way
    dx, dy = -math.cos(math.radians(ang)), math.sin(math.radians(ang))   # y flipped for the schematic
    ex, ey = snap(px + 2.54 * dx), snap(py + 2.54 * dy)
    if abs(dx) > 0.5:
        lang, just = (0, "left") if dx > 0 else (180, "right")
    else:
        lang, just = (90, "left") if dy < 0 else (270, "left")
    wire = '(wire (pts (xy %s %s) (xy %s %s)) (stroke (width 0) (type default)) (uuid "%s"))' % (px, py, ex, ey, uid("w", key))
    lab = ('(label "%s" (at %s %s %s) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify %s bottom)) (uuid "%s"))'
           % (net, ex, ey, lang, just, uid("l", key)))
    return wire + "\n" + lab


def schematic_text():
    root = uid("root")
    used = sorted({p["lib_id"] for p in D.P.values()} | {"power:PWR_FLAG"})
    libsyms = "\n".join(symbol_def(l) for l in used)
    items = []
    for x, y, t in D.SECTIONS:
        items.append('(text "%s" (exclude_from_sim no) (at %s %s 0) (effects (font (size 2 2) bold) (justify left bottom)) (uuid "%s"))'
                     % (t, x, y, uid("t", t)))
    for ref, p in sorted(D.P.items()):
        X, Y = snap(p["sch"][0]), snap(p["sch"][1])
        pins = symbol_pins(p["lib_id"])
        pin_uuids = " ".join('(pin "%s" (uuid "%s"))' % (n, uid("p", ref, n)) for n in sorted(pins))
        hidden_ref = ref.startswith("FID") or ref.startswith("H")
        inst = ('(symbol (lib_id "%s") (at %s %s 0) (unit 1) (exclude_from_sim no) (in_bom %s) (on_board yes) (dnp %s) (uuid "%s")\n'
                '  %s\n  %s\n  %s\n  %s\n  %s\n  %s\n'
                '  (instances (project "wavehat" (path "/%s" (reference "%s") (unit 1))))\n)'
                % (p["lib_id"], X, Y, "no" if p["fp"].startswith(("Jumper:", "TestPoint:", "MountingHole:", "Fiducial:", "wavehat:N2K")) else "yes",
                   "yes" if p["dnp"] else "no", uid("s", ref),
                   prop("Reference", ref, X + 3.0, Y - 1.5, False), prop("Value", p["value"], X + 3.0, Y + 1.5, False),
                   prop("Footprint", p["fp"], X, Y + 5.0, True), prop("Datasheet", "", X, Y + 7.0, True),
                   prop("MPN", p["mpn"], X, Y + 9.0, True), pin_uuids, root, ref))
        items.append(inst)
        for n, (lx, ly, ang) in pins.items():
            px, py = round(X + lx, 4), round(Y - ly, 4)
            net = p["pins"].get(n, "__absent__")
            if net == "__absent__":
                raise KeyError("%s pin %s has no entry in wavehat_design.py" % (ref, n))
            if net is None:
                items.append('(no_connect (at %s %s) (uuid "%s"))' % (px, py, uid("nc", ref, n)))
            else:
                items.append(stub_and_label(px, py, ang, net, ref + "." + n))
    for i, (net, (x, y)) in enumerate(sorted(D.PWR_FLAGS.items())):
        X, Y = snap(x), snap(y)
        ref = "#FLG0%d" % (i + 1)
        items.append('(symbol (lib_id "power:PWR_FLAG") (at %s %s 0) (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid "%s")\n'
                     '  %s\n  %s\n  %s\n  %s\n  (pin "1" (uuid "%s"))\n  (instances (project "wavehat" (path "/%s" (reference "%s") (unit 1))))\n)'
                     % (X, Y, uid("s", ref), prop("Reference", ref, X, Y - 3, True), prop("Value", "PWR_FLAG", X, Y - 4, False),
                        prop("Footprint", "", X, Y, True), prop("Datasheet", "", X, Y, True), uid("p", ref, 1), root, ref))
        items.append(stub_and_label(X, Y, 90, net, ref))
    return ('(kicad_sch (version 20231120) (generator "wavehat_gen") (uuid "%s") (paper "A3")\n'
            '(title_block (title "WaveHat: sea-state sensor and CAN node for the Seeed XIAO") (date "2026-10-17") (rev "A")\n'
            '  (comment 1 "Generated from wavehat_design.py by gen_schematic.py - edit the design file, not this one")\n'
            '  (comment 2 "Circuit origin: the Takuma project XIAO node (XIAO ESP32-C3 + LSM6DSO + SN65HVD230)")\n'
            '  (comment 3 "XIAO footprint derived from Seeed OPL_Kicad_Library, CC BY-SA 4.0"))\n'
            '(lib_symbols\n%s\n)\n%s\n(sheet_instances (path "/" (page "1")))\n)\n'
            % (root, libsyms, "\n".join(items)))


def project_files():
    pro = ('{\n  "meta": {"filename": "wavehat.kicad_pro", "version": 1},\n'
           '  "board": {"design_settings": {"rules": {"min_clearance": 0.15, "min_track_width": 0.15, "min_via_diameter": 0.6, '
           '"min_through_hole_diameter": 0.3}}},\n  "sheets": [["%s", "Root"]]\n}\n' % uid("root"))
    # project-level tables list every library used, so the project opens cleanly even before KiCad's
    # global library tables exist (they are only created the first time the KiCad app is launched)
    symlibs = sorted({p["lib_id"].split(":")[0] for p in D.P.values()} | {"power"})
    fplibs = sorted({p["fp"].split(":")[0] for p in D.P.values()})
    sym = "(sym_lib_table (version 7)\n"
    for l in symlibs:
        uri = "${KIPRJMOD}/lib/wavehat.kicad_sym" if l == "wavehat" else "${KICAD10_SYMBOL_DIR}/%s.kicad_sym" % l
        sym += '  (lib (name "%s") (type "KiCad") (uri "%s") (options "") (descr ""))\n' % (l, uri)
    sym += ")\n"
    fpt = "(fp_lib_table (version 7)\n"
    for l in fplibs:
        uri = "${KIPRJMOD}/lib/wavehat.pretty" if l == "wavehat" else "${KICAD10_FOOTPRINT_DIR}/%s.pretty" % l
        fpt += '  (lib (name "%s") (type "KiCad") (uri "%s") (options "") (descr ""))\n' % (l, uri)
    fpt += ")\n"
    return pro, sym, fpt


def main():
    os.makedirs(os.path.join(HERE, "lib", "wavehat.pretty"), exist_ok=True)
    open(os.path.join(HERE, "lib", "wavehat.kicad_sym"), "w").write(custom_lib_text())
    open(os.path.join(HERE, "lib", "wavehat.pretty", "XIAO_ESP32_14P_SMD.kicad_mod"), "w").write(xiao_footprint())
    open(os.path.join(HERE, "lib", "wavehat.pretty", "N2K_Pads_1x05_P3.0mm.kicad_mod"), "w").write(n2k_pads_footprint())
    open(os.path.join(HERE, "lib", "wavehat.pretty", "SD_NAND_LGA-8_8x6mm_P1.27mm.kicad_mod"), "w").write(sdnand_footprint())
    open(os.path.join(HERE, "wavehat.kicad_sch"), "w").write(schematic_text())
    pro, sym, fpt = project_files()
    if not os.path.exists(os.path.join(HERE, "wavehat.kicad_pro")):
        open(os.path.join(HERE, "wavehat.kicad_pro"), "w").write(pro)
    open(os.path.join(HERE, "sym-lib-table"), "w").write(sym)
    open(os.path.join(HERE, "fp-lib-table"), "w").write(fpt)
    nets = sorted({n for p in D.P.values() for n in p["pins"].values() if n})
    print("schematic: %d parts, %d nets" % (len(D.P), len(nets)))


if __name__ == "__main__":
    main()
