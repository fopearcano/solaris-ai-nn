"""Membrane reports: all generated, safety boundaries, blocked visible, ClaimGuard."""

from __future__ import annotations

import json
import os
import shutil

from solaris_ai_nn.live_birth import approved_governance, feeder_registry_template
from solaris_ai_nn.environmental_membrane import EnvironmentalMembraneRuntime

try:
    from solaris_ai_nn.governance.compliance import ClaimGuard
    _HAS_GUARD = True
except Exception:  # pragma: no cover
    _HAS_GUARD = False

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_FIXTURES = os.path.join(_ROOT, "examples", "environmental_membrane")


def _run(tmp_path):
    state = str(tmp_path)
    for sub in ("governance", "feeders", "inbox"):
        os.makedirs(os.path.join(state, sub), exist_ok=True)
    json.dump(approved_governance(), open(os.path.join(
        state, "governance", "LIVE_READONLY_GOVERNANCE.json"), "w"))
    json.dump(feeder_registry_template(), open(os.path.join(
        state, "feeders", "FEEDER_REGISTRY.json"), "w"))
    for fx in ("sample_validated_events.jsonl",
               "sample_contaminated_events.jsonl"):
        shutil.copy(os.path.join(_FIXTURES, fx),
                    os.path.join(state, "inbox", fx))
    EnvironmentalMembraneRuntime(state_dir=state, require_governance=True).run()
    return state


def test_all_reports_generated(tmp_path):
    state = _run(tmp_path)
    base = os.path.join(state, "membrane", "reports")
    for name in ("ENVIRONMENTAL_MEMBRANE_REPORT.md", "RECEPTOR_FIELD_REPORT.md",
                 "PERMEABILITY_REPORT.md", "SENSORY_IMPRESSION_REPORT.md",
                 "SOURCE_PRESSURE_REPORT.md", "SALIENCE_REPORT.md",
                 "CONTAMINATION_REPORT.md", "IMMUNE_RESPONSE_REPORT.md",
                 "MEMBRANE_MEMORY_REPORT.md", "MEMBRANE_SAFETY_REPORT.md"):
        assert os.path.isfile(os.path.join(base, name)), name


def test_safety_boundaries_included(tmp_path):
    state = _run(tmp_path)
    md = open(os.path.join(state, "membrane", "reports",
                           "ENVIRONMENTAL_MEMBRANE_REPORT.md")).read().lower()
    assert "no feeder was started" in md
    assert "no consciousness/life/agency claim is made" in md
    assert "sensory impressions are operational boundary records" in md


def test_blocked_quarantined_visible(tmp_path):
    state = _run(tmp_path)
    md = open(os.path.join(state, "membrane", "reports",
                           "PERMEABILITY_REPORT.md")).read().lower()
    assert "blocked" in md and "quarantined" in md


def test_reports_are_claimguard_safe(tmp_path):
    if not _HAS_GUARD:
        return
    state = _run(tmp_path)
    base = os.path.join(state, "membrane")
    for root, _, files in os.walk(base):
        for f in files:
            if f.endswith(".md"):
                txt = open(os.path.join(root, f)).read()
                assert ClaimGuard().scan_text(txt).safe, f
