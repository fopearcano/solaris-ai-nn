#!/usr/bin/env python3
"""Delayed-consequence hypothesis demo: cause now, effect later.

    python examples/run_delayed_consequence_hypothesis_demo.py

A delayed-feedback nursery produces consequence groups linked only by a
group id. The engine forms a delayed-consequence hypothesis candidate and
tests it in the nursery; the result is either a nursery-simulated update or
an honest inconclusive verdict. No correct-answer label is supplied.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.ecology.nursery import DevelopmentalNursery, NurseryConfig
from solaris_ai_nn.ecology.regimes import RegimeType
from solaris_ai_nn.hypothesis import HypothesisEngine, HypothesisReportBuilder


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Delayed-consequence hypothesis demo")
    parser.add_argument("--steps", type=int, default=160)
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/hypothesis_delayed")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    nursery = DevelopmentalNursery(config=NurseryConfig(
        nursery_id="delayed-hyp-nursery", seed=args.seed,
        duration_steps=args.steps, delayed_consequence_rate=0.3,
        active_regimes=[RegimeType.DELAYED_FEEDBACK_WORLD],
        output_state_dir=args.state_dir))
    for step in range(args.steps):
        nursery.stimulus_provider(step)
    engine = HypothesisEngine(state_dir=args.state_dir, nursery=nursery)

    summary_eco = nursery.summary()
    ctx = {
        "step": args.steps, "mysterium_pressure": 0.4,
        "ecology": {
            "delayed_consequence_group_count":
                summary_eco["delayed_consequence_group_count"],
            "delayed_groups": [r["group_id"] for r in
                               nursery.ecology.delayed.groups[:3]]},
        "health_level": "ok",
    }
    out = engine.tick(ctx)
    summary = engine.summary()
    families = engine.memory.family_counts()

    print("=" * 70)
    print("Solaris-AI-NN -- delayed-consequence hypothesis (cause now, "
          "effect later)")
    print("=" * 70)
    print(f"delayed groups in nursery: "
          f"{summary_eco['delayed_consequence_group_count']}")
    print(f"hypotheses generated:      {out['new_hypotheses']}")
    print(f"delayed-consequence family: "
          f"{families.get('delayed_consequence_hypothesis', 0)}")
    print(f"tests run:                 {summary['tests_run']}")
    print(f"last evidence result:      {summary['last_evidence_result']}")
    print()

    builder = HypothesisReportBuilder(engine)
    paths = builder.save(Path(args.state_dir) / "report.json",
                         Path(args.state_dir) / "report.md")
    print(f"report: {paths['markdown']} (claim guard safe: "
          f"{paths['claim_guard']['safe']})")
    print()
    print("note: cause and effect share only a group id, never a label. The "
          "hypothesis is a candidate association; a supported result is a "
          "nursery-simulated finding, not a proven cause.")


if __name__ == "__main__":
    main()
