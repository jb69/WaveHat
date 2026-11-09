# WaveHat rev B, full build (both sides, with log storage): JLCPCB assembly quote

**Ordered 20 Oct 2026** with these files: 5 boards, OSP finish (ENIG was about A$15 a board more), tented vias, A$277.96 paid including shipping (US$193.07: US$187.07 boards and assembly, US$6.00 shipping). JLCPCB order [order number] (PCB [PCB number]), in production.

These files get a JLCPCB quote for the complete board:
- **Top side:** 25 parts (26 with J5), J6 the 10-pin IO header among them (7 Nov 2026).
- **Bottom side:** the 7 log-storage parts under the XIAO: U5 (Zetta ZDSD02GLGEAG SD NAND, 256 MB), C8, C9 and R9–R12.
- **No XIAO:** U4 is not in the BOM. JLCPCB doesn't stock XIAOs; you solder on your own XIAO ESP32C6 afterwards.
- **Two packs:** `full/` leaves J5 (the GNSS port) off for hand fitting; `full-gnss/` has JLCPCB fit it. Both fit J6. Nothing else differs.

For comparison:
- **Seeed:** the two-sided build was quoted at US$370 with Seeed's XIAO, and the 0.1 mm mask dam would add US$25.
- **JLCPCB (estimate):** the sourcing report puts this build at about **US$220 (≈ A$350 with GST)**, parts and shipping included. That's arithmetic on published rates (`../../../sourcing.md` §5), not a quote.

The top-side-only build is in `../no-storage/`.

## Files

| File | Upload where |
|---|---|
| `wavehat-gerbers.zip` | "Add gerber file" on https://jlcpcb.com/quote. The same Gerbers as every other build |
| `wavehat-jlcpcb-bom.csv` | BOM upload: 20 lines (21 with J5; Comment, Designator, Footprint, LCSC Part #), both sides |
| `wavehat-jlcpcb-cpl.csv` | CPL upload: 32 placements (25 Top, 7 Bottom; 33 and 26 with J5). Coordinates in mm from the board's lower-left corner, seen from the top, as JLCPCB expects for both sides |

## The order, step by step

1. **https://jlcpcb.com/quote**, then **Add gerber file**: `wavehat-gerbers.zip` (21 × 69 mm, 2 layers).
2. **PCB options:**
   - 2 layers, qty 5 or 10, 1.6 mm
   - Surface finish **ENIG**, 1 oz, via covering tented
   - Choose a location for JLCPCB's order number (the bottom face near the J4 pads), or remove it
3. **PCB Assembly:** on.
   - Assembly side: **Both sides**. Two-sided boards usually need the Standard PCBA tier; the Economic tier is top-side only.
   - PCBA quantity: 5
   - Tooling holes: let JLCPCB add them, if it asks
   - Confirm parts placement: **Yes**
4. **Upload the BOM and CPL.** All 20 lines (21 with J5) should match an LCSC number. U4, the XIAO, is deliberately missing, so it won't be placed.
5. **Placement preview, both sides:**
   - **Bottom:** the preview mirrors it. Check **U5's pin 1** against the silkscreen dot, then C8, C9 and R9–R12. U5's model sat about 1 mm off-centre in JLCPCB's preview (20 Oct 2026): nudge it to the middle of its outline with the arrow buttons, and put in the order remark "U5 (LGA-8, 8×6 mm): pin 1 at the silkscreen dot, centre on the footprint".
   - **Top:** U1 (pin 1), U2, U3, the diode bands on D1–D3 and TVS1, and J2/J3/J6 (J5 too in the with-GNSS pack). J6 is the mirror of J3: on the left-hand edge, opening outward, rotation 270° in the CPL where J3 has 90°; if its model faces inboard in the preview, turn it 180°.
   - KiCad and JLCPCB don't always agree on a part's zero rotation. The CPL already carries the corrections found in the preview on 20 Oct 2026: U2 +180°, U3 −90° (90° clockwise), U5 +180°. Fix any others that are off.
6. **Add to cart** and compare with Seeed.

## Things to know

- **Basic parts:** the BOM uses JLCPCB "Basic" parts for 7 plain resistor and capacitor lines (C1525, C19702, C45783, C25900, C25768, C25079, C25744): same package, value and rating as the design's Murata/Yageo parts, and no feeder-loading fee. R3 (C25750, 120 kΩ) is Extended in JLCPCB's review; it stays, since a Basic alternative would mean a different divider for about US$1.50. R4 is 22 kΩ instead of 22.1 kΩ (5.16 V instead of 5.14 V out). The chips, connectors, inductor, fuse, TVS and C4 stay Extended.
- **Via plating method:** choose **Horizontal Electroless Copper Plating** (added 30 Oct 2026: the first lot, ordered with "Not specified", came back with open vias; see `../jlcpcb-quality-case.md`).
- **Via covering:** choose **Tented**. The design's vias are tented; the paid via-covering options added A$72.76 to the first quote.

- **Reflow order:** JLCPCB assembles the bottom first (7 small parts), then the top.
- **U1 stock:** LCSC had only **38** LSM6DSOTR on 20 Oct 2026. If it's short, pre-order it to your JLCPCB parts library.
- **J6 stock:** the 10-pin JST-GH (SM10B-GHS-TB, C2683602, Extended) showed 1 in stock at LCSC on 7 Nov 2026. If the BOM tool can't match it, delete the J6 line and hand-fit (2 mm clear round its pads); or pre-order it to the parts library.
- **U5:** the Zetta ZDSD02GLGEAG is LCSC C2875853. If it's out, the MK MKDV4GCL-ABB (C7500178, 512 MB) fits the same pads.
- **C4** (Murata GRM31CR72A225KA73L) is obsolete; LCSC still has stock. Samsung CL31B225KCHSNNE or Yageo CC1206KKX7R0BB225 are drop-in replacements.
- **Mask dam and X-ray:** JLCPCB's standard form offers neither the 0.1 mm mask dam nor X-ray of an LGA. Ask for both in the order remark (U1 LGA-14, U5 LGA-8).
- **Fitting your XIAO:** see `../../seeed/no-storage/ORDER.md`, "Fitting your own XIAO ESP32C6".

## BOM match, rev B with J5 (30 Oct 2026)

JLCPCB's BOM tool matched all 20 lines of `fab/jlcpcb/full-gnss/wavehat-jlcpcb-bom.csv` with no warnings, 5 boards assembled, parts estimate **US$93.28**. J5 (SM06B-GHS-TB, C133065) matched with stock, US$1.79 for the 5. The big lines are unchanged from rev A: U5 SD NAND US$42.81, U1 IMU US$19.98, U2 buck US$11.56 (9 pcs; JLCPCB rounds small parts up). Eight lines are Basic (C1525, C45783, C19702, C2480, C25900, C25768, C25079, C25744); the other twelve are Extended and each carries the feeder-loading fee, which the parts estimate does not include. Re-match before ordering if more than 24 hours have passed.

**Quote, rev B with J5 (30 Oct 2026):** A$278.90 before shipping for 5 assembled boards. PCB A$2.84 (special offer, tented vias free); setup A$73.17; stencil A$23.50; components A$132.53 (20 lines); feeder loading A$44.04 (12 Extended parts); SMT A$2.10; packaging A$0.71; depanel A$4.70; **flying probe test A$7.26 (keep it: the bare-board e-test rev A never had)**; assembly 3–4 days at no charge. Rev A was A$277.96 shipped. With **Horizontal Electroless Copper Plating** selected the PCB line rises to A$7.63 (A$4.79 for the plating) and the total to **A$283.69** before shipping. 

**Quote, rev B with J5 and J6 (7 Nov 2026, the 21 × 69 mm board):** **A$295.78** before shipping for 5 assembled boards. PCB A$10.63 (special offer A$5.76, Horizontal Electroless Copper plating A$4.87, tented vias free); setup A$74.15; stencil A$23.81; components A$132.55 (21 lines, J6 C2683602 matched); feeder loading A$46.87; SMT A$2.30; packaging A$0.72; depanel A$4.77; assembly 3–4 days at no charge. A$12 over the 30 Oct quote, for the longer board and J6. Placement preview checked: J6 opens outward on the left-hand edge with pin 1 forward (the mirror of J3), U1 and U3 pin-1 dots on their markers; no rotation fix needed for J6.
