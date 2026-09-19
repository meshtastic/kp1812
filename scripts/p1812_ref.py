"""Where the ITU reference lives, and which revision of it the fixtures were captured from.

Every script in this directory imports this. Bumping PY1812_COMMIT is how the fixtures are
allowed to follow a reference change: the export scripts refuse to run against any other
checkout, so a regenerated fixture always says exactly what it was captured from.
"""
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "scripts"
COMMON_TEST = REPO / "src" / "commonTest" / "kotlin" / "org" / "meshtastic" / "kp1812"

# github.com/eeveetza/Py1812 - the ITU-R WP 3K approved reference implementation.
PY1812_REPO = "https://github.com/eeveetza/Py1812"
PY1812_COMMIT = "6c9061dd022e93c84169059a016643926ce89964"  # 2026-08-28, "Fix for Issue #11"
PY1812_REVISION = "P.1812-8"  # what that commit implements (its bt_loss docstring says so)
# The committed fixtures were captured here. The reference is numpy over doubles, so a capture
# on another platform or numpy moves last digits: measured 3.2e-15 relative per function and
# 2.9e-14 dB end-to-end between macOS arm64 and Linux x86_64 - three orders inside the test
# tolerances (1e-12 relative, 1e-6 dB), and a reason to regenerate only when the pin moves.
PY1812_CAPTURE = "macOS arm64, numpy 2.5.3"


def py1812_dir() -> Path:
    """The reference checkout: $PY1812 if set, else scripts/Py1812 (gitignored)."""
    return Path(os.environ.get("PY1812", SCRIPTS / "Py1812")).resolve()


def check_pin(root: Path) -> None:
    head = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()
    if head != PY1812_COMMIT:
        sys.exit(
            f"{root} is at {head[:12]}, but the fixtures are pinned to {PY1812_COMMIT[:12]}.\n"
            f"Either check that commit out, or bump PY1812_COMMIT in scripts/p1812_ref.py "
            f"deliberately and regenerate everything."
        )


def ensure_stub_maps(root: Path) -> None:
    """P1812.py loads P1812.npz at import time. The real file is built from the ITU digital
    maps (DN50/N050), which are ITU copyright and not redistributable. Every validation
    profile carries its own DN and N0, and the exporters assert that, so the maps are never
    read - this stub only satisfies the module-level np.load. It is NOT ITU data."""
    import numpy as np

    npz = root / "src" / "Py1812" / "P1812.npz"
    if npz.exists():
        return
    np.savez(npz, DN50=np.zeros((121, 241)), N050=np.zeros((121, 241)))
    print(f"wrote zero stub {npz} (not ITU data; never read for these profiles)")


def import_reference():
    root = py1812_dir()
    if not root.is_dir():
        sys.exit(
            f"no reference checkout at {root}.\n"
            f"  git clone {PY1812_REPO} {SCRIPTS / 'Py1812'} && "
            f"git -C {SCRIPTS / 'Py1812'} checkout {PY1812_COMMIT}"
        )
    check_pin(root)
    ensure_stub_maps(root)
    sys.path.insert(0, str(root / "src"))
    sys.path.insert(0, str(root / "tests"))
    from Py1812 import P1812  # noqa: E402

    return P1812, root / "tests" / "validation_profiles", root / "tests" / "validation_results"


def provenance_lines() -> list[str]:
    """The lines a generated file's header carries so it says what it was captured from."""
    return [
        f" * Reference: {PY1812_REPO} at {PY1812_COMMIT[:12]} ({PY1812_REVISION}),",
        f" * captured on {PY1812_CAPTURE}; another platform moves last digits, inside tolerance.",
        " * Regenerating against any other commit is a deliberate bump of PY1812_COMMIT in",
        " * scripts/p1812_ref.py, never a silent drift.",
    ]
