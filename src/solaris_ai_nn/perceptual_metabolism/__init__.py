"""Perceptual metabolism -- an organism metabolizes stimuli, it does not just record.

Prompts 41-45 gave Solaris-AI-NN a plural sensorium and an external feeder system.
This layer adds the regulation that turns continuous exposure into a *metabolism*:
operational perceptual needs, a finite energy/attention budget, sensory
homeostasis, an attention economy, overload and deprivation detection, novelty
appetite, source-diet analysis, and consolidation pressure --

    outside world -> external feeders -> plural sensorium -> receptor states ->
    sensory field pressure -> perceptual metabolism -> attention allocation ->
    homeostatic regulation -> memory/proto-symbol/world-model adaptation ->
    changed future perception

Perceptual *needs* are operational regulatory pressures, NOT feelings, emotions,
or subjective experience; "metabolism" is a computational regulation metaphor, NOT
biological life. All regulation is internal and bounded: nothing here controls
hardware, starts a feeder, accesses the network, runs a shell, modifies a source,
or actuates the real world, and no claim of consciousness, sentience, life,
personhood, agency, or free will is made.
"""

from __future__ import annotations

from .attention_economy import (
    AttentionAllocation,
    AttentionEconomy,
    AttentionMarketState,
    AttentionTarget,
)
from .consolidation_pressure import (
    ConsolidationPressureEstimator,
    ConsolidationPressureState,
    ConsolidationRecommendation,
)
from .deprivation import (
    DeprivationDetector,
    DeprivationEvent,
    DeprivationKind,
    SensoryDeprivationState,
)
from .energy_budget import (
    EnergyAllocation,
    EnergyBudgetResult,
    PerceptualEnergyBudget,
)
from .metabolic_runtime import (
    MetabolismMilestone,
    PerceptualMetabolismRuntime,
)
from .needs import (
    PerceptualNeed,
    PerceptualNeedModel,
    PerceptualNeedState,
    PerceptualNeedType,
)
from .novelty_appetite import (
    NoveltyAppetiteRegulator,
    NoveltyAppetiteState,
)
from .overload import (
    OverloadDetector,
    OverloadEvent,
    OverloadKind,
    SensoryOverloadState,
)
from .reports import PerceptualMetabolismReportBuilder
from .safety import HARD_RULES, PerceptualMetabolismSafetyValidator
from .sensory_homeostasis import (
    HomeostaticSetPoint,
    SensoryHomeostasisRegulator,
    SensoryHomeostasisState,
)
from .source_diet import (
    SourceDietAnalyzer,
    SourceDietBalance,
    SourceDietProfile,
)

__all__ = [
    "AttentionAllocation", "AttentionEconomy", "AttentionMarketState",
    "AttentionTarget",
    "ConsolidationPressureEstimator", "ConsolidationPressureState",
    "ConsolidationRecommendation",
    "DeprivationDetector", "DeprivationEvent", "DeprivationKind",
    "SensoryDeprivationState",
    "EnergyAllocation", "EnergyBudgetResult", "PerceptualEnergyBudget",
    "MetabolismMilestone", "PerceptualMetabolismRuntime",
    "PerceptualNeed", "PerceptualNeedModel", "PerceptualNeedState",
    "PerceptualNeedType",
    "NoveltyAppetiteRegulator", "NoveltyAppetiteState",
    "OverloadDetector", "OverloadEvent", "OverloadKind",
    "SensoryOverloadState",
    "PerceptualMetabolismReportBuilder",
    "HARD_RULES", "PerceptualMetabolismSafetyValidator",
    "HomeostaticSetPoint", "SensoryHomeostasisRegulator",
    "SensoryHomeostasisState",
    "SourceDietAnalyzer", "SourceDietBalance", "SourceDietProfile",
]
