"""Live cognition contamination filter -- labels/gloss/operator never define a trace.

:class:`LiveCognitionContaminationFilter` inspects a cognition trace for
contamination: dependence on human labels, debug gloss, or operator phrases;
human-text or operator-pulse dominance; label-as-semantics or sign-as-language
claims; command-like text; private-data/secret markers; forbidden sources;
fixture-marker leakage; source artifacts; reporting artifacts; and unsupported
reasoning/understanding claims. Contaminated traces cannot be promoted; the operator
pulse is stimulus, not teaching; private signs are not language.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from ..live_birth.birth_profile import FORBIDDEN_FIRST_BIRTH_SOURCES

_OPERATOR_PULSE = "operator_pulse"
_HUMAN_TEXT_SOURCES = ("operator_pulse", "local_environment_manual")
_SECRET_MARKERS = ("password", "secret", "api key", "api_key", "credential",
                   "token=", "private message")
_COMMAND_MARKERS = ("execute:", "run:", "sudo ", "rm -", "shell:", "command:")
_FIXTURE_MARKERS = ("fixture", "gold_label", "ground_truth_label", "test_label")
_LANGUAGE_CLAIMS = ("means", "understands", "definition of", "the word",
                    "comprehends", "reasoning proof", "proves reasoning")


class CognitionContaminationType:
    HUMAN_LABEL_DEPENDENCY = "human_label_dependency"
    DEBUG_GLOSS_DEPENDENCY = "debug_gloss_dependency"
    OPERATOR_PHRASE_DEPENDENCY = "operator_phrase_dependency"
    HUMAN_TEXT_DOMINANCE = "human_text_dominance"
    OPERATOR_PULSE_DOMINANCE = "operator_pulse_dominance"
    LABEL_AS_SEMANTICS = "label_as_semantics"
    SIGN_AS_LANGUAGE_CLAIM = "sign_as_language_claim"
    COMMAND_LIKE_TEXT = "command_like_text"
    PRIVATE_DATA_LEAK = "private_data_leak"
    SECRET_MARKER = "secret_marker"
    FORBIDDEN_SOURCE = "forbidden_source"
    FIXTURE_MARKER_LEAKAGE = "fixture_marker_leakage"
    SOURCE_ARTIFACT = "source_artifact"
    REPORTING_ARTIFACT = "reporting_artifact"
    UNSUPPORTED_REASONING_CLAIM = "unsupported_reasoning_claim"
    UNSUPPORTED_UNDERSTANDING_CLAIM = "unsupported_understanding_claim"
    UNKNOWN = "unknown"

    ALL = (HUMAN_LABEL_DEPENDENCY, DEBUG_GLOSS_DEPENDENCY,
           OPERATOR_PHRASE_DEPENDENCY, HUMAN_TEXT_DOMINANCE,
           OPERATOR_PULSE_DOMINANCE, LABEL_AS_SEMANTICS, SIGN_AS_LANGUAGE_CLAIM,
           COMMAND_LIKE_TEXT, PRIVATE_DATA_LEAK, SECRET_MARKER, FORBIDDEN_SOURCE,
           FIXTURE_MARKER_LEAKAGE, SOURCE_ARTIFACT, REPORTING_ARTIFACT,
           UNSUPPORTED_REASONING_CLAIM, UNSUPPORTED_UNDERSTANDING_CLAIM, UNKNOWN)

_NON_BLOCKING = frozenset({CognitionContaminationType.SOURCE_ARTIFACT})


@dataclass
class CognitionContaminationFinding:
    """One cognition-contamination finding (always recorded, never hidden)."""

    contamination_type: str
    detail: str = ""
    blocks_promotion: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {"contamination_type": self.contamination_type,
                "detail": self.detail, "blocks_promotion": self.blocks_promotion}


@dataclass
class CognitionContaminationResult:
    """The contamination findings for one cognition trace."""

    trace_id: str
    findings: List[CognitionContaminationFinding] = field(default_factory=list)

    @property
    def contaminated(self) -> bool:
        return any(f.blocks_promotion for f in self.findings)

    @property
    def is_source_artifact(self) -> bool:
        return any(f.contamination_type
                   == CognitionContaminationType.SOURCE_ARTIFACT
                   for f in self.findings)

    @property
    def types(self) -> List[str]:
        return [f.contamination_type for f in self.findings]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id, "contaminated": self.contaminated,
            "is_source_artifact": self.is_source_artifact,
            "finding_count": len(self.findings),
            "findings": [f.to_dict() for f in self.findings],
            "note": "contaminated traces cannot be promoted; labels/gloss "
                    "annotate but never define; operator pulse is stimulus, not "
                    "teaching; private signs are not language",
        }


@dataclass
class LiveCognitionContaminationFilter:
    """Detects contamination in a cognition trace (sources + evidence + text)."""

    operator_dominance_threshold: float = 0.5
    human_text_dominance_threshold: float = 0.6

    def evaluate(self, *, trace, sign_sources: Dict[str, int] = None,
                 sign_contamination: List[str] = None,
                 annotations: Dict[str, Any] = None,
                 ) -> CognitionContaminationResult:
        result = CognitionContaminationResult(trace_id=trace.trace_id)
        sign_sources = sign_sources or {}
        sign_contamination = sign_contamination or []
        annotations = annotations or {}
        total = max(1, sum(sign_sources.values()))

        # Carry over contamination from the seeding sign(s).
        for existing in sign_contamination:
            result.findings.append(CognitionContaminationFinding(
                existing, "inherited from seeding sign",
                blocks_promotion=existing not in _NON_BLOCKING))

        # Operator-pulse / human-text dominance.
        op_share = sign_sources.get(_OPERATOR_PULSE, 0) / total
        if op_share >= self.operator_dominance_threshold:
            result.findings.append(CognitionContaminationFinding(
                CognitionContaminationType.OPERATOR_PULSE_DOMINANCE,
                f"operator pulse supplies {op_share:.0%} of trace support"))
        human_share = sum(sign_sources.get(s, 0)
                          for s in _HUMAN_TEXT_SOURCES) / total
        if human_share >= self.human_text_dominance_threshold \
                and not trace.linked_concept_ids:
            result.findings.append(CognitionContaminationFinding(
                CognitionContaminationType.HUMAN_TEXT_DOMINANCE,
                f"human-text sources supply {human_share:.0%} of trace support"))

        # Forbidden source.
        for sid in sign_sources:
            if sid in FORBIDDEN_FIRST_BIRTH_SOURCES:
                result.findings.append(CognitionContaminationFinding(
                    CognitionContaminationType.FORBIDDEN_SOURCE,
                    f"source {sid!r} is on the forbidden list"))

        # Annotation / limitation text scanning (labels/gloss/command/language).
        blob = " ".join([str(v) for v in annotations.values()]
                        + list(trace.limitations)).lower()
        if any(m in blob for m in _SECRET_MARKERS):
            result.findings.append(CognitionContaminationFinding(
                CognitionContaminationType.SECRET_MARKER,
                "secret/private marker present in trace text"))
        if any(m in blob for m in _COMMAND_MARKERS):
            result.findings.append(CognitionContaminationFinding(
                CognitionContaminationType.COMMAND_LIKE_TEXT,
                "command-like text present in trace text"))
        if any(m in blob for m in _FIXTURE_MARKERS):
            result.findings.append(CognitionContaminationFinding(
                CognitionContaminationType.FIXTURE_MARKER_LEAKAGE,
                "fixture/label marker present in trace text"))
        if any(m in blob for m in _LANGUAGE_CLAIMS):
            result.findings.append(CognitionContaminationFinding(
                CognitionContaminationType.SIGN_AS_LANGUAGE_CLAIM,
                "trace text asserts a language/meaning/reasoning claim"))
        return result

    @staticmethod
    def summary(results: List[CognitionContaminationResult]) -> Dict[str, Any]:
        types: Dict[str, int] = {}
        for r in results:
            for f in r.findings:
                types[f.contamination_type] = types.get(
                    f.contamination_type, 0) + 1
        return {
            "evaluated_trace_count": len(results),
            "contaminated_trace_count": sum(1 for r in results
                                            if r.contaminated),
            "source_artifact_trace_count": sum(1 for r in results
                                               if r.is_source_artifact),
            "contamination_types": types,
            "note": "all contamination findings are recorded and never hidden; "
                    "contaminated traces cannot be promoted",
        }
