#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Rewrite the platform and minos of a thin 64-bit Mach-O's LC_BUILD_VERSION, in place.

    macho_platform.py <file> <platform> <minos>

<platform> is the LC_BUILD_VERSION number (6 Mac Catalyst, 11 visionOS, 12 visionOS
simulator) and <minos> is X.Y. The command keeps its size, so this works on object files,
which have no load-command padding for `vtool -set-build-version -replace` to grow into.
"""
import struct
import sys

LC_BUILD_VERSION = 0x32
MH_MAGIC_64 = 0xFEEDFACF
MACH_HEADER_64_SIZE = 32


def main():
    path, platform, minos = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    major, minor = (int(p) for p in minos.split("."))
    with open(path, "rb") as f:
        data = bytearray(f.read())
    magic, _, _, _, ncmds = struct.unpack_from("<5I", data, 0)
    if magic != MH_MAGIC_64:
        sys.exit(f"{path}: not a thin 64-bit Mach-O")
    offset, patched = MACH_HEADER_64_SIZE, 0
    for _ in range(ncmds):
        cmd, size = struct.unpack_from("<II", data, offset)
        if cmd == LC_BUILD_VERSION:
            struct.pack_into("<II", data, offset + 8, platform, (major << 16) | (minor << 8))
            patched += 1
        offset += size
    if patched != 1:
        sys.exit(f"{path}: expected one LC_BUILD_VERSION, found {patched}")
    with open(path, "wb") as f:
        f.write(data)


if __name__ == "__main__":
    main()
