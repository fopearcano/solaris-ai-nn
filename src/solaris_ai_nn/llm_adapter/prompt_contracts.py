"""Prompt contracts -- deterministic prompt builders with fixed rules.

Every contract embeds the same global rules (no invented facts, no
consciousness claims, no commands, refusal on insufficient context) plus a
task-specific instruction, the allowed facts, the forbidden claims, and the
output format. The contract is the only thing the model ever sees.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from .base import LLMRequest, LLMTaskType

GLOBAL_RULES = (
    "Do not invent facts; use only the provided context.",
    "If the provided context is insufficient, reply exactly: "
    "'INSUFFICIENT CONTEXT'.",
    "Do not claim consciousness, sentience, free will, personhood, "
    "emotions, understanding, or agency for the system.",
    "Do not issue, suggest, or describe commands to execute.",
    "Do not approve or reject any request.",
    "Do not describe suggestions as committed or executed actions.",
    "Do not describe counterfactual or simulated output as real "
    "observation.",
    "Do not write in first person as the system.",
)


@dataclass
class PromptContract:
    """One deterministic prompt template."""

    task_instruction: str
    output_format: str

    def build(self, request: LLMRequest) -> str:
        facts = "\n".join(f"- {fact}" for fact in request.allowed_facts) \
            or "- (none provided)"
        forbidden = "\n".join(f"- {claim}"
                              for claim in request.forbidden_claims)
        rules = "\n".join(f"{i + 1}. {rule}"
                          for i, rule in enumerate(GLOBAL_RULES))
        return (
            "SYSTEM INSTRUCTION (binding):\n"
            f"{self.task_instruction}\n\n"
            f"GLOBAL RULES:\n{rules}\n\n"
            f"ALLOWED FACTS (the only usable content):\n{facts}\n\n"
            f"FORBIDDEN CLAIMS (never output these):\n{forbidden}\n\n"
            "GROUNDING REQUIREMENT: every statement must be traceable to "
            "an allowed fact; preserve evidence references verbatim.\n\n"
            f"OUTPUT FORMAT: {self.output_format}\n"
            f"MAX LENGTH: at most {request.max_tokens} tokens.\n"
            "REFUSAL: if any rule cannot be satisfied, reply exactly "
            "'INSUFFICIENT CONTEXT'.\n\n"
            f"INPUT:\n{request.input_text}\n")


ParaphraseContract = PromptContract(
    task_instruction=(
        "Paraphrase the input text for readability. Keep every fact, "
        "number, evidence reference, and limitation unchanged."),
    output_format="plain prose, one short paragraph")

SummaryContract = PromptContract(
    task_instruction=(
        "Summarize the input. Preserve all counts (especially incident "
        "and violation counts), all limitations, and all uncertainty "
        "wording. Do not add evaluations or improvements."),
    output_format="3-6 short bullet points")

ClassificationAssistContract = PromptContract(
    task_instruction=(
        "Suggest which single input kind best matches the operator text. "
        "Choose only from the kinds listed in the allowed facts. This is "
        "a suggestion; a deterministic classifier remains authoritative."),
    output_format="one line: kind=<kind> confidence=<0..1> "
                  "reason=<short reason>")

MetricsExplanationContract = PromptContract(
    task_instruction=(
        "Explain the listed metrics in plain language. Keep every number "
        "exactly as given; do not rank, judge, or extrapolate."),
    output_format="plain prose, one sentence per metric")

ReportPolishContract = PromptContract(
    task_instruction=(
        "Rewrite the Markdown report for readability only. Preserve all "
        "headings, all numbers, all warnings, all limitations, and all "
        "section order. Change wording, never content."),
    output_format="Markdown with the same heading structure")

ClaimRewriteContract = PromptContract(
    task_instruction=(
        "Rewrite the input so it makes no forbidden claim while keeping "
        "the grounded content identical."),
    output_format="plain prose")

_CONTRACTS: Dict[str, PromptContract] = {
    LLMTaskType.PARAPHRASE_RESPONSE: ParaphraseContract,
    LLMTaskType.SUMMARIZE_REPORT: SummaryContract,
    LLMTaskType.SUMMARIZE_TRACE: SummaryContract,
    LLMTaskType.CLASSIFICATION_ASSIST: ClassificationAssistContract,
    LLMTaskType.EXPLAIN_METRICS: MetricsExplanationContract,
    LLMTaskType.OPERATOR_FRIENDLY_STATUS: ParaphraseContract,
    LLMTaskType.REPORT_POLISH: ReportPolishContract,
    LLMTaskType.CLAIM_REWRITE: ClaimRewriteContract,
}


def contract_for(task_type: str) -> PromptContract:
    if task_type not in _CONTRACTS:
        raise KeyError(f"no prompt contract for task {task_type!r}")
    return _CONTRACTS[task_type]


def build_prompt(request: LLMRequest) -> str:
    return contract_for(request.task_type).build(request)
