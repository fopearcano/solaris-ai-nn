"""Optional local LLM adapter (Prompt 20) -- a translator, never authority.

The authority chain stays deterministic end to end; the adapter sits
beside it, paraphrasing, summarizing, and polishing text that was already
grounded and already safe. Disabled by default, localhost-only by default,
mock-backed for every test, validated by grounding heuristics and
ClaimGuard, audited by hash, and structurally unable to decide, approve,
execute, or remember anything.
"""

from .audit import LLMAuditEvent, LLMAuditLog, text_hash
from .base import (
    DEFAULT_FORBIDDEN_CLAIMS,
    LLMAdapter,
    LLMAdapterStatus,
    LLMRequest,
    LLMResponse,
    LLMTaskType,
)
from .claim_filter import LLMClaimFilter
from .classification_assist import (
    RISK_ORDER,
    ClassificationSuggestion,
    LLMClassificationAssistant,
    risk_rank,
)
from .config import LLMAdapterConfig, is_localhost_url
from .grounding import GroundingReport, GroundingValidator
from .local_client import LocalHTTPLLMAdapter
from .mock_client import MockLLMAdapter
from .paraphrase import LLMParaphraser
from .prompt_contracts import (
    GLOBAL_RULES,
    ClaimRewriteContract,
    ClassificationAssistContract,
    MetricsExplanationContract,
    ParaphraseContract,
    PromptContract,
    ReportPolishContract,
    SummaryContract,
    build_prompt,
    contract_for,
)
from .report_polish import PolishResult, ReportPolisher
from .safety import LLMAdapterSafetyValidator, LLMSafetyReport
from .summary import LLMSummarizer

__all__ = [
    "DEFAULT_FORBIDDEN_CLAIMS", "GLOBAL_RULES", "RISK_ORDER",
    "ClaimRewriteContract", "ClassificationAssistContract",
    "ClassificationSuggestion", "GroundingReport", "GroundingValidator",
    "LLMAdapter", "LLMAdapterConfig", "LLMAdapterSafetyValidator",
    "LLMAdapterStatus", "LLMAuditEvent", "LLMAuditLog", "LLMClaimFilter",
    "LLMClassificationAssistant", "LLMParaphraser", "LLMRequest",
    "LLMResponse", "LLMSafetyReport", "LLMSummarizer", "LLMTaskType",
    "LocalHTTPLLMAdapter", "MetricsExplanationContract",
    "MockLLMAdapter", "ParaphraseContract", "PolishResult",
    "PromptContract", "ReportPolishContract", "ReportPolisher",
    "SummaryContract", "build_prompt", "contract_for",
    "is_localhost_url", "risk_rank", "text_hash",
]
