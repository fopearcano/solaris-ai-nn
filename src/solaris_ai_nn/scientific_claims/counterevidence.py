"""Counterevidence -- evidence against a claim, kept as visible as evidence for it.

:class:`CounterEvidenceAnalyzer` detects counterevidence (failed replication,
falsification failure, passive-parser equivalence, log-accumulation warning,
fixture overfit, human-label dependency, missing live data, failed tests, safety
regression, ClaimGuard failure, contradictory metric, insufficient sample size,
missing artifact, operator uncertainty). Counterevidence is as visible as
evidence, may downgrade or block a claim, and is never ignored for being
inconvenient.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class CounterEvidenceType:
    FAILED_REPLICATION = "failed_replication"
    FALSIFICATION_FAILURE = "falsification_failure"
    PASSIVE_PARSER_EQUIVALENCE = "passive_parser_equivalence"
    LOG_ACCUMULATION_WARNING = "log_accumulation_warning"
    FIXTURE_OVERFIT = "fixture_overfit"
    HUMAN_LABEL_DEPENDENCY = "human_label_dependency"
    MISSING_LIVE_DATA = "missing_live_data"
    FAILED_TESTS = "failed_tests"
    SAFETY_REGRESSION = "safety_regression"
    CLAIMGUARD_FAILURE = "claimguard_failure"
    CONTRADICTORY_METRIC = "contradictory_metric"
    INSUFFICIENT_SAMPLE_SIZE = "insufficient_sample_size"
    MISSING_ARTIFACT = "missing_artifact"
    OPERATOR_UNCERTAINTY = "operator_uncertainty"
    UNKNOWN = "unknown"

    ALL = (FAILED_REPLICATION, FALSIFICATION_FAILURE,
           PASSIVE_PARSER_EQUIVALENCE, LOG_ACCUMULATION_WARNING,
           FIXTURE_OVERFIT, HUMAN_LABEL_DEPENDENCY, MISSING_LIVE_DATA,
           FAILED_TESTS, SAFETY_REGRESSION, CLAIMGUARD_FAILURE,
           CONTRADICTORY_METRIC, INSUFFICIENT_SAMPLE_SIZE, MISSING_ARTIFACT,
           OPERATOR_UNCERTAINTY, UNKNOWN)

    # Counterevidence that blocks (rather than merely downgrades) a claim.
    BLOCKING = (FALSIFICATION_FAILURE, SAFETY_REGRESSION, CLAIMGUARD_FAILURE)


@dataclass
class CounterEvidenceRecord:
    """One piece of counterevidence against a claim (kept fully visible)."""

    counter_type: str
    claim_ref: str = ""
    detail: str = ""
    blocks_claim: bool = False
    source: str = ""

    def __post_init__(self) -> None:
        if self.counter_type not in CounterEvidenceType.ALL:
            self.counter_type = CounterEvidenceType.UNKNOWN
        if self.counter_type in CounterEvidenceType.BLOCKING:
            self.blocks_claim = True

    def to_dict(self) -> Dict[str, Any]:
        return {"counter_type": self.counter_type, "claim_ref": self.claim_ref,
                "detail": self.detail, "blocks_claim": self.blocks_claim,
                "source": self.source, "ignored": False, "visible": True}


@dataclass
class CounterEvidenceAnalyzer:
    """Detects counterevidence from the evidence bundle (recommend-only)."""

    def detect(self, bundle: Dict[str, Any], *,
               claim_ref: str = "") -> List[CounterEvidenceRecord]:
        bundle = bundle or {}
        out: List[CounterEvidenceRecord] = []

        def add(ctype: str, detail: str, source: str = "") -> None:
            out.append(CounterEvidenceRecord(counter_type=ctype,
                                             claim_ref=claim_ref, detail=detail,
                                             source=source))

        repl = bundle.get("replication", {}) or {}
        fals = bundle.get("falsification", {}) or {}
        soak = bundle.get("soak", {}) or {}
        diff = bundle.get("sensorium_differentiation", {}) or {}
        intake = bundle.get("implementation_intake", {}) or {}
        safety = bundle.get("safety", {}) or {}

        if int(repl.get("failed_replication_count", 0) or 0) > 0:
            add(CounterEvidenceType.FAILED_REPLICATION,
                "one or more replication arms failed", "replication_falsification")
        if int(fals.get("falsified_claim_count", 0) or 0) > 0:
            add(CounterEvidenceType.FALSIFICATION_FAILURE,
                "a core claim was falsified", "replication_falsification")
        if diff.get("passive_parser_equivalent") or \
                bundle.get("passive_parser_equivalent"):
            add(CounterEvidenceType.PASSIVE_PARSER_EQUIVALENCE,
                "structure indistinguishable from a passive parser",
                "sensorium_differentiation")
        if soak.get("log_accumulation_warning") or \
                bundle.get("log_accumulation_warning"):
            add(CounterEvidenceType.LOG_ACCUMULATION_WARNING,
                "growth may be log accumulation, not development",
                "developmental_soak")
        if diff.get("fixture_overfit_risk") or bundle.get("fixture_overfit_risk"):
            add(CounterEvidenceType.FIXTURE_OVERFIT,
                "result may be overfit to the fixture", "sensorium_differentiation")
        if diff.get("label_contamination_risk") or \
                bundle.get("label_contamination_risk"):
            add(CounterEvidenceType.HUMAN_LABEL_DEPENDENCY,
                "result may depend on human labels", "sensorium_differentiation")
        if bundle.get("missing_live_data") or \
                (bundle.get("live_field") is not None and not bundle["live_field"]):
            add(CounterEvidenceType.MISSING_LIVE_DATA,
                "no live-field evidence; only fixtures", "live_field")
        if int(intake.get("failed_test_count", 0) or 0) > 0:
            add(CounterEvidenceType.FAILED_TESTS,
                "implementation intake reports failing tests",
                "implementation_intake")
        if int(intake.get("critical_safety_regression_count", 0) or 0) > 0 or \
                int(safety.get("critical_regression_count", 0) or 0) > 0:
            add(CounterEvidenceType.SAFETY_REGRESSION,
                "a critical safety regression is present", "safety_invariants")
        if bundle.get("claimguard_failed"):
            add(CounterEvidenceType.CLAIMGUARD_FAILURE,
                "a generated report failed ClaimGuard", "evaluation")
        for cm in (bundle.get("contradictory_metrics") or []):
            add(CounterEvidenceType.CONTRADICTORY_METRIC,
                str(cm), "evaluation")
        if bundle.get("insufficient_sample_size"):
            add(CounterEvidenceType.INSUFFICIENT_SAMPLE_SIZE,
                "sample size too small to support the claim", "evaluation")
        for ma in (bundle.get("missing_artifacts") or []):
            add(CounterEvidenceType.MISSING_ARTIFACT,
                f"missing artifact: {ma}", "research_cycle")
        if bundle.get("operator_uncertainty"):
            add(CounterEvidenceType.OPERATOR_UNCERTAINTY,
                str(bundle.get("operator_uncertainty")), "operator_notes")
        return out

    @staticmethod
    def summary(records: List[CounterEvidenceRecord]) -> Dict[str, Any]:
        blocking = [r for r in records if r.blocks_claim]
        return {
            "counterevidence_count": len(records),
            "blocking_counterevidence_count": len(blocking),
            "records": [r.to_dict() for r in records],
            "note": "counterevidence is as visible as evidence; it may downgrade "
                    "or block a claim and is never ignored for being inconvenient",
        }
