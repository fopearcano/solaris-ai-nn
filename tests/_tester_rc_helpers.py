"""Shared helpers for tester release-candidate tests (not a test module)."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.tester_release_candidate import TesterRCRuntime


def seed_ready_state(base: str) -> None:
    """Write minimal packaging + safety-freeze artifacts so the RC is ready."""
    pkg = os.path.join(base, "packaging", "reports")
    os.makedirs(pkg, exist_ok=True)
    with open(os.path.join(pkg, "PACKAGING_REPORT.json"), "w",
              encoding="utf-8") as fh:
        json.dump({"sections": {"packaging_status": {
            "readiness": "ready_with_warnings", "doctor_status": "pass",
            "clean_machine_status": "pass_with_warnings",
            "blocker_count": 0}}}, fh)
    for n in ("PACKAGING_REPORT.md", "ENVIRONMENT_DOCTOR_REPORT.md",
              "COMMAND_REGISTRY_REPORT.md", "CLEAN_MACHINE_READINESS_REPORT.md"):
        with open(os.path.join(pkg, n), "w", encoding="utf-8") as fh:
            fh.write(f"# {n}\nlocal report-only.\n")
    ig = os.path.join(base, "packaging", "install_guides")
    os.makedirs(ig, exist_ok=True)
    for n in ("TESTER_INSTALL_GUIDE.md", "TESTER_QUICKSTART.md"):
        with open(os.path.join(ig, n), "w", encoding="utf-8") as fh:
            fh.write("pip install -e .\n")
    sf = os.path.join(base, "safety_freeze", "manifests")
    os.makedirs(sf, exist_ok=True)
    with open(os.path.join(sf, "TESTER_SAFETY_FREEZE_MANIFEST.json"), "w",
              encoding="utf-8") as fh:
        json.dump({"readiness": "ready_with_warnings",
                   "release_blocker_count": 0, "critical_open_count": 0,
                   "forbidden_claim_count": 0,
                   "capability_blocker_count": 0}, fh)
    sfr = os.path.join(base, "safety_freeze", "reports")
    os.makedirs(sfr, exist_ok=True)
    for n in ("TESTER_SAFETY_FREEZE_REPORT.md", "TESTER_RELEASE_BLOCKERS.md"):
        with open(os.path.join(sfr, n), "w", encoding="utf-8") as fh:
            fh.write("local report/gate-only.\n")
    ff = os.path.join(base, "feedback", "forms")
    os.makedirs(ff, exist_ok=True)
    with open(os.path.join(ff, "TESTER_FEEDBACK_FORM.md"), "w",
              encoding="utf-8") as fh:
        fh.write("local QA evidence; not training.\n")
    console = os.path.join(base, "console")
    os.makedirs(console, exist_ok=True)
    with open(os.path.join(console, "INDEX.md"), "w", encoding="utf-8") as fh:
        fh.write("# tester console (read-only)\n")


def run_rc(base: str, **kwargs) -> TesterRCRuntime:
    rt = TesterRCRuntime(tester_state_dir=base, max_runtime_s=60.0, **kwargs)
    rt.run()
    return rt
