"""Plasticity: habit/synthesis substrates + controlled, safe self-modification.

The Prompt-1 pieces (habit reinforcement, synthesis pruning, drift) are the
*substrates* that change. The Prompt-5 pieces (engine, policy, safety, rollback,
audit, mutation) are the *controller* that proposes, validates, applies, logs,
and rolls back bounded changes to those substrates' runtime parameters -- never
to source code.
"""

from .audit import PlasticityAuditLog  # noqa: F401
from .drift import DriftMonitor  # noqa: F401
from .habit_reinforcement import HabitReinforcement  # noqa: F401
from .mutation import (  # noqa: F401
    PlasticityChange,
    PlasticityResult,
    PlasticityStep,
    PlasticityTarget,
    TargetRegistry,
)
from .plasticity_engine import PlasticityEngine  # noqa: F401
from .policy import PlasticityPolicy  # noqa: F401
from .rollback import RollbackManager  # noqa: F401
from .safety import PlasticitySafetyValidator, SafetyReport  # noqa: F401
from .synthesis_pruning import (  # noqa: F401
    Removal,
    SubtractionReport,
    SynthesisPruner,
)

__all__ = [
    "HabitReinforcement",
    "SynthesisPruner",
    "SubtractionReport",
    "Removal",
    "DriftMonitor",
    "PlasticityStep",
    "PlasticityTarget",
    "PlasticityChange",
    "PlasticityResult",
    "TargetRegistry",
    "PlasticityEngine",
    "PlasticityPolicy",
    "PlasticitySafetyValidator",
    "SafetyReport",
    "RollbackManager",
    "PlasticityAuditLog",
]
