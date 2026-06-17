#!/usr/bin/env python3
"""Tester reproducibility demo: pass, pass-with-warnings, and a required-miss fail.

    python examples/run_tester_reproducibility_demo.py --state-dir .solaris_ai_nn_tester/repro

Runs a real known-good fixture demo (pass), then demonstrates a pass-with-warnings case
(a missing optional module) and a fail case (a missing required artifact) using the
reproducibility checker with synthetic contexts. Reproducibility ignores timestamps and
run ids and fails on missing required artifacts or unsupported claims.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.tester_fixture_spine import (
    TesterFixtureDemoRuntime,
    TesterReproducibilityCheck,
    default_expected_outputs,
)


def _base_context(ok=True):
    return {
        "fixture_present": True, "unsafe_quarantined": True,
        "secret_present": False, "membrane_present": True,
        "membrane_impression_count": 16,
        "all_impressions_have_receptor": True,
        "all_impressions_have_source_ref": True,
        "operator_pulse_attenuated": True, "debug_gloss_not_truth": True,
        "human_label_not_truth": True, "source_pressure_present": True,
        "membrane_memory_present": True,
        "observation_distinguishes_diets": True,
        "ontogenesis_ran": True, "ontogenesis_used_impressions": True,
        "semiogenesis_ran": True, "semiogenesis_ancestry_preserved": True,
        "cognition_ran": True, "cognition_ancestry_preserved": True,
        "reports_have_disclaimers": True, "claims_safe": True,
        "raw_bypass_detected": False, "no_external_access": True,
        "fixture_quarantined_count": 1, "blocked": False,
        "fixture_hash": "deadbeef",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--state-dir", default=".solaris_ai_nn_tester/repro")
    args = ap.parse_args()

    rt = TesterFixtureDemoRuntime(state_dir=args.state_dir,
                                  profile="fixture_tester_v0")
    rt.run()
    print("tester reproducibility demo")
    print(f"  real fixture run    : {rt.reproducibility['reproducibility_status']}")

    spec = default_expected_outputs()
    check = TesterReproducibilityCheck()
    gm = rt.golden_manifest
    fixture_hash = rt.context.get("fixture_hash", "")
    # Present artifacts consistent with the golden baseline (all present).
    all_present = {a.artifact_type: True for a in gm.artifacts}

    warn_ctx = _base_context()
    warn_ctx["fixture_hash"] = fixture_hash
    warn_ctx["present_artifacts"] = dict(all_present)
    warn_ctx["present_artifacts"]["ontogenesis_candidate_summary"] = False
    warn = check.check(context=warn_ctx, expected_spec=spec,
                       golden_manifest=gm, expected_fixture_hash=fixture_hash)
    print(f"  missing optional    : {warn.status}")

    fail_ctx = _base_context()
    fail_ctx["fixture_hash"] = fixture_hash
    fail_ctx["present_artifacts"] = dict(all_present)
    fail_ctx["present_artifacts"]["membrane_report"] = False
    fail_ctx["membrane_impression_count"] = 0
    fail_ctx["membrane_present"] = False
    fail = check.check(context=fail_ctx, expected_spec=spec,
                       golden_manifest=gm, expected_fixture_hash=fixture_hash)
    print(f"  missing required    : {fail.status}")
    print("note: reproducibility ignores timestamps/run ids; it fails on missing "
          "required artifacts, safety violations, or unsupported claims.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
