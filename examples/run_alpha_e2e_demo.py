#!/usr/bin/env python3
"""Alpha end-to-end demo: one bounded fixture-only research path.

    python examples/run_alpha_e2e_demo.py --state-dir .solaris_ai_nn_alpha/test_e2e --max-ticks 25

Runs the same bounded orchestration the CLI ``run-demo`` command uses: initialize
state, build the module registry, run doctor, execute the fixture demo path, and
write the alpha report, artifact index, and operator runbook. The demo is
fixture-only, completes quickly, and shows skipped modules honestly. It controls no
feeders/hardware, calls no Git/GitHub, publishes nothing, and makes no
consciousness/life/agency claim.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.alpha_system import AlphaResearchOrchestrator


def main():
    parser = argparse.ArgumentParser(description="Alpha end-to-end demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_alpha/test_e2e")
    parser.add_argument("--max-ticks", type=int, default=25, dest="max_ticks")
    parser.add_argument("--max-runtime-s", type=float, default=60.0,
                        dest="max_runtime_s")
    args = parser.parse_args()

    orch = AlphaResearchOrchestrator(
        state_dir=args.state_dir, max_ticks=args.max_ticks,
        max_runtime_s=args.max_runtime_s)
    result = orch.run()
    status = orch.alpha_status()

    print("=== Alpha end-to-end demo ===")
    print(f"  profile               : {status['alpha_profile_id']} "
          f"(fixture-only)")
    print(f"  modules available     : {status['alpha_available_module_count']}/"
          f"{status['alpha_module_count']} "
          f"(missing {status['alpha_missing_module_count']}, blocked "
          f"{status['alpha_blocked_module_count']})")
    print(f"  demo steps            : "
          f"{status['alpha_demo_step_completed_count']} completed, "
          f"{status['alpha_demo_step_skipped_count']} skipped")
    print(f"  artifacts             : {status['alpha_artifact_count']}")
    print(f"  cycle stage           : {status['alpha_cycle_stage']}")
    print(f"  next action           : {status['alpha_next_action']}")
    print(f"  blockers / warnings   : {result['blocker_count']} / "
          f"{result['warning_count']}")
    print(f"  controls feeders/git  : {status['controls_feeders']} / "
          f"{status['calls_github']}")
    print("  generated:")
    print(f"    state manifest      : {orch.layout.manifest_path}")
    print(f"    artifact index      : {orch.artifact_index.json_path}")
    print(f"    alpha report        : {status['latest_alpha_report_path']}")
    print("note                    : the alpha demo is local, bounded, and "
          "fixture-only. Skipped modules are shown honestly. It controls no "
          "feeders/hardware, calls no Git/GitHub, publishes nothing, and makes "
          "no consciousness/life/agency claim.")


if __name__ == "__main__":
    main()
