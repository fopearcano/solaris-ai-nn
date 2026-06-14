"""Conscience -- the unified runtime spine that assembles the whole organism.

This package turns the project's independent modules into one runnable,
bounded, auditable developmental process. It preserves the Solaris spine
(Stimulus -> Push -> Desire -> ActionCandidate/ActionSuggestion ->
Reaction/Outcome -> Memory/World Model/Inner MAP/Developmental State) while
keeping every action internal/simulation-only and ensuring no module is
sovereign: nothing bypasses executive inhibition, Ego boundaries, safety,
governance, ClaimGuard, the emergency stop, or auto-regeneration safety.

It does not add new cognitive theory, LLM authority, real-world autonomy, or
any network/OS/browser automation.
"""

from __future__ import annotations

from .bus import BusMessage, BusSubscription, BusTopic, BusTrace, ConscienceBus
from .full_system_report import FullSystemReport, FullSystemReportBuilder
from .integration_health import (
    HealthStatus,
    IntegrationHealthCheck,
    IntegrationHealthMonitor,
    IntegrationHealthReport,
)
from .module_lifecycle import (
    LifecycleTransition,
    ModuleLifecycleManager,
    ModuleLifecycleState,
)
from .module_registry import (
    ConscienceModuleRegistry,
    ModuleCapability,
    ModuleDescriptor,
    ModuleStatus,
)
from .orchestrator import ConscienceOrchestrator
from .run_context import (
    RunAuthority,
    RunBoundary,
    RunContext,
    RunMode,
)
from .safety import (
    HARD_RULES,
    ConscienceRuntimeSafetyValidator,
    ConscienceSafetyReport,
)
from .scenario_profiles import (
    ScenarioProfile,
    ScenarioProfileRegistry,
)
from .scenario_runner import (
    ScenarioExitStatus,
    ScenarioRunResult,
    ScenarioRunner,
)
from .scheduler import (
    ConscienceScheduler,
    ScheduleCadence,
    ScheduleSlot,
)
from .snapshots import ConscienceSnapshot, SnapshotBuilder
from .spine import (
    ConscienceSpine,
    PhaseStatus,
    SpineEvent,
    SpinePhase,
    SpineTrace,
)

__all__ = [
    # bus
    "BusMessage", "BusSubscription", "BusTopic", "BusTrace", "ConscienceBus",
    # spine
    "ConscienceSpine", "PhaseStatus", "SpineEvent", "SpinePhase", "SpineTrace",
    # registry / lifecycle
    "ConscienceModuleRegistry", "ModuleCapability", "ModuleDescriptor",
    "ModuleStatus", "LifecycleTransition", "ModuleLifecycleManager",
    "ModuleLifecycleState",
    # run context / safety
    "RunAuthority", "RunBoundary", "RunContext", "RunMode",
    "HARD_RULES", "ConscienceRuntimeSafetyValidator", "ConscienceSafetyReport",
    # scheduler
    "ConscienceScheduler", "ScheduleCadence", "ScheduleSlot",
    # orchestrator
    "ConscienceOrchestrator",
    # scenarios
    "ScenarioProfile", "ScenarioProfileRegistry", "ScenarioExitStatus",
    "ScenarioRunResult", "ScenarioRunner",
    # health / snapshots / reports
    "HealthStatus", "IntegrationHealthCheck", "IntegrationHealthMonitor",
    "IntegrationHealthReport", "ConscienceSnapshot", "SnapshotBuilder",
    "FullSystemReport", "FullSystemReportBuilder",
]
