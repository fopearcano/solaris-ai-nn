"""Research report -- the claim-guarded account of what the evidence shows.

The :class:`ResearchReportBuilder` assembles the research question, designs,
variants/baselines/ablations tested, metrics, null-model results, comparisons,
module-effect analysis, the safety summary, reproducibility status, the
leaderboard, conclusions, limitations, and recommended architecture changes into
a JSON + Markdown report. The Markdown is ClaimGuard-scanned; benchmark scores
are never consciousness scores.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ResearchReport:
    report_id: str
    sections: Dict[str, Any] = field(default_factory=dict)
    narrative: str = ""
    claim_guard_safe: bool = True
    claim_guard_findings: int = 0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {"report_id": self.report_id, "timestamp": self.timestamp,
                "claim_guard_safe": self.claim_guard_safe,
                "claim_guard_findings": self.claim_guard_findings,
                "sections": self.sections, "narrative": self.narrative}


@dataclass
class ResearchReportBuilder:
    base_dir: str = ".solaris_ai_nn_research"

    def build(self, *, designs: Optional[List[Any]] = None,
              variants: Optional[List[str]] = None,
              baselines: Optional[List[str]] = None,
              ablations: Optional[List[str]] = None,
              metrics_snapshot: Optional[Dict] = None,
              null_model_results: Optional[List[Dict]] = None,
              comparisons: Optional[List[Dict]] = None,
              effect_analysis: Any = None, safety_summary: Optional[Dict] = None,
              reproducibility: Optional[Dict] = None, leaderboard: Any = None,
              extra: Optional[Dict[str, Any]] = None) -> ResearchReport:
        extra = dict(extra or {})
        effects = (effect_analysis.to_dict()
                   if hasattr(effect_analysis, "to_dict")
                   else (effect_analysis or {}))
        board = (leaderboard.to_dict() if hasattr(leaderboard, "to_dict")
                 else (leaderboard or {}))
        sections: Dict[str, Any] = {
            "research_question": extra.get(
                "research_question",
                "Which architectural components produce measurable structural "
                "development, stability, prediction, grounding, compression, "
                "safety, or adaptability?"),
            "experiment_designs": [d.to_dict() if hasattr(d, "to_dict") else d
                                   for d in (designs or [])],
            "variants_tested": variants or [],
            "baselines_tested": baselines or [],
            "ablations_tested": ablations or [],
            "metrics": metrics_snapshot or {},
            "null_model_results": null_model_results or [],
            "comparison_results": comparisons or [],
            "module_effect_analysis": effects,
            "safety_invariant_summary": safety_summary or {},
            "reproducibility_status": reproducibility or {},
            "leaderboard": board,
            "conclusions": extra.get("conclusions", [
                "Findings are provisional and evidence-scoped.",
                "The full system does not automatically outperform simpler "
                "baselines on every metric.",
            ]),
            "limitations": [
                "Bounded fixture/simulated experiments, not real long runs.",
                "Single/few runs; differences are observed, not causal.",
                "Benchmark scores are operational proxies; they do not measure "
                "or prove consciousness, sentience, life, personhood, or free "
                "will.",
                "Negative and inconclusive results are preserved, not hidden.",
            ],
            "recommended_architecture_changes": extra.get(
                "recommended_architecture_changes",
                ["Re-test inconclusive modules with more runs before pruning.",
                 "Keep all hard safety boundaries enabled regardless of "
                 "findings."]),
        }
        narrative = self._narrative(sections)
        from ..governance.compliance import ClaimGuard

        scan = ClaimGuard().scan_text(narrative)
        if not scan.safe:
            narrative = ClaimGuard().rewrite(narrative)
        return ResearchReport(
            report_id=f"RESRPT_{uuid.uuid4().hex[:10]}", sections=sections,
            narrative=narrative, claim_guard_safe=scan.safe,
            claim_guard_findings=len(scan.findings))

    def _narrative(self, sections: Dict[str, Any]) -> str:
        effects = sections["module_effect_analysis"]
        lines = [
            "# Research Report",
            "",
            "This reports a bounded, evidence-based architecture validation of "
            "a software system. It compares the full architecture against "
            "minimal, random, fixed-policy, and ablated variants using shared "
            "operational metrics. **Benchmark scores are operational proxies "
            "(prediction, compression, grounding, stability, safety, "
            "reproducibility); they do not measure or prove consciousness, "
            "sentience, life, personhood, or free will.**",
            "",
            "## Research question",
            f"- {sections['research_question']}",
            "",
            "## Coverage",
            f"- variants tested: {len(sections['variants_tested'])}",
            f"- baselines tested: {len(sections['baselines_tested'])}",
            f"- ablations tested: {len(sections['ablations_tested'])}",
            "",
            "## Module effect analysis",
            f"- positive modules: {effects.get('positive_modules', [])}",
            f"- harmful candidates: {effects.get('harmful_candidates', [])}",
            f"- inconclusive: {effects.get('inconclusive_candidates', [])}",
            "",
            "## Leaderboard",
            f"- best overall (operational): "
            f"{sections['leaderboard'].get('best_overall')}",
            "",
            "## Conclusions",
        ]
        lines += [f"- {c}" for c in sections["conclusions"]]
        lines += ["", "## Limitations"]
        lines += [f"- {lim}" for lim in sections["limitations"]]
        return "\n".join(lines)

    def write(self, report: ResearchReport) -> Dict[str, str]:
        os.makedirs(self.base_dir, exist_ok=True)
        md_path = os.path.join(self.base_dir, "RESEARCH_REPORT.md")
        json_path = os.path.join(self.base_dir, "RESEARCH_REPORT.json")
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(report.narrative)
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(report.to_dict(), fh, indent=2, default=str)
        return {"markdown": md_path, "json": json_path}

    def build_and_write(self, **kwargs: Any) -> ResearchReport:
        report = self.build(**kwargs)
        report.sections["report_paths"] = self.write(report)
        return report
