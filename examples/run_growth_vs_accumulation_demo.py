#!/usr/bin/env python3
"""Growth-vs-accumulation demo: accumulation vs real growth, conservatively.

    python examples/run_growth_vs_accumulation_demo.py --state-dir .solaris_ai_nn_development/test_growth_vs_accumulation

Contrasts two runs: one where module statuses are flat (mere accumulation) and one
where prediction/action/concept/sign/contamination-resistance improve durably (real
structural growth). The analyzer is conservative; inconclusive is valid.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.developmental_life import LongHorizonDevelopmentalRuntime


def _growth_run(state_dir):
    ont = {"proto_concept_count": 10, "stable_concept_count": 6}
    sem = {"internal_sign_count": 8, "stable_sign_count": 4,
           "contaminated_sign_ratio": 0.05, "gloss_dependence_score": 0.05}
    cog = {"prediction_success_rate": 0.6, "failed_prediction_count": 2}
    ar = {"learned_effect_count": 4, "constructive_reaction_ratio": 0.7}
    sb = {"boundary_confidence_score": 0.8, "live_grounded": True,
          "source_attribution_uncertainty_score": 0.2}
    dev = LongHorizonDevelopmentalRuntime(
        state_dir=os.path.join(state_dir, "growth"),
        modules={"perceptual_ontogenesis": ont, "semiogenesis": sem,
                 "sensorium_cognition": cog, "action_reaction": ar,
                 "self_boundary": sb,
                 "perceptual_metabolism": {"source_diet_diversity": 0.6}},
        max_ticks=6)
    dev.run_bounded()
    return dev.developmental_status()


def _accumulation_run(state_dir):
    modules = {"perceptual_ontogenesis": {"proto_concept_count": 2,
                                          "stable_concept_count": 0},
               "sensorium_cognition": {"prediction_success_rate": 0.0},
               "perceptual_metabolism": {"source_diet_diversity": 0.1}}
    dev = LongHorizonDevelopmentalRuntime(
        state_dir=os.path.join(state_dir, "accumulation"), modules=modules,
        max_ticks=6)
    dev.run_bounded()
    return dev.developmental_status()


def main():
    parser = argparse.ArgumentParser(description="Growth vs accumulation demo")
    parser.add_argument(
        "--state-dir", type=str,
        default=".solaris_ai_nn_development/test_growth_vs_accumulation")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    growth = _growth_run(args.state_dir)
    accumulation = _accumulation_run(args.state_dir)

    print("=== Growth vs accumulation demo ===")
    print(f"growth run verdict       : {growth['structural_growth_status']} "
          f"(score {growth['structural_growth_score']})")
    print(f"accumulation run verdict : "
          f"{accumulation['structural_growth_status']} "
          f"(score {accumulation['structural_growth_score']})")
    print(f"accumulation warnings    : "
          f"{accumulation['accumulation_warning_count']}")
    print("note: growth vs accumulation is judged conservatively; a negative or "
          "inconclusive result is valid, and growth is never over-claimed.")


if __name__ == "__main__":
    main()
