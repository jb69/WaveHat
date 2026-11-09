#!/usr/bin/env python3
"""Probe points, pockets and the legend for the WaveHat rev A test jig, read from the KiCad layout.

Run with KiCad's Python (it needs pcbnew):
    /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3 gen_test_plate.py

Writes test_plate_points.scad (for wavehat_test_plate.scad) and legend.md.

The board lies component side down on the BASE and the PLATE lies on its bottom face. The plate has a
hole over each bottom-side probe pad (1..N); the base has a hole up through it at each component-side
landmark (T1..TN), numbered on its underside. Every reading is between two exposed pads on the same net
whose only connection runs through one or more vias, so 0 Ω (or the stated resistor) means those vias
conduct. Three kinds: bottom-to-bottom (plate hole to plate hole), top-to-top (base hole to base hole)
and bottom-to-top (plate hole to base hole). Via pads are tented, so none of this needs mask scraped.

Coordinates: mm from the board's lower-left corner. The plate is drawn in the bottom view (x mirrored:
x = 21 - x_top); the base's holes are given in the top view and mirrored by the .scad, since its
underside, seen from below with the bow away, is the top view again."""

import os
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(HERE, "..", "kicad", "wavehat.kicad_pcb")
ORIGIN = (100.0, 154.0)   # KiCad coordinates of the board's lower-left corner
BOARD_W, BOARD_L = 21.0, 54.0

# Bottom-side probe pads (plate holes 1..): (ref, pad, net label)
BOTTOM = [
    ("C9", "1", "3V3 (NAND island)"), ("JP3", "1", "3V3 (JP3)"), ("JP3", "2", "SA0"),
    ("JP1", "1", "SDA"), ("JP1", "2", "SDA_PU"), ("JP2", "1", "SCL"), ("JP2", "2", "SCL_PU"),
    ("JP4", "1", "IMU_INT1"), ("JP5", "1", "IMU_INT2"),
    ("TP1", "1", "LED_R (D2)"), ("TP2", "1", "LED_B (D3, NAND CS)"), ("R9", "2", "SD_CS (D3 through JP7)"),
    ("R10", "2", "SD_SCK (D8)"), ("R11", "2", "SD_MISO (D9)"), ("R12", "2", "SD_MOSI (D10)"),
    ("J4", "2", "VIN_RAW"), ("J4", "3", "GND"), ("J4", "4", "CANH"), ("J4", "5", "CANL"),
    ("JP6", "2", "CANL (JP6)"), ("JP6", "1", "TERM"),
]
# Component-side landmarks (base holes T1..): (ref, pad, label). U4 pads are the XIAO castellation lands.
TOP = [
    ("U4", "1", "CAN_RX, XIAO D0"), ("U4", "2", "CAN_TX, XIAO D1"), ("U4", "3", "LED_R, XIAO D2"),
    ("U4", "4", "LED_B, XIAO D3"), ("U4", "5", "SDA, XIAO D4"), ("U4", "6", "SCL, XIAO D5"),
    ("U4", "9", "SD_SCK, XIAO D8"), ("U4", "10", "SD_MISO, XIAO D9"), ("U4", "11", "SD_MOSI, XIAO D10"),
    ("U4", "12", "3V3, XIAO 3V3"), ("U4", "13", "GND, XIAO GND"), ("U4", "14", "XIAO_5V, XIAO 5V"),
    ("U3", "1", "CAN_TX, transceiver TXD"), ("U3", "4", "CAN_RX, transceiver RXD"), ("U3", "6", "CANL, transceiver"),
    ("J3", "2", "CANL, J3 tail"), ("J3", "3", "CANH, J3 tail"), ("J3", "4", "5V_CAN, J3 tail"),
    ("J2", "3", "SDA, J2 tail"), ("J2", "4", "SCL, J2 tail"),
    ("D3", "2", "5V_CAN, D3 cathode"), ("D2", "1", "XIAO_5V, D2 anode"), ("D2", "2", "5V_BUCK, D2 cathode"),
    ("C5", "1", "5V_BUCK, buck output"), ("C6", "1", "CB, bootstrap"), ("U2", "1", "CB, buck BST"),
    ("C4", "1", "VIN, input capacitor"), ("TVS1", "1", "VIN, TVS"), ("F1", "1", "VIN_RAW, fuse"),
]
# Readings. Each: (net, kind, A, B, expect, note). A and B are (ref, pad); kind B = plate-plate,
# T = base-base, X = plate-base. Which vias a reading covers comes from the layer islands (see the
# connectivity check in the WaveHat session notes, 30 Oct 2026).
READINGS = [
    ("3V3", "B", ("C9", "1"), ("JP3", "1"), "0 Ω", "both 3V3 vias in series: board 2's fault"),
    ("CANL", "B", ("J4", "5"), ("JP6", "2"), "0 Ω", "all four CANL vias"),
    ("SDA_PU", "B", ("JP1", "2"), ("JP3", "1"), "4.7 kΩ", "the SDA_PU via, through R1 on top"),
    ("SCL_PU", "B", ("JP2", "2"), ("JP3", "1"), "4.7 kΩ", "the SCL_PU via, through R2 on top"),
    ("TERM", "B", ("JP6", "1"), ("J4", "4"), "120 Ω", "the TERM via and J4's CANH via, through R5"),
    ("CAN_TX", "T", ("U4", "2"), ("U3", "1"), "0 Ω", "all four CAN_TX vias"),
    ("CAN_RX", "T", ("U4", "1"), ("U3", "4"), "0 Ω", "both CAN_RX vias"),
    ("CANL", "T", ("J3", "2"), ("U3", "6"), "0 Ω", "the two CANL vias between J3 and U3"),
    ("5V_CAN", "T", ("D3", "2"), ("J3", "4"), "0 Ω", "both 5V_CAN vias"),
    ("XIAO_5V", "T", ("U4", "14"), ("D2", "1"), "0 Ω", "both XIAO_5V vias"),
    ("5V_BUCK", "T", ("C5", "1"), ("D2", "2"), "0 Ω", "both 5V_BUCK vias"),
    ("CB", "T", ("C6", "1"), ("U2", "1"), "0 Ω", "both CB vias"),
    ("VIN", "T", ("C4", "1"), ("TVS1", "1"), "0 Ω", "both VIN vias"),
    ("SDA", "T", ("U4", "5"), ("J2", "3"), "0 Ω", "the SDA vias between the XIAO and J2 (not the one at the IMU)"),
    ("SCL", "T", ("U4", "6"), ("J2", "4"), "0 Ω", "the SCL vias between the XIAO and J2 (not the one at the IMU)"),
    ("SD_SCK", "X", ("R10", "2"), ("U4", "9"), "0 Ω", "its single via"),
    ("SD_MISO", "X", ("R11", "2"), ("U4", "10"), "0 Ω", "its single via"),
    ("SD_MOSI", "X", ("R12", "2"), ("U4", "11"), "0 Ω", "its single via"),
    ("LED_B / SD CS", "X", ("TP2", "1"), ("U4", "4"), "0 Ω", "its single via: board 2's second fault"),
    ("LED_R", "X", ("TP1", "1"), ("U4", "3"), "0 Ω", "its single via"),
    ("VIN_RAW", "X", ("J4", "2"), ("F1", "1"), "0 Ω", "its single via"),
    ("CANH", "X", ("J4", "4"), ("J3", "3"), "0 Ω", "the CANH vias between J4 and J3"),
    ("3V3 island", "X", ("C9", "1"), ("U4", "12"), "0 Ω", "the island's via alone"),
    ("SDA", "X", ("JP1", "1"), ("U4", "5"), "0 Ω", "the SDA vias to the pull-up jumper"),
    ("SCL", "X", ("JP2", "1"), ("U4", "6"), "0 Ω", "the SCL vias to the pull-up jumper"),
    ("GND", "X", ("J4", "3"), ("U4", "13"), "0 Ω", "reference (the pours carry GND)"),
]
UNTESTABLE = ("SA0 (JP3 pin 2), IMU_INT1 (JP4 pin 1) and IMU_INT2 (JP5 pin 1) end at the IMU's LGA pads under the "
              "chip: no meter check. SA0 passes if the IMU answers at 0x6B with JP3 at 3V3; the INT lines are unused "
              "unless JP4/JP5 are bridged.")

# Part heights above the board (mm) by footprint name fragment; every part taller than 0 gets a pocket
# (bounding box + margin, height + headroom) in whichever part lies on that face.
HEIGHTS = [("JST_GH", 4.3), ("JST_SH", 2.9), ("D_SMB", 2.6), ("D_SMA", 2.5), ("L_Changjiang", 2.1),
           ("C_1206", 1.8), ("SOIC-8", 1.75), ("Fuse_1812", 1.6), ("SOT-23", 1.45), ("C_0805", 1.4),
           ("SD_NAND", 1.0), ("C_0603", 0.9), ("LGA-14", 0.9), ("0402", 0.6),
           ("SolderJumper", 0), ("TestPoint", 0), ("N2K_Pads", 0), ("MountingHole", 0), ("Fiducial", 0),
           ("XIAO", 0)]   # the XIAO is not fitted when the jig is used
POCKET_MARGIN = 0.5
POCKET_HEADROOM = 0.5


def mm(v):
    return v / 1e6


def layout_labels(pts, pitch, y_max, y_min):
    """Margin label rows: points left of the median x label left, the rest right; stacked from the bow
    end at least `pitch` apart, kept inside y_min..y_max. Returns {index: (side, y)}."""
    labels = {}
    split = sorted(p[0] for p in pts)[len(pts) // 2]
    for side, sel in ((0, lambda p: p[0] < split), (1, lambda p: p[0] >= split)):
        idx = sorted((i for i, p in enumerate(pts) if sel(p)), key=lambda i: -pts[i][1])
        ys, prev = [], y_max + pitch
        for i in idx:
            y = min(pts[i][1], prev - pitch)
            ys.append(y)
            prev = y
        if ys and ys[-1] < y_min:
            prev = y_min - pitch
            for k in range(len(ys) - 1, -1, -1):
                ys[k] = max(ys[k], prev + pitch)
                prev = ys[k]
        for i, y in zip(idx, ys):
            labels[i] = (side, y)
    return labels


def main():
    b = pcbnew.LoadBoard(PCB)
    ox, oy = ORIGIN
    top = lambda p: (mm(p.x) - ox, oy - mm(p.y))
    pads = {(f.GetReference(), p.GetNumber()): p for f in b.GetFootprints() for p in f.Pads()}
    for ref, num, _ in BOTTOM + TOP:
        assert (ref, num) in pads, (ref, num)

    bottom_pts = [(BOARD_W - top(pads[(r, n)].GetPosition())[0], top(pads[(r, n)].GetPosition())[1], r, n, lab)
                  for r, n, lab in BOTTOM]
    top_pts = [(*top(pads[(r, n)].GetPosition()), r, n, lab) for r, n, lab in TOP]
    bottom_pts.sort(key=lambda p: (-round(p[1] / 3.0), p[0]))   # numbered from the bow end down
    top_pts.sort(key=lambda p: (-round(p[1] / 3.0), p[0]))
    bnum = {(r, n): i + 1 for i, (_, _, r, n, _) in enumerate(bottom_pts)}
    tnum = {(r, n): i + 1 for i, (_, _, r, n, _) in enumerate(top_pts)}
    for net, kind, a, c, *_ in READINGS:
        for key, where in ((a, kind in "BX"), (c, kind in "B")):
            assert key in (bnum if where else tnum), (net, key)
    blab = layout_labels(bottom_pts, 3.0, 56.0, -1.0)
    tlab = layout_labels(top_pts, 3.0, 56.0, -1.0)

    parts = {"F.Cu": [], "B.Cu": []}   # (x1, y1, x2, y2, depth, ref), top view
    for f in b.GetFootprints():
        fp = f.GetFPIDAsString()
        h = next((hh for frag, hh in HEIGHTS if frag in fp), None)
        if h is None:
            raise SystemExit(f"no height for {f.GetReference()} {fp}")
        if h == 0:
            continue
        bb = f.GetBoundingBox(False, False)
        side = "F.Cu" if f.GetLayer() == pcbnew.F_Cu else "B.Cu"
        parts[side].append((mm(bb.GetLeft()) - ox - POCKET_MARGIN, oy - mm(bb.GetBottom()) - POCKET_MARGIN,
                            mm(bb.GetRight()) - ox + POCKET_MARGIN, oy - mm(bb.GetTop()) + POCKET_MARGIN,
                            h + POCKET_HEADROOM, f.GetReference()))
    mirror = lambda r: (BOARD_W - r[2], r[1], BOARD_W - r[0], r[3], r[4], r[5])
    holes = {k: top(pads[(k, "1")].GetPosition()) for k in ("H1", "H2")}

    with open(os.path.join(HERE, "test_plate_points.scad"), "w") as f:
        f.write("// Generated by gen_test_plate.py from ../kicad/wavehat.kicad_pcb. mm from the board's lower-left corner.\n")
        f.write(f"board = [{BOARD_W}, {BOARD_L}];\n")
        f.write(f"mount_holes = [[{holes['H1'][0]:.2f}, {holes['H1'][1]:.2f}], [{holes['H2'][0]:.2f}, {holes['H2'][1]:.2f}]];  // symmetric in x\n")
        f.write("// Plate holes, bottom view: [x, y, number, label side (0 left, 1 right), label y]\n")
        f.write("points = [\n")
        for i, (x, y, r, n, lab) in enumerate(bottom_pts):
            side, ly = blab[i]
            f.write(f"  [{x:6.2f}, {y:6.2f}, {i + 1:2d}, {side}, {ly:6.2f}],  // {lab}: {r} pad {n}\n")
        f.write("];\n")
        f.write("// Base holes, TOP view (the .scad mirrors x): [x, y, number, label side, label y]\n")
        f.write("base_points = [\n")
        for i, (x, y, r, n, lab) in enumerate(top_pts):
            side, ly = tlab[i]
            f.write(f"  [{x:6.2f}, {y:6.2f}, {i + 1:2d}, {side}, {ly:6.2f}],  // T{i + 1} {lab}: {r} pad {n}\n")
        f.write("];\n")

        def pocket_list(name, rows, comment):
            f.write(f"// {comment}: [x1, y1, x2, y2, depth]\n{name} = [\n")
            for r in sorted(rows, key=lambda r: r[5]):
                f.write(f"  [{r[0]:6.2f}, {r[1]:6.2f}, {r[2]:6.2f}, {r[3]:6.2f}, {r[4]:4.1f}],  // {r[5]}\n")
            f.write("];\n")
        pocket_list("plate_pockets", [mirror(r) for r in parts["B.Cu"]],
                    "Plate underside pockets over the bottom-side parts (bottom view)")
        pocket_list("base_pockets", [mirror(r) for r in parts["F.Cu"]],
                    "Base top pockets over the component-side parts (bottom view)")

    with open(os.path.join(HERE, "legend.md"), "w") as f:
        f.write("# Test jig legend (WaveHat rev A)\n\n")
        f.write("The board lies component side down on the base, bow end at BOW, pegs through its mounting holes; "
                "the plate lies on the bottom face. Plate holes are numbered 1-21 on the plate; base holes T1-T29 "
                "go up through the base to the component side and are numbered on the base's underside. Every "
                "reading below is between two pads whose only connection runs through vias, so 0 Ω (or the "
                "resistor stated) means those vias conduct and nothing needs its solder mask scraped. "
                "Work through the three tables; a fail names the net and the vias in question "
                "(`../kicad/reports/vias.md` has their positions).\n\n")
        kinds = {"B": "## Plate to plate (both probes from above)\n\n| Net | Probe A | Probe B | Expect | Covers |\n|---|---|---|---|---|\n",
                 "T": "## Base to base (both probes from below, up through the base)\n\n| Net | Probe A | Probe B | Expect | Covers |\n|---|---|---|---|---|\n",
                 "X": "## Plate to base (one probe each side)\n\n| Net | Plate hole | Base hole | Expect | Covers |\n|---|---|---|---|---|\n"}
        for k in "BTX":
            f.write(kinds[k])
            for net, kind, a, c, expect, note in READINGS:
                if kind != k:
                    continue
                A = f"{bnum[a]} ({a[0]} pad {a[1]})" if kind in "BX" else f"T{tnum[a]} ({a[0]} pad {a[1]})"
                C = f"{bnum[c]} ({c[0]} pad {c[1]})" if kind == "B" else f"T{tnum[c]} ({c[0]} pad {c[1]})"
                f.write(f"| {net} | {A} | {C} | {expect} | {note} |\n")
            f.write("\n")
        f.write(f"**Not testable with a meter:** {UNTESTABLE}\n\n")
        f.write("## Plate holes (bottom view, x mirrored)\n\n| No. | Over | Net |\n|---|---|---|\n")
        for i, (x, y, r, n, lab) in enumerate(bottom_pts, 1):
            f.write(f"| {i} | {r} pad {n} ({x:.1f}, {y:.1f}) | {lab} |\n")
        f.write("\n## Base holes (top view)\n\n| No. | Over | Net |\n|---|---|---|\n")
        for i, (x, y, r, n, lab) in enumerate(top_pts, 1):
            f.write(f"| T{i} | {r} pad {n} ({x:.1f}, {y:.1f}) | {lab} |\n")
        f.write("\nXIAO pads: the castellation lands of the unfitted XIAO; with a XIAO fitted the jig no longer fits "
                "(no pocket for it).\n")
    print(f"{len(bottom_pts)} plate holes, {len(top_pts)} base holes, {len(READINGS)} readings, "
          f"{len(parts['F.Cu'])}+{len(parts['B.Cu'])} pockets written")


if __name__ == "__main__":
    main()
