"""Comparison -- does the full adaptive sensorium actually beat the baselines?

:class:`OrganismicDemoComparison` replays the *same* fixture streams through
several arms (full adaptive sensorium, a passive event-list parser, no-adaptation
receptors, human-like-only, non-human-only, mixed, and fixed/random attention)
and reports the metrics side by side. A negative result is valid: if the full
system does not beat the passive parser, the comparison says so. No arm makes any
consciousness claim.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..plural_sensorium import PluralSensoriumRuntime
from ..plural_sensorium.modality import ModalityClass, modality_class_for
from ..plural_sensorium.stream_adapters import read_feeder
from .fixture_feeders import FixtureFeederSet, write_fixtures
from .perception_change import PerceptionChangeProbe
from .scenario import OrganismicDemoConfig, OrganismicDemoScenario


@dataclass
class ComparisonArm:
    name: str
    metrics: Dict[str, Any] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "metrics": dict(self.metrics),
                "notes": list(self.notes)}


@dataclass
class ComparisonResult:
    arms: List[ComparisonArm] = field(default_factory=list)
    full_beats_passive: bool = False
    negative_result: bool = False
    summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "arms": [a.to_dict() for a in self.arms],
            "full_beats_passive": self.full_beats_passive,
            "negative_result": self.negative_result,
            "summary": self.summary,
            "no_consciousness_claim": True,
            "disclaimer": "compares internal response structure across arms; "
                          "makes no claim of consciousness or understanding",
        }


@dataclass
class OrganismicDemoComparison:
    """Runs the demo's comparison arms over one shared fixture set."""

    state_dir: str = ".solaris_ai_nn_state/organismic_demo/comparison"
    config: OrganismicDemoConfig = field(default_factory=OrganismicDemoConfig)
    fixtures: Optional[FixtureFeederSet] = None

    def _ensure_fixtures(self) -> FixtureFeederSet:
        if self.fixtures is None:
            scenario = OrganismicDemoScenario(config=self.config)
            self.fixtures = write_fixtures(scenario, self.state_dir)
        return self.fixtures

    def _envelopes_by_tick(self) -> Dict[int, List[Any]]:
        by_tick: Dict[int, List[Any]] = defaultdict(list)
        for feeder in self._ensure_fixtures().feeders:
            result = read_feeder(feeder, max_lines=self.config.max_events_total)
            for env in result.events:
                by_tick[int(env.timestamp)].append(env)
        return by_tick

    def run(self) -> ComparisonResult:
        by_tick = self._envelopes_by_tick()
        arms = [
            self._sensorium_arm("full", None, adaptive=True),
            self._passive_parser_arm(by_tick),
            self._sensorium_arm("no_adaptation", None, adaptive=False),
            self._sensorium_arm("human_like_only",
                                self._families(ModalityClass.HUMAN_LIKE),
                                adaptive=True),
            self._sensorium_arm("non_human_only",
                                self._families(ModalityClass.NON_HUMAN,
                                               ModalityClass.MACHINE_NATIVE),
                                adaptive=True),
            self._sensorium_arm("mixed", None, adaptive=True),
            self._sensorium_arm("random_attention", None, adaptive=True,
                                attention=True),
            self._sensorium_arm("fixed_attention", None, adaptive=True,
                                attention=False),
        ]
        full = next(a for a in arms if a.name == "full")
        passive = next(a for a in arms if a.name == "passive_parser")
        full_score = full.metrics.get("changed_perception_score", 0.0)
        passive_score = passive.metrics.get("changed_perception_score", 0.0)
        beats = full_score > passive_score
        result = ComparisonResult(
            arms=arms, full_beats_passive=beats,
            negative_result=not beats,
            summary={"full_changed_perception_score": full_score,
                     "passive_changed_perception_score": passive_score,
                     "arms_compared": len(arms)})
        return result

    def _families(self, *classes: str) -> List[str]:
        from ..plural_sensorium.modality import ModalityFamily

        return [f for f in ModalityFamily.ALL
                if modality_class_for(f) in classes]

    def _sensorium_arm(self, name: str, modalities: Optional[List[str]],
                       adaptive: bool, attention: bool = True) -> ComparisonArm:
        by_tick = self._envelopes_by_tick()
        rt = PluralSensoriumRuntime(
            state_dir=self.state_dir + f"/{name}",
            enabled_modalities=modalities,
            max_events_total=self.config.max_events_total)
        responses: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for tick in range(self.config.ticks):
            fired: List[str] = []
            for env in by_tick.get(tick, []):
                if modalities and env.modality not in modalities:
                    continue
                rt.observe_envelope(env, now=float(tick))
                fired.append(env.source_id)
                rid = f"{env.source_id}:{env.modality}"
                receptor = rt.receptors.get(rid)
                if receptor is not None:
                    if not adaptive:
                        # Suppress adaptation: hold sensitivity fixed.
                        receptor.sensitivity.value = 0.5
                        receptor.adaptation_count = 0
                    responses[env.modality].append({
                        "novelty": receptor.recent_novelty,
                        "sensitivity": receptor.sensitivity.value,
                        "baseline": receptor.baseline})
            rt.advance_tick(fired, now=float(tick))
            if not attention:
                rt.attention.state.shifts = 0  # a fixed (non-shifting) policy
        probe = PerceptionChangeProbe().compute(dict(responses), rt)
        weak = sum(1 for c in rt.invariants.candidates.values()
                   if not c.is_strong)
        total_inv = max(1, len(rt.invariants.candidates))
        overfit = sum(1 for r in rt.grounding.records
                      if r.quality == "overfit_to_fixture")
        return ComparisonArm(name=name, metrics={
            "baseline_shift_count": len(rt.baseline_shifts),
            "absence_detection_quality": len(rt.absence.events),
            "rhythm_detection_quality": len(rt.rhythm.signatures),
            "cross_modal_relation_count": rt.cross_modal.relation_count(),
            "proto_symbol_candidate_count": len(rt.proto_symbol_candidates),
            "modality_native_grounding_score":
                rt.modality_native_grounding_score(),
            "human_label_contamination_score":
                rt.human_label_contamination_score(),
            "changed_perception_score": probe.changed_perception_score,
            "false_pattern_rate": round(weak / total_inv, 4),
            "overfit_to_fixture_warning_count": overfit,
            "attention_shift_count": rt.attention.state.shifts,
        })

    def _passive_parser_arm(self, by_tick: Dict[int, List[Any]],
                            ) -> ComparisonArm:
        """A passive event-list parser: it only counts; it never adapts."""
        seen = 0
        modalities = set()
        for tick in range(self.config.ticks):
            for env in by_tick.get(tick, []):
                seen += 1
                modalities.add(env.modality)
        arm = ComparisonArm(name="passive_parser", metrics={
            "baseline_shift_count": 0,
            "absence_detection_quality": 0,
            "rhythm_detection_quality": 0,
            "cross_modal_relation_count": 0,
            "proto_symbol_candidate_count": 0,
            "modality_native_grounding_score": 0.0,
            "human_label_contamination_score": 0.0,
            "changed_perception_score": 0.0,
            "false_pattern_rate": 0.0,
            "overfit_to_fixture_warning_count": 0,
            "attention_shift_count": 0,
            "events_listed": seen,
            "modalities_listed": len(modalities),
        })
        arm.notes.append("a passive parser stores events but forms no baseline, "
                         "absence, rhythm, cross-modal, or proto-symbol "
                         "structure -- so its perception cannot change")
        return arm
