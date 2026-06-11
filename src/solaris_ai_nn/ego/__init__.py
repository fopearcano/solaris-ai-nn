"""Ego boundary, self-model, and dimensional comparison (Prompt 18).

An *operational* self-model: identity anchors and runtime continuity,
self/not-self boundaries, dimensional frames, ownership attribution, a
simulated body schema, perspective tracking, a narrative trace, and safe
self-reports. It observes and classifies for safety, explanation,
governance, and the Inner MAP -- it is not consciousness, personhood,
agency, or free will, and it can override none of the layers above it.
"""

from .body_schema import ActionAuthority, BodyBoundary, BodySchema
from .boundaries import (
    BoundaryEvent,
    BoundaryRegistry,
    BoundaryState,
    BoundaryStatus,
    BoundaryType,
    register_default_boundaries,
)
from .continuity import ContinuityAssessment, EgoContinuityMonitor
from .dimensional_comparison import (
    Dimension,
    DimensionalComparator,
    DimensionalComparison,
    DimensionalFrame,
)
from .identity import IdentityAnchor, IdentityContinuityScore, IdentityState
from .narrative_trace import NarrativeTrace, NarrativeTraceEvent
from .ownership import AttributionResult, OwnershipAttributor, OwnershipClaim
from .perspective import PerspectiveMode, PerspectiveState, PerspectiveTracker
from .safety import EgoSafetyReport, EgoSafetyValidator
from .self_model import (
    SelfClassification,
    SelfModel,
    SelfModelObserver,
    SelfModelSnapshot,
)
from .self_report import EgoQueryInterface, SelfReportBuilder

__all__ = [
    "ActionAuthority", "AttributionResult", "BodyBoundary", "BodySchema",
    "BoundaryEvent", "BoundaryRegistry", "BoundaryState", "BoundaryStatus",
    "BoundaryType", "ContinuityAssessment", "Dimension",
    "DimensionalComparator", "DimensionalComparison", "DimensionalFrame",
    "EgoContinuityMonitor", "EgoQueryInterface", "EgoSafetyReport",
    "EgoSafetyValidator", "IdentityAnchor", "IdentityContinuityScore",
    "IdentityState", "NarrativeTrace", "NarrativeTraceEvent",
    "OwnershipAttributor", "OwnershipClaim", "PerspectiveMode",
    "PerspectiveState", "PerspectiveTracker", "SelfClassification",
    "SelfModel", "SelfModelObserver", "SelfModelSnapshot",
    "SelfReportBuilder", "register_default_boundaries",
]
