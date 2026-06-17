"""Receptor field: receptors load, source matching, conservative unknown."""

from __future__ import annotations

from solaris_ai_nn.environmental_membrane import (
    EnvironmentalReceptorField,
    ReceptorKind,
)


def _ev(sid, modality="scalar", absence=False, noisy=False):
    return {"event_id": "e", "source_id": sid, "modality": modality,
            "channel": "c", "payload": {"v": 1},
            "quality": {"is_absence": absence, "is_noisy": noisy}}


def test_receptors_load():
    field = EnvironmentalReceptorField()
    ids = {r.receptor_id for r in field.receptors}
    for required in (ReceptorKind.CHRONOS, ReceptorKind.ABSENCE,
                     ReceptorKind.MACHINE_BODY, ReceptorKind.LOCAL_ENVIRONMENT,
                     ReceptorKind.WEATHER, ReceptorKind.PROJECT_FIELD,
                     ReceptorKind.OPERATOR_PULSE, ReceptorKind.NOISE,
                     ReceptorKind.OVERLOAD, ReceptorKind.DEPRIVATION,
                     ReceptorKind.UNKNOWN_SOURCE):
        assert required in ids
    assert field.index()["membrane_receptor_count"] == 11


def test_chronos_event_matches_chronos_receptor():
    m = EnvironmentalReceptorField().match(_ev("chronos_absence", "chronos"))
    assert m.receptor_id == ReceptorKind.CHRONOS
    assert m.evidence_refs == ["e"]


def test_machine_body_event_matches_machine_body_receptor():
    m = EnvironmentalReceptorField().match(_ev("machine_body"))
    assert m.receptor_id == ReceptorKind.MACHINE_BODY


def test_operator_pulse_receptor_attenuated_default():
    r = EnvironmentalReceptorField().receptor(ReceptorKind.OPERATOR_PULSE)
    assert r.baseline_permeability < 0.7
    machine = EnvironmentalReceptorField().receptor(ReceptorKind.MACHINE_BODY)
    assert r.baseline_permeability < machine.baseline_permeability


def test_unknown_source_conservative():
    m = EnvironmentalReceptorField().match(_ev("mystery_source"))
    assert m.receptor_id == ReceptorKind.UNKNOWN_SOURCE
    r = EnvironmentalReceptorField().receptor(ReceptorKind.UNKNOWN_SOURCE)
    assert r.conservative is True
    assert r.baseline_permeability <= 0.3


def test_absence_routes_to_absence_receptor():
    m = EnvironmentalReceptorField().match(
        _ev("chronos_absence", "chronos", absence=True))
    assert m.receptor_id == ReceptorKind.ABSENCE
    assert m.is_absence is True
