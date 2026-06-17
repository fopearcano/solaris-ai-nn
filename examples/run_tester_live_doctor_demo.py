#!/usr/bin/env python3
"""Tester live doctor demo: missing-governance blocker, safe pass, forbidden blocker.

    python examples/run_tester_live_doctor_demo.py \\
        --state-dir .solaris_ai_nn_live/test_live_doctor \\
        --tester-state-dir .solaris_ai_nn_tester/live/test_live_doctor

Shows the live tester doctor blocking on missing/disabled governance, passing on an
approved-and-safe config, and blocking when a forbidden source is allowed.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.tester_live_readonly import (
    GovernanceTemplateBuilder,
    TesterFeederTemplateBuilder,
    TesterLiveDoctor,
)


def _write_governance(state_dir, data):
    os.makedirs(os.path.join(state_dir, "governance"), exist_ok=True)
    path = os.path.join(state_dir, "governance",
                        "LIVE_READONLY_GOVERNANCE.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--state-dir", default=".solaris_ai_nn_live/test_live_doctor")
    ap.add_argument("--tester-state-dir",
                    default=".solaris_ai_nn_tester/live/test_live_doctor")
    args = ap.parse_args()
    sd = args.state_dir
    os.makedirs(sd, exist_ok=True)
    TesterFeederTemplateBuilder().write_live_registry(sd, overwrite=True)

    print("tester live doctor demo")
    # 1. Missing governance -> blocked.
    doc = TesterLiveDoctor().check(state_dir=sd)
    print(f"  missing governance : {doc.overall_status} "
          f"(blockers {len(doc.blockers)})")

    # 2. Approved, safe governance -> pass.
    gov = GovernanceTemplateBuilder().build().to_dict()
    gov.update(live_readonly_enabled=True, operator_approved=True,
               approved_by="Tester", approved_at_utc="2026-06-17T00:00:00Z")
    _write_governance(sd, gov)
    doc = TesterLiveDoctor().check(state_dir=sd)
    print(f"  approved + safe    : {doc.overall_status} "
          f"(blockers {len(doc.blockers)})")

    # 3. Forbidden source allowed -> blocked/unsafe.
    bad = dict(gov)
    bad["allowed_sources"] = list(gov["allowed_sources"]) + ["raw_microphone"]
    _write_governance(sd, bad)
    doc = TesterLiveDoctor().check(state_dir=sd)
    forbidden = [f.check for f in doc.blockers
                 if f.check == "no_forbidden_source_allowed"]
    print(f"  forbidden allowed  : {doc.overall_status} "
          f"(triggered {forbidden})")
    print("note: missing/disabled governance and forbidden sources block the "
          "live test; Solaris controls nothing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
