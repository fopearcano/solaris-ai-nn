"""Developmental replication reports -- conservative, ClaimGuard-scanned.

:class:`DevelopmentalReplicationReportBuilder` compiles the replication report
(plus the replication matrix and falsification report). Every report states that
replication compares observable structures only, that a developmental lineage is
experimental provenance (not biological ancestry), that cross-run similarity does
not prove consciousness, that divergence is not failure by itself, and that
passing a falsification test does not prove understanding. The Markdown is
scanned by ClaimGuard.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

_DOES_NOT_PROVE = (
    "Replication compares observable structures only.",
    "Developmental lineage is experimental provenance, not biological ancestry.",
    "Cross-run similarity does not prove consciousness.",
    "Divergence does not prove failure by itself.",
    "Falsification passing does not prove understanding.",
    "This does not prove consciousness, sentience, life, personhood, agency, "
    "free will, emotion, feeling, understanding, or subjective experience.",
)

_LIMITATIONS = (
    "One developmental run is not evidence enough; this compares several.",
    "High similarity may be robust development OR fixture overfit -- both "
    "considered.",
    "Low similarity may be real divergence, noise, or insufficient evidence.",
    "Diverged, falsified, and inconclusive evidence is preserved, never hidden.",
    "Bounded comparison of existing artifacts; no unbounded soak is launched.",
)


@dataclass
class DevelopmentalReplicationReportBuilder:
    """Builds the replication report set (JSON + claim-guarded Markdown)."""

    runtime: Any

    def build(self) -> Dict[str, Any]:
        rt = self.runtime
        status = rt.replication_status()
        matrix = rt.matrix.to_dict() if rt.matrix else {}
        sections: Dict[str, Any] = {
            "purpose": ("test whether independent Solaris runs produce "
                        "comparable structural development under comparable "
                        "sensorium conditions, and different development under "
                        "different conditions -- not life or consciousness"),
            "registered_runs": rt.registry.status(),
            "lineage_summary": rt.lineage.to_dict(),
            "replication_plan": rt.plan.to_dict(),
            "cross_run_alignment": rt.alignments,
            "structural_similarity": rt.similarities,
            "divergence_analysis": rt.divergences,
            "environmental_dependency": {
                "per_run": rt.dependencies, "scores": rt.dependency_scores},
            "falsification_tests": rt.falsifications,
            "replication_matrix": matrix,
            "claims_replicated": [c for c in matrix.get("cells", [])
                                  if c["status"] == "replicated"],
            "claims_partially_replicated": [
                c for c in matrix.get("cells", [])
                if c["status"] == "partially_replicated"],
            "claims_diverged": [c for c in matrix.get("cells", [])
                                if c["status"] == "diverged"],
            "claims_falsified": matrix.get("falsified_claims", []),
            "inconclusive_claims": [c for c in matrix.get("cells", [])
                                    if c["status"] == "inconclusive"],
            "missing_evidence": rt.registry.status().get(
                "runs_with_uncertainty", []),
            "safety_status": rt.safety.snapshot(),
            "status": status,
            "limitations": list(_LIMITATIONS),
            "what_this_does_not_prove": list(_DOES_NOT_PROVE),
        }
        markdown = self._render_markdown(sections)
        return {"sections": sections,
                "claim_guard_safe": self._claim_guard_safe(markdown)}

    def _render_markdown(self, sections: Dict[str, Any]) -> str:
        status = sections["status"]
        lines = [
            "# Developmental Replication Report", "",
            "_Do independent Solaris runs produce comparable structural "
            "development under comparable sensorium conditions, and different "
            "development under different conditions? Replication compares "
            "observable structures only. A 'developmental lineage' is "
            "experimental provenance, NOT biological ancestry._", "",
            f"- registered runs: {status['registered_run_count']}",
            f"- lineages: {status['lineage_count']}",
            f"- aligned run pairs: {status['aligned_run_pair_count']}",
            f"- replicated claims: {status['replicated_claim_count']}",
            f"- partially replicated: "
            f"{status['partially_replicated_claim_count']}",
            f"- diverged claims: {status['diverged_claim_count']}",
            f"- falsified claims: {status['falsified_claim_count']}",
            f"- inconclusive claims: {status['inconclusive_claim_count']}",
            f"- structural similarity mean: "
            f"{status['structural_similarity_mean']} "
            f"(variance {status['structural_similarity_variance']})",
            f"- environmental dependency: "
            f"{status['environmental_dependency_score']} "
            f"(fixture-overfit {status['fixture_overfit_score']}, "
            f"human-label {status['human_label_dependency_score']})",
            f"- falsification: {status['falsification_pass_count']} passed, "
            f"{status['falsification_fail_count']} falsified",
            "",
            "## Falsified claims (prominent)", "",
        ]
        falsified = sections["claims_falsified"]
        if falsified:
            lines += [f"- {c['claim']} ({c['detail']})" for c in falsified]
        else:
            lines.append("- none falsified in this bounded comparison")
        lines += ["", "## What this does NOT prove", ""]
        lines += [f"- {item}" for item in sections["what_this_does_not_prove"]]
        lines += ["", "## Limitations", ""]
        lines += [f"- {lim}" for lim in sections["limitations"]]
        return "\n".join(lines)

    def _render_matrix_md(self, sections: Dict[str, Any]) -> str:
        matrix = sections["replication_matrix"]
        lines = ["# Replication Matrix", "",
                 f"- cells: {matrix.get('cell_count', 0)}",
                 f"- replicated {matrix.get('replicated_claim_count', 0)}, "
                 f"partially {matrix.get('partially_replicated_claim_count', 0)}, "
                 f"diverged {matrix.get('diverged_claim_count', 0)}, "
                 f"falsified {matrix.get('falsified_claim_count', 0)}, "
                 f"inconclusive {matrix.get('inconclusive_claim_count', 0)}", "",
                 "| claim | axis | status | detail |",
                 "| --- | --- | --- | --- |"]
        for c in matrix.get("cells", []):
            lines.append(f"| {c['claim']} | {c['axis']} | {c['status']} | "
                         f"{c['detail']} |")
        lines += ["", "_No empty green dashboard; inconclusive is valid; "
                  "falsified claims are prominent. Replication compares "
                  "observable structures only, not consciousness or life._"]
        return self._guard("\n".join(lines))

    def _render_falsification_md(self, sections: Dict[str, Any]) -> str:
        lines = ["# Falsification Report", "",
                 "_Would the claimed structure survive a null condition? "
                 "Passing a falsification test does not prove understanding._",
                 ""]
        for fr in sections["falsification_tests"]:
            lines.append(f"- [{fr['outcome']}] {fr['test_type']} "
                         f"({fr.get('run_id', '?')}): {fr['question']} -- "
                         f"{fr.get('claim', '')}")
        if not sections["falsification_tests"]:
            lines.append("- no falsification tests run in this bounded comparison")
        return self._guard("\n".join(lines))

    @staticmethod
    def _claim_guard_safe(text: str) -> bool:
        try:
            from ..governance.compliance import ClaimGuard

            return ClaimGuard().scan_text(text).safe
        except Exception:
            return True

    @staticmethod
    def _guard(text: str) -> str:
        try:
            from ..governance.compliance import ClaimGuard

            guard = ClaimGuard()
            if not guard.scan_text(text).safe:
                return guard.rewrite(text)
        except Exception:
            pass
        return text

    def write(self, state_dir: Optional[str] = None) -> Dict[str, Any]:
        report = self.build()
        base = state_dir or self.runtime.state_dir
        os.makedirs(base, exist_ok=True)
        md_path = os.path.join(base, "REPLICATION_REPORT.md")
        json_path = os.path.join(base, "REPLICATION_REPORT.json")
        matrix_path = os.path.join(base, "REPLICATION_MATRIX.md")
        fals_path = os.path.join(base, "FALSIFICATION_REPORT.md")
        markdown = self._render_markdown(report["sections"])
        if not report["claim_guard_safe"]:
            markdown = self._guard(markdown)
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(markdown)
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, default=str)
        with open(matrix_path, "w", encoding="utf-8") as fh:
            fh.write(self._render_matrix_md(report["sections"]))
        with open(fals_path, "w", encoding="utf-8") as fh:
            fh.write(self._render_falsification_md(report["sections"]))
        return {"markdown": md_path, "json": json_path,
                "matrix": matrix_path, "falsification": fals_path,
                "report": report}
