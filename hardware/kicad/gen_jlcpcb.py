#!/usr/bin/env python3
"""Package the WaveHat for a JLCPCB assembly quote, to compare with Seeed Fusion: both builds.

    python3 -I gen_jlcpcb.py          (after run_pipeline.sh / gen_seeed.py have written fab/)

Writes fab/jlcpcb/no-storage/ (top side only) and fab/jlcpcb/full/ (both sides, with the log storage), each with:
  wavehat-gerbers.zip            the same Gerbers as the Seeed builds (fab/seeed/wavehat-seeed-gerbers.zip)
  wavehat-jlcpcb-bom.csv         JLCPCB's BOM format: Comment, Designator, Footprint, LCSC Part #
  wavehat-jlcpcb-cpl.csv         JLCPCB's CPL format: Designator, Mid X, Mid Y, Layer, Rotation
  ORDER.md                       the order form, step by step (ORDER-JLCPCB.md / ORDER-JLCPCB-FULL.md)

The XIAO (U4) is in neither BOM nor CPL: JLCPCB doesn't stock it, and you fit your own XIAO ESP32C6 afterwards.
"""
import csv
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_seeed as S  # noqa: E402  (assembled(), natural(), the shared Gerber zip)
import wavehat_design as D  # noqa: E402

BASE = os.path.join(HERE, "fab", "jlcpcb")

# LCSC numbers for the exact MPNs, checked in stock on 20 Oct 2026 (hardware/sourcing.md section 1)
LCSC = {
    "GRM155R71C104KA88D": "C71629",      # 100 nF 0402
    "GRM188R61A106KE69D": "C77044",      # 10 uF 0603
    "GRM31CR72A225KA73L": "C913599",     # 2.2 uF 100 V 1206 (obsolete at Murata; alt. Samsung CL31B225KCHSNNE)
    "GRM21BR61A226ME51L": "C77074",      # 22 uF 0805
    "SS14": "C2480",                     # MDD SS14, SMA (a JLCPCB basic part)
    "1812L050/60MR": "C87383",           # Littelfuse PTC 0.5 A 60 V (alt. BHFUSE BSMD1812-050-60V C883142)
    "SM04B-SRSS-TB(LF)(SN)": "C160404",  # JST SH 4-pin, Qwiic
    "SM04B-GHS-TB(LF)(SN)": "C189895",   # JST GH 4-pin, VESC CAN
    "FNR4020S150MT": "C167837",          # 15 uH 4020
    "RC0402FR-074K7L": "C105871",
    "RC0402FR-07120KL": "C93945",
    "RC0402FR-0722K1L": "C163478",
    "RC0402FR-07120RL": "C114758",
    "RC0402FR-0710KL": "C60490",
    "SMBJ30A": "C113998",                # MDD SMBJ30A
    "LSM6DSOTR": "C2655100",
    "LMR51606YDBVR": "C33545953",
    "SN65HVD230DR": "C12084",
    "ZDSD02GLGEAG": "C2875853",          # Zetta 2 Gbit SD NAND (full build only)
}


# JLCPCB "Basic" equivalents for the plain passives: no feeder-loading fee (about A$2.34 per Extended part type).
# Same package, value, rating and dielectric (C5 at 25 V instead of 10 V); R4 22k instead of 22.1k gives 5.16 V
# out instead of 5.14 V. JLCPCB's BOM review (20 Oct 2026) listed all of them as Basic except C25750 (120k, Extended:
# a stocked value, kept). JLCPCB BOM only: the board and
# the Seeed BOM keep the Murata/Yageo parts.
BASIC = {
    "GRM155R71C104KA88D": ("C1525", "100nF 16V X7R (CL05B104KO5NNNC)"),
    "GRM188R61A106KE69D": ("C19702", "10uF 10V X5R (CL10A106KP8NNNC)"),
    "GRM21BR61A226ME51L": ("C45783", "22uF 25V X5R (CL21A226MAQNNNE)"),
    "RC0402FR-074K7L": ("C25900", "4.7k 1% (0402WGF4701TCE)"),
    "RC0402FR-07120KL": ("C25750", "120k 1% (0402WGF1203TCE)"),
    "RC0402FR-0722K1L": ("C25768", "22k 1% (0402WGF2202TCE), replaces 22.1k: 5.16 V out"),
    "RC0402FR-07120RL": ("C25079", "120R 1% (0402WGF1200TCE)"),
    "RC0402FR-0710KL": ("C25744", "10k 1% (0402WGF1002TCE)"),
}

# JLCPCB's part models disagree with KiCad's footprint zero rotation on some packages: add this many degrees.
# Checked part by part in JLCPCB's placement preview (purple pin-1 dot against the board's pin-1 marker).
# Angles are counter-clockwise, as in KiCad and JLCPCB's CPL.
ROT_FIX = {"U2": 180,   # SOT-23-6: JLCPCB's model sat with pin 1 diagonally opposite (preview, 20 Oct 2026)
           "U3": -90,   # SOIC-8: needed 90 degrees clockwise in the preview (20 Oct 2026)
           "U5": 180}   # SD NAND, bottom: pin 1 sat diagonally opposite the silkscreen dot (20 Oct 2026); JLCPCB's
                        # model also sat about 1 mm off-centre in the preview, so ask them to centre it (order remark)


# Footprint column text for JLCPCB's reviewers, where our footprint name could mislead (it is only a label to them)
FP_LABEL = {"SD_NAND_LGA-8_8x6mm_P1.27mm": "LGA-8 8x6mm SD NAND (lands fit 1.25-1.27 mm pitch)"}


def build(storage):
    S.STORAGE = storage
    OUT = os.path.join(BASE, "full" if storage else "no-storage")
    parts = S.assembled()                       # U4 excluded; bottom side only in the full build
    missing = sorted({p["mpn"] for p in parts.values()} - set(LCSC))
    if missing:
        raise SystemExit("no LCSC number for: " + ", ".join(missing))
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)

    groups = {}
    for ref, p in parts.items():
        groups.setdefault(p["mpn"], []).append(ref)
    rows = []
    for mpn, refs in groups.items():
        p = D.P[refs[0]]
        lcsc, comment = BASIC.get(mpn, (LCSC[mpn], "%s (%s)" % (p["value"], mpn)))
        rows.append([comment, ",".join(sorted(refs, key=S.natural)),
                     FP_LABEL.get(p["fp"].split(":")[1], p["fp"].split(":")[1]), lcsc])
    rows.sort(key=lambda r: S.natural(r[1].split(",")[0]))
    with open(os.path.join(OUT, "wavehat-jlcpcb-bom.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
        w.writerows(rows)

    cpl = []
    for side_file, layer in (("wavehat-cpl-top.csv", "Top"), ("wavehat-cpl-bottom.csv", "Bottom")):
        for r in csv.DictReader(open(os.path.join(S.FAB, side_file))):
            if r["Ref"] in parts:
                rot = (float(r["Rot"]) + ROT_FIX.get(r["Ref"], 0)) % 360
                cpl.append([r["Ref"], "%.3fmm" % float(r["PosX"]), "%.3fmm" % float(r["PosY"]), layer, "%g" % rot])
    cpl.sort(key=lambda r: S.natural(r[0]))
    with open(os.path.join(OUT, "wavehat-jlcpcb-cpl.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        w.writerows(cpl)

    shutil.copy(os.path.join(S.OUT, "wavehat-seeed-gerbers.zip"), os.path.join(OUT, "wavehat-gerbers.zip"))
    shutil.copy(os.path.join(HERE, "ORDER-JLCPCB-FULL.md" if storage else "ORDER-JLCPCB.md"), os.path.join(OUT, "ORDER.md"))
    sides = sorted({c[3] for c in cpl})
    print("jlcpcb %s: BOM %d lines, CPL %d parts (%s; no XIAO)" % ("full" if storage else "no-storage", len(rows),
                                                                   len(cpl), " + ".join(sides)))
    S.STORAGE = True


def main():
    build(False)
    build(True)


if __name__ == "__main__":
    main()
