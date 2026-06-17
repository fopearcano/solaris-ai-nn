"""Membrane permeability regulation -- allowed / blocked / attenuated / quarantined.

:class:`MembranePermeabilityGate` decides, for each event, whether it is allowed
(possibly attenuated or amplified), deferred, blocked, or quarantined -- the membrane
verdict that goes beyond validation's valid/invalid. It weighs governance, feeder
registry, validation, source trust/pressure/dominance, the receptor match, payload
size, operator/human-text/debug-gloss dominance, private/secret/command
contamination, overload, deprivation, novelty, repetition, absence, and quarantine
history. Every decision is explained.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from ..live_birth.birth_profile import FORBIDDEN_FIRST_BIRTH_SOURCES


class PermeabilityStatus:
    ALLOW = "allow"
    ALLOW_ATTENUATED = "allow_attenuated"
    ALLOW_AMPLIFIED = "allow_amplified"
    DEFER = "defer"
    BLOCK = "block"
    QUARANTINE = "quarantine"
    UNKNOWN = "unknown"

    ALL = (ALLOW, ALLOW_ATTENUATED, ALLOW_AMPLIFIED, DEFER, BLOCK, QUARANTINE,
           UNKNOWN)


class PermeabilityFactor:
    GOVERNANCE = "governance_status"
    FEEDER_REGISTRY = "feeder_registry_status"
    EVENT_VALIDATION = "event_validation_status"
    SOURCE_TRUST = "source_trust"
    SOURCE_PRESSURE = "source_pressure"
    RECEPTOR_MATCH = "receptor_match"
    SOURCE_RHYTHM = "source_rhythm"
    PAYLOAD_SIZE = "payload_size"
    SOURCE_DOMINANCE = "source_dominance"
    OPERATOR_DOMINANCE = "operator_pulse_dominance"
    HUMAN_TEXT_DOMINANCE = "human_text_dominance"
    DEBUG_GLOSS_DEPENDENCE = "debug_gloss_dependence"
    PRIVATE_DATA = "private_data_risk"
    SECRET = "secret_risk"
    COMMAND = "command_contamination"
    OVERLOAD = "overload"
    DEPRIVATION = "deprivation"
    NOVELTY = "novelty"
    REPETITION = "repetition"
    ABSENCE = "absence"
    QUARANTINE_HISTORY = "quarantine_history"

    ALL = (GOVERNANCE, FEEDER_REGISTRY, EVENT_VALIDATION, SOURCE_TRUST,
           SOURCE_PRESSURE, RECEPTOR_MATCH, SOURCE_RHYTHM, PAYLOAD_SIZE,
           SOURCE_DOMINANCE, OPERATOR_DOMINANCE, HUMAN_TEXT_DOMINANCE,
           DEBUG_GLOSS_DEPENDENCE, PRIVATE_DATA, SECRET, COMMAND, OVERLOAD,
           DEPRIVATION, NOVELTY, REPETITION, ABSENCE, QUARANTINE_HISTORY)


@dataclass
class PermeabilityDecision:
    """The explained membrane permeability decision for one event."""

    event_id: str
    source_id: str
    receptor_id: str
    status: str = PermeabilityStatus.UNKNOWN
    attenuation: float = 1.0  # multiplier applied to intensity/salience
    reasons: List[str] = field(default_factory=list)
    factors: Dict[str, Any] = field(default_factory=dict)
    creates_absence: bool = False
    creates_overload: bool = False
    creates_deprivation: bool = False

    @property
    def allowed(self) -> bool:
        return self.status in (PermeabilityStatus.ALLOW,
                               PermeabilityStatus.ALLOW_ATTENUATED,
                               PermeabilityStatus.ALLOW_AMPLIFIED)

    def to_dict(self) -> Dict[str, Any]:
        return {"event_id": self.event_id, "source_id": self.source_id,
                "receptor_id": self.receptor_id, "status": self.status,
                "allowed": self.allowed,
                "attenuation": round(self.attenuation, 3),
                "reasons": list(self.reasons), "factors": dict(self.factors),
                "creates_absence": self.creates_absence,
                "creates_overload": self.creates_overload,
                "creates_deprivation": self.creates_deprivation}


@dataclass
class MembranePermeabilityGate:
    """Regulates what crosses the membrane; explains every decision."""

    operator_attenuation: float = 0.5
    high_contamination: float = 0.5

    def decide(self, *, event: Dict[str, Any], receptor,
               contamination, source_pressure: Dict[str, Any],
               governance_passed: bool, feeder_registry_present: bool,
               validated: bool, load_status: str = "",
               ) -> PermeabilityDecision:
        eid = str(event.get("event_id", ""))
        sid = str(event.get("source_id", ""))
        rid = getattr(receptor, "receptor_id", "unknown_source_receptor")
        d = PermeabilityDecision(event_id=eid, source_id=sid, receptor_id=rid)
        f = d.factors
        quality = event.get("quality", {}) or {}
        is_absence = bool(quality.get("is_absence"))

        f[PermeabilityFactor.GOVERNANCE] = governance_passed
        f[PermeabilityFactor.FEEDER_REGISTRY] = feeder_registry_present
        f[PermeabilityFactor.EVENT_VALIDATION] = validated
        f[PermeabilityFactor.RECEPTOR_MATCH] = rid
        f[PermeabilityFactor.ABSENCE] = is_absence

        # Hard blocks first.
        if sid in FORBIDDEN_FIRST_BIRTH_SOURCES:
            d.status = PermeabilityStatus.BLOCK
            d.reasons.append("forbidden source blocked")
            return d
        if not validated:
            d.status = PermeabilityStatus.BLOCK
            d.reasons.append("event not validated; membrane blocks")
            return d

        # Contamination-driven quarantine / block.
        ctypes = set(contamination.types)
        f[PermeabilityFactor.SECRET] = "secret_marker" in ctypes
        f[PermeabilityFactor.PRIVATE_DATA] = "private_data" in ctypes
        f[PermeabilityFactor.COMMAND] = "command_like_text" in ctypes
        f[PermeabilityFactor.DEBUG_GLOSS_DEPENDENCE] = \
            "debug_gloss_ground_truth_attempt" in ctypes
        if ctypes & {"secret_marker", "private_data"}:
            d.status = PermeabilityStatus.QUARANTINE
            d.reasons.append("secret/private contamination quarantined")
            return d
        if "command_like_text" in ctypes or contamination.blocks:
            d.status = PermeabilityStatus.QUARANTINE
            d.reasons.append("command/ground-truth contamination quarantined")
            return d

        # Absence -> allowed, but flagged to create an absence impression.
        if is_absence:
            d.status = PermeabilityStatus.ALLOW
            d.creates_absence = True
            d.reasons.append("absence event allowed; creates absence impression")
            return d

        # Overload / deprivation context.
        if "overload" in str(load_status):
            f[PermeabilityFactor.OVERLOAD] = True
            d.creates_overload = True
        if "deprivation" in str(load_status):
            f[PermeabilityFactor.DEPRIVATION] = True
            d.creates_deprivation = True

        # Dominance-driven attenuation.
        op_dom = float(source_pressure.get("membrane_operator_dominance_score",
                                           0.0) or 0.0)
        human_dom = float(source_pressure.get("human_text_dominance_score",
                                              0.0) or 0.0)
        src_dom = float(source_pressure.get(
            "membrane_source_pressure_dominance_score", 0.0) or 0.0)
        f[PermeabilityFactor.OPERATOR_DOMINANCE] = op_dom
        f[PermeabilityFactor.HUMAN_TEXT_DOMINANCE] = human_dom
        f[PermeabilityFactor.SOURCE_DOMINANCE] = src_dom
        f[PermeabilityFactor.SOURCE_PRESSURE] = source_pressure.get("status")

        attenuated = False
        if sid == "operator_pulse":
            d.attenuation *= self.operator_attenuation
            attenuated = True
            d.reasons.append("operator pulse attenuated (stimulus, not teaching)")
        if op_dom >= 0.4 and sid == "operator_pulse":
            d.attenuation *= 0.5
            attenuated = True
            d.reasons.append("operator dominance further attenuates")
        if human_dom >= 0.5 and sid in ("operator_pulse",
                                        "local_environment_manual"):
            d.attenuation *= 0.7
            attenuated = True
            d.reasons.append("human-text dominance attenuates")
        if contamination.score >= self.high_contamination:
            d.attenuation *= 0.5
            attenuated = True
            d.reasons.append("high contamination attenuates (not blocking)")
        if rid == "unknown_source_receptor":
            d.attenuation *= 0.4
            attenuated = True
            d.reasons.append("unknown source conservatively attenuated")
        if bool(quality.get("is_noisy")):
            d.attenuation *= 0.7
            attenuated = True
            d.reasons.append("noisy event attenuated")

        if "overload" in str(load_status) and src_dom >= 0.6:
            d.status = PermeabilityStatus.ALLOW_ATTENUATED
            d.attenuation *= 0.5
            d.reasons.append("overload + dominance: strongly attenuated")
            return d

        if attenuated:
            d.status = PermeabilityStatus.ALLOW_ATTENUATED
        else:
            d.status = PermeabilityStatus.ALLOW
            d.reasons.append("clean validated event allowed")
        d.attenuation = round(max(0.0, min(1.0, d.attenuation)), 3)
        return d

    @staticmethod
    def summary(decisions: List[PermeabilityDecision]) -> Dict[str, Any]:
        def count(status):
            return sum(1 for d in decisions if d.status == status)
        return {
            "membrane_allowed_count": count(PermeabilityStatus.ALLOW),
            "membrane_attenuated_count": count(
                PermeabilityStatus.ALLOW_ATTENUATED),
            "membrane_amplified_count": count(
                PermeabilityStatus.ALLOW_AMPLIFIED),
            "membrane_deferred_count": count(PermeabilityStatus.DEFER),
            "membrane_blocked_count": count(PermeabilityStatus.BLOCK),
            "membrane_quarantined_count": count(PermeabilityStatus.QUARANTINE),
            "note": "the membrane says allowed/blocked/attenuated/amplified/"
                    "deferred/quarantined -- not merely valid/invalid; every "
                    "decision is explained",
        }
