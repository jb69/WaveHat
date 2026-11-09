# WaveHat wave maths: accuracy on synthetic seas

93 runs per method, 20 min analysis window (14 Welch segments).

- **calibrated**: Hs bias +0.0 %, RMS 3.1 %, worst -11.4 %; Tp bias -1.1 %, RMS 3.8 %, worst -18.1 %; Tz (vs band-limited) bias +0.2 %, worst -4.1 %
- **uncalibrated**: Hs bias +0.4 %, RMS 3.8 %, worst +12.7 %; Tp bias -1.1 %, RMS 3.9 %, worst -18.3 %; Tz (vs band-limited) bias +0.3 %, worst -5.0 %
- **ideal sensor**: Hs bias +0.0 %, RMS 3.2 %, worst -11.8 %; Tp bias -1.0 %, RMS 3.8 %, worst -18.1 %; Tz (vs band-limited) bias +0.2 %, worst -4.0 %
- **no tilt correction**: Hs bias +86.0 %, RMS 161.3 %, worst +594.9 %; Tp bias +179.5 %, RMS 260.3 %, worst +650.2 %; Tz (vs band-limited) bias +46.6 %, worst +247.6 %
- **flat calm** (sensor noise and bias only): Hs reads 0.6 cm at most
- **period gate** (Tp, Tz withheld below Hs 5 cm, with the peak on a band edge, or the peak under 2x the band median): periods reported in 90 of 90 sea runs (lowest peak ratio 2.9), withheld in 3 of 3 flat-calm runs

## Per sea state (calibrated board, both spectra, all seeds)

| Sea state (Hs, Tp, RMS roll) | Runs | Hs error mean / worst | Tp error mean / worst | Tz error vs band-limited truth | Heave RMS error (time domain) |
|---|---|---|---|---|---|
| 0.3 m, 3 s, 5° | 6 | -7.9 % / -11.4 % | +0.7 % / +7.1 % | +0.5 % / +1.2 % | +0.7 % / +1.3 % |
| 0.5 m, 4 s, 5° | 6 | -1.4 % / -3.5 % | +0.9 % / +3.6 % | +0.6 % / +0.9 % | +0.3 % / +0.9 % |
| 0.8 m, 5 s, 5° | 6 | +0.3 % / +3.3 % | -2.7 % / -9.2 % | +0.4 % / +0.8 % | +0.1 % / +0.8 % |
| 1.0 m, 6 s, 5° | 6 | +0.7 % / +3.2 % | -1.1 % / -4.0 % | +0.1 % / +0.8 % | -0.1 % / -0.6 % |
| 1.5 m, 7 s, 5° | 6 | -0.4 % / -3.8 % | -3.6 % / -9.5 % | -0.4 % / -1.0 % | -0.2 % / -0.6 % |
| 2.0 m, 8 s, 5° | 6 | +0.5 % / +2.7 % | +2.2 % / +4.0 % | +0.2 % / +0.5 % | -0.1 % / -0.4 % |
| 2.5 m, 9 s, 5° | 6 | +1.7 % / +3.6 % | -1.0 % / -2.7 % | +0.7 % / +1.2 % | -0.1 % / -0.3 % |
| 1.0 m, 10 s, 5° | 6 | +2.2 % / +3.0 % | +0.3 % / +3.1 % | +0.8 % / +1.9 % | -0.1 % / -0.3 % |
| 3.0 m, 10 s, 5° | 6 | +2.2 % / +3.1 % | +0.3 % / +3.1 % | +0.8 % / +1.9 % | -0.1 % / -0.2 % |
| 0.5 m, 12 s, 5° | 6 | +0.3 % / +2.1 % | -5.0 % / -9.7 % | -0.3 % / +1.8 % | +0.0 % / +0.3 % |
| 4.0 m, 12 s, 5° | 6 | +0.2 % / +2.2 % | -5.0 % / -9.6 % | -0.3 % / +1.7 % | -0.2 % / -0.4 % |
| 1.5 m, 14 s, 5° | 6 | -1.5 % / -8.8 % | -3.2 % / -18.1 % | -0.9 % / -4.1 % | -0.2 % / -0.4 % |
| 1.0 m, 6 s, 15° | 6 | +0.8 % / +3.1 % | -1.1 % / -4.0 % | +0.1 % / +1.0 % | +1.1 % / +4.0 % |
| 2.0 m, 8 s, 15° | 6 | +0.6 % / +2.7 % | +2.2 % / +4.0 % | +0.2 % / +0.5 % | +0.2 % / +0.9 % |
| 3.0 m, 10 s, 15° | 6 | +2.2 % / +3.0 % | +0.3 % / +3.1 % | +0.8 % / +1.9 % | +0.0 % / -0.2 % |
