# WaveHat rev A: sourcing parts for 5 boards, DIY vs Seeed assembly

All prices were checked on **2026-10-20**. Distributor sites were read live (LCSC through its product-detail data, DigiKey, Mouser, element14 and RS in a browser; Seeed, JLCPCB and PCBWay from their instant-quote calculators, without logging in or uploading files). Nothing was ordered.

- **Currency:** USD is converted at **1 USD = 1.43 AUD** (Wise mid-market 1.429, https://wise.com/gb/currency-converter/usd-to-aud-rate?amount=1). Card or PayPal conversion is usually 2–3 % worse.
- **GST:** DigiKey, element14 and RS show AUD prices **without GST** and add 10 % at checkout. Core, Jaycar and AliExpress show prices that include it. For LCSC, JLCPCB and Seeed, the 10 % is assumed to be added at checkout (not verified without logging in).
- **Estimates:** "**est.**" marks my own estimate. "not verified" means the figure couldn't be confirmed.
- **The XIAO (U4)** is excluded throughout: you supply your own XIAO ESP32-C6 boards.

Two builds are compared:

- **Full build:** both sides, with the 256 MB SD NAND log storage. BOM: `kicad/fab/seeed/wavehat-bom-detailed.csv`.
- **No-storage build:** top side only. U5, C8, C9 and R9–R12 are left off. BOM: `kicad/fab/seeed/no-storage/`.

---

## 1. Parts: recommended source per line (LCSC)

LCSC is the cheapest source on almost every line, has every part in stock, and is the only place that sells the SD NAND. Buy quantities cover 5 boards plus spares, rounded up to LCSC's minimum or multiple. 0402 parts are bought by the hundred because a hundred costs cents.

| # | Ref (qty for 5 boards) | Part | Buy | LCSC part, unit price (USD) | Line (USD) | MOQ / multiple | Stock | URL |
|---|---|---|---|---|---|---|---|---|
| 1 | C1,C3,C6,C7,C8 (25) | Murata GRM155R71C104KA88D 100 nF 0402 | 100 | C71629, 0.0052 | 0.52 | 100 / 100 | 951,900 | https://www.lcsc.com/product-detail/C71629.html |
| 2 | C2,C9 (10) | Murata GRM188R61A106KE69D 10 µF 0603 | 20 | C77044, 0.0351 | 0.70 | 10 / 10 | 138,690 | https://www.lcsc.com/product-detail/C77044.html |
| 3 | C4 (5) | Murata GRM31CR72A225KA73L 2.2 µF 100 V 1206 (**obsolete at Murata**; LCSC has the last stock) | 10 | C913599, 0.4529 | 4.53 | 5 / 5 | 2,465 | https://www.lcsc.com/product-detail/C913599.html |
| 4 | C5 (5) | Murata GRM21BR61A226ME51L 22 µF 10 V 0805 | 10 | C77074, 0.181 | 1.81 | 5 / 5 | 32,430 | https://www.lcsc.com/product-detail/C77074.html |
| 5 | D1–D3 (15) | SS14 SMA (MDD) | 50 | C2480, 0.0193 | 0.97 | 50 / 50 | 902,150 | https://www.lcsc.com/product-detail/C2480.html |
| 6 | F1 (5) | BHFUSE BSMD1812-050-60V, the equivalent listed in ORDER-SEEED.md (the Littelfuse 1812L050/60MR is C87383, US$3.80 for 10) | 10 | C883142, 0.0894 | 0.89 | 5 / 5 | 30,140 | https://www.lcsc.com/product-detail/C883142.html |
| 7 | J2 (5) | JST SM04B-SRSS-TB(LF)(SN) | 10 | C160404, 0.216 | 2.16 | 5 / 5 | 44,140 | https://www.lcsc.com/product-detail/C160404.html |
| 8 | J3 (5) | JST SM04B-GHS-TB(LF)(SN) | 10 | C189895, 0.3069 | 3.07 | 5 / 5 | 835 | https://www.lcsc.com/product-detail/C189895.html |
| 9 | L1 (5) | Changjiang FNR4020S150MT 15 µH, Isat 1.5 A | 10 | C167837, 0.0819 | 0.82 | 10 / 10 | 5,740 | https://www.lcsc.com/product-detail/C167837.html |
| 10 | R1,R2 (10) | Yageo RC0402FR-074K7L 4.7 k | 100 | C105871, 0.0029 | 0.29 | 100 / 100 | 7.5 M | https://www.lcsc.com/product-detail/C105871.html |
| 11 | R3 (5) | Yageo RC0402FR-07120KL 120 k | 100 | C93945, 0.0017 | 0.17 | 100 / 100 | 1.3 M | https://www.lcsc.com/product-detail/C93945.html |
| 12 | R4 (5) | Yageo RC0402FR-0722K1L 22.1 k | 100 | C163478, 0.0020 | 0.20 | 100 / 100 | 1.7 M | https://www.lcsc.com/product-detail/C163478.html |
| 13 | R5 (5) | Yageo RC0402FR-07120RL 120 Ω | 100 | C114758, 0.0019 | 0.19 | 100 / 100 | 1.4 M | https://www.lcsc.com/product-detail/C114758.html |
| 14 | R6,R9–R12 (25) | Yageo RC0402FR-0710KL 10 k | 100 | C60490, 0.0024 | 0.24 | 100 / 100 | 468,600 | https://www.lcsc.com/product-detail/C60490.html |
| 15 | TVS1 (5) | SMBJ30A (MDD) | 10 | C113998, 0.049 | 0.49 | 10 / 10 | 142,890 | https://www.lcsc.com/product-detail/C113998.html |
| 16 | U1 (5) | ST LSM6DSOTR (2 spares for hand-assembly losses) | 7 | C2655100, 3.9232 | 27.46 | 1 / 1 | **38, low: order soon** | https://www.lcsc.com/product-detail/C2655100.html |
| 17 | U2 (5) | TI LMR51606YDBVR | 6 | C33545953, 1.3783 | 8.27 | 1 / 1 | 1,539 | https://www.lcsc.com/product-detail/C33545953.html |
| 18 | U3 (5) | TI SN65HVD230DR | 6 | C12084, 0.5768 | 3.46 | 1 / 1 | 115,684 | https://www.lcsc.com/product-detail/C12084.html |
| 19 | U5 (5) | Zetta ZDSD02GLGEAG 2 Gbit SD NAND (full build only) | 6 | C2875853, 8.5975 | 51.59 | 1 / 1 | 2,520 | https://www.lcsc.com/product-detail/C2875853.html |
| | | **Full build** | | | **107.83** (≈A$154) | | | |
| | | **No-storage build** (no line 19; C8, C9 and R9–R12 come from the same reels) | | | **56.24** (≈A$80) | | | |

- **Lead time:** all lines are in stock, and LCSC normally ships in 1–3 days.
- **Shipping to Australia is not verified.** LCSC publishes no rate table; the price only appears at checkout with an address entered.
  - LCSC lists DHL, UPS, FedEx, Global Direct Standard Line and others (https://www.lcsc.com/help-center/shipping-delivering/shipping-methods) and raised freight rates on 14 Apr 2026 (https://www.lcsc.com/help-center/notice/logistics-rate-update-due-to-fuel-surcharge).
  - **est.:** about US$10–15 standard (7–15 business days) or US$20–30 DHL/FedEx (3–6 days). The totals below use US$20.
- **Duties:** LCSC's terms leave duties and taxes to the buyer (https://www.lcsc.com/help-center/shipping-delivering/customs-duties-taxes). Budget 10 % GST.
- **Other SD NAND options for the same footprint (LCSC):**
  - MK MKDV1GCL-ABA (1 Gbit): US$37.40 for 6, C6152616.
  - MK MKDV4GCL-ABB (4 Gbit): US$84.19 for 6, C7500178.
  - CS CSNP4GCR01-BOW: out of stock.

## 2. Fast Australian alternatives, per line

Use these if you want delivery in about 4 days, or LCSC is short of something. Prices are AUD **ex GST** at the quantity shown unless noted.

| # | Part | Best local option | A$ | Stock / lead | URL |
|---|---|---|---|---|---|
| 1 | 100 nF 0402 | element14 4326785, exact part, 50 pcs | 2.20 | 2.7 M, UK stock, 3–5 days | https://au.element14.com/murata/grm155r71c104ka88d/cap-mlcc-0-1uf-x7r-16v-0402/dp/4326785 |
| 2 | 10 µF 0603 | DigiKey GRM188R61A106ME69D (±20 %; the KE69D is not stocked in AU), 20 pcs | 1.98 | 4,979 | https://www.digikey.com.au/en/products/detail/murata-electronics/GRM188R61A106ME69D/5027560 |
| 3 | 2.2 µF 100 V 1206 | Mouser Samsung CL31B225KCHSNNE X7R, 10 pcs. The exact Murata part is A$7.74 for 10 at element14 4740654 | 4.99 | 169,123 | https://au.mouser.com/c/?q=CL31B225KCHSNNE |
| 4 | 22 µF 0805 | element14 2494270, exact part, 10 pcs | 3.34 | 133,626 | https://au.element14.com/murata/grm21br61a226me51l/cap-22-f-10v-20-x5r-0805/dp/2494270 |
| 5 | SS14 | Mouser Panjit SS14L_R1_00001, 20 pcs | 3.80 | 13,345 | https://au.mouser.com/c/?q=SS14&instock=y |
| 6 | 1812L050/60MR | DigiKey, exact part, 6 pcs (element14 3516024: A$10.68). RS only has the 30 V version | 8.86 | 35,459 | https://www.digikey.com.au/en/products/detail/littelfuse-inc/1812L050-60MR/6234813 |
| 7 | SM04B-SRSS-TB | element14 183083901, 10 pcs | 3.80 | 102,752 | https://au.element14.com/jst-japan-solderless-terminals/sm04b-srss-tb-lf-sn/connector-header-smt-r-a-1mm-4way/dp/183083901 |
| 8 | SM04B-GHS-TB | Mouser, 6 pcs (backorder at DigiKey and element14; RS 175-5704 A$8.34 for 10) | 3.40 | 56,349 | https://au.mouser.com/c/?q=SM04B-GHS-TB(LF)(SN) |
| 9 | 15 µH 4×4 | **The FNR4020 is not sold in AU.** Bourns SRP4020TA-150M (Isat 1.9 A) at DigiKey, 6 pcs. It measures 4.45 × 4.06 mm against the 4.0 × 4.0 mm footprint, so check the pads. Würth 74438356150 (4.1 × 4.1 mm) is A$18.42 at Mouser. SRN4018-150M (Isat 1.1 A) does **not** meet the 1.4 A spec | 9.90 | 12,689 | https://www.digikey.com.au/en/products/detail/bourns-inc/SRP4020TA-150M/4901000 |
| 10–14 | 0402 resistors | Mouser, exact Yageo parts: 100 of 4.7 k and 10 k (A$1.00 each), 10 each of 120 k, 22.1 k and 120 Ω (A$0.16 each) | 2.48 | all in stock | https://au.mouser.com/c/?q=RC0402FR-0710KL |
| 15 | SMBJ30A | DigiKey Good-Ark, 6 pcs | 2.82 | 4,442 | https://www.digikey.com.au/en/products/detail/good-ark-semiconductor/SMBJ30A/18649068 |
| 16 | LSM6DSOTR | Mouser, 7 pcs (DigiKey is on backorder to 26 Oct; RS has 178 left at A$7.66 each) | 41.51 | 1,125 | https://au.mouser.com/c/?q=LSM6DSOTR |
| 17 | LMR51606YDBVR | Mouser, 6 pcs. **Not carried by element14, RS or any AU retailer**; DigiKey has 1 | 13.92 | 7,851 | https://au.mouser.com/c/?q=LMR51606YDBVR |
| 18 | SN65HVD230DR | RS 218-4566, packs of 5, so 10 pcs. Out of stock at DigiKey, Mouser and element14. Mouser's SN65HVD230QDR (14 left) is A$34.56 for 6 | 43.60 | 115 | https://au.rs-online.com/web/p/can-interface-ics/2184566 |
| 19 | SD NAND | **Not sold in Australia.** No AU retailer, DigiKey or Mouser stocks any of the four parts listed in ORDER-SEEED.md, so buy it from LCSC (§1) | n/a | | https://www.digikey.com.au/en/products/result?keywords=ZDSD02GLGEAG |

**Shipping:**
- **DigiKey AU:** free from A$60, otherwise A$24, about 4 days (https://www.digikey.com.au/en/help-support/delivery-information/delivery-time-and-cost).
- **Mouser AU:** free over A$60 (https://au.mouser.com/).
- **element14 AU:** free from A$60 ex GST, otherwise A$24. This is from a search snippet; the live page was blocked.
- **RS AU:** free over A$80 ex GST for private accounts, otherwise A$20; 5–10 working days for global stock (https://au.rs-online.com/web/content/support/all-articles/delivery).

**Hobby retailers (checked, little use):**
- **Core Electronics** sells a JST-SH 4-pin SMD clone for A$0.20 (https://core-electronics.com.au/connector-sh-4pin-r-a-smd.html). It has the LSM6DSO only on breakout boards and no 0402 parts.
- **Altronics** sells SS14 in packs of 5 for A$3.35 inc GST (https://www.altronics.com.au/product/y0084-ss14-sma-do-214ac-schottky-diode-pk-5).
- **Jaycar and Wiltronics** have nothing useful for this BOM.
- **None of them** stock the bare ICs or the SD NAND.

**AliExpress:**
- **Generic parts:** SS14, SMBJ30A, 0402/0603/0805 passives and a JST-SH clone come to about A$30–40 for one pack of each, including GST and shipping, and take 1–4 weeks. Example listings:
  - SS14 ×100, A$4.93: https://www.aliexpress.com/item/1005012987928101.html
  - SMBJ30A ×20, A$2.92: https://www.aliexpress.com/item/1005012052808979.html
  - 0402 22.1 k ×100, A$2.32: https://www.aliexpress.com/item/1005005166921794.html
- **Not worth it:** LCSC sells genuine parts for less.
- **Unsuitable listings:** AliExpress has no 60 V 1812 PTC, and its "JST 1.25" connectors are often PicoBlade, not GH.
- **Counterfeit risk:**
  - LSM6DSOTR is listed at about A$2–3 each, against A$5.50–7.70 at distributors (https://www.aliexpress.com/item/1005009993708755.html).
  - SN65HVD230 is listed as "VP230" at about A$1 each.
  - An MKDV4GCL SD NAND listing exists, authenticity unknown.
  - Do not buy the IMU, buck regulator, CAN transceiver or SD NAND there.

## 3. Basket totals for the parts (5 boards plus spares)

| Basket | Full build | No-storage build | Delivery |
|---|---|---|---|
| **LCSC only (recommended)** | US$107.83 + about US$20 shipping (est.) = US$127.83 ≈ A$183, **≈ A$201 with GST** | US$56.24 + US$20 (est.) = US$76.24 ≈ A$109, **≈ A$120 with GST** | Ships in 1–3 days, then about 1–2 weeks (est.) |
| Mouser AU, lines 1–18, + LCSC for the SD NAND | Mouser A$147.96 + GST ≈ A$163; LCSC SD NAND US$51.59 + US$15 shipping (est.) ≈ A$105 with GST. **≈ A$268** | **≈ A$163**, Mouser only, with free shipping | Mouser about 4 days. Its 22 µF line is on backorder: use element14's part for that line |
| DigiKey AU, lines 1–18 | A$136.45 ex GST, ≈ A$150 + the SD NAND from LCSC ≈ **A$255** | **≈ A$150**, but the LSM6DSO and the GH connector are on backorder, and it needs SN65HVD231DR and LMR51606YFDBVR substitutes | About 4 days once in stock |
| element14 AU | Incomplete: no LMR51606, no SD NAND. A$160.68 ex GST for what it has | Incomplete: no LMR51606 | 3–5 days from UK stock |
| RS AU | Incomplete: no LMR51606, SD NAND or 60 V PTC. A$197.66 ex GST for what it has | Incomplete | 5–10 working days |

The full per-distributor tables, including the substitutes and every URL, are in the session notes `wavehat-sourcing-distributors.md`, `wavehat-sourcing-au-retail.md` and `wavehat-sourcing-fab-tools.md`.

## 4. DIY extras beyond the parts

### Bare boards and stencil

You only need **one stencil**. All three vendors offer "top and bottom on a single stencil", which carries both paste layers side by side. Order it **0.10–0.12 mm thick** for the 0.5 mm-pitch LGA.

| Item | Source | USD | A$ | Lead time | URL |
|---|---|---|---|---|---|
| **5 bare boards, ENIG (recommended)** | JLCPCB | 20.80 (10 boards: 22.10) | 29.74 | 3-day build | https://jlcpcb.com/quote |
| Frameless stencil, custom 100 × 100 mm, top + bottom on one stencil | JLCPCB | 3.10 | 4.43 | 1–2 days; ships with the boards | https://jlcpcb.com/resources/small-stencil |
| Shipping to AU, boards + stencil | JLCPCB UPS Saver | 9.84 | 14.07 | 5–7 business days (Global Standard Direct: US$8.76, 10–14 days) | https://jlcpcb.com/quote |
| **JLCPCB subtotal** | | **33.74** | **≈ 48** (≈ 53 with GST, est.) | **≈ 2 weeks door to door** | |
| 5 bare boards, ENIG (your quote: US$39) | Seeed Fusion | 39.90 (5 or 10 boards) | 57.06 | 4–5 working days | https://www.seeedstudio.com/fusion_pcb.html |
| Frameless stencil 10 × 15 cm, top + bottom on one stencil | Seeed Fusion | 8.90 | 12.73 | | https://support.seeed.cc/portal/en/kb/articles/fusion-pcb-stencil-specification |
| Shipping to AU, boards + stencil | Seeed DHL (Epacket: US$11.77, 15–25 days) | 24.76 | 35.41 | 3–5 working days | https://www.seeedstudio.com/fusion_pcb.html |
| **Seeed subtotal** | | **73.56** | **≈ 105** | ≈ 1.5–2 weeks | |
| Stencil, alternative | PCBWay, non-framework, top + bottom | 10.00 | 14.30 | AU shipping not checked | https://www.pcbway.com/stencil.aspx |

On Seeed, don't pick the 28 × 38 cm stencil: its weight pushes DHL to Australia up to US$106.80.

### Tools and consumables

Skip anything you already own. Prices are A$ including GST.

| Item | Pick | A$ | Notes | URL |
|---|---|---|---|---|
| SAC305 paste, bottom side | Core Electronics 10 g syringe | 20.35 | In stock | https://core-electronics.com.au/sac305-lead-free-solder-paste-10g-syringe.html |
| Low-temp paste, top side (Sn42Bi57.6Ag0.4, melts at 138 °C) | Chip Quik TS391LT, 15 g, DigiKey | ≈ 27.15 | 123 in stock, about 4 days | https://www.digikey.com.au/en/product-highlight/c/chip-quik/thermally-stable-solder-paste |
| Hotplate | FNIRSI HT-P1A 50 × 50 mm (Core), plus a USB-C PD supply (≈ A$40, est.) | 153.95 | 50 mm is marginal for the 54 mm board. A generic 100 × 100 mm plate is better: ≈ A$60–110 on AliExpress or eBay (est., not verified). The Miniware MHP30 (30 × 30 mm) is too small | https://core-electronics.com.au/fnirsi-ht-p1a-150w-mini-hot-plate-reflow-station.html |
| Hot-air station | Altronics T1285A, 320 W (a generic 858D is ≈ A$60–90, est.) | 269.00 | For rework and the second side | https://www.altronics.com.au/p/t1285a-micron-320w-smd-hot-air-re-work-station/ |
| Tack flux | Chip Quik SMD291, 10 cc (Core) | 39.80 | Dispatches 28 Oct – 2 Nov | https://core-electronics.com.au/chip-quik-tack-flux-10cc-syringe-with-plunger-and-tip-smd291.html |
| Flux pen | Altronics T1927 | 11.95 | For touch-up | https://www.altronics.com.au/p/t1927-no-clean-solder-flux-pen-12ml/ |
| ESD tweezers | Core ADA422 | 9.05 | | https://core-electronics.com.au/fine-tip-curved-tweezers-esd-safe-120mm.html |
| Kapton tape | Core, 16 mm × 33 m | 19.05 | For the stencil jig | https://core-electronics.com.au/16mm-x-33m-high-temperature-polyimide-tape.html |
| IPA, 1 L | Core | 18.10 | Price from cache | https://core-electronics.com.au/catalog/product/view/sku/CE04601 |
| Magnification | Jaycar QC3193 microscope with 4.3" screen | ≈ 139–159 | Price from cache. Essential for checking the 0402s and LGA alignment | https://jaycar.com.au/kits-science-learning/science-learning/microscopes/c/4CA |
| **Tool kit, budget** | Generic hotplate and 858D, both pastes, flux, tweezers, tape, IPA, Jaycar microscope | **≈ 410** (est.) | | |
| **Tool kit, mid-range** | FNIRSI plate and Altronics station instead | **≈ 700** (est.) | | |

## 5. DIY total vs Seeed PCBA (5 boards, using your own XIAOs)

**Seeed quotes you received (US$, 5 boards, each with Seeed's XIAO C6):**
- **No-storage build, final quote: US$314.67 delivered.** Shipping is free on PCB assembly orders.

  | Item | US$ |
  |---|---|
  | PCB: 10 bare ENIG boards (the price is the same for 5 or 10) | 39.90 |
  | Setup | 50.00 |
  | Consumables | 15.00 |
  | Components, including the XIAO C6 at 26.00 | 74.31 |
  | Assembly | 110.46 |
  | Subtotal | 289.67 |
  | 0.1 mm solder mask dam | 25.00 |
  | **Total** | **314.67** |

- **Ten assembled boards cost US$415.91:** US$376.01 PCBA plus US$39.90 PCB, or US$41.59 a board against US$62.93 a board for 5.
- **Full build, two-sided: US$370.** This earlier quote did not show the US$25 solder mask dam. With the dam it comes to about US$395 (est.).
  - Components total about US$119. The largest lines are the SD NAND (U5) at 45.59, the XIAO C6 at 26.00, the IMU (U1) at 23.14 and the buck converter (U2) at 8.15.
  - One-sided assembly saves US$81: the SD NAND (US$45.59) plus about US$35 of second-side setup and stencil. JLCPCB's published two-sided surcharge is about the same, US$33.77 (https://jlcpcb.com/help/article/pcb-assembly-price).
- **Earlier figure:** a quote of US$310 came before U5 and L1 were priced.

**Notes on the figures:**
- **Without the XIAO** (no-XIAO BOM), each quote drops by US$26. The no-storage build then costs **US$288.67**.
- **Solder mask dam on DIY boards:** if Seeed makes the bare boards, they would presumably carry the same US$25 charge. JLCPCB's standard green mask is generally quoted with a 0.1 mm minimum dam, but this was not verified on its quote form.
- **GST:** whether Seeed adds GST for Australia is not verified.
- **Coupons:** Seeed lists a US$50-off PCBA coupon for new customers until 2026-11-19 (https://www.seeedstudio.com/fusion_pcb.html). The 30 % XIAO discount is a coupon issued once an order that includes a XIAO is confirmed, so it doesn't help an order without one.

| | Full build | No-storage build |
|---|---|---|
| **Seeed PCBA, your own XIAOs** | ≈ US$369 (US$344 + US$25 dam, est.) ≈ **A$528** | US$288.67 ≈ **A$413** (US$314.67 ≈ A$450 with Seeed's XIAO) |
| DIY parts from LCSC, with GST and shipping (est.) | A$201 | A$120 |
| DIY boards + stencil from JLCPCB, with GST (est.) | A$53 | A$53 |
| **DIY, tools already owned** | **≈ A$254** | **≈ A$173** |
| Saving vs Seeed | **≈ A$274** | **≈ A$240** |
| DIY plus the budget tool kit (+A$410, est.) | ≈ A$664, **A$136 more** than Seeed | ≈ A$583, **A$170 more** than Seeed |
| DIY plus the mid-range tool kit (+A$700, est.) | ≈ A$954 | ≈ A$873 |
| Your time (est.) | ≈ 6–10 h: two stencil prints and two reflows per board, inspection, rework | ≈ 4–6 h |
| Calendar time (est.) | ≈ 2 weeks for parts and boards, then a weekend | same |
| **JLCPCB PCBA, no XIAO** | **A$355.95 (real quote**; shipping and GST not confirmed) | ≈ A$225 (est.) |
| Seeed calendar time (est.) | ≈ 3–4 weeks: 4–5 working days for the PCB, PCBA "from 7 working days", then shipping | same |

DIY also leaves you with 2 spare IMUs, a spare of each IC, and reels of passives.

**Third option: JLCPCB PCBA.**

**Real quote, full build:** A$355.95 for 5 assembled two-sided boards with the storage (U5 Zetta ZDSD02GLGEAG), ENIG, no XIAO. Files are in `kicad/fab/jlcpcb/full/`.

- Not yet confirmed: whether that figure includes shipping and GST.
- Placement needed three rotation fixes, U2 +180°, U3 −90° and U5 +180°, which are now in the CPL.
- The estimate below was ≈ A$350, so the quote matches it.

The estimate came from JLCPCB's published its assembly rates (https://jlcpcb.com/help/article/pcb-assembly-price, updated Sep 2026) and stocks every part of this BOM through LCSC.

| Fee | Full build, two-sided | No-storage build, one-sided |
|---|---|---|
| Setup | US$51.12 | US$25.56 |
| Stencil | US$16.42 | US$8.21 |
| Feeder loading, US$1.53 per part type | ≈ US$32 (21 types) | ≈ US$28 (18 types) |
| Joints, US$0.0016 each | ≈ US$1 | ≈ US$1 |
| **Assembly subtotal** | **≈ US$100** | **≈ US$62** |

Add about US$21 for the boards, the parts at LCSC prices (≈ US$85 full, ≈ US$42 no-storage) and about US$15 shipping:

- **Full build:** about US$220, ≈ **A$350** with GST.
- **No-storage build:** about US$140, ≈ **A$225** with GST.

The full-build quote confirms that arithmetic, so the no-storage estimate is probably close too. That puts JLCPCB's no-storage build within about A$50 of DIY, with no tools, labour or LGA risk. JLCPCB's full build (A$355.95) is about A$170 cheaper than Seeed's (≈ A$528) and only about A$100 more than DIY.

## 6. Hand-assembly risks, in plain words

**U1 LSM6DSO (LGA-14, 0.5 mm pitch, 2.5 × 3 mm).** This is the hard part.
- All its pads are underneath the chip, so you can't see or touch the joints.
- With a good stencil print, flux, careful alignment under the microscope and a hotplate, most hobbyists get it right most of the time. **Plan on one board in five needing rework** (est.).
- Without X-ray, test it electrically: read WHO_AM_I (0x6C) over I²C, then run the accelerometer and gyro self-test before fitting the board in its enclosure.
- To rework it: remove it with hot air, wick the pads flat, re-paste and reflow. The 2 spare IMUs cover chips damaged that way.

**U5 SD NAND (LGA-8, 1.27 mm pitch).**
- Much easier: the pads are large and widely spaced.
- Test it by letting the firmware mount and format it.

**Two-sided reflow order.**
1. **Bottom first** (U5 and 6 passives) with SAC305 paste, while the top is still bare so the board sits flat on the hotplate.
2. **Flip and do the top** with low-temp SnBi paste, so the bottom joints don't remelt. The board now has parts underneath: rest it on strips of scrap 1.6 mm FR-4 on the plate, or preheat it and finish from above with hot air.
3. **Fit the XIAO last** with an iron (14 large castellated pads).

**Caveats on the two-sided method.**
- **Brittle joints:** SnBi joints are more brittle under shock and vibration, which matters on a boat. The alternative is SAC305 on both sides, relying on surface tension to hold the light bottom parts during the second pass; they are well within the usual limit.
- **No-storage build:** this whole step disappears. One stencil print, one reflow, SAC305 throughout.

**Diagnosing faults.** Rev A is untested hardware. When a board misbehaves, you won't know at first whether the cause is an assembly fault or a design fault. Factory assembly with X-ray removes the first of the two.

## 7. Recommendation

1. **If you already own a hotplate or hot-air station and a microscope,** hand assembly is the cheapest route:
   - About **A$250 for the full build**, against about A$530 at Seeed without a XIAO (est.): a saving of about A$270.
   - About **A$175 for the no-storage build**, against A$413 at Seeed (US$288.67 for 5 without a XIAO): a saving of about A$240.
   - Against JLCPCB's full-build quote (A$355.95), DIY saves only about A$100.
   - What you pay with is a weekend of work and the LGA-14 risk.
   - Buy everything from **LCSC** (the only source for the SD NAND, and the cheapest by far) and the boards plus one top + bottom stencil from **JLCPCB**. Both ship from Shenzhen.
   - Order the LSM6DSO soon: LCSC had only 38 in stock.
2. **If you'd have to buy the tools (≈ A$410–700),** DIY costs more than Seeed for 5 boards. Use factory assembly instead:
   - **JLCPCB PCBA is the cheapest factory option**: A$355.95 for the full build (real quote; shipping and GST not confirmed), and ≈ A$225 for the no-storage build (est.; get it quoted).
   - Otherwise take **Seeed's no-XIAO quote**: US$288.67 for the no-storage build, about US$369 for the full build. At 10 boards Seeed is about US$42 a board.
3. **If speed matters more than price,** Mouser AU can supply every part except the SD NAND in about 4 days, with free shipping.
4. **Part-supply notes for any route:**
   - The Murata C4 (GRM31CR72A225KA73L) is obsolete. LCSC still has 2,465, and the in-stock replacements are Samsung CL31B225KCHSNNE or Yageo CC1206KKX7R0BB225 (both 2.2 µF 100 V X7R 1206).
   - The SN65HVD230DR is out of stock at DigiKey, Mouser and element14, but in stock at LCSC and RS.
