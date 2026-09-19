#!/usr/bin/env python3
"""Capture per-equation input/output pairs from the ITU reference P.1812.

The claim under test is that P.1812 can be ported step by step, because the
Recommendation names every intermediate. This wraps the internal functions a
port implements and records exactly what each was called with and what it
returned, during real runs over the official validation profiles.

Output: scripts/p1812_fixtures.json - one record per (function, call), which
gen_fixtures.py turns into ReferenceFixtures.kt.
"""
import json
import os
import sys

import numpy as np

from p1812_ref import SCRIPTS, import_reference

P1812, PROFILES, _ = import_reference()

# The functions the port implements: earth radius, terrain smoothing, the two
# Bullington variants, spherical-earth diffraction, the delta-Bullington
# combination, and the small closed forms around them.
TARGETS = [
    "earth_rad_eff",
    "smooth_earth_heights",
    "dl_bull",
    "dl_se",
    "dl_se_ft",
    "dl_delta_bull",
    "dl_p",
    "pl_los",
    "beta0",
    "path_fraction",
    "inv_cum_norm",
]

captured = []


def jsonable(x):
    if isinstance(x, np.ndarray):
        return [jsonable(v) for v in x.tolist()]
    if isinstance(x, (np.floating, float)):
        f = float(x)
        return None if (f != f or f in (float("inf"), float("-inf"))) else f
    if isinstance(x, (np.integer, int)):
        return int(x)
    if isinstance(x, (list, tuple)):
        return [jsonable(v) for v in x]
    if isinstance(x, (str, bool)) or x is None:
        return x
    return repr(x)


def wrap(name):
    orig = getattr(P1812, name)

    def wrapped(*args, **kwargs):
        out = orig(*args, **kwargs)
        captured.append(dict(
            fn=name,
            args=[jsonable(a) for a in args],
            kwargs={k: jsonable(v) for k, v in kwargs.items()},
            out=jsonable(out) if isinstance(out, tuple) else [jsonable(out)],
        ))
        return out

    wrapped.__name__ = name
    return wrapped


for t in TARGETS:
    if hasattr(P1812, t):
        setattr(P1812, t, wrap(t))
    else:
        print(f"  (no such function: {t})", file=sys.stderr)


def main():
    files = sorted(f for f in os.listdir(PROFILES) if f.endswith(".csv"))
    print(f"{len(files)} validation profiles")
    runs = 0
    for fn in files:
        try:
            sg = P1812.read_sg3_measurements2(os.path.join(PROFILES, fn), "Fryderyk_csv")
        except Exception as e:  # noqa: BLE001
            print(f"  skip {fn}: {e}")
            continue
        sg.debug = 0
        sg.pathinfo = 1
        sg.ClutterCode = []
        # The stub P1812.npz is zeros; assert we never depend on it.
        assert sg.DN is not None and sg.N0 is not None, f"{fn}: profile lacks DN/N0"
        if not (sg.DN > 0 and sg.N0 > 0):
            print(f"  skip {fn}: DN={sg.DN} N0={sg.N0} would hit the stub maps")
            continue
        for measID in range(len(sg.hRx)):
            try:
                P1812.bt_loss(
                    sg.frequency[measID] / 1e3, sg.TimePercent[measID],
                    sg.x, sg.h_gamsl, sg.h_ground_cover, sg.radio_met_code,
                    sg.hTx[0], sg.hRx[measID], sg.polHVC[measID],
                    sg.TxLAT, sg.RxLAT, sg.TxLON, sg.RxLON,
                    pL=50.0, sigmaL=0.0, Ptx=1.0,
                    DN=sg.DN, N0=sg.N0,
                    dct=getattr(sg, "dct", 500.0), dcr=getattr(sg, "dcr", 500.0),
                    flag4=0, debug=0,
                )
                runs += 1
            except Exception as e:  # noqa: BLE001
                print(f"  {fn}[{measID}] failed: {type(e).__name__}: {e}")
    print(f"{runs} model runs, {len(captured)} captured calls")
    by_fn = {}
    for c in captured:
        by_fn[c["fn"]] = by_fn.get(c["fn"], 0) + 1
    for k in sorted(by_fn):
        print(f"  {k:24s} {by_fn[k]}")

    out = SCRIPTS / "p1812_fixtures.json"
    with open(out, "w") as f:
        json.dump(captured, f)
    print(f"wrote {out} ({os.path.getsize(out)/1e6:.1f} MB)")


if __name__ == "__main__":
    main()
