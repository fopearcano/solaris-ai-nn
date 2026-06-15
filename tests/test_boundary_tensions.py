"""BoundaryTensionDetector: internal/external + sim/observation; unknown kept."""

from __future__ import annotations

from solaris_ai_nn.self_boundary import (
    BoundaryMarker,
    BoundaryTensionType,
    InternalExternalClassifier,
    OrganismicContinuity,
    OwnershipAttributor,
    SimulationBoundaryValidator,
    SourceAttributionEngine,
)
from solaris_ai_nn.self_boundary.boundary_tensions import BoundaryTensionDetector


def _detect(ownership, classifier, simulation, continuity, source):
    return BoundaryTensionDetector().detect(
        ownership=ownership, classifier=classifier, simulation=simulation,
        continuity=continuity, source_attribution=source)


def test_internal_external_tension_detected():
    clf = InternalExternalClassifier()
    clf.classify("r1", "plural_sensorium")  # mixed
    tensions = _detect(OwnershipAttributor(), clf,
                       SimulationBoundaryValidator(), OrganismicContinuity(),
                       SourceAttributionEngine())
    types = {t.tension_type for t in tensions}
    assert BoundaryTensionType.INTERNAL_VS_EXTERNAL in types


def test_simulation_observation_tension_detected():
    sim = SimulationBoundaryValidator()
    sim.mark("s1", BoundaryMarker.SIMULATION)
    tensions = _detect(OwnershipAttributor(), InternalExternalClassifier(),
                       sim, OrganismicContinuity(), SourceAttributionEngine())
    types = {t.tension_type for t in tensions}
    assert BoundaryTensionType.SIMULATION_VS_OBSERVATION in types


def test_unknown_origin_preserved():
    own = OwnershipAttributor()
    own.attribute("totally_unknown", "blob")  # ambiguous/unknown
    tensions = _detect(own, InternalExternalClassifier(),
                       SimulationBoundaryValidator(), OrganismicContinuity(),
                       SourceAttributionEngine())
    types = {t.tension_type for t in tensions}
    assert BoundaryTensionType.UNKNOWN_ORIGIN in types


def test_unrecovered_break_tension():
    cont = OrganismicContinuity()
    cont.record_break("source_silence")
    tensions = _detect(OwnershipAttributor(), InternalExternalClassifier(),
                       SimulationBoundaryValidator(), cont,
                       SourceAttributionEngine())
    types = {t.tension_type for t in tensions}
    assert BoundaryTensionType.SELF_CONTINUITY_VS_RESTART_GAP in types
