// WaveHat enclosure: 3D-printable, gasketed, rigidly mounted.
// Origin of the WaveHat design: the Takuma box node (efoil workspace, designs/ranges/takuma/wiring.md §3).
//
// Print:  base and lid in ASA (UV-stable) or PETG below decks; gasket and usb_plug in TPU 95A.
//         0.2 mm layers, 5+ perimeters, 40 % gyroid. Base upside-down is not needed: it prints open side up.
// Render: openscad -D 'part="base"' -o wavehat_base.stl wavehat_enclosure.scad   (base | lid | gasket | usb_plug | assembly)
// Hardware: 2 x M2x5 + M2 heat-set inserts (board), 4 x M3x8 + M3 heat-set inserts (lid),
//           4 x M4 screws to the boat, 1 x PG7 cable gland (3-6.5 mm cable).
//
// Coordinates: board corner at the origin, board X across (21 mm), board Y from the mounting end (0)
// to the USB-C end (44). The board's silkscreen Y axis points to the mounting end: that end faces the bow.

part = "assembly";

/* [Board, from projects/wavehat/hardware/DESIGN.md] */
pcb_w = 21.0;
pcb_l = 54.0;
pcb_t = 1.6;
holes = [[2.7, 2.7], [18.3, 2.7]];   // M2 mounting holes
xiao_x0 = 1.6;  xiao_w = 17.8;         // XIAO body across the board
xiao_t = 1.0;                          // XIAO PCB thickness
usb_w = 9.0;  usb_h = 3.3;             // USB-C receptacle

/* [Enclosure] */
wall = 2.4;
floor_t = 2.4;
lid_t = 3.0;
standoff = 5.0;                        // board underside above the floor: room for the lead soldered to the J4 pads
inner_h = 18.0;                        // floor top to rim
side_clr = 3.5;                        // board edge to inner wall (room for the lid bosses)
gland_end = 14.0;                      // room for the gland nut and cable bend at the bow end
usb_end = 1.5;                         // board edge to the inner wall at the USB end (USB overhangs ~1.2)
insert_m3_d = 4.0;  insert_m2_d = 3.2; // heat-set insert holes
screw_m3_d = 3.4;   screw_m4_d = 4.5;
gland_d = 12.5;                        // PG7 cable gland through-hole
gasket_w = 2.0; gasket_t = 1.6;        // printed TPU gasket (or 1.5-2 mm cord in the groove)
$fn = 48;

// derived
xi0 = -side_clr;           xi1 = pcb_w + side_clr;
yi0 = -gland_end;          yi1 = pcb_l + usb_end;
xo0 = xi0 - wall;          xo1 = xi1 + wall;
yo0 = yi0 - wall;          yo1 = yi1 + wall;
H = floor_t + inner_h;                      // base height
pcb_z = floor_t + standoff;                 // board underside
pcb_top = pcb_z + pcb_t;
usb_z = pcb_top + xiao_t + usb_h / 2;       // USB-C centre height
boss_r = 4.0;
corners = [[xi0 - 1.0, yi0 - 1.0], [xi1 + 1.0, yi0 - 1.0], [xi0 - 1.0, yi1 + 1.0], [xi1 + 1.0, yi1 + 1.0]];
ears = [[xo0, yo0 + 12], [xo0, yo1 - 12], [xo1, yo0 + 12], [xo1, yo1 - 12]];

module rounded_box(x0, y0, x1, y1, h, r = 3) {
    hull() for (x = [x0 + r, x1 - r], y = [y0 + r, y1 - r]) translate([x, y, 0]) cylinder(r = r, h = h);
}

module base() {
    difference() {
        union() {
            rounded_box(xo0, yo0, xo1, yo1, H);
            for (c = corners) translate([c[0], c[1], 0]) cylinder(r = boss_r, h = H);
            // mounting ears, 4 mm thick, flush with the bottom
            for (e = ears) translate([e[0], e[1], 0]) hull() {
                cylinder(r = 5, h = 4);
                translate([e[0] < pcb_w / 2 ? -7 : 7, 0, 0]) cylinder(r = 5, h = 4);
            }
        }
        // cavity
        translate([0, 0, floor_t]) rounded_box(xi0, yi0, xi1, yi1, H, 1.5);
        // lid screw inserts
        for (c = corners) translate([c[0], c[1], H - 8]) cylinder(d = insert_m3_d, h = 9);
        // ear holes, slotted 2 mm so the box can be squared to the boat's axis
        for (e = ears) translate([e[0] + (e[0] < pcb_w / 2 ? -6 : 6), e[1], -1]) hull() {
            translate([0, -1, 0]) cylinder(d = screw_m4_d, h = 6);
            translate([0, 1, 0]) cylinder(d = screw_m4_d, h = 6);
        }
        // PG7 gland at the bow end, centred on the board
        translate([pcb_w / 2, yo0 - 1, floor_t + inner_h / 2]) rotate([-90, 0, 0]) cylinder(d = gland_d, h = wall + 2);
        // USB-C opening at the stern end, lined up with the XIAO's connector
        translate([xiao_x0 + xiao_w / 2, yi1 - 1, usb_z]) rotate([-90, 0, 0])
            hull() for (dx = [-(usb_w + 2) / 2 + 2, (usb_w + 2) / 2 - 2]) translate([dx, 0, 0]) cylinder(r = 2.5, h = wall + 2);
        // "BOW" on the outside of the gland end
        translate([pcb_w / 2, yo0 + 0.6, 1.0]) rotate([90, 0, 0]) linear_extrude(1)
            text("BOW", size = 3, halign = "center", font = "Liberation Sans:style=Bold");
    }
    // board standoffs with M2 inserts
    for (h = holes) translate([h[0], h[1], floor_t - 0.01]) difference() {
        cylinder(d = 5.6, h = standoff);
        translate([0, 0, standoff - 4.5]) cylinder(d = insert_m2_d, h = 5);
    }
    // support rail under the USB end: the board has holes at one end only, so the far end rests here
    translate([3, pcb_l - 5, floor_t - 0.01]) cube([pcb_w - 6, 4, standoff]);
}

module lid() {
    difference() {
        union() {
            rounded_box(xo0, yo0, xo1, yo1, lid_t);
            for (c = corners) translate([c[0], c[1], 0]) cylinder(r = boss_r, h = lid_t);
        }
        for (c = corners) translate([c[0], c[1], -1]) {
            cylinder(d = screw_m3_d, h = lid_t + 2);
            translate([0, 0, lid_t - 1.2]) cylinder(d = 6.2, h = 2);       // shallow counterbore
        }
        // gasket groove on the underside, on the wall centreline
        translate([0, 0, -0.01]) difference() {
            rounded_box(xi0 - wall / 2 - gasket_w / 2, yi0 - wall / 2 - gasket_w / 2, xi1 + wall / 2 + gasket_w / 2, yi1 + wall / 2 + gasket_w / 2, 1.0, 2.5);
            translate([0, 0, -1]) rounded_box(xi0 - wall / 2 + gasket_w / 2, yi0 - wall / 2 + gasket_w / 2, xi1 + wall / 2 - gasket_w / 2, yi1 + wall / 2 - gasket_w / 2, 3, 1.5);
        }
        // top marking: name and bow arrow
        translate([pcb_w / 2, (yo0 + yo1) / 2 + 6, lid_t - 0.6]) linear_extrude(1)
            text("WaveHat", size = 4.2, halign = "center", font = "Liberation Sans:style=Bold");
        translate([pcb_w / 2, yo0 + 10, lid_t - 0.6]) linear_extrude(1) polygon([[-5, 0], [5, 0], [0, -7]]);
        translate([pcb_w / 2, yo0 + 12.5, lid_t - 0.6]) linear_extrude(1)
            text("BOW", size = 3.2, halign = "center", font = "Liberation Sans:style=Bold");
    }
    // fingers that hold the USB end of the board down on its rail (TPU pad or a dab of silicone on the tip)
    finger_len = H - pcb_top - 0.2;
    for (x = [0.6, pcb_w - 0.6]) translate([x - 0.6, pcb_l - 4.5, -finger_len]) cube([1.2, 3, finger_len + 0.01]);
}

module gasket() {
    difference() {
        rounded_box(xi0 - wall / 2 - gasket_w / 2 + 0.15, yi0 - wall / 2 - gasket_w / 2 + 0.15, xi1 + wall / 2 + gasket_w / 2 - 0.15, yi1 + wall / 2 + gasket_w / 2 - 0.15, gasket_t, 2.5);
        translate([0, 0, -1]) rounded_box(xi0 - wall / 2 + gasket_w / 2 - 0.15, yi0 - wall / 2 + gasket_w / 2 - 0.15, xi1 + wall / 2 - gasket_w / 2 + 0.15, yi1 + wall / 2 - gasket_w / 2 + 0.15, gasket_t + 2, 1.5);
    }
}

module usb_plug() {
    // TPU plug: flange outside, a ribbed stem that presses into the USB opening
    hull() for (dx = [-(usb_w + 6) / 2 + 3, (usb_w + 6) / 2 - 3]) translate([dx, 0, 0]) cylinder(r = 3.5, h = 1.6);
    translate([0, 0, 1.6]) hull() for (dx = [-(usb_w + 2) / 2 + 2.6, (usb_w + 2) / 2 - 2.6]) translate([dx, 0, 0]) cylinder(r = 2.6, h = wall);
    translate([(usb_w + 6) / 2 + 1, -1.5, 0]) cube([8, 3, 1.2]);           // pull tab
}

module board_ghost() {
    color("darkgreen", 0.8) translate([0, 0, pcb_z]) cube([pcb_w, pcb_l, pcb_t]);
    color("dimgray", 0.9) translate([xiao_x0, pcb_l - 21, pcb_top]) cube([xiao_w, 21, xiao_t + 2.5]);
    color("silver") translate([xiao_x0 + xiao_w / 2 - usb_w / 2, pcb_l - 7 + 1.2, pcb_top + xiao_t]) cube([usb_w, 7, usb_h]);
}

if (part == "base") base();
else if (part == "lid") translate([0, 0, lid_t]) mirror([0, 0, 1]) lid();      // printed upside down: flat top on the bed
else if (part == "gasket") gasket();
else if (part == "usb_plug") usb_plug();
else {
    color("lightsteelblue") base();
    board_ghost();
    color("lightsteelblue", 0.35) translate([0, 0, H + 8]) lid();
}
