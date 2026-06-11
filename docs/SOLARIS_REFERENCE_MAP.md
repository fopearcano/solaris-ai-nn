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
| Inner MAP (self-representation) | `modules/inner_map.py` | `inner_map/model.py` + `inner_map/observer.py` | Implemented (Phase 4): a read-only self-model observing the substrate; `memory/state_memory.py` snapshots feed it. See the Inner MAP mapping below. |
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

---

## Compatibility-bridge mapping (Phase 1)

The first compatibility bridge (`bridges/neural_bridge.py`,
`signals/adapters.py`, `reservoir/modulation.py`) makes the table above
concrete. The bridge consumes Solaris_Ai-style signals (by duck typing — no
import of `solaris-ai`), runs them through the substrate, and emits Action/Desire
*suggestions*.

| Solaris_Ai reference (file / concept) | Solaris-AI-NN implementation |
|---|---|
| `runtime/signals.py` | `signals/canonical.py` (+ `signals/adapters.py` `SolarisSignalAdapter` for duck-typed translation) |
| `core/aion_impulse.py` (heartbeat / absence) | `experiments/absence_stimulus_bridge.py` (synthesised "I exist!" stimuli keep the reservoir alive in silence) |
| `core/logos.py` (division / union / fracture) | `reservoir/modulation.py` (`LogosModulator`: fracture→input gain, union→noise, division→confidence) |
| `modules/habit.py` | `plasticity/habit_reinforcement.py` (reinforced via `SolarisNeuralBridge.react`) |
| `modules/synthesis.py` | `plasticity/synthesis_pruning.py` (synthesis through subtraction) |
| `modules/backpropagation.py` | online readout feedback update — `reservoir/online_learning.py` driven by `SolarisNeuralBridge.react` |
| `modules/inner_map.py` | future persistent state coupling — `memory/state_memory.py` + `memory/consolidation.py` (Phase 3) |
| `conscience.py` topology (assembled bus network) | future bus bridge — `bridges/signal_bridge.py` (`inbound`/`outbound`) → live `Bus` subscription (Phase 7) |

### The bridge data path

```
raw Solaris-like signal
        │  SolarisSignalAdapter.to_nn_signal   (dataclass | dict | object)
        ▼
canonical NN Signal
        │  EventEncoder.encode
        ▼
feature vector ──► LogosModulator.apply_to_input (gain + noise from LogosTension)
        │
        ▼
ESN.update → reservoir state ──► LinearReadout → scores
        │                              │  (+ habit bias, epsilon-greedy)
        │                              ▼
        │                    Action / Desire SUGGESTION  (not a decision)
        ▼
Reaction feedback ──► online NLMS update + habit reinforcement
```

Actions/Desires leave the bridge as **suggestions**; Solaris_Ai (or a future I/O
layer) decides whether to commit them.

---

## Inner MAP mapping (Phase 4)

The Inner MAP self-observation layer maps several Solaris_Ai concepts onto
concrete NN modules. As always: re-expressed, never imported; the reference repo
is untouched.

| Solaris_Ai reference (file / concept) | Solaris-AI-NN implementation |
|---|---|
| `modules/inner_map.py` (self-model: facts + boundaries) | `inner_map/model.py` (`InnerMapModel` + section dataclasses) and `inner_map/observer.py` (`InnerMapObserver`, read-only) |
| `modules/dimensional_comparison.py` (knowing one's own edges) | `inner_map/boundaries.py` (`BoundaryRegistry`: hard/soft boundaries + violation checks) |
| `modules/memory_senses.py` (distilling experience) | `memory/trace_memory.py` (episodic trace) + `memory/consolidation.py` (`MemoryConsolidator`: structural/statistical, no LLM/embeddings) |
| `conscience.py` topology (assembled network) | `inner_map/state_graph.py` (`StateGraph` → DOT/Mermaid self-map) |
| `core/aion_impulse.py` absence stimuli | Inner MAP **absence-cycle tracking** — `MemoryConsolidator.absence_cycles` + `MemoryState.recent_absence_count` |
| `modules/habit.py` | Inner MAP **habit state** — `PlasticityState.{habit_pathways, strongest_habits, most_repeated_mappings}` |
| `modules/synthesis.py` (subtraction) | Inner MAP **synthesis/subtraction state** — `PlasticityState.{pruning_count, last_pruning_report, removed_pathway_count, subtraction_ratio}` |
| `modules/mysterium.py` (unknown pressure) | Inner MAP `UnknownState.unknown_pressure` (placeholder) + drift/novelty estimates |

The Inner MAP observes the substrate, persists `inner_map.json` on every
checkpoint, and restores its continuity section across restarts — providing the
inspectable self-model and boundary registry that later self-modification work
will depend on.

---

## Controlled plasticity mapping (Phase 5)

Controlled, safe self-modification (`plasticity/` engine, policy, safety,
rollback, audit) maps several Solaris_Ai concepts onto bounded runtime-parameter
mutation. Re-expressed, never imported; no source-code rewriting.

| Solaris_Ai reference (file / concept) | Solaris-AI-NN implementation |
|---|---|
| `modules/backpropagation.py` (responsibility / "who, how much") | online readout updates (`reservoir/online_learning.py`) **plus** plasticity policy triggers (`plasticity/policy.py`) that react to prediction error |
| `modules/auto_regeneration.py` (rewrite/repair parameters) | controlled runtime parameter mutation — `plasticity/plasticity_engine.py` + `mutation.py` `TargetRegistry` (bounded, validated, logged, rollbackable; **never** source code) |
| `modules/habit.py` | habit-reinforcement plasticity targets — `reinforcement_rate`, `max_habit_weight`, `decay_rate`, and individual `weight:<pattern>|<action>` |
| `modules/synthesis.py` (subtraction) | synthesis pruning targets + `SubtractionReport` — `pruning_threshold`, `pruning_interval`, `max_prune_fraction` |
| `modules/dimensional_comparison.py` (knowing one's edges) | plasticity **safety boundaries** — `plasticity/safety.py` `PlasticitySafetyValidator` + `SAFE_BOUNDS` + hard prohibitions |
| `modules/inner_map.py` (self-state) | plasticity observability — Inner MAP `PlasticityState` (applied/rejected/rollback counts, last steps, mutable parameters, safety status, audit path) |

Plasticity is **off by default**; when enabled it obeys the safety validator,
supports a dry-run mode, persists mutable parameters across restarts, and can
roll back any applied step from the audit log.

---

## Substrate-laboratory mapping (Phase 6)

The substrate lab (`substrates/`) generalises the nervous layer: ESN,
liquid-state, and spiking-recurrent substrates all consume the same Solaris
signal vectors. The conceptual correspondences:

| Solaris_Ai reference (file / concept) | Solaris-AI-NN implementation |
|---|---|
| `core/aion_impulse.py` continuous heartbeat | the substrate **update loop** — every substrate advances on every event/heartbeat via `BaseSubstrate.update`, so the nervous layer never sits still |
| `core/aion_impulse.py` absence Stimulus ("I exist!") | `experiments/spiking_silence.py` — escalating absence stimuli drive the liquid/spiking substrates through silence; the experiment measures that they do not go inert |
| `core/logos.py` LogosTension | substrate **modulation** — `LogosModulator` gain/noise shapes the encoded vector before *any* substrate consumes it (fracture→gain, union→noise, division→confidence) |
| `modules/inner_map.py` | substrate **observability** — `NeuralSubstrateState` now records substrate type, activity rate, drift, spike rate, silence/saturation ratios, and switch history |
| Plasticity (Habit/Synthesis/Auto-Regeneration family) | **safe substrate parameter mutation** — liquid/spiking knobs (threshold, leak, decay, refractory, noise) are registered plasticity targets under hard `SAFE_BOUNDS`; substrate *switching* is a forbidden mutation |
| `modules/dimensional_comparison.py` (knowing one's edges) | substrate **boundary validation** — safety rules: thresholds within numeric bounds, refractory non-negative, recurrent sparsity bounded, state size capped, switches explicit + checkpointed |

The substrates remain *consciousness-inspired mechanisms*: fixed recurrent
cores, an external adaptive readout, and observable metrics — never a claim of
experience.

---

## Sidecar-integration mapping (Phase 7)

The integration layer (`integration/`) is the first real seam to the actual
reference runtime. As ever: duck-typed, optional, never imported as a hard
dependency, and the reference repo is untouched.

| Solaris_Ai reference (file / concept) | Solaris-AI-NN implementation |
|---|---|
| `conscience.py` (the assembled organism) | `integration/conscience_sidecar.py` — `SolarisNNSidecar` **attach point**: probe → attach → observe → suggest → detach; never stimulate/react/death |
| `runtime/bus.py` (typed async pub/sub) | `integration/bus_connector.py` — `SolarisBusConnector`: subscribe_all (async-aware), forward to the bridge, reversible detach |
| `runtime/signals.py` | `signals/adapters.py` + `signals/canonical.py` — observed signals adapt by name/fields; real classes detected via `integration/optional_imports.py` when present |
| `core/logos.py` | `reservoir/modulation.py` — observed `LogosTension` modulates substrate input/confidence exactly as in Phase 1 |
| `modules/inner_map.py` | Inner MAP **integration state** — `InnerMapModel.integration` (attached, observe-only, compatibility level, mirrored/suggestion counts, `action_authority: false`, sidecar health) |
| `modules/io_module.py` (acting on the world) | **action authority remains outside the NN sidecar** — the `SuggestionChannel` emits `committed=False` suggestions only and rejects anything claiming otherwise |
| `modules/language.py` | future: natural-language explanation of suggestions (the `reason` field on `NeuralSuggestion` is the seam where richer explanations will attach) |

Compatibility grading (`integration/compatibility.py`): `unavailable → minimal
→ bus_observable → sidecar_ready → full_test_ready`; the sidecar requires at
least `bus_observable`, plasticity requires `sidecar_ready` to even *propose*
enabling real integration, and observe-only remains the default everywhere.

---

## Embodiment mapping (Phase 8)

The sensorimotor sandbox (`embodiment/`) realises Solaris_Ai's embodiment-facing
principles inside a bounded simulation. As always: concepts re-expressed as
mechanisms; the reference repo untouched; no real-world actuation.

| Solaris_Ai principle / concept | Solaris-AI-NN implementation |
|---|---|
| Sensory Integration principle | `embodiment/sensors.py` — proximity/object/boundary/energy/absence/clock sensors emitting canonical Stimulus/MeaningEvent |
| Embodiment Interface | `embodiment/body.py` (`SimulatedBody`) + `embodiment/grid_world.py` (`GridWorld`) — a body with position/energy in a bounded, deterministic world |
| Reactivity Engine | the sensorimotor loop (`embodiment/simulation_runner.py`): perceive → suggest → safety-validate → act → Reaction → learn, every step |
| Inner MAP | body/world/energy observation — `InnerMapModel.embodiment` (position, energy, exhaustion, actions, boundaries, `action_authority: simulation-only`) |
| Memory–Sensory Interaction | bounded sensor/action histories + feedback valence record (`embodiment/state.py` summaries persisted as `embodiment_state.json`) |
| Action/Reaction concept | `embodiment/effectors.py` (simulated actions only) + `embodiment/feedback.py` (`EmbodimentFeedback` → canonical Reaction with explicit reasons) |
| AION absence Stimulus | `AbsenceSensor` — an empty sensory neighbourhood emits "I sense nothing" (`is_absence=True`); the embodied absence experiment measures the result |

---

## Language-layer mapping (Phase 9)

The internal language layer (`language/`) realises Solaris_Ai's "language as
cross-functional meaning" principle as deterministic, grounded machinery.

| Solaris_Ai reference (file / concept) | Solaris-AI-NN implementation |
|---|---|
| `modules/language.py` (cross-functional meaning) | the whole `language/` package — controlled vocabulary, meaning atoms, explanations, reports; internal structure before any external conversation |
| `runtime/signals.py` | `language/meaning_trace.py` — MeaningAtoms are generated from canonical signals (received / encoded_as / updated / suggested...) |
| `conscience.py` topology (who talks to whom) | `language/causal_trace.py` — `CausalTraceBuilder` reconstructs hedged chains across the module topology; only coded paths carry `caused` |
| `modules/inner_map.py` | `ExplanationContext` — the Inner MAP snapshot is a primary grounding source for explanations, and the Inner MAP records language status back |
| Habit / Synthesis / Backpropagation family | explanation of adaptation — `explain_strongest_habit`, `explain_pruning`, `explain_plasticity` render exactly what those mechanisms recorded |
| Embodiment principle | explanation of sensorimotor feedback — per-step sensor/suggestion/safety/result/reaction explanations in the simulation runner |

---

## World-model mapping (Phase 15)

The world model (`world_model/`) realises Solaris_Ai's "cognition maps
stimuli to meaning and an Inner MAP" as a minimal, inspectable symbolic
graph that grows from experience.

| Solaris_Ai reference (file / concept) | Solaris-AI-NN implementation |
|---|---|
| `modules/cognition.py` (stimuli -> meaning mapping) | `world_model/builder.py` (`WorldModelBuilder`) + the five extractors (`world_model/extractors.py`) — recorded events become typed nodes and hedged relations |
| `modules/memory_senses.py` (memory-sense interaction) | graph evidence from trace memory — `update_from_trace` turns the chronological trace into precedence chains, associations, and `causes_candidate` edges with evidence refs |
| `modules/inner_map.py` (self/world representation) | `InnerMapModel.world_model` — the graph summary (counts, strongest association, top causal candidate, unknowns, contexts) is part of the self-representation |
| `modules/anticipation.py` | `world_model/prediction.py` (`WorldModelPredictor`) — graph-count predictions feed the existing `latent/anticipation.py` tracker as priors and are scored honestly |
| `modules/mysterium.py` (pull of the unknown) | `unknown` nodes with `mysterium` markers + high-Mysterium graph areas; prediction misses raise unknown pressure through the shared `MysteriumTracker` |
| `modules/synthesis.py` (synthesis through subtraction) | `world_model/pruning.py` (`GraphSynthesisPruner`) — weak/redundant graph structure is proposed for subtraction, dry-run by default, evidence preserved, reversible |
| `modules/language.py` (meaning expressed) | `world_model/query.py` + report builder — six fixed queries answered with cautious vocabulary ("observed association", "candidate causal relation"), ClaimGuard-scanned |

---

## Homeostasis mapping (Phase 16)

The homeostasis layer (`homeostasis/`) realises Solaris_Ai's "Will = Need"
as bounded, observable drive regulation.

| Solaris_Ai reference (file / concept) | Solaris-AI-NN implementation |
|---|---|
| "Will = Need" | `homeostasis/needs.py` (`NeedEstimator`) — fourteen need types as pressure estimates with intensity, urgency, sources, and evidence; never commands |
| `Stimulus → Push → Desire → Action` | `homeostasis/desire_synthesis.py` (`DesireSynthesisEngine`) — need/drive pressure becomes ranked candidates that map to the canonical `Desire` signal and bias (never commit) bridge suggestions |
| `modules/auto_determination.py` (Being/Not-Being) | `homeostasis/auto_determination.py` (`AutoDeterminationEngine`) — two bounded pressures from operational facts; implication is a recommendation the ops watchdog may act on |
| `modules/ego.py` / Inner MAP (self-continuity) | the continuity variable group (heartbeat/checkpoint freshness, restart stability, operational health) + `InnerMapModel.homeostasis` |
| `modules/mysterium.py` (pull of the unknown) | novelty/unknown variable group — Mysterium pressure and prediction misses become `reduce_uncertainty` need pressure |
| `modules/complexity.py` | complexity pressure feeds `increase_exploration` / `increase_stabilization` needs and the exploration/stabilization drives |
| `modules/io_module.py` (actions committed) | formal `DesireCandidate` objects with `committed=False` semantics — the bridge suggests, Solaris_Ai (or the simulation) decides |

---

## Executive function mapping (Phase 17)

The executive layer (`executive/`) realises Solaris_Ai's Desire → Action
transition as bounded, inspectable arbitration — selection among
suggestions, never agency.

| Solaris_Ai reference (file / concept) | Solaris-AI-NN implementation |
|---|---|
| `Stimulus → Push → Desire → Action` (the Desire → Action step) | `executive/coordinator.py` (`ExecutiveLayer`) — Desire candidates queue, are inhibited with reasons, scored across fourteen visible components, and one *suggestion* is selected |
| `modules/io_module.py` (actions committed) | `executive/action_candidates.py` — `ActionCandidate` with four executable scopes and `committed=False` enforced at construction; commitment stays with Solaris_Ai / the simulation |
| Conflict between desires | `executive/desire_queue.py` + `executive/arbitration.py` — deterministic priority ordering and penalty-dominant scoring; `executive/inhibition.py` suppresses with rule, family, and reason across five families |
| `modules/anticipation.py` (expectation before action) | `executive/prospection.py` (`ProspectionEngine`) — bounded simulated consequence estimates with confidence and evidence basis; "unknown" without evidence, never invented |
| Planning as imagined sequence | `executive/planner.py` (`ShortHorizonPlanner`) — ≤3-step (hard max 5) suggestion-only plans evaluated in simulation; long-horizon autonomous planning is structurally refused |
| `modules/conscience.py` (modes of operation) | `executive/policy.py` (`ExecutivePolicy`) — six modes forced by ops status; emergency cannot be self-cleared (`can_override_emergency_stop()` is `False`) |
| `modules/inner_map.py` (self-observation) | `InnerMapModel.executive` + ten executive state-graph nodes — mode, focus, queue, selection, inhibitions, and decision counts are part of the self-representation |
| Working attention / focus | `executive/working_memory.py` + `executive/attention.py` — bounded TTL context and rule-based prioritization, explicitly not awareness |
| `modules/language.py` (meaning expressed) | `executive/reports.py` — full score tables, inhibition ledgers, and seven fixed queries in safe vocabulary ("the arbitrator selected…"), ClaimGuard-scanned |

---

## Ego mapping (Phase 18)

The ego layer (`ego/`) realises Solaris_Ai's Ego — a necessary forced
construct from continuous I/O and differentiation — as an explicit,
operational boundary and identity model. No consciousness, personhood, or
metaphysical self is claimed.

| Solaris_Ai reference (file / concept) | Solaris-AI-NN implementation |
|---|---|
| `modules/ego.py` (the forced self-construct) | `ego/self_model.py` (`SelfModel`) + `ego/identity.py` (`IdentityState`) + `ego/perspective.py` (`PerspectiveTracker`) — anchors, runtime continuity, recorded operating modes |
| `modules/dimensional_comparison.py` | `ego/dimensional_comparison.py` (`DimensionalComparator`) — six fixed axes (temporal, scope, authority, evidence, certainty, risk) with deterministic distances and explained differences |
| Inner MAP (self/world representation) | `InnerMapModel.ego` + ten ego state-graph nodes — identity continuity, perspective, boundary status, and classification counts as observed self-state |
| `modules/mysterium.py` / `modules/anticipation.py` (uncertainty) | reported identity uncertainty, unknown attribution as an honest category, and context-driven perspective shifts with recorded reasons |
| IO/Action (commitment) | `ego/boundaries.py` action-authority and suggestion boundaries — hard rules that no suggestion becomes a committed action and no real-world actuation exists |
| `modules/language.py` (meaning expressed) | `ego/self_report.py` (ClaimGuard + identity-claim scanned reports, eight safe-vocabulary queries) + `ego/narrative_trace.py` (templated, evidence-backed continuity story; no first-person claims) |
| Ego boundary (self vs not-self) | `ego/boundaries.py` (`BoundaryRegistry`) — sixteen boundaries with recorded crossings/violations; `ego/ownership.py` (`OwnershipAttributor`) keeps stream, operator, sidecar, replay, and counterfactual sources straight |
| Embodiment principle (the body in the world) | `ego/body_schema.py` (`BodySchema`) — a simulated body declared simulated, with `simulation_only` action authority and physical embodiment explicitly absent |
