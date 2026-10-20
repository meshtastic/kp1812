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
LC_BUILD_VERSION_SIZE = 24
LOAD_COMMAND_HEADER_SIZE = 8
MH_MAGIC_64 = 0xFEEDFACF
MACH_HEADER_64_SIZE = 32


def main():
    path, platform, minos = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    major, minor = (int(p) for p in minos.split("."))
    with open(path, "rb") as f:
        data = bytearray(f.read())
    if len(data) < MACH_HEADER_64_SIZE:
        sys.exit(f"{path}: too short for a Mach-O header")
    magic, _, _, _, ncmds, sizeofcmds = struct.unpack_from("<6I", data, 0)
    if magic != MH_MAGIC_64:
        sys.exit(f"{path}: not a thin 64-bit Mach-O")
    end = MACH_HEADER_64_SIZE + sizeofcmds
    if end > len(data):
        sys.exit(f"{path}: load commands run past the end of the file")
    offset, patched = MACH_HEADER_64_SIZE, 0
    for _ in range(ncmds):
        if offset + LOAD_COMMAND_HEADER_SIZE > end:
            sys.exit(f"{path}: load command at {offset} runs past sizeofcmds")
        cmd, size = struct.unpack_from("<II", data, offset)
        if size < LOAD_COMMAND_HEADER_SIZE or offset + size > end:
            sys.exit(f"{path}: malformed cmdsize {size} at {offset}")
        if cmd == LC_BUILD_VERSION:
            if size < LC_BUILD_VERSION_SIZE:
                sys.exit(f"{path}: LC_BUILD_VERSION at {offset} is {size} bytes")
            struct.pack_into("<II", data, offset + 8, platform, (major << 16) | (minor << 8))
            patched += 1
        offset += size
    if patched != 1:
        sys.exit(f"{path}: expected one LC_BUILD_VERSION, found {patched}")
    with open(path, "wb") as f:
        f.write(data)


if __name__ == "__main__":
    main()
