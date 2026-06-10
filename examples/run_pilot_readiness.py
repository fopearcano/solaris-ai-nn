#!/usr/bin/env python3
"""Generate a pilot readiness report WITHOUT running the pilot.

    python examples/run_pilot_readiness.py --profile simulated
    python examples/run_pilot_readiness.py --profile read_only_stream \
        --input examples/sample_streams/sensory_events.jsonl
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.governance import GovernancePolicy
from solaris_ai_nn.pilot import (
    PilotManifest,
    PilotProfileType,
    PilotReadinessCheck,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Pilot readiness check")
    parser.add_argument("--profile", type=str, default="simulated",
                        choices=list(PilotProfileType.ALL))
    parser.add_argument("--input", type=str, default=None,
                        help="input file (read_only_stream profile)")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/pilot_readiness")
    parser.add_argument("--artifact-dir", type=str,
                        default=".solaris_ai_nn_pilots/readiness")
    parser.add_argument("--operator", type=str, default="local-operator")
    args = parser.parse_args()

    manifest = PilotManifest(
        profile=args.profile, operator=args.operator,
        state_dir=args.state_dir, artifact_dir=args.artifact_dir,
        input_sources=[args.input] if args.input else [],
        max_steps=100,
        notes="readiness check only; the pilot itself is not run")
    check = PilotReadinessCheck(manifest=manifest,
                                governance=GovernancePolicy())
    report = check.run({
        "quick_suite_passed": "skipped",
        "restart_demo_passed": "skipped",
        # Explicit CLI directories are the operator's approved outputs.
        "approved_output_roots": [args.state_dir, args.artifact_dir],
    })

    out_dir = Path(args.artifact_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "readiness_report.json"
    md_path = out_dir / "readiness_report.md"
    json_path.write_text(json.dumps(report.to_dict(), indent=2, default=str),
                         encoding="utf-8")
    md_path.write_text(report.to_markdown(), encoding="utf-8")

    print("=" * 70)
    print(f"Pilot readiness: profile {args.profile!r}")
    print("=" * 70)
    print(f"verdict:   {'READY' if report.ready else 'NOT READY'}")
    for issue in report.blocking_issues():
        print(f"  BLOCKING [{issue.area}] {issue.detail}")
    for issue in report.warnings():
        print(f"  warning  [{issue.area}] {issue.detail}")
    print(f"next step: {report.recommended_next_step}")
    print(f"report:    {md_path}")


if __name__ == "__main__":
    main()
