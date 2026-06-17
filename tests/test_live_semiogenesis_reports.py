"""Live semiogenesis reports: all generated, safety boundaries, ClaimGuard-safe."""

from __future__ import annotations

import json
import os
import shutil

from solaris_ai_nn.live_birth import approved_governance, feeder_registry_template
from solaris_ai_nn.live_observation import PostBirthLiveObservationRuntime
from solaris_ai_nn.live_ontogenesis import FirstLiveOntogenesisRuntime
from solaris_ai_nn.live_semiogenesis import FirstLiveSemiogenesisRuntime

try:
    from solaris_ai_nn.governance.compliance import ClaimGuard
    _HAS_GUARD = True
except Exception:  # pragma: no cover
    _HAS_GUARD = False

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ONTO_FIXTURE = os.path.join(_ROOT, "examples", "live_ontogenesis",
                             "sample_stable_patterns.jsonl")


def _run(tmp_path):
    state = str(tmp_path)
    for sub in ("governance", "feeders", "inbox", "certificates"):
        os.makedirs(os.path.join(state, sub), exist_ok=True)
    json.dump(approved_governance(), open(os.path.join(
        state, "governance", "LIVE_READONLY_GOVERNANCE.json"), "w"))
    json.dump(feeder_registry_template(), open(os.path.join(
        state, "feeders", "FEEDER_REGISTRY.json"), "w"))
    open(os.path.join(state, "certificates", "c.md"), "w").write("# cert\n")
    shutil.copy(_ONTO_FIXTURE, os.path.join(state, "inbox", "ev.jsonl"))
    PostBirthLiveObservationRuntime(state_dir=state).run()
    FirstLiveOntogenesisRuntime(state_dir=state, allow_limited_birth=True).run()
    FirstLiveSemiogenesisRuntime(state_dir=state, allow_limited_birth=True).run()
    return state


def test_all_reports_generated(tmp_path):
    state = _run(tmp_path)
    base = os.path.join(state, "semiogenesis", "reports")
    for name in ("LIVE_SEMIOGENESIS_REPORT.md", "CONCEPT_INPUT_REPORT.md",
                 "SIGN_CANDIDATES.md", "SIGN_UTILITY_REPORT.md",
                 "PRIVATE_SYNTAX_REPORT.md", "SIGN_CONTAMINATION_REPORT.md",
                 "SIGN_BIRTH_GATE_REPORT.md", "LIVE_SIGN_MEMORY_REPORT.md"):
        assert os.path.isfile(os.path.join(base, name)), name


def test_safety_boundaries_in_report(tmp_path):
    state = _run(tmp_path)
    md = open(os.path.join(state, "semiogenesis", "reports",
                           "LIVE_SEMIOGENESIS_REPORT.md")).read().lower()
    assert "no full cognition was enabled by default" in md
    assert "private signs are not proof of language or understanding" in md
    assert "no consciousness/life/agency claim is made" in md


def test_reports_are_claimguard_safe(tmp_path):
    if not _HAS_GUARD:
        return
    state = _run(tmp_path)
    base = os.path.join(state, "semiogenesis")
    for root, _, files in os.walk(base):
        for f in files:
            if f.endswith(".md"):
                txt = open(os.path.join(root, f)).read()
                assert ClaimGuard().scan_text(txt).safe, f
