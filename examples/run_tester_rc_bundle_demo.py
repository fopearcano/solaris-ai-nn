#!/usr/bin/env python3
"""Tester RC bundle demo: local bundle generation, manifest, missing-artifact report.

    python examples/run_tester_rc_bundle_demo.py \\
        --tester-state-dir .solaris_ai_nn_tester/test_rc_bundle

Assembles the local RC bundle and prints the bundle directory, the included/missing
artifact counts, and confirmation that nothing was uploaded or published. The bundle is
local only; it is shared manually only if a tester requests it.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.tester_release_candidate import TesterRCRuntime


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tester-state-dir",
                    default=".solaris_ai_nn_tester/test_rc_bundle")
    args = ap.parse_args()

    rt = TesterRCRuntime(tester_state_dir=args.tester_state_dir,
                         profile="tester_rc_bundle_only_v0", max_runtime_s=60.0)
    rt.run()
    b = rt.bundle.to_dict()
    print("tester rc bundle demo")
    print(f"  bundle dir : {b['bundle_dir']}")
    print(f"  included   : {b['included_count']}")
    print(f"  missing    : {b['missing_count']}")
    print(f"  zipped     : {b['zipped']}")
    print(f"  uploaded   : {b['uploaded']}; published: {b['published']}")
    print("  missing artifacts:")
    for a in b["missing"][:10]:
        print(f"    - {a['name']}")
    print("note: local bundle only; nothing uploaded/published/tagged/released; "
          "no private payloads; no consciousness/life/agency claim.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
