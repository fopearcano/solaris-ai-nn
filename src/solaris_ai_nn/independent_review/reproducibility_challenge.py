"""Reproducibility challenge -- instructions a reviewer could run, never executed.

:class:`ReproducibilityChallengeBuilder` generates the challenges an external
reviewer would run to reproduce bounded demos and controls (fixture demo,
scientific claim report, safe abstract, falsification replay, passive-parser /
no-metabolism / no-semiogenesis controls, shuffled order, random labels, growth-vs-
accumulation, ClaimGuard scan, safety invariant scan). It generates instructions
only -- it executes nothing -- and every challenge lists expected artifacts and
how to interpret failure. Missing prerequisites mark a challenge unavailable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class ChallengeType:
    FIXTURE_DEMO = "fixture_demo_reproduction"
    SCIENTIFIC_CLAIM_REPORT = "scientific_claim_report_reproduction"
    SAFE_ABSTRACT = "safe_abstract_reproduction"
    FALSIFICATION_REPLAY = "falsification_replay"
    PASSIVE_PARSER_CONTROL = "passive_parser_control_comparison"
    NO_METABOLISM_CONTROL = "no_metabolism_control_comparison"
    NO_SEMIOGENESIS_CONTROL = "no_semiogenesis_control_comparison"
    SHUFFLED_EVENT_ORDER = "shuffled_event_order_test"
    RANDOM_LABELS_SAME_FEATURES = "random_labels_same_features_test"
    GROWTH_VS_ACCUMULATION = "growth_vs_accumulation_check"
    CLAIMGUARD_SCAN = "claimguard_scan"
    SAFETY_INVARIANT_SCAN = "safety_invariant_scan"

    ALL = (FIXTURE_DEMO, SCIENTIFIC_CLAIM_REPORT, SAFE_ABSTRACT,
           FALSIFICATION_REPLAY, PASSIVE_PARSER_CONTROL, NO_METABOLISM_CONTROL,
           NO_SEMIOGENESIS_CONTROL, SHUFFLED_EVENT_ORDER,
           RANDOM_LABELS_SAME_FEATURES, GROWTH_VS_ACCUMULATION, CLAIMGUARD_SCAN,
           SAFETY_INVARIANT_SCAN)


class ChallengeStatus:
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    INCONCLUSIVE = "inconclusive"

    ALL = (AVAILABLE, UNAVAILABLE, INCONCLUSIVE)


# challenge -> (command instruction, prerequisite bundle key, expected artifact).
_SPECS = {
    ChallengeType.FIXTURE_DEMO: (
        "python examples/run_minimal_field_organism_demo.py",
        "research_baseline", "organism demo trace + metrics"),
    ChallengeType.SCIENTIFIC_CLAIM_REPORT: (
        "python examples/run_scientific_claims_demo.py",
        "scientific_claims", "SCIENTIFIC_CLAIM_REPORT.md/.json"),
    ChallengeType.SAFE_ABSTRACT: (
        "python examples/run_safe_abstract_demo.py",
        "scientific_claims", "SAFE_ABSTRACTS.md"),
    ChallengeType.FALSIFICATION_REPLAY: (
        "python examples/run_falsification_demo.py",
        "falsification", "falsification report; falsified claims preserved"),
    ChallengeType.PASSIVE_PARSER_CONTROL: (
        "compare full run vs passive-parser control arm",
        "replication", "control arm metrics; equivalence => counterevidence"),
    ChallengeType.NO_METABOLISM_CONTROL: (
        "compare full run vs no-metabolism ablation",
        "replication", "ablation metrics; no-effect => weaker claim"),
    ChallengeType.NO_SEMIOGENESIS_CONTROL: (
        "compare full run vs no-semiogenesis ablation",
        "replication", "ablation metrics; no-effect => weaker claim"),
    ChallengeType.SHUFFLED_EVENT_ORDER: (
        "re-run with shuffled temporal order",
        "soak", "prediction effect should vanish if it was temporal"),
    ChallengeType.RANDOM_LABELS_SAME_FEATURES: (
        "re-run with random labels, identical features",
        "soak", "structure surviving random labels => label-independent"),
    ChallengeType.GROWTH_VS_ACCUMULATION: (
        "compare growth metric vs raw log size over time",
        "soak", "growth tracking log size => log accumulation, not development"),
    ChallengeType.CLAIMGUARD_SCAN: (
        "run ClaimGuard over all generated reports",
        "scientific_claims", "ClaimGuard clean; any finding blocks readiness"),
    ChallengeType.SAFETY_INVARIANT_SCAN: (
        "run the safety invariant check",
        "safety", "all invariants hold; any failure blocks the claim"),
}


@dataclass
class ChallengeExpectedResult:
    """What a reviewer should see, and how to read a failure."""

    expected_artifact: str
    failure_interpretation: str

    def to_dict(self) -> Dict[str, Any]:
        return {"expected_artifact": self.expected_artifact,
                "failure_interpretation": self.failure_interpretation}


@dataclass
class ChallengeStep:
    """One reproducibility challenge (instruction only; never executed)."""

    challenge_type: str
    command: str
    prerequisite: str
    expected: ChallengeExpectedResult
    status: str = ChallengeStatus.AVAILABLE
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"challenge_type": self.challenge_type, "command": self.command,
                "prerequisite": self.prerequisite,
                "expected": self.expected.to_dict(), "status": self.status,
                "detail": self.detail, "executed": False}


@dataclass
class ReproducibilityChallenge:
    """The full challenge set (instructions only; executes nothing)."""

    steps: List[ChallengeStep] = field(default_factory=list)

    @property
    def available(self) -> List[ChallengeStep]:
        return [s for s in self.steps if s.status == ChallengeStatus.AVAILABLE]

    @property
    def unavailable(self) -> List[ChallengeStep]:
        return [s for s in self.steps if s.status == ChallengeStatus.UNAVAILABLE]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reproducibility_challenge_count": len(self.steps),
            "available_challenge_count": len(self.available),
            "unavailable_challenge_count": len(self.unavailable),
            "steps": [s.to_dict() for s in self.steps],
            "note": "challenges are instructions only; nothing is executed; "
                    "missing prerequisite artifacts mark a challenge unavailable",
        }


@dataclass
class ReproducibilityChallengeBuilder:
    """Builds reproducibility challenges from the available evidence bundle."""

    def build(self, bundle: Dict[str, Any], *,
              max_challenges: int = 50) -> ReproducibilityChallenge:
        bundle = bundle or {}
        challenge = ReproducibilityChallenge()
        for ctype in ChallengeType.ALL[:max_challenges]:
            command, prereq, expected = _SPECS[ctype]
            available = bool(bundle.get(prereq))
            challenge.steps.append(ChallengeStep(
                challenge_type=ctype, command=command, prerequisite=prereq,
                expected=ChallengeExpectedResult(
                    expected_artifact=expected,
                    failure_interpretation=(
                        "a failure or null result is itself a finding; record "
                        "it as counterevidence, not as an error to hide")),
                status=(ChallengeStatus.AVAILABLE if available
                        else ChallengeStatus.UNAVAILABLE),
                detail=("" if available
                        else f"prerequisite {prereq!r} artifact is missing")))
        return challenge
