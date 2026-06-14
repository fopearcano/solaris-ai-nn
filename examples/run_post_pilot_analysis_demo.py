#!/usr/bin/env python3
"""Post-pilot analysis demo: create mock artifacts, run forensics, write reports.

    python examples/run_post_pilot_analysis_demo.py --state-dir .solaris_ai_nn_pilot1/test_post_pilot

Writes a small mock Pilot-1 artifact set, runs the read-only post-pilot
forensic pipeline, and generates the post-pilot analysis report and research
dossier. No real pilot is required; nothing in runtime state is mutated; and
no consciousness claim is made.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.post_pilot import PostPilotForensics


def _write_mock_artifacts(base: str, state: str) -> None:
    os.makedirs(os.path.join(base, "daily"), exist_ok=True)
    os.makedirs(state, exist_ok=True)
    with open(os.path.join(base, "observability.jsonl"), "w",
              encoding="utf-8") as fh:
        for i in range(8):
            fh.write(json.dumps({"kind": "metrics", "payload": {
                "structural_change_score": 0.04 * i,
                "proto_symbol_count": i}}) + "\n")
    with open(os.path.join(base, "incidents.jsonl"), "w",
              encoding="utf-8") as fh:
        fh.write(json.dumps({"kind": "incident",
                             "payload": {"severity": "warning"}}) + "\n")
    with open(os.path.join(base, "PILOT_REPORT.json"), "w",
              encoding="utf-8") as fh:
        json.dump({"sections": {"run": {"mode": "developmental_simulated",
                                        "steps": 120}, "uptime_ratio": 0.98},
                   "claim_guard_safe": True}, fh)
    for day, sym, delta in (("day_001", 2, 0.0), ("day_030", 14, 0.2)):
        with open(os.path.join(base, "daily", f"{day}.json"), "w",
                  encoding="utf-8") as fh:
            json.dump({"proto_symbol_changes": sym,
                       "structural_change_delta": delta,
                       "safety_incidents": 0, "stagnation_hours": 1}, fh)
    for name, payload in (("developmental_state.json", {"epoch": "infancy"}),
                          ("proto_symbols.json", {"count": 14}),
                          ("hypotheses.json", {"count": 5})):
        with open(os.path.join(state, name), "w", encoding="utf-8") as fh:
            json.dump(payload, fh)


def main() -> None:
    parser = argparse.ArgumentParser(description="Post-pilot analysis demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_pilot1/test_post_pilot")
    args = parser.parse_args()

    base = os.path.join(args.state_dir, "pilot1")
    state = os.path.join(args.state_dir, "state")
    _write_mock_artifacts(base, state)

    out = PostPilotForensics(base_dir=base, state_dir=state).run()
    summary = out["summary"]
    print("=== Post-pilot analysis ===")
    print(f"artifact completeness : {summary['artifact_completeness']}")
    print(f"growth classification : {summary['growth_classification']}")
    print(f"structural evidence   : {summary['structural_evidence_count']}")
    print(f"traceability score    : {summary['traceability_score']}")
    print(f"regression severity   : {summary['regression_severity']}")
    print(f"phase-2 recommendation: {summary['phase2_recommendation']}")
    print(f"report                : {out['report_paths']['markdown']}")
    print(f"dossier               : {out['dossier_paths']['markdown']}")
    print("note                  : operational/analyzability findings only; "
          "no consciousness claim")


if __name__ == "__main__":
    main()
