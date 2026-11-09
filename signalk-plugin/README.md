# signalk-seastate

A measured sea state in Signal K, from the heave a boat already has on its NMEA 2000 bus.

A B&G / Simrad / Lowrance **Precision-9** compass sends heave as PGN 127252 at 10 Hz, next to heading, pitch and roll. Signal K has a path for it (`environment.heave`), but the NMEA 2000 converter (`n2k-signalk`) has no mapping for that PGN, so it never arrives; and nothing, on the instruments or in Signal K, turns heave into a wave height. This plugin does both.

| Path | Units | What |
|---|---|---|
| `environment.heave` | m | The compass's heave, up positive, at 2 Hz (optional) |
| `environment.waves.significantHeight` | m | Hs = 4 √m0 over the last ~20 min, every ~102 s |
| `environment.waves.period` | s | Tp, the spectrum's peak. **null** when there is no clear peak |
| `environment.waves.meanPeriod` | s | Tz = √(m0/m2), zero-crossing period. null with Tp |
| `environment.waves.underway` | bool | The boat moved during the window (mean SOG above 1.5 kn, or above it for a quarter of the window): the periods are then Doppler-shifted. Needs `navigation.speedOverGround` |

`environment.heave` is in the Signal K specification. The `environment.waves.*` paths are **proposed**: they are the ones the [WaveHat](../README.md) sensor sends, named after the Weather API's `waveSignificantHeight` and `wavePeriod`. Each is sent with its units and description, so the server shows them properly.

## How it works

1. Heave arrives from the server's `N2KAnalyzerOut` event (canboatjs's decoding of every PGN), filtered to 127252, following one source address. Or, set the input to a Signal K path and it takes heave from there (a WaveHat's `environment.heave`, say).
2. Samples are averaged into 0.4 s bins (2.5 Hz). The averaging's roll-off is divided back out of the spectrum.
3. Welch's method: 512-point Hann segments (205 s), 50 % overlap, the last 11 averaged (~20 min). First result after 5 segments (~10 min).
4. Hs, Tp and Tz from the spectral moments over 0.04–0.5 Hz (25 s to 2 s). Tp by a 3-bin smoothed peak with log-parabolic interpolation.
5. Tp and Tz are sent only if Hs is at least 0.05 m, the peak is inside the band and it stands at least 2× above the band's median.
6. A silence of more than 5 s in the heave starts the window again.

The maths is [`seastate.js`](seastate.js), with no dependencies. It is the WaveHat firmware's wave maths (`../firmware/lib/wavemath`, `../firmware/desktop/wavemath.py`) from the point where that has a displacement.

## What this is and is not

It measures **the boat's** vertical motion where the compass sits, not the water's. A hull follows long swell closely and short chop less, so Hs reads a little low in a short sea; and a compass away from the hull's roll and pitch centre moves up and down as the boat rolls, which reads as extra heave. How much depends on the compass's own heave filter, which Navico doesn't publish. Comparing this against a WaveHat at the roll/pitch centre (which corrects for its mounting position and logs both) is the experiment this plugin was written for.

One sensor gives no wave direction.

## Install

Until it is on npm, from a checkout:

```bash
cd ~/.signalk && npm install /path/to/wavehat/signalk-plugin
```

Restart the server, then enable **Sea state from heave** under Server → Plugin Config. The plugin's status line shows "Waiting for NMEA 2000 PGN 127252", then a countdown to the first result, then the latest Hs and Tp.

To check that the compass is sending heave at all, look for PGN 127252 in the server's Data Browser source list or with `candump`; a Precision-9 sends it at 10 Hz.

## Tests

```bash
npm test
```

Ten tests: single swell, mixed sea, short chop, flat calm, slow drift, a gap in the input, and the plugin driven end to end by a stand-in for the server (PGN in, deltas out, a second source ignored, metadata once, the path input).

## Status (9 Nov 2026)

The maths is tested against known seas. The plugin has **not yet run on a Signal K server with a real compass**: the event name and field names (`Heave`, or `heave` with camelCase enabled) are from the canboatjs and server documentation, and both spellings are handled.

MIT licence.
