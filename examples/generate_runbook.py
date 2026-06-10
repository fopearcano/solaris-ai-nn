#!/usr/bin/env python3
"""Generate a Markdown runbook for an experiment type.

    python examples/generate_runbook.py --type bounded
    python examples/generate_runbook.py --type plasticity --output-dir docs/templates
    python examples/generate_runbook.py --type soak24
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.governance import RUNBOOK_TYPES, RunbookBuilder
from solaris_ai_nn.governance.audit import RUNBOOK_GENERATED, GovernanceAuditLog


def main() -> None:
    parser = argparse.ArgumentParser(description="Runbook generator")
    parser.add_argument("--type", type=str, default="bounded",
                        choices=list(RUNBOOK_TYPES))
    parser.add_argument("--output-dir", type=str,
                        default=".solaris_ai_nn_governance")
    args = parser.parse_args()

    runbook = RunbookBuilder().build(args.type)
    out_dir = Path(args.output_dir)
    path = runbook.save(out_dir / f"runbook_{args.type}.md")

    audit = GovernanceAuditLog(out_dir / "governance_audit.jsonl")
    audit.record(RUNBOOK_GENERATED, decision="generated",
                 reason=f"runbook type {args.type}",
                 metadata={"path": str(path)})
    audit.close()

    print(f"runbook type: {runbook.runbook_type}")
    print(f"title:        {runbook.title}")
    print(f"sections:     {len(runbook.sections)}")
    print(f"written to:   {path}")
    print("-" * 70)
    print(runbook.to_markdown())


if __name__ == "__main__":
    main()
