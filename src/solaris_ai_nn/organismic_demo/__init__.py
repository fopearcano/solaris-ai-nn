"""Minimal field organism demo -- the first observable organismic perception.

This package orchestrates the Prompt 41 plural sensorium into a bounded,
observable demo: Solaris is treated as a minimal evolving organism continuously
exposed to environmental flux through external-feeder-style streams. It generates
fixture feeders, reads them through the same read-only sensory adapter path,
updates stateful receptors, maintains a continuous sensory field, learns
baselines, detects absences / rhythms / invariants / cross-modal relations, adapts
attention, forms modality-grounded proto-symbol candidates, and then runs a
*changed-perception probe* asking whether the organism's future response actually
changed after exposure.

The demo orchestrates and evaluates; the plural sensorium remains the sensory
organ. It accesses no hardware, no network, and no shell; it never mutates a
source during perception; it keeps the cross-modal debug-truth file out of
perception; and it makes no claim of consciousness, sentience, life, personhood,
agency, or free will -- a positive result is evidence of changed internal
response structure, nothing more.
"""

from __future__ import annotations

from .comparison import (
    ComparisonArm,
    ComparisonResult,
    OrganismicDemoComparison,
)
from .demo_report import MinimalFieldOrganismDemoReportBuilder
from .field_runner import MinimalFieldOrganismRunner
from .fixture_feeders import FixtureFeederSet, write_fixtures
from .observation_trace import ObservationTrace, TraceEvent, TraceEventType
from .perception_change import (
    PerceptionChangeMetric,
    PerceptionChangeProbe,
    PerceptionChangeResult,
)
from .safety import OrganismicDemoSafetyValidator
from .scenario import (
    OrganismicDemoConfig,
    OrganismicDemoPhase,
    OrganismicDemoScenario,
)

__all__ = [
    "ComparisonArm", "ComparisonResult", "OrganismicDemoComparison",
    "MinimalFieldOrganismDemoReportBuilder",
    "MinimalFieldOrganismRunner",
    "FixtureFeederSet", "write_fixtures",
    "ObservationTrace", "TraceEvent", "TraceEventType",
    "PerceptionChangeMetric", "PerceptionChangeProbe", "PerceptionChangeResult",
    "OrganismicDemoSafetyValidator",
    "OrganismicDemoConfig", "OrganismicDemoPhase", "OrganismicDemoScenario",
]
