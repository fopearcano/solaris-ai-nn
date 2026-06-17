#!/usr/bin/env python3
"""Tester RC manifest demo: manifest generation, missing modules/artifacts.

    python examples/run_tester_rc_manifest_demo.py \\
        --tester-state-dir .solaris_ai_nn_tester/test_rc_manifest

Builds the RC manifest against a fresh tester state and prints the package metadata, the
commit hash (read from .git/HEAD as a file, never a Git call), the readiness, the missing
required artifacts, and the known-missing optional modules (warning only). The manifest is
local only and implies no publication.
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
                    default=".solaris_ai_nn_tester/test_rc_manifest")
    args = ap.parse_args()

    rt = TesterRCRuntime(tester_state_dir=args.tester_state_dir,
                         profile="tester_rc_manifest_only_v0",
                         max_runtime_s=60.0)
    rt.run()
    m = rt.manifest.to_dict()
    print("tester rc manifest demo")
    print(f"  rc id        : {m['rc_id']}")
    print(f"  package      : {m['package_name']} "
          f"{m['package_version'] or '(version unknown)'}")
    print(f"  python        : {m['python_requirement']}")
    print(f"  commit       : {m['commit_hash']}")
    print(f"  readiness    : {m['readiness']}")
    print(f"  missing req  : {m['missing_required_artifact_count']} "
          f"({m['artifacts'] and 'see manifest' or 'none'})")
    print(f"  missing optional modules (warning only): "
          f"{m['known_missing_optional_modules']}")
    print(f"  implies publication: {m['implies_publication']}; uploaded: "
          f"{m['uploaded']}")
    print("note: local manifest only; missing optional modules are warnings, "
          "missing required artifacts block readiness; nothing is published.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
