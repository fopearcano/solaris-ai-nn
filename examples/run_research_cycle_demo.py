#!/usr/bin/env python3
"""Closed research cycle demo: where is the program, what is blocked, what next.

    python examples/run_research_cycle_demo.py --state-dir .solaris_ai_nn_research_cycle/test_demo

Runs the closed research cycle tracker on a validated cycle (baseline ->
roadmap -> architecture -> experiment pack -> intake -> post-merge -> validated
baseline, with an operator merge confirmation) and on a blocked cycle (a critical
safety regression at intake). The tracker reads the local evidence bundle and
writes reports only: it modifies no source, runs no Git, calls no GitHub, creates
no branch/tag/release/PR, executes no validation command, runs no external agent,
and never approves itself.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.research_cycle import ResearchCycleRuntime


def _validated_bundle():
    return {
        "cycle_manifest": {"cycle_id": "cycle_3", "parent_cycle_id": "cycle_2",
                           "baseline_id": "baseline_v2"},
        "research_baseline": {"baseline_status": "validated",
                              "safety_boundary_status": "pass",
                              "critical_limitation_count": 0},
        "roadmap": {"roadmap_item_count": 4},
        "architecture_evolution": {"proposal_count": 2},
        "experiment_compiler": {"ready_spec_count": 3,
                                "safety_gate_failure_count": 0},
        "implementation_intake": {"merge_recommendation_status": "recommend",
                                  "critical_safety_regression_count": 0,
                                  "coverage_gap_count": 0},
        "post_merge": {"candidate_baseline_status": "validated",
                       "critical_regression_count": 0,
                       "rollback_recommendation_status": "none"},
        "soak": {"status": "pass"},
        "replication": {"status": "pass"},
        "falsification": {"falsified_claim_count": 0},
        "operator_decisions": [
            {"decision_type": "confirm_external_merge", "status": "approved",
             "operator_ref": "operator:local"},
            {"decision_type": "approve_candidate_baseline", "status": "approved",
             "operator_ref": "operator:local"}],
    }


def _blocked_bundle():
    return {
        "cycle_manifest": {"cycle_id": "cycle_4", "parent_cycle_id": "cycle_3"},
        "research_baseline": {"baseline_status": "in_progress"},
        "roadmap": {"roadmap_item_count": 3},
        "architecture_evolution": {"proposal_count": 1},
        "experiment_compiler": {"ready_spec_count": 2,
                                "safety_gate_failure_count": 0},
        "implementation_intake": {
            "merge_recommendation_status": "block_merge_due_to_safety",
            "critical_safety_regression_count": 1, "coverage_gap_count": 2},
    }


def _run(label, bundle, state_dir):
    rt = ResearchCycleRuntime(state_dir=state_dir, require_operator_decisions=True)
    rt.load_bundle(bundle)
    rt.run()
    rt.write_artifacts()
    st = rt.research_cycle_status()
    print(f"=== {label} ===")
    print(f"  stage                 : {st['current_cycle_stage']} "
          f"({st['current_cycle_status']})")
    print(f"  decision gates        : {st['decision_gate_count']} "
          f"(failed {st['failed_decision_gate_count']})")
    print(f"  operator decisions req: {st['operator_decision_required_count']}")
    print(f"  blocked states        : {st['blocked_state_count']} "
          f"(unresolved {st['unresolved_blocker_count']})")
    print(f"  evidence ledger       : {st['evidence_ledger_entry_count']} entries "
          f"(missing {st['missing_evidence_entry_count']}, negative "
          f"{st['negative_evidence_entry_count']}, falsified "
          f"{st['falsified_evidence_entry_count']})")
    print(f"  next actions          : {st['next_action_count']}")
    for a in rt.next_actions.get("actions", []):
        ctx = f" [{a['safety_context']}]" if a.get("safety_context") else ""
        print(f"    - [{a['priority']}] {a['action_type']}: "
              f"{a['detail']}{ctx}")
    print(f"  approves itself        : {st['approves_itself']}")
    print(f"  runs git / github      : {st['runs_git']} / {st['calls_github']}")
    print(f"  report                 : {st['latest_research_cycle_report_path']}")


def main():
    parser = argparse.ArgumentParser(description="Closed research cycle demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_research_cycle/test_demo")
    args = parser.parse_args()

    _run("Validated cycle", _validated_bundle(),
         os.path.join(args.state_dir, "validated"))
    print()
    _run("Blocked cycle (critical safety)", _blocked_bundle(),
         os.path.join(args.state_dir, "blocked"))
    print()
    print("note                  : the cycle tracker reports where the research "
          "program is, what is blocked, and what the operator should do next. It "
          "tracks the scientific state only -- it executes nothing, never "
          "approves itself, and makes no consciousness/life claim.")


if __name__ == "__main__":
    main()
