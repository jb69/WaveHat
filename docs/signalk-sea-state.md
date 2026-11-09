# A measured sea state for Signal K

*Why Signal K has no measured wave height, what the maths has to do to get one from a boat's motion, where the result lands in the specification, and how a boat with a heave-capable compass can try it today with no hardware.* Written November 2026; the status section says what has and hasn't been tested.

## The gap

Signal K knows nearly everything about the water around a boat: depth, wind, current, temperature, pressure, and through the Weather API even a forecast wave height. What it has no *measured* value for is the sea the boat is actually sitting in. `environment.heave` is in the specification, but almost nothing produces it, and there is no path at all for a measured significant wave height or period. So "is this anchorage going to be miserable at 2 am", "has the swell dropped enough to leave" and "what was it really like last night" get answered by looking out the hatch, or by a buoy fifty miles away.

An IMU can measure this directly. The boat is the buoy: a hull at anchor follows the long waves closely, and a 20-minute record of its vertical motion gives the same statistics a wave buoy reports.

## What WaveHat is

A 21 × 69 mm carrier board for a Seeed XIAO ESP32 (C3, C6 or S3), with:

- an ST LSM6DSO accelerometer and gyro, sampled at 26 Hz into its FIFO and read every 250 ms;
- a 12 V buck input from the NMEA 2000 backbone (Micro-C) and **listen-only** CAN: it never transmits, not even an ACK, so it needs no address and can't disturb the network;
- 256 MB of SD NAND soldered on the board, so every result is logged on the node whether or not Wi-Fi is up;
- JST-GH ports for a GNSS module and a Qwiic/I²C sensor, a 10-pin IO header, and a 1S battery option for a standalone node;
- [SensESP](https://signalk.org/SensESP/) firmware: web UI for configuration, OTA updates, Signal K deltas over WebSocket.

The printed box around it is roughly 33 × 89 × 23 mm before the mounting ears and the cable gland. Power has not been measured yet; from the datasheets, with Wi-Fi up and streaming, expect 0.3 to 0.6 W, about 40 mA from a 12 V backbone (LEN 2), with brief peaks when the radio transmits.

The same board runs a second life as an eFoil telemetry node under [VESC Express](https://github.com/vedderb/vesc_express), which is where the circuit came from; the yacht firmware is the one described here.

## What the maths does

The hard part isn't the hardware, it's turning hull acceleration into wave statistics without lying.

1. **Attitude.** A Mahony filter fuses gyro and accelerometer so the node knows which way is up, and the acceleration is rotated into the earth frame. Skip that and 15° of roll reads as +86 % on wave height.
2. **Lever arm.** The IMU is never at the hull's roll/pitch centre, so rolling and pitching swing it up and down. You enter the box's offset from that centre (x starboard, y forward, z up, in metres; a tape measure is fine) and the lever-arm term is removed. A metre off the centreline is +10 to +87 % on Hs uncorrected, depending on the roll period. On a wide catamaran this matters: the bridgedeck centreline near the mast step is where the box wants to be.
3. **Heave.** Vertical acceleration is high-passed at 0.02 Hz and integrated twice to displacement, published as `environment.heave` at 4 Hz.
4. **Spectrum.** Every 79 s a 512-point Welch segment (Hann window, 50 % overlap, at 3.25 Hz after decimation) gives a heave spectrum; the last ~20 minutes (14 segments) are averaged. From the spectral moments over 0.04–0.5 Hz (2 to 25 s): Hs = 4 √m0, Tp (the peak period) and Tz = √(m0/m2) (the zero-crossing period).
5. **Honest nulls.** Tp and Tz go out as null when there is no clear peak (Hs below 0.05 m, or the peak less than twice the band's median). No "0.0 m at 22 s" in the data browser.
6. **Underway.** A flag: speed over ground above 1.5 kn for the window means the spectrum is Doppler-shifted and the periods aren't trustworthy, so consumers can ignore them. SOG comes off the NMEA 2000 bus, from the GNSS port, or from Signal K if the node is Wi-Fi only.

On synthetic seas (93 runs, Hs 0.3–4 m, Tp 4–14 s, with roll and pitch), Hs comes out within 3 % RMS after a six-face accelerometer calibration done once in the web UI, and the per-sample chain costs 0.4 % of an ESP32-C3. The same C++ runs on the desktop against a Python reference, so the firmware maths is tested before it meets a boat. Details and the results tables are in [`firmware/README.md`](../firmware/README.md).

## Where it lands in the Signal K specification

This is as much a spec question as a sensor one, and a second opinion from people running real Signal K boats is wanted.

- **`environment.heave` already exists** in the vessel schema: units m, "Vertical movement of the vessel due to waves". NMEA 2000 has a matching message, PGN 127252 Heave (0.01 m resolution, with a field for the delay the heave calculation added). Some rate-gyro compasses send it: the B&G / Simrad / Lowrance Precision-9 puts heave on the bus at 10 Hz alongside heading, pitch and roll. But as far as we can find, `n2k-signalk` has no mapping for 127252, so it stops at the CAN bus: the path is in the spec, the data is on many backbones, and the two never meet. WaveHat fills `environment.heave` at 4 Hz from its own IMU, with a filter and a mounting correction you can see and change.
- **Nothing in the vessel schema holds a measured sea state.** `environment` has ten groups: outside, inside, water, depth, current, tide, heave, wind, time, mode. `water` is temperature and salinity; `tide` is heights and times. Wave height and period appear nowhere; the only "wave" in the whole schema is in heave's description.
- **The Weather API has the words, but from a provider.** `WeatherData.water` carries `waveSignificantHeight`, `wavePeriod`, `waveDirection`, `swellHeight`, `swellPeriod`, `swellDirection` and `seaStateValue` (Beaufort), typed as observation, daily or point forecast, and all of it comes from a Weather Provider plugin, i.e. a web service. So Signal K can tell you the forecast swell for your position, but not the swell you're sitting in. Nor can the instruments: heading, trim, heel and an instantaneous heave number, yes; significant wave height and period, no. Nobody on the boat is doing the statistics.

So WaveHat sends `environment.heave` as the standard path, and these as proposed ones:

| Path | Units | What |
|---|---|---|
| `environment.waves.significantHeight` | m | Hs = 4 √m0 over the last ~20 min |
| `environment.waves.period` | s | Tp, spectral peak; null when there's no clear peak |
| `environment.waves.meanPeriod` | s | Tz = √(m0/m2), zero-crossing; null with Tp |
| `environment.waves.underway` | bool | the window was Doppler-shifted by boat speed |

Each delta carries its metadata (units, description), so a server shows them properly before the spec knows them. The names deliberately mirror the Weather API's `waveSignificantHeight` / `wavePeriod`, so a forecast and a measurement sit side by side with the same vocabulary.

**Open question.** A new `environment.waves` group (clean, and matches how `wind` and `current` are their own groups), or `environment.water.waveSignificantHeight` and friends, a flatter mirror of the Weather API's `water.*` block, whose source comment says it is "aligned with Signal K environment specification"? OpenCPN's Signal K input already reads `environment.water.waves.*` paths (from its AIS decoding), which is a third candidate and a reason to look before choosing. Direction isn't in the table yet because one IMU can't measure it; two nodes, or an IMU plus the boat's heading and the roll/pitch cross-spectrum, could. When this is settled the intention is a pull request to `signalk/specification` for the `environment` schema, with real logged data behind it. Opinions to the issue tracker, please.

## Two heave sources, one boat

If your compass already sends PGN 127252, you have a second, independent heave signal, and three things fall out of that:

- **A software-only first step.** The wave maths doesn't care where heave comes from. [`signalk-plugin/`](../signalk-plugin/) is a Signal K server plugin (`signalk-seastate`) that picks PGN 127252 out of the server's N2K stream, publishes it as `environment.heave`, and runs the same Welch/moments code to give Hs, Tp and Tz from the compass you already have, before any board arrives. Install it and your boat has a measured sea state in Signal K this evening.
- **A proper comparison.** A compass sits where the magnetics are good, not where the motion is small, and manufacturers don't publish their heave filters or whether they correct for mounting position. WaveHat sits at the roll/pitch centre with a known 0.02 Hz high-pass and a lever-arm correction. Logging both tells us how much of a compass's "heave" on a given hull is really roll and pitch, which is a number nobody seems to have published.
- **WaveHat listens to the bus anyway**, so it logs the compass's heave statistics next to its own, row for row, on its own storage.

## The box, for the printer

The enclosure is [OpenSCAD](../enclosure/), not a STEP file someone else owns: a gasketed base and lid in ASA or PETG, a TPU gasket and USB plug, M2 heat-set inserts for the board, M3 for the lid, four M4 slotted ears to the boat and a PG7 gland for the Micro-C lead. Every dimension is a parameter at the top of the file, so if you want the ears to land on a particular frame spacing, or a flatter lid, it's a number change and a reprint. Same for the pogo-pin [test jig](../hardware/test-plate/) that checks every net on a bare board in one press.

## Where to mount it

Pure heave is the same everywhere on a rigid hull: the whole boat goes up and down together. What differs by position is the contamination from roll and pitch, which is lever arm × angular acceleration. The firmware removes that term from the offset you enter, so a box a metre off-centre still gives the right answer in principle, but the correction is only as good as the measured offset, the gyro noise and the assumption that the hull is rigid. At the motion centre the term is near zero and none of that matters. So mount as close as you can, enter what's left, and let the correction clean up the residual rather than carry the load.

- **Monohull:** on the centreline, low, near midships; the roll centre is near the waterline and the pitch centre near the middle of the waterline length.
- **Catamaran:** the roll centre is on the bridgedeck centreline, roughly at the waterline, and the pitch centre near midships. Low in the bridgedeck near the mast step, on structure, is as good as it gets. It is also where a compass is least likely to be, which is what makes the compass-heave comparison above interesting on a cat.
- Measure the offset from the mast step or a frame, not by eye: 0.3 m of error in x is tolerable, a metre isn't.
- Bolt to structure, not to a panel. A locker lid that flexes under the box reads as motion.

## What a test boat needs

- a mounting spot near the roll/pitch centre as above, bolted to structure, with the offset measured;
- 12 V from the backbone or a USB-C supply, and Wi-Fi to the Signal K server;
- ten minutes in the web UI: mounting offset, calibration, done.

What you get: a measured sea state in Signal K and on your displays, an on-board log of every anchorage you sit in (a heave trace and a 20-minute Hs line are about the most satisfying graphs a boat can draw in Grafana), and a board that's yours to hack. Everything is in this repository: KiCad generated from a Python description, so the board is reproducible; firmware; the Python maths and test harness; the plugin; the enclosure.

## Where it stands, honestly

As of November 2026: rev A boards have run on the bench. Rev B (GNSS port, IO header, battery option) is at the fab. The plugin's maths is tested against known seas and it has not yet met a real compass. **No boat has been to sea with one yet.** The first boats to do so will be finding the problems, not buying a product; that is the deal, and it's why the whole design is open.

If you'd rather have the raw 26 Hz IMU stream to play with yourself, open an issue; it's a build flag away.
