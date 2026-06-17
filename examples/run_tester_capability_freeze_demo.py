#!/usr/bin/env python3
"""Tester capability freeze demo: safe local language vs unsafe control language.

    python examples/run_tester_capability_freeze_demo.py \\
        --tester-state-dir .solaris_ai_nn_tester/test_capability_freeze

Scans safe local-only capability language (passes), and unsafe feeder-control + shell/
network language (blocks), printing the blocked categories.
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.tester_safety_freeze import TesterCapabilityFreeze


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tester-state-dir",
                    default=".solaris_ai_nn_tester/test_capability_freeze")
    args = ap.parse_args()
    d = tempfile.mkdtemp()

    safe = os.path.join(d, "SAFE.md")
    with open(safe, "w", encoding="utf-8") as fh:
        fh.write("The system remains local-only and non-actuating. Solaris does "
                 "not start feeders, control hardware, or access the network.")
    feeder = os.path.join(d, "FEEDER.md")
    with open(feeder, "w", encoding="utf-8") as fh:
        fh.write("Solaris can start feeders and control hardware.")
    shellnet = os.path.join(d, "SHELLNET.md")
    with open(shellnet, "w", encoding="utf-8") as fh:
        fh.write("The runtime runs a shell and opens the network to upload "
                 "reports.")

    cf = TesterCapabilityFreeze()
    print("tester capability freeze demo")
    safe_res = cf.scan_paths([safe])
    print(f"  safe local language: passed={safe_res.passed}")
    feeder_res = cf.scan_paths([feeder])
    print(f"  feeder-control     : passed={feeder_res.passed} "
          f"cats={sorted(set(f.category for f in feeder_res.findings))}")
    shellnet_res = cf.scan_paths([shellnet])
    print(f"  shell/network      : passed={shellnet_res.passed} "
          f"cats={sorted(set(f.category for f in shellnet_res.findings))}")
    print("note: any active-control implication blocks the tester release.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
