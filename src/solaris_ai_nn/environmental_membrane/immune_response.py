"""Membrane immune response -- local metadata + routing, never source control.

:class:`MembraneImmuneResponse` turns a permeability decision + contamination into a
routing action (allow / attenuate / amplify / defer / block / quarantine / mark-toxic
/ mark-source-artifact / mark-operator-contamination / mark-private-risk /
create-absence|overload|deprivation-impression). It is local metadata and routing
only: it changes no feeder behavior, modifies no source files, deletes no events, and
preserves blocked/quarantined evidence.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List


class ImmuneResponseAction:
    ALLOW = "allow"
    ATTENUATE = "attenuate"
    AMPLIFY = "amplify"
    DEFER = "defer"
    BLOCK = "block"
    QUARANTINE = "quarantine"
    MARK_TOXIC = "mark_toxic"
    MARK_SOURCE_ARTIFACT = "mark_source_artifact"
    MARK_OPERATOR_CONTAMINATION = "mark_operator_contamination"
    MARK_PRIVATE_RISK = "mark_private_risk"
    CREATE_ABSENCE_IMPRESSION = "create_absence_impression"
    CREATE_OVERLOAD_IMPRESSION = "create_overload_impression"
    CREATE_DEPRIVATION_IMPRESSION = "create_deprivation_impression"

    ALL = (ALLOW, ATTENUATE, AMPLIFY, DEFER, BLOCK, QUARANTINE, MARK_TOXIC,
           MARK_SOURCE_ARTIFACT, MARK_OPERATOR_CONTAMINATION, MARK_PRIVATE_RISK,
           CREATE_ABSENCE_IMPRESSION, CREATE_OVERLOAD_IMPRESSION,
           CREATE_DEPRIVATION_IMPRESSION)

_STATUS_ACTION = {
    "allow": ImmuneResponseAction.ALLOW,
    "allow_attenuated": ImmuneResponseAction.ATTENUATE,
    "allow_amplified": ImmuneResponseAction.AMPLIFY,
    "defer": ImmuneResponseAction.DEFER,
    "block": ImmuneResponseAction.BLOCK,
    "quarantine": ImmuneResponseAction.QUARANTINE,
}


@dataclass
class ImmuneResponseRecord:
    """One immune-response record for an event (routing metadata only)."""

    event_id: str
    source_id: str
    actions: List[str] = field(default_factory=list)
    detail: str = ""
    preserves_evidence: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {"event_id": self.event_id, "source_id": self.source_id,
                "actions": list(self.actions), "detail": self.detail,
                "preserves_evidence": self.preserves_evidence,
                "changes_feeder_behavior": False, "modifies_source": False,
                "deletes_events": False}


@dataclass
class MembraneImmuneResponse:
    """Derives routing actions from permeability + contamination (read-only)."""

    def respond(self, *, decision, contamination) -> ImmuneResponseRecord:
        rec = ImmuneResponseRecord(event_id=decision.event_id,
                                   source_id=decision.source_id)
        rec.actions.append(_STATUS_ACTION.get(decision.status,
                                              ImmuneResponseAction.DEFER))
        ctypes = set(contamination.types)
        if "operator_pulse_dominance" in ctypes:
            rec.actions.append(
                ImmuneResponseAction.MARK_OPERATOR_CONTAMINATION)
        if ctypes & {"secret_marker", "private_data"}:
            rec.actions.append(ImmuneResponseAction.MARK_PRIVATE_RISK)
        if "source_artifact" in ctypes:
            rec.actions.append(ImmuneResponseAction.MARK_SOURCE_ARTIFACT)
        if contamination.blocks and decision.status != "block":
            rec.actions.append(ImmuneResponseAction.MARK_TOXIC)
        if decision.creates_absence:
            rec.actions.append(ImmuneResponseAction.CREATE_ABSENCE_IMPRESSION)
        if decision.creates_overload:
            rec.actions.append(ImmuneResponseAction.CREATE_OVERLOAD_IMPRESSION)
        if decision.creates_deprivation:
            rec.actions.append(
                ImmuneResponseAction.CREATE_DEPRIVATION_IMPRESSION)
        rec.detail = "; ".join(decision.reasons[:4])
        return rec

    @staticmethod
    def write(records: List[ImmuneResponseRecord], state_dir: str,
              ) -> Dict[str, str]:
        base = os.path.join(state_dir, "membrane", "immune")
        os.makedirs(base, exist_ok=True)
        jsonl = os.path.join(base, "MEMBRANE_IMMUNE_RESPONSE.jsonl")
        report = os.path.join(base, "MEMBRANE_IMMUNE_REPORT.md")
        with open(jsonl, "w", encoding="utf-8") as fh:
            for r in records:
                fh.write(json.dumps(r.to_dict(), default=str) + "\n")
        counts: Dict[str, int] = {}
        for r in records:
            for a in r.actions:
                counts[a] = counts.get(a, 0) + 1
        lines = ["# Membrane Immune Response Report", "",
                 f"- responses: {len(records)}",
                 f"- actions: {counts}", "",
                 "_Immune response is local metadata and routing only. It changes "
                 "no feeder behavior, modifies no source files, deletes no "
                 "events, and preserves blocked/quarantined evidence._"]
        with open(report, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
        return {"jsonl": jsonl, "report": report}

    @staticmethod
    def summary(records: List[ImmuneResponseRecord]) -> Dict[str, Any]:
        counts: Dict[str, int] = {}
        for r in records:
            for a in r.actions:
                counts[a] = counts.get(a, 0) + 1
        return {
            "membrane_immune_response_count": len(records),
            "action_counts": counts,
            "membrane_absence_impression_count": counts.get(
                ImmuneResponseAction.CREATE_ABSENCE_IMPRESSION, 0),
            "membrane_overload_impression_count": counts.get(
                ImmuneResponseAction.CREATE_OVERLOAD_IMPRESSION, 0),
            "membrane_deprivation_impression_count": counts.get(
                ImmuneResponseAction.CREATE_DEPRIVATION_IMPRESSION, 0),
            "note": "immune response routes metadata only; it never controls "
                    "feeders, modifies source, or deletes events",
        }
