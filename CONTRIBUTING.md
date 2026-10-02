# Contributing to kp1812

## The rule that matters

Every change to the model keeps `ReferenceConformanceTest` and `EndToEndTest`
green on **every target**. Those suites compare the model against the
International Telecommunication Union (ITU) reference implementation over its
19 validation profiles. They're what separates this library from a
plausible-looking wrong answer.

Cross-compiling a target isn't testing it. A passing `./gradlew jvmTest` says
nothing about Kotlin/Native or Wasm.

## Environment

Any JDK launches the build. The Gradle daemon is pinned to Java 21
(`gradle/gradle-daemon-jvm.properties`), and the foojay resolver downloads one
if the machine has none. Kotlin/Native targets need their host: Apple tests run
on macOS, `mingwX64Test` on Windows, and `linuxX64Test` on Linux.

## Before opening a PR

```shell
./gradlew spotlessApply                      # format, and stamp the license header
./gradlew spotlessCheck detekt apiCheck
./gradlew jvmTest jsNodeTest wasmJsNodeTest wasmWasiNodeTest linuxX64Test   # Linux host
./gradlew macosArm64Test iosSimulatorArm64Test tvosSimulatorArm64Test        # macOS host
```

Regenerate `apiDump` on a macOS host. Apple targets build nowhere else, and a
dump taken elsewhere silently drops them. Commit both `api/kp1812.api` and
`api/kp1812.klib.api`.

## Commits and PRs

- Sign off every commit (DCO): `git commit -s`.
- Conventional Commits, imperative mood, with a body that says what and why.
  Spotless (ktlint) and detekt gate CI, and `.editorconfig` is the single source
  of style.
- A change a consumer can notice gets a `CHANGELOG.md` entry under
  `## [Unreleased]`: a new or changed public API, a behavior change, or a fix to
  something they could have hit. Anything that moves an `api/*.api` dump always
  needs one, under `### Breaking` if the consumer has to change code rather than
  recompile. Refactors and test-only changes need none.
- Releases are cut from `main` following `RELEASING.md`, so don't bump versions
  in a feature PR.

## Equation numbers are part of the code

Each function carries the equation and section numbers it implements. Keep them
accurate, because they're how the next person localizes a defect. The model is
P.1812-8, the revision the pinned reference implements. The numbers follow the
reference's own annotations, which cite the P.1812-6 text. P.1812-8 didn't
renumber any equation this code cites.

## Regenerating the fixtures

`ReferenceFixtures.kt` and `E2EFixtures.kt` are generated. The pipeline lives in
`scripts/` and is pinned to one commit of the ITU reference, and
`scripts/README.md` has the four commands. Regenerating against a newer
reference is a deliberate bump of `PY1812_COMMIT` in `scripts/p1812_ref.py`, in
its own commit, with the regenerated files beside it.
