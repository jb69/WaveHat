# WaveHat rev A, no-storage build: JLCPCB assembly quote

These files get a JLCPCB quote for the same build as Seeed's no-storage order, so the two can be compared. The build:
- **Top side only:** 24 parts.
- **Storage left off:** the bottom-side log storage (U5, C8, C9, R9–R12) is not fitted, but its pads stay on the board.
- **No XIAO:** U4 is not in the BOM. JLCPCB doesn't stock XIAOs; you solder on your own XIAO ESP32C6 afterwards, by its 14 castellated pads with an iron.

Seeed's quote for comparison: **US$314.67 delivered** for 5 boards, with Seeed's XIAO C6 and the 0.1 mm mask dam (US$288.67 without the XIAO). The sourcing report estimates JLCPCB at about **US$140 (≈ A$225 with GST)** for this build, parts and shipping included. That estimate is arithmetic on JLCPCB's published rates (`../../../sourcing.md` §5), not a quote.

## Files

| File | Upload where |
|---|---|
| `wavehat-gerbers.zip` | "Add gerber file" on https://jlcpcb.com/quote. The same Gerbers as the Seeed order |
| `wavehat-jlcpcb-bom.csv` | The assembly step's BOM upload. Columns Comment, Designator, Footprint, LCSC Part #: 18 lines, every part with its LCSC number |
| `wavehat-jlcpcb-cpl.csv` | The assembly step's CPL (pick and place) upload. Columns Designator, Mid X, Mid Y, Layer, Rotation; top side only, mm from the board's lower-left corner |

## The order, step by step

1. **https://jlcpcb.com/quote**, then **Add gerber file**: `wavehat-gerbers.zip`. The size should read 21 × 54 mm, 2 layers.
2. **PCB options:**
   - Base material FR-4, 2 layers, PCB qty 5 (or 10: bare boards are cheap)
   - Thickness 1.6 mm, any colour
   - Surface finish **ENIG** (the IMU is a 0.5 mm-pitch LGA)
   - Outer copper 1 oz, via covering tented
   - JLCPCB prints an order number on the board by default. Choose a location for it (the bottom face near the J4 pads has room) or pay to remove it.
3. **PCB Assembly:** on.
   - Assembly side: **Top side**
   - PCBA quantity: 5
   - Tooling holes: let JLCPCB add them, if it asks
   - Confirm parts placement: **Yes**
   - PCBA type: Economic is the cheaper tier for top-side-only boards. If it refuses a part, switch to Standard.
4. **Upload the BOM and CPL**, then check the part matching:
   - Every line should match its LCSC number.
   - U4 (the XIAO) and the bottom-side parts are deliberately missing from both files, so they won't be placed.
5. **Placement preview:** check the rotation of U1 (pin 1 dot), U2 (SOT-23-6), U3 (SOIC-8), the diodes D1–D3 and TVS1 (cathode band), and the connectors J2/J3. The purple dot (the part's pin 1) should sit on the board's pin-1 marker. The CPL already carries the corrections found in the preview on 20 Oct 2026: U2 +180°, U3 −90° (90° clockwise). Fix any others that are off.
6. **Add to cart** and compare the total with Seeed's US$314.67 (or US$288.67 without Seeed's XIAO).

## Things to know

- **Basic parts:** the BOM uses JLCPCB "Basic" parts for 7 plain resistor and capacitor lines (C1525, C19702, C45783, C25900, C25768, C25079, C25744): same package, value and rating as the design's Murata/Yageo parts, and no feeder-loading fee. R3 (C25750, 120 kΩ) is Extended in JLCPCB's review; it stays, since a Basic alternative would mean a different divider for about US$1.50. R4 is 22 kΩ instead of 22.1 kΩ (5.16 V instead of 5.14 V out). The chips, connectors, inductor, fuse, TVS and C4 stay Extended.
- **Via covering:** choose **Tented**. The design's vias are tented; the paid via-covering options added A$72.76 to the first quote.

- **U1 stock:** LCSC had only **38** LSM6DSOTR when the sourcing report was written (20 Oct 2026). If JLCPCB shows it short, pre-order it to your JLCPCB parts library, or use Seeed.
- **C4** (Murata GRM31CR72A225KA73L) is obsolete at Murata; LCSC still has stock. If it runs out, Samsung CL31B225KCHSNNE or Yageo CC1206KKX7R0BB225 (2.2 µF 100 V X7R 1206) are drop-in replacements.
- **The solder mask dam** you bought from Seeed (0.1 mm, US$25) is not a separate option on JLCPCB's standard form. Their DFM review decides whether the dams between the IMU's pads stay. Ask in the order remark if it matters; not verified.
- **No X-ray by default:** JLCPCB X-rays BGA-type parts. Ask in the order remark for U1, an LGA.
- **Fitting your XIAO:** see `fab/seeed/no-storage/ORDER.md`, "Fitting your own XIAO ESP32C6". The steps are the same.
