#!/usr/bin/env python3
"""Tester golden manifest demo: build the golden manifest and check its structure.

    python examples/run_tester_golden_demo.py --state-dir .solaris_ai_nn_tester/golden

Runs the tester demo to build (or rebuild) the golden run manifest, then prints the
expected artifact structure -- required vs optional, present vs missing -- showing that
the manifest tolerates changing run ids and timestamps and checks semantics, not
fragile values.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.tester_fixture_spine import (
    GoldenRunManifest,
    TesterFixtureDemoRuntime,
)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--state-dir", default=".solaris_ai_nn_tester/golden")
    args = ap.parse_args()

    rt = TesterFixtureDemoRuntime(state_dir=args.state_dir,
                                  profile="fixture_tester_v0",
                                  regenerate_golden=True)
    rt.run()
    manifest = GoldenRunManifest.load(rt.state_dir)
    d = manifest.to_dict() if manifest else {}
    print("tester golden manifest")
    print(f"  profile        : {d.get('profile_id')}")
    print(f"  fixture hash   : {d.get('fixture_hash', '')[:16]}")
    print(f"  artifacts      : {d.get('artifact_count', 0)} "
          f"(required {d.get('required_artifact_count', 0)}, "
          f"missing required {d.get('missing_required_artifact_count', 0)})")
    print("  expected structure:")
    for a in d.get("artifacts", []):
        print(f"    - {a['artifact_type']:36s} required={a['required']!s:5s} "
              f"{a['status']}")
    print("note: the golden manifest records expected structure + safety "
          "invariants; it tolerates run ids/timestamps. Missing required "
          "artifacts fail reproducibility.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
