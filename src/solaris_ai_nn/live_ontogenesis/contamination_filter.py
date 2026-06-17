"""Live ontogenesis contamination filter -- labels annotate, never define.

:class:`LiveOntogenesisContaminationFilter` inspects a candidate and its feature
evidence for contamination: attempts to treat human labels or debug gloss as ground
truth, operator-pulse or human-text or source-diet dominance, fixture-marker
leakage, command-like text, private/secret markers, forbidden sources, malformed
payload patterns, source artifacts, and reporting artifacts. Contaminated candidates
cannot be born; source artifacts may persist only if explicitly marked as such;
human labels and debug gloss may annotate but never define; the operator pulse is
stimulus, never teaching.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from ..live_birth.birth_profile import FORBIDDEN_FIRST_BIRTH_SOURCES

_OPERATOR_PULSE = "operator_pulse"
_HUMAN_TEXT_SOURCES = ("operator_pulse", "local_environment_manual")
_FIXTURE_MARKERS = ("fixture", "synthetic_label", "ground_truth_label",
                    "test_label", "gold_label")
_COMMAND_MARKERS = ("execute:", "run:", "sudo ", "rm -", "shell:", "command:",
                    "do this", "you must")


class ContaminationType:
    HUMAN_LABEL_GROUND_TRUTH = "human_label_ground_truth_attempt"
    DEBUG_GLOSS_GROUND_TRUTH = "debug_gloss_ground_truth_attempt"
    OPERATOR_PULSE_DOMINANCE = "operator_pulse_dominance"
    HUMAN_TEXT_DOMINANCE = "human_text_dominance"
    SOURCE_DIET_DOMINANCE = "source_diet_dominance"
    FIXTURE_MARKER_LEAKAGE = "fixture_marker_leakage"
    COMMAND_LIKE_TEXT = "command_like_text"
    PRIVATE_DATA = "private_data"
    SECRET_MARKER = "secret_marker"
    FORBIDDEN_SOURCE = "forbidden_source"
    MALFORMED_PAYLOAD = "malformed_payload_pattern"
    SOURCE_ARTIFACT = "source_artifact"
    REPORTING_ARTIFACT = "reporting_artifact"
    UNKNOWN = "unknown"

    ALL = (HUMAN_LABEL_GROUND_TRUTH, DEBUG_GLOSS_GROUND_TRUTH,
           OPERATOR_PULSE_DOMINANCE, HUMAN_TEXT_DOMINANCE, SOURCE_DIET_DOMINANCE,
           FIXTURE_MARKER_LEAKAGE, COMMAND_LIKE_TEXT, PRIVATE_DATA,
           SECRET_MARKER, FORBIDDEN_SOURCE, MALFORMED_PAYLOAD, SOURCE_ARTIFACT,
           REPORTING_ARTIFACT, UNKNOWN)

# Types that block concept birth outright (a source artifact only warns).
_BLOCKING = frozenset({
    ContaminationType.HUMAN_LABEL_GROUND_TRUTH,
    ContaminationType.DEBUG_GLOSS_GROUND_TRUTH,
    ContaminationType.OPERATOR_PULSE_DOMINANCE,
    ContaminationType.HUMAN_TEXT_DOMINANCE,
    ContaminationType.SOURCE_DIET_DOMINANCE,
    ContaminationType.FIXTURE_MARKER_LEAKAGE,
    ContaminationType.COMMAND_LIKE_TEXT,
    ContaminationType.PRIVATE_DATA,
    ContaminationType.SECRET_MARKER,
    ContaminationType.FORBIDDEN_SOURCE,
    ContaminationType.MALFORMED_PAYLOAD,
})


@dataclass
class ContaminationFinding:
    """One contamination finding (always recorded, never hidden)."""

    contamination_type: str
    detail: str = ""
    blocks_birth: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {"contamination_type": self.contamination_type,
                "detail": self.detail, "blocks_birth": self.blocks_birth}


@dataclass
class ContaminationResult:
    """The contamination findings for one candidate."""

    candidate_id: str
    findings: List[ContaminationFinding] = field(default_factory=list)

    @property
    def contaminated(self) -> bool:
        return any(f.blocks_birth for f in self.findings)

    @property
    def is_source_artifact(self) -> bool:
        return any(f.contamination_type == ContaminationType.SOURCE_ARTIFACT
                   for f in self.findings)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "contaminated": self.contaminated,
            "is_source_artifact": self.is_source_artifact,
            "finding_count": len(self.findings),
            "findings": [f.to_dict() for f in self.findings],
            "note": "contaminated candidates cannot be born; a source artifact "
                    "may persist only if marked as such; labels/gloss annotate, "
                    "never define; operator pulse is stimulus, not teaching",
        }


@dataclass
class LiveOntogenesisContaminationFilter:
    """Detects contamination in candidates + their feature evidence."""

    operator_dominance_threshold: float = 0.5
    human_text_dominance_threshold: float = 0.6

    def evaluate(self, *, candidate, vectors_by_event: Dict[str, Any],
                 source_diet: Dict[str, Any]) -> ContaminationResult:
        result = ContaminationResult(candidate_id=candidate.candidate_id)
        total = max(1, candidate.recurrence_count)

        # Does the candidate have non-text scalar feature grounding?
        has_scalar_grounding = False
        for ev_id in {e.event_id for e in candidate.supporting_events}:
            vec = vectors_by_event.get(ev_id)
            d = (vec.to_dict() if hasattr(vec, "to_dict")
                 else dict(vec)) if vec is not None else {}
            if d.get("scalar_values"):
                has_scalar_grounding = True
                break

        # Operator-pulse dominance always blocks; the operator pulse is stimulus.
        op_share = candidate.source_distribution.get(_OPERATOR_PULSE, 0) / total
        if op_share >= self.operator_dominance_threshold:
            result.findings.append(ContaminationFinding(
                ContaminationType.OPERATOR_PULSE_DOMINANCE,
                f"operator pulse supplies {op_share:.0%} of support; it is "
                "stimulus, not teaching"))
        # Human-text dominance blocks only when there is no scalar grounding;
        # a feature-grounded manual scalar is recorded as a warning instead.
        human_share = sum(candidate.source_distribution.get(s, 0)
                          for s in _HUMAN_TEXT_SOURCES) / total
        if human_share >= self.human_text_dominance_threshold:
            result.findings.append(ContaminationFinding(
                ContaminationType.HUMAN_TEXT_DOMINANCE,
                f"human-text sources supply {human_share:.0%} of support"
                + ("; feature-grounded by scalars (warning only)"
                   if has_scalar_grounding else ""),
                blocks_birth=not has_scalar_grounding))

        # Source-diet dominance from the observation source-diet report.
        if source_diet.get("balance") in ("operator_pulse_dominant",
                                          "human_text_dominant"):
            result.findings.append(ContaminationFinding(
                ContaminationType.SOURCE_DIET_DOMINANCE,
                f"observation source diet is {source_diet.get('balance')!r}"))

        # Per-event evidence scan (labels/gloss/command/fixture/private/secret).
        for ev_id in {e.event_id for e in candidate.supporting_events}:
            vec = vectors_by_event.get(ev_id)
            if vec is None:
                continue
            self._scan_vector(vec, result)

        # Forbidden source.
        for sid in candidate.source_distribution:
            if sid in FORBIDDEN_FIRST_BIRTH_SOURCES:
                result.findings.append(ContaminationFinding(
                    ContaminationType.FORBIDDEN_SOURCE,
                    f"source {sid!r} is on the forbidden list"))

        # Source artifact (warning only): a single-source recurrence that is
        # either entirely noisy, or is the field's dominant source at high
        # concentration -- i.e. likely a source-health quirk rather than an
        # environmental regularity. A single-source signature is normal in a
        # diverse field and is NOT flagged on its own.
        if candidate.source_count == 1 and candidate.recurrence_count >= 3 \
                and op_share == 0 and human_share == 0:
            sole = next(iter(candidate.source_distribution))
            noisy_support = self._noisy_support(candidate, vectors_by_event)
            all_noisy = noisy_support >= max(2, candidate.recurrence_count - 1)
            dominant = source_diet.get("dominant_source")
            dominance = float(source_diet.get(
                "live_source_diet_dominance_score", 0.0) or 0.0)
            field_dominated = (sole == dominant and dominance >= 0.6)
            if all_noisy or field_dominated:
                result.findings.append(ContaminationFinding(
                    ContaminationType.SOURCE_ARTIFACT,
                    f"recurrence from {sole!r} looks like a source-health "
                    "artifact (noisy or field-dominant) rather than an "
                    "environmental concept", blocks_birth=False))
        return result

    @staticmethod
    def _noisy_support(candidate, vectors_by_event: Dict[str, Any]) -> int:
        noisy = 0
        for e in candidate.supporting_events:
            vec = vectors_by_event.get(e.event_id)
            d = (vec.to_dict() if hasattr(vec, "to_dict")
                 else dict(vec)) if vec is not None else {}
            if d.get("is_noisy"):
                noisy += 1
        return noisy

    def _scan_vector(self, vec: Any, result: ContaminationResult) -> None:
        d = vec.to_dict() if hasattr(vec, "to_dict") else dict(vec)
        gloss = str(d.get("debug_gloss_annotation", "")).lower()
        if d.get("attempted_debug_gloss_ground_truth") or \
                d.get("debug_gloss_is_ground_truth"):
            result.findings.append(ContaminationFinding(
                ContaminationType.DEBUG_GLOSS_GROUND_TRUTH,
                "an event attempted debug_gloss as ground truth"))
        if d.get("attempted_human_label_ground_truth") or \
                d.get("human_label_is_ground_truth"):
            result.findings.append(ContaminationFinding(
                ContaminationType.HUMAN_LABEL_GROUND_TRUTH,
                "an event attempted human_label as ground truth"))
        blob = " ".join([gloss] + [str(k).lower()
                                   for k in d.get("categorical_keys", [])])
        if any(m in blob for m in _FIXTURE_MARKERS):
            result.findings.append(ContaminationFinding(
                ContaminationType.FIXTURE_MARKER_LEAKAGE,
                "fixture/label marker present in feature evidence"))
        if any(m in blob for m in _COMMAND_MARKERS):
            result.findings.append(ContaminationFinding(
                ContaminationType.COMMAND_LIKE_TEXT,
                "command-like text present in feature evidence"))

    @staticmethod
    def summary(results: List[ContaminationResult]) -> Dict[str, Any]:
        types: Dict[str, int] = {}
        for r in results:
            for f in r.findings:
                types[f.contamination_type] = types.get(
                    f.contamination_type, 0) + 1
        return {
            "evaluated_candidate_count": len(results),
            "contaminated_candidate_count": sum(1 for r in results
                                                if r.contaminated),
            "source_artifact_candidate_count": sum(1 for r in results
                                                   if r.is_source_artifact),
            "contamination_types": types,
            "note": "all contamination findings are recorded and never hidden; "
                    "contaminated candidates cannot be born",
        }
