"""Sensory <-> Ecology: nursery and membrane source boundaries preserved."""

from __future__ import annotations

from solaris_ai_nn.ego.ownership import OwnershipAttributor
from solaris_ai_nn.sensory_membrane import (
    RawSensoryEvent,
    SensoryEventNormalizer,
)


def test_nursery_and_membrane_boundaries_distinct():
    attr = OwnershipAttributor()
    nursery = attr.attribute_event({"source": "developmental_nursery"})
    membrane = attr.attribute_event(
        {"origin": "read_only_environmental_input"})
    assert nursery.category == "generated_by_developmental_nursery"
    assert membrane.category == "read_only_environmental_input"
    assert nursery.category != membrane.category


def test_membrane_event_origin_is_environmental():
    raw = RawSensoryEvent(source_id="s", source_type="jsonl_file",
                          payload={"x": 1})
    stim = SensoryEventNormalizer().normalize(raw).to_stimulus_dict()
    # Environmental input, never tagged as nursery-generated.
    assert stim["origin"] == "read_only_environmental_input"
    assert "nursery" not in stim["origin"]


def test_mixed_mode_preserves_source_boundary():
    attr = OwnershipAttributor()
    cats = {attr.attribute_event({"source": s}).category
            for s in ("developmental_nursery", "sensory_membrane")}
    # Two distinct categories: the boundary is preserved in mixed mode.
    assert len(cats) == 2
