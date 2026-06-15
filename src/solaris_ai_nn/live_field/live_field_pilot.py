"""Live field pilot -- a bounded, governed, phased real read-only field run.

:class:`LiveFieldPilot` runs the phases of a live-field pilot: preflight, feeder
validation, baseline observation, continuous exposure, absence monitoring,
cross-modal observation, changed-perception probe, comparison, and report. The
default pilot is bounded (10 minutes, 15-minute hard cap) and can be shortened for
tests. It never runs automatically: live mode requires governance approval, and a
fixture fallback is used if no real feeders exist.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .live_field_runtime import LiveFieldRuntime


class LiveFieldPilotPhase:
    PREFLIGHT = "preflight"
    FEEDER_VALIDATION = "feeder_validation"
    BASELINE_OBSERVATION = "baseline_observation"
    CONTINUOUS_EXPOSURE = "continuous_exposure"
    ABSENCE_MONITORING = "absence_monitoring"
    CROSS_MODAL_OBSERVATION = "cross_modal_observation"
    CHANGED_PERCEPTION_PROBE = "changed_perception_probe"
    COMPARISON = "comparison"
    REPORT = "report"

    ALL = (PREFLIGHT, FEEDER_VALIDATION, BASELINE_OBSERVATION,
           CONTINUOUS_EXPOSURE, ABSENCE_MONITORING, CROSS_MODAL_OBSERVATION,
           CHANGED_PERCEPTION_PROBE, COMPARISON, REPORT)


@dataclass
class LiveFieldPilotConfig:
    """Bounded pilot configuration (shortenable for tests)."""

    duration_s: float = 600.0          # 10 minutes default
    hard_cap_s: float = 900.0          # 15 minute hard cap
    poll_interval_s: float = 1.0
    max_ticks: int = 120
    max_events_total: int = 2000
    live: bool = False                 # live mode requires governance
    fixture_fallback: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class LiveFieldPilotResult:
    phases_run: List[str] = field(default_factory=list)
    refused: bool = False
    refusal_reasons: List[str] = field(default_factory=list)
    runtime_status: Dict[str, Any] = field(default_factory=dict)
    comparison: Optional[Dict[str, Any]] = None
    changed_perception: Optional[Dict[str, Any]] = None
    report_paths: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "phases_run": list(self.phases_run),
            "refused": self.refused,
            "refusal_reasons": list(self.refusal_reasons),
            "runtime_status": self.runtime_status,
            "comparison": self.comparison,
            "changed_perception": self.changed_perception,
            "report_paths": {k: v for k, v in self.report_paths.items()
                             if k != "report"},
        }


@dataclass
class LiveFieldPilot:
    """Orchestrates a bounded, governed live-field pilot through its phases."""

    state_dir: str = ".solaris_ai_nn_live"
    config: LiveFieldPilotConfig = field(default_factory=LiveFieldPilotConfig)
    governance: Any = None
    runtime: Optional[LiveFieldRuntime] = None

    def __post_init__(self) -> None:
        if self.runtime is None:
            cap = min(self.config.duration_s, self.config.hard_cap_s)
            self.runtime = LiveFieldRuntime(
                state_dir=self.state_dir, live_root=self.state_dir,
                max_runtime_s=cap, max_ticks=self.config.max_ticks,
                max_events_total=self.config.max_events_total,
                fixture_fallback=self.config.fixture_fallback,
                governance=self.governance)

    def run(self, *, governance_approved: bool = False) -> LiveFieldPilotResult:
        result = LiveFieldPilotResult()

        # Phase: preflight.
        result.phases_run.append(LiveFieldPilotPhase.PREFLIGHT)
        preflight = self.runtime.preflight()
        result.phases_run.append(LiveFieldPilotPhase.FEEDER_VALIDATION)

        # Live mode gate.
        if self.config.live and not (governance_approved
                                     or preflight["live_mode_allowed"]):
            result.refused = True
            result.refusal_reasons.append(
                "live mode requires governance approval")
            return result

        # Phases: baseline -> continuous -> absence -> cross-modal (one run).
        for phase in (LiveFieldPilotPhase.BASELINE_OBSERVATION,
                      LiveFieldPilotPhase.CONTINUOUS_EXPOSURE,
                      LiveFieldPilotPhase.ABSENCE_MONITORING,
                      LiveFieldPilotPhase.CROSS_MODAL_OBSERVATION):
            result.phases_run.append(phase)
        run_out = self.runtime.run(live=self.config.live,
                                   governance_approved=governance_approved)
        if run_out.get("refused"):
            result.refused = True
            result.refusal_reasons.extend(run_out.get("reasons", []))
            return result
        result.runtime_status = self.runtime.live_field_status()

        # Phase: changed-perception probe.
        result.phases_run.append(LiveFieldPilotPhase.CHANGED_PERCEPTION_PROBE)
        from ..organismic_demo import PerceptionChangeProbe

        probe = PerceptionChangeProbe().compute(
            dict(self.runtime.modality_responses), self.runtime.sensorium)
        result.changed_perception = probe.to_dict()

        # Phase: comparison.
        result.phases_run.append(LiveFieldPilotPhase.COMPARISON)
        from .comparison import LiveFieldComparison

        comparison = LiveFieldComparison(
            state_dir=self.state_dir + "/comparison").run(self.runtime)
        result.comparison = comparison.to_dict()

        # Phase: report.
        result.phases_run.append(LiveFieldPilotPhase.REPORT)
        from .live_field_report import LiveFieldReportBuilder

        result.report_paths = LiveFieldReportBuilder(
            self.runtime, comparison=comparison, probe=probe).write()
        return result
