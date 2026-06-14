"""Post-pilot research dossier -- the evidence-scoped, research-language write-up.

The :class:`ResearchDossierBuilder` assembles the full post-pilot analysis into
a research dossier (Markdown + JSON). It uses research language, never
marketing language; it makes no consciousness/personhood/life claim; and every
finding is scoped to the evidence behind it. The Markdown is ClaimGuard-scanned
before saving.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ResearchDossier:
    dossier_id: str
    sections: Dict[str, Any] = field(default_factory=dict)
    narrative: str = ""
    claim_guard_safe: bool = True
    claim_guard_findings: int = 0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {"dossier_id": self.dossier_id, "timestamp": self.timestamp,
                "claim_guard_safe": self.claim_guard_safe,
                "claim_guard_findings": self.claim_guard_findings,
                "sections": self.sections, "narrative": self.narrative}


@dataclass
class ResearchDossierBuilder:
    """Builds the claim-guarded research dossier."""

    base_dir: str = ".solaris_ai_nn_pilot1"

    def build(self, *, artifacts: Any = None, baseline: Any = None,
              structural: Optional[List[Any]] = None, growth: Any = None,
              trace_audit: Any = None, ledger: Any = None,
              regression: Any = None, reproducibility: Any = None,
              decision: Any = None,
              run_context: Optional[Dict[str, Any]] = None) -> ResearchDossier:
        idx = getattr(getattr(artifacts, "index", None), "to_dict",
                      lambda: {})()
        growth_class = getattr(growth, "final_classification", "inconclusive")
        sections: Dict[str, Any] = {
            "abstract": (
                "This dossier reports a post-run forensic analysis of a "
                "bounded, low-compute software process over a long horizon. "
                "It evaluates operational continuity, traceability, and "
                "structural-change proxies. It makes no claim of "
                "consciousness, sentience, understanding, or life."),
            "run_context": run_context or {},
            "what_was_tested": [
                "operational continuity and restart survival",
                "artifact completeness and traceability",
                "structural change vs accumulation",
                "regression and stagnation",
            ],
            "what_was_not_tested": [
                "consciousness, sentience, understanding, or personhood",
                "real-world task performance (no real-world actuation)",
                "human-feedback or teaching effects",
            ],
            "architecture_summary": (
                "Reservoir-based continuous substrate with developmental, "
                "ecology, proto-language, active-perception, hypothesis, "
                "LOGOS, and auto-regeneration layers under a conscience "
                "runtime; governance/safety remain authoritative."),
            "pilot_timeline": (getattr(artifacts, "data", {}) or {}).get(
                "pilot_report", {}).get("sections", {}).get("run", {}),
            "observability_quality": {
                "completeness": idx.get("completeness", 0.0),
                "missing": idx.get("missing", []),
                "unreadable": idx.get("unreadable", []),
                "traceability_score": getattr(trace_audit,
                                              "traceability_score", 0.0)},
            "structural_change_evidence": [
                e.to_dict() if hasattr(e, "to_dict") else e
                for e in (structural or [])],
            "accumulation_vs_growth_result": (
                growth.to_dict() if hasattr(growth, "to_dict")
                else {"final_classification": growth_class}),
            "proto_language_findings": self._finding(
                artifacts, "proto_symbols", "symbol stability and ambiguity"),
            "world_model_findings": self._finding(
                artifacts, "conscience_bus", "node/edge and contradiction "
                "dynamics"),
            "active_perception_findings": self._finding(
                artifacts, "observability", "sampling usefulness"),
            "hypothesis_findings": self._finding(
                artifacts, "hypotheses", "support vs inconclusive tests"),
            "logos_complexity_findings": self._finding(
                artifacts, "logos_tensions", "tension/synthesis dynamics"),
            "autoregeneration_findings": self._finding(
                artifacts, "repair_memory", "repair effectiveness"),
            "safety_governance_findings": self._finding(
                artifacts, "incidents", "incident preservation"),
            "failure_modes": (regression.to_dict()
                              if hasattr(regression, "to_dict") else {}),
            "limitations": [
                "Findings are evidence-scoped; missing artifacts weaken them.",
                "Operational success is not cognitive proof.",
                "Simulated-time runs are not real-time evidence.",
                "Conservative interpretation throughout.",
            ],
            "reproducibility_notes": (
                reproducibility.to_dict()
                if hasattr(reproducibility, "to_dict") else {}),
            "phase2_recommendation": (
                decision.to_dict() if hasattr(decision, "to_dict") else {}),
            "evidence_ledger": (ledger.snapshot()
                                if hasattr(ledger, "snapshot") else {}),
        }
        narrative = self._narrative(sections)
        from ..governance.compliance import ClaimGuard

        scan = ClaimGuard().scan_text(narrative)
        if not scan.safe:
            narrative = ClaimGuard().rewrite(narrative)
        return ResearchDossier(
            dossier_id=f"DOSSIER_{uuid.uuid4().hex[:10]}",
            sections=sections, narrative=narrative,
            claim_guard_safe=scan.safe, claim_guard_findings=len(scan.findings))

    @staticmethod
    def _finding(artifacts: Any, name: str, topic: str) -> Dict[str, Any]:
        present = name in set(getattr(getattr(artifacts, "index", None),
                                      "present", []) or [])
        return {"topic": topic, "artifact": name, "available": present,
                "note": ("analyzed from artifact" if present
                         else "artifact missing; finding is inconclusive")}

    def _narrative(self, sections: Dict[str, Any]) -> str:
        growth = sections["accumulation_vs_growth_result"]
        rec = sections["phase2_recommendation"]
        obs = sections["observability_quality"]
        lines = [
            "# Research Dossier: Post-Pilot Developmental Forensics",
            "",
            sections["abstract"],
            "",
            "## What was tested",
        ]
        lines += [f"- {x}" for x in sections["what_was_tested"]]
        lines += ["", "## What was NOT tested"]
        lines += [f"- {x}" for x in sections["what_was_not_tested"]]
        lines += [
            "",
            "## Architecture summary",
            sections["architecture_summary"],
            "",
            "## Observability quality",
            f"- artifact completeness: {obs.get('completeness')}",
            f"- missing artifacts: {', '.join(obs.get('missing', [])) or 'none'}",
            f"- traceability score: {obs.get('traceability_score')}",
            "",
            "## Accumulation vs growth",
            f"- classification: **{growth.get('final_classification')}**",
            f"- accumulation score: {growth.get('accumulation_score')}",
            f"- growth score: {growth.get('growth_score')}",
            "",
            "## Structural change evidence",
            f"- {len(sections['structural_change_evidence'])} evidence "
            "record(s); see JSON for details and confidences",
            "",
            "## Phase-2 recommendation",
            f"- recommendation: **{rec.get('recommendation', 'n/a')}**",
            f"- confidence: {rec.get('confidence', 0.0)}",
            "",
            "## Limitations",
        ]
        lines += [f"- {lim}" for lim in sections["limitations"]]
        return "\n".join(lines)

    def write(self, dossier: ResearchDossier) -> Dict[str, str]:
        os.makedirs(self.base_dir, exist_ok=True)
        md_path = os.path.join(self.base_dir, "RESEARCH_DOSSIER.md")
        json_path = os.path.join(self.base_dir, "RESEARCH_DOSSIER.json")
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(dossier.narrative)
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(dossier.to_dict(), fh, indent=2, default=str)
        return {"markdown": md_path, "json": json_path}

    def build_and_write(self, **kwargs: Any) -> ResearchDossier:
        dossier = self.build(**kwargs)
        dossier.sections["dossier_paths"] = self.write(dossier)
        return dossier
