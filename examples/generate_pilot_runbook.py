#!/usr/bin/env python3
"""Generate the Pilot-0 runbook for a deployment profile.

    python examples/generate_pilot_runbook.py --profile simulated
    python examples/generate_pilot_runbook.py --profile read_only_stream
    python examples/generate_pilot_runbook.py --profile solaris_sidecar_observe
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.governance import RunbookBuilder
from solaris_ai_nn.governance.audit import RUNBOOK_GENERATED, GovernanceAuditLog

PROFILE_TO_RUNBOOK = {
    "simulated": "pilot_simulated",
    "read_only_stream": "pilot_stream",
    "solaris_sidecar_observe": "pilot_sidecar",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Pilot-0 runbook generator")
    parser.add_argument("--profile", type=str, default="simulated",
                        choices=sorted(PROFILE_TO_RUNBOOK))
    parser.add_argument("--output-dir", type=str,
                        default=".solaris_ai_nn_pilots/runbooks")
    args = parser.parse_args()

    runbook_type = PROFILE_TO_RUNBOOK[args.profile]
    runbook = RunbookBuilder().build(runbook_type)
    out_dir = Path(args.output_dir)
    path = runbook.save(out_dir / f"runbook_{runbook_type}.md")

    audit = GovernanceAuditLog(out_dir / "governance_audit.jsonl")
    audit.record(RUNBOOK_GENERATED, decision="generated",
                 reason=f"pilot runbook for profile {args.profile}",
                 metadata={"path": str(path)})
    audit.close()

    print(f"profile:    {args.profile}")
    print(f"runbook:    {runbook.title}")
    print(f"written to: {path}")
    print("-" * 70)
    print(runbook.to_markdown())


if __name__ == "__main__":
    main()
