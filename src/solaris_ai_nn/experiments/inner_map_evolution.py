"""Inner MAP evolution experiment.

Runs a bounded continuous session while the Inner MAP repeatedly observes the
substrate, so you can watch the self-model evolve: the reservoir state moves,
habits strengthen, synthesis subtracts weak pathways, absence cycles appear in
silence, and reactions accumulate. The final Inner MAP is persisted to
``inner_map.json`` and a compact report (plus a Mermaid self-map) is printed.

Nothing here is conscious. The Inner MAP is a structured, measured self-model.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ..inner_map.state_graph import build_default_state_graph
from ..runtime.continuous_runner import ContinuousRunner
from .soak_continuity import ACTIONS, WORLD, _make_providers


@dataclass
class InnerMapEvolutionResult:
    """Outcome of the Inner MAP evolution experiment."""

    snapshot: Dict[str, Any]
    inner_map_path: str
    reservoir_norm: float
    strongest_habits: List[Dict[str, Any]]
    pruning_count: int
    dominant_signal_type: Optional[str]
    recent_absence_count: int
    brain_death_gap_seconds: float
    suggested_action: Optional[str]
    suggested_desire: Optional[str]
    hard_boundaries: List[str]
    mermaid_preview: str


def run_inner_map_evolution(
    steps: int = 300,
    state_dir: str = ".solaris_ai_nn_state/inner_map_demo",
    seed: int = 7,
    checkpoint_interval: int = 50,
    inner_map_update_interval: int = 10,
    prune_interval: int = 120,
    verbose: bool = False,
) -> InnerMapEvolutionResult:
    """Run the bounded Inner MAP evolution experiment and return its result."""
    stimulus_provider, reaction_provider = _make_providers()
    runner = ContinuousRunner(
        state_dir=state_dir,
        max_steps=steps,
        heartbeat_interval_s=0.5,
        checkpoint_interval_steps=checkpoint_interval,
        prune_interval_steps=prune_interval,
        inner_map_update_interval_steps=inner_map_update_interval,
        seed=seed,
        action_labels=ACTIONS,
        vocabulary=list(WORLD.keys()) + ["I exist!"],
        stimulus_provider=stimulus_provider,
        reaction_provider=reaction_provider,
        silence_threshold=3,
    )
    snapshot = runner.run()
    model = snapshot["inner_map"]

    graph = build_default_state_graph()
    mermaid_preview = "\n".join(graph.to_mermaid().splitlines()[:10])

    result = InnerMapEvolutionResult(
        snapshot=snapshot,
        inner_map_path=snapshot["inner_map_path"],
        reservoir_norm=model["neural"]["reservoir_state_norm"],
        strongest_habits=model["plasticity"]["strongest_habits"],
        pruning_count=model["plasticity"]["pruning_count"],
        dominant_signal_type=model["memory"]["dominant_recent_signal_type"],
        recent_absence_count=model["memory"]["recent_absence_count"],
        brain_death_gap_seconds=model["continuity"]["brain_death_gap_seconds"],
        suggested_action=model["tendencies"]["suggested_action"],
        suggested_desire=model["tendencies"]["suggested_desire"],
        hard_boundaries=[b["name"] for b in snapshot["boundaries"]["hard"]],
        mermaid_preview=mermaid_preview,
    )

    if verbose:
        print("=" * 64)
        print("Solaris-AI-NN -- Inner MAP evolution experiment")
        print("=" * 64)
        print(f"state dir:               {snapshot['state_dir']}")
        print(f"session / lifetime steps: {snapshot['session_steps']} / {snapshot['lifetime_steps']}")
        print(f"reservoir state norm:     {result.reservoir_norm:.4f}")
        print(f"recent signal dominance:  {result.dominant_signal_type} "
              f"(absence stimuli: {result.recent_absence_count})")
        print(f"pruning count:            {result.pruning_count}")
        print(f"brain-death gap (s):      {result.brain_death_gap_seconds:.3f}")
        print(f"suggested action/desire:  {result.suggested_action} / {result.suggested_desire}")
        print("strongest habits:")
        for h in result.strongest_habits[:5]:
            print(f"    {h['pattern']} -> {h['action']}  (w={h['weight']})")
        print(f"hard boundaries:          {', '.join(result.hard_boundaries)}")
        print(f"inner_map.json:           {result.inner_map_path}")
        print("-" * 64)
        print("Self-map (Mermaid preview):")
        print(result.mermaid_preview)
        print("-" * 64)
        print("The Inner MAP is a structured self-model -- observed, not conscious.")

    return result


def main() -> None:
    run_inner_map_evolution(verbose=True)


if __name__ == "__main__":
    main()
