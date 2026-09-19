# AGENTS.md

Canonical guidance for AI coding agents and maintainers working in this repo.
(`CLAUDE.md` and `GEMINI.md` are pointers to this file.)

## First read

1. `README.md` — what kp1812 is, its API, and what it does not implement.
2. `CONTRIBUTING.md` — environment, the gate, DCO sign-off, PR flow.
3. `scripts/README.md` — how the conformance fixtures are made, and from what.
4. The design invariants below — do not violate them.

## What this is

kp1812 is Recommendation ITU-R P.1812 in pure Kotlin Multiplatform: the ITU's
current path-specific propagation model for point-to-area terrestrial services,
30 MHz to 6 GHz. It exists so a coverage planner can run the same arithmetic
on Android, the JVM, Apple, Linux, Windows, JS and Wasm with **zero runtime
dependencies**, validated against the ITU reference rather than against
goldens this project generated for itself.

## Layout

- `src/commonMain/kotlin/org/meshtastic/kp1812/` — the whole library. `P1812.kt`
  is the public API (`P1812.predict()`, `P1812.receivedPower()`, `TerrainPath`,
  `Atmosphere`, `Prediction`, `Polarization`, `Dbm`); `Diffraction.kt` and
  `Mechanisms.kt` are the internal model, one function per block of the
  Recommendation.
- `src/commonTest/` — the conformance suite. `ReferenceFixtures.kt` and
  `E2EFixtures.kt` are **generated** (see `scripts/`); `RefCall.kt` and
  `E2ECase.kt` parse them; the two `*Test.kt` files compare.
- `scripts/` — the fixture pipeline, pinned to one commit of the ITU reference
  implementation. The reference checkout and the raw captures are gitignored.
- `docs/template-evaluation.md` — why this repo was scaffolded from `kzstd`.

Single-module on purpose: one small model, no `build-logic`, no BOM.

## Design invariants (do not violate)

- **Pure `kotlin.math`, one `commonMain`.** No `expect`/`actual`, no cinterop,
  no vendored native code, no runtime dependency. Every target compiles the same
  source, which is the whole reason a KMP port is defensible here.
- **Equation numbers are code.** Every function names the block of the
  Recommendation it implements. They are how a conformance failure is localised
  to an equation instead of a pixel. Keep them accurate.
- **The fixtures are generated and pinned.** Never hand-edit
  `ReferenceFixtures.kt` or `E2EFixtures.kt`. Regenerate with `scripts/`, and
  only against the commit named by `PY1812_COMMIT` in `scripts/p1812_ref.py`.
  Following a reference change is a deliberate bump of that constant, in its own
  commit, with the regenerated files beside it. The capture is platform-sensitive
  in its last digits (see `scripts/README.md`); that is not a model change.
- **The conformance suite runs on every target.** Fixtures are embedded as
  Kotlin strings because Kotlin/Native and Wasm have no filesystem in
  `commonTest`. Cross-compiling a target is not testing it; CI executes the
  suite on Linux, macOS and Windows hosts.
- **The ITU digital maps are never read.** `DN50`/`N050` are ITU copyright and
  not redistributable. `Atmosphere` takes ΔN and N₀ directly with global medians
  as defaults, and the exporters assert every validation profile supplies its
  own.
- **`explicitApi()` + binary-compatibility-validator with the klib dump.** Run
  `./gradlew apiDump` on macOS after any public-API change and commit both
  `api/kp1812.api` and `api/kp1812.klib.api`; a dump taken elsewhere silently
  omits the Apple targets.
- **Bytecode 21, API 21.** `jvmToolchain(21)`, `-Xjdk-release=21` and
  `options.release` move together.

## Commands

```bash
./gradlew spotlessApply                                  # format; stamps the license header
./gradlew spotlessCheck detekt apiCheck                  # the quality gate
./gradlew jvmTest jsNodeTest wasmJsNodeTest wasmWasiNodeTest linuxX64Test   # Linux host
./gradlew macosArm64Test iosSimulatorArm64Test tvosSimulatorArm64Test        # macOS host
./gradlew mingwX64Test                                                       # Windows host
./gradlew getChangelog --unreleased --no-header --no-links                   # what a release would say
```

The daemon is pinned to Java 21 (`gradle/gradle-daemon-jvm.properties`) and
foojay downloads one if the machine has none; the launcher JDK does not matter.

## Publishing

Maven Central via the vanniktech plugin (`org.meshtastic:kp1812`), from
`.github/workflows/release.yml` on a `v*` tag or a manual dispatch. See
`RELEASING.md`. Nothing has been published yet.

## Conventions

- Commits are **signed off** (DCO): `git commit -s`. The repo owner prefers to be
  the commit author — do **not** add `Co-Authored-By` trailers.
- Conventional Commits, imperative mood, a body that says what and why.
- Every source file carries the license header from
  `config/spotless/license-header.txt`; `spotlessApply` stamps it.
- A change a consumer can notice gets a `CHANGELOG.md` entry under
  `## [Unreleased]`; anything that moves an `api/*.api` dump always does, under
  `### Breaking` if the consumer has to change code rather than recompile.
- Do not auto-commit; stage changes and describe what you did.
