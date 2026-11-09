#!/usr/bin/env python3
"""Draw hole_map.png for CHECKLIST.md: the plate seen from above (holes 1-21) and the base seen from
below (holes T1-T29), each with the board outline, the part pockets as ghosts and the labels in the
margins exactly where the jig's lettering is. Reads test_plate_points.scad; needs matplotlib.

    python3 gen_hole_map.py
"""
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle

HERE = Path(__file__).parent
SRC = (HERE / "test_plate_points.scad").read_text()


def scad_list(name):
    """Rows of numbers from `name = [ [..], [..], ];`, with the trailing // comment of each row."""
    body = re.search(rf"{name} = \[(.*?)\n\];", SRC, re.S).group(1)
    rows = []
    for line in body.splitlines():
        m = re.match(r"\s*\[([^\]]*)\],\s*(?://\s*(.*))?", line)
        if m:
            rows.append(([float(v) for v in m.group(1).split(",")], (m.group(2) or "").strip()))
    return rows


board = [float(v) for v in re.search(r"board = \[(.*?)\];", SRC).group(1).split(",")]
mounts = [[float(v) for v in m.split(",")] for m in re.findall(r"\[([\d., ]+)\]", re.search(r"mount_holes = \[(.*?)\];", SRC).group(1))]
plate_pts = scad_list("points")
base_pts = scad_list("base_points")
plate_pockets = scad_list("plate_pockets")
base_pockets = scad_list("base_pockets")

W, L = board
MARGIN_X, MARGIN_Y = 14, 6      # the jig's outer margins
PLATE_C, BASE_C = "#1f6fb2", "#d1622a"


def panel(ax, title, pts, pockets, colour, prefix, mirror_pts):
    ax.set_aspect("equal")
    ax.set_xlim(-MARGIN_X - 24, W + MARGIN_X + 24)
    ax.set_ylim(-MARGIN_Y - 2, L + MARGIN_Y + 2)
    ax.axis("off")
    ax.set_title(title, fontsize=11, fontweight="bold", pad=6)
    # jig outline, board outline
    ax.add_patch(Rectangle((-MARGIN_X, -MARGIN_Y), W + 2 * MARGIN_X, L + 2 * MARGIN_Y, fc="#f2f2f2", ec="#999", lw=1))
    ax.add_patch(Rectangle((0, 0), W, L, fc="#dfeedb", ec="#2e6b2e", lw=1.2))
    ax.text(W / 2, L + MARGIN_Y / 2, "BOW", ha="center", va="center", fontsize=9, fontweight="bold")
    ax.text(W / 2, -MARGIN_Y / 2, "stern (USB-C)", ha="center", va="center", fontsize=7)
    for mx, my in mounts:
        ax.add_patch(Circle((mx, my), 1.1, fc="white", ec="#444", lw=0.8))
    # pockets (parts) as ghosts, named
    for (x1, y1, x2, y2, _d), name in pockets:
        ax.add_patch(Rectangle((x1, y1), x2 - x1, y2 - y1, fc="none", ec="#777", lw=0.6, ls=(0, (2, 2))))
        if (x2 - x1) * (y2 - y1) > 12:
            ax.text((x1 + x2) / 2, (y1 + y2) / 2, name, ha="center", va="center", fontsize=5, color="#888")
    # holes with the jig's labels in the margins
    for (x, y, n, side, ly), comment in pts:
        if mirror_pts:
            x = W - x
        n = int(n)
        net = comment.split(":")[0]
        net = re.sub(r"^T\d+\s+", "", net)       # base comments start with "T7 "
        ax.add_patch(Circle((x, y), 0.8, fc="white", ec=colour, lw=1.4, zorder=5))
        if side == 0:
            tx, lx, ha = -MARGIN_X + 1, -MARGIN_X + 6.2, "left"
        else:
            tx, lx, ha = W + 4.4, W + 4.2, "left"
        ax.plot([lx, x], [ly, y], color=colour, lw=0.6, alpha=0.8, zorder=4)
        ax.text(tx, ly, f"{prefix}{n}", ha="left", va="center", fontsize=7.5, fontweight="bold", color=colour)
        # net name outside the jig
        ox = -MARGIN_X - 1.2 if side == 0 else W + MARGIN_X + 1.2
        ax.text(ox, ly, net, ha="right" if side == 0 else "left", va="center", fontsize=6, color="#333")


fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 5.6))
panel(a1, "PLATE, seen from above (board bottom face)\nholes 1-21 over bottom-side pads",
      plate_pts, plate_pockets, PLATE_C, "", mirror_pts=False)
panel(a2, "BASE, seen from below (board component side)\nholes T1-T29 up to component-side pads",
      base_pts, base_pockets, BASE_C, "T", mirror_pts=True)
fig.text(0.5, 0.012,
         "Both views as you hold the jig while probing, bow away from you. Dashed boxes are the part pockets\n"
         "(plate: NAND side under the plate; base: component side, on the far face). Numbers sit where the jig's lettering is.",
         ha="center", va="bottom", fontsize=7, color="#333")
fig.tight_layout(rect=(0, 0.05, 1, 1))
fig.savefig(HERE / "hole_map.png", dpi=170)
fig.savefig(HERE / "hole_map.svg")
print("wrote hole_map.png / hole_map.svg")
