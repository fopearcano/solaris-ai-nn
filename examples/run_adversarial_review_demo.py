#!/usr/bin/env python3
"""Adversarial review demo: fixture overfit, passive parser, missing replication.

    python examples/run_adversarial_review_demo.py --state-dir .solaris_ai_nn_review/test_adversarial

Generates adversarial alternative explanations for an evidence bundle with fixture
overfit risk, passive-parser equivalence, and no replication. Those alternatives
are flagged as strong (they downgrade review readiness); every alternative lists
the evidence needed to reduce its uncertainty and is preserved, never dismissed.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.independent_review import AdversarialReviewEngine


def main():
    parser = argparse.ArgumentParser(description="Adversarial review demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_review/test_adversarial")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    bundle = {
        "sensorium_differentiation": {"fixture_overfit_risk": True,
                                      "passive_parser_equivalent": True},
        # no "replication" -> missing-replication alternative is strong
        "counterevidence": {"records": [
            {"counter_type": "fixture_overfit", "detail": "maybe overfit"}]},
    }
    finding = AdversarialReviewEngine().review(bundle).to_dict()

    print("=== Adversarial review demo ===")
    print(f"  alternatives : {finding['alternative_explanation_count']} "
          f"(strong {finding['strong_alternative_count']})")
    for e in finding["explanations"]:
        flag = " (STRONG)" if e["strong"] else ""
        print(f"    - {e['explanation_type']}{flag}: {e['text']}")
        print(f"        evidence needed: {e['evidence_needed']} "
              f"(auto_dismissed={e['auto_dismissed']})")
    print("note         : alternative explanations are preserved and never "
          "auto-dismissed. A strong alternative (fixture overfit, passive "
          "parser, missing replication) downgrades review readiness until the "
          "listed evidence is collected.")


if __name__ == "__main__":
    main()
