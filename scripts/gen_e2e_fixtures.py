#!/usr/bin/env python3
"""Emit E2EFixtures.kt from scripts/p1812_e2e.json (see export_e2e.py).

Pure Python, no numpy. The E2ECase class lives in E2ECase.kt so this file has no
top-level class (detekt's MatchingDeclarationName). Cases are emitted in chunked
functions rather than one list literal: a single initializer this large overflows the JVM 64 KB method limit, and
at this size it also crashed HotSpot's C2 compiler when the Kover agent was attached.
"""
import json
import os

from p1812_ref import COMMON_TEST, SCRIPTS, provenance_lines

CHUNK = 8


def arr(v):
    return "*" + ",".join(repr(float(x)) for x in v)


HEADER = """/*
 * GENERATED - do not edit. Regenerate with scripts/gen_e2e_fixtures.py.
 *
 * END-TO-END cases: a full terrain profile and every model input, through to the basic
 * transmission loss (Eq 69) and field strength (Eq 70) produced by the ITU-R WP 3K
 * approved reference implementation over its 19 official validation profiles.
 *
 * Each expected Lb was cross-checked against the value committed in the reference repo's
 * own validation_results logs before being emitted here, so a fixture cannot silently
 * encode a value this project computed for itself.
 *
 * Emitted in chunked functions rather than one list literal: a single initializer this
 * large overflows the JVM 64 KB method limit, and at this size it also crashed HotSpot's
 * C2 compiler (Internal Error type.cpp:1283) when the Kover agent was attached.
 *
@@PROVENANCE@@
 */
package org.meshtastic.kp1812"""


def main():
    cases = json.load(open(SCRIPTS / "p1812_e2e.json"))
    body = [HEADER.replace("@@PROVENANCE@@", "\n".join(provenance_lines()))]
    chunks = [cases[i:i + CHUNK] for i in range(0, len(cases), CHUNK)]
    for ci, ch in enumerate(chunks):
        body.append(f"\nprivate fun e2eChunk{ci}(): List<E2ECase> = listOf(")
        for c in ch:
            body.append(f"""    E2ECase(
        "{c['name']}",
        "{arr(c['d'])}",
        "{arr(c['h'])}",
        "{arr(c['r'])}",
        "{arr(c['zone'])}",
        {float(c['f'])}, {float(c['p'])}, {float(c['htg'])}, {float(c['hrg'])}, {int(c['pol'])},
        {float(c['phi'])}, {float(c['dn'])}, {float(c['n0'])}, {float(c['dct'])}, {float(c['dcr'])},
        {float(c['pl'])}, {float(c['sigmal'])}, {float(c['lb'])}, {float(c['ep'])},
    ),""")
        body.append(")")
    joined = " +\n        ".join(f"e2eChunk{i}()" for i in range(len(chunks)))
    body.append(f"\ninternal val E2E_CASES: List<E2ECase> by lazy {{\n    {joined}\n}}")
    dest = COMMON_TEST / "E2EFixtures.kt"
    dest.write_text("\n".join(body) + "\n")
    print(f"{len(cases)} cases in {len(chunks)} chunks -> {dest.relative_to(SCRIPTS.parent)} "
          f"({os.path.getsize(dest)/1e6:.2f} MB)")


if __name__ == "__main__":
    main()
