"""Environmental receptor field -- the membrane's typed sensory receptors.

:class:`EnvironmentalReceptorField` holds the typed receptors that match validated
events: chronos, absence, machine-body, local-environment, weather, project-field,
operator-pulse, noise, overload, deprivation, and a conservative unknown-source
receptor. Each receptor carries baseline permeability/salience/risk and sensitivity
parameters. The unknown-source receptor is conservative, the operator-pulse receptor
is attenuated by default, and debug gloss never defines internal truth.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class ReceptorKind:
    CHRONOS = "chronos_receptor"
    ABSENCE = "absence_receptor"
    MACHINE_BODY = "machine_body_receptor"
    LOCAL_ENVIRONMENT = "local_environment_receptor"
    WEATHER = "weather_receptor"
    PROJECT_FIELD = "project_field_receptor"
    OPERATOR_PULSE = "operator_pulse_receptor"
    NOISE = "noise_receptor"
    OVERLOAD = "overload_receptor"
    DEPRIVATION = "deprivation_receptor"
    UNKNOWN_SOURCE = "unknown_source_receptor"

    ALL = (CHRONOS, ABSENCE, MACHINE_BODY, LOCAL_ENVIRONMENT, WEATHER,
           PROJECT_FIELD, OPERATOR_PULSE, NOISE, OVERLOAD, DEPRIVATION,
           UNKNOWN_SOURCE)


@dataclass
class MembraneReceptor:
    """One typed membrane receptor with baseline parameters + sensitivities."""

    receptor_id: str
    accepted_source_ids: List[str] = field(default_factory=list)
    accepted_modalities: List[str] = field(default_factory=list)
    accepted_channels: List[str] = field(default_factory=list)
    baseline_permeability: float = 0.7
    baseline_salience: float = 0.5
    baseline_risk: float = 0.1
    expected_rhythm: str = "irregular"
    saturation_limit: int = 200
    privacy_risk: str = "low"
    contamination_sensitivity: float = 0.5
    operator_text_sensitivity: float = 0.5
    debug_gloss_sensitivity: float = 1.0
    absence_sensitivity: float = 0.5
    overload_sensitivity: float = 0.5
    deprivation_sensitivity: float = 0.5
    conservative: bool = False

    def matches(self, event: Dict[str, Any]) -> bool:
        sid = str(event.get("source_id", ""))
        if self.accepted_source_ids and sid in self.accepted_source_ids:
            return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "receptor_id": self.receptor_id,
            "accepted_source_ids": list(self.accepted_source_ids),
            "accepted_modalities": list(self.accepted_modalities),
            "accepted_channels": list(self.accepted_channels),
            "baseline_permeability": self.baseline_permeability,
            "baseline_salience": self.baseline_salience,
            "baseline_risk": self.baseline_risk,
            "expected_rhythm": self.expected_rhythm,
            "saturation_limit": self.saturation_limit,
            "privacy_risk": self.privacy_risk,
            "contamination_sensitivity": self.contamination_sensitivity,
            "operator_text_sensitivity": self.operator_text_sensitivity,
            "debug_gloss_sensitivity": self.debug_gloss_sensitivity,
            "absence_sensitivity": self.absence_sensitivity,
            "overload_sensitivity": self.overload_sensitivity,
            "deprivation_sensitivity": self.deprivation_sensitivity,
            "conservative": self.conservative,
        }


@dataclass
class ReceptorMatchResult:
    """The result of matching one event to the receptor field."""

    event_id: str
    source_id: str
    receptor_id: str
    matched: bool = True
    is_absence: bool = False
    is_noisy: bool = False
    evidence_refs: List[str] = field(default_factory=list)
    note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"event_id": self.event_id, "source_id": self.source_id,
                "receptor_id": self.receptor_id, "matched": self.matched,
                "is_absence": self.is_absence, "is_noisy": self.is_noisy,
                "evidence_refs": list(self.evidence_refs), "note": self.note}


def _default_receptors() -> List[MembraneReceptor]:
    return [
        MembraneReceptor(ReceptorKind.CHRONOS,
                         accepted_source_ids=["chronos_absence"],
                         accepted_modalities=["chronos"],
                         expected_rhythm="periodic", baseline_salience=0.4,
                         absence_sensitivity=0.9),
        MembraneReceptor(ReceptorKind.MACHINE_BODY,
                         accepted_source_ids=["machine_body"],
                         accepted_modalities=["scalar"],
                         expected_rhythm="periodic", baseline_permeability=0.85),
        MembraneReceptor(ReceptorKind.LOCAL_ENVIRONMENT,
                         accepted_source_ids=["local_environment_manual"],
                         accepted_modalities=["manual", "scalar"],
                         operator_text_sensitivity=0.7,
                         baseline_permeability=0.6),
        MembraneReceptor(ReceptorKind.WEATHER,
                         accepted_source_ids=["local_weather_readonly_external"],
                         accepted_modalities=["scalar"],
                         baseline_permeability=0.8),
        MembraneReceptor(ReceptorKind.PROJECT_FIELD,
                         accepted_source_ids=["project_artifact_field"],
                         accepted_modalities=["field"],
                         baseline_permeability=0.8),
        MembraneReceptor(ReceptorKind.OPERATOR_PULSE,
                         accepted_source_ids=["operator_pulse"],
                         accepted_modalities=["pulse"],
                         baseline_permeability=0.45, baseline_salience=0.3,
                         operator_text_sensitivity=1.0,
                         contamination_sensitivity=0.8),
    ]


@dataclass
class EnvironmentalReceptorField:
    """The full set of membrane receptors + matching logic (evidence-preserving)."""

    receptors: List[MembraneReceptor] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.receptors:
            self.receptors = _default_receptors()
        # Always include the special-purpose + conservative unknown receptors.
        ids = {r.receptor_id for r in self.receptors}
        for special in (
                MembraneReceptor(ReceptorKind.ABSENCE, absence_sensitivity=1.0,
                                 baseline_salience=0.4),
                MembraneReceptor(ReceptorKind.NOISE, baseline_risk=0.5,
                                 baseline_salience=0.3),
                MembraneReceptor(ReceptorKind.OVERLOAD, overload_sensitivity=1.0,
                                 baseline_risk=0.6),
                MembraneReceptor(ReceptorKind.DEPRIVATION,
                                 deprivation_sensitivity=1.0,
                                 baseline_salience=0.3),
                MembraneReceptor(ReceptorKind.UNKNOWN_SOURCE,
                                 baseline_permeability=0.2, baseline_risk=0.6,
                                 baseline_salience=0.2, conservative=True,
                                 contamination_sensitivity=0.9,
                                 privacy_risk="unknown")):
            if special.receptor_id not in ids:
                self.receptors.append(special)

    @property
    def by_source(self) -> Dict[str, MembraneReceptor]:
        out: Dict[str, MembraneReceptor] = {}
        for r in self.receptors:
            for sid in r.accepted_source_ids:
                out[sid] = r
        return out

    def receptor(self, receptor_id: str) -> Optional[MembraneReceptor]:
        for r in self.receptors:
            if r.receptor_id == receptor_id:
                return r
        return None

    def match(self, event: Dict[str, Any]) -> ReceptorMatchResult:
        """Match one validated event to its receptor (evidence preserved)."""
        sid = str(event.get("source_id", ""))
        eid = str(event.get("event_id", ""))
        quality = event.get("quality", {}) or {}
        is_absence = bool(quality.get("is_absence"))
        is_noisy = bool(quality.get("is_noisy"))

        by_source = self.by_source
        # Absence routes to the absence receptor regardless of source.
        if is_absence:
            return ReceptorMatchResult(
                event_id=eid, source_id=sid,
                receptor_id=ReceptorKind.ABSENCE, is_absence=True,
                is_noisy=is_noisy, evidence_refs=[eid],
                note="absence-marked event routed to the absence receptor")
        if sid in by_source:
            r = by_source[sid]
            # Noisy events are additionally tagged for the noise receptor.
            return ReceptorMatchResult(
                event_id=eid, source_id=sid, receptor_id=r.receptor_id,
                is_noisy=is_noisy, evidence_refs=[eid],
                note=f"matched {r.receptor_id}")
        return ReceptorMatchResult(
            event_id=eid, source_id=sid,
            receptor_id=ReceptorKind.UNKNOWN_SOURCE, is_noisy=is_noisy,
            evidence_refs=[eid],
            note="no source-specific receptor; conservative unknown receptor")

    def index(self) -> Dict[str, Any]:
        return {
            "membrane_receptor_count": len(self.receptors),
            "receptors": [r.to_dict() for r in self.receptors],
            "note": "the unknown-source receptor is conservative; the operator-"
                    "pulse receptor is attenuated by default; debug gloss never "
                    "defines internal truth",
        }
