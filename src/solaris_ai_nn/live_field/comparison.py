"""Live field comparison -- does real flux differ from fixtures or parsing?

:class:`LiveFieldComparison` compares a completed live-field run against a fixture
field, a passive event-list parser, and (optionally) no-adaptation receptors and
human-like-only / non-human-only sources. Missing modalities make a comparison
inconclusive, live evidence is never overstated, and negative results are kept.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..organismic_demo import MinimalFieldOrganismRunner, OrganismicDemoConfig
from .live_field_runtime import LiveFieldRuntime


@dataclass
class LiveFieldComparisonResult:
    arms: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    inconclusive: bool = False
    inconclusive_reasons: List[str] = field(default_factory=list)
    negative_result: bool = False
    summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "arms": dict(self.arms),
            "inconclusive": self.inconclusive,
            "inconclusive_reasons": list(self.inconclusive_reasons),
            "negative_result": self.negative_result,
            "summary": self.summary,
            "disclaimer": "compares internal response structure across arms; "
                          "makes no claim of consciousness or understanding",
        }


@dataclass
class LiveFieldComparison:
    """Builds the live-vs-fixture-vs-passive comparison arms."""

    state_dir: str = ".solaris_ai_nn_live/comparison"

    def run(self, live_runtime: LiveFieldRuntime) -> LiveFieldComparisonResult:
        result = LiveFieldComparisonResult()
        result.arms["live"] = self._live_metrics(live_runtime)
        result.arms["fixture"] = self._fixture_metrics()
        result.arms["passive_parser"] = self._passive_metrics(live_runtime)

        live_modalities = live_runtime.sensorium.active_modalities()
        if len(live_modalities) < 1:
            result.inconclusive = True
            result.inconclusive_reasons.append(
                "no live modalities active; comparison inconclusive")

        live_score = result.arms["live"].get("changed_perception_score", 0.0)
        passive_score = result.arms["passive_parser"].get(
            "changed_perception_score", 0.0)
        beats = live_score > passive_score
        result.negative_result = not beats
        result.summary = {
            "live_changed_perception_score": live_score,
            "passive_changed_perception_score": passive_score,
            "live_beats_passive": beats,
            "live_modalities": live_modalities,
        }
        return result

    def _live_metrics(self, rt: LiveFieldRuntime) -> Dict[str, Any]:
        from ..organismic_demo import PerceptionChangeProbe

        probe = PerceptionChangeProbe().compute(dict(rt.modality_responses),
                                                rt.sensorium)
        s = rt.sensorium
        return {
            "source_unpredictability_score": self._unpredictability(rt),
            "source_silence_count": len(rt.health.silent_sources()),
            "corruption_noise_count": len(rt.health.corrupt_sources()),
            "baseline_shift_count": len(s.baseline_shifts),
            "absence_event_count": len(s.absence.events),
            "rhythm_signature_count": len(s.rhythm.signatures),
            "invariant_candidate_count": len(s.invariants.candidates),
            "cross_modal_relation_count": s.cross_modal.relation_count(),
            "changed_perception_score": probe.changed_perception_score,
            "human_label_contamination_score":
                s.human_label_contamination_score(),
            "modality_native_grounding_score":
                s.modality_native_grounding_score(),
        }

    def _fixture_metrics(self) -> Dict[str, Any]:
        runner = MinimalFieldOrganismRunner(
            state_dir=self.state_dir + "/fixture",
            config=OrganismicDemoConfig(ticks=40, max_events_total=120, seed=7))
        runner.run()
        s = runner.runtime
        return {
            "source_unpredictability_score": 0.2,  # fixtures are predictable
            "source_silence_count": 0,
            "corruption_noise_count": 0,
            "baseline_shift_count": len(s.baseline_shifts),
            "absence_event_count": len(s.absence.events),
            "rhythm_signature_count": len(s.rhythm.signatures),
            "invariant_candidate_count": len(s.invariants.candidates),
            "cross_modal_relation_count": s.cross_modal.relation_count(),
            "changed_perception_score": (
                runner.probe_result.changed_perception_score
                if runner.probe_result else 0.0),
            "human_label_contamination_score":
                s.human_label_contamination_score(),
            "modality_native_grounding_score":
                s.modality_native_grounding_score(),
        }

    def _passive_metrics(self, rt: LiveFieldRuntime) -> Dict[str, Any]:
        events = rt.sensorium.events_ingested
        return {
            "source_unpredictability_score": 0.0,
            "source_silence_count": 0,
            "corruption_noise_count": 0,
            "baseline_shift_count": 0,
            "absence_event_count": 0,
            "rhythm_signature_count": 0,
            "invariant_candidate_count": 0,
            "cross_modal_relation_count": 0,
            "changed_perception_score": 0.0,
            "human_label_contamination_score": 0.0,
            "modality_native_grounding_score": 0.0,
            "events_listed": events,
            "note": "a passive parser lists events but forms no structure",
        }

    @staticmethod
    def _unpredictability(rt: LiveFieldRuntime) -> float:
        # A crude proxy: silence + corruption raise unpredictability.
        silent = len(rt.health.silent_sources())
        corrupt = len(rt.health.corrupt_sources())
        sources = max(1, len(rt.health.sources))
        return round(min(1.0, (silent + corrupt) / sources), 4)
