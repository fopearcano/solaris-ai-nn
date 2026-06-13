"""Active perception, intrinsic exploration, and self-directed sampling.

Until now the ecology *fed* stimuli into Solaris-AI-NN. This package lets the
system begin to **regulate its own exposure**: estimate salience, uncertainty,
intrinsic (curiosity) pressure, expected information gain, stagnation, and
attention focus; propose *safe* sampling actions (look, wait, rest, focus,
replay, consolidate, seek novelty/absence, inspect a node/symbol/boundary,
emit a simulated ping, observe a sidecar); route them through
safety/governance/executive/ego; and record what actually helped.

It is **not** real-world autonomy. Every action is simulation-only,
internal-only, read-only, sidecar-observe-only, or suggestion-only. Curiosity
is an *intrinsic pressure metric*, never a human desire, and it can never
override safety, governance, executive inhibition, ego boundaries, or the
emergency stop. No LLM is used for any exploration decision.
"""

from __future__ import annotations

from .active_sensing import ActiveSensingController
from .attention_control import (
    ActiveAttentionController,
    AttentionControlState,
    AttentionFocus,
)
from .curiosity import CuriosityEstimator, CuriosityState, IntrinsicPressure
from .exploration_memory import ExplorationMemory, ExplorationRecord
from .information_gain import (
    InformationGainEstimate,
    InformationGainEstimator,
)
from .reports import (
    ActivePerceptionQueryInterface,
    ActivePerceptionReportBuilder,
)
from .safety import ActivePerceptionSafetyValidator
from .salience import SalienceEstimator, SalienceMap, SalienceSignal
from .sampling_actions import (
    SamplingAction,
    SamplingActionResult,
    SamplingActionType,
    SamplingScope,
)
from .sampling_policy import (
    SamplingDecision,
    SamplingPolicy,
    SamplingPolicyMode,
)
from .stagnation import StagnationDetector, StagnationState
from .uncertainty import (
    UncertaintyEstimator,
    UncertaintySource,
    UncertaintyState,
)

__all__ = [
    "ActiveAttentionController", "ActivePerceptionQueryInterface",
    "ActivePerceptionReportBuilder",
    "ActivePerceptionSafetyValidator", "ActiveSensingController",
    "AttentionControlState", "AttentionFocus", "CuriosityEstimator",
    "CuriosityState", "ExplorationMemory", "ExplorationRecord",
    "InformationGainEstimate", "InformationGainEstimator",
    "IntrinsicPressure", "SalienceEstimator", "SalienceMap",
    "SalienceSignal", "SamplingAction", "SamplingActionResult",
    "SamplingActionType", "SamplingDecision", "SamplingPolicy",
    "SamplingPolicyMode", "SamplingScope", "StagnationDetector",
    "StagnationState", "UncertaintyEstimator", "UncertaintySource",
    "UncertaintyState",
]
