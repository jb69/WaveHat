# WaveHat rev A, full build (both sides, with log storage): JLCPCB assembly quote

**Ordered 20 Oct 2026** with these files: 5 boards, OSP finish (ENIG was about A$15 a board more), tented vias, A$277.96 paid including shipping (US$193.07: US$187.07 boards and assembly, US$6.00 shipping). JLCPCB order [order number] (PCB [PCB number]), in production.

These files get a JLCPCB quote for the complete board:
- **Top side:** 24 parts.
- **Bottom side:** the 7 log-storage parts under the XIAO: U5 (Zetta ZDSD02GLGEAG SD NAND, 256 MB), C8, C9 and R9–R12.
- **No XIAO:** U4 is not in the BOM. JLCPCB doesn't stock XIAOs; you solder on your own XIAO ESP32C6 afterwards.

For comparison:
- **Seeed:** the two-sided build was quoted at US$370 with Seeed's XIAO, and the 0.1 mm mask dam would add US$25.
- **JLCPCB (estimate):** the sourcing report puts this build at about **US$220 (≈ A$350 with GST)**, parts and shipping included. That's arithmetic on published rates (`../../../sourcing.md` §5), not a quote.

The top-side-only build is in `../no-storage/`.

## Files

| File | Upload where |
|---|---|
| `wavehat-gerbers.zip` | "Add gerber file" on https://jlcpcb.com/quote. The same Gerbers as every other build |
| `wavehat-jlcpcb-bom.csv` | BOM upload: 19 lines (Comment, Designator, Footprint, LCSC Part #), both sides |
| `wavehat-jlcpcb-cpl.csv` | CPL upload: 31 placements (24 Top, 7 Bottom). Coordinates in mm from the board's lower-left corner, seen from the top, as JLCPCB expects for both sides |

## The order, step by step

1. **https://jlcpcb.com/quote**, then **Add gerber file**: `wavehat-gerbers.zip` (21 × 54 mm, 2 layers).
2. **PCB options:**
   - 2 layers, qty 5 or 10, 1.6 mm
   - Surface finish **ENIG**, 1 oz, via covering tented
   - Choose a location for JLCPCB's order number (the bottom face near the J4 pads), or remove it
3. **PCB Assembly:** on.
   - Assembly side: **Both sides**. Two-sided boards usually need the Standard PCBA tier; the Economic tier is top-side only.
   - PCBA quantity: 5
   - Tooling holes: let JLCPCB add them, if it asks
   - Confirm parts placement: **Yes**
4. **Upload the BOM and CPL.** All 19 lines should match an LCSC number. U4, the XIAO, is deliberately missing, so it won't be placed.
5. **Placement preview, both sides:**
   - **Bottom:** the preview mirrors it. Check **U5's pin 1** against the silkscreen dot, then C8, C9 and R9–R12. U5's model sat about 1 mm off-centre in JLCPCB's preview (20 Oct 2026): nudge it to the middle of its outline with the arrow buttons, and put in the order remark "U5 (LGA-8, 8×6 mm): pin 1 at the silkscreen dot, centre on the footprint".
   - **Top:** U1 (pin 1), U2, U3, the diode bands on D1–D3 and TVS1, and J2/J3.
   - KiCad and JLCPCB don't always agree on a part's zero rotation. The CPL already carries the corrections found in the preview on 20 Oct 2026: U2 +180°, U3 −90° (90° clockwise), U5 +180°. Fix any others that are off.
6. **Add to cart** and compare with Seeed.

## Things to know

- **Basic parts:** the BOM uses JLCPCB "Basic" parts for 7 plain resistor and capacitor lines (C1525, C19702, C45783, C25900, C25768, C25079, C25744): same package, value and rating as the design's Murata/Yageo parts, and no feeder-loading fee. R3 (C25750, 120 kΩ) is Extended in JLCPCB's review; it stays, since a Basic alternative would mean a different divider for about US$1.50. R4 is 22 kΩ instead of 22.1 kΩ (5.16 V instead of 5.14 V out). The chips, connectors, inductor, fuse, TVS and C4 stay Extended.
- **Via covering:** choose **Tented**. The design's vias are tented; the paid via-covering options added A$72.76 to the first quote.

- **Reflow order:** JLCPCB assembles the bottom first (7 small parts), then the top.
- **U1 stock:** LCSC had only **38** LSM6DSOTR on 20 Oct 2026. If it's short, pre-order it to your JLCPCB parts library.
- **U5:** the Zetta ZDSD02GLGEAG is LCSC C2875853. If it's out, the MK MKDV4GCL-ABB (C7500178, 512 MB) fits the same pads.
- **C4** (Murata GRM31CR72A225KA73L) is obsolete; LCSC still has stock. Samsung CL31B225KCHSNNE or Yageo CC1206KKX7R0BB225 are drop-in replacements.
- **Mask dam and X-ray:** JLCPCB's standard form offers neither the 0.1 mm mask dam nor X-ray of an LGA. Ask for both in the order remark (U1 LGA-14, U5 LGA-8).
- **Fitting your XIAO:** see `../../seeed/no-storage/ORDER.md`, "Fitting your own XIAO ESP32C6".
