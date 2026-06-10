"""Internal language layer: cross-module meaning, not chat.

Structured meaning traces (controlled vocabulary), heuristic causal traces,
grounded deterministic explanations, structural summaries, JSON/Markdown
reports, and a fixed query interface. No LLMs, no external APIs, no claims of
consciousness -- every statement reduces to recorded runtime state.
"""

from .causal_trace import CausalTraceBuilder  # noqa: F401
from .explanation import ExplanationEngine  # noqa: F401
from .meaning_trace import MeaningTraceBuilder, atom  # noqa: F401
from .query import QueryInterface, normalize  # noqa: F401
from .reporting import ExperimentReportBuilder, SessionReport  # noqa: F401
from .schemas import (  # noqa: F401
    CausalLink,
    CausalTrace,
    Explanation,
    ExplanationContext,
    ExperimentReport,
    LanguageEvent,
    MeaningAtom,
    MeaningTrace,
    QueryResult,
    SystemUtterance,
)
from .serialization import (  # noqa: F401
    save_causal_trace,
    save_explanations,
    save_meaning_trace,
    save_report,
)
from .summarizer import STANDARD_LIMITATIONS, StructuralSummarizer  # noqa: F401
from .templates import TEMPLATES, render  # noqa: F401
from .vocabulary import (  # noqa: F401
    CATEGORIES,
    PREDICATES,
    normalize_category,
    normalize_predicate,
)

__all__ = [
    "LanguageEvent", "MeaningAtom", "MeaningTrace", "CausalLink", "CausalTrace",
    "Explanation", "ExplanationContext", "SystemUtterance", "ExperimentReport",
    "QueryResult", "MeaningTraceBuilder", "atom", "CausalTraceBuilder",
    "ExplanationEngine", "QueryInterface", "normalize", "StructuralSummarizer",
    "STANDARD_LIMITATIONS", "ExperimentReportBuilder", "SessionReport",
    "TEMPLATES", "render", "CATEGORIES", "PREDICATES", "normalize_category",
    "normalize_predicate", "save_meaning_trace", "save_causal_trace",
    "save_explanations", "save_report",
]
