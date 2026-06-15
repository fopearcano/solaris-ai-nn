"""Self-boundary OwnershipAttributor: external/receptor/sim; ambiguous kept."""

from __future__ import annotations

from solaris_ai_nn.self_boundary import (
    BoundaryZone,
    OwnershipAttributor,
    OwnershipType,
)


def test_external_event_attributed_external():
    att = OwnershipAttributor().attribute("external_feeder", "rf_event")
    assert att.ownership_type == OwnershipType.EXTERNAL_FEEDER_ARTIFACT
    assert att.is_self is False
    assert att.zone == BoundaryZone.EXTERNAL_FEEDER


def test_receptor_state_attributed_body_schema():
    att = OwnershipAttributor().attribute("receptor_state", "recv_1")
    assert att.ownership_type == OwnershipType.SELF_RECEPTOR_STATE
    assert att.is_self is True
    assert att.zone == BoundaryZone.RECEPTOR_BODY


def test_simulation_attributed_simulation():
    att = OwnershipAttributor().attribute("internal_simulation", "sim_1")
    assert att.ownership_type == OwnershipType.INTERNAL_SIMULATION
    assert att.zone == BoundaryZone.SIMULATION
    assert att.is_self is False


def test_ambiguous_preserved():
    attributor = OwnershipAttributor()
    attributor.attribute("ambiguous", "blob")
    attributor.attribute("totally_unknown_kind", "blob2")
    ambiguous = attributor.ambiguous()
    assert len(ambiguous) == 2
    assert all(a.is_ambiguous for a in ambiguous)


def test_processed_sensory_input_not_self():
    att = OwnershipAttributor().attribute("external_source", "world_src")
    assert att.is_self is False
    assert "processed sensory input is not 'self'" in att.to_dict()["note"]
