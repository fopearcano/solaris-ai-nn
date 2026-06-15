"""Organismic-demo scenario -- structured but not fully predictable flux.

:class:`OrganismicDemoScenario` generates a bounded, seed-replayable world of
external-feeder events across human-like and non-human modalities. It is *not*
random-only and *not* a perfectly scripted toy world: it contains repeating
rhythms with jitter, missing expected events, delayed cross-modal events, noise
bursts, source silence, a baseline shift, weak recurring patterns, false
patterns, and ambiguous coincidences. The fixtures are a controlled rehearsal for
later real feeder streams -- they are not the theory.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple


class OrganismicDemoPhase:
    BASELINE_EXPOSURE = "baseline_exposure"
    RHYTHM_ESTABLISHMENT = "rhythm_establishment"
    CROSS_MODAL_COUPLING = "cross_modal_coupling"
    ABSENCE_DISRUPTION = "absence_disruption"
    NOVELTY_INJECTION = "novelty_injection"
    RECOVERY = "recovery"
    CHANGED_PERCEPTION_PROBE = "changed_perception_probe"
    REPORT_ONLY = "report_only"

    ALL = (BASELINE_EXPOSURE, RHYTHM_ESTABLISHMENT, CROSS_MODAL_COUPLING,
           ABSENCE_DISRUPTION, NOVELTY_INJECTION, RECOVERY,
           CHANGED_PERCEPTION_PROBE, REPORT_ONLY)


@dataclass
class OrganismicDemoConfig:
    """Bounded configuration for one demo run (seed-replayable)."""

    ticks: int = 120
    max_runtime_s: float = 60.0
    max_events_total: int = 500
    seed: int = 7
    fixture_mode: bool = True
    real_read_only_mode: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


# Feeder file names and the modality each carries.
FEEDER_FILES = {
    "human_text_log.jsonl": ["human_textual"],
    "light_temperature_stream.jsonl": ["light", "ordinary_temperature"],
    "rf_feature_stream.jsonl": ["radio_frequency"],
    "echo_feature_stream.jsonl": ["ultrasound_echo"],
    "vibration_stream.jsonl": ["vibration"],
    "magnetic_stream.jsonl": ["magnetic"],
    "absence_schedule.jsonl": ["absence_silence"],
}
DEBUG_TRUTH_FILE = "cross_modal_truth_debug.jsonl"


def _phase_for_tick(tick: int, ticks: int) -> str:
    frac = tick / max(1, ticks)
    if frac < 0.17:
        return OrganismicDemoPhase.BASELINE_EXPOSURE
    if frac < 0.37:
        return OrganismicDemoPhase.RHYTHM_ESTABLISHMENT
    if frac < 0.58:
        return OrganismicDemoPhase.CROSS_MODAL_COUPLING
    if frac < 0.75:
        return OrganismicDemoPhase.ABSENCE_DISRUPTION
    if frac < 0.88:
        return OrganismicDemoPhase.NOVELTY_INJECTION
    return OrganismicDemoPhase.RECOVERY


@dataclass
class OrganismicDemoScenario:
    """Generates the structured-but-uncertain flux for the demo."""

    config: OrganismicDemoConfig = field(default_factory=OrganismicDemoConfig)

    def generate(self) -> Tuple[Dict[str, List[Dict[str, Any]]],
                                List[Dict[str, Any]]]:
        """Return (feeder_events_by_file, debug_truth_records)."""
        rng = random.Random(self.config.seed)
        streams: Dict[str, List[Dict[str, Any]]] = {
            name: [] for name in FEEDER_FILES}
        debug: List[Dict[str, Any]] = []
        ticks = self.config.ticks

        def emit(file_name: str, modality: str, features: Dict[str, Any],
                 tick: int, annotation=None) -> None:
            rec = {"modality": modality, "ts": float(tick), **features}
            if annotation is not None:
                rec["annotation"] = annotation
                rec["annotation_status"] = "external_non_ground_truth"
            streams[file_name].append(rec)

        rf_period = 4
        for tick in range(ticks):
            phase = _phase_for_tick(tick, ticks)

            # -- Human-like streams (valid, never privileged) ----------------
            if phase != OrganismicDemoPhase.ABSENCE_DISRUPTION or tick % 3:
                # A textual environmental log line (observation, not command).
                if rng.random() < 0.7:
                    emit("human_text_log.jsonl", "human_textual",
                         {"length": float(20 + rng.randint(0, 30)),
                          "token_count": float(4 + rng.randint(0, 8))},
                         tick, annotation=f"ambient log line {tick}")
            emit("light_temperature_stream.jsonl", "light",
                 {"lux": round(0.5 + 0.1 * rng.random(), 3)}, tick)
            if tick % 2 == 0:
                emit("light_temperature_stream.jsonl", "ordinary_temperature",
                     {"celsius": round(21.0 + 0.5 * rng.random(), 3)}, tick)

            # -- RF rhythm with jitter --------------------------------------
            rf_fires = (tick % rf_period == 0) and not (
                phase == OrganismicDemoPhase.ABSENCE_DISRUPTION
                and tick % (rf_period * 2) == 0)  # missing expected RF bursts
            if phase == OrganismicDemoPhase.BASELINE_EXPOSURE:
                rf_fires = rng.random() < 0.4
            if rf_fires:
                jitter = rng.uniform(-0.2, 0.2)
                power = round(0.7 + jitter, 3)
                emit("rf_feature_stream.jsonl", "radio_frequency",
                     {"power": power, "band": round(2.4 + 0.1 * rng.random(),
                                                    3)}, tick)
                # Cross-modal truth: RF tends to PRECEDE vibration by 1 tick.
                if phase in (OrganismicDemoPhase.CROSS_MODAL_COUPLING,
                             OrganismicDemoPhase.RECOVERY) and rng.random() < 0.8:
                    emit("vibration_stream.jsonl", "vibration",
                         {"amp": round(0.4 + 0.1 * rng.random(), 3)}, tick + 1)
                    debug.append({"relation": "rf_precedes_vibration",
                                  "rf_tick": tick, "vibration_tick": tick + 1})

            # -- Vibration rhythm (stops during absence) --------------------
            if phase in (OrganismicDemoPhase.RHYTHM_ESTABLISHMENT,) \
                    and tick % 3 == 0:
                emit("vibration_stream.jsonl", "vibration",
                     {"amp": round(0.4 + 0.05 * rng.random(), 3)}, tick)

            # -- Echo / radar-like reflections ------------------------------
            if phase != OrganismicDemoPhase.ABSENCE_DISRUPTION \
                    and rng.random() < 0.5:
                emit("echo_feature_stream.jsonl", "ultrasound_echo",
                     {"boundary": round(1.0 + 0.3 * rng.random(), 3),
                      "reflectivity": round(0.5 + 0.2 * rng.random(), 3)}, tick)
                # thermal/light drift tends to coincide with echo change.
                if phase == OrganismicDemoPhase.CROSS_MODAL_COUPLING:
                    emit("light_temperature_stream.jsonl", "light",
                         {"lux": round(0.8 + 0.1 * rng.random(), 3)}, tick)
                    debug.append({"relation": "echo_coincides_light",
                                  "tick": tick})

            # -- Magnetic drift with a mid-run anomaly (a baseline shift) ----
            mid = ticks // 2
            if mid <= tick < mid + 3:
                # An abrupt magnetic anomaly large enough to shift the baseline.
                field_val = round(1.6 + 0.1 * rng.random(), 3)
            else:
                drift = 0.0 if tick < mid else 0.5
                field_val = round(0.2 + drift + 0.05 * rng.random(), 3)
            emit("magnetic_stream.jsonl", "magnetic", {"field": field_val}, tick)

            # -- Absence schedule (records observed silence windows) --------
            if phase == OrganismicDemoPhase.ABSENCE_DISRUPTION and tick % 4 == 0:
                emit("absence_schedule.jsonl", "absence_silence",
                     {"silent_sources": 1.0}, tick)

            # -- Novelty injection: noise bursts + false/ambiguous patterns -
            if phase == OrganismicDemoPhase.NOVELTY_INJECTION:
                if rng.random() < 0.5:
                    emit("rf_feature_stream.jsonl", "radio_frequency",
                         {"power": round(2.0 + rng.random(), 3),
                          "band": round(5.0 + rng.random(), 3)}, tick)
                if rng.random() < 0.3:  # a false (one-off) "pattern"
                    emit("echo_feature_stream.jsonl", "ultrasound_echo",
                         {"boundary": round(9.0 + rng.random(), 3),
                          "reflectivity": 0.99}, tick)

        return streams, debug

    def phases(self) -> List[str]:
        return list(OrganismicDemoPhase.ALL)
