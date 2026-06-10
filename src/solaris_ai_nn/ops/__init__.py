"""Operations layer: supervised, healthy, interruptible long-running runs.

Continuity requires supervision: health checks, a watchdog that *requests*
(never forces) safe shutdown, resource budgets, artifact rotation, incident
logs, a run registry, staged soak plans, and an optional read-only localhost
status server. Long-running modes always require explicit flags.
"""

from .artifact_rotation import ArtifactRotationPolicy  # noqa: F401
from .health import (  # noqa: F401
    HealthCheck,
    HealthMonitor,
    HealthReport,
    HealthStatus,
)
from .incident import INCIDENT_TYPES, Incident, IncidentLog  # noqa: F401
from .local_status_server import LocalStatusServer  # noqa: F401
from .resource_budget import BudgetReport, ResourceBudget  # noqa: F401
from .run_manifest import (  # noqa: F401
    OperationalRunManifest,
    RunMode,
    RunSafetyMode,
)
from .run_registry import RunRegistry  # noqa: F401
from .safe_shutdown import SafeShutdownManager  # noqa: F401
from .soak_plan import SoakPlan, SoakPlanBuilder, SoakStage  # noqa: F401
from .status import OperationalStatus  # noqa: F401
from .supervisor import OperationalSupervisor, default_runner_factory  # noqa: F401
from .watchdog import Watchdog, WatchdogDecision  # noqa: F401

__all__ = [
    "OperationalRunManifest", "RunMode", "RunSafetyMode",
    "HealthMonitor", "HealthReport", "HealthCheck", "HealthStatus",
    "Watchdog", "WatchdogDecision",
    "ResourceBudget", "BudgetReport",
    "ArtifactRotationPolicy", "SafeShutdownManager",
    "Incident", "IncidentLog", "INCIDENT_TYPES",
    "RunRegistry", "OperationalStatus",
    "SoakPlan", "SoakStage", "SoakPlanBuilder",
    "LocalStatusServer",
    "OperationalSupervisor", "default_runner_factory",
]
