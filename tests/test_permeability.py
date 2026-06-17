"""Membrane permeability: allow, attenuate, block, quarantine, absence impression."""

from __future__ import annotations

from solaris_ai_nn.environmental_membrane import (
    EnvironmentalReceptorField,
    MembraneContaminationAnalyzer,
    MembranePermeabilityGate,
)


def _ev(sid, modality="scalar", absence=False, noisy=False, command=False,
        secret=False):
    return {"event_id": "e", "source_id": sid, "modality": modality,
            "channel": "c", "payload": {"v": 1}, "is_command": command,
            "human_label_is_ground_truth": False,
            "quality": {"is_absence": absence, "is_noisy": noisy},
            "safety": {"private_data": False, "contains_instruction": command,
                       "contains_secret": secret, "allow_learning": False},
            "debug_gloss": "x", "debug_gloss_is_ground_truth": False}


def _decide(ev, source_pressure=None, load_status=""):
    field = EnvironmentalReceptorField()
    m = field.match(ev)
    receptor = field.receptor(m.receptor_id)
    contamination = MembraneContaminationAnalyzer().evaluate(
        ev, source_pressure=source_pressure or {})
    return MembranePermeabilityGate().decide(
        event=ev, receptor=receptor, contamination=contamination,
        source_pressure=source_pressure or {}, governance_passed=True,
        feeder_registry_present=True, validated=True, load_status=load_status)


def test_safe_event_allowed():
    d = _decide(_ev("machine_body"))
    assert d.status == "allow"
    assert d.allowed is True


def test_operator_dominance_attenuated():
    d = _decide(_ev("operator_pulse", "pulse"),
                source_pressure={"membrane_operator_dominance_score": 0.6})
    assert d.status == "allow_attenuated"
    assert d.attenuation < 1.0


def test_forbidden_source_blocked():
    d = _decide(_ev("raw_microphone", "audio"))
    assert d.status == "block"


def test_secret_quarantined():
    d = _decide(_ev("machine_body", secret=True))
    assert d.status == "quarantine"


def test_command_quarantined():
    d = _decide(_ev("operator_pulse", "pulse", command=True))
    assert d.status == "quarantine"


def test_absence_creates_absence_impression():
    d = _decide(_ev("chronos_absence", "chronos", absence=True))
    assert d.creates_absence is True
    assert d.allowed is True


def test_every_decision_explained():
    d = _decide(_ev("machine_body"))
    assert d.reasons  # the gate explains every decision
