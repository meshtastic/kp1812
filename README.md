# kp1812

[![Maven Central](https://img.shields.io/maven-central/v/org.meshtastic/kp1812)](https://central.sonatype.com/artifact/org.meshtastic/kp1812)
[![CI](https://github.com/meshtastic/kp1812/actions/workflows/ci.yml/badge.svg)](https://github.com/meshtastic/kp1812/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/meshtastic/kp1812/graph/badge.svg)](https://codecov.io/gh/meshtastic/kp1812)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![Kotlin Multiplatform](https://img.shields.io/badge/Kotlin-Multiplatform-blue.svg?logo=kotlin)](https://kotlinlang.org)
[![Revved up by Develocity](https://img.shields.io/badge/Revved%20up%20by-Develocity-06A0CE?logo=Gradle&labelColor=02303A)](https://community.develocity.cloud/scans?search.rootProjectNames=kp1812)

Recommendation ITU-R P.1812 in pure Kotlin Multiplatform: path-specific
propagation prediction for point-to-area terrestrial services from 30 MHz to
6 GHz. Given a terrain profile, it predicts how much signal arrives at the far
end.

```kotlin
val prediction = P1812.predict(
    path = TerrainPath(distancesKm, heightsM, clutterHeightsM, zones),
    frequencyGhz = 0.915,
    txHeightM = 10.0,
    rxHeightM = 1.5,
    pathCenterLatitudeDeg = 47.6,
)

println(prediction.basicTransmissionLossDb)
println(P1812.receivedPower(prediction, txPowerDbm = 30.0, txGainDbi = 2.0).value)
```

## Conformance

The International Telecommunication Union (ITU) publishes a reference
implementation of P.1812 with validation data for every intermediate quantity,
so each function here is checked against it directly. The fixtures are calls
captured from [`eeveetza/Py1812`](https://github.com/eeveetza/Py1812) at
`6c9061dd` (P.1812-8) over its 19 validation profiles. Another 63 cases run the
whole model from 30 MHz to 6 GHz, and the worst deviation in basic transmission
loss is 3.3e-9 dB. The fixtures are compiled into `commonTest`, so the suite
runs on every target, and `scripts/` regenerates them from the pinned
reference.

The model uses only `kotlin.math`: no `expect`/`actual`, no cinterop, and no
runtime dependencies.

## Install

```kotlin
implementation("org.meshtastic:kp1812:<version>")
```

Android consumes the `jvm` artifact. There's no Android target, which keeps the
Android Gradle Plugin and the Android SDK out of the build.

Swift takes a static `Kp1812.xcframework` through Swift Package Manager
(SwiftPM). Each GitHub release attaches `Kp1812.xcframework.zip` and a
`Package.swift` whose `binaryTarget` names it by URL and checksum. Copy that
`binaryTarget` into your own package.

```swift
.binaryTarget(
    name: "Kp1812",
    url: "https://github.com/meshtastic/kp1812/releases/download/v<version>/Kp1812.xcframework.zip",
    checksum: "<checksum from that release's Package.swift>"
)
```

It covers iOS 15, macOS 12, and tvOS 15, device and simulator. There's no Mac
Catalyst or watchOS slice: Kotlin/Native has no Catalyst target. From Swift, the
API is `P1812.shared.predict(...)` with every argument spelled out, since
Objective-C export drops Kotlin defaults. `TerrainPath` takes `KotlinDoubleArray`
and `KotlinIntArray`.

## Targets

`jvm` · `js` · `wasmJs` · `wasmWasi` · `iosArm64` · `iosSimulatorArm64` ·
`iosX64` · `macosArm64` · `tvosArm64` · `tvosSimulatorArm64` · `linuxX64` ·
`linuxArm64` · `mingwX64`

## Scope

Implemented: free-space and line-of-sight loss, β₀, effective earth radius,
smooth-earth heights and horizon geometry, Bullington and delta-Bullington
diffraction, spherical-earth first-term diffraction, diffraction for p% time,
troposcatter, ducting and layer reflection, location variability, and their
combination into basic transmission loss and field strength.

Not implemented: the ITU digital maps for `DN50`/`N050`. They're ITU copyright
and not redistributable, so `Atmosphere` takes Δ*N* and *N*₀ directly and
defaults to the global medians.

## License

GPL-3.0-or-later. The P.1812 algorithm is an ITU Recommendation, and kp1812 is
an independent implementation of it.
