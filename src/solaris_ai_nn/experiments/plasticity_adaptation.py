"""Plasticity adaptation experiment (feedback inversion).

Runs a bounded session where the world's reward rule **flips at the midpoint**:
an action that was correct in the first half becomes wrong in the second half.
With plasticity enabled, the engine can adjust the learning rate, habit weights,
and pruning threshold (all bounded, validated, logged, rollbackable) to help the
substrate re-adapt. The experiment reports before/after metrics and the
plasticity audit path.

Nothing here edits source code or runs unbounded; plasticity only tunes runtime
parameters within safe bounds.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..runtime.continuous_runner import ContinuousRunner
from ..signals import canonical as C

WORLD = {"light": "approach", "noise": "withdraw", "food": "consume"}
FLIPPED = {"light": "withdraw", "noise": "consume", "food": "approach"}
ACTIONS = ["approach", "withdraw", "consume"]


@dataclass
class PlasticityAdaptationResult:
    snapshot: Dict[str, Any]
    audit_path: str
    applied_count: int
    rejected_count: int
    learning_rate_before: float
    learning_rate_after: float
    exploration_before: float
    exploration_after: float
    accuracy_first_phase: float
    accuracy_after_flip: float
    history: List[int] = field(default_factory=list)


def _make_providers(half: int, history: List[Dict[str, Any]]):
    payloads = list(WORLD.keys())

    def stimulus_provider(step: int) -> Optional[C.Stimulus]:
        if step % 9 < 3:  # silence window -> absence stimuli
            return None
        return C.Stimulus(origin="world", modality="sensor",
                          payload=payloads[step % len(payloads)], intensity=0.6)

    def reaction_provider(result: Dict[str, Any], stim: C.Stimulus) -> Optional[float]:
        step = result["step"]
        mapping = WORLD if step < half else FLIPPED
        correct = mapping.get(str(stim.payload))
        if correct is None:
            return None
        hit = 1 if result["suggested_action"] == correct else 0
        history.append({"phase": 1 if step < half else 2, "hit": hit})
        return 1.0 if hit else -1.0

    return stimulus_provider, reaction_provider


def _phase_accuracy(history: List[Dict[str, Any]], phase: int, tail_frac: float = 0.4) -> float:
    rows = [h["hit"] for h in history if h["phase"] == phase]
    if not rows:
        return 0.0
    tail = rows[-max(1, int(len(rows) * tail_frac)):]
    return sum(tail) / len(tail)


def run_plasticity_adaptation(
    steps: int = 500,
    state_dir: str = ".solaris_ai_nn_state/plasticity_demo",
    seed: int = 7,
    enable_plasticity: bool = True,
    dry_run: bool = False,
    verbose: bool = False,
) -> PlasticityAdaptationResult:
    """Run the feedback-inversion adaptation experiment."""
    history: List[Dict[str, Any]] = []
    stimulus_provider, reaction_provider = _make_providers(steps // 2, history)

    runner = ContinuousRunner(
        state_dir=state_dir, max_steps=steps, checkpoint_interval_steps=50,
        prune_interval_steps=max(80, steps // 5), seed=seed, action_labels=ACTIONS,
        vocabulary=list(WORLD.keys()) + ["I exist!"],
        stimulus_provider=stimulus_provider, reaction_provider=reaction_provider,
        silence_threshold=3, enable_plasticity=enable_plasticity,
        plasticity_interval_steps=50, plasticity_dry_run=dry_run,
    )
    lr_before = runner.bridge.learner.lr
    explore_before = runner.bridge.exploration
    snapshot = runner.run()
    eng = runner.plasticity_engine

    result = PlasticityAdaptationResult(
        snapshot=snapshot,
        audit_path=str(runner.pm.plasticity_audit_path),
        applied_count=eng.applied_count if eng else 0,
        rejected_count=eng.rejected_count if eng else 0,
        learning_rate_before=lr_before,
        learning_rate_after=runner.bridge.learner.lr,
        exploration_before=explore_before,
        exploration_after=runner.bridge.exploration,
        accuracy_first_phase=_phase_accuracy(history, 1),
        accuracy_after_flip=_phase_accuracy(history, 2),
        history=[h["hit"] for h in history],
    )

    if verbose:
        _print_report(result, dry_run)
    return result


def rollback_last(state_dir: str, seed: int = 7, verbose: bool = False) -> Dict[str, Any]:
    """Load a persisted brain and roll back its last applied plasticity step."""
    runner = ContinuousRunner(
        state_dir=state_dir, max_steps=1, seed=seed, action_labels=ACTIONS,
        vocabulary=list(WORLD.keys()) + ["I exist!"], enable_plasticity=True,
    )
    engine = runner.plasticity_engine
    rec = engine.rollback_manager.last_applied()
    if rec is None:
        if verbose:
            print("No applied plasticity step found to roll back.")
        return {"rolled_back": False, "message": "nothing to roll back"}

    before = engine.registry.get(rec.target)
    result = runner.rollback_last_plasticity()
    after = engine.registry.get(rec.target)
    # Persist the rolled-back parameters so the change sticks.
    runner._checkpoint("post-rollback", 0, runner.lifetime_base)

    out = {
        "rolled_back": result.applied,
        "step_id": result.step_id,
        "target": rec.target.label(),
        "value_before_rollback": before,
        "value_after_rollback": after,
        "message": result.message,
    }
    if verbose:
        print("=" * 60)
        print("Solaris-AI-NN -- rollback last plasticity step")
        print("=" * 60)
        print(f"target:               {out['target']}")
        print(f"value before rollback: {out['value_before_rollback']}")
        print(f"value after rollback:  {out['value_after_rollback']}")
        print(f"rolled back:          {out['rolled_back']} ({out['message']})")
    return out


def _print_report(result: PlasticityAdaptationResult, dry_run: bool) -> None:
    print("=" * 64)
    print("Solaris-AI-NN -- plasticity adaptation experiment (feedback inversion)")
    print("=" * 64)
    snap = result.snapshot
    print(f"state dir:                 {snap['state_dir']}")
    print(f"session steps:             {snap['session_steps']}")
    print(f"plasticity:                {'DRY-RUN' if dry_run else 'enabled'}")
    print(f"applied / rejected steps:  {result.applied_count} / {result.rejected_count}")
    print(f"learning rate before/after:{result.learning_rate_before:.4f} -> {result.learning_rate_after:.4f}")
    print(f"exploration before/after:  {result.exploration_before:.4f} -> {result.exploration_after:.4f}")
    print(f"accuracy phase 1 (late):   {result.accuracy_first_phase:.0%}")
    print(f"accuracy after flip (late):{result.accuracy_after_flip:.0%}")
    print(f"plasticity audit:          {result.audit_path}")
    print("-" * 64)
    if dry_run:
        print("Dry-run: proposals were validated and logged but NOT applied.")
    print("Every mutation is proposed, validated, logged, and rollbackable.")
    print("No source code was modified; no claim of consciousness.")


def main() -> None:
    run_plasticity_adaptation(verbose=True)


if __name__ == "__main__":
    main()
