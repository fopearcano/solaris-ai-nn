"""Embodiment: a simulated body and bounded grid world. Simulation-only.

Sensors emit canonical Stimuli; the bridge suggests actions; effectors act
only inside the GridWorld; consequences come back as Reactions. There is no
real-world actuation anywhere here, and no claim of consciousness.
"""

from .action_space import (  # noqa: F401
    ACTION_SPACE,
    ALLOWED_ACTIONS,
    FORBIDDEN_ACTIONS,
    ActionSpec,
    get_action,
)
from .base import (  # noqa: F401
    ActionResult,
    Body,
    EffectorCommand,
    Effector,
    EmbodimentState,
    Environment,
    Sensor,
    SensorReading,
)
from .body import SimulatedBody  # noqa: F401
from .effectors import default_effectors  # noqa: F401
from .energy import EnergyModel  # noqa: F401
from .environment import create_environment  # noqa: F401
from .feedback import EmbodimentFeedback  # noqa: F401
from .grid_world import GridWorld  # noqa: F401
from .safety import EmbodimentSafety, SafetyReport  # noqa: F401
from .sensors import SENSOR_VOCABULARY, default_sensors  # noqa: F401
from .simulation_runner import SensorimotorSimulationRunner  # noqa: F401
from .state import build_embodiment_state  # noqa: F401

__all__ = [
    "Sensor", "Effector", "Body", "Environment", "EmbodimentState",
    "SensorReading", "EffectorCommand", "ActionResult",
    "ActionSpec", "ACTION_SPACE", "ALLOWED_ACTIONS", "FORBIDDEN_ACTIONS",
    "get_action", "GridWorld", "create_environment", "SimulatedBody",
    "EnergyModel", "EmbodimentFeedback", "EmbodimentSafety", "SafetyReport",
    "SensorimotorSimulationRunner", "default_sensors", "default_effectors",
    "SENSOR_VOCABULARY", "build_embodiment_state",
]
