#!/usr/bin/env python3
"""Build an END-TO-END fixture: profile + inputs -> the reference's final Lb.

The per-equation fixtures validate each block in isolation. This validates the
whole model: every input the Recommendation takes, through to basic transmission
loss (Eq 69) and field strength (Eq 70).

Source of truth is `tests/validation_results/*_log.csv` - the committed outputs of
the ITU-R WP 3K approved reference implementation over its 19 official validation
profiles. Each log carries its own inputs, so a log plus its terrain profile is a
complete, self-contained record.

As a guard, the reference is re-run here with the inputs parsed out of each log and
the recomputed Lb is asserted equal to the committed one. A fixture is only emitted
if that holds, so a parsing mistake cannot silently produce a wrong target.

Output: scripts/p1812_e2e.json, which gen_e2e_fixtures.py turns into E2EFixtures.kt.
"""
import csv
import json
import os
import re

import numpy as np

from p1812_ref import SCRIPTS, import_reference

P1812, PROFILES, RESULTS = import_reference()


def read_log(path):
    """Parse a reference log into {label: value}. Labels repeat; keep the first."""
    vals = {}
    with open(path) as f:
        for row in csv.reader(f):
            if len(row) < 4:
                continue
            key = row[0].strip()
            raw = row[3].strip()
            if not key or key.startswith("#") or not raw:
                continue
            try:
                v = float(raw)
            except ValueError:
                continue
            vals.setdefault(key, v)
            vals[key + "__last"] = v
    return vals


def main():
    logs = sorted(f for f in os.listdir(RESULTS) if f.endswith("_log.csv"))
    print(f"{len(logs)} reference logs")
    out = []
    skipped = []
    for lf in logs:
        m = re.match(r"^(.*)_(\d+)_log\.csv$", lf)
        if not m:
            continue
        stem, idx = m.group(1), int(m.group(2))
        log = read_log(os.path.join(RESULTS, lf))
        prof_path = os.path.join(PROFILES, stem + ".csv")
        if not os.path.exists(prof_path):
            skipped.append((lf, "no profile"))
            continue
        try:
            sg = P1812.read_sg3_measurements2(prof_path, "Fryderyk_csv")
        except Exception as e:  # noqa: BLE001
            skipped.append((lf, f"profile read: {e}"))
            continue
        sg.debug = 0
        sg.pathinfo = 1
        sg.ClutterCode = []

        need = ["f (GHz)", "p (%)", "htg (m)", "hrg (m)", "pol", "DN", "N0",
                "dct (km)", "dcr (km)", "phi_t (deg)", "phi_r (deg)",
                "lam_t (deg)", "lam_r (deg)", "pL (%)", "sigmaL (dB)", "Lb (dB)"]
        got = {}
        for k in need:
            v = log.get(k) if k in log else log.get(k + " ")
            if v is None:
                got = None
                break
            got[k] = v
        if got is None:
            skipped.append((lf, "missing input rows"))
            continue

        try:
            lb, ep = P1812.bt_loss(
                got["f (GHz)"], got["p (%)"], sg.x, sg.h_gamsl, sg.h_ground_cover,
                sg.radio_met_code, got["htg (m)"], got["hrg (m)"], int(got["pol"]),
                got["phi_t (deg)"], got["phi_r (deg)"], got["lam_t (deg)"], got["lam_r (deg)"],
                pL=got["pL (%)"], sigmaL=got["sigmaL (dB)"], Ptx=1.0,
                DN=got["DN"], N0=got["N0"], dct=got["dct (km)"], dcr=got["dcr (km)"],
                flag4=0, debug=0,
            )
        except Exception as e:  # noqa: BLE001
            skipped.append((lf, f"bt_loss: {type(e).__name__}: {e}"))
            continue

        # Guard: our re-run must reproduce the committed Lb, or the parse is wrong.
        committed = got["Lb (dB)"]
        if abs(float(lb) - committed) > 1e-6 * max(1.0, abs(committed)):
            skipped.append((lf, f"Lb mismatch: rerun {float(lb):.6f} vs committed {committed:.6f}"))
            continue

        # phi_path is derived inside bt_loss; the log records it as "phi (deg)".
        phi = log.get("phi (deg)")
        if phi is None:
            skipped.append((lf, "no phi"))
            continue

        out.append(dict(
            name=f"{stem}_{idx}",
            d=[float(x) for x in np.asarray(sg.x).tolist()],
            h=[float(x) for x in np.asarray(sg.h_gamsl).tolist()],
            r=[float(x) for x in np.asarray(sg.h_ground_cover).tolist()],
            zone=[int(x) for x in np.asarray(sg.radio_met_code).tolist()],
            f=got["f (GHz)"], p=got["p (%)"],
            htg=got["htg (m)"], hrg=got["hrg (m)"], pol=int(got["pol"]),
            phi=phi, dn=got["DN"], n0=got["N0"],
            dct=got["dct (km)"], dcr=got["dcr (km)"],
            pl=got["pL (%)"], sigmal=got["sigmaL (dB)"],
            lb=float(lb), ep=float(ep),
        ))

    print(f"{len(out)} end-to-end cases verified against their committed Lb")
    if skipped:
        from collections import Counter

        print(f"{len(skipped)} skipped:")
        for reason, c in Counter(s[1].split(":")[0] for s in skipped).most_common():
            print(f"  {reason}: {c}")
    dest = SCRIPTS / "p1812_e2e.json"
    json.dump(out, open(dest, "w"))
    print(f"wrote {dest} ({os.path.getsize(dest)/1e6:.1f} MB)")


if __name__ == "__main__":
    main()
