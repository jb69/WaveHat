"""Run the wave maths over a matrix of synthetic sea states and report errors.

    python3 evaluate.py            # full matrix, ~2 min on 8 cores
    python3 evaluate.py --quick    # 1 seed per case

Writes results/results.csv, results/summary.md and results/accuracy.png.
"""

from __future__ import annotations

import argparse
import csv
import math
import os
from concurrent.futures import ProcessPoolExecutor

import numpy as np

import seasim as ss
import wavemath as wm

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results")

# (Hs m, Tp s): wind sea from chop to a gale, plus long low swell. Steepness
# stays below breaking (Hs / (1.56 Tp^2) < 1/15).
SEAS = [(0.3, 3), (0.5, 4), (0.8, 5), (1.0, 6), (1.5, 7), (2.0, 8), (2.5, 9),
        (3.0, 10), (4.0, 12), (1.0, 10), (1.5, 14), (0.5, 12)]
HEAVY_ROLL = [(1.0, 6), (2.0, 8), (3.0, 10)]  # rolled hard: 15 deg RMS roll, 5 pitch


def cases(seeds):
    out = []
    for gamma in (3.3, 1.0):
        for hs, tp in SEAS:
            for seed in seeds:
                out.append(dict(hs_nom=hs, tp_nom=tp, gamma=gamma, roll=5.0, pitch=2.0, seed=seed))
        for hs, tp in HEAVY_ROLL:
            for seed in seeds:
                out.append(dict(hs_nom=hs, tp_nom=tp, gamma=gamma, roll=15.0, pitch=5.0, seed=seed))
    for seed in seeds:
        out.append(dict(hs_nom=0.0, tp_nom=8, gamma=3.3, roll=0.0, pitch=0.0, seed=seed))  # flat calm
    return out


def run_case(c):
    sea = ss.SeaState(c["hs_nom"], c["tp_nom"], gamma=c["gamma"], roll_deg=c["roll"],
                      pitch_deg=c["pitch"])
    rows = []
    for method, ideal, attitude, cal in (("calibrated", False, True, ss.CALIBRATED),
                                         ("uncalibrated", False, True, {}),
                                         ("ideal sensor", True, True, {}),
                                         ("no tilt correction", False, False, ss.CALIBRATED)):
        rec = ss.simulate(sea, duration=1500.0, seed=c["seed"], ideal=ideal, **cal)
        p = wm.WaveProcessor(wm.Config(attitude=attitude))
        stats, heave = p.run(rec.gyro, rec.accel)
        s = stats[-1]
        n = int(s.segments * p.cfg.hop * p.cfg.decimation)
        rows.append(dict(c, method=method, hs_true=rec.hs_true, hs_band=rec.hs_band,
                         tp_true=rec.tp_true, tz_true=rec.tz_true, tz_band=rec.tz_band,
                         heave_rms_true=float(np.std(rec.heave[-n:])),
                         hs=s.hs, tp=s.tp, tz=s.tz, heave_rms=s.heave_rms,
                         heave_rms_td=s.heave_rms_td, segments=s.segments,
                         periods_valid=int(s.periods_valid), peak_ratio=s.peak_ratio))
    return rows


def pct(a, b):
    return 100.0 * (a - b) / b if b else float("nan")


def summarise(rows):
    for r in rows:
        r["hs_err"] = pct(r["hs"], r["hs_true"])
        r["tp_err"] = pct(r["tp"], r["tp_true"])
        r["tz_err"] = pct(r["tz"], r["tz_true"])
        r["tz_band_err"] = pct(r["tz"], r["tz_band"])
        r["heave_td_err"] = pct(r["heave_rms_td"], r["heave_rms_true"])
    return rows


def write_csv(rows, path):
    keys = list(rows[0].keys())
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, keys)
        w.writeheader()
        for r in rows:
            w.writerow({k: (f"{v:.4f}" if isinstance(v, float) else v) for k, v in r.items()})


def table(rows):
    """Markdown table: one line per sea state, calibrated board, all seeds/spectra."""
    fw = [r for r in rows if r["method"] == "calibrated" and r["hs_nom"] > 0]
    groups = {}
    for r in fw:
        groups.setdefault((r["hs_nom"], r["tp_nom"], r["roll"]), []).append(r)
    lines = ["| Sea state (Hs, Tp, RMS roll) | Runs | Hs error mean / worst | Tp error mean / worst | Tz error vs band-limited truth | Heave RMS error (time domain) |",
             "|---|---|---|---|---|---|"]

    def mw(v):
        v = np.array(v)
        return f"{np.mean(v):+.1f} % / {v[np.argmax(np.abs(v))]:+.1f} %"
    for (hs, tp, roll), g in sorted(groups.items(), key=lambda kv: (kv[0][2], kv[0][1], kv[0][0])):
        lines.append(f"| {hs:.1f} m, {tp:.0f} s, {roll:.0f}° | {len(g)} | {mw([r['hs_err'] for r in g])} | "
                     f"{mw([r['tp_err'] for r in g])} | {mw([r['tz_band_err'] for r in g])} | "
                     f"{mw([r['heave_td_err'] for r in g])} |")
    return "\n".join(lines)


def overall(rows, method, key):
    v = np.array([r[key] for r in rows if r["method"] == method and r["hs_true"] > 0])
    v = v[np.isfinite(v)]
    return np.mean(v), np.sqrt(np.mean(v ** 2)), v[np.argmax(np.abs(v))]


def chart(rows, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    surface, ink, ink2, grid = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
    colors = {"calibrated": "#2a78d6", "uncalibrated": "#eb6834"}
    plt.rcParams.update({"font.size": 10, "axes.edgecolor": grid, "axes.labelcolor": ink2,
                         "xtick.color": ink2, "ytick.color": ink2, "text.color": ink})
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), facecolor=surface)
    rng = np.random.default_rng(0)
    offset = {"calibrated": -0.17, "uncalibrated": 0.17}
    panels = (("hs_err", "Significant wave height Hs: error, %"),
              ("tp_err", "Peak period Tp: error, %"))
    for ax, (key, title) in zip(axes, panels):
        ax.set_facecolor(surface)
        ax.axhspan(-10, 10, color="#efeeea", zorder=0, lw=0)
        ax.axhline(0, color=ink2, lw=0.8, zorder=1)
        for method, col in colors.items():
            pts = [r for r in rows if r["method"] == method and r["hs_true"] > 0]
            x = (np.array([r["tp_true"] for r in pts]) + offset[method]
                 + rng.uniform(-0.08, 0.08, len(pts)))
            y = np.array([r[key] for r in pts])
            ax.scatter(x, y, s=22, color=col, edgecolor=surface, linewidth=1.0,
                       label={"calibrated": "after six-face calibration",
                              "uncalibrated": "uncalibrated (±20 mg, ±1 %)"}[method],
                       zorder=3)
        ax.set_title(title, loc="left", fontsize=11, color=ink)
        ax.set_xlabel("True peak period Tp, s")
        ax.grid(axis="y", color=grid, lw=0.6)
        ax.set_axisbelow(True)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        ax.set_xticks(range(3, 15))
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, frameon=False, loc="upper right", ncol=2, fontsize=9)
    for ax in axes:
        ax.set_ylim(-20, 20)
    fig.text(0.01, 0.01, "Synthetic JONSWAP and Pierson-Moskowitz seas, 0.3-4 m, 3-14 s, 5° and 15° RMS roll, "
             "simulated LSM6DSO noise, offset, scale error and mount tilt. Shaded: ±10 %.",
             fontsize=8, color=ink2)
    fig.tight_layout(rect=(0, 0.04, 1, 0.93))
    fig.savefig(path, dpi=150, facecolor=surface)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--chart-only", action="store_true", help="redraw from results.csv")
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    if args.chart_only:
        with open(os.path.join(OUT, "results.csv")) as f:
            rows = [{k: (v if k == "method" else float(v)) for k, v in r.items()}
                    for r in csv.DictReader(f)]
        chart(rows, os.path.join(OUT, "accuracy.png"))
        return
    seeds = [1] if args.quick else [1, 2, 3]
    with ProcessPoolExecutor() as ex:
        rows = [r for rs in ex.map(run_case, cases(seeds)) for r in rs]
    rows = summarise(rows)
    write_csv(rows, os.path.join(OUT, "results.csv"))
    chart(rows, os.path.join(OUT, "accuracy.png"))

    calm = [r for r in rows if r["hs_true"] == 0 and r["method"] == "calibrated"]
    lines = ["# WaveHat wave maths: accuracy on synthetic seas", "",
             f"{len([r for r in rows if r['method'] == 'calibrated'])} runs per method, "
             f"20 min analysis window (14 Welch segments).", ""]
    for method in ("calibrated", "uncalibrated", "ideal sensor", "no tilt correction"):
        hs = overall(rows, method, "hs_err")
        tp = overall(rows, method, "tp_err")
        tz = overall(rows, method, "tz_band_err")
        lines.append(f"- **{method}**: Hs bias {hs[0]:+.1f} %, RMS {hs[1]:.1f} %, worst {hs[2]:+.1f} %; "
                     f"Tp bias {tp[0]:+.1f} %, RMS {tp[1]:.1f} %, worst {tp[2]:+.1f} %; "
                     f"Tz (vs band-limited) bias {tz[0]:+.1f} %, worst {tz[2]:+.1f} %")
    if calm:
        lines.append(f"- **flat calm** (sensor noise and bias only): Hs reads "
                     f"{max(r['hs'] for r in calm) * 100:.1f} cm at most")
    cal = [r for r in rows if r["method"] == "calibrated"]
    seas = [r for r in cal if r["hs_true"] > 0]
    kept = [r for r in seas if int(r["periods_valid"])]
    lines.append(f"- **period gate** (Tp, Tz withheld below Hs 5 cm, with the peak on a band edge, or the peak "
                 f"under 2x the band median): periods reported in {len(kept)} of {len(seas)} sea runs "
                 f"(lowest peak ratio {min(float(r['peak_ratio']) for r in seas):.1f}), withheld in "
                 f"{len([r for r in cal if r['hs_true'] == 0 and not int(r['periods_valid'])])} of "
                 f"{len([r for r in cal if r['hs_true'] == 0])} flat-calm runs")
    lines += ["", "## Per sea state (calibrated board, both spectra, all seeds)", "", table(rows), ""]
    with open(os.path.join(OUT, "summary.md"), "w") as f:
        f.write("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
