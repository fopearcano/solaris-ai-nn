"""A code-level map from Solaris_Ai concepts to Solaris-AI-NN modules.

This is documentation that lives in code so it cannot silently drift from the
package. It does **not** import the reference repo; it records, per Solaris_Ai
concept, which reference module inspired it and which NN module realises it as a
concrete mechanism (object / metric / experiment). The prose version lives in
``docs/SOLARIS_REFERENCE_MAP.md``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class Mapping:
    """One concept's correspondence between the two repositories."""

    concept: str
    reference_module: str  # path within fopearcano/solaris-ai
    nn_module: str  # dotted module within solaris_ai_nn
    relationship: str  # how NN relates without duplicating the reference


REFERENCE_MAP: List[Mapping] = [
    Mapping(
        concept="Signal vocabulary (Stimulus->Push->Desire->Action + side streams)",
        reference_module="src/solaris/runtime/signals.py",
        nn_module="solaris_ai_nn.signals.canonical",
        relationship="Re-expressed as self-contained dataclasses; field-compatible "
        "so the substrate speaks the same language. Not imported.",
    ),
    Mapping(
        concept="Typed pub/sub Bus",
        reference_module="src/solaris/runtime/bus.py",
        nn_module="solaris_ai_nn.runtime.experiment_loop",
        relationship="NN uses a single in-process loop, not a bus; the loop is the "
        "integration seam where a real Bus could later drive it.",
    ),
    Mapping(
        concept="AION / Impulse heartbeat + absence (Subtraction Principle)",
        reference_module="src/solaris/core/aion_impulse.py",
        nn_module="solaris_ai_nn.runtime.experiment_loop",
        relationship="Loop emits continuity heartbeats and synthesises escalating "
        "absence stimuli after silence; the substrate keeps adapting on its own beat.",
    ),
    Mapping(
        concept="Logos: division / union / fracture (dia-ballein vs sun-ballein)",
        reference_module="src/solaris/core/logos.py",
        nn_module="solaris_ai_nn.signals.canonical.LogosTension",
        relationship="LogosTension is consumed as a scalar input feature (fracture "
        "slot in the encoder); NN does not re-run the opposition engine itself.",
    ),
    Mapping(
        concept="Inner MAP (self-representation / boundaries)",
        reference_module="src/solaris/modules/inner_map.py",
        nn_module="solaris_ai_nn.memory.state_memory",
        relationship="State snapshots are the NN analogue of self-state; real "
        "MAP coupling is ROADMAP Phase 3.",
    ),
    Mapping(
        concept="Habit (per-meaning bias scalars, reinforcement)",
        reference_module="src/solaris/modules/habit.py",
        nn_module="solaris_ai_nn.plasticity.habit_reinforcement",
        relationship="Same [-1,+1] bias-toward-valence rule, reframed as "
        "(situation, action) pathway reinforcement that nudges the readout.",
    ),
    Mapping(
        concept="Synthesis through Subtraction (pruning weak weights)",
        reference_module="src/solaris/modules/synthesis.py",
        nn_module="solaris_ai_nn.plasticity.synthesis_pruning",
        relationship="Directly realised: prunes weak readout/habit weights and "
        "emits a SubtractionReport. Subtraction, not compression.",
    ),
    Mapping(
        concept="Backpropagation (conceptual responsibility assignment)",
        reference_module="src/solaris/modules/backpropagation.py",
        nn_module="solaris_ai_nn.reservoir.online_learning",
        relationship="NN uses a literal-but-tiny delta rule on the readout only "
        "(no BPTT); credit assignment is local and online, matching 'who/how much'.",
    ),
    Mapping(
        concept="Auto-Regeneration (repair / rewrite parameters)",
        reference_module="src/solaris/modules/auto_regeneration.py",
        nn_module="solaris_ai_nn.memory.consolidation",
        relationship="Stubbed: consolidation summarises memory; write-back/repair "
        "into the substrate is ROADMAP Phase 3.",
    ),
    Mapping(
        concept="Mysterium / Anticipation / Complexity",
        reference_module="src/solaris/modules/{mysterium,anticipation,complexity}.py",
        nn_module="solaris_ai_nn.signals.encoding + experiment_loop",
        relationship="Novelty/uncertainty enter via the encoder's novelty slot; "
        "absence-injection plays Complexity's anti-stagnation role. Dedicated NN "
        "modules are future work.",
    ),
]


def describe() -> str:
    """Render the mapping as a readable multi-line string."""
    lines = ["Solaris_Ai -> Solaris-AI-NN concept map:"]
    for m in REFERENCE_MAP:
        lines.append(f"\n* {m.concept}")
        lines.append(f"    reference: {m.reference_module}")
        lines.append(f"    nn:        {m.nn_module}")
        lines.append(f"    relation:  {m.relationship}")
    return "\n".join(lines)
