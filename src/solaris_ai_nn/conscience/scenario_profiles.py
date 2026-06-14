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
