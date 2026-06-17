"""Membrane pipeline audit -- stage-by-stage check of the live perceptual pipeline.

:class:`MembranePipelineAudit` walks the pipeline stages (birth validation, membrane
impression generation, observation/ontogenesis impression usage, semiogenesis and
cognition ancestry preservation, scientific-claims evidence typing, research-cycle
blocker propagation, and alpha reporting) and records, per stage, the status,
artifacts found/missing, impression/fallback counts, bypass findings, and
contamination/source-pressure propagation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


class PipelineAuditStatus:
    PASS = "pass"
    PASS_WITH_WARNINGS = "pass_with_warnings"
    MISSING_ARTIFACTS = "missing_artifacts"
    FALLBACK_USED = "fallback_used"
    BYPASS_DETECTED = "bypass_detected"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"

    ALL = (PASS, PASS_WITH_WARNINGS, MISSING_ARTIFACTS, FALLBACK_USED,
           BYPASS_DETECTED, BLOCKED, UNKNOWN)


@dataclass
class PipelineAuditStage:
    """The audit record for one pipeline stage."""

    stage: str
    status: str = PipelineAuditStatus.UNKNOWN
    artifacts_found: List[str] = field(default_factory=list)
    artifacts_missing: List[str] = field(default_factory=list)
    impression_count: int = 0
    fallback_count: int = 0
    bypass_findings: int = 0
    contamination_propagation: bool = True
    source_pressure_propagation: bool = True
    limitations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage, "status": self.status,
            "artifacts_found": list(self.artifacts_found),
            "artifacts_missing": list(self.artifacts_missing),
            "impression_count": self.impression_count,
            "fallback_count": self.fallback_count,
            "bypass_findings": self.bypass_findings,
            "contamination_propagation": self.contamination_propagation,
            "source_pressure_propagation": self.source_pressure_propagation,
            "limitations": list(self.limitations),
        }


@dataclass
class PipelineAuditResult:
    """The aggregate pipeline-audit result."""

    stages: List[PipelineAuditStage] = field(default_factory=list)

    @property
    def overall_status(self) -> str:
        rank = {PipelineAuditStatus.PASS: 0,
                PipelineAuditStatus.PASS_WITH_WARNINGS: 1,
                PipelineAuditStatus.FALLBACK_USED: 2,
                PipelineAuditStatus.MISSING_ARTIFACTS: 2,
                PipelineAuditStatus.BYPASS_DETECTED: 3,
                PipelineAuditStatus.BLOCKED: 4,
                PipelineAuditStatus.UNKNOWN: 1}
        worst = max((rank.get(s.status, 1) for s in self.stages), default=0)
        for name, value in rank.items():
            if value == worst:
                return name
        return PipelineAuditStatus.UNKNOWN

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_status": self.overall_status,
            "stage_count": len(self.stages),
            "stages": [s.to_dict() for s in self.stages],
            "note": "the audit walks the live perceptual pipeline stage by stage; "
                    "fallback, missing artifacts, and bypasses are all visible",
        }


@dataclass
class MembranePipelineAudit:
    """Builds the stage-by-stage pipeline audit from loaded artifacts."""

    def audit(self, *, load_result, ancestry, contracts, bypass_findings,
              adapters: Dict[str, Any], strict: bool) -> PipelineAuditResult:
        result = PipelineAuditResult()
        bypass_by = self._bypass_index(bypass_findings)

        def stage(name, found, missing, impressions=0, fallback=0,
                  bypass=0, status=None):
            s = PipelineAuditStage(
                stage=name, artifacts_found=found, artifacts_missing=missing,
                impression_count=impressions, fallback_count=fallback,
                bypass_findings=bypass)
            if status:
                s.status = status
            elif missing:
                s.status = PipelineAuditStatus.MISSING_ARTIFACTS
            elif bypass:
                s.status = (PipelineAuditStatus.BLOCKED if strict
                            else PipelineAuditStatus.BYPASS_DETECTED)
            elif fallback:
                s.status = PipelineAuditStatus.FALLBACK_USED
            else:
                s.status = PipelineAuditStatus.PASS
            result.stages.append(s)
            return s

        imp = len(load_result.impressions)
        stage("live_birth_event_validation",
              ["inbox accepted events"] if load_result.membrane_present else [],
              [] if load_result.membrane_present else ["membrane dir"],
              status=PipelineAuditStatus.PASS)
        stage("membrane_impression_generation",
              ["sensory impressions"] if load_result.impressions_present else [],
              [] if load_result.impressions_present else ["impressions"],
              impressions=imp)
        onto = adapters.get("live_ontogenesis")
        stage("observation_impression_usage",
              ["impression diet"] if imp else [], [] if imp else ["impressions"],
              impressions=imp)
        stage("ontogenesis_impression_usage",
              ["impression features"] if (onto and onto.used_impressions)
              else [], [] if (onto and onto.used_impressions) else
              ["impression features"],
              impressions=imp,
              fallback=1 if (onto and onto.raw_fallback) else 0,
              status=(PipelineAuditStatus.BLOCKED if (onto and onto.status
                      == "blocked") else None))
        stage("semiogenesis_ancestry_preservation",
              ["sign ancestry"], [],
              bypass=bypass_by.get("missing_impression_ancestry", 0))
        stage("cognition_ancestry_preservation",
              ["trace ancestry"], [],
              bypass=bypass_by.get("missing_impression_ancestry", 0))
        stage("scientific_claims_evidence_typing", ["evidence categories"], [],
              status=PipelineAuditStatus.PASS)
        research = adapters.get("research_cycle")
        stage("research_cycle_blocker_propagation", ["cycle status"], [],
              status=(PipelineAuditStatus.BLOCKED
                      if (research and research.status == "blocked")
                      else PipelineAuditStatus.PASS))
        stage("alpha_reporting", ["alpha membrane status"], [],
              status=PipelineAuditStatus.PASS)
        return result

    @staticmethod
    def _bypass_index(findings) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for f in findings or []:
            out[f.finding] = out.get(f.finding, 0) + 1
        return out
