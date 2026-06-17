"""Live sign contamination filter -- labels annotate, never define a sign.

:class:`LiveSignContaminationFilter` inspects a sign candidate for contamination:
tokens copied from human labels / debug gloss / operator phrases, human-text or
operator-pulse dominance, label/gloss ground-truth dependency, command-like text,
private-data / secret markers in the token, forbidden sources, fixture-marker
leakage, source artifacts, reporting artifacts, and unsupported language claims.
Contaminated signs cannot be born; sign memory never stores private data or secrets
as a token; human labels and debug gloss may annotate but never define a sign; the
operator pulse is stimulus, never teaching.
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
_LANGUAGE_CLAIMS = ("means", "understands", "translation", "definition of",
                    "the word")


class SignContaminationType:
    HUMAN_LABEL_COPY = "human_label_copy"
    DEBUG_GLOSS_COPY = "debug_gloss_copy"
    OPERATOR_PHRASE_COPY = "operator_phrase_copy"
    HUMAN_TEXT_DOMINANCE = "human_text_dominance"
    OPERATOR_PULSE_DOMINANCE = "operator_pulse_dominance"
    LABEL_GROUND_TRUTH_DEPENDENCY = "label_ground_truth_dependency"
    GLOSS_GROUND_TRUTH_DEPENDENCY = "gloss_ground_truth_dependency"
    COMMAND_LIKE_TEXT = "command_like_text"
    PRIVATE_DATA_LEAK = "private_data_leak"
    SECRET_MARKER = "secret_marker"
    FORBIDDEN_SOURCE = "forbidden_source"
    FIXTURE_MARKER_LEAKAGE = "fixture_marker_leakage"
    SOURCE_ARTIFACT = "source_artifact"
    REPORTING_ARTIFACT = "reporting_artifact"
    UNSUPPORTED_LANGUAGE_CLAIM = "unsupported_language_claim"
    UNKNOWN = "unknown"

    ALL = (HUMAN_LABEL_COPY, DEBUG_GLOSS_COPY, OPERATOR_PHRASE_COPY,
           HUMAN_TEXT_DOMINANCE, OPERATOR_PULSE_DOMINANCE,
           LABEL_GROUND_TRUTH_DEPENDENCY, GLOSS_GROUND_TRUTH_DEPENDENCY,
           COMMAND_LIKE_TEXT, PRIVATE_DATA_LEAK, SECRET_MARKER,
           FORBIDDEN_SOURCE, FIXTURE_MARKER_LEAKAGE, SOURCE_ARTIFACT,
           REPORTING_ARTIFACT, UNSUPPORTED_LANGUAGE_CLAIM, UNKNOWN)

# Findings that block sign birth outright (a source artifact only warns).
_NON_BLOCKING = frozenset({SignContaminationType.SOURCE_ARTIFACT})


@dataclass
class SignContaminationFinding:
    """One sign-contamination finding (always recorded, never hidden)."""

    contamination_type: str
    detail: str = ""
    blocks_birth: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {"contamination_type": self.contamination_type,
                "detail": self.detail, "blocks_birth": self.blocks_birth}


@dataclass
class SignContaminationResult:
    """The contamination findings for one sign candidate."""

    sign_id: str
    findings: List[SignContaminationFinding] = field(default_factory=list)

    @property
    def contaminated(self) -> bool:
        return any(f.blocks_birth for f in self.findings)

    @property
    def is_source_artifact(self) -> bool:
        return any(f.contamination_type == SignContaminationType.SOURCE_ARTIFACT
                   for f in self.findings)

    @property
    def types(self) -> List[str]:
        return [f.contamination_type for f in self.findings]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sign_id": self.sign_id, "contaminated": self.contaminated,
            "is_source_artifact": self.is_source_artifact,
            "finding_count": len(self.findings),
            "findings": [f.to_dict() for f in self.findings],
            "note": "contaminated signs cannot be born; tokens never store "
                    "private data/secrets; labels/gloss annotate but never "
                    "define; the operator pulse is stimulus, not teaching",
        }


@dataclass
class LiveSignContaminationFilter:
    """Detects contamination in a sign candidate (token + sources + evidence)."""

    operator_dominance_threshold: float = 0.5
    human_text_dominance_threshold: float = 0.6

    def evaluate(self, *, candidate, concept_contaminated: bool = False,
                 ) -> SignContaminationResult:
        result = SignContaminationResult(sign_id=candidate.sign_id)
        token = str(candidate.private_token).lower()
        alias = str(candidate.debug_alias).lower()
        total = max(1, sum(candidate.source_distribution.values()))

        # Carry over any contamination already flagged by the generator.
        for existing in candidate.contamination_findings:
            result.findings.append(SignContaminationFinding(
                existing, "flagged during sign generation",
                blocks_birth=existing not in _NON_BLOCKING))

        # Token must be a private/opaque identifier, never a secret/command.
        if any(m in token for m in _SECRET_MARKERS):
            result.findings.append(SignContaminationFinding(
                SignContaminationType.SECRET_MARKER,
                "sign token contains a secret/private marker"))
        if any(m in token for m in _COMMAND_MARKERS):
            result.findings.append(SignContaminationFinding(
                SignContaminationType.COMMAND_LIKE_TEXT,
                "sign token contains command-like text"))
        if not token.startswith(("sig_live_", "lσ-", "lΣ-")) and " " in token:
            result.findings.append(SignContaminationFinding(
                SignContaminationType.HUMAN_LABEL_COPY,
                "sign token is not a private/opaque identifier"))

        # The concept it links to must not be contaminated.
        if concept_contaminated:
            result.findings.append(SignContaminationFinding(
                SignContaminationType.SOURCE_ARTIFACT
                if False else SignContaminationType.REPORTING_ARTIFACT,
                "linked proto-concept is contaminated"))

        # Source-distribution dominance.
        op_share = candidate.source_distribution.get(_OPERATOR_PULSE, 0) / total
        if op_share >= self.operator_dominance_threshold:
            result.findings.append(SignContaminationFinding(
                SignContaminationType.OPERATOR_PULSE_DOMINANCE,
                f"operator pulse supplies {op_share:.0%} of support"))
        human_share = sum(candidate.source_distribution.get(s, 0)
                          for s in _HUMAN_TEXT_SOURCES) / total
        if human_share >= self.human_text_dominance_threshold \
                and not candidate.feature_signature_refs:
            result.findings.append(SignContaminationFinding(
                SignContaminationType.HUMAN_TEXT_DOMINANCE,
                f"human-text sources supply {human_share:.0%} of support"))

        # Forbidden source.
        for sid in candidate.source_distribution:
            if sid in FORBIDDEN_FIRST_BIRTH_SOURCES:
                result.findings.append(SignContaminationFinding(
                    SignContaminationType.FORBIDDEN_SOURCE,
                    f"source {sid!r} is on the forbidden list"))

        # Fixture/label markers + unsupported language claims in the alias.
        if any(m in alias for m in _FIXTURE_MARKERS):
            result.findings.append(SignContaminationFinding(
                SignContaminationType.FIXTURE_MARKER_LEAKAGE,
                "fixture/label marker present in debug alias"))
        if any(m in alias for m in _LANGUAGE_CLAIMS):
            result.findings.append(SignContaminationFinding(
                SignContaminationType.UNSUPPORTED_LANGUAGE_CLAIM,
                "debug alias asserts a language/meaning claim"))
        return result

    @staticmethod
    def summary(results: List[SignContaminationResult]) -> Dict[str, Any]:
        types: Dict[str, int] = {}
        for r in results:
            for f in r.findings:
                types[f.contamination_type] = types.get(
                    f.contamination_type, 0) + 1
        return {
            "evaluated_sign_count": len(results),
            "contaminated_sign_count": sum(1 for r in results if r.contaminated),
            "source_artifact_sign_count": sum(1 for r in results
                                              if r.is_source_artifact),
            "contamination_types": types,
            "note": "all contamination findings are recorded and never hidden; "
                    "contaminated signs cannot be born",
        }
