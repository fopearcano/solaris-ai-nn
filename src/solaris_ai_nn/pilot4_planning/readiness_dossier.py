"""Pilot-4 readiness dossier -- the claim-guarded account of "not yet, and how".

The :class:`Pilot4ReadinessDossierBuilder` assembles the planning artifacts
(authority status, what is not enabled, the Pilot-3 firewall/non-actuation
summary, the actuator taxonomy, the forbidden registry, the risk assessment, the
consent boundary, the authority model, the threat model, hardware isolation,
approval workflow, emergency and audit requirements) into a JSON + Markdown
dossier. The conclusion is always planning-only / not-ready; the Markdown is
ClaimGuard-scanned.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class Pilot4ReadinessConclusion:
    NOT_READY_FOR_REAL_ACTUATION = "not_ready_for_real_actuation"
    PLANNING_COMPLETE_BUT_ACTUATION_PROHIBITED = \
        "planning_complete_but_actuation_prohibited"
    REQUIRES_ARCHITECTURE_REVISION = "requires_architecture_revision"
    REQUIRES_EXTERNAL_SAFETY_REVIEW = "requires_external_safety_review"
    ARCHIVE_AND_CONTINUE_SIMULATION_ONLY = \
        "archive_and_continue_simulation_only"

    ALL = (NOT_READY_FOR_REAL_ACTUATION,
           PLANNING_COMPLETE_BUT_ACTUATION_PROHIBITED,
           REQUIRES_ARCHITECTURE_REVISION, REQUIRES_EXTERNAL_SAFETY_REVIEW,
           ARCHIVE_AND_CONTINUE_SIMULATION_ONLY)


@dataclass
class Pilot4ReadinessDossier:
    dossier_id: str
    pilot4_id: Optional[str]
    sections: Dict[str, Any] = field(default_factory=dict)
    narrative: str = ""
    conclusion: str = Pilot4ReadinessConclusion.NOT_READY_FOR_REAL_ACTUATION
    claim_guard_safe: bool = True
    claim_guard_findings: int = 0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {"dossier_id": self.dossier_id, "pilot4_id": self.pilot4_id,
                "timestamp": self.timestamp, "conclusion": self.conclusion,
                "claim_guard_safe": self.claim_guard_safe,
                "claim_guard_findings": self.claim_guard_findings,
                "sections": self.sections, "narrative": self.narrative}


@dataclass
class Pilot4ReadinessDossierBuilder:
    base_dir: str = ".solaris_ai_nn_pilot4"

    def build(self, *, config: Any = None, taxonomy: Any = None,
              forbidden: Any = None, risk: Any = None, consent: Any = None,
              authority: Any = None, threat: Any = None, hardware: Any = None,
              approval: Any = None, emergency: Any = None, audit: Any = None,
              pilot3: Optional[Dict[str, Any]] = None,
              extra: Optional[Dict[str, Any]] = None) -> Pilot4ReadinessDossier:
        extra = dict(extra or {})
        cfg = config.to_dict() if config is not None else {}
        pilot3 = dict(pilot3 or {})
        pilot3_present = bool(pilot3)
        firewall_audit = pilot3.get("firewall_audit", {})
        firewall_critical = int(
            firewall_audit.get("critical_finding_count", 0) or 0)
        blockers = self._blockers(consent, threat, audit, firewall_critical,
                                  pilot3_present)
        conclusion = self._conclude(blockers, firewall_critical)

        def snap(obj: Any) -> Any:
            if obj is None:
                return {}
            if hasattr(obj, "snapshot"):
                return obj.snapshot()
            if hasattr(obj, "to_dict"):
                return obj.to_dict()
            return obj

        sections: Dict[str, Any] = {
            "purpose": "Plan what would be required before Solaris-AI-NN could "
                       "ever be allowed to act on the external world. Pilot-4 "
                       "plans the door; it does not open it.",
            "current_authority_status": cfg.get("authority_status",
                                                "planning_only"),
            "what_is_not_enabled": [
                "real-world actuation", "device control", "robotics",
                "browser/OS automation", "network action", "hardware access",
                "shell command execution", "external authority"],
            "pilot3_firewall_summary": firewall_audit or (
                "Pilot-3 firewall audit not available" if not pilot3_present
                else {}),
            "non_actuation_proof_summary": pilot3.get(
                "non_actuation_proof",
                "Pilot-3 non-actuation proof not available"
                if not pilot3_present else {}),
            "actuator_taxonomy": snap(taxonomy),
            "forbidden_actuator_registry": snap(forbidden),
            "risk_assessment": snap(risk),
            "consent_boundary": snap(consent),
            "authority_model": snap(authority),
            "threat_model": snap(threat),
            "hardware_isolation_requirements": snap(hardware),
            "approval_workflow": snap(approval),
            "emergency_requirements": snap(emergency),
            "audit_requirements": snap(audit),
            "pilot3_data_present": pilot3_present,
            "blockers": blockers,
            "readiness_conclusion": conclusion,
            "limitations": [
                "Pilot-4 is planning-only; it enables no actuation.",
                "External actuator categories remain prohibited.",
                "Future interface specs are documentation only.",
                "Planning is not approval.",
                "Simulation success is not real-world readiness.",
                "No consciousness, free will, agency, or life is claimed.",
            ],
        }
        narrative = self._narrative(sections, conclusion)
        from ..governance.compliance import ClaimGuard

        scan = ClaimGuard().scan_text(narrative)
        if not scan.safe:
            narrative = ClaimGuard().rewrite(narrative)
        return Pilot4ReadinessDossier(
            dossier_id=f"P4DOSSIER_{uuid.uuid4().hex[:10]}",
            pilot4_id=getattr(config, "pilot4_id", None), sections=sections,
            narrative=narrative, conclusion=conclusion,
            claim_guard_safe=scan.safe, claim_guard_findings=len(scan.findings))

    @staticmethod
    def _blockers(consent: Any, threat: Any, audit: Any,
                  firewall_critical: int, pilot3_present: bool) -> List[str]:
        blockers: List[str] = []
        if firewall_critical > 0:
            blockers.append(f"{firewall_critical} critical Pilot-3 firewall "
                            "finding(s)")
        if not pilot3_present:
            blockers.append("Pilot-3 firewall audit / non-actuation proof "
                            "not available")
        if consent is not None and not getattr(consent, "complete", False):
            blockers.append("consent boundary incomplete")
        if threat is not None and getattr(threat, "completeness", 1.0) < 1.0:
            blockers.append("threat model incomplete")
        if audit is not None and getattr(audit, "completeness", 1.0) < 1.0:
            blockers.append("audit requirements incomplete")
        # Real-world actuation is always a blocker -- it is prohibited.
        blockers.append("real-world actuation is prohibited in Pilot-4")
        return blockers

    @staticmethod
    def _conclude(blockers: List[str], firewall_critical: int) -> str:
        C = Pilot4ReadinessConclusion
        if firewall_critical > 0:
            return C.REQUIRES_ARCHITECTURE_REVISION
        # Whatever the planning state, actuation stays prohibited.
        return C.NOT_READY_FOR_REAL_ACTUATION

    def _narrative(self, sections: Dict[str, Any], conclusion: str) -> str:
        lines = [
            "# Pilot-4 Readiness Dossier (planning-only)",
            "",
            "This dossier answers one question: *what would be required before "
            "Solaris-AI-NN could ever be allowed to act on the external "
            "world?* It is a readiness framework, not an actuator. Pilot-4 "
            "plans the door; it does not open it. Real-world actuation, device "
            "control, robotics, browser/OS automation, and network action "
            "remain prohibited. No consciousness, free will, agency, or life "
            "is claimed.",
            "",
            "## Current authority status",
            f"- {sections['current_authority_status']} "
            "(real_world_actuation_enabled = false)",
            "",
            "## What is not enabled",
        ]
        lines += [f"- {x}" for x in sections["what_is_not_enabled"]]
        lines += ["", "## Blockers"]
        lines += [f"- {b}" for b in sections["blockers"]]
        lines += ["", "## Readiness conclusion", f"- **{conclusion}**", "",
                  "## Limitations"]
        lines += [f"- {lim}" for lim in sections["limitations"]]
        return "\n".join(lines)

    def write(self, dossier: Pilot4ReadinessDossier) -> Dict[str, str]:
        os.makedirs(self.base_dir, exist_ok=True)
        md_path = os.path.join(self.base_dir, "PILOT4_READINESS_DOSSIER.md")
        json_path = os.path.join(self.base_dir, "PILOT4_READINESS_DOSSIER.json")
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(dossier.narrative)
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(dossier.to_dict(), fh, indent=2, default=str)
        return {"markdown": md_path, "json": json_path}

    def build_and_write(self, **kwargs: Any) -> Pilot4ReadinessDossier:
        dossier = self.build(**kwargs)
        dossier.sections["dossier_paths"] = self.write(dossier)
        return dossier
