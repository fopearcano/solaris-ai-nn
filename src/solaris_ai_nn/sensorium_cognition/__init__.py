"""Sensorium-native cognition -- sign-based thought, anticipation, simulation.

Prompt 48 gave Solaris-AI-NN sensorium-native internal signs. This layer adds
*cognition* grounded in those structures rather than human language:

    sensory field -> proto-concepts -> internal signs -> sign relations ->
    cognitive moves -> anticipation/prediction/simulation -> tension/uncertainty/
    question pressure -> attention and internal-action recommendations ->
    memory consolidation -> changed future perception

A *cognitive move* is NOT a sentence. It is an operation over signs,
proto-concepts, relations, memory traces, hypotheses, LOGOS tensions, and
perceptual-metabolism states. No LLM is used, no human language is the internal
default, no chain-of-thought text is the cognitive substrate, and human-readable
summaries are debug glosses only. Internal simulation is marked non-real and is
never a live observation; failed predictions are preserved. Nothing here controls
hardware, feeders, the network, a shell, a source, or the real world, and no claim
of consciousness, sentience, life, personhood, agency, free will, understanding, or
subjective experience is made.
"""

from __future__ import annotations

from .analogy import AnalogyEngine, AnalogyResult, SensoriumAnalogy
from .anticipation import (
    AnticipationEngine,
    AnticipationEvent,
    AnticipationKind,
    AnticipationState,
)
from .cognition_runtime import (
    CognitionMilestone,
    SensoriumCognitionRuntime,
)
from .cognitive_memory import (
    CognitiveMemoryRecord,
    CognitiveMemoryStore,
    CognitiveTraceIndex,
)
from .cognitive_moves import (
    CognitiveMove,
    CognitiveMoveResult,
    CognitiveMoveType,
)
from .cognitive_state import (
    CognitiveContinuity,
    CognitiveFocus,
    CognitivePressure,
    SensoriumCognitiveState,
)
from .counterfactuals import (
    Counterfactual,
    CounterfactualEngine,
    CounterfactualForm,
    CounterfactualResult,
)
from .internal_simulation import (
    InternalSimulation,
    SimulationResult,
    SimulationScope,
    SimulationStep,
)
from .prediction import (
    PredictionEngine,
    PredictionOutcome,
    PredictionResult,
    PredictionType,
    SensoriumPrediction,
)
from .question_pressure import (
    QuestionPressure,
    QuestionPressureEngine,
    QuestionPressureType,
)
from .reports import SensoriumCognitionReportBuilder
from .safety import HARD_RULES, SensoriumCognitionSafetyValidator
from .sign_reasoning import (
    SignInferenceType,
    SignReasoner,
    SignReasoningTrace,
    SignRelationInference,
)
from .synthesis import (
    CognitiveSynthesis,
    SynthesisEngine,
    SynthesisOp,
    SynthesisResult,
)

__all__ = [
    "AnalogyEngine", "AnalogyResult", "SensoriumAnalogy",
    "AnticipationEngine", "AnticipationEvent", "AnticipationKind",
    "AnticipationState",
    "CognitionMilestone", "SensoriumCognitionRuntime",
    "CognitiveMemoryRecord", "CognitiveMemoryStore", "CognitiveTraceIndex",
    "CognitiveMove", "CognitiveMoveResult", "CognitiveMoveType",
    "CognitiveContinuity", "CognitiveFocus", "CognitivePressure",
    "SensoriumCognitiveState",
    "Counterfactual", "CounterfactualEngine", "CounterfactualForm",
    "CounterfactualResult",
    "InternalSimulation", "SimulationResult", "SimulationScope",
    "SimulationStep",
    "PredictionEngine", "PredictionOutcome", "PredictionResult",
    "PredictionType", "SensoriumPrediction",
    "QuestionPressure", "QuestionPressureEngine", "QuestionPressureType",
    "SensoriumCognitionReportBuilder",
    "HARD_RULES", "SensoriumCognitionSafetyValidator",
    "SignInferenceType", "SignReasoner", "SignReasoningTrace",
    "SignRelationInference",
    "CognitiveSynthesis", "SynthesisEngine", "SynthesisOp", "SynthesisResult",
]
