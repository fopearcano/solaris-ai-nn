"""Developmental soak runtime -- the bounded study manager around the engine.

:class:`DevelopmentalSoakRuntime` orchestrates the month-scale soak protocol. It
is *protocol orchestration and evidence compilation only*: the Long-Horizon
Developmental Runtime (Prompt 53) remains the growth detector, and this runtime
never duplicates that logic. Per invocation it is bounded (a tick cap and a
runtime cap); long runs are reached by repeated invocations + checkpoints, never
by an unbounded daemon. It starts no feeders, controls no hardware, touches no
network/shell/browser/OS, modifies no source, uses no human teaching loop, and
makes no claim of life or consciousness.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .checkpointing import CheckpointManager
from .control_arms import ControlArmId, SoakControlArm
from .daily_packet import DailyEvidencePacketBuilder
from .evidence_dossier import EvidenceDossierBuilder
from .post_run_autopsy import PostRunAutopsy
from .preflight import SoakPreflight
from .restart_drills import RestartDrill, RestartDrillRunner, RestartDrillType
from .run_phases import SoakPhaseState, SoakRunPhase
from .safety import DevelopmentalSoakSafetyValidator
from .soak_plan import DevelopmentalSoakPlan, SoakPlanStageId
from .weekly_review import WeeklyReviewBuilder

# Status method per module name (mirrors the developmental engine's map).
_STATUS_METHODS = {
    "plural_sensorium": "plural_sensorium_status",
    "perceptual_metabolism": "metabolism_status",
    "perceptual_ontogenesis": "ontogenesis_status",
    "semiogenesis": "semiogenesis_status",
    "sensorium_cognition": "cognition_status",
    "self_boundary": "self_boundary_status",
    "desire_formation": "desire_status",
    "action_reaction": "action_reaction_status",
}


@dataclass
class DevelopmentalSoakRuntime:
    """Bounded staged study manager wrapping the developmental engine."""

    state_dir: str = ".solaris_ai_nn_soak"
    plan_path: Optional[str] = None
    stage: str = SoakPlanStageId.DRY_RUN_2H
    max_runtime_s: float = 30.0
    max_ticks: int = 12
    report_only: bool = False
    dry_run: bool = False
    fixture_mode: bool = True
    allow_live_read_only: bool = False
    require_governance_for_live: bool = True
    governance_approved: bool = False
    run_control_arms: bool = False
    run_restart_drills: bool = False
    modules: Dict[str, Any] = field(default_factory=dict)

    plan: DevelopmentalSoakPlan = field(default=None, init=False)
    preflight: SoakPreflight = field(default_factory=SoakPreflight, init=False)
    checkpoints: CheckpointManager = field(default=None, init=False)
    phase_state: SoakPhaseState = field(default_factory=SoakPhaseState,
                                        init=False)
    safety: DevelopmentalSoakSafetyValidator = field(
        default_factory=DevelopmentalSoakSafetyValidator, init=False)

    daily_packets: List[Any] = field(default_factory=list, init=False)
    weekly_reviews: List[Any] = field(default_factory=list, init=False)
    restart_drill_results: List[Any] = field(default_factory=list, init=False)
    control_arm_results: List[Any] = field(default_factory=list, init=False)
    preflight_results: List[Any] = field(default_factory=list, init=False)
    dossier: Any = field(default=None, init=False)
    autopsy: Any = field(default=None, init=False)
    dev_runtime: Any = field(default=None, init=False)
    ticks_run: int = field(default=0, init=False)
    safety_block_count: int = field(default=0, init=False)
    _refused: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self.plan = DevelopmentalSoakPlan.default()
        self.checkpoints = CheckpointManager(state_dir=self.state_dir,
                                             persist=not self.dry_run)
        bounded = self.safety.validate_bounded(self.max_ticks,
                                               self.max_runtime_s)
        self._refused = not bounded.safe

    # -- preflight ------------------------------------------------------------

    def run_preflight(self, *, source_paths: Optional[List[str]] = None,
                      ) -> Dict[str, Any]:
        self.preflight_results = self.preflight.run(
            state_dir=self.state_dir, modules=self.modules, plan=self.plan,
            allow_live_read_only=self.allow_live_read_only,
            require_governance_for_live=self.require_governance_for_live,
            governance_approved=self.governance_approved,
            source_paths=source_paths)
        return self.preflight.summary(self.preflight_results)

    # -- engine construction (calls Prompt 53; never duplicates it) -----------

    def _build_fixture_stack(self, base: str) -> Dict[str, Any]:
        """Build a small bounded fixture sensorium stack for the engine."""
        import json

        from ..plural_sensorium import PluralSensoriumRuntime, fixture_feeder

        os.makedirs(base, exist_ok=True)
        sensorium = PluralSensoriumRuntime(state_dir=base)
        for mod in ("alien_rf", "alien_vibration"):
            path = os.path.join(base, f"{mod}.jsonl")
            with open(path, "w", encoding="utf-8") as fh:
                for i in range(12):
                    fh.write(json.dumps({"modality": mod, "v": 0.6,
                                         "ts": float(i)}) + "\n")
            sensorium.add_feeder(fixture_feeder(f"{mod}_feed", path, mod))
        sensorium.run_bounded(max_polls=3)
        stack: Dict[str, Any] = {"plural_sensorium": sensorium}
        try:
            from ..perceptual_metabolism import PerceptualMetabolismRuntime

            met = PerceptualMetabolismRuntime(state_dir=base,
                                              sensorium=sensorium)
            met.update(events_this_tick=16, tick=0)
            stack["perceptual_metabolism"] = met
        except Exception:
            pass
        return stack

    def build_dev_runtime(self, modules: Optional[Dict[str, Any]] = None,
                          *, state_dir: Optional[str] = None,
                          max_ticks: Optional[int] = None) -> Any:
        from ..developmental_life import LongHorizonDevelopmentalRuntime

        base = state_dir or os.path.join(self.state_dir, "developmental")
        if modules is None:
            modules = self.modules or self._build_fixture_stack(base)
        dev = LongHorizonDevelopmentalRuntime(
            state_dir=base, modules=modules,
            max_ticks=max_ticks or self.max_ticks,
            max_runtime_s=self.max_runtime_s,
            allow_live_read_only=self.allow_live_read_only,
            require_governance_for_live=self.require_governance_for_live,
            dry_run=self.dry_run, report_only=self.report_only,
            fixture_mode=self.fixture_mode)
        return dev

    def _collect_statuses(self, dev: Any) -> Dict[str, Dict[str, Any]]:
        out: Dict[str, Dict[str, Any]] = {}
        for name, component in (dev.modules or {}).items():
            if component is None:
                continue
            if isinstance(component, dict):
                out[name] = component
                continue
            method = _STATUS_METHODS.get(name)
            if method and hasattr(component, method):
                try:
                    out[name] = getattr(component, method)()
                except Exception:
                    out[name] = {}
            elif hasattr(component, "snapshot"):
                try:
                    out[name] = component.snapshot()
                except Exception:
                    out[name] = {}
        return out

    # -- staged bounded execution ---------------------------------------------

    def run_stage(self, stage_id: Optional[str] = None) -> Dict[str, Any]:
        """Execute one bounded soak stage (preflight + dev cycle + evidence)."""
        if self._refused:
            return {"refused": True, "reason": "unbounded runtime"}
        stage_id = stage_id or self.stage
        stage = self.plan.stage(stage_id)
        base = os.path.join(self.state_dir, stage_id)

        pf = self.run_preflight()
        if not pf["passed"] and stage_id not in (SoakPlanStageId.PREFLIGHT,):
            return {"refused": False, "stage": stage_id, "preflight": pf,
                    "ran": False, "reason": "preflight failed"}

        # Pure preflight / autopsy stages do not run the developmental cycle.
        if stage_id in (SoakPlanStageId.PREFLIGHT,
                        SoakPlanStageId.POST_RUN_AUTOPSY):
            self.dev_runtime = self.build_dev_runtime(
                state_dir=base, max_ticks=min(stage.max_ticks, self.max_ticks))
            if stage_id == SoakPlanStageId.POST_RUN_AUTOPSY:
                self.dev_runtime.run_bounded()
                self.build_evidence_dossier()
                self.run_post_run_autopsy()
            return {"refused": False, "stage": stage_id, "preflight": pf,
                    "ran": stage_id == SoakPlanStageId.POST_RUN_AUTOPSY}

        ticks = min(stage.max_ticks, self.max_ticks)
        self.dev_runtime = self.build_dev_runtime(state_dir=base,
                                                  max_ticks=ticks)

        started = time.time()
        cp_interval = max(1, stage.checkpoint_interval_ticks or 5)
        for tick in range(ticks):
            if time.time() - started > min(stage.hard_runtime_cap_s,
                                           self.max_runtime_s):
                break
            self._run_phase_cycle(stage_id, tick, cp_interval)
            self.ticks_run += 1
        # Close the developmental run for the stage.
        self.dev_runtime.run_bounded(max_ticks=1)
        self.dev_runtime.write_artifacts()

        # Build the latest daily packet + (if enough days) a weekly review.
        self._build_daily_packet(stage_id)
        if len(self.daily_packets) >= 1:
            self._build_weekly_review()

        if self.run_restart_drills:
            self.run_restart_drills_now()
        if self.run_control_arms:
            self.run_control_arms_now()

        self.build_evidence_dossier()
        return {"refused": False, "stage": stage_id, "preflight": pf,
                "ran": True, "ticks_run": self.ticks_run,
                "phase_state": self.phase_state.to_dict()}

    def _run_phase_cycle(self, stage_id: str, tick: int,
                         cp_interval: int) -> None:
        dev = self.dev_runtime

        def phase_fn(phase: str, t: int) -> Dict[str, Any]:
            if phase == SoakRunPhase.ACTIVE_DEVELOPMENTAL_CYCLE:
                dev.update(tick=t)
                return {"developmental": "updated", "tick": t}
            if phase == SoakRunPhase.CHECKPOINT and t % cp_interval == 0:
                self._checkpoint(tick=t)
                return {"checkpoint": True}
            if phase == SoakRunPhase.SAFETY_SCAN:
                rep = self.safety.validate_operation("bounded developmental "
                                                     "soak tick")
                if not rep.safe:
                    self.safety_block_count += 1
                return {"safe": rep.safe}
            return {"ran": True}

        self.phase_state.run_full_cycle(tick=tick, phase_fn=phase_fn)

    def _checkpoint(self, *, tick: int) -> Any:
        dev = self.dev_runtime
        statuses = self._collect_statuses(dev)
        cp = self.checkpoints.create(
            tick=tick,
            run_manifest={"state_dir": self.state_dir, "stage": self.stage},
            module_states=statuses,
            inner_map=self._inner_map_view(),
            developmental_life=dev.developmental_status(),
            safety=self.safety.snapshot(),
            artifact_index=[dev.developmental_status().get(
                "latest_developmental_report_path") or ""])
        self.checkpoints.verify(cp)  # record integrity
        return cp

    def _build_daily_packet(self, stage_id: str) -> Any:
        dev = self.dev_runtime
        statuses = self._collect_statuses(dev)
        builder = DailyEvidencePacketBuilder()
        packet = builder.build(
            run_day=len(self.daily_packets) + 1, active_phase=stage_id,
            tick_range=[0, self.ticks_run], statuses=statuses,
            dev_status=dev.developmental_status(),
            artifact_list=[c.checkpoint_id for c in self.checkpoints.checkpoints],
            safety_blocks=self.safety_block_count)
        self.daily_packets.append(packet)
        return packet

    def _build_weekly_review(self) -> Any:
        review = WeeklyReviewBuilder().build(
            week=len(self.weekly_reviews) + 1,
            daily_packets=list(self.daily_packets),
            dev_status=self.dev_runtime.developmental_status()
            if self.dev_runtime else {})
        self.weekly_reviews.append(review)
        return review

    # -- drills, controls, dossier, autopsy -----------------------------------

    def run_restart_drills_now(self) -> List[Any]:
        runner = RestartDrillRunner()
        for dt in (RestartDrillType.GRACEFUL_SHUTDOWN_RESTART,
                   RestartDrillType.SIMULATED_CRASH_MARKER,
                   RestartDrillType.MISSING_CHECKPOINT_RECOVERY,
                   RestartDrillType.CHECKPOINT_CORRUPTION_DETECTION,
                   RestartDrillType.STATE_CONTINUITY_VERIFICATION):
            self.restart_drill_results.append(runner.run(
                RestartDrill(dt), checkpoint_manager=self.checkpoints,
                developmental_runtime=self.dev_runtime))
        return self.restart_drill_results

    def run_control_arms_now(self, arm_ids: Optional[List[str]] = None) -> List:
        arm = SoakControlArm()
        stack = (self.dev_runtime.modules if self.dev_runtime else {}) \
            or self.modules
        base = os.path.join(self.state_dir, "control_arms")

        def build_runtime(subset: Dict[str, Any], config) -> Any:
            from ..developmental_life import LongHorizonDevelopmentalRuntime

            arm_dir = os.path.join(base, config.arm_id)
            return LongHorizonDevelopmentalRuntime(
                state_dir=arm_dir, modules=subset, max_ticks=config.max_ticks,
                max_runtime_s=self.max_runtime_s, dry_run=self.dry_run,
                fixture_mode=True)

        self.control_arm_results = arm.run_default_arms(
            module_stack=stack, build_runtime=build_runtime, arm_ids=arm_ids,
            governance_approved=self.governance_approved,
            max_ticks=min(4, self.max_ticks))
        return self.control_arm_results

    def build_evidence_dossier(self) -> Any:
        dev_status = (self.dev_runtime.developmental_status()
                      if self.dev_runtime else {})
        self.dossier = EvidenceDossierBuilder().build(
            dev_status=dev_status, daily_packets=self.daily_packets,
            weekly_reviews=self.weekly_reviews,
            control_arms=self.control_arm_results,
            safety_block_count=self.safety_block_count)
        return self.dossier

    def run_post_run_autopsy(self) -> Any:
        if self.dossier is None:
            self.build_evidence_dossier()
        dev_status = (self.dev_runtime.developmental_status()
                      if self.dev_runtime else {})
        self.autopsy = PostRunAutopsy().run(
            dev_status=dev_status, dossier=self.dossier,
            safety_block_count=self.safety_block_count,
            control_arm_results=self.control_arm_results,
            live_arm_available=any(
                getattr(a, "arm_id", "") == ControlArmId.LIVE_READ_ONLY_IF_AVAILABLE
                and getattr(a, "available", False)
                for a in self.control_arm_results))
        return self.autopsy

    # -- integration views ----------------------------------------------------

    def _inner_map_view(self) -> Dict[str, Any]:
        return {"developmental_soak_enabled": True, "current_stage": self.stage}

    def architecture_proposals(self) -> List[Dict[str, Any]]:
        from ..architecture_evolution import soak_revision_proposals

        return soak_revision_proposals(self.soak_status())

    def soak_status(self) -> Dict[str, Any]:
        pf = self.preflight.summary(self.preflight_results) \
            if self.preflight_results else {"passed": None, "pass_count": 0,
                                            "fail_count": 0}
        dossier_d = self.dossier.to_dict() if self.dossier else {}
        autopsy_d = self.autopsy.to_dict() if self.autopsy else {}
        dev_status = (self.dev_runtime.developmental_status()
                      if self.dev_runtime else {})
        return {
            "developmental_soak_enabled": True,
            "active_plan_id": self.plan.plan_id,
            "current_stage": self.stage,
            "soak_stage_count": len(self.plan.stages),
            "preflight_passed": pf.get("passed"),
            "preflight_pass_count": pf.get("pass_count", 0),
            "preflight_fail_count": pf.get("fail_count", 0),
            "checkpoint_count": self.checkpoints.status()["checkpoint_count"],
            "checkpoint_corruption_count":
                self.checkpoints.status()["checkpoint_corruption_count"],
            "daily_packet_count": len(self.daily_packets),
            "weekly_review_count": len(self.weekly_reviews),
            "restart_drill_count": len(self.restart_drill_results),
            "control_arm_count": len(self.control_arm_results),
            "evidence_claim_count": dossier_d.get("claim_count", 0),
            "strong_evidence_claim_count":
                dossier_d.get("strong_claim_count", 0),
            "inconclusive_claim_count":
                dossier_d.get("inconclusive_claim_count", 0),
            "autopsy_recommendation": autopsy_d.get("recommendation"),
            "autopsy_finding_count": autopsy_d.get("finding_count", 0),
            "structural_growth_status":
                dev_status.get("structural_growth_status", "inconclusive"),
            "regression_count": dev_status.get("regression_count", 0),
            "plateau_count": dev_status.get("plateau_count", 0),
            "soak_safety_block_count": self.safety_block_count,
            "soak_safety_rejected_count": self.safety.rejected_count,
            "latest_soak_report_path": self._report_path(),
            "is_biological_life": False,
            "is_consciousness_or_personhood": False,
        }

    def _report_path(self) -> Optional[str]:
        path = os.path.join(self.state_dir, "SOAK_PROTOCOL_REPORT.md")
        return path if os.path.isfile(path) else None

    def snapshot(self) -> Dict[str, Any]:
        return self.soak_status()

    def write_artifacts(self) -> Dict[str, Any]:
        from .reports import DevelopmentalSoakReportBuilder

        return DevelopmentalSoakReportBuilder(self).write()
