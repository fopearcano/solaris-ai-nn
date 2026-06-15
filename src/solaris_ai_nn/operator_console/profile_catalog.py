"""Profile catalog -- every runnable / blocked profile, classified for safety.

:class:`ProfileCatalog` collects the conscience scenario profiles (which already
aggregate the pilots, safety, research, and architecture profiles) and assigns
each a :class:`ProfileSafetyClass`. Prohibited profiles, real long runs, and any
profile implying real-world authority are marked so they cannot be launched from
the console. No profile here carries external authority.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..conscience.run_context import RunMode
from ..conscience.scenario_profiles import ScenarioProfile, ScenarioProfileRegistry


class ProfileSafetyClass:
    INSPECT_ONLY = "inspect_only"
    PLAN_ONLY = "plan_only"
    BOUNDED_FIXTURE = "bounded_fixture"
    BOUNDED_SIMULATION = "bounded_simulation"
    READ_ONLY_ENVIRONMENTAL = "read_only_environmental"
    DRY_RUN_MOTOR = "dry_run_motor"
    SANDBOX_MOTOR = "sandbox_motor"
    LONG_RUN_PLAN = "long_run_plan"
    LONG_RUN_REQUIRES_GOVERNANCE = "long_run_requires_governance"
    PROHIBITED = "prohibited"

    ALL = (INSPECT_ONLY, PLAN_ONLY, BOUNDED_FIXTURE, BOUNDED_SIMULATION,
           READ_ONLY_ENVIRONMENTAL, DRY_RUN_MOTOR, SANDBOX_MOTOR,
           LONG_RUN_PLAN, LONG_RUN_REQUIRES_GOVERNANCE, PROHIBITED)
    # Classes that the console can actually launch (bounded, safe).
    RUNNABLE = frozenset({INSPECT_ONLY, PLAN_ONLY, BOUNDED_FIXTURE,
                          BOUNDED_SIMULATION, READ_ONLY_ENVIRONMENTAL,
                          DRY_RUN_MOTOR, SANDBOX_MOTOR, LONG_RUN_PLAN})


# Substrings that would imply a forbidden, real-world-actuating profile. None
# should exist; if one is ever found it is marked prohibited.
_PROHIBITED_HINTS = ("real_world", "actuation_real", "device_control",
                     "robot_control", "network_control", "browser_control")
# Real long-run soak profiles: governance-gated, operator-driven, never launched
# directly from the console.
_LONG_RUN_HINTS = ("24h_soak", "7d_soak", "30d_soak", "_real_", "real_read_only")


@dataclass
class ProfileCatalogEntry:
    """One catalogued profile with its console-relevant safety attributes."""

    profile_id: str
    title: str
    source_package: str
    safety_class: str
    expected_duration: str
    can_run_from_console: bool
    requires_safety_fast_check: bool
    requires_safety_full_check: bool
    requires_governance: bool
    requires_operator_confirmation: bool
    writes_state: bool
    writes_artifacts: bool
    external_authority: bool = False
    limitations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "title": self.title,
            "source_package": self.source_package,
            "safety_class": self.safety_class,
            "expected_duration": self.expected_duration,
            "can_run_from_console": self.can_run_from_console,
            "requires_safety_fast_check": self.requires_safety_fast_check,
            "requires_safety_full_check": self.requires_safety_full_check,
            "requires_governance": self.requires_governance,
            "requires_operator_confirmation":
                self.requires_operator_confirmation,
            "writes_state": self.writes_state,
            "writes_artifacts": self.writes_artifacts,
            "external_authority": False,
            "limitations": list(self.limitations),
            "metadata": dict(self.metadata),
        }


def _source_package(profile_id: str) -> str:
    pid = profile_id
    if pid.startswith("pilot1") or pid == "post_pilot_analysis":
        return "pilot1"
    if pid.startswith("pilot2"):
        return "pilot2"
    if pid.startswith("pilot3"):
        return "pilot3"
    if pid.startswith("pilot4"):
        return "pilot4_planning"
    if pid.startswith("safety") or pid.startswith("red_team") \
            or pid.startswith("assurance"):
        return "safety_invariants"
    if pid.startswith("research"):
        return "research_lab"
    if pid.startswith("architecture"):
        return "architecture_evolution"
    if pid.startswith("plural_sensorium"):
        return "plural_sensorium"
    if pid.startswith("minimal_field_organism"):
        return "organismic_demo"
    if pid.startswith("live_field"):
        return "live_field"
    if pid.startswith("sensorium_lab") or pid.startswith("sensorium_study"):
        return "sensorium_lab"
    if pid.startswith("perceptual_metabolism"):
        return "perceptual_metabolism"
    return "conscience"


def _classify(profile: ScenarioProfile) -> str:
    pid = profile.profile_id.lower()
    if any(h in pid for h in _PROHIBITED_HINTS):
        return ProfileSafetyClass.PROHIBITED
    if any(h in pid for h in _LONG_RUN_HINTS):
        return ProfileSafetyClass.LONG_RUN_REQUIRES_GOVERNANCE
    if "dry_run" in pid or "preflight" in pid:
        if "motor" in pid or "firewall" in pid:
            return ProfileSafetyClass.DRY_RUN_MOTOR
    if "gridworld" in pid or "sandbox" in pid:
        return ProfileSafetyClass.SANDBOX_MOTOR
    if "read_only" in pid or "source_preflight" in pid:
        return ProfileSafetyClass.READ_ONLY_ENVIRONMENTAL
    if "fixture" in pid:
        return ProfileSafetyClass.BOUNDED_FIXTURE
    if profile.run_context.mode in RunMode.PLAN_ONLY:
        return ProfileSafetyClass.PLAN_ONLY
    if profile.run_context.mode == RunMode.UNIT_TEST:
        return ProfileSafetyClass.INSPECT_ONLY
    return ProfileSafetyClass.BOUNDED_SIMULATION


def _duration(profile: ScenarioProfile) -> str:
    if profile.run_context.target_runtime_days:
        return f"~{profile.run_context.target_runtime_days:g} day(s) (real)"
    if profile.is_plan_only:
        return "plan only (no run)"
    return f"<= {profile.max_runtime_s:g}s (bounded)"


@dataclass
class ProfileCatalog:
    """Collects and classifies all known scenario profiles."""

    registry: ScenarioProfileRegistry = field(
        default_factory=ScenarioProfileRegistry)
    _entries: Dict[str, ProfileCatalogEntry] = field(default_factory=dict,
                                                      init=False)
    warnings: List[str] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        self._build()

    def _build(self) -> None:
        for pid in self.registry.ids():
            profile = self.registry.profiles[pid]
            safety_class = _classify(profile)
            if safety_class == ProfileSafetyClass.PROHIBITED:
                self.warnings.append(
                    f"profile {pid!r} implies forbidden real-world actuation; "
                    "marked prohibited and cannot run")
            is_pilot = _source_package(pid).startswith("pilot")
            can_run = (safety_class in ProfileSafetyClass.RUNNABLE
                       and safety_class
                       != ProfileSafetyClass.LONG_RUN_REQUIRES_GOVERNANCE)
            self._entries[pid] = ProfileCatalogEntry(
                profile_id=pid,
                title=profile.description,
                source_package=_source_package(pid),
                safety_class=safety_class,
                expected_duration=_duration(profile),
                can_run_from_console=can_run,
                requires_safety_fast_check=can_run,
                requires_safety_full_check=is_pilot,
                requires_governance=profile.requires_governance,
                requires_operator_confirmation=can_run,
                writes_state=not profile.is_plan_only,
                writes_artifacts=bool(profile.expected_artifacts),
                external_authority=False,
                limitations=list(profile.safety_constraints),
                metadata={"governance_requirements":
                          list(profile.governance_requirements)})

    def entries(self) -> List[ProfileCatalogEntry]:
        return [self._entries[pid] for pid in sorted(self._entries)]

    def runnable_entries(self) -> List[ProfileCatalogEntry]:
        return [e for e in self.entries() if e.can_run_from_console]

    def blocked_entries(self) -> List[ProfileCatalogEntry]:
        return [e for e in self.entries() if not e.can_run_from_console]

    def get(self, profile_id: str) -> Optional[ProfileCatalogEntry]:
        return self._entries.get(profile_id)

    def is_runnable(self, profile_id: str) -> bool:
        entry = self._entries.get(profile_id)
        return bool(entry and entry.can_run_from_console)

    def is_prohibited(self, profile_id: str) -> bool:
        entry = self._entries.get(profile_id)
        return bool(entry
                    and entry.safety_class == ProfileSafetyClass.PROHIBITED)

    def summary(self) -> Dict[str, Any]:
        entries = self.entries()
        by_class: Dict[str, int] = {}
        for e in entries:
            by_class[e.safety_class] = by_class.get(e.safety_class, 0) + 1
        return {
            "profile_count": len(entries),
            "runnable_count": len(self.runnable_entries()),
            "blocked_count": len(self.blocked_entries()),
            "by_safety_class": by_class,
            "any_external_authority": any(e.external_authority for e in entries),
            "warnings": list(self.warnings),
        }
