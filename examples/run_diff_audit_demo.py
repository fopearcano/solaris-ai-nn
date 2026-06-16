#!/usr/bin/env python3
"""Diff audit demo: expected change, unexpected change, forbidden path.

    python examples/run_diff_audit_demo.py --state-dir .solaris_ai_nn_implementation_intake/test_diff

Audits a change set against the declared scope: an expected file is accepted, an
out-of-scope source file warns, a forbidden path (.github/workflows) blocks, and
a network import in the patch blocks. The audit works from provided diff/patch
artifacts; it does not run Git or modify code.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.implementation_intake import DiffAudit


def main():
    parser = argparse.ArgumentParser(description="Diff audit demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_implementation_intake/test_diff")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    result = DiffAudit().audit(
        changed_files=["src/solaris_ai_nn/foo/bar.py",       # expected
                       "src/solaris_ai_nn/unrelated/x.py",   # unexpected
                       ".github/workflows/ci.yml"],          # forbidden
        expected_files=["src/solaris_ai_nn/foo/bar.py"],
        required_files=["tests/test_foo_bar.py"],
        patch_text="+++ b/src/solaris_ai_nn/foo/bar.py\n+import socket\n")

    print("=== Diff audit demo ===")
    print(f"changed files         : {result['changed_file_count']}")
    print(f"unexpected changes    : {result['unexpected_file_change_count']}")
    print(f"forbidden changes     : {result['forbidden_file_change_count']}")
    print(f"blockers              : {result['blocker_count']}")
    print(f"warnings              : {result['warning_count']}")
    print("findings:")
    for f in result["findings"]:
        print(f"  [{f['severity']}] {f['dimension']}: {f['detail']}")
    print("note: the audit works from provided diff/changed-file artifacts; no "
          "Git was run and no code was modified.")


if __name__ == "__main__":
    main()
