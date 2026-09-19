# Fixture pipeline

The conformance suite in `commonTest` runs against two generated files,
`ReferenceFixtures.kt` and `E2EFixtures.kt`. They are captured from the ITU-R
WP 3K approved reference implementation,
[`eeveetza/Py1812`](https://github.com/eeveetza/Py1812), at the one commit named
in `p1812_ref.py`. Everything here is reproducible from that commit; nothing in
the fixtures was computed by this project.

```bash
git clone https://github.com/eeveetza/Py1812 scripts/Py1812
git -C scripts/Py1812 checkout "$(python3 -c 'import sys; sys.path.insert(0, "scripts"); import p1812_ref; print(p1812_ref.PY1812_COMMIT)')"

cd scripts
python3 export_p1812.py       # per-function calls  -> p1812_fixtures.json  (needs numpy)
python3 export_e2e.py         # whole-model cases   -> p1812_e2e.json       (needs numpy)
python3 gen_fixtures.py       # -> ../src/commonTest/.../ReferenceFixtures.kt
python3 gen_e2e_fixtures.py   # -> ../src/commonTest/.../E2EFixtures.kt
```

The checkout and the JSON are gitignored. `PY1812=/elsewhere` points the
scripts at another checkout; they refuse any checkout that is not at the pinned
commit, so following a reference change is a visible edit to `PY1812_COMMIT`,
never a drift.

| script | reads | writes | what it asserts |
| --- | --- | --- | --- |
| `export_p1812.py` | the 19 validation profiles | `p1812_fixtures.json` | every profile supplies its own ΔN and N₀, so the ITU digital maps are never read |
| `export_e2e.py` | the profiles and the reference's committed `validation_results/*_log.csv` | `p1812_e2e.json` | the re-run Lb equals the committed Lb before a case is emitted |
| `gen_fixtures.py` | `p1812_fixtures.json` | `ReferenceFixtures.kt` | the largest embedded string stays under the JVM's 65535-byte constant limit |
| `gen_e2e_fixtures.py` | `p1812_e2e.json` | `E2EFixtures.kt` | cases are chunked, because one initialiser this large overflows the JVM 64 KB method limit |

The two `gen_*` scripts are pure Python and deterministic from the JSON, so the
Kotlin output is the thing to diff when the reference moves. Both emit the
formatted form `spotlessApply` would produce, so a regeneration is a clean tree.

## The capture is platform-sensitive in the last digits

The reference is numpy over doubles, and summation order differs by platform and
numpy build. Measured between the committed capture (macOS arm64, numpy 2.5.3)
and a Linux x86_64 recapture at the same commit: 243 of 1,228 per-function
records differ, worst 3.2e-15 relative; all 63 end-to-end cases differ in `lb`
and `ep` by at most 2.9e-14 dB, and in no input. The conformance tests allow
1e-12 relative and 1e-6 dB, so a capture from either platform passes against the
same port. Consequence: regenerate only when `PY1812_COMMIT` moves, and expect a
few hundred last-digit line changes in the Kotlin when the capturing machine
changes. Those are not a model change.

## The ITU digital maps

`P1812.py` loads `P1812.npz` at import. The real file is built from the ITU
`DN50`/`N050` maps, which are ITU copyright and not redistributable. Every
validation profile carries its own ΔN and N₀ and the exporters assert that, so
the maps are never consulted; `p1812_ref.ensure_stub_maps()` writes a zero-filled
stub of the right shape purely to satisfy the import. It is not ITU data, and
the library itself takes ΔN and N₀ directly for the same reason (see
`Atmosphere`).
