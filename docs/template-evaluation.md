# Why this repo is not from the JetBrains KMP library template

Evaluated 2026-09-16 before scaffolding.

## `Kotlin/multiplatform-library-template` — current, but thin by design

Not stale: last pushed 2026-08-07, not archived. But its own README says it
sets up none of *"tracking of backwards compatibility, explicit API mode,
licensing, contribution guideline, code of conduct and others."*

What it gives you:

| | JetBrains template | `meshtastic/kzstd` |
| --- | --- | --- |
| Targets | 5 (jvm, androidLibrary, iosArm64, iosSimulatorArm64, linuxX64) | **13** (jvm, js, wasmJs, wasmWasi, 9 native) |
| Coordinate | `io.github.kotlin` | **`org.meshtastic`** — the org root |
| `explicitApi()` | no | yes |
| `allWarningsAsErrors`, `progressiveMode` | no | yes |
| Binary-compatibility validator | no | yes, **with klib ABI** enabled |
| Dokka | no | yes (AGENTS.md: Central accepts a 261-byte empty javadoc stub silently) |
| Kover / Codecov | no | yes |
| Spotless + detekt | no | yes |
| `SECURITY.md`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `CODEOWNERS`, `RELEASING.md` | no | yes |
| Renovate | no | yes |

Every row the template omits is something `AGENTS.md` → Org conventions
*requires* of a KMP library in this org. `meshtastic/.github` supplies no
community-health defaults, so a repo without its own `SECURITY.md` has none.

## `kzstd` is also the right architectural match

This library is pure computation over `kotlin.math` with no platform-specific
code — the same shape as kzstd's pure-Kotlin codec: one `commonMain`
implementation, no `expect`/`actual`, no cinterop, no vendored native library.
kzstd's build script already encodes the consequences of that shape, including
why `js {}` needs no JS dependency and why the klib ABI dump matters when
there is no JVM-only surface to hide behind.

kzstd also deliberately has **no Android target** — Android consumes the `jvm()`
artifact. That avoids an AGP dependency and an Android SDK requirement in CI,
and applies here for the same reason.

## Conclusion

Start from `kzstd`, not the template. The template would mean re-deriving
every org invariant by hand and getting some of them wrong.
