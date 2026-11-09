// WaveHat rev A test jig: holds the board component side down and guides meter probes onto numbered
// probe points on both faces, so every layer crossing can be checked for open vias with a multimeter.
//
// Two parts, both flat against the board, with pockets only where parts are (no board-shaped recess,
// so a board still in its JLCPCB rails lies flat across the jig and can be tested before it is snapped
// out). The BASE is a solid slab with pockets for J2, J3 and every other component-side part and a 2 mm
// hole up through it at each component-side probe landmark (T1..T29, numbered on its underside). Two
// M2 screws from below, through the board's mounting holes (bow end), locate the board and the plate.
// The PLATE lies on the board's bottom face, with pockets for the SD NAND and its passives, a 1.6 mm
// hole over each bottom-side probe pad (1..21) and the numbers recessed in its margins with leaders.
//
// Probe points and pockets come from test_plate_points.scad (gen_test_plate.py reads them from the
// KiCad layout). Model coordinates are mm from the board's lower-left corner in the BOTTOM view, bow
// at +y; the base's holes are listed in the top view and mirrored here.
//
// Single-colour parts (lettering recessed 0.5 mm):
//   openscad -D 'part="base"'  -o wavehat_test_plate_base.stl  wavehat_test_plate.scad
//   openscad -D 'part="plate"' -o wavehat_test_plate_plate.stl wavehat_test_plate.scad
// Two-colour parts for a dual-extruder printer: the body with the lettering cut out, and the lettering
// as its own 0.5 mm solid that fills the cut, in the same coordinates. Load each pair into the slicer
// as one object with two parts and give the lettering the second extruder.
//   openscad -D 'part="base_body"'  -o dual/wavehat_test_plate_base_body.stl  wavehat_test_plate.scad
//   openscad -D 'part="base_text"'  -o dual/wavehat_test_plate_base_text.stl  wavehat_test_plate.scad
//   (and plate_body / plate_text)
// Every STL is in print orientation: the base pockets-down with the underside numbers on top, the
// plate numbers up. 0.2 mm layers, no supports. PETG or PLA.

include <test_plate_points.scad>

part = "assembly";           // base, plate, base_body, base_text, plate_body, plate_text, assembly

// --- board
board_t     = 1.6;
// --- base
margin_x    = 14;            // beyond the board's long edges
margin_y    = 6;             // beyond the board's ends
deck_t      = 8;             // the deepest pocket is J3 at 4.8 mm
base_hole_d = 2.0;           // up through the deck to the component-side landmarks
screw_d     = 1.7;           // M2 screws from below, through the mounting holes, into the plate
screw_head  = [4.2, 2.2];    // counterbore under the deck
// --- plate
plate_t     = 4;
hole_d      = 1.6;
text_h      = 2.4;
engrave     = 0.5;           // depth of the recessed lettering and leader lines
leader_w    = 0.5;
font        = "Liberation Sans:style=Bold";

outer = [board[0] + 2 * margin_x, board[1] + 2 * margin_y];
$fn = 32;

module outline(size, z) { translate([-(size[0] - board[0]) / 2, -(size[1] - board[1]) / 2, 0]) cube([size[0], size[1], z]); }

// pockets cut down from a face at height z0 (rows: x1, y1, x2, y2, depth)
module pockets(list, z0) {
    for (r = list) translate([r[0], r[1], z0 - r[4]]) cube([r[2] - r[0], r[3] - r[1], r[4] + 1]);
}

// number labels in the margins with a leader to each hole, extruded to height h from z = 0.
// rows: [x, y, number, side, label y]; prefix goes before the number.
module labels(list, prefix, inner, h) {
    for (p = list) {
        left = (p[3] == 0);
        tx = left ? -inner + 1 : board[0] + 4.4;         // text start
        lx = left ? -inner + 6.2 : board[0] + 4.2;       // leader end at the label
        linear_extrude(h) translate([tx, p[4]])
            text(str(prefix, p[2]), size = text_h, font = font, halign = "left", valign = "center");
        hull() {
            translate([lx, p[4], 0]) cylinder(d = leader_w, h = h);
            translate([p[0], p[1], 0]) cylinder(d = leader_w, h = h);
        }
    }
}

// ------------------------------------------------------------------ base, as used (deck top at z = deck_t)
// the lettering, as a solid from z = -1 to z = engrave (the underside face is z = 0) and the BOW on top
module base_lettering() {
    // underside numbers: drawn in the top view (what you see from below with the bow away), then
    // mirrored into the model so they read right from below
    translate([board[0], 0, -1]) mirror([1, 0, 0]) {
        labels(base_points, "T", margin_x, engrave + 1);
        linear_extrude(engrave + 1) translate([board[0] / 2, board[1] + margin_y / 2 + 0.8])
            text("BOW  -  WaveHat A base, from below", size = 1.8, font = font, halign = "center", valign = "center");
    }
    translate([board[0] / 2, board[1] + margin_y / 2, deck_t - engrave]) linear_extrude(engrave + 1)
        text("BOW", size = 3, font = font, halign = "center", valign = "center");
}
module base_holes() {
    pockets(base_pockets, deck_t);
    for (p = base_points) translate([board[0] - p[0], p[1], -1]) cylinder(d = base_hole_d, h = deck_t + 2);
    for (m = mount_holes) translate([m[0], m[1], -1]) {
        cylinder(d = screw_d, h = deck_t + 2);
        cylinder(d = screw_head[0], h = screw_head[1] + 1);
    }
}
module base_body_as_used() { difference() { outline(outer, deck_t); base_holes(); base_lettering(); } }
module base_text_as_used() { difference() { intersection() { outline(outer, deck_t); base_lettering(); } base_holes(); } }
// print orientation: pockets down, underside numbers up
module to_print(z) { translate([0, board[1], z]) rotate([180, 0, 0]) children(); }

// ------------------------------------------------------------------ plate
module plate_lettering() {
    translate([0, 0, plate_t - engrave]) {
        labels(points, "", margin_x, engrave + 1);
        linear_extrude(engrave + 1) translate([board[0] / 2, board[1] + margin_y / 2 + 0.8])
            text("BOW  -  WaveHat A plate, bottom face up", size = 1.8, font = font, halign = "center", valign = "center");
        linear_extrude(engrave + 1) translate([board[0] / 2, -margin_y / 2 - 1.2])
            text("stern (USB-C)", size = 1.8, font = font, halign = "center", valign = "center");
    }
}
module plate_holes() {
    mirror([0, 0, 1]) pockets(plate_pockets, 0);
    for (p = points) translate([p[0], p[1], -1]) cylinder(d = hole_d, h = plate_t + 2);
    for (m = mount_holes) translate([m[0], m[1], -1]) cylinder(d = 2.4, h = plate_t + 2);
}
module plate_body() { difference() { outline(outer, plate_t); plate_holes(); plate_lettering(); } }
module plate_text() { difference() { intersection() { outline(outer, plate_t); plate_lettering(); } plate_holes(); } }

module board_model() {
    color("ForestGreen", 0.6) translate([0, 0, deck_t]) cube([board[0], board[1], board_t]);
}

if (part == "base")            to_print(deck_t) base_body_as_used();
else if (part == "base_body")  to_print(deck_t) base_body_as_used();
else if (part == "base_text")  to_print(deck_t) base_text_as_used();
else if (part == "plate")      plate_body();
else if (part == "plate_body") plate_body();
else if (part == "plate_text") plate_text();
else if (part == "dual_preview") {   // the two colours, both parts in print orientation side by side
    color("DarkSlateGray") to_print(deck_t) base_body_as_used();
    color("Gold") to_print(deck_t) base_text_as_used();
    translate([outer[0] + 10, 0, 0]) { color("DarkSlateGray") plate_body(); color("Gold") plate_text(); }
}
else {
    base_body_as_used();
    base_text_as_used();
    board_model();
    translate([0, 0, deck_t + board_t]) { plate_body(); plate_text(); }
}
