"""Post-pilot forensics -- the one read-only entry point for run analysis.

The :class:`PostPilotForensics` is a thin façade over the post-pilot package:
it loads artifacts, runs the full analysis pipeline, builds the post-pilot
report and the research dossier, and returns everything as one bundle. It
performs **no** cognition loop, **no** runtime mutation, and **no** repairs --
it only reads artifacts and writes analysis outputs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .artifact_loader import PilotArtifactLoader
from .reports import PostPilotAnalysis, PostPilotReportBuilder
from .research_dossier import ResearchDossierBuilder
from .safety import PostPilotSafetyValidator


@dataclass
class PostPilotForensics:
    """Read-only orchestrator for post-pilot developmental forensics."""

    base_dir: str = ".solaris_ai_nn_pilot1"
    state_dir: str = ".solaris_ai_nn_state"
    safety: PostPilotSafetyValidator = field(
        default_factory=PostPilotSafetyValidator)

    def run(self, *, before: Optional[Dict[str, Any]] = None,
            after: Optional[Dict[str, Any]] = None,
            signals: Optional[Dict[str, Any]] = None,
            run_context: Optional[Dict[str, Any]] = None,
            write_dossier: bool = True,
            write_report: bool = True) -> Dict[str, Any]:
        """Load artifacts, analyze, and (optionally) write report + dossier."""
        artifacts = PilotArtifactLoader(self.base_dir, self.state_dir).load()
        report_builder = PostPilotReportBuilder(
            base_dir=self.base_dir, state_dir=self.state_dir,
            safety=self.safety)
        analysis: PostPilotAnalysis = report_builder.build(
            artifacts=artifacts, before=before, after=after, signals=signals,
            run_context=run_context)
        if write_report:
            report_builder.write(analysis)
        dossier = None
        if write_dossier:
            dossier = ResearchDossierBuilder(base_dir=self.base_dir).build_and_write(
                artifacts=artifacts, baseline=analysis.comparison,
                structural=analysis.structural_evidence, growth=analysis.growth,
                trace_audit=analysis.trace_audit, ledger=analysis.ledger,
                regression=analysis.regression,
                reproducibility=analysis.reproducibility,
                decision=analysis.decision, run_context=run_context)
        return {
            "analysis": analysis,
            "summary": analysis.summary(),
            "report_paths": analysis.report_paths,
            "dossier": dossier,
            "dossier_paths": (dossier.sections.get("dossier_paths")
                              if dossier is not None else None),
            "read_only": True,
            "mutated_runtime": False,
        }
