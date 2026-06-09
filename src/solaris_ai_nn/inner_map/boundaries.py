"""BoundaryRegistry -- the Inner MAP's record of what the system may/may not do.

Mirrors the dimensional-comparison role in Solaris_Ai
(``modules/dimensional_comparison.py``): the self-model must know its own edges.
Boundaries are split into:

* **hard** boundaries -- invariants this experimental substrate must never cross
  (CPU-only, no heavy ML frameworks, no autonomous file deletion or source
  rewriting, no unbounded run unless explicitly requested, and -- most
  importantly -- no autonomous action commitment: the NN only *suggests*
  Actions/Desires);
* **soft** boundaries -- recommended operating points (reservoir size, trace
  length, checkpoint interval, pruning threshold, silence window).

``check_violation`` inspects a small state dict and reports any crossings. The
registry only *observes and reports*; it does not enforce anything by itself.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class Boundary:
    """A single named boundary."""

    name: str
    kind: str  # "hard" | "soft"
    description: str
    recommended: Any = None


@dataclass
class BoundaryViolation:
    """A detected crossing of a boundary."""

    boundary: str
    kind: str
    detail: str

    def to_dict(self) -> Dict[str, Any]:
        return {"boundary": self.boundary, "kind": self.kind, "detail": self.detail}


# Hard invariants of the experimental substrate.
HARD_BOUNDARIES: List[Boundary] = [
    Boundary("cpu_only", "hard", "Runs on CPU only; no GPU/accelerator required."),
    Boundary("no_heavy_ml_frameworks", "hard",
             "No PyTorch/TensorFlow/JAX/transformers/LangChain or vector DBs."),
    Boundary("no_autonomous_file_deletion", "hard",
             "Never deletes files autonomously; trace memory is append-only."),
    Boundary("no_source_code_rewriting", "hard",
             "Does not rewrite its own source code."),
    Boundary("no_unbounded_run_unless_requested", "hard",
             "No unbounded loop unless continuous=True is explicitly set."),
    Boundary("action_authority_suggest_only", "hard",
             "May only suggest Actions/Desires; never commits them autonomously."),
]

# Recommended operating points (defaults the runner/bridge use).
SOFT_BOUNDARIES: List[Boundary] = [
    Boundary("reservoir_size", "soft", "Recommended reservoir units.", recommended=128),
    Boundary("trace_length", "soft", "Recommended max in-memory trace length.", recommended=10_000),
    Boundary("checkpoint_interval_steps", "soft", "Recommended checkpoint cadence.", recommended=50),
    Boundary("pruning_threshold", "soft", "Recommended readout pruning magnitude.", recommended=0.01),
    Boundary("max_silence_window", "soft",
             "Recommended silent steps before absence-stimulus generation.", recommended=5),
]


@dataclass
class BoundaryRegistry:
    """Holds the hard/soft boundaries and checks a state dict against them."""

    hard: List[Boundary] = field(default_factory=lambda: list(HARD_BOUNDARIES))
    soft: List[Boundary] = field(default_factory=lambda: list(SOFT_BOUNDARIES))

    def list_boundaries(self) -> List[Boundary]:
        """All boundaries (hard first, then soft)."""
        return list(self.hard) + list(self.soft)

    def check_violation(self, state: Dict[str, Any]) -> List[BoundaryViolation]:
        """Inspect ``state`` and return any boundary violations.

        Recognised state keys (all optional):
            unbounded / explicitly_continuous, action_committed, uses_heavy_ml,
            deleted_files, rewrote_source, uses_gpu,
            reservoir_size, trace_length.
        """
        violations: List[BoundaryViolation] = []

        if state.get("unbounded") and not state.get("explicitly_continuous"):
            violations.append(BoundaryViolation(
                "no_unbounded_run_unless_requested", "hard",
                "running unbounded without an explicit continuous=True request"))
        if state.get("action_committed"):
            violations.append(BoundaryViolation(
                "action_authority_suggest_only", "hard",
                "an Action was committed autonomously; only suggestions are allowed"))
        if state.get("uses_heavy_ml"):
            violations.append(BoundaryViolation(
                "no_heavy_ml_frameworks", "hard",
                "a disallowed heavy ML framework is in use"))
        if state.get("uses_gpu"):
            violations.append(BoundaryViolation("cpu_only", "hard", "GPU/accelerator in use"))
        if state.get("deleted_files"):
            violations.append(BoundaryViolation(
                "no_autonomous_file_deletion", "hard", "files were deleted autonomously"))
        if state.get("rewrote_source"):
            violations.append(BoundaryViolation(
                "no_source_code_rewriting", "hard", "source code was rewritten"))

        # Soft boundaries: report, but mark as 'soft' (advisory).
        rec = {b.name: b.recommended for b in self.soft}
        if "reservoir_size" in state and state["reservoir_size"] > 4 * rec["reservoir_size"]:
            violations.append(BoundaryViolation(
                "reservoir_size", "soft",
                f"reservoir {state['reservoir_size']} far exceeds recommended {rec['reservoir_size']}"))
        if "trace_length" in state and state["trace_length"] > rec["trace_length"]:
            violations.append(BoundaryViolation(
                "trace_length", "soft",
                f"trace {state['trace_length']} exceeds recommended {rec['trace_length']}"))
        return violations

    def to_dict(self) -> Dict[str, Any]:
        def dump(bs: List[Boundary]) -> List[Dict[str, Any]]:
            return [
                {"name": b.name, "kind": b.kind, "description": b.description,
                 "recommended": b.recommended}
                for b in bs
            ]
        return {"hard": dump(self.hard), "soft": dump(self.soft)}
