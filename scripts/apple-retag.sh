#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
#
# Kotlin/Native has no Mac Catalyst or visionOS target. kp1812 is pure kotlin.math, so its
# iOS binaries run unchanged on both once relabeled: this rewrites the platform in each
# Mach-O's LC_BUILD_VERSION (scripts/macho_platform.py) and touches nothing else.
#
#   scripts/apple-retag.sh xcframework <out.xcframework>
#       After `./gradlew assembleKp1812ReleaseXCFramework`. Writes an XCFramework holding
#       Gradle's five slices plus Mac Catalyst (arm64, x86_64), visionOS and the visionOS
#       simulator.
#
#   scripts/apple-retag.sh test
#       After `./gradlew linkDebugTestIosArm64 linkDebugTestIosX64
#       linkDebugTestIosSimulatorArm64`. Runs the conformance suite as Mac Catalyst arm64,
#       Mac Catalyst x86_64 under Rosetta, and on a visionOS simulator.
set -euo pipefail

root=$(cd "$(dirname "$0")/.." && pwd)
bin=$root/build/bin
patch=$root/scripts/macho_platform.py

# LC_BUILD_VERSION platforms, and floors matching the iOS 15 that Kotlin/Native builds for.
# Mac Catalyst counts in iOS versions: 15.0 is macOS 12.
CATALYST=6 CATALYST_MIN=15.0
XROS=11 XRSIM=12 XROS_MIN=1.0

# retag_archive <thin static archive> <platform> <minos> <out.a>
retag_archive() {
  local in=$1 platform=$2 minos=$3 dst=$4 work o
  work=$(mktemp -d)
  if [ -n "$(ar -t "$in" | sort | uniq -d)" ]; then
    echo "$in has duplicate member names; ar -x would drop objects" >&2
    exit 1
  fi
  (cd "$work" && ar -x "$in")
  for o in "$work"/*.o; do python3 "$patch" "$o" "$platform" "$minos"; done
  xcrun libtool -static -no_warning_for_no_symbols -o "$dst" "$work"/*.o
  rm -rf "$work"
}

# retag_framework <ios framework> <binary> <dst framework> <plist platform> <minos>
retag_framework() {
  local src=$1 binary=$2 dst=$3 plat=$4 minos=$5
  mkdir -p "$dst"
  cp -R "$src/Headers" "$src/Modules" "$src/Info.plist" "$dst/"
  cp "$binary" "$dst/Kp1812"
  plutil -replace CFBundleSupportedPlatforms -json "[\"$plat\"]" "$dst/Info.plist"
  plutil -replace MinimumOSVersion -string "$minos" "$dst/Info.plist"
}

xcframework() {
  local out=${1:?usage: scripts/apple-retag.sh xcframework <out.xcframework>}
  local gradle=$root/build/XCFrameworks/release/Kp1812.xcframework
  local ios=$bin/iosArm64/releaseFramework/Kp1812.framework
  local iosx64=$bin/iosX64/releaseFramework/Kp1812.framework
  local iossim=$bin/iosSimulatorArm64/releaseFramework/Kp1812.framework
  local f
  for f in "$gradle" "$ios" "$iosx64" "$iossim"; do
    [ -d "$f" ] || { echo "no $f - run ./gradlew assembleKp1812ReleaseXCFramework first" >&2; exit 1; }
  done

  local work
  work=$(mktemp -d)

  # Mac Catalyst takes the macOS bundle layout, one fat binary under Versions/A.
  local cat=$work/maccatalyst/Kp1812.framework
  mkdir -p "$cat/Versions/A/Resources"
  retag_archive "$ios/Kp1812" "$CATALYST" "$CATALYST_MIN" "$work/catalyst-arm64.a"
  retag_archive "$iosx64/Kp1812" "$CATALYST" "$CATALYST_MIN" "$work/catalyst-x86_64.a"
  xcrun lipo -create "$work/catalyst-arm64.a" "$work/catalyst-x86_64.a" -output "$cat/Versions/A/Kp1812"
  cp -R "$ios/Headers" "$ios/Modules" "$cat/Versions/A/"
  cp "$ios/Info.plist" "$cat/Versions/A/Resources/Info.plist"
  plutil -replace CFBundleSupportedPlatforms -json '["MacOSX"]' "$cat/Versions/A/Resources/Info.plist"
  plutil -remove MinimumOSVersion "$cat/Versions/A/Resources/Info.plist"
  plutil -replace LSMinimumSystemVersion -string 12.0 "$cat/Versions/A/Resources/Info.plist"
  ln -s A "$cat/Versions/Current"
  for f in Kp1812 Headers Modules Resources; do ln -s "Versions/Current/$f" "$cat/$f"; done

  retag_archive "$ios/Kp1812" "$XROS" "$XROS_MIN" "$work/xros.a"
  retag_framework "$ios" "$work/xros.a" "$work/xros/Kp1812.framework" XROS "$XROS_MIN"
  retag_archive "$iossim/Kp1812" "$XRSIM" "$XROS_MIN" "$work/xrsimulator.a"
  retag_framework "$iossim" "$work/xrsimulator.a" "$work/xrsimulator/Kp1812.framework" XRSimulator "$XROS_MIN"

  local args=()
  for f in "$gradle"/*/Kp1812.framework "$cat" "$work/xros/Kp1812.framework" "$work/xrsimulator/Kp1812.framework"; do
    args+=(-framework "$f")
  done
  rm -rf "$out"
  xcodebuild -create-xcframework "${args[@]}" -output "$out" >/dev/null
  rm -rf "$work"
  echo "$out: $(plutil -extract AvailableLibraries raw "$out/Info.plist") slices"
}

# run_retagged <test.kexe> <platform> <minos> <label> [launcher...]
run_retagged() {
  local kexe=$1 platform=$2 minos=$3 label=$4 work
  shift 4
  [ -f "$kexe" ] || { echo "no $kexe - link the iOS test binaries first" >&2; exit 1; }
  work=$(mktemp -d)
  cp "$kexe" "$work/test.kexe"
  python3 "$patch" "$work/test.kexe" "$platform" "$minos"
  codesign -f -s - "$work/test.kexe" 2>/dev/null
  echo "== $label"
  "$@" "$work/test.kexe"
  rm -rf "$work"
}

test_retagged() {
  run_retagged "$bin/iosArm64/debugTest/test.kexe" "$CATALYST" "$CATALYST_MIN" "Mac Catalyst arm64"
  run_retagged "$bin/iosX64/debugTest/test.kexe" "$CATALYST" "$CATALYST_MIN" "Mac Catalyst x86_64" arch -x86_64

  local udid booted
  udid=$(xcrun simctl list devices available -j | python3 -c '
import json, sys
devices = json.load(sys.stdin)["devices"]
print(next((d["udid"] for runtime, ds in sorted(devices.items()) if "xrOS" in runtime for d in ds), ""))')
  [ -n "$udid" ] || { echo "no visionOS simulator available - xcodebuild -downloadPlatform visionOS" >&2; exit 1; }
  booted=$(xcrun simctl list devices booted | grep -c "$udid" || true)
  [ "$booted" -gt 0 ] || xcrun simctl boot "$udid"
  xcrun simctl bootstatus "$udid" -b >/dev/null
  run_retagged "$bin/iosSimulatorArm64/debugTest/test.kexe" "$XRSIM" "$XROS_MIN" "visionOS simulator" \
    xcrun simctl spawn "$udid"
  [ "$booted" -gt 0 ] || xcrun simctl shutdown "$udid"
}

case ${1:-} in
  xcframework) xcframework "${2:-}" ;;
  test) test_retagged ;;
  *) echo "usage: scripts/apple-retag.sh xcframework <out.xcframework> | test" >&2; exit 2 ;;
esac
