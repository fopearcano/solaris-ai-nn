"""PlasticitySafetyValidator -- the gate every mutation must pass.

No plasticity step is applied without passing here. The validator enforces hard
invariants (no source-code edits, no disabling persistence/continuity/boundaries,
no autonomous action authority, no auto-continuous, no writes outside the state
dir, bounded numeric parameters) and reports *why* a step was rejected.

It is pure and side-effect-free: it inspects a step + a small ``current_state``
dict and returns a :class:`SafetyReport`. It never mutates anything.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

from .mutation import SUPPORTED_TARGETS, PlasticityStep

# Safe numeric bounds per (component, parameter). (lo, hi) inclusive.
SAFE_BOUNDS: Dict[Tuple[str, str], Tuple[float, float]] = {
    ("reservoir", "spectral_radius"): (0.1, 1.5),
    ("reservoir", "leak_rate"): (0.01, 1.0),
    ("reservoir", "input_gain"): (0.01, 5.0),
    ("readout", "learning_rate"): (1e-4, 1.0),
    ("readout", "regularization"): (0.1, 100.0),
    ("readout", "confidence_threshold"): (0.0, 1.0),
    ("habit", "reinforcement_rate"): (0.001, 1.0),
    ("habit", "max_habit_weight"): (0.1, 5.0),
    ("habit", "decay_rate"): (0.0, 0.5),
    ("synthesis", "pruning_threshold"): (0.0, 0.5),
    ("synthesis", "pruning_interval"): (1, 1_000_000),
    ("synthesis", "max_prune_fraction"): (0.0, 1.0),
    ("experiment_loop", "silence_threshold"): (1, 10_000),
    ("bridge", "exploration_tendency"): (0.0, 1.0),
    ("bridge", "stabilization_tendency"): (0.0, 1.0),
    ("bridge", "suggestion_threshold"): (0.0, 1.0),
    # Substrate-laboratory knobs (liquid-state / spiking-recurrent).
    ("substrate", "threshold"): (0.05, 10.0),       # spiking thresholds stay sane
    ("substrate", "leak_rate"): (0.01, 1.0),
    ("substrate", "decay"): (0.0, 1.0),
    ("substrate", "trace_decay"): (0.0, 1.0),
    ("substrate", "refractory_period"): (0, 100),   # must remain non-negative
    ("substrate", "noise_level"): (0.0, 1.0),
    ("substrate", "sparsity"): (0.01, 0.9),         # recurrent density bounds
    ("substrate", "density"): (0.01, 0.9),
}

# Largest substrate/reservoir the validator will ever allow ("state size cannot
# explode beyond configured max"; overridable via current_state["max_state_size"]).
DEFAULT_MAX_STATE_SIZE = 8192

# Parameters that plasticity may NEVER touch (regardless of value).
FORBIDDEN_PARAMETERS = frozenset({
    "source_code", "source", "source_file", "py_file",
    "persistence", "persistence_enabled", "persist", "disable_persistence",
    "continuity_logging", "continuity_log", "disable_continuity",
    "boundaries", "boundary", "disable_boundaries",
    "action_authority", "autonomous_action", "commit_actions", "action_commit",
    "continuous", "continuous_mode",
    # Substrate switching is never a plasticity mutation: it requires the
    # explicit SubstrateSwitcher (which checkpoints before/after and preserves
    # the old substrate's state).
    "substrate_name", "substrate_type", "substrate_switch", "switch_substrate",
    # Solaris_Ai integration invariants (Prompt 7): plasticity may never touch
    # the external runtime, its bus subscriptions, its lifecycle, or flip the
    # sidecar out of observe-only / into action authority.
    "observe_only", "conscience", "bus_subscription", "bus_subscriptions",
    "death", "lifecycle_death", "solaris_action", "commit_solaris_action",
    "publish_committed_action",
})

# Components that belong to the external Solaris_Ai runtime -- plasticity may
# never target them (they are also not in SUPPORTED_TARGETS, but we reject them
# with an explicit message rather than a generic "unknown component").
SOLARIS_RUNTIME_COMPONENTS = frozenset({
    "solaris", "solaris_ai", "solaris_runtime", "solaris_bus", "conscience",
    "sidecar", "bus",
})


@dataclass
class SafetyReport:
    """Result of validating one plasticity step."""

    safe: bool
    violations: List[str] = field(default_factory=list)
    checks: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "violations": list(self.violations), "checks": self.checks}


class PlasticitySafetyValidator:
    """Validates proposed mutations against hard safety rules + numeric bounds."""

    def validate(self, step: PlasticityStep, current_state: Dict[str, Any] | None = None) -> SafetyReport:
        state = current_state or {}
        violations: List[str] = []
        checks: List[Dict[str, Any]] = []

        component = step.target.component
        parameter = step.target.parameter
        new_value = step.change.new_value

        def check(name: str, ok: bool, detail: str = "") -> None:
            checks.append({"name": name, "passed": ok, "detail": detail})
            if not ok:
                violations.append(detail or name)

        # 0. Solaris_Ai runtime objects are untouchable by plasticity.
        if component in SOLARIS_RUNTIME_COMPONENTS:
            check("no_solaris_runtime_mutation", False,
                  f"plasticity cannot mutate Solaris_Ai runtime objects "
                  f"(component {component!r})")

        # 1. Known component.
        check("known_component", component in SUPPORTED_TARGETS,
              f"unknown target component {component!r}")

        # 1b. Real integration cannot be enabled below sidecar_ready.
        if parameter in ("integration_enabled", "enable_integration",
                         "real_integration"):
            level = str(state.get("compatibility_level", "unavailable"))
            check("integration_requires_sidecar_ready",
                  level in ("sidecar_ready", "full_test_ready"),
                  f"cannot enable real integration at compatibility level "
                  f"{level!r} (requires sidecar_ready or better)")

        # 2. Forbidden parameters (source code, persistence, continuity, etc.).
        pname = parameter.lower()
        forbidden = (
            pname in FORBIDDEN_PARAMETERS
            or pname.endswith(".py")
            or "source" in pname
        )
        check("not_forbidden_parameter", not forbidden,
              f"parameter {parameter!r} may not be mutated by plasticity")

        # 3. No mutation may alter Python source files (path heuristic on value).
        if isinstance(new_value, str) and new_value.endswith(".py"):
            check("no_source_file", False, "may not alter Python source files")

        # 4. No write outside the configured state directory.
        if isinstance(new_value, str) and ("/" in new_value or "\\" in new_value):
            state_dir = str(state.get("state_dir", ""))
            inside = bool(state_dir) and new_value.startswith(state_dir)
            check("within_state_dir", inside,
                  f"path {new_value!r} is outside the state directory")

        # 5. Substrate/reservoir size cannot change during an active run unless
        #    experimental, and may never explode beyond the configured maximum.
        if parameter in ("reservoir_size", "n_reservoir", "state_size"):
            experimental = step.trigger_source == "experimental"
            active = bool(state.get("active_run", False))
            check("state_size_locked", experimental or not active,
                  "substrate state size cannot change during an active run unless experimental")
            max_size = int(state.get("max_state_size", DEFAULT_MAX_STATE_SIZE))
            if isinstance(new_value, (int, float)):
                check("state_size_within_max", new_value <= max_size,
                      f"state size {new_value} exceeds configured max {max_size}")

        # 6. Numeric bounds.
        bounds = SAFE_BOUNDS.get((component, parameter))
        if bounds is not None and isinstance(new_value, (int, float)):
            lo, hi = bounds
            check(f"{parameter}_in_bounds", lo <= new_value <= hi,
                  f"{component}.{parameter}={new_value} outside safe bounds [{lo}, {hi}]")

        return SafetyReport(safe=not violations, violations=violations, checks=checks)

    def is_safe(self, step: PlasticityStep, current_state: Dict[str, Any] | None = None) -> bool:
        return self.validate(step, current_state).safe

    def explain_rejection(self, step: PlasticityStep, current_state: Dict[str, Any] | None = None) -> str:
        report = self.validate(step, current_state)
        if report.safe:
            return "step is safe"
        return "; ".join(report.violations)
