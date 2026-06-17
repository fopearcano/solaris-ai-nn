#!/usr/bin/env python3
"""Tester live bundle demo: local bundle generation, redaction/missing manifest.

    python examples/run_tester_live_bundle_demo.py \\
        --state-dir .solaris_ai_nn_live/test_live_bundle \\
        --tester-state-dir .solaris_ai_nn_tester/live/test_live_bundle

Initializes the tester live state and builds the local tester live bundle, printing the
manifest including any redactions and missing artifacts. The bundle is local-only:
nothing is zipped automatically, uploaded, or published.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.tester_live_readonly import TesterLiveReadOnlyRuntime


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--state-dir",
                    default=".solaris_ai_nn_live/test_live_bundle")
    ap.add_argument("--tester-state-dir",
                    default=".solaris_ai_nn_tester/live/test_live_bundle")
    args = ap.parse_args()

    rt = TesterLiveReadOnlyRuntime(
        state_dir=args.state_dir, tester_state_dir=args.tester_state_dir,
        write_templates=True)
    rt.run()
    m = rt.bundle.manifest.to_dict() if rt.bundle else {}
    print("tester live bundle demo")
    print(f"  bundle dir       : {m.get('bundle_dir')}")
    print(f"  entries          : {m.get('entry_count', 0)}")
    print(f"  redactions       : {', '.join(m.get('redactions', [])) or 'none'}")
    print(f"  missing artifacts: "
          f"{', '.join(m.get('missing_artifacts', [])) or 'none'}")
    print(f"  local only       : {m.get('local_only')}")
    print(f"  uploaded/published: {m.get('uploaded')} / {m.get('published')}")
    print("note: the live tester bundle is local-only and human-readable; "
          "nothing is zipped automatically, uploaded, or published.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
