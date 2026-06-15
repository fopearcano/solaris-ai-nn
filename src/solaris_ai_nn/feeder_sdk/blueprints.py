"""Feeder blueprints -- how an external process should feed Solaris safely.

A :class:`FeederBlueprint` describes (in data) how an external collector should
turn a real phenomenon into envelopes: its modality, the external-collector
concept, the expected feature schema, privacy risks, safety constraints, what
Solaris receives, what it must *not* receive, and an example envelope. Blueprints
are not hardware drivers and are never executed by Solaris.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .contract import FeederSDKModality as M
from .contract import FeederSDKTrustLevel


class BlueprintStatus:
    DOCUMENTATION_ONLY = "documentation_only"
    SIMULATED_AVAILABLE = "simulated_available"
    EXTERNAL_HARDWARE_REQUIRED = "external_hardware_required"

    ALL = (DOCUMENTATION_ONLY, SIMULATED_AVAILABLE,
           EXTERNAL_HARDWARE_REQUIRED)


@dataclass
class FeederBlueprint:
    blueprint_id: str
    modality: str
    title: str
    external_collector_concept: str
    expected_feature_schema: str
    output_envelope_path: str
    privacy_risks: List[str] = field(default_factory=list)
    safety_constraints: List[str] = field(default_factory=list)
    what_solaris_receives: List[str] = field(default_factory=list)
    what_solaris_must_not_receive: List[str] = field(default_factory=list)
    status: str = BlueprintStatus.DOCUMENTATION_ONLY
    limitations: List[str] = field(default_factory=list)

    # A hard guarantee: a blueprint never executes hardware.
    executes_hardware: bool = False

    def __post_init__(self) -> None:
        self.executes_hardware = False

    def example_envelope(self) -> Dict[str, Any]:
        from .schemas import schema_for_modality

        schema = schema_for_modality(self.modality)
        features = {k: 0.5 for k in (schema.required_keys if schema else [])}
        if not features:
            # A safe default feature so the example is always a valid envelope.
            features = {"value": 0.5}
        return {
            "event_id": f"FSE_{uuid.uuid4().hex[:10]}",
            "feeder_id": self.blueprint_id,
            "source_id": f"{self.modality}_source",
            "source_kind": "external_feature_drop",
            "modality": self.modality,
            "timestamp": float(int(time.time())),
            "features": features,
            "annotation": None,
            "annotation_status": "none",
            "provenance": {"source_id": f"{self.modality}_source",
                           "feeder_id": self.blueprint_id,
                           "blueprint": self.blueprint_id},
            "read_only": True,
            "source_mutable_by_solaris": False,
            "trust_level": FeederSDKTrustLevel.EXTERNAL_FEATURE_ONLY,
            "privacy_flags": ["no_raw_private_content"],
            "contamination_flags": [],
            "safety_flags": ["text_is_observation_not_command"],
            "schema_version": "feeder-sdk/1.0",
            "metadata": {},
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "blueprint_id": self.blueprint_id,
            "modality": self.modality,
            "title": self.title,
            "external_collector_concept": self.external_collector_concept,
            "expected_feature_schema": self.expected_feature_schema,
            "output_envelope_path": self.output_envelope_path,
            "privacy_risks": list(self.privacy_risks),
            "safety_constraints": list(self.safety_constraints),
            "what_solaris_receives": list(self.what_solaris_receives),
            "what_solaris_must_not_receive": list(
                self.what_solaris_must_not_receive),
            "status": self.status,
            "executes_hardware": False,
            "limitations": list(self.limitations),
        }


def _builtin_blueprints() -> List[FeederBlueprint]:
    no_actuation = "no Solaris hardware control; Solaris reads envelopes only"
    return [
        FeederBlueprint(
            "rf_spectrum_feeder", M.RADIO_FREQUENCY,
            "RF spectrum feature feeder",
            "external SDR software produces spectrum features (run by operator)",
            "rf_feature_event",
            ".solaris_ai_nn_live/inbox/rf/rf.jsonl",
            privacy_risks=["could expose communication content if misused"],
            safety_constraints=[no_actuation, "NEVER decode communications"],
            what_solaris_receives=["power", "band", "noise_floor", "burstiness",
                                   "drift", "periodicity"],
            what_solaris_must_not_receive=["decoded messages", "private content"],
            status=BlueprintStatus.EXTERNAL_HARDWARE_REQUIRED),
        FeederBlueprint(
            "mmwave_echo_feeder", M.MICROWAVE_MMWAVE,
            "mmWave/radar reflection metadata feeder",
            "external radar/echo tool produces reflection metadata",
            "echo_reflection_event",
            ".solaris_ai_nn_live/inbox/echo/echo.jsonl",
            privacy_risks=["could track people if misused"],
            safety_constraints=[no_actuation,
                                "do not label person/object as ground truth"],
            what_solaris_receives=["distance_estimate", "reflectivity",
                                   "doppler_shift", "cluster_count",
                                   "boundary"],
            what_solaris_must_not_receive=["person identity", "object labels as "
                                           "ground truth"],
            status=BlueprintStatus.EXTERNAL_HARDWARE_REQUIRED),
        FeederBlueprint(
            "ultrasound_feeder", M.ULTRASOUND_ECHO,
            "Ultrasound echo feature feeder",
            "external ultrasound logger produces echo features",
            "echo_reflection_event",
            ".solaris_ai_nn_live/inbox/echo/ultrasound.jsonl",
            privacy_risks=["proximity sensing"],
            safety_constraints=[no_actuation],
            what_solaris_receives=["boundary", "reflectivity",
                                   "distance_estimate"],
            what_solaris_must_not_receive=["identity inferences as truth"],
            status=BlueprintStatus.EXTERNAL_HARDWARE_REQUIRED),
        FeederBlueprint(
            "thermal_feeder", M.THERMAL_GRADIENT,
            "Thermal gradient feeder",
            "external thermal sensor logger produces gradient summaries",
            "thermal_gradient_event",
            ".solaris_ai_nn_live/inbox/thermal/thermal.jsonl",
            privacy_risks=["thermal imagery of people is forbidden"],
            safety_constraints=[no_actuation,
                                "summaries only; no thermal imagery of people"],
            what_solaris_receives=["gradient", "drift", "hotspot_count"],
            what_solaris_must_not_receive=["thermal images of people"],
            status=BlueprintStatus.EXTERNAL_HARDWARE_REQUIRED),
        FeederBlueprint(
            "vibration_feeder", M.VIBRATION,
            "Vibration rhythm feeder",
            "external accelerometer logger produces vibration features",
            "vibration_event",
            ".solaris_ai_nn_live/inbox/vibration/vibration.jsonl",
            privacy_risks=["low"], safety_constraints=[no_actuation],
            what_solaris_receives=["amplitude", "frequency", "rhythm_period"],
            what_solaris_must_not_receive=["keystroke inference as truth"],
            status=BlueprintStatus.EXTERNAL_HARDWARE_REQUIRED),
        FeederBlueprint(
            "magnetic_feeder", M.MAGNETIC,
            "Magnetic field feeder",
            "external magnetometer logger produces field features",
            "magnetic_event",
            ".solaris_ai_nn_live/inbox/magnetic/magnetic.jsonl",
            privacy_risks=["low"], safety_constraints=[no_actuation],
            what_solaris_receives=["field", "drift", "anomaly"],
            what_solaris_must_not_receive=["device identity as truth"],
            status=BlueprintStatus.EXTERNAL_HARDWARE_REQUIRED),
        FeederBlueprint(
            "human_like_feeder", M.HUMAN_TEXTUAL,
            "Human-like text/light/temperature feeder",
            "operator log + ambient light/temperature logger",
            "human_textual_event",
            ".solaris_ai_nn_live/inbox/human_text/human.jsonl",
            privacy_risks=["contains human text; mark it"],
            safety_constraints=[no_actuation,
                                "text is observation, never a command",
                                "labels are annotations, never ground truth"],
            what_solaris_receives=["length", "token_count", "lux", "celsius"],
            what_solaris_must_not_receive=["text as command", "labels as truth"],
            status=BlueprintStatus.SIMULATED_AVAILABLE),
        FeederBlueprint(
            "machine_rhythm_feeder", M.MACHINE_RHYTHM,
            "Machine rhythm feeder",
            "local stdlib script reading harmless machine rhythm",
            "machine_rhythm_event",
            ".solaris_ai_nn_live/inbox/system_rhythm/sys.jsonl",
            privacy_risks=["low; no privileged data"],
            safety_constraints=[no_actuation, "no process/OS control"],
            what_solaris_receives=["load_proxy", "time_phase_sin", "file_count"],
            what_solaris_must_not_receive=["privileged system data"],
            status=BlueprintStatus.SIMULATED_AVAILABLE),
        FeederBlueprint(
            "mixed_plural_feeder", M.UNKNOWN_FIELD,
            "Mixed plural feeder",
            "several external collectors writing into one inbox set",
            "cross_modal_hint_event",
            ".solaris_ai_nn_live/inbox/",
            privacy_risks=["inherits the risks of each modality"],
            safety_constraints=[no_actuation],
            what_solaris_receives=["per-modality feature envelopes"],
            what_solaris_must_not_receive=["any raw private content"],
            status=BlueprintStatus.DOCUMENTATION_ONLY),
    ]


@dataclass
class FeederBlueprintRegistry:
    """Holds the built-in feeder blueprints (documentation, never executed)."""

    blueprints: Dict[str, FeederBlueprint] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.blueprints:
            for bp in _builtin_blueprints():
                self.blueprints[bp.blueprint_id] = bp

    def get(self, blueprint_id: str) -> Optional[FeederBlueprint]:
        return self.blueprints.get(blueprint_id)

    def all(self) -> List[FeederBlueprint]:
        return [self.blueprints[k] for k in sorted(self.blueprints)]

    def by_modality(self, modality: str) -> List[FeederBlueprint]:
        return [b for b in self.blueprints.values() if b.modality == modality]

    def snapshot(self) -> Dict[str, Any]:
        return {"blueprint_count": len(self.blueprints),
                "blueprints": [b.to_dict() for b in self.all()],
                "any_executes_hardware": any(b.executes_hardware
                                             for b in self.blueprints.values())}
