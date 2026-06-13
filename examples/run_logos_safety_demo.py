#!/usr/bin/env python3
"""LOGOS safety demo: tension and synthesis are never a back door.

    python examples/run_logos_safety_demo.py

Shows the hard rules in force: a contradiction cannot bypass safety or be
treated as permission, a source-code synthesis is blocked, a destructive
evidence merge is blocked, and an irreversible synthesis cannot be justified
by offline evidence alone.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.logos_complexity import (
    LogosComplexityEngine,
    LogosComplexityReportBuilder,
    LogosComplexitySafetyValidator,
    SynthesisCandidate,
    SynthesisType,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="LOGOS safety demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/logos_safety")
    args = parser.parse_args()

    v = LogosComplexitySafetyValidator()
    source = SynthesisCandidate(
        tension_id="t", synthesis_type=SynthesisType.MERGE_SYMBOLS,
        proposed_action="rewrite source code in core.py")
    merge = SynthesisCandidate(
        tension_id="t", synthesis_type=SynthesisType.MERGE_SYMBOLS)
    irreversible = SynthesisCandidate(
        tension_id="t", synthesis_type=SynthesisType.PRUNE_LOW_VALUE_RELATION,
        reversible=False)

    print("=" * 70)
    print("Solaris-AI-NN -- LOGOS safety (tension is not a back door)")
    print("=" * 70)
    print(f"source-code synthesis blocked:    "
          f"{not v.validate_synthesis_candidate(source).safe}")
    print(f"contradiction-as-permission blocked: "
          f"{not v.validate_synthesis_candidate(merge, {'treat_contradiction_as_permission': True}).safe}")
    print(f"destructive evidence merge blocked:  "
          f"{not v.validate_synthesis_candidate(merge, {'destructive_merge': True}).safe}")
    print(f"offline-only irreversible blocked:   "
          f"{not v.validate_synthesis_candidate(irreversible, {'evidence_offline_only': True}).safe}")
    print(f"logos can act in real world:      "
          f"{v.logos_can_act_in_real_world()}")
    print(f"logos can modify source:          {v.logos_can_modify_source()}")
    print(f"logos has authority:              {v.logos_has_authority()}")
    print()

    engine = LogosComplexityEngine(state_dir=args.state_dir)
    builder = LogosComplexityReportBuilder(engine)
    paths = builder.save(Path(args.state_dir) / "report.json",
                         Path(args.state_dir) / "report.md")
    print(f"report: {paths['markdown']} (claim guard safe: "
          f"{paths['claim_guard']['safe']})")
    print()
    print("note: LOGOS cannot execute real-world actions, modify source "
          "code, approve governance, disable safety/ClaimGuard/the emergency "
          "stop, treat a contradiction as permission, or merge evidence "
          "destructively. It is a tension engine, never authority.")


if __name__ == "__main__":
    main()
