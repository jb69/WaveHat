#!/usr/bin/env python3
"""WaveHat -> Exodus radar: write ~/.swell.json from Signal K.

Runs on the boat computer next to the Signal K server. Every minute it reads
the WaveHat's sea-state paths from the Signal K REST API and, if they are
fresh and were not measured underway, writes the file the Exodus radar's swell
display reads (format: reference/sailing-exodus/01-radar/source/README.md):

    {"t": <unix time>, "hs_ft": 3.0, "period_s": 8}

No direction is written: one IMU cannot give a reliable swell direction, and
the radar then shows height and period without direction bars.

"t" is when the WaveHat measured the values (the older of the Hs and Tp
timestamps), not when this script ran, so the radar's 10-minute limit counts
from the measurement. The file is not refreshed, and the radar stops drawing
swell, when:
  * the data is more than 10 minutes old (a WaveHat that stopped);
  * the boat was underway (periods are distorted), or nothing says it was not:
    underway missing, or older than the result (no SOG reached the WaveHat).
    --assume-anchored writes anyway, for a boat with no SOG anywhere;
  * there is no wave period (the WaveHat sends null in flat calm, or when the
    spectrum has no clear peak inside its band).

    python3 swell_bridge.py                     # loop, http://localhost:3000
    python3 swell_bridge.py --once --verbose
    SIGNALK_TOKEN=... python3 swell_bridge.py   # if the server needs a token

The Exodus radar reads /home/pi/.swell.json; --out defaults to ~/.swell.json,
the same file when this runs as the pi user.

Standard library only.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime

M_PER_FT = 0.3048
MAX_AGE_S = 10 * 60   # WaveHat publishes every ~79 s; the radar's own limit is 10 min too
UNDERWAY_SLACK_S = 120  # underway is sent with each result; older than this = not this result


def parse_ts(ts: str | None) -> float | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def fetch_waves(server: str, token: str | None) -> dict:
    url = server.rstrip("/") + "/signalk/v1/api/vessels/self/environment/waves"
    req = urllib.request.Request(url)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.load(r)


def swell_from_waves(waves: dict, now: float, assume_anchored: bool = False) -> tuple[dict | None, str]:
    """Return (swell.json content, reason) from the Signal K waves object."""
    hs = waves.get("significantHeight") or {}
    tp = waves.get("period") or {}
    underway = waves.get("underway") or {}
    if hs.get("value") is None:
        return None, "no WaveHat data in Signal K"
    t_hs, t_tp = parse_ts(hs.get("timestamp")), parse_ts(tp.get("timestamp"))
    if t_hs is None:
        return None, "Hs has no timestamp"
    if now - t_hs > MAX_AGE_S:
        return None, f"data is {int(now - t_hs)} s old"
    # Tp is sent with every result, as a number or as null; an older Tp is a past result's.
    if tp.get("value") is None or t_tp is None or t_tp < t_hs - UNDERWAY_SLACK_S:
        return None, "no wave period (flat calm, or no clear peak in the spectrum)"
    t_uw = parse_ts(underway.get("timestamp"))
    if underway.get("value") is None or t_uw is None or t_uw < t_hs - UNDERWAY_SLACK_S:
        if not assume_anchored:
            return None, "underway unknown (no SOG reached the WaveHat); --assume-anchored to write anyway"
    elif underway["value"] is True:
        return None, "measured underway: periods are not meaningful"
    return {"t": int(min(t_hs, t_tp)),
            "hs_ft": round(float(hs["value"]) / M_PER_FT, 1),
            "period_s": round(float(tp["value"]), 1)}, "ok"


def http_reason(code: int) -> str:
    if code in (401, 403):
        return (f"Signal K refused the request (HTTP {code}): set SIGNALK_TOKEN to a device token "
                "(Security > Devices in the server's admin UI), or allow read-only access")
    if code == 404:
        return ("no environment.waves in Signal K yet (HTTP 404): the WaveHat's first result "
                "comes about 10 minutes after it starts")
    return f"Signal K answered HTTP {code}"


def write_atomic(path: str, data: dict) -> None:
    d = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".swell.", suffix=".tmp")
    with os.fdopen(fd, "w") as f:
        json.dump(data, f)
    os.replace(tmp, path)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--server", default=os.environ.get("SIGNALK_URL", "http://localhost:3000"))
    ap.add_argument("--out", default=os.path.expanduser("~/.swell.json"))
    ap.add_argument("--interval", type=float, default=60.0)
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--assume-anchored", action="store_true",
                    help="write even when the WaveHat does not know whether the boat is underway")
    args = ap.parse_args()
    token = os.environ.get("SIGNALK_TOKEN")
    while True:
        now = time.time()
        try:
            swell, why = swell_from_waves(fetch_waves(args.server, token), now, args.assume_anchored)
        except urllib.error.HTTPError as e:
            swell, why = None, http_reason(e.code)
        except (urllib.error.URLError, OSError, ValueError) as e:
            swell, why = None, f"Signal K not reachable: {e}"
        if swell:
            write_atomic(args.out, swell)
        if args.verbose or not swell:
            print(json.dumps(swell) if swell else f"not written: {why}", flush=True)
        if args.once:
            return 0 if swell else 1
        time.sleep(args.interval)


if __name__ == "__main__":
    sys.exit(main())
