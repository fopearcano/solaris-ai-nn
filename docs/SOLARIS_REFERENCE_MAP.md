# Solaris_Ai → Solaris-AI-NN reference map

This document is the result of auditing the canonical reference repository
[`fopearcano/solaris-ai`](https://github.com/fopearcano/solaris-ai) (package
`src/solaris/`) **before** writing any code in this repo. It records what each
reference concept does and maps it to the concrete Solaris-AI-NN module that was
inspired by it.

Two rules govern this relationship:

1. **Do not duplicate Solaris_Ai.** This repo builds *neural/learning substrates*
   around the concepts; it does not re-implement the conceptual modules.
2. **Do not import, mutate, or overwrite Solaris_Ai.** The vocabulary is
   re-expressed self-containedly (`signals/canonical.py`), field-compatible so a
   future bridge can wire the two together.

The machine-readable version of this map lives in
`solaris_ai_nn/bridges/solaris_reference.py` (`REFERENCE_MAP`).

---

## Audit summary of the reference architecture

### Canonical signal chain — `src/solaris/runtime/signals.py`
A typed message hierarchy on a base `Signal` (`id`, `timestamp`, `origin`). The
spine is `Stimulus → Push → Desire → Action`, enriched by `Reaction`,
`MeaningEvent`, `MapUpdate`, and `LogosTension`. `Stimulus.is_absence` encodes
the **Subtraction Principle**: the *absence* of expected input is meaningful.
`Reaction.valence ∈ [−1, +1]` drives reinforcement. `LogosTension` computes
`fracture = |division − union|`.

### AION / Impulse — `src/solaris/core/aion_impulse.py`
The system's **heartbeat**. Every `period` it emits a low-intensity *continuity*
`Push` so the system is never inert. External stimuli trigger a *reactive* `Push`
proportional to intensity. After silence exceeds a threshold it emits a
self-directed **absence** `Stimulus` ("I exist!") whose intensity escalates, then
resets — the Subtraction Principle in action. It assigns no meaning; it only
generates activity.

### Logos — `src/solaris/core/logos.py`
The **opposition engine**. *Dia-ballein* (rational, division, data-present) vs
*sun-ballein* (irrational, union, data-absent) as competing decaying scalars.
Reactive pushes feed `division`; continuity pushes feed `union`. Each cycle it
decays both and publishes a `LogosTension`. **Fracture** (the mismatch) is "the
substrate of choice".

### Inner MAP — `src/solaris/modules/inner_map.py`
The system's **self-representation**: `facts` (beliefs about itself) and
`boundaries` (self-limits / habituated edges). A passive listener — consumes
`MapUpdate`, `MeaningEvent`, `LogosTension`; publishes nothing; exposes a
`snapshot()`.

### Habit — `src/solaris/modules/habit.py`
**Reinforcement** via per-meaning bias scalars in `[−1, +1]`, updated
`new = old + lr·valence` on each Action→Reaction pair. Crossing `±0.5` publishes a
`MapUpdate` (forcing a boundary into the Inner MAP). Exposes `bias_for()` and
`prune_below()`.

### Synthesis — `src/solaris/modules/synthesis.py`
**Synthesis through subtraction.** On a slow cycle it prunes weak habit weights
below a (Mysterium-scaled) threshold; each removal shifts information from
"present" to "absent". Explicitly *not* compression — reduction that also
produces the Irrational. Publishes `MapUpdate` with pruned counts.

### Backpropagation — `src/solaris/modules/backpropagation.py`
**Conceptual** credit assignment, not gradient descent. On a negative `Reaction`
it traces recent module activity and assigns responsibility adjustments ("who do
we hold responsible, and by how much?"), published as `MapUpdate`s.

### Auto-Regeneration — `src/solaris/modules/auto_regeneration.py`
Reads accumulated backprop adjustments to **rewrite/repair** module parameters,
closing the plasticity loop at the system level.

### Mysterium / Anticipation / Complexity — `src/solaris/modules/`
- **Mysterium**: a `[0,1]` "unknown pressure" that rises with novelty and decays;
  high pressure makes Synthesis more aggressive and loosens Uncertainty.
- **Anticipation**: a first-order transition table over recent meanings; correct
  predictions reward Logos.division, misses raise Mysterium.
- **Complexity**: anti-stagnation — when fracture stays low too long, it injects
  a pair of opposing stimuli (B+ / B−) to restart motion.

### Bus / Lifecycle — `src/solaris/runtime/{bus.py,lifecycle.py}`
A typed async pub/sub `Bus` (modules never call each other directly; a failing
handler does not stop the network) and a birth/death lifecycle.

---

## Concept → module mapping

| Solaris_Ai concept | Reference module | Solaris-AI-NN module | Relationship (no duplication) |
|---|---|---|---|
| Signal vocabulary (spine + side streams) | `runtime/signals.py` | `signals/canonical.py` | Re-expressed as self-contained, field-compatible dataclasses. Not imported. |
| Typed pub/sub Bus | `runtime/bus.py` | `runtime/experiment_loop.py` | NN uses a single in-process loop, not a bus; the loop is the seam where a real Bus could drive it. |
| AION/Impulse heartbeat + absence | `core/aion_impulse.py` | `runtime/experiment_loop.py` | Loop emits continuity heartbeats and synthesises escalating absence stimuli after silence. |
| Logos division/union/fracture | `core/logos.py` | `signals/canonical.py::LogosTension` + encoder | `LogosTension.fracture` is consumed as a scalar input feature; NN does not re-run the opposition engine. |
| Inner MAP (self-representation) | `modules/inner_map.py` | `memory/state_memory.py` | State snapshots are the NN analogue of self-state; real MAP coupling is Phase 3. |
| Habit (bias reinforcement) | `modules/habit.py` | `plasticity/habit_reinforcement.py` | Same `[−1,+1]` bias-toward-valence rule, reframed as `(situation, action)` pathway reinforcement that nudges the readout. |
| Synthesis through subtraction | `modules/synthesis.py` | `plasticity/synthesis_pruning.py` | Directly realised: prunes weak readout/habit weights, emits a `SubtractionReport`. Subtraction, not compression. |
| Backpropagation (responsibility) | `modules/backpropagation.py` | `reservoir/online_learning.py` | A literal-but-tiny delta rule on the readout only (no BPTT); local, online credit assignment matching "who / how much". |
| Auto-Regeneration (repair) | `modules/auto_regeneration.py` | `memory/consolidation.py` | Stubbed: consolidation summarises memory; write-back/repair into the substrate is Phase 3. |
| Mysterium (unknown pressure) | `modules/mysterium.py` | `signals/encoding.py` (novelty slot) | Novelty enters the substrate via the encoder; a dedicated NN pressure module is future work. |
| Anticipation (prediction) | `modules/anticipation.py` | `reservoir/` (readout as predictor) | The readout *is* a predictor of expected valence; an explicit transition model is future work. |
| Complexity (anti-stagnation) | `modules/complexity.py` | `runtime/experiment_loop.py` (absence injection) + `exploration` | Absence stimuli and epsilon-greedy exploration play the anti-stagnation role. |

## How Solaris-AI-NN should relate to these (summary)

- **Speak the same language.** Use the identical signal vocabulary so events can
  cross the bridge unchanged.
- **Add substrates, not duplicates.** Where Solaris_Ai *describes* a process
  (habit, synthesis, backprop), Solaris-AI-NN supplies a *learnable mechanism*
  with measurable state.
- **Stay separable.** Each mechanism is its own small module so it can be
  swapped, benchmarked, or eventually mounted into the real Solaris_Ai runtime as
  an optional learning substrate (Phase 7).
- **Never overwrite the reference.** All coupling happens through `bridges/`.
