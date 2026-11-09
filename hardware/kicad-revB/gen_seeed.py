#!/usr/bin/env python3
"""Package the WaveHat for Seeed Fusion: bare boards (Fusion PCB) or assembled boards (Fusion PCBA).

    python3 -I gen_seeed.py          (after run_pipeline.sh has written fab/)

Writes fab/seeed/:
  wavehat-seeed-gerbers.zip      Gerbers with the Protel names Seeed lists (GTL GBL GTS GBS GTO GBO GTP GBP GKO)
                                 and the Excellon drill as .TXT, origin at the board's lower-left corner
  wavehat-seeed-bom-*.csv        Seeed's BOM template (Designator, MPN or Seeed SKU, Qty, Link), one per option:
                                 no XIAO, or the XIAO C3 / C6 / S3 from Seeed's Open Parts Library placed by Seeed
  wavehat-seeed-cpl.csv          pick-and-place, both sides, the parts in the BOM only
  wavehat-assembly-top.pdf, wavehat-assembly-bottom.pdf    assembly drawings (bottom seen from below)
  wavehat-seeed-assembly.zip     for the "Upload Assembly Instructions" box: CPL, assembly drawings, renders, notes
  wavehat-seeed-pcba-*.zip       everything for one PCBA option in one flat archive (Gerbers, BOM, CPL, drawings)
  ORDER.md                       what to pick on the order forms
  no-storage/                    the same files for top-side-only assembly, the bottom-side log storage left off
"""
import csv
import os
import re
import shutil
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import wavehat_design as D  # noqa: E402

FAB = os.path.join(HERE, "fab")
OUT = os.path.join(FAB, "seeed")
K = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"

GERBERS = {  # KiCad file -> Seeed's name
    "wavehat-F_Cu.gtl": "wavehat.GTL", "wavehat-B_Cu.gbl": "wavehat.GBL",
    "wavehat-F_Mask.gts": "wavehat.GTS", "wavehat-B_Mask.gbs": "wavehat.GBS",
    "wavehat-F_Silkscreen.gto": "wavehat.GTO", "wavehat-B_Silkscreen.gbo": "wavehat.GBO",
    "wavehat-F_Paste.gtp": "wavehat.GTP", "wavehat-B_Paste.gbp": "wavehat.GBP",
    "wavehat-Edge_Cuts.gm1": "wavehat.GKO", "wavehat.drl": "wavehat.TXT",
}

XIAO = {"c3": ("113991054", "Seeed Studio XIAO ESP32C3"),
        "c6": ("113991254", "Seeed Studio XIAO ESP32C6"),
        "s3": ("113991114", "Seeed Studio XIAO ESP32S3")}

LINKS = {"ZDSD02GLGEAG": "https://www.lcsc.com/product-detail/C2875853.html",
         "LMR51606YDBVR": "https://www.ti.com/product/LMR51606/part-details/LMR51606YDBVR",
         "1812L050/60MR": "https://www.lcsc.com/product-detail/C87383.html",
         "SM04B-GHS-TB(LF)(SN)": "https://www.digikey.com/en/products/detail/jst-sales-america-inc/SM04B-GHS-TB/807788",
         "FNR4020S150MT": "https://www.lcsc.com/product-detail/C167837.html",
         "SM04B-SRSS-TB(LF)(SN)": "https://www.lcsc.com/search?q=SM04B-SRSS-TB(LF)(SN)"}

NOT_PARTS = ("Jumper:", "TestPoint:", "MountingHole:", "Fiducial:", "wavehat:N2K")

MAKERS = [("GRM", "Murata"), ("RC0402", "Yageo"), ("SS1", "any (SMA Schottky)"), ("SMBJ", "any (SMB TVS)"),
          ("1812L", "Littelfuse"), ("SM04B", "JST"), ("SM10B", "JST"), ("FNR4020", "Changjiang (cjiang)"), ("LSM6DSO", "STMicroelectronics"),
          ("LMR51606", "Texas Instruments"), ("SN65HVD230", "Texas Instruments"), ("ZDSD", "Zetta")]

DESCR = {"Device:C": "Capacitor, ceramic MLCC", "Device:R": "Resistor, thick film 1 %", "Device:D_Schottky": "Diode, Schottky",
         "Device:D_Zener": "TVS diode, unidirectional", "Device:Polyfuse": "PTC resettable fuse", "Device:L": "Inductor, shielded",
         "Connector_Generic:Conn_01x04": "Connector, 4-pin SMD right angle", "wavehat:LSM6DSO": "IMU, 6-axis accelerometer + gyro",
         "wavehat:LMR51606": "Buck converter 4-65 V, 0.6 A", "Interface_CAN_LIN:SN65HVD230": "CAN transceiver, 3.3 V",
         "wavehat:SD_NAND": "SD NAND flash 2 Gbit (256 MB), SLC, SD/SPI"}

FAB_NOTES = """WaveHat rev B (2026-10): fabrication notes. Via plating: electroless copper (not conductive adhesive); every signal via is twinned.
Board: 21.00 x 54.00 mm (+-0.2 mm), outline in wavehat.GKO, corner radius 1.2 mm
Layers: 2; FR-4 TG130 or better; finished thickness 1.6 mm (+-10 %); copper 1 oz both layers
Surface finish: ENIG (two LGA parts: U1 LSM6DSO, U5 SD NAND)
Solder mask: both sides, any colour; minimum solder mask dam 0.1 mm (keeps mask between the IMU's 0.5 mm-pitch pads);
            silkscreen both sides (version and date on the bottom)
Minimum track / space: 0.15 / 0.15 mm (6/6 mil); minimum drill 0.3 mm (vias 0.6 mm pad, tented); copper to edge 0.3 mm
Holes: 2 plated M2 mounting holes (2.2 mm); no castellated holes, no slots, no V-cuts, no impedance control
Origin: all files (Gerbers, drill, pick and place) measure from the board's lower-left corner
Files: wavehat.GTL/GBL copper, GTS/GBS mask, GTO/GBO silkscreen, GTP/GBP paste, GKO outline, TXT Excellon drill
Assembly: see the assembly instructions zip (pick and place, drawings, BOM). The same Gerbers serve every build;
          only what is placed differs (full build: both sides; no-storage build: top side only).
"""


def maker(mpn):
    return next((m for prefix, m in MAKERS if mpn.startswith(prefix)), "")


def side_of(refs):
    """'Top', 'Bottom', or 'Top: C1,C3 / Bottom: C8' for a group on both sides."""
    top = [r for r in sorted(refs, key=natural) if D.P[r]["pcb"][3] == "F"]
    bot = [r for r in sorted(refs, key=natural) if D.P[r]["pcb"][3] == "BA"]
    if top and bot:
        return "Top: %s / Bottom: %s" % (",".join(top), ",".join(bot))
    return "Bottom" if bot else "Top"


def write_detailed_bom(path):
    """The fuller BOM Seeed's Open Manufacturing whitepaper asks for (manufacturer, description, value, package)."""
    groups = {}
    for ref, p in assembled().items():
        groups.setdefault(p["mpn"], []).append(ref)
    rows = []
    for mpn, refs in groups.items():
        p = D.P[refs[0]]
        rows.append([",".join(sorted(refs, key=natural)), len(refs), p["value"], DESCR.get(p["lib_id"], ""),
                     p["fp"].split(":")[1], maker(mpn), mpn,
                     side_of(refs), LINKS.get(mpn, "")])
    rows.sort(key=lambda r: natural(r[0].split(",")[0]))
    rows.append(["U4", 1, "XIAO ESP32C3 / C6 / S3", "MCU module (Seeed Open Parts Library), castellated SMD",
                 "XIAO 14-pad", "Seeed Studio", "113991054 / 113991254 / 113991114", "Top", "optional: per BOM option"])
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Designator", "Qty", "Value", "Description", "Package", "Manufacturer", "MPN or Seeed SKU", "Side", "Link"])
        w.writerows(rows)


def natural(ref):
    m = re.match(r"([A-Z]+)(\d+)", ref)
    return (m.group(1), int(m.group(2))) if m else (ref, 0)


STORAGE = True   # False builds the no-storage variant: top side only, the bottom-side log storage left off


def assembled():
    """{ref: part} for everything the assembler buys and places, the XIAO excepted."""
    sides = ("F", "BA") if STORAGE else ("F",)
    return {r: p for r, p in D.P.items()
            if r != "U4" and p["pcb"][3] in sides and not p["dnp"] and not p["fp"].startswith(NOT_PARTS)}


def bom_rows(xiao=None):
    groups = {}
    for ref, p in assembled().items():
        groups.setdefault(p["mpn"], []).append(ref)
    rows = [(",".join(sorted(refs, key=natural)), mpn, len(refs), LINKS.get(mpn, ""))
            for mpn, refs in groups.items()]
    if xiao:
        sku, name = XIAO[xiao]
        rows.append(("U4", sku, 1, "Seeed Open Parts Library: " + name))
    return sorted(rows, key=lambda r: natural(r[0].split(",")[0]))


def write_bom(path, rows):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Designator", "Manufacturer Part Number or Seeed SKU", "Qty", "Link"])
        w.writerows(rows)


def write_cpl(path):
    """One file, both sides, only the parts in the BOM (and the XIAO, used when it is ordered)."""
    keep = set(assembled()) | {"U4"}
    rows = []
    for side_file, layer in (("wavehat-cpl-top.csv", "Top"), ("wavehat-cpl-bottom.csv", "Bottom")):
        for r in csv.DictReader(open(os.path.join(FAB, side_file))):
            if r["Ref"] in keep:
                rows.append([r["Ref"], r["Val"], r["Package"], r["PosX"], r["PosY"], layer, r["Rot"]])
    rows.sort(key=lambda r: natural(r[0]))
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Designator", "Comment", "Footprint", "Mid X", "Mid Y", "Layer", "Rotation"])
        w.writerows(rows)
    return rows


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    cpl = os.path.join(OUT, "wavehat-seeed-cpl.csv")
    placed = write_cpl(cpl)
    notes = os.path.join(OUT, "wavehat-fab-notes.txt")
    open(notes, "w").write(FAB_NOTES)
    dbom = os.path.join(OUT, "wavehat-bom-detailed.csv")
    write_detailed_bom(dbom)
    # one Gerber package for every build: the board doesn't change, only what is placed on it
    gz = os.path.join(OUT, "wavehat-seeed-gerbers.zip")
    with zipfile.ZipFile(gz, "w", zipfile.ZIP_DEFLATED) as z:
        for src, dst in GERBERS.items():
            z.write(os.path.join(FAB, "gerbers", src), dst)
        z.write(notes, "wavehat-fab-notes.txt")
    for opt in ("noxiao", "c3", "c6", "s3"):
        write_bom(os.path.join(OUT, "wavehat-seeed-bom-%s.csv" % opt), bom_rows(None if opt == "noxiao" else opt))
    pcb = os.path.join(HERE, "wavehat.kicad_pcb")
    for name, layers, extra in (("top", "F.Fab,F.SilkS,Edge.Cuts", []),
                                ("bottom", "B.Fab,B.SilkS,Edge.Cuts", ["--mirror"])):
        subprocess.run([K, "pcb", "export", "pdf", "--mode-single", "--sp", "--scale", "0", "--layers", layers, "--ibt",
                        "-o", os.path.join(OUT, "wavehat-assembly-%s.pdf" % name)] + extra + [pcb],
                       check=True, capture_output=True)
    for opt in ("noxiao", "c3", "c6", "s3"):
        with zipfile.ZipFile(os.path.join(OUT, "wavehat-seeed-pcba-%s.zip" % opt), "w", zipfile.ZIP_DEFLATED) as z:
            for src, dst in GERBERS.items():          # flat: Gerbers at the top level, no zip inside a zip
                z.write(os.path.join(FAB, "gerbers", src), dst)
            z.write(os.path.join(OUT, "wavehat-seeed-bom-%s.csv" % opt), "wavehat-seeed-bom-%s.csv" % opt)
            z.write(cpl, "wavehat-seeed-cpl.csv")
            for s in ("top", "bottom"):
                z.write(os.path.join(OUT, "wavehat-assembly-%s.pdf" % s), "wavehat-assembly-%s.pdf" % s)
            z.write(os.path.join(HERE, "ORDER-SEEED.md"), "ORDER.md")
    shutil.copy(os.path.join(HERE, "ORDER-SEEED.md"), os.path.join(OUT, "ORDER.md"))
    # for the form's "Upload Assembly Instructions" box: pick and place, assembly drawings, renders, notes
    with zipfile.ZipFile(os.path.join(OUT, "wavehat-seeed-assembly.zip"), "w", zipfile.ZIP_DEFLATED) as z:
        z.write(cpl, "wavehat-seeed-cpl.csv")
        z.write(dbom, "wavehat-bom-detailed.csv")
        z.write(notes, "wavehat-fab-notes.txt")
        for s in ("top", "bottom"):
            z.write(os.path.join(OUT, "wavehat-assembly-%s.pdf" % s), "wavehat-assembly-%s.pdf" % s)
            z.write(os.path.join(HERE, "img", "wavehat-3d-%s.png" % s), "wavehat-3d-%s.png" % s)
        z.write(os.path.join(HERE, "img", "wavehat-3d-angle.png"), "wavehat-3d-angle.png")
        z.write(os.path.join(HERE, "ORDER-SEEED.md"), "ORDER.md")

    parts = assembled()
    top = sorted((r for r, p in parts.items() if p["pcb"][3] == "F"), key=natural)
    bot = sorted((r for r, p in parts.items() if p["pcb"][3] == "BA"), key=natural)
    pads = 0
    for r in parts:
        pads += len([n for n in D.P[r]["pins"]])
    print("seeed: gerbers %d files; BOM %d lines (+ XIAO option); %d placed parts: top %d, bottom %d (%s); "
          "%d SMD pads without the XIAO" % (len(GERBERS), len(bom_rows()), len(parts), len(top), len(bot),
                                            " ".join(bot), pads))
    print("CPL rows: %d (incl. U4)" % len(placed))
    build_nostorage(pcb)


def build_nostorage(pcb):
    """fab/seeed/no-storage/: the same board, assembled on the top side only. The bottom-side log storage (U5, C8,
    C9, R9-R12) is left off, so there is one stencil and one assembly pass; the empty pads can be fitted later."""
    global STORAGE
    STORAGE = False
    out = os.path.join(OUT, "no-storage")
    os.makedirs(out)
    left_off = sorted((r for r, p in D.P.items() if p["pcb"][3] == "BA" and not p["fp"].startswith(NOT_PARTS)), key=natural)
    cpl = os.path.join(out, "wavehat-seeed-cpl-nostorage.csv")
    placed = write_cpl(cpl)
    notes = os.path.join(OUT, "wavehat-fab-notes.txt")
    dbom = os.path.join(out, "wavehat-bom-detailed-nostorage.csv")
    write_detailed_bom(dbom)
    gz = os.path.join(out, "wavehat-seeed-gerbers.zip")
    shutil.copy(os.path.join(OUT, "wavehat-seeed-gerbers.zip"), gz)     # identical to the full build's
    for opt in ("noxiao", "c3", "c6", "s3"):
        write_bom(os.path.join(out, "wavehat-seeed-bom-nostorage-%s.csv" % opt), bom_rows(None if opt == "noxiao" else opt))
    shutil.copy(os.path.join(OUT, "wavehat-assembly-top.pdf"), os.path.join(out, "wavehat-assembly-top.pdf"))
    shutil.copy(os.path.join(HERE, "ORDER-SEEED-NOSTORAGE.md"), os.path.join(out, "ORDER.md"))
    with zipfile.ZipFile(os.path.join(out, "wavehat-seeed-assembly-nostorage.zip"), "w", zipfile.ZIP_DEFLATED) as z:
        z.write(cpl, "wavehat-seeed-cpl-nostorage.csv")
        z.write(dbom, "wavehat-bom-detailed-nostorage.csv")
        z.write(notes, "wavehat-fab-notes.txt")
        z.write(os.path.join(out, "wavehat-assembly-top.pdf"), "wavehat-assembly-top.pdf")
        z.write(os.path.join(HERE, "img", "wavehat-3d-top.png"), "wavehat-3d-top.png")
        z.write(os.path.join(HERE, "img", "wavehat-3d-angle.png"), "wavehat-3d-angle.png")
        z.write(os.path.join(HERE, "ORDER-SEEED-NOSTORAGE.md"), "ORDER.md")
    for opt in ("noxiao", "c3", "c6", "s3"):
        with zipfile.ZipFile(os.path.join(out, "wavehat-seeed-pcba-nostorage-%s.zip" % opt), "w", zipfile.ZIP_DEFLATED) as z:
            for src, dst in GERBERS.items():
                z.write(os.path.join(FAB, "gerbers", src), dst)
            z.write(os.path.join(out, "wavehat-seeed-bom-nostorage-%s.csv" % opt), "wavehat-seeed-bom-nostorage-%s.csv" % opt)
            z.write(cpl, "wavehat-seeed-cpl-nostorage.csv")
            z.write(os.path.join(out, "wavehat-assembly-top.pdf"), "wavehat-assembly-top.pdf")
            z.write(os.path.join(HERE, "ORDER-SEEED-NOSTORAGE.md"), "ORDER.md")
    print("no-storage: %d placed parts, top only; left off: %s; BOM %d lines (+ XIAO option); CPL rows %d"
          % (len(assembled()), " ".join(left_off), len(bom_rows()), len(placed)))
    STORAGE = True


if __name__ == "__main__":
    main()
