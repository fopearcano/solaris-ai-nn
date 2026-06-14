"""Post-pilot report -- run the whole forensic pipeline, write the summary.

The :class:`PostPilotReportBuilder` ties the post-pilot package together: it
loads artifacts, builds baseline comparisons, derives structural-change
evidence, classifies accumulation vs growth, audits traceability, builds the
developmental-evidence ledger, runs regression analysis, packages
reproducibility, and applies the Phase-2 decision gate -- then writes a
ClaimGuard-scanned POST_PILOT_ANALYSIS report (Markdown + JSON).
"""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .accumulation_vs_growth import AccumulationVsGrowthAnalyzer
from .artifact_loader import PilotArtifactLoader
from .baseline import BaselineComparator
from .decision_gate import Phase2DecisionGate
from .developmental_evidence import DevelopmentalEvidenceLedger
from .regression_analysis import RegressionAnalyzer
from .reproducibility import ReproducibilityPackager
from .safety import PostPilotSafetyValidator
from .structural_change import StructuralChangeAnalyzer
from .trace_audit import DevelopmentalTraceAuditor


@dataclass
class PostPilotAnalysis:
    """The full bundle of post-pilot analysis results."""

    analysis_id: str
    artifacts: Any = None
    comparison: Any = None
    structural_evidence: List[Any] = field(default_factory=list)
    growth: Any = None
    trace_audit: Any = None
    ledger: Any = None
    regression: Any = None
    reproducibility: Any = None
    reproducibility_paths: Dict[str, str] = field(default_factory=dict)
    decision: Any = None
    narrative: str = ""
    claim_guard_safe: bool = True
    claim_guard_findings: int = 0
    report_paths: Dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def summary(self) -> Dict[str, Any]:
        idx = getattr(getattr(self.artifacts, "index", None), "to_dict",
                      lambda: {})()
        return {
            "analysis_id": self.analysis_id,
            "artifact_completeness": idx.get("completeness", 0.0),
            "missing_artifacts": idx.get("missing", []),
            "growth_classification": getattr(
                self.growth, "final_classification", "inconclusive"),
            "structural_evidence_count": len(self.structural_evidence),
            "traceability_score": getattr(self.trace_audit,
                                          "traceability_score", 0.0),
            "regression_severity": getattr(self.regression,
                                           "overall_severity", "none"),
            "phase2_recommendation": getattr(self.decision, "recommendation",
                                             None),
            "decision_confidence": getattr(self.decision, "confidence", 0.0),
            "report_path": self.report_paths.get("json"),
            "claim_guard_safe": self.claim_guard_safe,
        }


@dataclass
class PostPilotReportBuilder:
    """Runs the forensic pipeline and writes POST_PILOT_ANALYSIS.*"""

    base_dir: str = ".solaris_ai_nn_pilot1"
    state_dir: str = ".solaris_ai_nn_state"
    safety: PostPilotSafetyValidator = field(
        default_factory=PostPilotSafetyValidator)

    def analyze(self, *, artifacts: Any = None,
                before: Optional[Dict[str, Any]] = None,
                after: Optional[Dict[str, Any]] = None,
                before_simulated: bool = False,
                after_simulated: bool = False,
                signals: Optional[Dict[str, Any]] = None,
                run_context: Optional[Dict[str, Any]] = None,
                write_reproducibility: bool = True) -> PostPilotAnalysis:
        if artifacts is None:
            artifacts = PilotArtifactLoader(self.base_dir,
                                            self.state_dir).load()
        analysis = PostPilotAnalysis(
            analysis_id=f"PPA_{uuid.uuid4().hex[:10]}", artifacts=artifacts)

        # Baseline comparison (derive from report sections when not supplied).
        before = before or self._derive_before(artifacts)
        after = after or self._derive_after(artifacts)
        comparator = BaselineComparator()
        analysis.comparison = comparator.compare_dicts(
            "before", before, "after", after,
            before_simulated=before_simulated,
            after_simulated=after_simulated)

        # Structural change + growth.
        analysis.structural_evidence = StructuralChangeAnalyzer().analyze(
            analysis.comparison, artifacts)
        analysis.growth = AccumulationVsGrowthAnalyzer().analyze(
            analysis.comparison, analysis.structural_evidence, artifacts,
            signals)

        # Trace audit + evidence ledger.
        analysis.trace_audit = DevelopmentalTraceAuditor().audit(artifacts)
        analysis.ledger = DevelopmentalEvidenceLedger()
        analysis.ledger.from_structural_evidence(analysis.structural_evidence)
        analysis.ledger.add(
            "structural_growth_detected" if "growth" in str(
                getattr(analysis.growth, "final_classification", ""))
            else "mostly_accumulation_detected",
            statement=f"classification="
                      f"{getattr(analysis.growth, 'final_classification', '')}",
            evidence_refs=[analysis.analysis_id],
            artifact_types=getattr(getattr(artifacts, "index", None),
                                   "present", []))

        # Regression + reproducibility + decision.
        analysis.regression = RegressionAnalyzer().analyze(
            analysis.comparison, signals)
        packager = ReproducibilityPackager(base_dir=self.base_dir)
        analysis.reproducibility = packager.build(artifacts)
        if write_reproducibility:
            analysis.reproducibility_paths = packager.write(
                analysis.reproducibility)

        safety_incidents = self._safety_incident_count(artifacts)
        analysis.decision = Phase2DecisionGate().decide(
            growth=analysis.growth, regression=analysis.regression,
            trace_audit=analysis.trace_audit, artifacts=artifacts,
            safety_incident_count=safety_incidents,
            reproducibility_complete=bool(analysis.reproducibility_paths),
            report_complete="pilot_report" in getattr(
                getattr(artifacts, "index", None), "present", []),
            identity_continuity_failed=not getattr(
                analysis.comparison, "identity_continuous", True))

        analysis._run_context = run_context or {}
        return analysis

    def build(self, analysis: Optional[PostPilotAnalysis] = None, **kwargs: Any,
              ) -> PostPilotAnalysis:
        analysis = analysis or self.analyze(**kwargs)
        sections = self._sections(analysis)
        narrative = self._narrative(sections)
        from ..governance.compliance import ClaimGuard

        scan = ClaimGuard().scan_text(narrative)
        # Post-pilot safety: also block unsupported consciousness phrasing.
        claim_check = self.safety.validate_claim_text(narrative)
        if not scan.safe or not claim_check.safe:
            narrative = ClaimGuard().rewrite(narrative)
        analysis.narrative = narrative
        analysis.claim_guard_safe = scan.safe and claim_check.safe
        analysis.claim_guard_findings = len(scan.findings)
        analysis._sections_cache = sections
        return analysis

    def _sections(self, a: PostPilotAnalysis) -> Dict[str, Any]:
        idx = getattr(getattr(a.artifacts, "index", None), "to_dict",
                      lambda: {})()
        return {
            "artifact_completeness": idx,
            "baseline_comparison": (a.comparison.to_dict()
                                    if hasattr(a.comparison, "to_dict")
                                    else {}),
            "structural_change_evidence": [
                e.to_dict() for e in a.structural_evidence],
            "accumulation_vs_growth": (a.growth.to_dict()
                                       if hasattr(a.growth, "to_dict")
                                       else {}),
            "developmental_evidence_ledger": (a.ledger.snapshot()
                                              if hasattr(a.ledger, "snapshot")
                                              else {}),
            "regression_analysis": (a.regression.to_dict()
                                    if hasattr(a.regression, "to_dict")
                                    else {}),
            "trace_audit": (a.trace_audit.to_dict()
                            if hasattr(a.trace_audit, "to_dict") else {}),
            "reproducibility_package": {
                "built": a.reproducibility is not None,
                "paths": a.reproducibility_paths},
            "decision_gate": (a.decision.to_dict()
                              if hasattr(a.decision, "to_dict") else {}),
            "limitations": [
                "All findings are evidence-scoped; missing artifacts weaken "
                "them.",
                "Operational success is not cognitive proof; no consciousness "
                "claim is made.",
                "Simulated-time runs are not real-time evidence.",
            ],
        }

    def _narrative(self, sections: Dict[str, Any]) -> str:
        growth = sections["accumulation_vs_growth"]
        decision = sections["decision_gate"]
        idx = sections["artifact_completeness"]
        lines = [
            "# Post-Pilot Analysis",
            "",
            "This is a forensic analysis of a bounded software process. It "
            "evaluates operational continuity, traceability, and "
            "structural-change proxies. It does not, and cannot, demonstrate "
            "consciousness, sentience, understanding, or life.",
            "",
            "## Artifact completeness",
            f"- completeness: {idx.get('completeness', 0.0)}",
            f"- missing: {', '.join(idx.get('missing', [])) or 'none'}",
            f"- unreadable: {', '.join(idx.get('unreadable', [])) or 'none'}",
            "",
            "## Accumulation vs growth",
            f"- classification: **{growth.get('final_classification')}**",
            f"- accumulation/growth scores: {growth.get('accumulation_score')}"
            f" / {growth.get('growth_score')}",
            "",
            "## Structural change evidence",
            f"- {len(sections['structural_change_evidence'])} evidence "
            "record(s) (see JSON for confidences and stability)",
            "",
            "## Trace audit",
            f"- traceability score: "
            f"{sections['trace_audit'].get('traceability_score', 0.0)}",
            "",
            "## Regression",
            f"- overall severity: "
            f"{sections['regression_analysis'].get('overall_severity')}",
            "",
            "## Phase-2 decision",
            f"- recommendation: **{decision.get('recommendation', 'n/a')}**",
            f"- confidence: {decision.get('confidence', 0.0)}",
            f"- blockers: {', '.join(decision.get('blockers', [])) or 'none'}",
            "",
            "## Limitations",
        ]
        lines += [f"- {lim}" for lim in sections["limitations"]]
        return "\n".join(lines)

    def write(self, analysis: PostPilotAnalysis) -> Dict[str, str]:
        os.makedirs(self.base_dir, exist_ok=True)
        sections = getattr(analysis, "_sections_cache", None) \
            or self._sections(analysis)
        md_path = os.path.join(self.base_dir, "POST_PILOT_ANALYSIS.md")
        json_path = os.path.join(self.base_dir, "POST_PILOT_ANALYSIS.json")
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(analysis.narrative)
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump({"summary": analysis.summary(), "sections": sections},
                      fh, indent=2, default=str)
        analysis.report_paths = {"markdown": md_path, "json": json_path}
        return analysis.report_paths

    def build_and_write(self, **kwargs: Any) -> PostPilotAnalysis:
        analysis = self.build(**kwargs)
        self.write(analysis)
        return analysis

    # -- helpers ----------------------------------------------------------------

    @staticmethod
    def _derive_before(artifacts: Any) -> Dict[str, Any]:
        data = getattr(artifacts, "data", {}) or {}
        daily = data.get("daily") or []
        if daily:
            return PostPilotReportBuilder._snap_from_daily(daily[0])
        return {}

    @staticmethod
    def _derive_after(artifacts: Any) -> Dict[str, Any]:
        data = getattr(artifacts, "data", {}) or {}
        daily = data.get("daily") or []
        if daily:
            return PostPilotReportBuilder._snap_from_daily(daily[-1])
        report = data.get("pilot_report") or {}
        return {"structural_change_score": float(
            (report.get("sections", {}) or {}).get(
                "structural_change_analysis", {}).get(
                "structural_change_score", 0.0) or 0.0)}

    @staticmethod
    def _snap_from_daily(day: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "proto_symbol_count": day.get("proto_symbol_changes", 0),
            "structural_change_score": day.get("structural_change_delta", 0.0),
            "safety_incident_count": day.get("safety_incidents", 0),
            "stagnation_seconds": float(day.get("stagnation_hours", 0.0) or 0.0)
            * 3600.0,
        }

    @staticmethod
    def _safety_incident_count(artifacts: Any) -> int:
        data = getattr(artifacts, "data", {}) or {}
        incidents = data.get("incidents") or []
        return sum(1 for i in incidents if isinstance(i, dict)
                   and str(i.get("payload", {}).get("severity",
                                                    i.get("severity", "")))
                   == "critical")
