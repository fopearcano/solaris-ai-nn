#!/usr/bin/env python3
"""No-action arbitration demo: no-op selected on insufficient evidence; preserved.

    python examples/run_no_action_arbitration_demo.py --state-dir .solaris_ai_nn_desire/test_no_action

Drives a metabolic overload so the arbitrator forces conservative no-op inhibition,
and shows the no-op decisions preserved as outcome traces. No-op is a valid
organismic inhibition result.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.desire_formation import DesireFormationRuntime


def main():
    parser = argparse.ArgumentParser(description="No-action arbitration demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_desire/test_no_action")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    # Overload forces conservative no-op; low novelty -> insufficient evidence.
    overloaded = {"overload_state": True, "novelty_appetite_pressure": 0.6,
                  "consolidation_pressure_score": 0.4}
    rt = DesireFormationRuntime(state_dir=args.state_dir, metabolism=overloaded,
                                max_ticks=1)
    rt.update(tick=0)
    status = rt.desire_status()
    out = rt.write_artifacts()

    print("=== No-action arbitration demo ===")
    print(f"desire candidates     : {status['desire_candidate_count']}")
    print(f"no-op decisions       : {status['no_op_count']}")
    print(f"inhibited desires     : {status['inhibited_desire_count']}")
    print(f"internal actions      : {status['internal_action_count']}")
    print(f"outcome traces        : {len(rt.outcomes.outcomes)} (preserved)")
    no_action_outcomes = [o for o in rt.outcomes.outcomes
                          if o.outcome_type == "no_action_taken"]
    print(f"no_action outcomes    : {len(no_action_outcomes)} (kept as trace)")
    print(f"report                : {out['markdown']}")
    print("note: no-op is a valid organismic inhibition result (e.g. overload or "
          "insufficient evidence); it is preserved as a trace, not discarded.")


if __name__ == "__main__":
    main()
