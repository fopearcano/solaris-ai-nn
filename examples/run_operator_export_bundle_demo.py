#!/usr/bin/env python3
"""Operator export-bundle demo: safety + research bundles, checksums, no upload.

    python examples/run_operator_export_bundle_demo.py --state-dir .solaris_ai_nn_operator/test_export

Seeds a couple of local reports, builds a safety-review bundle and a
research-review bundle, and shows that each bundle includes checksums and a
clear local-export-only note, and is never uploaded.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.operator_console import ExportBundleBuilder, OperatorConsoleConfig


def main():
    parser = argparse.ArgumentParser(description="Operator export-bundle demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_operator/test_export")
    args = parser.parse_args()
    cfg = OperatorConsoleConfig(state_dir=args.state_dir)
    cfg.ensure_dirs()

    # Seed local reports under the operator state dir so the indexer finds them.
    with open(os.path.join(cfg.state_dir, "SAFETY_INVARIANT_REPORT.json"), "w",
              encoding="utf-8") as fh:
        json.dump({"status": "ok", "summary": "invariants held"}, fh)
    with open(os.path.join(cfg.state_dir, "research_report.json"), "w",
              encoding="utf-8") as fh:
        json.dump({"summary": "operational evidence only"}, fh)

    builder = ExportBundleBuilder(config=cfg, safety_status={"status": "ok",
                                                             "unresolved_blocker_count": 0})
    safety_bundle = builder.build("safety_review_bundle")
    research_bundle = builder.build("research_review_bundle")

    print("=== Operator export-bundle demo ===")
    print(f"safety bundle id      : {safety_bundle.bundle_id}")
    print(f"  included files      : {len(safety_bundle.included_files)}")
    print(f"  checksums included  : {bool(safety_bundle.checksums)}")
    print(f"  uploaded            : {safety_bundle.uploaded}")
    print(f"research bundle id    : {research_bundle.bundle_id}")
    print(f"  included files      : {len(research_bundle.included_files)}")
    print(f"  checksums included  : {bool(research_bundle.checksums)}")
    print(f"  bundle dir          : {research_bundle.bundle_dir}")
    print("note                  : local export only; no upload, no network "
          "calls.")


if __name__ == "__main__":
    main()
