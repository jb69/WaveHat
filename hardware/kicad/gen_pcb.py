#!/usr/bin/env python3
"""Build the WaveHat PCB from wavehat_design.py with KiCad's pcbnew module.

    PY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3
    $PY gen_pcb.py place      # outline, footprints, nets, keep-outs, silkscreen, rules; writes wavehat.dsn
    java -jar freerouting.jar -de wavehat.dsn -do wavehat.ses -mp 100
    $PY gen_pcb.py import     # routes from wavehat.ses, GND pours on both layers, stitching vias, fill, save

Every net, GND included, is routed as tracks first; the pours then make GND solid on both layers.
Design rules and net classes are written into wavehat.kicad_pro, where KiCad keeps them.
Footprints link to the schematic symbols by UUID, so "Update PCB from Schematic" works on the result.
"""
import json
import os
import sys
import uuid

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import wavehat_design as D  # noqa: E402
import gen_schematic as G  # noqa: E402  (symbol pin names, for KiCad's "unconnected-(...)" nets)

FPDIR = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints"
NS = uuid.UUID("6f0c4d8e-6a1d-4f63-9a7e-7a0e5d0b2a11")    # same namespace as gen_schematic.py
OX, OY = 100.0, 100.0                                   # board origin on the page (mm)
PCB = os.path.join(HERE, "wavehat.kicad_pcb")
PRO = os.path.join(HERE, "wavehat.kicad_pro")
MM = pcbnew.FromMM

RULES = dict(clearance=0.15, track=0.15, via=0.6, drill=0.3, power_track=0.4, edge=0.3)
ROUTE_CLEARANCE = 0.17   # Freerouting routes with a little margin, so pad-entry segments it thins can be widened
                         # back to the 0.15 mm minimum track without breaking the 0.15 mm clearance


def uid(*key):
    return str(uuid.uuid5(NS, "/".join(map(str, key))))


def pt(x, y):
    return pcbnew.VECTOR2I(MM(OX + x), MM(OY + y))


def lib_path(nick):
    return os.path.join(HERE, "lib", "wavehat.pretty") if nick == "wavehat" else os.path.join(FPDIR, nick + ".pretty")


def add_line(board, layer, a, b, w=0.1):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(pt(*a))
    s.SetEnd(pt(*b))
    s.SetLayer(layer)
    s.SetWidth(MM(w))
    board.Add(s)


def add_arc(board, layer, c, start, deg, w=0.1):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_ARC)
    s.SetCenter(pt(*c))
    s.SetStart(pt(*start))
    s.SetArcAngleAndEnd(pcbnew.EDA_ANGLE(deg, pcbnew.DEGREES_T), True)
    s.SetLayer(layer)
    s.SetWidth(MM(w))
    board.Add(s)


def add_text(board, layer, text, x, y, size=0.8, rot=0, mirror=False):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(text)
    t.SetPosition(pt(x, y))
    t.SetLayer(layer)
    t.SetTextSize(pcbnew.VECTOR2I(MM(size), MM(size)))
    t.SetTextThickness(MM(max(0.1, size * 0.15)))
    t.SetTextAngleDegrees(rot)
    if mirror:
        t.SetMirrored(True)
    board.Add(t)


def rect(cx, cy, hw, hh):
    return [(cx - hw, cy - hh), (cx + hw, cy - hh), (cx + hw, cy + hh), (cx - hw, cy + hh)]


def rule_area(board, poly, name, tracks=True, vias=True, pour=True, layers=None):
    z = pcbnew.ZONE(board)
    ls = pcbnew.LSET()
    for layer in layers or (pcbnew.F_Cu, pcbnew.B_Cu):
        ls.AddLayer(layer)
    z.SetLayerSet(ls)
    o = z.Outline()
    o.NewOutline()
    for x, y in poly:
        o.Append(MM(OX + x), MM(OY + y))
    z.SetIsRuleArea(True)
    z.SetDoNotAllowTracks(tracks)
    z.SetDoNotAllowVias(vias)
    z.SetDoNotAllowZoneFills(pour)
    z.SetDoNotAllowPads(False)
    z.SetDoNotAllowFootprints(False)
    z.SetZoneName(name)
    board.Add(z)


def gnd_pour(board, net, layer):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    o = z.Outline()
    o.NewOutline()
    for x, y in rect(D.BOARD_W / 2, D.BOARD_L / 2, D.BOARD_W / 2 - 0.3, D.BOARD_L / 2 - 0.3):
        o.Append(MM(OX + x), MM(OY + y))
    z.SetNet(net)
    z.SetMinThickness(MM(0.2))
    z.SetLocalClearance(MM(0.25))
    z.SetThermalReliefGap(MM(0.3))
    z.SetThermalReliefSpokeWidth(MM(0.3))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    try:
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    except Exception:
        pass
    z.SetZoneName("GND " + ("top" if layer == pcbnew.F_Cu else "bottom"))
    board.Add(z)


def flip_to_back(fp):
    try:
        fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    except Exception:
        fp.Flip(fp.GetPosition(), True)


def write_project_rules():
    """KiCad keeps design rules and net classes in the .kicad_pro; set them there on every run."""
    d = json.load(open(PRO)) if os.path.exists(PRO) else {"meta": {"filename": "wavehat.kicad_pro", "version": 1}}
    r = d.setdefault("board", {}).setdefault("design_settings", {}).setdefault("rules", {})
    r.update({"min_clearance": RULES["clearance"], "min_track_width": RULES["track"], "min_via_diameter": 0.5,
              "min_through_hole_diameter": 0.3, "min_copper_edge_clearance": RULES["edge"], "min_hole_clearance": 0.25,
              "min_via_annular_width": 0.1, "min_text_height": 0.6, "min_text_thickness": 0.08,
              "min_resolved_spokes": 1})

    def nc(name, track, clr, via, drill):
        return {"name": name, "clearance": clr, "track_width": track, "via_diameter": via, "via_drill": drill,
                "microvia_diameter": 0.3, "microvia_drill": 0.1, "diff_pair_width": 0.2, "diff_pair_gap": 0.25,
                "diff_pair_via_gap": 0.25, "wire_width": 6, "bus_width": 12, "line_style": 0,
                "pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)",
                "priority": 2147483647 if name == "Default" else 0}
    ns = d.setdefault("net_settings", {})
    ns["classes"] = [nc("Default", RULES["track"], RULES["clearance"], RULES["via"], RULES["drill"]),
                     nc("Power", RULES["power_track"], RULES["clearance"], 0.8, 0.4)]
    ns["netclass_patterns"] = [{"netclass": "Power", "pattern": "/" + n} for n in sorted(D.POWER_NETS)]
    ns["netclass_assignments"] = None
    json.dump(d, open(PRO, "w"), indent=2)


def place():
    board = pcbnew.NewBoard(PCB)
    W, L, r = D.BOARD_W, D.BOARD_L, 1.2
    E = pcbnew.Edge_Cuts
    add_line(board, E, (r, 0), (W - r, 0))
    add_line(board, E, (W, r), (W, L - r))
    add_line(board, E, (W - r, L), (r, L))
    add_line(board, E, (0, L - r), (0, r))
    add_arc(board, E, (r, r), (0, r), 90)
    add_arc(board, E, (W - r, r), (W - r, 0), 90)
    add_arc(board, E, (W - r, L - r), (W, L - r), 90)
    add_arc(board, E, (r, L - r), (r, L), 90)

    tb = board.GetTitleBlock()
    tb.SetTitle("WaveHat: sea-state sensor and CAN node for the Seeed XIAO")
    tb.SetRevision("A")
    tb.SetDate("2026-10-20")
    tb.SetComment(0, "Generated from wavehat_design.py by gen_pcb.py")
    tb.SetComment(1, "2 layers, 1.6 mm FR-4, ENIG, 1 oz; parts on both sides (bottom: U5 C8 C9 R9-R12)")
    # drill / place origin at the board's lower-left corner: Gerbers, drill and pick-and-place all read from there
    board.GetDesignSettings().SetAuxOrigin(pt(0, L))

    nets = {}
    for p in D.P.values():
        for n in p["pins"].values():
            if n and n not in nets:
                ni = pcbnew.NETINFO_ITEM(board, "/" + n)       # local labels on the root sheet are "/NAME"
                board.Add(ni)
                nets[n] = ni

    for ref, p in sorted(D.P.items()):
        nick, name = p["fp"].split(":")
        fp = pcbnew.FootprintLoad(lib_path(nick), name)
        if fp is None:
            raise RuntimeError("footprint not found: " + p["fp"])
        fp.SetFPID(pcbnew.LIB_ID(nick, name))
        fp.SetReference(ref)
        fp.SetValue(p["value"])
        fp.SetPath(pcbnew.KIID_PATH("/" + uid("s", ref)))
        x, y, rot, side = p["pcb"]
        fp.SetPosition(pt(x, y))
        fp.SetOrientationDegrees(rot)
        board.Add(fp)
        if side in ("B", "BA"):
            flip_to_back(fp)
        if side == "B":                        # bare copper: nothing for the assembler to place
            fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_EXCLUDE_FROM_POS_FILES | pcbnew.FP_EXCLUDE_FROM_BOM)
        if p["dnp"]:
            try:
                fp.SetDNP(True)
            except Exception:
                pass
        names = G.pin_names(p["lib_id"]) if p["pins"] else {}
        for pad in fp.Pads():
            num = pad.GetNumber()
            if num not in p["pins"]:
                continue                       # mechanical pads (connector MP tabs) stay unconnected
            n = p["pins"][num]
            if n:
                pad.SetNet(nets[n])
            else:                              # no-connect pin: same net name the schematic gives it
                nm = "unconnected-(%s-%s-Pad%s)" % (ref, names.get(num, "").replace("/", "{slash}"), num)
                ni = pcbnew.NETINFO_ITEM(board, nm)
                board.Add(ni)
                pad.SetNet(ni)
        try:
            fp.SetField("MPN", p["mpn"])
            f = fp.GetField("MPN")
            f.SetVisible(False)
            f.SetLayer(pcbnew.B_Fab if side != "F" else pcbnew.F_Fab)
        except Exception as e:
            print("MPN field not set on %s: %s" % (ref, e))
        small = any(k in p["fp"] for k in ("0402", "0603", "0805", "SOT-23", "LGA-14", "Fiducial"))
        if small:
            fp.Reference().SetLayer(pcbnew.B_Fab if side != "F" else pcbnew.F_Fab)
            fp.Reference().SetTextSize(pcbnew.VECTOR2I(MM(0.45), MM(0.45)))
            fp.Reference().SetTextThickness(MM(0.07))
        fp.Value().SetVisible(False)

    # keep-outs
    ux, uy = D.P["U1"]["pcb"][0], D.P["U1"]["pcb"][1]
    rule_area(board, rect(ux, uy, 0.75, 0.5), "IMU: nothing under the package")
    for f in sorted(r for r in D.P if r.startswith("FID")):
        fx, fy, _, fside = D.P[f]["pcb"]
        rule_area(board, rect(fx, fy, 1.4, 1.4), "fiducial clearance",
                  layers=(pcbnew.F_Cu,) if fside == "F" else (pcbnew.B_Cu,))
    xo, yo = D.P["U4"]["pcb"][0], D.XIAO_TOP
    under = [(4.445, -10.882, 2.5, 1.1), (4.445, -12.787, 2.5, 1.1),   # C3 / S3 battery pads
             (7.11, -4.968, 2.5, 1.1), (9.65, -4.968, 2.5, 1.1),      # C6 battery pads
             (10.01, -8.5, 2.75, 2.5),                               # S3 centre pad
             (8.89, -15.3, 4.2, 9.2)]                                # JTAG / boot pads (all three)
    for fx, fy, w, h in under:
        rule_area(board, rect(xo - fx, yo - fy, w / 2 + 0.6, h / 2 + 0.6), "XIAO underside pad: no vias",
                  tracks=False, vias=True, pour=False)

    S, SB = pcbnew.F_SilkS, pcbnew.B_SilkS
    add_text(board, S, "WaveHat A", 10.5, 8.7, 0.8)
    ax, ay = 13.6, 7.8                       # IMU axes: Y points to the mounting end, which faces the bow
    for a, b in (((ax, ay), (ax, ay - 2.2)), ((ax, ay - 2.2), (ax - 0.5, ay - 1.6)), ((ax, ay - 2.2), (ax + 0.5, ay - 1.6)),
                 ((ax, ay), (ax + 2.2, ay)), ((ax + 2.2, ay), (ax + 1.6, ay - 0.5)), ((ax + 2.2, ay), (ax + 1.6, ay + 0.5))):
        add_line(board, S, a, b, 0.15)
    add_text(board, S, "Y bow", ax, ay - 2.9, 0.6)
    add_text(board, S, "X", ax + 2.8, ay, 0.6)
    add_text(board, SB, "WaveHat rev A", 10.5, 3.0, 0.8, mirror=True)
    add_text(board, SB, "2026-10, Takuma node", 10.5, 4.4, 0.6, mirror=True)
    add_text(board, SB, "JP3: 0x6B (default) / 0x6A", 10.5, 9.3, 0.6, mirror=True)
    add_text(board, SB, "JP4/5: INT to D2/D3", 14.4, 20.0, 0.6, mirror=True)
    add_text(board, SB, "JP6: CAN 120R", 10.5, 16.2, 0.6, mirror=True)
    add_text(board, SB, "JP7: CS", 16.6, 41.8, 0.6, mirror=True)
    add_text(board, SB, "log storage", 10.5, 43.7, 0.6, mirror=True)
    add_text(board, SB, "NMEA 2000 / 5-30 V: SH S(+) C(GND) H L", 10.5, 29.0, 0.6, mirror=True)

    pcbnew.SaveBoard(PCB, board)
    write_project_rules()
    board = pcbnew.LoadBoard(PCB)          # reload so the exporter sees the project's rules
    dsn = os.path.join(HERE, "wavehat.dsn")
    ok = pcbnew.ExportSpecctraDSN(board, dsn)
    # the router's copy of the rules carries the extra margin; KiCad's own (and DRC's) stay at the minimum
    um = "(clearance %d)" % round(RULES["clearance"] * 1000)
    text = open(dsn).read()
    open(dsn, "w").write(text.replace(um, "(clearance %d)" % round(ROUTE_CLEARANCE * 1000)))
    print("placed %d footprints, %d nets; rules %s; DSN export: %s" % (len(D.P), len(nets), RULES, ok))


def stitching_vias(board, gnd, pitch=1.6):
    """GND vias on a grid wherever they clear every pad, track and other via, and stay off parts and keep-outs."""
    keepouts = [z for z in board.Zones() if z.GetIsRuleArea() and z.GetDoNotAllowVias()]
    courtyards = []
    for fp in board.GetFootprints():
        if fp.GetReference() == "U4":
            continue
        cy = fp.GetCourtyard(pcbnew.B_CrtYd if fp.IsFlipped() else pcbnew.F_CrtYd)
        if cy.OutlineCount():
            courtyards.append(cy)
    pads = [p for fp in board.GetFootprints() for p in fp.Pads()]
    items = list(board.GetTracks())
    margin = MM(RULES["via"] / 2 + RULES["clearance"] + 0.05)
    added = 0
    y = 1.0
    while y < D.BOARD_L - 0.9:
        x = 0.9
        while x < D.BOARD_W - 0.8:
            p = pt(x, y)
            ok = not any(k.Outline().Collide(p, MM(RULES["via"] / 2 + 0.05)) for k in keepouts)
            ok = ok and not any(c.Contains(p) for c in courtyards)
            ok = ok and not any(pd.HitTest(p, margin) for pd in pads)
            ok = ok and not any(t.HitTest(p, margin) for t in items if t.GetNetname() != "/GND" or t.GetClass() == "PCB_VIA")
            if ok:
                v = pcbnew.PCB_VIA(board)
                v.SetPosition(p)
                v.SetWidth(MM(RULES["via"]))
                v.SetDrill(MM(RULES["drill"]))
                v.SetNet(gnd)
                board.Add(v)
                items.append(v)
                added += 1
            x += pitch
        y += pitch
    return added


def do_import():
    board = pcbnew.LoadBoard(PCB)
    for t in list(board.GetTracks()):      # re-import onto a clean board
        board.Remove(t)
    for z in [z for z in board.Zones() if not z.GetIsRuleArea()]:
        board.Remove(z)
    ok = pcbnew.ImportSpecctraSES(board, os.path.join(HERE, "wavehat.ses"))
    gnd = board.FindNet("/GND")
    # Freerouting may drop GND vias into via keep-outs it did not see; the pours carry GND there instead
    keep = [z for z in board.Zones() if z.GetIsRuleArea() and z.GetDoNotAllowVias()]
    dropped = 0
    for t in list(board.GetTracks()):
        if t.GetClass() == "PCB_VIA" and any(z.Outline().Collide(t.GetPosition(), t.GetWidth(pcbnew.F_Cu) // 2) for z in keep):
            board.Remove(t)
            dropped += 1
    # Freerouting thins a few pad-entry segments (to ~0.11 mm) to squeeze between fine-pitch pads; bring them
    # back to the 0.15 mm minimum (DRC then confirms the clearances still hold)
    widened = 0
    for t in board.GetTracks():
        if t.GetClass() != "PCB_VIA" and t.GetWidth() < MM(RULES["track"]):
            t.SetWidth(MM(RULES["track"]))
            widened += 1
    added = stitching_vias(board, gnd)
    gnd_pour(board, gnd, pcbnew.F_Cu)
    gnd_pour(board, gnd, pcbnew.B_Cu)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    # a stitching via is only useful where the pour reaches it on both layers; drop the ones in islands
    pours = [z for z in board.Zones() if not z.GetIsRuleArea()]
    island = [v for v in board.GetTracks() if v.GetClass() == "PCB_VIA" and v.GetNetname() == "/GND"
              and getattr(v, "stitch", False) is False and not all(
                  any(z.GetFilledPolysList(layer).Contains(v.GetPosition()) for z in pours if z.GetLayer() == layer)
                  for layer in (pcbnew.F_Cu, pcbnew.B_Cu))
              and not any(t.GetClass() != "PCB_VIA" and t.GetNetname() == "/GND" and t.HitTest(v.GetPosition(), 1)
                          for t in board.GetTracks())]
    for v in island:
        board.Remove(v)
    if island:
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    added -= len(island)
    board.BuildConnectivity()
    pcbnew.SaveBoard(PCB, board)
    tracks = list(board.GetTracks())
    vias = [t for t in tracks if t.GetClass() == "PCB_VIA"]
    print("SES import: %s; %d segments (%d widened to %.2f mm), %d vias (%d stitching, %d removed from keep-outs); "
          "GND poured both layers" % (ok, len(tracks) - len(vias), widened, RULES["track"], len(vias), added, dropped))


if __name__ == "__main__":
    {"place": place, "import": do_import}[sys.argv[1] if len(sys.argv) > 1 else "place"]()
