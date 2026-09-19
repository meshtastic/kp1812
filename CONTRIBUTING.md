# Contributing to kp1812

## The rule that matters

Every change to the model must keep `ReferenceConformanceTest` green on
**every target**. That suite compares each function against the ITU reference
implementation over its 19 official validation profiles, and it is the only
thing standing between this library and a plausible-looking wrong answer.

Cross-compiling a target is not testing it. `./gradlew jvmTest` passing tells
you nothing about Kotlin/Native or wasm.

## Environment

Any JDK launches the build; the Gradle daemon itself is pinned to Java 21
(`gradle/gradle-daemon-jvm.properties`) and downloaded by the foojay resolver if
the machine has none. Kotlin/Native targets need their host: Apple tests run on
macOS, `mingwX64Test` on Windows, `linuxX64Test` on Linux.

## Before opening a PR

```bash
./gradlew spotlessApply                      # format, and stamp the license header
./gradlew spotlessCheck detekt apiCheck
./gradlew jvmTest jsNodeTest wasmJsNodeTest wasmWasiNodeTest linuxX64Test   # Linux host
./gradlew macosArm64Test iosSimulatorArm64Test tvosSimulatorArm64Test        # macOS host
```

`apiDump` must be regenerated on a macOS host — Apple targets build nowhere
else, and a dump taken elsewhere silently drops them. Commit both
`api/kp1812.api` and `api/kp1812.klib.api`.

## Commits and PRs

- Sign off every commit (DCO): `git commit -s`.
- Conventional Commits, imperative mood, with a body that says what and why.
- A change a consumer can notice gets a `CHANGELOG.md` entry under
  `## [Unreleased]`: a new or changed public API, a behaviour change, a fix to
  something they could have hit. Anything that moves an `api/*.api` dump always
  needs one, under `### Breaking` if the consumer has to change code rather than
  just recompile. Refactors and test-only changes need none.
- Releases are cut from `main` by `RELEASING.md`; you do not bump versions in a
  feature PR.

## Equation numbers are part of the code

Each function carries the equation and section numbers it implements. Keep
them accurate: they are how the next person localises a defect, and they are
the reason this model was chosen over ITM. The model is P.1812-8, which is what
the reference commit the fixtures are captured from implements; the numbers
follow the reference's own annotations, which still cite the P.1812-6 text, and
they have not been renumbered between those revisions where this code cites
them.

## Regenerating the fixtures

`ReferenceFixtures.kt` and `E2EFixtures.kt` are generated. The pipeline lives in
`scripts/` and is pinned to one commit of the ITU reference; `scripts/README.md`
has the four commands. Regenerating against a newer reference is a deliberate
bump of `PY1812_COMMIT` in `scripts/p1812_ref.py`, in its own commit, with the
regenerated files beside it.

## Style

Conventional Commits. Spotless (ktlint) and detekt gate CI; `.editorconfig` is
the single style source of truth.
