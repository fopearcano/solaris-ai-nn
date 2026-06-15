"""Semiogenesis -- sensorium-native internal signs, private syntax, no human words.

Prompt 47 gave Solaris-AI-NN sensorium-native proto-concepts. This layer adds
*semiogenesis*: the birth of internal signs from those concepts --

    perceptual atoms -> proto-concepts -> internal signs -> sign families ->
    private syntax -> internal utterances -> compression/prediction/attention
    utility -> optional human-readable gloss (for reports only)

A *sign* is NOT a word and NOT a human label. It is a compact internal marker
(``rf:03a``, ``abs:burst_gap_07``, ``xmod:rf_vib_11``) that helps Solaris compress,
recall, relate, predict, or attend to sensorium-native structures. Private syntax
is internal sign-relation structure, NOT human grammar. Human-readable *gloss* is
an approximate debug annotation only -- never ground truth, never the internal
language. No LLM is used, no human language is the internal default, no human label
is ground truth, and nothing here controls hardware, feeders, the network, a shell,
a source, or the real world. No claim of consciousness, sentience, life,
personhood, agency, free will, language understanding, or subjective experience is
made.
"""

from __future__ import annotations

from .contamination import (
    SignContaminationAnalyzer,
    SignContaminationReport,
)
from .drift import SignDrift, SignDriftDetector, SignDriftResult
from .private_syntax import (
    PrivateSyntaxPattern,
    SyntaxPatternBuilder,
    SyntaxRelation,
)
from .reports import SemiogenesisReportBuilder
from .safety import HARD_RULES, SemiogenesisSafetyValidator
from .semiogenesis_runtime import (
    SemiogenesisMilestone,
    SemiogenesisRuntime,
)
from .sign_birth import (
    SignBirthCandidate,
    SignBirthEngine,
    SignBirthTrigger,
)
from .sign_family import (
    SignFamily,
    SignFamilyBuilder,
    SignFamilyRelation,
    SignFamilyType,
)
from .sign_memory import (
    SignMemoryIndex,
    SignMemoryRecord,
    SignMemoryStore,
)
from .sign_utility import SignUtilityEvaluator, SignUtilityResult
from .signs import (
    InternalSign,
    SignGrounding,
    SignKind,
    SignStatus,
    operational_sign_code,
)
from .translation_gloss import GlossBuilder, GlossStatus, TranslationGloss
from .utterance import (
    InternalUtterance,
    UtteranceBuilder,
    UtteranceKind,
)

__all__ = [
    "SignContaminationAnalyzer", "SignContaminationReport",
    "SignDrift", "SignDriftDetector", "SignDriftResult",
    "PrivateSyntaxPattern", "SyntaxPatternBuilder", "SyntaxRelation",
    "SemiogenesisReportBuilder",
    "HARD_RULES", "SemiogenesisSafetyValidator",
    "SemiogenesisMilestone", "SemiogenesisRuntime",
    "SignBirthCandidate", "SignBirthEngine", "SignBirthTrigger",
    "SignFamily", "SignFamilyBuilder", "SignFamilyRelation", "SignFamilyType",
    "SignMemoryIndex", "SignMemoryRecord", "SignMemoryStore",
    "SignUtilityEvaluator", "SignUtilityResult",
    "InternalSign", "SignGrounding", "SignKind", "SignStatus",
    "operational_sign_code",
    "GlossBuilder", "GlossStatus", "TranslationGloss",
    "InternalUtterance", "UtteranceBuilder", "UtteranceKind",
]
