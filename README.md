# kp1812

[![Maven Central](https://img.shields.io/maven-central/v/org.meshtastic/kp1812)](https://central.sonatype.com/artifact/org.meshtastic/kp1812)
[![CI](https://github.com/meshtastic/kp1812/actions/workflows/ci.yml/badge.svg)](https://github.com/meshtastic/kp1812/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/meshtastic/kp1812/graph/badge.svg)](https://codecov.io/gh/meshtastic/kp1812)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![Kotlin Multiplatform](https://img.shields.io/badge/Kotlin-Multiplatform-blue.svg?logo=kotlin)](https://kotlinlang.org)
[![Revved up by Develocity](https://img.shields.io/badge/Revved%20up%20by-Develocity-06A0CE?logo=Gradle&labelColor=02303A)](https://community.develocity.cloud/scans?search.rootProjectNames=kp1812)

**Recommendation ITU-R P.1812 in pure Kotlin Multiplatform.**

A path-specific propagation prediction method for point-to-area terrestrial
services in the frequency range 30 MHz to 6 GHz — the ITU's current model for
exactly the question a coverage planner asks: *given this terrain profile, how
much signal arrives over there?*

```kotlin
val prediction = P1812.predict(
    path = TerrainPath(distancesKm, heightsM, clutterHeightsM, zones),
    frequencyGhz = 0.915,
    txHeightM = 10.0,
    rxHeightM = 1.5,
    pathCentreLatitudeDeg = 47.6,
)

println(prediction.basicTransmissionLossDb)
println(P1812.receivedPower(prediction, txPowerDbm = 30.0, txGainDbi = 2.0).value)
```

## Why this, and why Kotlin

The alternative is SPLAT!'s ITM/ITWOM — a 2011 C++ translation of 1968 FORTRAN
that has not moved since, wrapped in per-platform native builds.

P.1812 is a maintained ITU Recommendation with something ITWOM has never had:
**an official reference implementation and published validation data for every
intermediate quantity.** That turns a port from a leap into a checklist. When
`dlBull` matches and `dlSe` does not, the block of the Recommendation to
re-read is unambiguous — rather than an aggregate pixel diff over a raster.

So this is not a reimplementation held together by hope. Every function is
checked against calls captured from the ITU reference running over its **19
official validation profiles**, and those fixtures are compiled into
`commonTest` so the conformance suite executes on **every target**, not just
the JVM. The reference is [`eeveetza/Py1812`](https://github.com/eeveetza/Py1812)
at commit `6c9061dd` (2026-08-28), which implements **P.1812-8**; the pipeline
that captures from it is under `scripts/`.

Pure `kotlin.math` throughout. No `expect`/`actual`, no cinterop, no vendored
native library, and **zero runtime dependencies** — the same source compiles
for JVM, Android, Apple, Linux, Windows, JS and WebAssembly.

## Install

```kotlin
// Maven Central — the version badge above is the current release
implementation("org.meshtastic:kp1812:<version>")
```

Android consumes the `jvm` artifact; there is no separate Android target.

Swift takes a static `Kp1812.xcframework` through SwiftPM. Each GitHub release
attaches `Kp1812.xcframework.zip` and a `Package.swift` whose `binaryTarget`
names it by URL and checksum; copy that `binaryTarget` into your own package.

```swift
.binaryTarget(
    name: "Kp1812",
    url: "https://github.com/meshtastic/kp1812/releases/download/v<version>/Kp1812.xcframework.zip",
    checksum: "<checksum from that release's Package.swift>"
)
```

It covers iOS 15, macOS 12 and tvOS 15, device and simulator. There is no Mac
Catalyst or watchOS slice: Kotlin/Native has no Catalyst target. From Swift the
API is `P1812.shared.predict(...)` with every argument spelled out, since
Objective-C export drops Kotlin defaults, and `TerrainPath` takes
`KotlinDoubleArray`/`KotlinIntArray`.

## Targets

`jvm` · `js` · `wasmJs` · `wasmWasi` · `iosArm64` · `iosSimulatorArm64` ·
`iosX64` · `macosArm64` · `tvosArm64` · `tvosSimulatorArm64` · `linuxX64` ·
`linuxArm64` · `mingwX64`

Android consumes the `jvm` artifact, which keeps AGP and the Android SDK out
of the build entirely.

## Scope

Implemented: free-space and line-of-sight loss, β₀, effective earth radius,
smooth-earth heights and horizon geometry, Bullington and delta-Bullington
diffraction, spherical-earth first-term diffraction, diffraction for p% time,
troposcatter, ducting / layer reflection, location variability, and the
combination of all of them into basic transmission loss and field strength.

Not implemented: the ITU digital maps for `DN50`/`N050`. Those are ITU
copyright and not redistributable, so [Atmosphere] takes Δ*N* and *N*₀
directly and defaults to the global medians.

## Licence

GPL-3.0-or-later. The P.1812 algorithm is an ITU Recommendation; this is an
independent implementation of it.
