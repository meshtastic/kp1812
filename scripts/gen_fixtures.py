#!/usr/bin/env python3
"""Emit ReferenceFixtures.kt from scripts/p1812_fixtures.json (see export_p1812.py).

Pure Python, no numpy: this half is deterministic from the JSON, so it can run
anywhere. The values are embedded as strings, parsed lazily by RefCall, because a
doubleArrayOf() literal of this size overflows the JVM's 64 KB limit on a class
initializer.
"""
import json
import os

from p1812_ref import COMMON_TEST, SCRIPTS, provenance_lines

# Per-function caps keep the file a few MB. These functions are called with long
# arrays; the first N calls already span every profile.
LIMITS = {"dl_bull": 12, "dl_delta_bull": 8, "dl_p": 6, "smooth_earth_heights": 6}


def field(v):
    if v is None:
        return "~"
    if isinstance(v, list):
        if v and isinstance(v[0], list):
            return "~"
        return "*" + ",".join(repr(float(x)) for x in v)
    return repr(float(v))


def main():
    calls = json.load(open(SCRIPTS / "p1812_fixtures.json"))
    seen, rows = {}, []
    for c in calls:
        if c.get("kwargs"):
            continue
        fn = c["fn"]
        seen[fn] = seen.get(fn, 0) + 1
        if LIMITS.get(fn) is not None and seen[fn] > LIMITS[fn]:
            continue
        rows.append(c)

    by_fn = {}
    for r in rows:
        by_fn.setdefault(r["fn"], []).append(r)

    out = ["/*",
           " * GENERATED - do not edit. Regenerate with scripts/gen_fixtures.py.",
           " *",
           " * Calls captured from the ITU-R reference implementation of P.1812",
           " * (github.com/eeveetza/Py1812) running over its 19 official validation profiles.",
           " *",
           " * Embedded as Kotlin so the conformance suite runs on every target - Kotlin/Native",
           " * and wasm have no filesystem in commonTest. Stored as strings rather than",
           " * doubleArrayOf() literals because a literal of this size overflows the JVM 64 KB",
           " * limit on a class initializer method.",
           " *",
           *provenance_lines(),
           " */",
           "package org.meshtastic.kp1812",
           ""]
    for fn, rs in sorted(by_fn.items()):
        out.append(f"internal val REF_{fn.upper()}: List<RefCall> = listOf(")
        for r in rs:
            a = ";".join(field(x) for x in r["args"])
            o = ";".join(field(x) for x in r["out"])
            out.append(f'    RefCall(\n        "{a}",\n        "{o}",\n    ),')
        out.append(")")
        out.append("")
    src = "\n".join(out).rstrip("\n") + "\n"
    dest = COMMON_TEST / "ReferenceFixtures.kt"
    dest.write_text(src)
    biggest = max(
        max(len(";".join(field(x) for x in r["args"])), len(";".join(field(x) for x in r["out"])))
        for r in rows
    )
    print(f"{len(rows)} calls -> {dest.relative_to(SCRIPTS.parent)} "
          f"({os.path.getsize(dest)/1e6:.2f} MB, largest single string {biggest} bytes, limit 65535)")


if __name__ == "__main__":
    main()
