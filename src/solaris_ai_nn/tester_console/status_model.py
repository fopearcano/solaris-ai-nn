"""Console status model -- per-stage tester-release health from discovered artifacts.

:class:`TesterConsoleStatus` aggregates per-stage :class:`StageStatus` health derived
read-only from the discovered artifacts. A missing *optional* stage is reported as
``skipped_optional`` (not failure); a missing *required* tester-release stage is a
visible blocker. Safety blockers override cosmetic success, and the model never hides
failed gates, quarantine, or membrane bypasses.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class StageHealth:
    NOT_STARTED = "not_started"
    READY = "ready"
    PASS = "pass"
    PASS_WITH_WARNINGS = "pass_with_warnings"
    BLOCKED = "blocked"
    FAILED = "failed"
    MISSING_ARTIFACTS = "missing_artifacts"
    SKIPPED_OPTIONAL = "skipped_optional"
    UNKNOWN = "unknown"

    ALL = (NOT_STARTED, READY, PASS, PASS_WITH_WARNINGS, BLOCKED, FAILED,
           MISSING_ARTIFACTS, SKIPPED_OPTIONAL, UNKNOWN)

    _OK = (READY, PASS, PASS_WITH_WARNINGS, SKIPPED_OPTIONAL, NOT_STARTED)


# (stage_id, required_for_tester_release, optional_stage)
_STAGES = (
    ("install_doctor", False, False),
    ("alpha_fixture", False, False),
    ("tester_fixture_demo", True, False),
    ("golden_reproducibility", True, False),
    ("tester_live_init", False, False),
    ("tester_live_doctor", False, False),
    ("live_birth", False, False),
    ("environmental_membrane", False, False),
    ("membrane_integration", False, False),
    ("live_observation", False, False),
    ("live_ontogenesis", False, True),
    ("live_semiogenesis", False, True),
    ("live_cognition", False, True),
    ("scientific_claims", False, False),
    ("tester_bundles", False, False),
    ("documentation", False, False),
    ("feedback_readiness", False, False),
)


@dataclass
class ConsoleBlocker:
    """A blocker surfaced on the dashboard (never hidden)."""

    stage: str
    detail: str
    severity: str = "blocker"

    def to_dict(self) -> Dict[str, Any]:
        return {"stage": self.stage, "detail": self.detail,
                "severity": self.severity}


@dataclass
class ConsoleWarning:
    """A warning surfaced on the dashboard."""

    stage: str
    detail: str

    def to_dict(self) -> Dict[str, Any]:
        return {"stage": self.stage, "detail": self.detail}


@dataclass
class StageStatus:
    """The health of one tester-release stage."""

    stage: str
    health: str = StageHealth.UNKNOWN
    required: bool = False
    optional: bool = False
    detail: str = ""
    report_path: str = ""

    @property
    def ok(self) -> bool:
        return self.health in StageHealth._OK

    def to_dict(self) -> Dict[str, Any]:
        return {"stage": self.stage, "health": self.health,
                "required": self.required, "optional": self.optional,
                "detail": self.detail, "report_path": self.report_path}


@dataclass
class TesterConsoleStatus:
    """The aggregate per-stage tester-release status."""

    stages: List[StageStatus] = field(default_factory=list)
    blockers: List[ConsoleBlocker] = field(default_factory=list)
    warnings: List[ConsoleWarning] = field(default_factory=list)

    def stage(self, stage_id: str) -> Optional[StageStatus]:
        for s in self.stages:
            if s.stage == stage_id:
                return s
        return None

    @property
    def overall_health(self) -> str:
        if self.blockers:
            return StageHealth.BLOCKED
        if any(s.health == StageHealth.FAILED for s in self.stages):
            return StageHealth.FAILED
        missing_required = [s for s in self.stages
                            if s.required and s.health in (
                                StageHealth.MISSING_ARTIFACTS,
                                StageHealth.NOT_STARTED)]
        if missing_required:
            return StageHealth.MISSING_ARTIFACTS
        if any(s.health == StageHealth.PASS_WITH_WARNINGS for s in self.stages) \
                or self.warnings:
            return StageHealth.PASS_WITH_WARNINGS
        if any(s.health == StageHealth.PASS for s in self.stages):
            return StageHealth.PASS
        return StageHealth.NOT_STARTED

    @property
    def release_ready(self) -> bool:
        if self.blockers:
            return False
        for s in self.stages:
            if s.required and not s.ok:
                return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_health": self.overall_health,
            "release_ready": self.release_ready,
            "stage_count": len(self.stages),
            "blocker_count": len(self.blockers),
            "warning_count": len(self.warnings),
            "stages": [s.to_dict() for s in self.stages],
            "blockers": [b.to_dict() for b in self.blockers],
            "warnings": [w.to_dict() for w in self.warnings],
            "note": "missing optional stages are not failures; safety blockers "
                    "override cosmetic success; failed gates/quarantine/bypass "
                    "are never hidden",
        }


@dataclass
class StatusModelBuilder:
    """Builds the per-stage status model from discovered artifacts."""

    def build(self, discovery, safety_panel=None) -> TesterConsoleStatus:
        from .artifact_discovery import ArtifactKind as K

        status = TesterConsoleStatus()
        for stage_id, required, optional in _STAGES:
            health, detail, path = self._stage_health(stage_id, discovery, K)
            st = StageStatus(stage=stage_id, health=health, required=required,
                             optional=optional, detail=detail, report_path=path)
            status.stages.append(st)
            if required and health in (StageHealth.MISSING_ARTIFACTS,
                                       StageHealth.NOT_STARTED):
                status.blockers.append(ConsoleBlocker(
                    stage=stage_id,
                    detail=f"required tester-release stage {stage_id!r} has no "
                           "artifacts yet"))
            if health == StageHealth.FAILED:
                status.blockers.append(ConsoleBlocker(
                    stage=stage_id, detail=detail or f"{stage_id} failed"))
            if health == StageHealth.PASS_WITH_WARNINGS:
                status.warnings.append(ConsoleWarning(stage=stage_id,
                                                      detail=detail))
        # Safety panel blockers override cosmetic success.
        if safety_panel is not None:
            for finding in getattr(safety_panel, "blocking_findings", lambda: [])():
                status.blockers.append(ConsoleBlocker(
                    stage="safety", detail=finding.detail or finding.check,
                    severity="safety_blocker"))
        return status

    def _stage_health(self, stage_id, discovery, K):
        def latest(kind):
            return discovery.latest(kind)

        if stage_id == "tester_fixture_demo":
            art = latest(K.TESTER_FIXTURE_REPORT)
            if not art:
                return (StageHealth.MISSING_ARTIFACTS,
                        "no fixture tester demo run found", "")
            repro = art.summary.get("reproducibility_status")
            if repro in ("fail", "blocked"):
                return StageHealth.FAILED, "fixture reproducibility failed", \
                    art.path
            return (StageHealth.PASS, "fixture tester demo present", art.path)

        if stage_id == "golden_reproducibility":
            repro = latest(K.TESTER_REPRODUCIBILITY_REPORT) \
                or latest(K.TESTER_FIXTURE_REPORT)
            if not repro:
                return (StageHealth.MISSING_ARTIFACTS,
                        "no reproducibility/golden run found", "")
            status = repro.summary.get("reproducibility_status", "")
            if status == "fail":
                return StageHealth.FAILED, "reproducibility failed", repro.path
            if status == "pass_with_warnings":
                return (StageHealth.PASS_WITH_WARNINGS,
                        "reproducibility passed with warnings", repro.path)
            return StageHealth.PASS, "reproducibility present", repro.path

        if stage_id in ("live_ontogenesis", "live_semiogenesis",
                        "live_cognition"):
            kind = {"live_ontogenesis": K.CONCEPT_MEMORY,
                    "live_semiogenesis": K.SIGN_MEMORY,
                    "live_cognition": K.COGNITION_MEMORY}[stage_id]
            art = latest(kind)
            if not art:
                return (StageHealth.SKIPPED_OPTIONAL,
                        "optional layer not run", "")
            return StageHealth.PASS, "optional layer present", art.path

        mapping = {
            "alpha_fixture": K.ALPHA_REPORT,
            "tester_live_init": K.LIVE_GOVERNANCE,
            "tester_live_doctor": K.TESTER_LIVE_REPORT,
            "live_birth": K.LIVE_BIRTH_REPORT,
            "environmental_membrane": K.MEMBRANE_REPORT,
            "membrane_integration": K.MEMBRANE_INTEGRATION_REPORT,
            "live_observation": K.OBSERVATION_REPORT,
            "scientific_claims": K.SCIENTIFIC_CLAIM_REPORT,
            "tester_bundles": K.TESTER_FIXTURE_BUNDLE,
            "documentation": K.ARCHITECTURE_DOCS,
        }
        kind = mapping.get(stage_id)
        if kind is None:
            return StageHealth.NOT_STARTED, "", ""
        art = latest(kind)
        if not art:
            return StageHealth.NOT_STARTED, "not run yet", ""
        if art.summary.get("blocked") or art.summary.get("live_birth_blocked"):
            return StageHealth.BLOCKED, f"{stage_id} reported blocked", art.path
        return StageHealth.PASS, f"{stage_id} present", art.path
