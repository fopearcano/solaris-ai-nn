"""Runnable experiments built on the adaptive event loop and neural bridge."""

from .absence_stimulus_bridge import (  # noqa: F401
    AbsenceResult,
    run_absence_stimulus_bridge,
)
from .minimal_continuous_esn import (  # noqa: F401
    ExperimentResult,
    RepeatedPatternEnvironment,
    main,
    run_minimal_continuous_esn,
)
from .inner_map_evolution import (  # noqa: F401
    InnerMapEvolutionResult,
    run_inner_map_evolution,
)
from .plasticity_adaptation import (  # noqa: F401
    PlasticityAdaptationResult,
    rollback_last,
    run_plasticity_adaptation,
)
from .embodied_absence import EmbodiedAbsenceResult, run_embodied_absence  # noqa: F401
from .language_trace_demo import (  # noqa: F401
    LanguageTraceResult,
    run_language_trace_demo,
)
from .reward_danger_adaptation import (  # noqa: F401
    RewardDangerResult,
    run_reward_danger_adaptation,
)
from .sensorimotor_gridworld import (  # noqa: F401
    SensorimotorResult,
    run_sensorimotor_gridworld,
)
from .soak_continuity import SoakResult, run_soak_continuity  # noqa: F401
from .solaris_sidecar_observation import (  # noqa: F401
    SidecarObservationResult,
    run_sidecar_observation,
)
from .spiking_silence import SilenceResult, run_spiking_silence  # noqa: F401
from .substrate_comparison import (  # noqa: F401
    SubstrateComparisonResult,
    run_substrate_comparison,
)

__all__ = [
    "run_minimal_continuous_esn",
    "RepeatedPatternEnvironment",
    "ExperimentResult",
    "main",
    "run_absence_stimulus_bridge",
    "AbsenceResult",
    "run_soak_continuity",
    "SoakResult",
    "run_inner_map_evolution",
    "InnerMapEvolutionResult",
    "run_plasticity_adaptation",
    "rollback_last",
    "PlasticityAdaptationResult",
    "run_substrate_comparison",
    "SubstrateComparisonResult",
    "run_spiking_silence",
    "SilenceResult",
    "run_sidecar_observation",
    "SidecarObservationResult",
    "run_sensorimotor_gridworld",
    "SensorimotorResult",
    "run_embodied_absence",
    "EmbodiedAbsenceResult",
    "run_reward_danger_adaptation",
    "RewardDangerResult",
    "run_language_trace_demo",
    "LanguageTraceResult",
]
