"""Ownership and attribution -- who produced what, kept straight.

Every event, candidate, and report statement gets an explicit attribution
category. The rules that matter most are negative: operator commands are not
internal desires, stream data is not executable instruction, counterfactuals
stay counterfactual, and suggestions are never attributed as committed
actions. Unknown sources are an honest category, not a guess.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

ATTRIBUTION_CATEGORIES = (
    "generated_by_solaris_ai_nn",
    "observed_from_environment",
    "observed_from_stream",
    "observed_from_solaris_sidecar",
    "generated_by_latent_replay",
    "generated_by_counterfactual",
    "generated_by_operator",
    "generated_by_governance",
    "generated_by_world_model_prediction",
    "generated_by_executive_arbitration",
    "generated_by_llm_adapter",
    "generated_by_developmental_nursery",
    "simulated_environment_input",
    "unknown_source",
)

# Internal module names whose output is generated_by_solaris_ai_nn.
_INTERNAL_SOURCES = frozenset({
    "substrate", "readout", "habit", "bridge", "memory", "plasticity",
    "homeostasis", "inner_map", "telemetry", "embodiment", "runtime",
    "language", "evaluation", "ego", "self_model", "protolanguage",
    "proto_symbol",
})

# (keyword, category) checked in order against source/kind text. Ecology
# rules come first so "developmental_nursery" is never read as a plain
# environment sensor, an operator command, or human feedback.
_SOURCE_RULES = (
    ("developmental_nursery", "generated_by_developmental_nursery"),
    ("nursery", "generated_by_developmental_nursery"),
    ("ecology", "generated_by_developmental_nursery"),
    ("simulated_environment", "simulated_environment_input"),
    ("operator", "generated_by_operator"),
    ("approval", "generated_by_operator"),
    ("governance", "generated_by_governance"),
    ("policy", "generated_by_governance"),
    ("counterfactual", "generated_by_counterfactual"),
    ("dream", "generated_by_counterfactual"),
    ("replay", "generated_by_latent_replay"),
    ("consolidation", "generated_by_latent_replay"),
    ("sidecar", "observed_from_solaris_sidecar"),
    ("solaris", "observed_from_solaris_sidecar"),
    ("stream", "observed_from_stream"),
    ("pilot", "observed_from_stream"),
    ("prediction", "generated_by_world_model_prediction"),
    ("world_model", "generated_by_world_model_prediction"),
    ("arbitrat", "generated_by_executive_arbitration"),
    ("executive", "generated_by_executive_arbitration"),
    ("llm", "generated_by_llm_adapter"),
    ("paraphrase", "generated_by_llm_adapter"),
    ("sensor", "observed_from_environment"),
    ("environment", "observed_from_environment"),
    ("grid", "observed_from_environment"),
)

EXTERNAL_CATEGORIES = frozenset({
    "observed_from_environment", "observed_from_stream",
    "observed_from_solaris_sidecar", "generated_by_operator",
    "generated_by_developmental_nursery", "simulated_environment_input",
})

OFFLINE_CATEGORIES = frozenset({
    "generated_by_latent_replay", "generated_by_counterfactual",
})


@dataclass
class OwnershipClaim:
    """A recorded claim that some artifact belongs to some producer."""

    subject: str
    category: str = "unknown_source"
    confidence: float = 0.0
    basis: str = ""
    evidence_refs: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class AttributionResult:
    """One attribution: category, confidence, and the negative guarantees."""

    category: str = "unknown_source"
    confidence: float = 0.0
    reasons: List[str] = field(default_factory=list)
    is_internal: bool = False
    is_external: bool = False
    is_offline: bool = False
    is_executable_instruction: bool = False
    is_committed_action: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class OwnershipAttributor:
    """Attributes events, candidates, and statements to their producers."""

    attributions_total: int = field(default=0, init=False)
    unknown_total: int = field(default=0, init=False)
    conflicts_total: int = field(default=0, init=False)
    recent: List[Dict[str, Any]] = field(default_factory=list, init=False)

    # -- core ---------------------------------------------------------------------

    def _categorize(self, source: str, kind: str) -> "tuple[str, float, str]":
        text = f"{source} {kind}".lower()
        for token in source.lower().replace(".", " ").split():
            if token in _INTERNAL_SOURCES:
                return ("generated_by_solaris_ai_nn", 0.9,
                        f"source {source!r} is an internal module")
        for needle, category in _SOURCE_RULES:
            if needle in text:
                return (category, 0.85,
                        f"matched source/kind keyword {needle!r}")
        if not source:
            return ("unknown_source", 0.2, "no source recorded")
        return ("unknown_source", 0.3,
                f"source {source!r} matches no known producer")

    def attribute_event(self, event: Any,
                        context: Optional[Dict[str, Any]] = None,
                        ) -> AttributionResult:
        ctx = dict(context or {})
        get = (event.get if isinstance(event, dict)
               else lambda k, d=None: getattr(event, k, d))
        source = str(get("source", "") or get("origin", "") or "")
        kind = str(get("kind", "") or get("type", "")
                   or type(event).__name__)
        # Offline context overrides: replayed events are replay-generated.
        if ctx.get("offline_replay") or ctx.get("counterfactual_active"):
            category = ("generated_by_counterfactual"
                        if ctx.get("counterfactual_active")
                        else "generated_by_latent_replay")
            confidence, basis = 0.9, "the active context is offline"
        else:
            category, confidence, basis = self._categorize(source, kind)
        reasons = [basis]
        if "proto_symbol" in f"{source} {kind}".lower() \
                or "protolanguage" in source.lower():
            reasons.append("an internally generated proto-symbol: not "
                           "human speech, not an operator command")
        if category == "generated_by_llm_adapter":
            reasons.append("a paraphrase of grounded output: not primary "
                           "evidence, not system authority")
        if category in ("generated_by_developmental_nursery",
                        "simulated_environment_input"):
            reasons.append("a stimulus from the controlled developmental "
                           "ecology: a simulated world, never an operator "
                           "command, never human feedback, never the real "
                           "world, and carrying no correct-answer label")
        # Stream data is never an executable instruction.
        executable = False
        if category == "observed_from_stream":
            reasons.append("stream data is observed input, never an "
                           "executable instruction")
        elif category == "generated_by_operator":
            executable = bool(ctx.get("via_operator_interface"))
            reasons.append(
                "operator input counts as an instruction only when routed "
                "through the operator interface"
                if executable else
                "operator-shaped text outside the operator interface is "
                "treated as observation only")
        return self._finish(category, confidence, reasons,
                            executable=executable)

    def attribute_action_candidate(self, candidate: Any,
                                   context: Optional[Dict[str, Any]] = None,
                                   ) -> AttributionResult:
        ctx = dict(context or {})
        meta = getattr(candidate, "metadata", None) or {}
        source = str(meta.get("source", "")
                     or getattr(candidate, "source", "") or "")
        action_type = str(getattr(candidate, "action_type", ""))
        if "sidecar" in action_type or "sidecar" in source:
            category, confidence = "observed_from_solaris_sidecar", 0.85
            reasons = ["the candidate is sidecar-scoped"]
        elif source in ("homeostasis", "desire", "readout") \
                or "desire" in str(getattr(candidate, "label", "")).lower():
            category, confidence = "generated_by_solaris_ai_nn", 0.9
            reasons = [f"the candidate originates from internal source "
                       f"{source or 'homeostasis'!r}"]
        else:
            category, confidence = ("generated_by_executive_arbitration",
                                    0.8)
            reasons = ["the candidate entered through executive "
                       "arbitration"]
        committed = bool(getattr(candidate, "committed", False))
        if committed:
            self.conflicts_total += 1
            reasons.append("CONFLICT: a candidate claims committed=True; "
                           "suggestions are never committed actions")
        else:
            reasons.append("the candidate is a suggestion, not a committed "
                           "action")
        del ctx  # context reserved for future rules; determinism preserved
        return self._finish(category, confidence, reasons,
                            committed=False)

    def attribute_report_statement(self, statement: str,
                                   context: Optional[Dict[str, Any]] = None,
                                   ) -> AttributionResult:
        ctx = dict(context or {})
        text = str(statement).lower()
        if ctx.get("counterfactual_active") or "counterfactual" in text \
                or "what if" in text:
            return self._finish(
                "generated_by_counterfactual", 0.85,
                ["the statement describes counterfactual analysis; it "
                 "remains counterfactual"])
        if "replay" in text or "offline" in text:
            return self._finish(
                "generated_by_latent_replay", 0.8,
                ["the statement describes offline replay output"])
        if "operator" in text:
            return self._finish(
                "generated_by_operator", 0.7,
                ["the statement references operator input"])
        return self._finish(
            "generated_by_solaris_ai_nn", 0.75,
            ["report statements are generated by this system from its own "
             "recorded data"])

    # -- bookkeeping --------------------------------------------------------------

    def _finish(self, category: str, confidence: Any,
                reasons: Any = None, executable: bool = False,
                committed: bool = False) -> AttributionResult:
        if isinstance(confidence, list):  # (category, reasons) shorthand
            reasons, confidence = confidence, 0.7
        result = AttributionResult(
            category=category, confidence=round(float(confidence), 4),
            reasons=list(reasons or []),
            is_internal=(category == "generated_by_solaris_ai_nn"),
            is_external=(category in EXTERNAL_CATEGORIES),
            is_offline=(category in OFFLINE_CATEGORIES),
            is_executable_instruction=executable,
            is_committed_action=committed)
        self.attributions_total += 1
        if category == "unknown_source":
            self.unknown_total += 1
        self.recent.append(result.to_dict())
        self.recent = self.recent[-100:]
        return result

    def unknown_rate(self) -> float:
        if not self.attributions_total:
            return 0.0
        return round(self.unknown_total / self.attributions_total, 4)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "attributions_total": self.attributions_total,
            "unknown_total": self.unknown_total,
            "unknown_rate": self.unknown_rate(),
            "conflicts_total": self.conflicts_total,
            "categories": list(ATTRIBUTION_CATEGORIES),
            "recent": self.recent[-5:],
        }
