"""WorldFormationBuilder: state built; no subjective/qualia claim; contamination."""

from __future__ import annotations

from solaris_ai_nn.perceptual_ontogenesis import (
    ProtoConcept,
    ProtoConceptKind,
    ProtoConceptStatus,
    WorldFormationBuilder,
)


def _concepts():
    a = ProtoConcept(kind=ProtoConceptKind.MODALITY_NATIVE,
                     modality_distribution={"radio_frequency": 3},
                     status=ProtoConceptStatus.STABLE, prediction_utility=0.6,
                     compression_utility=0.6)
    b = ProtoConcept(kind=ProtoConceptKind.CROSS_MODAL,
                     modality_distribution={"radio_frequency": 1,
                                            "vibration": 1},
                     status=ProtoConceptStatus.EMERGING)
    c = ProtoConcept(kind=ProtoConceptKind.ABSENCE_BASED,
                     modality_distribution={"radio_frequency": 1},
                     status=ProtoConceptStatus.STABLE)
    return [a, b, c]


def test_world_formation_state_built():
    world = WorldFormationBuilder().build(
        _concepts(), family_distribution={"rf_family": 3},
        relation_density=0.5)
    state = world.state.to_dict()
    assert state["active_concept_count"] == 3
    assert state["stable_concept_count"] == 2
    assert state["cross_modal_integration"] > 0.0
    assert state["absence_integration"] > 0.0
    assert world.formation_density >= 0.0


def test_no_subjective_or_qualia_claim():
    world = WorldFormationBuilder().build(
        _concepts(), family_distribution={}, relation_density=0.0)
    note = world.state.to_dict()["note"].lower()
    assert "not a subjective world" in note
    assert "not qualia" in note
    assert "not proof of experience" in note


def test_contamination_visible():
    contaminated = ProtoConcept(
        kind=ProtoConceptKind.HUMAN_LABEL_CONTAMINATED,
        modality_distribution={"human_textual": 3},
        human_label_contamination_score=0.9)
    world = WorldFormationBuilder().build(
        [contaminated], family_distribution={}, relation_density=0.0)
    assert world.state.human_label_contamination > 0.0
