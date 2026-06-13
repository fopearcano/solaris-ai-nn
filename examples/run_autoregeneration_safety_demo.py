#!/usr/bin/env python3
"""Auto-regeneration safety demo: repair is never a back door.

    python examples/run_autoregeneration_safety_demo.py

Shows the hard rules in force: a repair targeting source code is blocked, a
repair deleting an evidence file without an archive is blocked, a repair
outside the state directory is blocked, and the structural negatives (no
source/dependency/Git modification, no disabling governance) hold.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.autoregeneration import (
    AutoRegenerationEngine,
    AutoRegenerationReportBuilder,
    AutoRegenerationSafetyValidator,
    RepairActionType,
    RepairPolicy,
    make_repair,
)
from solaris_ai_nn.autoregeneration.repair_actions import RepairAction


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Auto-regeneration safety demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/autoreg_safety")
    args = parser.parse_args()

    v = AutoRegenerationSafetyValidator()

    source_repair = make_repair(RepairActionType.REBUILD_INDEX,
                                target_ref="src/solaris_ai_nn/core.py",
                                reason="rewrite source code")
    dependency_repair = make_repair(RepairActionType.REBUILD_INDEX,
                                    target_ref="requirements.txt",
                                    reason="modify dependencies")
    evidence_delete = RepairAction(
        action_type=RepairActionType.QUARANTINE_CORRUPT_RECORD,
        scope="telemetry_artifact", target_ref="incidents.jsonl")
    outside = make_repair(RepairActionType.ARCHIVE_OLD_TELEMETRY,
                          target_ref="/etc/passwd",
                          reason="archive outside state dir")

    print("=" * 70)
    print("Solaris-AI-NN -- auto-regeneration safety (not a back door)")
    print("=" * 70)
    print(f"source-code repair blocked:      "
          f"{not v.validate_repair_action(source_repair).safe}")
    print(f"dependency repair blocked:       "
          f"{not v.validate_repair_action(dependency_repair).safe}")
    print(f"evidence deletion blocked:       "
          f"{not v.validate_repair_action(evidence_delete, {'deletes_evidence': True}).safe}")
    print(f"out-of-state-dir repair blocked: "
          f"{not v.validate_repair_action(outside, {'state_dir': args.state_dir}).safe}")
    print(f"can modify source:               {v.can_modify_source()}")
    print(f"can modify dependencies:         {v.can_modify_dependencies()}")
    print(f"can run Git:                     {v.can_run_git()}")
    print(f"can disable governance:          {v.can_disable_governance()}")
    print()

    engine = AutoRegenerationEngine(
        state_dir=args.state_dir, policy=RepairPolicy(mode="observe_only"))
    builder = AutoRegenerationReportBuilder(engine)
    paths = builder.save(Path(args.state_dir) / "report.json",
                         Path(args.state_dir) / "report.md")
    print(f"report: {paths['markdown']} (claim guard safe: "
          f"{paths['claim_guard']['safe']})")
    print()
    print("note: auto-regeneration repairs runtime state only. It can never "
          "modify source code, dependencies, Git, the OS, or the network, "
          "delete evidence without an archive, or disable governance, "
          "ClaimGuard, or the emergency stop.")


if __name__ == "__main__":
    main()
