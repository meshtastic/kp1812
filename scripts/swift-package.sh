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
xcf=$root/build/XCFrameworks/release/Kp1812.xcframework
out=$root/build/swift-package

[ -d "$xcf" ] || { echo "no $xcf - run ./gradlew assembleKp1812ReleaseXCFramework first" >&2; exit 1; }

rm -rf "$out"
mkdir -p "$out"
ditto -c -k --keepParent "$xcf" "$out/Kp1812.xcframework.zip"
# From $out: SwiftPM leaves a .build/ in whatever directory it runs in.
checksum=$(cd "$out" && swift package compute-checksum Kp1812.xcframework.zip)

# Floors are Kotlin/Native's own minimum deployment targets; the framework will not load below them.
cat > "$out/Package.swift" <<EOF
// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "Kp1812",
    platforms: [.iOS(.v15), .macOS(.v12), .tvOS(.v15)],
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
