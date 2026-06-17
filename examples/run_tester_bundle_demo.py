#!/usr/bin/env python3
"""Tester bundle demo: generate a local artifact bundle and list its manifest.

    python examples/run_tester_bundle_demo.py --state-dir .solaris_ai_nn_tester/bundle

Runs the tester demo with the optional learning stages disabled, then prints the local
artifact bundle manifest -- including the entries and the missing optional artifacts --
showing that the bundle is local-only and lists missing optional artifacts clearly.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.tester_fixture_spine import TesterFixtureDemoRuntime


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--state-dir", default=".solaris_ai_nn_tester/bundle")
    args = ap.parse_args()

    # Membrane-only profile -> optional learning stages skip honestly, so their
    # summaries are listed as missing optional artifacts in the bundle.
    rt = TesterFixtureDemoRuntime(state_dir=args.state_dir,
                                  profile="fixture_membrane_only_v0")
    rt.run()
    m = rt.bundle.manifest.to_dict() if rt.bundle else {}
    print("tester artifact bundle demo")
    print(f"  bundle dir       : {m.get('bundle_dir')}")
    print(f"  entries          : {m.get('entry_count', 0)}")
    print(f"  missing optional : "
          f"{', '.join(m.get('missing_optional_artifacts', [])) or 'none'}")
    print(f"  local only       : {m.get('local_only')}")
    print(f"  zipped/uploaded  : {m.get('zipped')} / {m.get('uploaded')}")
    print(f"  published        : {m.get('published')}")
    print(f"  skipped stages   : {', '.join(rt.skipped_stages) or 'none'}")
    print("note: the tester bundle is local-only and human-readable; nothing is "
          "zipped automatically, uploaded, or published.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
