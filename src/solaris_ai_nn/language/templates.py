"""Deterministic explanation templates.

Plain ``str.format_map`` templates with a safe default for missing fields:
absent values render as ``unknown`` rather than raising or being invented.
Same inputs always produce the same string -- templates are testable artifacts,
not generation.
"""

from __future__ import annotations

from typing import Any, Dict


class _SafeFields(dict):
    """format_map helper: missing fields render as 'unknown'."""

    def __missing__(self, key: str) -> str:
        return "unknown"


TEMPLATES: Dict[str, str] = {
    "signal_received": (
        "A {signal_type} signal from {origin} was received with intensity "
        "{intensity}."),
    "signal_absence": (
        "An absence stimulus was detected: the system sensed no meaningful "
        "input and generated internal drive instead."),
    "substrate_updated": (
        "The selected substrate was {substrate_type}; its state norm changed "
        "from {old_norm} to {new_norm}."),
    "substrate_state": (
        "The {substrate_type} substrate has {state_size} units; state norm "
        "{state_norm}, activity rate {activity_rate}, drift {drift}."),
    "action_suggested": (
        "The readout suggested {action} with confidence {confidence}. This is "
        "a tendency, not a committed decision."),
    "action_explored": (
        "The suggestion {action} came from exploration (epsilon {exploration}) "
        "rather than the highest-scoring tendency."),
    "action_blocked": (
        "The action {action} was blocked because {reason}."),
    "action_executed": (
        "The simulated action {action} was executed; consequence: {consequence}."),
    "reaction_feedback": (
        "The last feedback valence was {valence}, so the online readout was "
        "updated toward that outcome."),
    "habit_reinforced": (
        "The habit pathway {pathway} was reinforced to {weight}."),
    "habit_strongest": (
        "The strongest habit maps {pattern} to {action} with weight {weight}, "
        "built from repeated feedback."),
    "synthesis_pruned": (
        "Synthesis removed {count} weak pathways because {reason}."),
    "plasticity_applied": (
        "Plasticity changed {target} from {old_value} to {new_value} because "
        "{reason}; the change is bounded, audited, and rollbackable."),
    "plasticity_rejected": (
        "Plasticity proposed changing {target} but the safety validator "
        "rejected it: {reason}."),
    "continuity_gap": (
        "A previous run appears to have stopped unexpectedly; the continuity "
        "gap was {seconds} seconds."),
    "continuity_clean": (
        "The system has restarted {restarts} time(s); the last shutdown was "
        "recorded as graceful."),
    "energy_low": (
        "Energy is low ({energy}); an internal low-energy stimulus was emitted."),
    "embodiment_state": (
        "The simulated body is at {position} with energy {energy} "
        "(exhausted: {exhausted}); its last action was {last_action} "
        "({last_result}). Action authority is {authority}."),
    "inner_map_state": (
        "The Inner MAP tracks: substrate {substrate_type} (norm {state_norm}), "
        "{habit_pathways} habit pathways, {pruning_count} pruning passes, "
        "lifetime steps {lifetime_steps}, restarts {restarts}."),
    "silence_summary": (
        "During silence the system processed {absence_count} absence stimuli; "
        "the substrate kept updating ({reservoir_updates} updates) instead of "
        "going inert."),
    "does_not_know": (
        "The system does not know: {missing} is not present in the current "
        "context, and the language layer does not invent missing data."),
}


def render(name: str, **fields: Any) -> str:
    """Render a named template deterministically; missing fields -> 'unknown'."""
    template = TEMPLATES.get(name)
    if template is None:
        return TEMPLATES["does_not_know"].format_map(
            _SafeFields(missing=f"template {name!r}"))
    safe = _SafeFields({k: ("unknown" if v is None else v)
                        for k, v in fields.items()})
    return template.format_map(safe)
