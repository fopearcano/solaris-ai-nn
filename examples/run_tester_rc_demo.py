#!/usr/bin/env python3
"""Tester RC demo: full local release-candidate assembly (ready vs blocked).

    python examples/run_tester_rc_demo.py \\
        --tester-state-dir .solaris_ai_nn_tester/test_rc_demo

Runs the full RC assembly twice: once against a fresh (under-prepared) tester state that
blocks on missing packaging/safety-freeze artifacts, and once against a temporary state
seeded with packaging and safety-freeze manifests so the RC reaches a ready-with-warnings
verdict. It is a local assembly step only; it publishes/uploads nothing.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.tester_release_candidate import TesterRCRuntime


def _seed_ready_state(base: str) -> None:
    """Write minimal packaging + safety-freeze manifests so the RC is ready."""
    pkg = os.path.join(base, "packaging", "reports")
    os.makedirs(pkg, exist_ok=True)
    with open(os.path.join(pkg, "PACKAGING_REPORT.json"), "w",
              encoding="utf-8") as fh:
        json.dump({"sections": {"packaging_status": {
            "readiness": "ready_with_warnings", "doctor_status": "pass",
            "clean_machine_status": "pass_with_warnings",
            "blocker_count": 0}}}, fh)
    sf = os.path.join(base, "safety_freeze", "manifests")
    os.makedirs(sf, exist_ok=True)
    with open(os.path.join(sf, "TESTER_SAFETY_FREEZE_MANIFEST.json"), "w",
              encoding="utf-8") as fh:
        json.dump({"readiness": "ready_with_warnings",
                   "release_blocker_count": 0, "critical_open_count": 0,
                   "forbidden_claim_count": 0,
                   "capability_blocker_count": 0}, fh)
    # Minimal install guide + feedback form so required artifacts resolve.
    ig = os.path.join(base, "packaging", "install_guides")
    os.makedirs(ig, exist_ok=True)
    for name in ("TESTER_INSTALL_GUIDE.md", "TESTER_QUICKSTART.md"):
        with open(os.path.join(ig, name), "w", encoding="utf-8") as fh:
            fh.write("# local editable install\n\npip install -e .\n")
    for name in ("PACKAGING_REPORT.md", "ENVIRONMENT_DOCTOR_REPORT.md",
                 "COMMAND_REGISTRY_REPORT.md",
                 "CLEAN_MACHINE_READINESS_REPORT.md"):
        with open(os.path.join(pkg, name), "w", encoding="utf-8") as fh:
            fh.write(f"# {name}\n\nlocal report-only.\n")
    sfr = os.path.join(base, "safety_freeze", "reports")
    os.makedirs(sfr, exist_ok=True)
    for name in ("TESTER_SAFETY_FREEZE_REPORT.md", "TESTER_RELEASE_BLOCKERS.md"):
        with open(os.path.join(sfr, name), "w", encoding="utf-8") as fh:
            fh.write(f"# {name}\n\nlocal report/gate-only.\n")
    ff = os.path.join(base, "feedback", "forms")
    os.makedirs(ff, exist_ok=True)
    with open(os.path.join(ff, "TESTER_FEEDBACK_FORM.md"), "w",
              encoding="utf-8") as fh:
        fh.write("# tester feedback form\n\nlocal QA evidence; not training.\n")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tester-state-dir",
                    default=".solaris_ai_nn_tester/test_rc_demo")
    args = ap.parse_args()

    print("tester rc demo")
    blocked = TesterRCRuntime(tester_state_dir=args.tester_state_dir,
                              max_runtime_s=60.0)
    blocked.run()
    bst = blocked.rc_status()
    print(f"  blocked case: readiness={bst['readiness']} "
          f"blockers={bst['blocker_count']} "
          f"missing_required={bst['missing_required_artifact_count']}")

    ready_base = tempfile.mkdtemp()
    _seed_ready_state(ready_base)
    ready = TesterRCRuntime(tester_state_dir=ready_base, max_runtime_s=60.0)
    ready.run()
    rst = ready.rc_status()
    print(f"  ready case  : readiness={rst['readiness']} "
          f"blockers={rst['blocker_count']} bundle={bool(rst['latest_rc_bundle_path'])}")
    print("note: local assembly only; no public release, no upload, no GitHub "
          "release/tag/issue, no consciousness/life/agency claim.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
