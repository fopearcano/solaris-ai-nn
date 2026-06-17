#!/usr/bin/env python3
"""Install guide demo: generate the quickstart, install guide, and platform notes.

    python examples/run_install_guide_demo.py \\
        --tester-state-dir .solaris_ai_nn_tester/test_install_guide

Generates the install guide, quickstart, and troubleshooting docs, plus the Windows/
macOS/Linux platform notes, and prints where they were written.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.tester_packaging import (
    PlatformNotesBuilder,
    TesterInstallGuideBuilder,
)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tester-state-dir",
                    default=".solaris_ai_nn_tester/test_install_guide")
    args = ap.parse_args()
    packaging = os.path.join(args.tester_state_dir, "packaging")

    guides = TesterInstallGuideBuilder().write(
        os.path.join(packaging, "install_guides"))
    platforms = PlatformNotesBuilder().write(
        os.path.join(packaging, "platforms"))
    print("install guide demo")
    for label, path in guides.items():
        print(f"  {label}: {path}")
    for kind, path in platforms.items():
        print(f"  platform {kind}: {path}")
    print("note: the guides document a local editable install (no global "
          "install, no publish/upload, no release/tag automation).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
