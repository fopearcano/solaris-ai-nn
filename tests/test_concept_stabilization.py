"""ConceptStabilizationEngine: criteria applied; fixture-only marked; provisional."""

from __future__ import annotations

from solaris_ai_nn.perceptual_ontogenesis import (
    ConceptStabilizationEngine,
    ProtoConcept,
    ProtoConceptKind,
    ProtoConceptStatus,
)


def test_stability_criteria_applied():
    c = ProtoConcept(
        kind=ProtoConceptKind.MODALITY_NATIVE,
        modality_distribution={"radio_frequency": 5, "alien_echo": 3},
        source_distribution={"rf_feed": 5, "echo_feed": 3},
        recurrence_count=5, stability_score=0.6, prediction_utility=0.7,
        compression_utility=0.7, attention_utility=0.6)
    res = ConceptStabilizationEngine().stabilize(c)
    assert res.status == ProtoConceptStatus.STABLE
    assert any(e.criterion == "recurrence_across_time" and e.met
               for e in res.evidence)


def test_fixture_only_stability_marked():
    c = ProtoConcept(
        kind=ProtoConceptKind.MODALITY_NATIVE,
        modality_distribution={"radio_frequency": 5, "alien_echo": 3},
        source_distribution={"rf_feed": 5, "echo_feed": 3},
        recurrence_count=5, stability_score=0.6, prediction_utility=0.7,
        compression_utility=0.7, attention_utility=0.6, live_grounded=False)
    res = ConceptStabilizationEngine().stabilize(c)
    assert res.fixture_only is True
    assert any("fixture" in lim for lim in c.limitations)


def test_stable_does_not_mean_true():
    c = ProtoConcept(kind=ProtoConceptKind.MODALITY_NATIVE,
                     modality_distribution={"radio_frequency": 5},
                     recurrence_count=5)
    res = ConceptStabilizationEngine().stabilize(c)
    note = res.to_dict()["note"]
    assert "stable does not mean true" in note


def test_weak_concept_not_stable():
    c = ProtoConcept(kind=ProtoConceptKind.UNKNOWN,
                     modality_distribution={"radio_frequency": 1},
                     recurrence_count=1)
    res = ConceptStabilizationEngine().stabilize(c)
    assert res.status != ProtoConceptStatus.STABLE
