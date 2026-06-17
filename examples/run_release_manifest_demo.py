#!/usr/bin/env python3
"""Release manifest demo: deterministic manifest with required/optional artifacts.

    python examples/run_release_manifest_demo.py \\
        --tester-state-dir .solaris_ai_nn_tester/test_manifest

Builds the local release artifact manifest and prints the package metadata, readiness,
and required/optional artifact listing. It does not call Git (the commit is read from
.git/HEAD if present, otherwise 'unknown') and it does not publish a release.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.tester_packaging import ReleaseManifestBuilder


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tester-state-dir",
                    default=".solaris_ai_nn_tester/test_manifest")
    args = ap.parse_args()
    manifests_dir = os.path.join(args.tester_state_dir, "packaging", "manifests")

    builder = ReleaseManifestBuilder()
    manifest = builder.build()
    path = builder.write(manifests_dir)
    d = manifest.to_dict()
    print("release manifest demo")
    print(f"  package    : {d['package_name']} {d['version']}")
    print(f"  commit     : {d['commit'][:12]} (read without calling Git)")
    print(f"  python req : {d['python_requirement']}")
    print(f"  readiness  : {d['readiness']}")
    print(f"  artifacts  : {d['artifact_count']} (by kind {d['by_kind']})")
    print(f"  missing required: {d['missing_required']}")
    print(f"  missing optional: {d['missing_optional']}")
    print(f"  manifest   : {path}")
    print(f"  calls git  : {d['calls_git']}; publishes: {d['publishes_release']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
