"""Membrane immune response: allow/attenuate/quarantine; overload/deprivation; preserved."""

from __future__ import annotations

from solaris_ai_nn.environmental_membrane import (
    MembraneContaminationAnalyzer,
    MembraneImmuneResponse,
    MembranePermeabilityGate,
    PermeabilityDecision,
)
from solaris_ai_nn.environmental_membrane.permeability import PermeabilityStatus


def _contamination(types=()):
    from solaris_ai_nn.environmental_membrane.contamination import (
        MembraneContaminationAssessment, MembraneContaminationFinding)
    a = MembraneContaminationAssessment(event_id="e", source_id="s")
    for t in types:
        a.findings.append(MembraneContaminationFinding(t, "x", blocks=False))
    return a


def _decision(status, **kw):
    return PermeabilityDecision(event_id="e", source_id="s",
                                receptor_id="r", status=status, **kw)


def test_allow_response():
    rec = MembraneImmuneResponse().respond(
        decision=_decision(PermeabilityStatus.ALLOW),
        contamination=_contamination())
    assert "allow" in rec.actions


def test_attenuate_response():
    rec = MembraneImmuneResponse().respond(
        decision=_decision(PermeabilityStatus.ALLOW_ATTENUATED),
        contamination=_contamination())
    assert "attenuate" in rec.actions


def test_quarantine_response():
    rec = MembraneImmuneResponse().respond(
        decision=_decision(PermeabilityStatus.QUARANTINE),
        contamination=_contamination(["secret_marker"]))
    assert "quarantine" in rec.actions


def test_overload_deprivation_impression_response():
    over = MembraneImmuneResponse().respond(
        decision=_decision(PermeabilityStatus.ALLOW_ATTENUATED,
                           creates_overload=True),
        contamination=_contamination())
    assert "create_overload_impression" in over.actions
    dep = MembraneImmuneResponse().respond(
        decision=_decision(PermeabilityStatus.ALLOW, creates_deprivation=True),
        contamination=_contamination())
    assert "create_deprivation_impression" in dep.actions


def test_original_event_preserved():
    rec = MembraneImmuneResponse().respond(
        decision=_decision(PermeabilityStatus.QUARANTINE),
        contamination=_contamination())
    d = rec.to_dict()
    assert d["preserves_evidence"] is True
    assert d["deletes_events"] is False
    assert d["modifies_source"] is False
