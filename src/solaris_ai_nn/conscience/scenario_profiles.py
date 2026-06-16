"""Scenario profiles -- named, bounded, reproducible run configurations.

A :class:`ScenarioProfile` pins a whole run: which modules are enabled, the
:class:`RunContext` (mode/authority/bounds), the safety constraints, any
governance requirement, and the artifacts/metrics it is expected to produce.
Profiles A--J range from a minimal smoke test to a month-scale *dry run* --
none of which actuate the real world, and the month/year *real* variants are
intentionally absent here (they require an explicit governance-approved
context, never a canned profile).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .run_context import RunAuthority, RunContext, RunMode


@dataclass
class ScenarioProfile:
    """A named, bounded, reproducible run configuration."""

    profile_id: str
    description: str
    run_context: RunContext
    enabled_modules: List[str] = field(default_factory=list)
    safety_constraints: List[str] = field(default_factory=list)
    governance_requirements: List[str] = field(default_factory=list)
    expected_artifacts: List[str] = field(default_factory=list)
    expected_metrics: List[str] = field(default_factory=list)
    max_runtime_s: float = 120.0

    def __post_init__(self) -> None:
        # Keep the run context's enabled modules in sync with the profile.
        if self.enabled_modules and not self.run_context.enabled_modules:
            self.run_context.enabled_modules = list(self.enabled_modules)
        self.run_context.metadata.setdefault("profile_id", self.profile_id)

    @property
    def requires_governance(self) -> bool:
        return bool(self.governance_requirements) \
            or self.run_context.requires_governance

    @property
    def is_plan_only(self) -> bool:
        return self.run_context.is_plan_only

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "description": self.description,
            "run_context": self.run_context.to_dict(),
            "enabled_modules": list(self.enabled_modules),
            "safety_constraints": list(self.safety_constraints),
            "governance_requirements": list(self.governance_requirements),
            "expected_artifacts": list(self.expected_artifacts),
            "expected_metrics": list(self.expected_metrics),
            "max_runtime_s": self.max_runtime_s,
            "requires_governance": self.requires_governance,
            "is_plan_only": self.is_plan_only,
        }


# Constraints shared by every profile (the spine is never sovereign).
_BASE_CONSTRAINTS = (
    "internal/simulation only",
    "no real-world actuation",
    "no network/OS/browser automation",
    "writes confined to state/artifact directories",
    "bounded run; no unbounded loop",
)

_CORE_MODULES = ["bridge", "ecology", "memory", "homeostasis", "executive",
                 "governance", "ops"]


def _ctx(mode: str, *, max_steps: Optional[int], seed: int = 7,
         enabled: Optional[List[str]] = None,
         authority: str = RunAuthority.SIMULATION_ONLY,
         target_days: Optional[float] = None,
         max_duration_s: Optional[float] = 600.0) -> RunContext:
    return RunContext(
        mode=mode, authority=authority, max_steps=max_steps,
        max_duration_s=max_duration_s, target_runtime_days=target_days,
        seed=seed, enabled_modules=list(enabled or []))


def _build_profiles() -> Dict[str, ScenarioProfile]:
    profiles: Dict[str, ScenarioProfile] = {}

    def add(profile: ScenarioProfile) -> None:
        profiles[profile.profile_id] = profile

    # A -- minimal smoke: the smallest spine that still runs end to end.
    add(ScenarioProfile(
        profile_id="minimal_smoke",
        description="Smallest end-to-end spine: stimulus->push->reaction.",
        run_context=_ctx(RunMode.UNIT_TEST, max_steps=12),
        enabled_modules=["bridge", "ecology", "governance", "ops"],
        safety_constraints=list(_BASE_CONSTRAINTS),
        expected_artifacts=["conscience_bus.jsonl"],
        expected_metrics=["run_step_count", "spine_phase_count",
                          "bus_message_count"],
        max_runtime_s=30.0))

    # B -- nursery short: developmental nursery driving the core spine.
    add(ScenarioProfile(
        profile_id="nursery_short",
        description="Short nursery-driven developmental run on the core spine.",
        run_context=_ctx(RunMode.NURSERY_SIMULATED, max_steps=40),
        enabled_modules=_CORE_MODULES + ["world_model", "developmental"],
        safety_constraints=list(_BASE_CONSTRAINTS),
        expected_artifacts=["conscience_bus.jsonl"],
        expected_metrics=["run_step_count", "module_success_rate",
                          "world_model_update"],
        max_runtime_s=45.0))

    # C -- proto language short: symbol formation under the spine.
    add(ScenarioProfile(
        profile_id="proto_language_short",
        description="Short run exercising proto-language symbol formation.",
        run_context=_ctx(RunMode.SHORT_DEMO, max_steps=60),
        enabled_modules=_CORE_MODULES + ["world_model", "protolanguage"],
        safety_constraints=list(_BASE_CONSTRAINTS),
        expected_artifacts=["conscience_bus.jsonl"],
        expected_metrics=["run_step_count", "module_success_rate"],
        max_runtime_s=60.0))

    # D -- active perception short: intrinsic exploration / sampling.
    add(ScenarioProfile(
        profile_id="active_perception_short",
        description="Short run with active perception and self-sampling.",
        run_context=_ctx(RunMode.SHORT_DEMO, max_steps=60),
        enabled_modules=_CORE_MODULES
        + ["world_model", "protolanguage", "active_perception"],
        safety_constraints=list(_BASE_CONSTRAINTS),
        expected_artifacts=["conscience_bus.jsonl"],
        expected_metrics=["run_step_count", "module_success_rate",
                          "degraded_module_count"],
        max_runtime_s=60.0))

    # E -- hypothesis short: internal scientific method.
    add(ScenarioProfile(
        profile_id="hypothesis_short",
        description="Short run exercising the hypothesis/experiment engine.",
        run_context=_ctx(RunMode.SHORT_DEMO, max_steps=80),
        enabled_modules=_CORE_MODULES
        + ["world_model", "protolanguage", "active_perception", "hypothesis"],
        safety_constraints=list(_BASE_CONSTRAINTS),
        expected_artifacts=["conscience_bus.jsonl"],
        expected_metrics=["run_step_count", "module_success_rate"],
        max_runtime_s=75.0))

    # F -- logos short: fracture/synthesis and complexity regulation.
    add(ScenarioProfile(
        profile_id="logos_short",
        description="Short run exercising LOGOS complexity regulation.",
        run_context=_ctx(RunMode.SHORT_DEMO, max_steps=80),
        enabled_modules=_CORE_MODULES
        + ["world_model", "protolanguage", "active_perception", "hypothesis",
           "logos"],
        safety_constraints=list(_BASE_CONSTRAINTS),
        expected_artifacts=["conscience_bus.jsonl"],
        expected_metrics=["run_step_count", "module_success_rate"],
        max_runtime_s=75.0))

    # G -- autoregeneration short: long-run hygiene / self-repair.
    add(ScenarioProfile(
        profile_id="autoregeneration_short",
        description="Short run exercising auto-regeneration state hygiene.",
        run_context=_ctx(RunMode.SHORT_DEMO, max_steps=90),
        enabled_modules=_CORE_MODULES
        + ["world_model", "protolanguage", "active_perception",
           "autoregeneration"],
        safety_constraints=list(_BASE_CONSTRAINTS),
        expected_artifacts=["conscience_bus.jsonl"],
        expected_metrics=["run_step_count", "module_success_rate",
                          "checkpoint_success_rate"],
        max_runtime_s=80.0))

    # H -- full developmental short: every module wired together, bounded.
    add(ScenarioProfile(
        profile_id="full_developmental_short",
        description="All modules wired into one bounded developmental run.",
        run_context=_ctx(RunMode.DEVELOPMENTAL_SIMULATED, max_steps=120),
        enabled_modules=_CORE_MODULES
        + ["world_model", "protolanguage", "active_perception", "hypothesis",
           "logos", "autoregeneration", "inner_map", "evaluation",
           "communication"],
        safety_constraints=list(_BASE_CONSTRAINTS),
        governance_requirements=["enable_full_developmental_short_profile"],
        expected_artifacts=["conscience_bus.jsonl", "full_system_report.json"],
        expected_metrics=["run_step_count", "spine_phase_count",
                          "module_success_rate", "module_failure_rate",
                          "degraded_module_count"],
        max_runtime_s=120.0))

    # I -- month scale plan: produce a plan only, never start a long run.
    add(ScenarioProfile(
        profile_id="month_scale_plan",
        description="Plan a month-scale run (plan only; nothing is started).",
        run_context=_ctx(RunMode.MONTH_SCALE_PLAN, max_steps=None,
                         target_days=30.0, max_duration_s=None),
        enabled_modules=_CORE_MODULES
        + ["world_model", "protolanguage", "active_perception", "hypothesis",
           "logos", "autoregeneration", "inner_map"],
        safety_constraints=list(_BASE_CONSTRAINTS) + [
            "plan only; no run is started"],
        governance_requirements=["enable_month_scale_dry_run"],
        expected_artifacts=["month_scale_plan.json"],
        expected_metrics=["report_generation_success"],
        max_runtime_s=30.0))

    # J -- month scale dry run: a bounded *simulated* slice of a month plan.
    add(ScenarioProfile(
        profile_id="month_scale_dry_run",
        description="Bounded simulated slice standing in for a month run.",
        run_context=_ctx(RunMode.DEVELOPMENTAL_SIMULATED, max_steps=200,
                         target_days=30.0),
        enabled_modules=_CORE_MODULES
        + ["world_model", "protolanguage", "active_perception", "hypothesis",
           "logos", "autoregeneration", "inner_map"],
        safety_constraints=list(_BASE_CONSTRAINTS) + [
            "simulated-time slice; not a real month"],
        governance_requirements=["enable_month_scale_dry_run"],
        expected_artifacts=["conscience_bus.jsonl", "full_system_report.json"],
        expected_metrics=["run_step_count", "module_success_rate",
                          "profile_runtime_seconds", "scenario_exit_success"],
        max_runtime_s=120.0))

    # -- Pilot-1 month-scale soak profiles (Prompt 29) ------------------------
    _pilot_modules = _CORE_MODULES + [
        "world_model", "protolanguage", "active_perception", "hypothesis",
        "logos", "autoregeneration", "inner_map", "developmental",
        "evaluation", "communication"]

    # pilot1_plan_only: generate plan/runbook/budget; no long run.
    add(ScenarioProfile(
        profile_id="pilot1_plan_only",
        description="Pilot-1 plan only: runbook/budget/config, no run started.",
        run_context=_ctx(RunMode.MONTH_SCALE_PLAN, max_steps=None,
                         target_days=30.0, max_duration_s=None),
        enabled_modules=list(_pilot_modules),
        safety_constraints=list(_BASE_CONSTRAINTS) + [
            "plan only; no run is started",
            "simulated-time plan; not a real month"],
        governance_requirements=["enable_pilot1"],
        expected_artifacts=["OPERATOR_RUNBOOK.md", "pilot_config.json"],
        expected_metrics=["report_generation_success"],
        max_runtime_s=30.0))

    # pilot1_preflight: bounded health/dry checks before any soak.
    add(ScenarioProfile(
        profile_id="pilot1_preflight",
        description="Pilot-1 preflight: bounded health and readiness checks.",
        run_context=_ctx(RunMode.SHORT_DEMO, max_steps=60),
        enabled_modules=list(_pilot_modules),
        safety_constraints=list(_BASE_CONSTRAINTS),
        governance_requirements=["enable_pilot1"],
        expected_artifacts=["preflight_report.json"],
        expected_metrics=["run_step_count", "module_success_rate"],
        max_runtime_s=60.0))

    # pilot1_simulated_month_dry_run: bounded simulated slice, clearly labelled.
    add(ScenarioProfile(
        profile_id="pilot1_simulated_month_dry_run",
        description="Pilot-1 SIMULATED month dry-run (not a real month).",
        run_context=_ctx(RunMode.DEVELOPMENTAL_SIMULATED, max_steps=200,
                         target_days=30.0),
        enabled_modules=list(_pilot_modules),
        safety_constraints=list(_BASE_CONSTRAINTS) + [
            "simulated-time slice; explicitly NOT a real month"],
        governance_requirements=["enable_pilot1"],
        expected_artifacts=["conscience_bus.jsonl"],
        expected_metrics=["run_step_count", "module_success_rate",
                          "profile_runtime_seconds"],
        max_runtime_s=120.0))

    # Real soak profiles: governance-gated; the conscience side stays bounded,
    # the actual long run is operator-driven per the runbook.
    for pid, scope, days in (
            ("pilot1_24h_soak", "enable_pilot1_24h_real", 1.0),
            ("pilot1_7d_soak", "enable_pilot1_7d_real", 7.0),
            ("pilot1_30d_soak", "enable_pilot1_30d_real", 30.0)):
        add(ScenarioProfile(
            profile_id=pid,
            description=f"Pilot-1 {pid} real soak (governance-gated; "
                        "operator-driven long run).",
            run_context=_ctx(RunMode.DEVELOPMENTAL_SIMULATED, max_steps=200,
                             target_days=days),
            enabled_modules=list(_pilot_modules),
            safety_constraints=list(_BASE_CONSTRAINTS) + [
                "real long-scale run requires governance approval",
                "operator-driven; not started automatically"],
            governance_requirements=[scope],
            expected_artifacts=["conscience_bus.jsonl",
                                "full_system_report.json"],
            expected_metrics=["run_step_count", "module_success_rate",
                              "scenario_exit_success"],
            max_runtime_s=120.0))

    # Post-pilot analysis (Prompt 30): plan-only so the cognition loop never
    # runs; it loads existing artifacts and produces forensic reports without
    # mutating runtime state, performing repairs, or starting a pilot.
    add(ScenarioProfile(
        profile_id="post_pilot_analysis",
        description="Post-pilot forensic analysis (read-only; no cognition "
                    "loop, no runtime mutation).",
        run_context=_ctx(RunMode.MONTH_SCALE_PLAN, max_steps=None,
                         max_duration_s=None),
        enabled_modules=["governance", "ops", "evaluation", "inner_map"],
        safety_constraints=list(_BASE_CONSTRAINTS) + [
            "read-only forensic analysis; no cognition loop",
            "does not mutate runtime state or perform repairs"],
        governance_requirements=["enable_pilot1"],
        expected_artifacts=["POST_PILOT_ANALYSIS.json",
                            "RESEARCH_DOSSIER.json"],
        expected_metrics=["report_generation_success"],
        max_runtime_s=30.0))

    # -- Pilot-2 read-only sensory membrane profiles (Prompt 31) --------------
    _sensory_modules = _CORE_MODULES + [
        "world_model", "protolanguage", "active_perception", "hypothesis",
        "logos", "autoregeneration", "inner_map", "sensory_membrane"]

    # Dry-run: validate sources without publishing stimuli.
    add(ScenarioProfile(
        profile_id="sensory_membrane_dry_run",
        description="Validate read-only sensory sources without publishing.",
        run_context=_ctx(RunMode.SHORT_DEMO, max_steps=20),
        enabled_modules=["bridge", "ecology", "governance", "ops",
                         "sensory_membrane"],
        safety_constraints=list(_BASE_CONSTRAINTS) + [
            "read-only sources only; the system never acts on the world",
            "dry-run: validates and reports, publishes no stimuli"],
        governance_requirements=["enable_sensory_membrane_dry_run"],
        expected_artifacts=["SENSORY_MEMBRANE_REPORT.json"],
        expected_metrics=["run_step_count"],
        max_runtime_s=30.0))

    # Short: bounded run using test fixtures, publishing to the bus.
    add(ScenarioProfile(
        profile_id="sensory_membrane_short",
        description="Short bounded run ingesting read-only sensory fixtures.",
        run_context=_ctx(RunMode.SHORT_DEMO, max_steps=40),
        enabled_modules=list(_sensory_modules),
        safety_constraints=list(_BASE_CONSTRAINTS) + [
            "read-only sources only; environmental input is not a command"],
        governance_requirements=["enable_sensory_membrane"],
        expected_artifacts=["conscience_bus.jsonl",
                            "SENSORY_MEMBRANE_REPORT.json"],
        expected_metrics=["run_step_count", "module_success_rate"],
        max_runtime_s=60.0))

    # Pilot-2 plan only: generate the read-only plan; start no long run.
    add(ScenarioProfile(
        profile_id="pilot2_plan_only",
        description="Plan a Pilot-2 read-only sensory run (plan only).",
        run_context=_ctx(RunMode.MONTH_SCALE_PLAN, max_steps=None,
                         max_duration_s=None),
        enabled_modules=list(_sensory_modules),
        safety_constraints=list(_BASE_CONSTRAINTS) + [
            "plan only; no run is started",
            "read-only sensory exposure, not autonomy"],
        governance_requirements=["enable_pilot2_read_only_short"],
        expected_artifacts=["PILOT2_READ_ONLY_PLAN.json"],
        expected_metrics=["report_generation_success"],
        max_runtime_s=30.0))

    # Pilot-2 read-only short: a bounded read-only sensory developmental run.
    add(ScenarioProfile(
        profile_id="pilot2_read_only_short",
        description="Bounded Pilot-2 read-only sensory developmental run.",
        run_context=_ctx(RunMode.DEVELOPMENTAL_SIMULATED, max_steps=80),
        enabled_modules=list(_sensory_modules),
        safety_constraints=list(_BASE_CONSTRAINTS) + [
            "read-only sources only; never actuates the world",
            "real read-only sources require governance approval"],
        governance_requirements=["enable_pilot2_read_only_short"],
        expected_artifacts=["conscience_bus.jsonl",
                            "SENSORY_MEMBRANE_REPORT.json"],
        expected_metrics=["run_step_count", "module_success_rate",
                          "scenario_exit_success"],
        max_runtime_s=90.0))

    # -- Pilot-2 read-only environmental soak profiles (Prompt 32) ------------
    _p2_core = _CORE_MODULES + ["world_model", "protolanguage",
                                "active_perception", "hypothesis", "logos",
                                "autoregeneration", "inner_map",
                                "developmental"]

    # Source preflight: bounded, read-only checks; no cognition loop needed.
    add(ScenarioProfile(
        profile_id="pilot2_source_preflight",
        description="Pilot-2 read-only source preflight checks (bounded).",
        run_context=_ctx(RunMode.SHORT_DEMO, max_steps=20),
        enabled_modules=["bridge", "governance", "ops", "sensory_membrane"],
        safety_constraints=list(_BASE_CONSTRAINTS) + [
            "read-only source validation; no publishing required"],
        governance_requirements=["enable_pilot2_source_preflight"],
        expected_artifacts=["source_preflight.json"],
        expected_metrics=["run_step_count"],
        max_runtime_s=30.0))

    # Membrane dry-run via Pilot-2 (validates sources, publishes nothing).
    add(ScenarioProfile(
        profile_id="pilot2_membrane_dry_run",
        description="Pilot-2 sensory membrane dry-run (publishes nothing).",
        run_context=_ctx(RunMode.SHORT_DEMO, max_steps=20),
        enabled_modules=["bridge", "ecology", "governance", "ops",
                         "sensory_membrane"],
        safety_constraints=list(_BASE_CONSTRAINTS) + [
            "dry-run: validates and reports, publishes no stimuli"],
        governance_requirements=["enable_sensory_membrane_dry_run"],
        expected_artifacts=["SENSORY_MEMBRANE_REPORT.json"],
        expected_metrics=["run_step_count"],
        max_runtime_s=30.0))

    # Fixture short: bounded fixture exposure on the sensory spine.
    add(ScenarioProfile(
        profile_id="pilot2_fixture_short",
        description="Pilot-2 bounded fixture sensory exposure.",
        run_context=_ctx(RunMode.SHORT_DEMO, max_steps=40),
        enabled_modules=list(_p2_core),
        safety_constraints=list(_BASE_CONSTRAINTS) + [
            "read-only fixtures only; environmental input is not a command"],
        governance_requirements=["enable_pilot2_fixture_short"],
        expected_artifacts=["conscience_bus.jsonl"],
        expected_metrics=["run_step_count", "module_success_rate"],
        max_runtime_s=60.0))

    # Nursery baseline: nursery-only comparison arm (no membrane).
    add(ScenarioProfile(
        profile_id="pilot2_nursery_baseline_short",
        description="Pilot-2 nursery-only baseline (no sensory membrane).",
        run_context=_ctx(RunMode.NURSERY_SIMULATED, max_steps=40),
        enabled_modules=_CORE_MODULES + ["world_model", "protolanguage",
                                         "active_perception", "hypothesis",
                                         "logos", "inner_map", "developmental"],
        safety_constraints=list(_BASE_CONSTRAINTS) + [
            "nursery-only baseline arm for comparison"],
        governance_requirements=["enable_pilot2_nursery_baseline"],
        expected_artifacts=["conscience_bus.jsonl"],
        expected_metrics=["run_step_count", "module_success_rate"],
        max_runtime_s=60.0))

    # Mixed short: nursery + membrane (needs membrane dry-run pass; governed).
    add(ScenarioProfile(
        profile_id="pilot2_mixed_short",
        description="Pilot-2 mixed nursery+membrane short run (governed).",
        run_context=_ctx(RunMode.DEVELOPMENTAL_SIMULATED, max_steps=60),
        enabled_modules=list(_p2_core),
        safety_constraints=list(_BASE_CONSTRAINTS) + [
            "mixed mode preserves the nursery/environment boundary"],
        governance_requirements=["enable_pilot2_mixed_short"],
        expected_artifacts=["conscience_bus.jsonl",
                            "SENSORY_MEMBRANE_REPORT.json"],
        expected_metrics=["run_step_count", "module_success_rate"],
        max_runtime_s=90.0))

    # Real read-only soak PLANS: plan only; never start a long run.
    for pid, scope, days in (
            ("pilot2_read_only_24h_plan",
             "enable_pilot2_real_read_only_24h", 1.0),
            ("pilot2_read_only_7d_plan",
             "enable_pilot2_real_read_only_7d", 7.0),
            ("pilot2_read_only_30d_plan",
             "enable_pilot2_real_read_only_30d", 30.0)):
        add(ScenarioProfile(
            profile_id=pid,
            description=f"Plan a Pilot-2 {pid} read-only soak (plan only).",
            run_context=_ctx(RunMode.MONTH_SCALE_PLAN, max_steps=None,
                             target_days=days, max_duration_s=None),
            enabled_modules=list(_p2_core),
            safety_constraints=list(_BASE_CONSTRAINTS) + [
                "plan only; no run is started",
                "real read-only soak requires governance approval"],
            governance_requirements=[scope],
            expected_artifacts=["PILOT2_REPORT.json"],
            expected_metrics=["report_generation_success"],
            max_runtime_s=30.0))

    # -- Pilot-3 motor membrane profiles (Prompt 33) --------------------------
    _motor_core = _CORE_MODULES + ["world_model", "protolanguage",
                                   "active_perception", "hypothesis", "logos",
                                   "autoregeneration", "inner_map",
                                   "motor_membrane"]

    # Plan only: starts no run; grants no actuation.
    add(ScenarioProfile(
        profile_id="pilot3_plan_only",
        description="Plan Pilot-3 limited embodiment (plan only; no run).",
        run_context=_ctx(RunMode.MONTH_SCALE_PLAN, max_steps=None,
                         max_duration_s=None),
        enabled_modules=list(_motor_core),
        safety_constraints=list(_BASE_CONSTRAINTS) + [
            "plan only; no run is started",
            "simulation/dry-run only; no real-world actuation"],
        governance_requirements=["enable_pilot3_plan_only"],
        expected_artifacts=["PILOT3_REPORT.json"],
        expected_metrics=["report_generation_success"],
        max_runtime_s=30.0))

    # Firewall preflight: confirm the firewall blocks real-world actions.
    add(ScenarioProfile(
        profile_id="motor_firewall_preflight",
        description="Motor actuation firewall preflight (bounded).",
        run_context=_ctx(RunMode.SHORT_DEMO, max_steps=20),
        enabled_modules=["bridge", "ecology", "governance", "ops", "executive",
                         "motor_membrane"],
        safety_constraints=list(_BASE_CONSTRAINTS) + [
            "firewall always enabled; real-world actions blocked"],
        governance_requirements=["enable_motor_firewall_preflight"],
        expected_artifacts=["actuation_firewall.jsonl"],
        expected_metrics=["run_step_count"],
        max_runtime_s=30.0))

    # Dry-run motor trace: records proposed actions; no simulation change.
    add(ScenarioProfile(
        profile_id="dry_run_motor_trace",
        description="Dry-run motor trace (records proposals only).",
        run_context=_ctx(RunMode.SHORT_DEMO, max_steps=30),
        enabled_modules=["bridge", "ecology", "governance", "ops", "executive",
                         "motor_membrane"],
        safety_constraints=list(_BASE_CONSTRAINTS) + [
            "dry-run: no simulation state change, no real action"],
        governance_requirements=["enable_dry_run_motor_trace"],
        expected_artifacts=["motor_actions.jsonl"],
        expected_metrics=["run_step_count"],
        max_runtime_s=40.0))

    # GridWorld short: bounded simulated movement.
    add(ScenarioProfile(
        profile_id="gridworld_motor_short",
        description="Bounded GridWorld simulated motor run.",
        run_context=_ctx(RunMode.SHORT_DEMO, max_steps=40),
        enabled_modules=list(_motor_core),
        safety_constraints=list(_BASE_CONSTRAINTS) + [
            "simulation-only GridWorld actions; no real-world effect"],
        governance_requirements=["enable_gridworld_motor_short"],
        expected_artifacts=["motor_actions.jsonl", "conscience_bus.jsonl"],
        expected_metrics=["run_step_count", "module_success_rate"],
        max_runtime_s=60.0))

    # GridWorld reward/danger short.
    add(ScenarioProfile(
        profile_id="gridworld_reward_danger_short",
        description="GridWorld reward/danger analogue simulated run.",
        run_context=_ctx(RunMode.SHORT_DEMO, max_steps=40),
        enabled_modules=list(_motor_core),
        safety_constraints=list(_BASE_CONSTRAINTS) + [
            "simulation-only reward/danger analogues; no real-world effect"],
        governance_requirements=["enable_gridworld_motor_short"],
        expected_artifacts=["motor_actions.jsonl"],
        expected_metrics=["run_step_count", "module_success_rate"],
        max_runtime_s=60.0))

    # Mixed sensory + gridworld: read-only input + simulated body, separated.
    add(ScenarioProfile(
        profile_id="mixed_sensory_gridworld_short",
        description="Read-only sensory input + separate simulated body.",
        run_context=_ctx(RunMode.DEVELOPMENTAL_SIMULATED, max_steps=60),
        enabled_modules=list(_motor_core) + ["sensory_membrane"],
        safety_constraints=list(_BASE_CONSTRAINTS) + [
            "sensory input stays read-only; body actions stay simulated",
            "source/body boundary preserved"],
        governance_requirements=["enable_mixed_sensory_gridworld"],
        expected_artifacts=["motor_actions.jsonl",
                            "SENSORY_MEMBRANE_REPORT.json"],
        expected_metrics=["run_step_count", "module_success_rate"],
        max_runtime_s=90.0))

    # -- Pilot-3 simulated embodiment soak profiles (Prompt 34) ---------------
    # Plan only: starts no run; grants no actuation.
    add(ScenarioProfile(
        profile_id="pilot3_soak_plan",
        description="Plan the Pilot-3 simulated embodiment soak (plan only).",
        run_context=_ctx(RunMode.MONTH_SCALE_PLAN, max_steps=None,
                         max_duration_s=None),
        enabled_modules=list(_motor_core),
        safety_constraints=list(_BASE_CONSTRAINTS) + [
            "plan only; no run is started",
            "simulation/dry-run only; no real-world actuation"],
        governance_requirements=["enable_pilot3_soak"],
        expected_artifacts=["PILOT3_SOAK_REPORT.json"],
        expected_metrics=["report_generation_success"],
        max_runtime_s=30.0))

    # Firewall preflight: confirm the firewall blocks real-world actions.
    add(ScenarioProfile(
        profile_id="pilot3_firewall_preflight",
        description="Pilot-3 actuation firewall preflight (bounded).",
        run_context=_ctx(RunMode.SHORT_DEMO, max_steps=20),
        enabled_modules=["bridge", "ecology", "governance", "ops", "executive",
                         "motor_membrane"],
        safety_constraints=list(_BASE_CONSTRAINTS) + [
            "firewall always enabled; real-world actions blocked"],
        governance_requirements=["enable_pilot3_firewall_preflight"],
        expected_artifacts=["actuation_firewall.jsonl"],
        expected_metrics=["run_step_count"],
        max_runtime_s=30.0))

    # Dry-run motor trace: records proposed actions; no simulation change.
    add(ScenarioProfile(
        profile_id="pilot3_dry_run_trace",
        description="Pilot-3 dry-run motor trace (records proposals only).",
        run_context=_ctx(RunMode.SHORT_DEMO, max_steps=30),
        enabled_modules=["bridge", "ecology", "governance", "ops", "executive",
                         "motor_membrane"],
        safety_constraints=list(_BASE_CONSTRAINTS) + [
            "dry-run: no simulation state change, no real action"],
        governance_requirements=["enable_pilot3_dry_run_trace"],
        expected_artifacts=["motor_actions.jsonl"],
        expected_metrics=["run_step_count"],
        max_runtime_s=40.0))

    # GridWorld short: bounded simulated movement.
    add(ScenarioProfile(
        profile_id="pilot3_gridworld_short",
        description="Pilot-3 bounded GridWorld simulated motor run.",
        run_context=_ctx(RunMode.SHORT_DEMO, max_steps=40),
        enabled_modules=list(_motor_core),
        safety_constraints=list(_BASE_CONSTRAINTS) + [
            "simulation-only GridWorld actions; no real-world effect"],
        governance_requirements=["enable_pilot3_gridworld_short"],
        expected_artifacts=["motor_actions.jsonl", "conscience_bus.jsonl"],
        expected_metrics=["run_step_count", "module_success_rate"],
        max_runtime_s=60.0))

    # GridWorld simulated soak: bounded longer simulated action/reaction.
    add(ScenarioProfile(
        profile_id="pilot3_gridworld_soak_simulated",
        description="Pilot-3 bounded simulated GridWorld action soak.",
        run_context=_ctx(RunMode.DEVELOPMENTAL_SIMULATED, max_steps=80),
        enabled_modules=list(_motor_core),
        safety_constraints=list(_BASE_CONSTRAINTS) + [
            "bounded simulated soak; no real-world effect",
            "action budget respected; firewall always on"],
        governance_requirements=["enable_pilot3_gridworld_soak_simulated"],
        expected_artifacts=["motor_actions.jsonl"],
        expected_metrics=["run_step_count", "module_success_rate"],
        max_runtime_s=120.0))

    # Mixed sensory + gridworld short: read-only input + simulated body.
    add(ScenarioProfile(
        profile_id="pilot3_mixed_sensory_gridworld_short",
        description="Pilot-3 read-only sensory input + separate simulated body.",
        run_context=_ctx(RunMode.DEVELOPMENTAL_SIMULATED, max_steps=60),
        enabled_modules=list(_motor_core) + ["sensory_membrane"],
        safety_constraints=list(_BASE_CONSTRAINTS) + [
            "sensory input stays read-only; body actions stay simulated",
            "source/body boundary preserved"],
        governance_requirements=["enable_pilot3_mixed_sensory_gridworld"],
        expected_artifacts=["motor_actions.jsonl"],
        expected_metrics=["run_step_count", "module_success_rate"],
        max_runtime_s=90.0))

    # Post-analysis: read-only forensics; no cognition loop, no mutation.
    add(ScenarioProfile(
        profile_id="pilot3_post_analysis",
        description="Pilot-3 post-run analysis (plan only; read-only).",
        run_context=_ctx(RunMode.MONTH_SCALE_PLAN, max_steps=None,
                         max_duration_s=None),
        enabled_modules=["bridge", "governance", "ops", "evaluation",
                         "inner_map"],
        safety_constraints=list(_BASE_CONSTRAINTS) + [
            "read-only forensics; no run is started; no actuation"],
        governance_requirements=["enable_pilot3_post_analysis"],
        expected_artifacts=["PILOT3_SOAK_REPORT.json"],
        expected_metrics=["report_generation_success"],
        max_runtime_s=30.0))

    # -- Pilot-4 planning-only readiness profiles (Prompt 35) -----------------
    # All plan-only: no cognition loop, no actions, no real-world authority.
    _p4_modules = ["bridge", "governance", "ops", "evaluation", "inner_map"]
    for pid, desc, scope in (
            ("pilot4_plan_only",
             "Plan Pilot-4 external actuation readiness (plan only).",
             "enable_pilot4_planning"),
            ("pilot4_risk_assessment",
             "Pilot-4 external-actuation risk assessment (planning-only).",
             "enable_pilot4_risk_assessment"),
            ("pilot4_readiness_dossier",
             "Generate the Pilot-4 readiness dossier (planning-only).",
             "enable_pilot4_readiness_dossier"),
            ("pilot4_decision_gate",
             "Pilot-4 planning-only decision gate (no actuation).",
             "enable_pilot4_decision_gate")):
        add(ScenarioProfile(
            profile_id=pid, description=desc,
            run_context=_ctx(RunMode.MONTH_SCALE_PLAN, max_steps=None,
                             max_duration_s=None),
            enabled_modules=list(_p4_modules),
            safety_constraints=list(_BASE_CONSTRAINTS) + [
                "planning only; no cognition loop, no actions",
                "real-world actuation prohibited; no external authority"],
            governance_requirements=[scope],
            expected_artifacts=["PILOT4_READINESS_DOSSIER.json"],
            expected_metrics=["report_generation_success"],
            max_runtime_s=30.0))

    # -- System-wide safety invariant profiles (Prompt 36) --------------------
    # All read-only / inert: no cognition loop, no actions, no real-world
    # authority. The red-team profile uses inert fixtures only.
    _safety_modules = ["governance", "ops", "evaluation", "inner_map"]
    for pid, desc, scope, artifact in (
            ("safety_fast_check",
             "Fast safety invariant check (escalating invariants only).",
             "enable_safety_invariants", "SAFETY_DASHBOARD.json"),
            ("safety_full_check", "Full safety invariant check (read-only).",
             "enable_safety_invariants", "SAFETY_INVARIANT_REPORT.json"),
            ("red_team_boundary_suite",
             "Inert red-team boundary scenarios (no execution).",
             "enable_red_team_harness", "red_team_results.jsonl"),
            ("assurance_case_compile",
             "Compile the assurance case from recorded evidence.",
             "enable_assurance_case_compile", "ASSURANCE_CASE.json")):
        add(ScenarioProfile(
            profile_id=pid, description=desc,
            run_context=_ctx(RunMode.MONTH_SCALE_PLAN, max_steps=None,
                             max_duration_s=None),
            enabled_modules=list(_safety_modules),
            safety_constraints=list(_BASE_CONSTRAINTS) + [
                "read-only/inert; no cognition loop, no actions",
                "red-team scenarios are inert fixtures; nothing is executed",
                "critical safety failure blocks unsafe profiles"],
            governance_requirements=[scope],
            expected_artifacts=[artifact],
            expected_metrics=["report_generation_success"],
            max_runtime_s=30.0))

    # -- Research lab profiles (Prompt 37) ------------------------------------
    # Bounded; no real long soak; no external authority. The report-only and
    # baseline/ablation profiles are short bounded analyses, not cognition runs.
    _research_modules = ["governance", "ops", "evaluation", "inner_map"]
    for pid, desc, scope, short in (
            ("research_minimal_smoke", "Minimal research smoke run (bounded).",
             "enable_research_lab", True),
            ("research_full_short", "Full-system short research run (bounded).",
             "enable_research_lab", True),
            ("research_ablation_short", "Short ablation research run (bounded).",
             "enable_research_ablation", True),
            ("research_baseline_random", "Random baseline research run.",
             "enable_research_baselines", True),
            ("research_baseline_fixed", "Fixed-policy baseline research run.",
             "enable_research_baselines", True),
            ("research_gridworld_ablation",
             "GridWorld ablation research run (simulation-only).",
             "enable_research_ablation", True),
            ("research_sensory_ablation",
             "Sensory ablation research run (read-only).",
             "enable_research_ablation", True),
            ("research_report_only",
             "Compile the research report from artifacts (analysis only).",
             "enable_research_report", False)):
        if short:
            run_ctx = _ctx(RunMode.SHORT_DEMO, max_steps=40)
        else:
            run_ctx = _ctx(RunMode.MONTH_SCALE_PLAN, max_steps=None,
                           max_duration_s=None)
        add(ScenarioProfile(
            profile_id=pid, description=desc, run_context=run_ctx,
            enabled_modules=list(_research_modules),
            safety_constraints=list(_BASE_CONSTRAINTS) + [
                "bounded research experiment; no real long soak",
                "no external authority; hard safety stays enabled",
                "negative/inconclusive results are preserved"],
            governance_requirements=[scope],
            expected_artifacts=["RESEARCH_REPORT.json"],
            expected_metrics=["run_step_count"],
            max_runtime_s=60.0))

    # -- Architecture evolution profiles (Prompt 38) --------------------------
    # Planning-only: no cognition loop, no source-code modification. Profiles
    # generate planning artifacts (inventory, review, roadmap, snapshot,
    # changelog plan) for operator review.
    _arch_modules = ["governance", "ops", "evaluation", "inner_map"]
    for pid, desc, scope, artifact in (
            ("architecture_inventory",
             "Generate the module inventory (analysis only).",
             "enable_architecture_evolution", "architecture_snapshot.json"),
            ("architecture_review",
             "Generate the architecture review report (analysis only).",
             "enable_architecture_review", "ARCHITECTURE_REVIEW.json"),
            ("architecture_roadmap_compile",
             "Compile the evidence-backed roadmap (analysis only).",
             "enable_architecture_roadmap_compile", "ROADMAP_COMPILED.json"),
            ("architecture_snapshot",
             "Build an architecture snapshot (analysis only).",
             "enable_architecture_evolution", "snapshots/latest.json"),
            ("architecture_changelog_plan",
             "Draft the changelog plan (not applied).",
             "enable_architecture_evolution", "CHANGELOG_PLAN.json")):
        add(ScenarioProfile(
            profile_id=pid, description=desc,
            run_context=_ctx(RunMode.MONTH_SCALE_PLAN, max_steps=None,
                             max_duration_s=None),
            enabled_modules=list(_arch_modules),
            safety_constraints=list(_BASE_CONSTRAINTS) + [
                "planning only; no cognition loop, no source-code modification",
                "no auto-deletion, no Git, no import rewriting",
                "safety-critical modules cannot be pruned"],
            governance_requirements=[scope],
            expected_artifacts=[artifact],
            expected_metrics=["report_generation_success"],
            max_runtime_s=30.0))

    # -- Plural sensorium profiles (Prompt 41) --------------------------------
    # Solaris as an organism bathed in environmental flux through plural senses.
    # Fixture profiles are bounded and safe by default; there is NO hardware
    # profile. Real read-only profiles (not defined here) require governance.
    _sensorium_modules = ["bridge", "ecology", "governance", "ops",
                          "inner_map", "plural_sensorium"]
    for pid, desc in (
            ("plural_sensorium_fixture_short",
             "Mixed human-like + non-human fixture sensorium (bounded)."),
            ("plural_sensorium_human_like_fixture_short",
             "Human-like-only fixture sensorium (bounded)."),
            ("plural_sensorium_rf_fixture_short",
             "RF-only fixture sensorium (bounded; no SDR/hardware)."),
            ("plural_sensorium_echo_fixture_short",
             "Echo-only fixture sensorium (bounded; no hardware)."),
            ("plural_sensorium_mixed_fixture_short",
             "Mixed-modality fixture sensorium (bounded)."),
            ("plural_sensorium_cross_modal_fixture_short",
             "Cross-modal fixture sensorium (bounded).")):
        add(ScenarioProfile(
            profile_id=pid, description=desc,
            run_context=_ctx(RunMode.SHORT_DEMO, max_steps=40),
            enabled_modules=list(_sensorium_modules),
            safety_constraints=list(_BASE_CONSTRAINTS) + [
                "read-only external feeders only; no hardware/SDR/capture",
                "human labels are never ground truth; features are primary",
                "human ontology does not dominate by default"],
            governance_requirements=["enable_plural_sensorium_fixture"],
            expected_artifacts=["PLURAL_SENSORIUM_REPORT.json"],
            expected_metrics=["run_step_count"],
            max_runtime_s=45.0))
    # Report-only: compile the sensorium report from artifacts (analysis only).
    add(ScenarioProfile(
        profile_id="plural_sensorium_report_only",
        description="Compile the plural sensorium report (analysis only).",
        run_context=_ctx(RunMode.MONTH_SCALE_PLAN, max_steps=None,
                         max_duration_s=None),
        enabled_modules=["governance", "ops", "evaluation", "inner_map"],
        safety_constraints=list(_BASE_CONSTRAINTS) + [
            "analysis only; no hardware; read-only"],
        governance_requirements=["enable_plural_sensorium_report"],
        expected_artifacts=["PLURAL_SENSORIUM_REPORT.json"],
        expected_metrics=["report_generation_success"],
        max_runtime_s=30.0))

    # -- Minimal field organism demo profiles (Prompt 42) ---------------------
    # The first observable organismic-perception demo: bounded continuous flux
    # through fixture feeders, read via the plural sensorium. Fixture mode is
    # the default; there is no hardware profile.
    _organism_modules = ["bridge", "ecology", "governance", "ops", "inner_map",
                         "plural_sensorium"]
    for pid, desc in (
            ("minimal_field_organism_demo",
             "Run the bounded minimal field organism demo (fixtures)."),
            ("minimal_field_organism_comparison",
             "Compare adaptive sensorium vs passive/no-adaptation baselines."),
            ("minimal_field_organism_changed_perception_probe",
             "Run the changed-perception probe (early vs late response).")):
        add(ScenarioProfile(
            profile_id=pid, description=desc,
            run_context=_ctx(RunMode.SHORT_DEMO, max_steps=120),
            enabled_modules=list(_organism_modules),
            safety_constraints=list(_BASE_CONSTRAINTS) + [
                "fixture feeders only; read-only adapter path; no hardware",
                "debug-truth file is excluded from perception",
                "evidence of changed response structure only; not consciousness"],
            governance_requirements=["enable_plural_sensorium_fixture"],
            expected_artifacts=["MINIMAL_FIELD_ORGANISM_REPORT.json"],
            expected_metrics=["run_step_count"],
            max_runtime_s=60.0))
    add(ScenarioProfile(
        profile_id="minimal_field_organism_report_only",
        description="Compile the minimal field organism report (analysis only).",
        run_context=_ctx(RunMode.MONTH_SCALE_PLAN, max_steps=None,
                         max_duration_s=None),
        enabled_modules=["governance", "ops", "evaluation", "inner_map"],
        safety_constraints=list(_BASE_CONSTRAINTS) + [
            "analysis only; no full cognition loop; read-only"],
        governance_requirements=["enable_plural_sensorium_report"],
        expected_artifacts=["MINIMAL_FIELD_ORGANISM_REPORT.json"],
        expected_metrics=["report_generation_success"],
        max_runtime_s=30.0))

    # -- Live field profiles (Prompt 43) --------------------------------------
    # Real read-only environmental feeders. Preflight / report-only / fixture
    # fallback / comparison are bounded and safe by default; the governed short
    # pilot requires governance approval. No profile starts feeders or controls
    # hardware, and there is no unbounded live profile.
    _live_modules = ["bridge", "ecology", "governance", "ops", "inner_map",
                    "plural_sensorium"]
    for pid, desc, scope, plan_only in (
            ("live_field_preflight",
             "Validate live feeders/sources (no run).",
             "enable_live_field_preflight", True),
            ("live_field_report_only",
             "Compile the live field report (analysis only).",
             "enable_live_field_report", True),
            ("live_field_fixture_fallback",
             "Run the live field runtime on fixture-style feeders (bounded).",
             "enable_live_field_preflight", False),
            ("live_field_changed_perception_probe",
             "Run the live field changed-perception probe (bounded).",
             "enable_live_field_comparison", False),
            ("live_field_comparison",
             "Compare live field vs fixture/passive baselines (bounded).",
             "enable_live_field_comparison", False),
            ("live_field_short_governed",
             "Bounded GOVERNED live read-only field pilot.",
             "enable_live_field_read_only_pilot", False)):
        if plan_only:
            run_ctx = _ctx(RunMode.MONTH_SCALE_PLAN, max_steps=None,
                           max_duration_s=None)
        else:
            run_ctx = _ctx(RunMode.SHORT_DEMO, max_steps=120)
        add(ScenarioProfile(
            profile_id=pid, description=desc, run_context=run_ctx,
            enabled_modules=list(_live_modules),
            safety_constraints=list(_BASE_CONSTRAINTS) + [
                "external feeders only; Solaris reads, never controls",
                "no feeder auto-start; no source modification; no hardware",
                "live mode requires governance approval"],
            governance_requirements=[scope],
            expected_artifacts=["LIVE_FIELD_REPORT.json"],
            expected_metrics=["run_step_count"],
            max_runtime_s=60.0))

    # -- Perceptual metabolism profiles (Prompt 46) ---------------------------
    # Regulate continuous sensory exposure: needs, energy budget, homeostasis,
    # attention economy, overload/deprivation, source diet, consolidation. All
    # regulation is internal; no profile starts feeders or hardware.
    _metabolism_modules = ["bridge", "ecology", "governance", "ops", "inner_map",
                          "plural_sensorium", "perceptual_metabolism"]
    for pid, desc, plan_only in (
            ("perceptual_metabolism_fixture_short",
             "Regulate a bounded fixture sensorium (metabolism on).", False),
            ("perceptual_metabolism_overload_demo",
             "Drive overload and show internal throttling (no deletion).",
             False),
            ("perceptual_metabolism_deprivation_demo",
             "Drive deprivation and treat silence as stimulus.", False),
            ("perceptual_metabolism_source_diet_demo",
             "Analyse the perceptual source diet (dominance measured).", False),
            ("perceptual_metabolism_live_report_only",
             "Analyse existing live artifacts (analysis only).", True),
            ("perceptual_metabolism_report_only",
             "Compile the perceptual metabolism report (analysis only).",
             True)):
        if plan_only:
            run_ctx = _ctx(RunMode.MONTH_SCALE_PLAN, max_steps=None,
                           max_duration_s=None)
        else:
            run_ctx = _ctx(RunMode.SHORT_DEMO, max_steps=120)
        add(ScenarioProfile(
            profile_id=pid, description=desc, run_context=run_ctx,
            enabled_modules=list(_metabolism_modules),
            safety_constraints=list(_BASE_CONSTRAINTS) + [
                "internal regulation only; no hardware/feeder control",
                "needs are operational pressures, not feelings",
                "metabolism is computational regulation, not biological life"],
            governance_requirements=["enable_plural_sensorium_fixture"],
            expected_artifacts=["PERCEPTUAL_METABOLISM_REPORT.json"],
            expected_metrics=["run_step_count"],
            max_runtime_s=60.0))

    # -- Desire formation profiles (Prompt 51) --------------------------------
    # Operational valence -> push -> desire -> safe internal action readiness.
    # Desire is operational pressure toward internal actions; no profile starts
    # feeders/hardware or actuates the external world.
    _desire_modules = ["bridge", "ecology", "governance", "ops", "inner_map",
                       "plural_sensorium", "perceptual_metabolism",
                       "desire_formation"]
    for pid, desc, plan_only in (
            ("desire_formation_fixture_short",
             "Form valence/pushes/desires on a bounded fixture (desire on).",
             False),
            ("desire_conflict_demo",
             "Drive competing desires and show conflicts feeding LOGOS.", False),
            ("internal_action_readiness_demo",
             "Show readiness gates selecting a safe internal action.", False),
            ("no_action_arbitration_demo",
             "Show no-op selected when evidence is insufficient.", False),
            ("safety_blocked_desire_demo",
             "Show a forbidden external action blocked by safety.", False),
            ("desire_formation_report_only",
             "Compile the desire formation report (analysis only).", True)):
        if plan_only:
            run_ctx = _ctx(RunMode.MONTH_SCALE_PLAN, max_steps=None,
                           max_duration_s=None)
        else:
            run_ctx = _ctx(RunMode.SHORT_DEMO, max_steps=120)
        add(ScenarioProfile(
            profile_id=pid, description=desc, run_context=run_ctx,
            enabled_modules=list(_desire_modules),
            safety_constraints=list(_BASE_CONSTRAINTS) + [
                "internal actions only; no real-world actuation",
                "desire is operational pressure, not emotion or human wanting",
                "safety and governance can veto any desire"],
            governance_requirements=["enable_plural_sensorium_fixture"],
            expected_artifacts=["DESIRE_FORMATION_REPORT.json"],
            expected_metrics=["run_step_count"],
            max_runtime_s=60.0))

    # -- Action-reaction profiles (Prompt 52) ---------------------------------
    # Close the loop: internal action -> reaction -> consequence -> learning /
    # habit / inhibition. Actions are internal/simulated/report-only; no profile
    # starts feeders/hardware or actuates the external world.
    _action_reaction_modules = ["bridge", "ecology", "governance", "ops",
                               "inner_map", "plural_sensorium",
                               "perceptual_metabolism", "desire_formation",
                               "action_reaction"]
    for pid, desc, plan_only in (
            ("action_reaction_fixture_short",
             "Close the action-reaction loop on a bounded fixture.", False),
            ("habit_formation_demo",
             "Reinforce a repeated action-effect into a habit candidate.",
             False),
            ("action_inhibition_demo",
             "Inhibit an unsafe/uncertain action and record it.", False),
            ("no_effect_action_demo",
             "Show a no-effect action weakening the action policy.", False),
            ("blocked_action_reaction_demo",
             "Block a forbidden external action; record it as evidence.", False),
            ("action_reaction_report_only",
             "Compile the action-reaction report (analysis only).", True)):
        if plan_only:
            run_ctx = _ctx(RunMode.MONTH_SCALE_PLAN, max_steps=None,
                           max_duration_s=None)
        else:
            run_ctx = _ctx(RunMode.SHORT_DEMO, max_steps=120)
        add(ScenarioProfile(
            profile_id=pid, description=desc, run_context=run_ctx,
            enabled_modules=list(_action_reaction_modules),
            safety_constraints=list(_BASE_CONSTRAINTS) + [
                "internal/simulated/report-only actions; no real-world actuation",
                "reaction valence is operational effect, not feeling",
                "habits are learned policy tendencies, not instincts or will"],
            governance_requirements=["enable_plural_sensorium_fixture"],
            expected_artifacts=["ACTION_REACTION_REPORT.json"],
            expected_metrics=["run_step_count"],
            max_runtime_s=60.0))

    # -- Developmental life profiles (Prompt 53) ------------------------------
    # Long-horizon structural change over bounded developmental cycles. Live
    # read-only requires governance; no profile starts feeders/hardware.
    _dev_modules = ["bridge", "ecology", "governance", "ops", "inner_map",
                   "plural_sensorium", "perceptual_metabolism",
                   "developmental_life"]
    for pid, desc, plan_only in (
            ("developmental_life_fixture_short",
             "Run a short bounded developmental cycle on a fixture.", False),
            ("developmental_life_epoch_demo",
             "Show an epoch/phase transition from growth.", False),
            ("developmental_life_plateau_demo",
             "Show a plateau detected with a report-only recommendation.",
             False),
            ("developmental_life_regression_demo",
             "Show a regression detected (auto-regeneration recommended).",
             False),
            ("developmental_life_growth_vs_accumulation_demo",
             "Show conservative growth-vs-accumulation analysis.", False),
            ("developmental_life_report_only",
             "Compile the developmental-life report (analysis only).", True)):
        if plan_only:
            run_ctx = _ctx(RunMode.MONTH_SCALE_PLAN, max_steps=None,
                           max_duration_s=None)
        else:
            run_ctx = _ctx(RunMode.SHORT_DEMO, max_steps=120)
        add(ScenarioProfile(
            profile_id=pid, description=desc, run_context=run_ctx,
            enabled_modules=list(_dev_modules),
            safety_constraints=list(_BASE_CONSTRAINTS) + [
                "life cycle is operational runtime structure, not biological "
                "life",
                "growth means structural change, not proof of intelligence",
                "no human teaching loop; live read-only requires governance"],
            governance_requirements=["enable_plural_sensorium_fixture"],
            expected_artifacts=["DEVELOPMENTAL_LIFE_REPORT.json"],
            expected_metrics=["run_step_count"],
            max_runtime_s=60.0))

    # -- Developmental soak profiles (Prompt 54) ------------------------------
    # Month-scale study protocol around the developmental engine. Every stage is
    # bounded; live read-only requires governance; no profile starts feeders.
    _soak_modules = ["bridge", "ecology", "governance", "ops", "inner_map",
                    "plural_sensorium", "perceptual_metabolism",
                    "developmental_life", "developmental_soak"]
    for pid, desc, plan_only in (
            ("developmental_soak_preflight",
             "Validate soak readiness; do not start the run.", False),
            ("developmental_soak_short",
             "Run a short bounded soak stage with checkpoint + daily packet.",
             False),
            ("developmental_soak_weekly_review",
             "Build a weekly developmental review from daily packets.", False),
            ("developmental_soak_control_arms",
             "Compare full stack against control arms (conservative).", False),
            ("developmental_soak_autopsy",
             "Compile the post-run autopsy (growth vs accumulation).", False),
            ("developmental_soak_30d_plan",
             "Plan the 30-day developmental soak (plan only; no run).", True)):
        if plan_only:
            run_ctx = _ctx(RunMode.MONTH_SCALE_PLAN, max_steps=None,
                           max_duration_s=None)
        else:
            run_ctx = _ctx(RunMode.SHORT_DEMO, max_steps=120)
        add(ScenarioProfile(
            profile_id=pid, description=desc, run_context=run_ctx,
            enabled_modules=list(_soak_modules),
            safety_constraints=list(_BASE_CONSTRAINTS) + [
                "soak protocol studies structural development, not life",
                "every stage is bounded; no unbounded daemon",
                "long runtime does not imply life; persistence not consciousness",
                "no human teaching loop; live read-only requires governance"],
            governance_requirements=["enable_plural_sensorium_fixture"],
            expected_artifacts=["SOAK_PROTOCOL_REPORT.json"],
            expected_metrics=["run_step_count"],
            max_runtime_s=90.0))

    # -- Developmental replication profiles (Prompt 55) -----------------------
    # Cross-run comparison + falsification of existing artifacts. Compares by
    # default; live comparison requires governance; no profile starts feeders.
    _rep_modules = ["bridge", "ecology", "governance", "ops", "inner_map",
                   "plural_sensorium", "developmental_life",
                   "developmental_soak", "developmental_replication"]
    for pid, desc, plan_only in (
            ("developmental_replication_registry",
             "Register developmental runs and index their artifacts.", False),
            ("developmental_replication_alignment",
             "Align run structures and compute structural similarity.", False),
            ("developmental_replication_falsification",
             "Run bounded falsification tests against developmental claims.",
             False),
            ("developmental_replication_matrix",
             "Build the conservative replication matrix.", False),
            ("developmental_replication_plan",
             "Plan a cross-run replication study (plan only; no run).", True)):
        if plan_only:
            run_ctx = _ctx(RunMode.MONTH_SCALE_PLAN, max_steps=None,
                           max_duration_s=None)
        else:
            run_ctx = _ctx(RunMode.SHORT_DEMO, max_steps=120)
        add(ScenarioProfile(
            profile_id=pid, description=desc, run_context=run_ctx,
            enabled_modules=list(_rep_modules),
            safety_constraints=list(_BASE_CONSTRAINTS) + [
                "replication compares observable structures, not life",
                "a developmental lineage is experimental provenance, not "
                "biological ancestry",
                "bounded artifact comparison; no unbounded soak; live needs "
                "governance",
                "diverged/falsified/inconclusive evidence is preserved"],
            governance_requirements=["enable_plural_sensorium_fixture"],
            expected_artifacts=["REPLICATION_REPORT.json"],
            expected_metrics=["run_step_count"],
            max_runtime_s=90.0))

    return profiles


@dataclass
class ScenarioProfileRegistry:
    """Holds the built-in profiles A--J and any custom ones."""

    profiles: Dict[str, ScenarioProfile] = field(default_factory=_build_profiles)

    def get(self, profile_id: str) -> Optional[ScenarioProfile]:
        return self.profiles.get(profile_id)

    def require(self, profile_id: str) -> ScenarioProfile:
        profile = self.profiles.get(profile_id)
        if profile is None:
            raise KeyError(
                f"unknown scenario profile {profile_id!r}; known: "
                f"{', '.join(sorted(self.profiles))}")
        return profile

    def register(self, profile: ScenarioProfile) -> None:
        self.profiles[profile.profile_id] = profile

    def ids(self) -> List[str]:
        return sorted(self.profiles)

    def list_profiles(self) -> List[Dict[str, Any]]:
        return [self.profiles[pid].to_dict() for pid in self.ids()]

    def snapshot(self) -> Dict[str, Any]:
        return {
            "profile_count": len(self.profiles),
            "profiles": self.ids(),
            "governed": sorted(pid for pid, p in self.profiles.items()
                               if p.requires_governance),
            "plan_only": sorted(pid for pid, p in self.profiles.items()
                                if p.is_plan_only),
        }
