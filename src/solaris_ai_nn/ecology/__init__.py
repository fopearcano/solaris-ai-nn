"""Developmental nursery and stimulus ecology (Prompt 23).

A developmental system needs a world, not a teacher. This package builds
a low-compute, inspectable, deterministic artificial ecology -- repetition,
absence, scarcity, rhythms, day/night cycles, novelty, danger/reward
analogues, boundaries, rare events, seasonal drift, long quiet periods,
pattern breaks, delayed consequences, and recoverable disruptions -- that
feeds canonical signals into the rest of the stack over long horizons.
No human teaching, no LLM language injection, no real-world actuation.
"""

from .anomalies import AnomalyGenerator, AnomalyKind
from .cycles import Cycle, CycleManager, CycleState, CycleType
from .delayed_consequence import (
    ConsequenceKind,
    DelayedConsequenceModel,
)
from .deprivation import DeprivationKind, DeprivationModel
from .ecology_memory import EcologyEpisode, EcologyMemory
from .events import (
    ECOLOGY_NOTE,
    EcologyEvent,
    EcologyEventType,
    EcologyStimulus,
    StimulusSource,
)
from .novelty import NoveltyGenerator
from .nursery import DevelopmentalNursery, NurseryConfig, NurseryState
from .regimes import (
    EcologyRegime,
    RegimeManager,
    RegimeType,
    get_regime,
)
from .reports import ECOLOGY_LIMITATIONS, EcologyReportBuilder
from .safety import EcologySafetyReport, EcologySafetyValidator
from .scarcity import ScarcityModel
from .seasonality import SeasonalityModel
from .stimulus_ecology import StimulusEcology
from .streams import EcologyStream, to_canonical_signal

__all__ = [
    "ECOLOGY_LIMITATIONS", "ECOLOGY_NOTE", "AnomalyGenerator",
    "AnomalyKind", "ConsequenceKind", "Cycle", "CycleManager",
    "CycleState", "CycleType", "DelayedConsequenceModel",
    "DeprivationKind", "DeprivationModel", "DevelopmentalNursery",
    "EcologyEpisode", "EcologyEvent", "EcologyEventType",
    "EcologyMemory", "EcologyRegime", "EcologyReportBuilder",
    "EcologySafetyReport", "EcologySafetyValidator", "EcologyStimulus",
    "EcologyStream", "NoveltyGenerator", "NurseryConfig",
    "NurseryState", "RegimeManager", "RegimeType", "ScarcityModel",
    "SeasonalityModel", "StimulusEcology", "StimulusSource",
    "get_regime", "to_canonical_signal",
]
