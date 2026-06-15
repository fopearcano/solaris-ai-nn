"""Self-boundary -- the operational distinction between Solaris and the world.

Prompts 41-49 gave Solaris a continuous sensorium, perceptual metabolism,
proto-concepts, internal signs, and sign-based cognition. This layer adds an
operational self/world *boundary*: it learns to distinguish

    internal state | receptor body | sensory membrane | external feeder |
    external world source | memory trace | prediction | simulation |
    counterfactual | operator annotation | unknown

It answers, operationally, "how does this organismic AI distinguish *my perceptual
body* from *the world that touches it*?" -- via ownership attribution, a receptor
body schema, perspective frames, continuity anchors, source attribution, internal/
external classification, simulation-boundary validation, an operational identity
trace, and boundary tensions.

This is NOT consciousness, NOT personhood, NOT a soul, and NOT subjective
experience. The body schema is receptor/sensorium structure, not a biological body;
the identity trace is continuity metadata, not personal identity. Nothing here
controls hardware, feeders, the network, a shell, a source, or the real world, and
processed sensory data is never silently collapsed into "internal self".
"""

from __future__ import annotations

from .body_schema import (
    BodySchemaUpdate,
    ReceptorBodyPart,
    SensoriumBodySchema,
)
from .boundary_state import (
    BoundaryConfidence,
    BoundaryEvent,
    BoundaryZone,
    SelfBoundaryState,
)
from .boundary_tensions import (
    BoundaryTension,
    BoundaryTensionDetector,
    BoundaryTensionType,
)
from .continuity import (
    ContinuityAnchor,
    ContinuityAnchorType,
    ContinuityBreak,
    ContinuityBreakType,
    ContinuityRecovery,
    OrganismicContinuity,
)
from .identity_trace import (
    IdentityTraceEvent,
    IdentityTraceEventType,
    IdentityTraceStore,
    OperationalIdentityTrace,
)
from .internal_external import (
    InternalExternalClassification,
    InternalExternalClassifier,
    InternalExternalLabel,
)
from .ownership import (
    OwnershipAttribution,
    OwnershipAttributor,
    OwnershipType,
)
from .perspective import (
    PerspectiveFrame,
    PerspectiveShift,
    SensoriumPerspective,
)
from .reports import SelfBoundaryReportBuilder
from .safety import HARD_RULES, SelfBoundarySafetyValidator
from .self_boundary_runtime import SelfBoundaryMilestone, SelfBoundaryRuntime
from .simulation_boundary import (
    BoundaryMarker,
    SimulationBoundaryMarker,
    SimulationBoundaryValidator,
    SimulationBoundaryViolation,
)
from .source_attribution import (
    AttributionEvidence,
    AttributionTarget,
    SourceAttribution,
    SourceAttributionEngine,
)

__all__ = [
    "BodySchemaUpdate", "ReceptorBodyPart", "SensoriumBodySchema",
    "BoundaryConfidence", "BoundaryEvent", "BoundaryZone", "SelfBoundaryState",
    "BoundaryTension", "BoundaryTensionDetector", "BoundaryTensionType",
    "ContinuityAnchor", "ContinuityAnchorType", "ContinuityBreak",
    "ContinuityBreakType", "ContinuityRecovery", "OrganismicContinuity",
    "IdentityTraceEvent", "IdentityTraceEventType", "IdentityTraceStore",
    "OperationalIdentityTrace",
    "InternalExternalClassification", "InternalExternalClassifier",
    "InternalExternalLabel",
    "OwnershipAttribution", "OwnershipAttributor", "OwnershipType",
    "PerspectiveFrame", "PerspectiveShift", "SensoriumPerspective",
    "SelfBoundaryReportBuilder",
    "HARD_RULES", "SelfBoundarySafetyValidator",
    "SelfBoundaryMilestone", "SelfBoundaryRuntime",
    "BoundaryMarker", "SimulationBoundaryMarker",
    "SimulationBoundaryValidator", "SimulationBoundaryViolation",
    "AttributionEvidence", "AttributionTarget", "SourceAttribution",
    "SourceAttributionEngine",
]
