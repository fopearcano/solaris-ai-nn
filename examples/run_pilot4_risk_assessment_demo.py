#!/usr/bin/env python3
"""Pilot-4 risk assessment demo: external categories are prohibited.

    python examples/run_pilot4_risk_assessment_demo.py --state-dir .solaris_ai_nn_pilot4/test_risk

Shows the forbidden actuator categories and the external-actuation risk model.
Every external actuator category is classified prohibited; no recommendation
ever enables actuation. Pilot-4 classifies what would be required later; it does
not open any door.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.pilot4_planning import (
    ActuatorCategory,
    ActuatorTaxonomy,
    ForbiddenActuatorRegistry,
    RiskModel,
    RiskRecommendation,
)


def main():
    parser = argparse.ArgumentParser(
        description="Pilot-4 risk assessment demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_pilot4/test_risk")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    taxonomy = ActuatorTaxonomy()
    forbidden = ForbiddenActuatorRegistry()
    rm = RiskModel()

    external = sorted(ActuatorCategory.EXTERNAL)
    assessments = {cat: rm.default_assessment(cat).to_dict()
                   for cat in external}
    out = {
        "forbidden_actuator_categories": forbidden.categories(),
        "prohibited_actuator_categories": taxonomy.prohibited_categories(),
        "risk_dimensions": rm.dimensions(),
        "assessments": assessments,
    }
    path = os.path.join(args.state_dir, "risk_assessment.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, default=str)

    print("=== Pilot-4 risk assessment demo ===")
    print(f"forbidden actuators : {len(forbidden.names())}")
    print(f"risk dimensions     : {len(rm.dimensions())}")
    for cat in external:
        rec = assessments[cat]["recommendation"]
        print(f"  {cat:<24} -> {rec}")
    all_prohibited = all(a["recommendation"] == RiskRecommendation.PROHIBITED
                         for a in assessments.values())
    print(f"all external prohibited : {all_prohibited}")
    print(f"no 'enable' recommendation : "
          f"{all('enable' not in r for r in RiskRecommendation.ALL)}")
    print(f"written : {path}")
    print("note    : Pilot-4 cannot recommend enabling real actuation; it "
          "classifies what would be required later.")


if __name__ == "__main__":
    main()
