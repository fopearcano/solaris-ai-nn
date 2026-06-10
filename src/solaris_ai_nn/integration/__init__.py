"""Optional Solaris_Ai integration -- the observe-first sidecar layer.

Everything that touches (or could touch) the real ``fopearcano/solaris-ai``
package is isolated here. Solaris_Ai is never a required dependency: all
imports of it are optional and duck-typed, and the whole package works against
fake runtimes. Solaris_Ai remains the organism and the action authority; this
layer observes, learns, and suggests.
"""

from .bus_connector import SolarisBusConnector  # noqa: F401
from .compatibility import (  # noqa: F401
    BUS_OBSERVABLE,
    COMPATIBILITY_LEVELS,
    FULL_TEST_READY,
    MINIMAL,
    SIDECAR_READY,
    UNAVAILABLE,
    FeatureStatus,
    SolarisCompatibilityReport,
    level_at_least,
)
from .conscience_sidecar import SolarisNNSidecar  # noqa: F401
from .integration_state import IntegrationState  # noqa: F401
from .optional_imports import (  # noqa: F401
    get_solaris_import_error,
    import_solaris_conscience,
    import_solaris_signals,
    is_solaris_available,
)
from .signal_mirror import MirroredSignal, SignalMirror  # noqa: F401
from .solaris_probe import SolarisRuntimeProbe  # noqa: F401
from .suggestion_channel import (  # noqa: F401
    ACTION_SUGGESTION,
    DESIRE_SUGGESTION,
    MODULATION_SUGGESTION,
    PLASTICITY_SUGGESTION,
    NeuralSuggestion,
    SuggestionChannel,
)

__all__ = [
    "is_solaris_available",
    "get_solaris_import_error",
    "import_solaris_signals",
    "import_solaris_conscience",
    "SolarisRuntimeProbe",
    "SolarisCompatibilityReport",
    "FeatureStatus",
    "COMPATIBILITY_LEVELS",
    "level_at_least",
    "UNAVAILABLE",
    "MINIMAL",
    "BUS_OBSERVABLE",
    "SIDECAR_READY",
    "FULL_TEST_READY",
    "SolarisBusConnector",
    "SignalMirror",
    "MirroredSignal",
    "NeuralSuggestion",
    "SuggestionChannel",
    "DESIRE_SUGGESTION",
    "ACTION_SUGGESTION",
    "MODULATION_SUGGESTION",
    "PLASTICITY_SUGGESTION",
    "SolarisNNSidecar",
    "IntegrationState",
]
