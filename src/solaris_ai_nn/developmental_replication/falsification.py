"""Falsification lab -- would the claimed structure survive a null condition?

The falsification lab challenges developmental claims with bounded null
conditions: shuffled event order, random labels / same features, same labels /
random features, no recurrence, silent source, passive parser, pure log
accumulation, fixture/human-label overfit probes, simulation-as-observation, and
module ablations. It uses existing artifacts or synthetic fixtures and *never
modifies the original evidence*. A claim that survives a falsification test is
*not* thereby proven; a claim that fails is made visible. Passing a test does not
prove consciousness or understanding.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .cross_run_alignment import _jaccard


class FalsificationTestType:
    SHUFFLED_EVENT_ORDER = "shuffled_event_order"
    RANDOM_LABELS_SAME_FEATURES = "random_labels_same_features"
    SAME_LABELS_RANDOM_FEATURES = "same_labels_random_features"
    NO_RECURRENCE_STREAM = "no_recurrence_stream"
    SILENT_SOURCE_CONTROL = "silent_source_control"
    PASSIVE_PARSER_COMPARISON = "passive_parser_comparison"
    LOG_ACCUMULATION_NULL = "log_accumulation_null"
    FIXTURE_OVERFIT_PROBE = "fixture_overfit_probe"
    HUMAN_LABEL_OVERFIT_PROBE = "human_label_overfit_probe"
    SIMULATION_AS_OBSERVATION_PROBE = "simulation_as_observation_probe"
    NO_ACTION_REACTION_CONTROL = "no_action_reaction_control"
    NO_METABOLISM_CONTROL = "no_metabolism_control"

    ALL = (SHUFFLED_EVENT_ORDER, RANDOM_LABELS_SAME_FEATURES,
           SAME_LABELS_RANDOM_FEATURES, NO_RECURRENCE_STREAM,
           SILENT_SOURCE_CONTROL, PASSIVE_PARSER_COMPARISON,
           LOG_ACCUMULATION_NULL, FIXTURE_OVERFIT_PROBE,
           HUMAN_LABEL_OVERFIT_PROBE, SIMULATION_AS_OBSERVATION_PROBE,
           NO_ACTION_REACTION_CONTROL, NO_METABOLISM_CONTROL)


class FalsificationOutcome:
    PASSED = "passed"          # the claimed structure survived the challenge
    FALSIFIED = "falsified"    # the claim did NOT survive -- it is falsified
    INCONCLUSIVE = "inconclusive"

    ALL = (PASSED, FALSIFIED, INCONCLUSIVE)


# Each test's guiding question (reported verbatim for honesty).
_QUESTIONS = {
    FalsificationTestType.SHUFFLED_EVENT_ORDER:
        "does shuffled time destroy prediction?",
    FalsificationTestType.RANDOM_LABELS_SAME_FEATURES:
        "does the system form concepts from features instead of labels?",
    FalsificationTestType.SAME_LABELS_RANDOM_FEATURES:
        "does structure follow labels rather than features?",
    FalsificationTestType.NO_RECURRENCE_STREAM:
        "does growth disappear when recurrence disappears?",
    FalsificationTestType.SILENT_SOURCE_CONTROL:
        "does claimed structure still appear under a silent source?",
    FalsificationTestType.PASSIVE_PARSER_COMPARISON:
        "does passive parsing produce the same report?",
    FalsificationTestType.LOG_ACCUMULATION_NULL:
        "would the claimed structure appear from pure log accumulation?",
    FalsificationTestType.FIXTURE_OVERFIT_PROBE:
        "is the structure an artifact of one fixture?",
    FalsificationTestType.HUMAN_LABEL_OVERFIT_PROBE:
        "is the structure driven by human labels?",
    FalsificationTestType.SIMULATION_AS_OBSERVATION_PROBE:
        "does the system confuse simulation with observation?",
    FalsificationTestType.NO_ACTION_REACTION_CONTROL:
        "does action-reaction learning actually contribute?",
    FalsificationTestType.NO_METABOLISM_CONTROL:
        "does perceptual metabolism actually contribute?",
}


@dataclass
class FalsificationFinding:
    """One observation produced while running a falsification test."""

    statement: str
    evidence_refs: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"statement": self.statement,
                "evidence_refs": list(self.evidence_refs)}


@dataclass
class FalsificationResult:
    """The bounded outcome of one falsification test (originals untouched)."""

    test_type: str
    question: str
    outcome: str
    claim: str = ""
    findings: List[FalsificationFinding] = field(default_factory=list)
    original_modified: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_type": self.test_type, "question": self.question,
            "outcome": self.outcome, "claim": self.claim,
            "findings": [f.to_dict() for f in self.findings],
            "original_modified": self.original_modified,
            "note": ("passing a falsification test does not prove consciousness "
                     "or understanding; a failed claim is made visible"),
        }


@dataclass
class FalsificationTest:
    """Runs a single bounded falsification test against run profiles (copies)."""

    def run(self, test_type: str, *, run_profile: Dict[str, Any],
            null_profile: Optional[Dict[str, Any]] = None) -> FalsificationResult:
        if test_type not in FalsificationTestType.ALL:
            raise ValueError(f"unknown falsification test {test_type!r}")
        # Always operate on copies so the original evidence is never modified.
        run = dict(run_profile or {})
        null = dict(null_profile or {})
        question = _QUESTIONS[test_type]
        handler = getattr(self, f"_{test_type}")
        outcome, claim, findings = handler(run, null)
        return FalsificationResult(test_type=test_type, question=question,
                                   outcome=outcome, claim=claim,
                                   findings=findings, original_modified=False)

    # -- individual tests -----------------------------------------------------

    def _shuffled_event_order(self, run, null):
        base = _f(run.get("durable_prediction_improvement_score"))
        shuffled = _f(null.get("durable_prediction_improvement_score"))
        claim = "prediction depends on real temporal structure"
        if base is None:
            return self._incon(claim, "no prediction score available")
        if null:
            outcome = (FalsificationOutcome.PASSED if shuffled < base * 0.6
                       else FalsificationOutcome.FALSIFIED)
            note = (f"prediction {base} -> {shuffled} under shuffle"
                    if outcome == FalsificationOutcome.PASSED else
                    f"prediction survived shuffle ({base} -> {shuffled})")
            return outcome, claim, [_finding(note, ["null:shuffled_order"])]
        return self._incon(claim, "no shuffled-order null profile supplied")

    def _random_labels_same_features(self, run, null):
        a = run.get("concept_family_distribution") or {}
        b = null.get("concept_family_distribution")
        claim = "concepts form from features, not labels"
        if not a:
            return self._incon(claim, "no concept families available")
        if b is not None:
            overlap = _jaccard(a, b)
            outcome = (FalsificationOutcome.PASSED if overlap >= 0.6
                       else FalsificationOutcome.FALSIFIED)
            return outcome, claim, [_finding(
                f"concept-family overlap under random labels: {overlap:.2f}",
                ["null:random_labels"])]
        return self._incon(claim, "no random-label null profile supplied")

    def _same_labels_random_features(self, run, null):
        a = run.get("concept_family_distribution") or {}
        b = null.get("concept_family_distribution")
        claim = "structure follows features, not labels"
        if not a or b is None:
            return self._incon(claim, "insufficient profiles for the probe")
        overlap = _jaccard(a, b)
        # If structure persists when features are randomized but labels kept,
        # it was label-driven -> falsified.
        outcome = (FalsificationOutcome.FALSIFIED if overlap >= 0.6
                   else FalsificationOutcome.PASSED)
        return outcome, claim, [_finding(
            f"concept overlap when features randomized: {overlap:.2f}",
            ["null:random_features"])]

    def _no_recurrence_stream(self, run, null):
        base = run.get("structural_growth_status")
        null_status = null.get("structural_growth_status")
        claim = "growth depends on real recurrence"
        if base is None:
            return self._incon(claim, "no growth verdict available")
        if null_status is not None:
            grew_null = null_status == "real_structural_growth"
            outcome = (FalsificationOutcome.FALSIFIED if grew_null
                       else FalsificationOutcome.PASSED)
            return outcome, claim, [_finding(
                f"growth under no-recurrence null: {null_status}",
                ["null:no_recurrence"])]
        return self._incon(claim, "no no-recurrence null profile supplied")

    def _silent_source_control(self, run, null):
        claim = "structure does not appear under a silent source"
        null_growth = null.get("structural_growth_status")
        if null_growth is None:
            return self._incon(claim, "no silent-source null profile supplied")
        outcome = (FalsificationOutcome.FALSIFIED
                   if null_growth == "real_structural_growth"
                   else FalsificationOutcome.PASSED)
        return outcome, claim, [_finding(
            f"growth under silent source: {null_growth}",
            ["null:silent_source"])]

    def _passive_parser_comparison(self, run, null):
        claim = "the stack produces more structure than a passive parser"
        a = run.get("sign_family_distribution") or run.get(
            "concept_family_distribution") or {}
        b = null.get("sign_family_distribution") or null.get(
            "concept_family_distribution")
        if not a or b is None:
            return self._incon(claim, "no passive-parser comparison available")
        overlap = _jaccard(a, b)
        # If the passive parser reproduces the same families, the stack added
        # nothing -> falsified.
        outcome = (FalsificationOutcome.FALSIFIED if overlap >= 0.85
                   else FalsificationOutcome.PASSED)
        return outcome, claim, [_finding(
            f"passive-parser family overlap: {overlap:.2f}",
            ["control:passive_parser"])]

    def _log_accumulation_null(self, run, null):
        claim = "growth is not mere log accumulation"
        status = run.get("structural_growth_status")
        if status is None:
            return self._incon(claim, "no growth verdict available")
        outcome = (FalsificationOutcome.FALSIFIED
                   if status in ("mere_event_accumulation", "log_bloat")
                   else FalsificationOutcome.PASSED
                   if status == "real_structural_growth"
                   else FalsificationOutcome.INCONCLUSIVE)
        return outcome, claim, [_finding(
            f"growth verdict: {status}", ["developmental_life:status"])]

    def _fixture_overfit_probe(self, run, null):
        claim = "the structure is not a fixture artifact"
        status = run.get("structural_growth_status")
        outcome = (FalsificationOutcome.FALSIFIED if status == "fixture_overfit"
                   else FalsificationOutcome.PASSED
                   if status == "real_structural_growth"
                   else FalsificationOutcome.INCONCLUSIVE)
        return outcome, claim, [_finding(
            f"growth verdict: {status}", ["developmental_life:status"])]

    def _human_label_overfit_probe(self, run, null):
        claim = "the structure is not driven by human labels"
        sig = run.get("world_signature", run)
        contamination = _f(sig.get("human_label_contamination_score"),
                           run.get("human_label_exposure"))
        status = run.get("structural_growth_status")
        if status == "human_label_overfit" or (contamination or 0) >= 0.6:
            return (FalsificationOutcome.FALSIFIED, claim, [_finding(
                f"human-label contamination/overfit ({contamination}, {status})",
                ["null:human_label"])])
        if contamination is None and status is None:
            return self._incon(claim, "no contamination evidence available")
        return (FalsificationOutcome.PASSED, claim, [_finding(
            f"low human-label dependence ({contamination})",
            ["null:human_label"])])

    def _simulation_as_observation_probe(self, run, null):
        claim = "the system does not confuse simulation with observation"
        sig = run.get("world_signature", run)
        integrity = _f(sig.get("simulation_boundary_integrity"))
        if integrity is None:
            return self._incon(claim, "no boundary-integrity evidence")
        outcome = (FalsificationOutcome.PASSED if integrity >= 0.6
                   else FalsificationOutcome.FALSIFIED)
        return outcome, claim, [_finding(
            f"simulation boundary integrity: {integrity}",
            ["self_boundary:integrity"])]

    def _no_action_reaction_control(self, run, null):
        return self._ablation(run, null, "action-reaction",
                              "durable_action_effect_learning_score")

    def _no_metabolism_control(self, run, null):
        return self._ablation(run, null, "perceptual metabolism",
                              "composite_growth")

    def _ablation(self, run, null, label, key):
        claim = f"{label} contributes to development"
        base = _f(run.get(key))
        ablated = _f(null.get(key))
        if base is None:
            return self._incon(claim, f"no {key} available")
        if null:
            outcome = (FalsificationOutcome.PASSED if ablated < base * 0.8
                       else FalsificationOutcome.FALSIFIED)
            return outcome, claim, [_finding(
                f"{key} {base} -> {ablated} when {label} ablated",
                [f"ablation:{label}"])]
        return self._incon(claim, f"no {label} ablation profile supplied")

    @staticmethod
    def _incon(claim, why):
        return (FalsificationOutcome.INCONCLUSIVE, claim,
                [_finding(why, ["falsification:inconclusive"])])


def _finding(statement: str, refs: List[str]) -> FalsificationFinding:
    return FalsificationFinding(statement=statement, evidence_refs=list(refs))


def _f(*vals):
    for v in vals:
        if isinstance(v, (int, float)):
            return float(v)
    return None
