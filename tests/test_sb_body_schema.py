"""SensoriumBodySchema: receptor body part; feeder not a body part; tracked."""

from __future__ import annotations

from dataclasses import dataclass

from solaris_ai_nn.self_boundary import OwnershipType, SensoriumBodySchema
from solaris_ai_nn.self_boundary.ownership import OwnershipAttributor


@dataclass
class _Receptor:
    receptor_id: str = "recv_1"
    modality: str = "radio_frequency"
    source_id: str = "rf_feed"
    reliability: float = 0.9
    fatigue: float = 0.2
    saturation: float = 0.1
    sensitivity: float = 0.5
    silence_duration: float = 0.0
    last_event_time: float = 1.0
    adaptation_state: str = "normal"


def test_receptor_body_part_created():
    schema = SensoriumBodySchema()
    part = schema.update_from_receptor(_Receptor())
    assert part.receptor_id == "recv_1"
    assert part.modality == "radio_frequency"
    assert schema.part_count == 1


def test_feeder_not_a_body_part():
    schema = SensoriumBodySchema()
    schema.update_from_receptor(_Receptor())
    note = schema.to_dict()["note"]
    assert "feeders are external nerve-like signals" in note
    # A feeder is attributed as external artifact, never a self receptor body.
    att = OwnershipAttributor().attribute("external_feeder", "rf_feed")
    assert att.ownership_type == OwnershipType.EXTERNAL_FEEDER_ARTIFACT
    assert att.is_self is False


def test_reliability_and_fatigue_tracked():
    schema = SensoriumBodySchema()
    part = schema.update_from_receptor(_Receptor(reliability=0.4, fatigue=0.7))
    d = part.to_dict()
    assert d["reliability"] == 0.4
    assert d["fatigue"] == 0.7
    # Low reliability lowers boundary confidence (corruption risk).
    assert part.boundary_confidence < 0.8


def test_related_receptors_linked_by_modality():
    schema = SensoriumBodySchema()
    schema.update_from_receptor(_Receptor(receptor_id="a"))
    schema.update_from_receptor(_Receptor(receptor_id="b"))
    schema.link_related()
    assert "b" in schema.parts["a"].related_receptors
