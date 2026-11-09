# IMU lever arm: Hs error by mounting position

From `lever_arm.py` (21 Oct 2026): seasim's calibrated board, 25 min runs, mean of 2 seeds, final 20-min window. The simulator scales roll to a fixed RMS (5° or 15°), which overstates roll in the 0.5 m sea; the 1-2 m rows are the realistic ones. Positions are from the hull's roll/pitch centre: X to starboard, Y forward.

```
sea                IMU position              Hs err    Tp err
0.5 m 5 s roll5    at centre                  +0.8%     -0.3%
0.5 m 5 s roll5    0.3 m off centreline      +17.7%     -0.5%
0.5 m 5 s roll5    1 m off centreline        +61.1%     -0.6%
0.5 m 5 s roll5    5 m forward                +6.1%     -0.6%
0.5 m 5 s roll5    1 m off, 5 m fwd          +57.2%     -2.1%
1.0 m 6 s roll5    at centre                  +0.8%     -1.1%
1.0 m 6 s roll5    0.3 m off centreline       +8.2%     -1.6%
1.0 m 6 s roll5    1 m off centreline        +27.5%     -2.5%
1.0 m 6 s roll5    5 m forward               -12.7%     -0.8%
1.0 m 6 s roll5    1 m off, 5 m fwd          +10.4%     -2.3%
2.0 m 8 s roll5    at centre                  +0.5%     +1.0%
2.0 m 8 s roll5    0.3 m off centreline       +3.0%     +0.9%
2.0 m 8 s roll5    1 m off centreline         +9.6%     +0.8%
2.0 m 8 s roll5    5 m forward                -8.1%     +1.2%
2.0 m 8 s roll5    1 m off, 5 m fwd           -0.5%     +1.1%
1.0 m 6 s roll15   at centre                  +0.7%     -1.1%
1.0 m 6 s roll15   0.3 m off centreline      +23.7%     -2.3%
1.0 m 6 s roll15   1 m off centreline        +86.9%     -3.9%
1.0 m 6 s roll15   5 m forward               -12.5%     -0.7%
1.0 m 6 s roll15   1 m off, 5 m fwd          +67.4%     -4.2%
```

At the centre the maths is within 1 %. One metre off the centreline adds +10 % (2 m / 8 s sea) to +87 % (1 m / 6 s, 15° roll); 0.3 m adds +3 to +24 %. Forward of the pitch centre the error has the other sign (pitch and heave partly cancel). The firmware has no term for this and the docs give no mounting rule: REVIEW.md gap G1.
