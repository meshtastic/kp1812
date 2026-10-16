#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
#
# Packages the release XCFramework for SwiftPM: zips it and writes the Package.swift whose
# binaryTarget names that zip by URL and checksum. Run after
# `./gradlew assembleKp1812ReleaseXCFramework`.
#
#   scripts/swift-package.sh <url the zip will be served from>
#
# Writes build/swift-package/Kp1812.xcframework.zip and build/swift-package/Package.swift.
# The checksum covers the zip's exact bytes, so the two files only ever ship together.
set -euo pipefail

url=${1:?usage: scripts/swift-package.sh <url the zip will be served from>}
root=$(cd "$(dirname "$0")/.." && pwd)
out=$root/build/swift-package

rm -rf "$out"
mkdir -p "$out"
# Gradle's slices plus the Mac Catalyst and visionOS ones relabeled from iOS.
"$root/scripts/apple-retag.sh" xcframework "$out/Kp1812.xcframework"
ditto -c -k --keepParent "$out/Kp1812.xcframework" "$out/Kp1812.xcframework.zip"
# From $out: SwiftPM leaves a .build/ in whatever directory it runs in.
checksum=$(cd "$out" && swift package compute-checksum Kp1812.xcframework.zip)

# Floors are Kotlin/Native's own minimum deployment targets; the framework will not load below them.
# Mac Catalyst 15 is macOS 12, and visionOS 1 is above the iOS 15 its slices are built for.
cat > "$out/Package.swift" <<EOF
// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "Kp1812",
    platforms: [.iOS(.v15), .macOS(.v12), .tvOS(.v15), .macCatalyst(.v15), .visionOS(.v1)],
    products: [
        .library(name: "Kp1812", targets: ["Kp1812"]),
    ],
    targets: [
        .binaryTarget(
            name: "Kp1812",
            url: "$url",
            checksum: "$checksum"
        ),
    ]
)
EOF

echo "$out/Kp1812.xcframework.zip"
echo "$out/Package.swift (checksum $checksum)"
