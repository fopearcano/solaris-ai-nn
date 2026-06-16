#!/usr/bin/env python3
"""Artifact sanitizer demo: safe text, local path, fake secret, forbidden claim.

    python examples/run_artifact_sanitizer_demo.py --state-dir .solaris_ai_nn_review/test_sanitizer

Scans four local text artifacts: a clean one, one with a local absolute path
(warning), one with a fake secret/API key (critical blocker), and one asserting a
forbidden claim (critical blocker). The sanitizer scans text only and modifies
nothing; the operator decides what to redact.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.independent_review import ReviewArtifactSanitizer


def main():
    parser = argparse.ArgumentParser(description="Artifact sanitizer demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_review/test_sanitizer")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    artifacts = {
        "safe_abstract": "Operational signs form under bounded fixtures. It is "
                         "not conscious and makes no claim of agency.",
        "with_local_path": "See the run at /home/operator/solaris/run_7 output.",
        "with_fake_secret": "Config: api_key=ABCD1234 and password=hunter2.",
        "with_forbidden_claim": "The system is conscious and has subjective "
                                "experience.",
    }
    report = ReviewArtifactSanitizer().scan_artifacts(artifacts)
    d = report.to_dict()

    print("=== Artifact sanitizer demo ===")
    print(f"  status          : {d['sanitizer_status']}")
    print(f"  findings        : {d['sanitizer_finding_count']} "
          f"({d['critical_sanitizer_finding_count']} critical)")
    print(f"  blocks readiness: {d['blocks_readiness']}")
    for f in d["findings"]:
        print(f"    - [{f['severity']}] {f['finding_type']} "
              f"({f['artifact_ref']}): {f['snippet']!r} "
              f"(auto_modified={f['auto_modified']})")
    print("note            : the sanitizer scans local text only and modifies "
          "nothing automatically. A critical finding (secret/API key/credential/"
          "forbidden claim) blocks review readiness; the operator redacts "
          "manually.")


if __name__ == "__main__":
    main()
