"""Emergent proto-language and self-generated symbols (Prompt 22).

Language begins as internal differentiation: repeated experience earns
compact generated signs, signs combine into proto-syntactic structures,
and every symbol must pay for itself in compression, prediction, or
grounding stability. No LLM, no human teaching, no human language, no
understanding claim, no authority -- internal signs under measurement.
"""

from .combinatorics import (
    SymbolCombination,
    SymbolCombinator,
    SymbolSequence,
)
from .compression import (
    PROTECTED_KINDS,
    SymbolCompressionEvaluator,
    SymbolizedTrace,
)
from .layer import ProtoLanguageLayer
from .pattern_naming import (
    FORBIDDEN_NAME_FRAGMENTS,
    TYPE_PREFIXES,
    InternalPatternNamer,
)
from .prediction_utility import SymbolPredictionEvaluator
from .reports import (
    HUMAN_LANGUAGE_ANSWER,
    PROTO_LANGUAGE_LIMITATIONS,
    ProtoLanguageQueryInterface,
    ProtoLanguageReportBuilder,
)
from .safety import (
    ProtoLanguageSafetyReport,
    ProtoLanguageSafetyValidator,
)
from .semantic_grounding import (
    GROUNDING_DIMENSIONS,
    GroundedMeaning,
    SemanticGroundingEngine,
)
from .symbol_emergence import SymbolCandidate, SymbolEmergenceEngine
from .symbol_memory import SymbolMemory, SymbolMemoryRecord
from .symbol_registry import SymbolRegistry
from .symbols import (
    ProtoSymbol,
    SymbolConfidence,
    SymbolGrounding,
    SymbolType,
)
from .syntax_probe import ProtoSyntaxRule, SyntaxProbe
from .translation import ProtoLanguageTranslator
from .utterance import (
    UTTERANCE_PURPOSES,
    ProtoUtterance,
    ProtoUtteranceBuilder,
)

__all__ = [
    "FORBIDDEN_NAME_FRAGMENTS", "GROUNDING_DIMENSIONS",
    "GroundedMeaning", "HUMAN_LANGUAGE_ANSWER", "InternalPatternNamer",
    "PROTECTED_KINDS", "PROTO_LANGUAGE_LIMITATIONS",
    "ProtoLanguageLayer", "ProtoLanguageQueryInterface",
    "ProtoLanguageReportBuilder", "ProtoLanguageSafetyReport",
    "ProtoLanguageSafetyValidator", "ProtoLanguageTranslator",
    "ProtoSymbol", "ProtoSyntaxRule", "ProtoUtterance",
    "ProtoUtteranceBuilder", "SemanticGroundingEngine",
    "SymbolCandidate", "SymbolCombination", "SymbolCombinator",
    "SymbolCompressionEvaluator", "SymbolConfidence",
    "SymbolEmergenceEngine", "SymbolGrounding", "SymbolMemory",
    "SymbolMemoryRecord", "SymbolPredictionEvaluator",
    "SymbolRegistry", "SymbolSequence", "SymbolType", "SymbolizedTrace",
    "SyntaxProbe", "TYPE_PREFIXES", "UTTERANCE_PURPOSES",
]
