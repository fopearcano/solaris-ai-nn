#!/usr/bin/env python3
"""Tester regression demo: no regression, membrane-disappeared, unsupported-claim.

    python examples/run_tester_regression_demo.py --state-dir .solaris_ai_nn_tester/regression

Runs a real known-good fixture demo (no regression), then demonstrates two regressions
using the regression checker with synthetic contexts: the membrane path disappearing
and an unsupported claim appearing. Regression is structural and safety-focused.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.tester_fixture_spine import (
    GoldenManifestBuilder,
    TesterFixtureDemoRuntime,
    TesterRegressionCheck,
    default_expected_outputs,
)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--state-dir", default=".solaris_ai_nn_tester/regression")
    args = ap.parse_args()

    rt = TesterFixtureDemoRuntime(state_dir=args.state_dir,
                                  profile="fixture_tester_v0")
    rt.run()
    print("tester regression demo")
    print(f"  real fixture run     : {rt.regression['regression_status']}")

    spec = default_expected_outputs()
    gm = GoldenManifestBuilder().build(
        profile_id="fixture_tester_v0", fixture_hash="deadbeef",
        present_artifacts={a.artifact_type: True for a in spec.artifacts})
    check = TesterRegressionCheck()

    good = {"membrane_present": True, "membrane_impression_count": 16,
            "raw_bypass_detected": False, "reports_have_disclaimers": True,
            "claims_safe": True, "fixture_quarantined_count": 1,
            "present_artifacts": {a.artifact_type: True for a in spec.artifacts}}
    print(f"  no regression        : "
          f"{check.check(context=good, golden_manifest=gm)['regression_status']}")

    no_membrane = dict(good, membrane_present=False,
                       membrane_impression_count=0)
    print(f"  membrane disappeared : "
          f"{check.check(context=no_membrane, golden_manifest=gm)['regression_status']}")

    claim = dict(good, claims_safe=False)
    print(f"  unsupported claim    : "
          f"{check.check(context=claim, golden_manifest=gm)['regression_status']}")
    print("note: regression fails if the membrane path disappears, a raw bypass "
          "appears, or unsupported claims / missing safety disclaimers appear.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
