# Architecture

Solaris-AI-NN is a thin, transparent neural substrate wrapped around the
Solaris_Ai conceptual spine. This document explains each layer and how an event
flows through it. Nothing here is conscious; read every name as
*consciousness-inspired*, and treat each concept as a concrete software object,
metric, or experiment.

## 1. The Solaris_Ai conceptual spine (preserved)

Solaris_Ai's canonical chain is preserved verbatim as the vocabulary of this
repo (`solaris_ai_nn/signals/canonical.py`):

```
Stimulus → Push → Desire → Action          (then a Reaction feeds back)
```

with side streams:

```
MeaningEvent   MapUpdate   LogosTension   Reaction
```

- **Stimulus** — sensory or internal input; `is_absence` carries the Subtraction
  Principle (absence of expected input is itself meaningful).
- **Push** — continuous motivational force (the AION/Impulse heartbeat).
- **Desire** — a proposed action with motivation + confidence.
- **Action** — the committed behavioural unit.
- **Reaction** — the consequence, scored with a valence in `[-1, +1]`.
- **LogosTension** — `division` (rational/data-present) vs `union`
  (irrational/data-absent), with `fracture = |division − union|`.

These are plain dataclasses, field-compatible with the reference repo, but **not
imported** from it — the repo is self-contained for now.

## 2. The Solaris-AI-NN neural substrate

```
          ┌─────────────────────────────────────────────────────────┐
 Stimulus │  EventEncoder → ESN reservoir → LinearReadout → Action   │ Reaction
 ───────► │      (vector)      (state)       (scores)               │ ◄────────
          │                         ▲            │                    │
          │        habit bias ──────┘            ▼                    │
          │                              online (NLMS) update         │
          │   habit reinforcement   ◄── valence feedback ──►  synthesis pruning
          └─────────────────────────────────────────────────────────┘
                              telemetry + memory throughout
```

The only trainable parameters are in the linear readout. The reservoir is fixed.
There is no backpropagation through time.

## 3. Event → vector encoding

`signals/encoding.py` turns any signal into a fixed-length float vector:

| Block | Slots | Meaning |
|-------|-------|---------|
| signal-kind one-hot | `len(KINDS)` = 8 | which signal type |
| scalar slots | 4 | intensity, valence, novelty, fracture |
| payload category one-hot | `PAYLOAD_BUCKETS` = 16 | dictionary slot (known words) + hash fallback |
| temporal slots | 2 | heartbeat flag, normalised time delta |

This is *event-continuity* encoding, **not** language understanding. A small
dictionary gives known payloads distinct, collision-free slots (a pure hash into
a few buckets collides too readily); unknown payloads hash into the remaining
buckets.

## 4. Reservoir state as a temporal "nervous" substrate

`reservoir/esn.py` is a leaky-integrator Echo State Network:

- **sparse recurrent matrix** `W` (most entries zero),
- **spectral-radius normalisation** toward the Echo State Property (estimated by
  power iteration — no eigensolver, no NumPy),
- **dense input projection** `W_in`,
- **leaky update**: `x' = (1 − leak)·x + leak·tanh(W_in·u + W·x)`.

The state `x` is a fading echo of the entire event history. It is the substrate's
"nervous state": bounded, continuous, deterministic given a seed, and cheap to
advance one step. The readout sees `features = state ⊕ [1.0]` (a bias term).

## 5. Readout as action tendency

`reservoir/readout.py` is a linear map from features to one **score per action**.
The score is interpreted as the *expected reaction valence* of taking that action
in the current context. The loop chooses with **epsilon-greedy** selection
(`argmax` of scores + habit bias, with occasional exploration) so that unvalued
actions can be discovered.

`reservoir/online_learning.py` trains it with a reward-modulated **normalized
LMS** delta rule, updating only the chosen action's row toward the observed
valence:

```
error = valence − score[chosen]
W[chosen] += (lr · error / (eps + ‖features‖²)) · features
```

Normalisation by `‖features‖²` is what keeps learning stable on the reservoir's
many correlated features (plain LMS diverges as dimensionality grows). This is
the mechanism behind the project's bet: *long-running weak adaptation > expensive
one-shot intelligence*.

## 6. Habit reinforcement

`plasticity/habit_reinforcement.py` mirrors Solaris_Ai's Habit: per-`(situation,
action)` bias scalars in `[-1, +1]` move toward observed valence
(`new = clamp(old + lr·valence, −1, +1)`). The biases lightly tilt action
selection toward repeatedly-rewarded pathways **without** retraining the
reservoir or readout — a cheap, separable second form of plasticity. "Situation"
is a coarse pattern key from the encoder, so habits reinforce *kinds of
situations*, not unique events.

## 7. Synthesis / pruning (subtraction, not compression)

`plasticity/synthesis_pruning.py` realises Solaris_Ai's explicit principle that
**synthesis proceeds by subtraction**. Periodically it removes weak/unused
pathways — zeroing low-magnitude readout weights and forgetting low-magnitude
habits — and returns a **`SubtractionReport`** logging *what* was removed and
*why*. The substrate is defined as much by what it has let go of as by what it
keeps. `plasticity/drift.py` separately measures how much the readout weights
move over time (plasticity without runaway change).

## 8. Memory trace

`memory/` keeps the substrate's episodic trail without a database:

- `trace_memory.py` — chronological event / action / reaction records (optionally
  mirrored to JSONL).
- `state_memory.py` — periodic reservoir-state snapshots; exposes total state
  drift over time.
- `consolidation.py` — a **stub** that summarises memory; write-back into the
  substrate is future work (Phase 3).

## 9. The adaptive event loop

`runtime/experiment_loop.py` ties it together. Each `step()`:

1. emits a continuity **heartbeat** (echoing AION/Impulse);
2. takes the next external **Stimulus**, or — after `silence_steps` of silence —
   synthesises an escalating **absence** Stimulus ("I exist!");
3. **encodes** the event and advances the **reservoir**;
4. forms a **Desire** (preferred action + confidence), biased by **habit**, and
   commits an **Action** (epsilon-greedy);
5. on **Reaction** feedback, applies the **online update** and **reinforces the
   habit**;
6. periodically runs **synthesis** and snapshots **memory**;
7. records **telemetry** throughout.

`run(max_steps)` is bounded and required (never infinite by default).
`run_until(stop_predicate, safety_limit=…)` expresses the system's continuous,
long-running nature without ever defaulting to a truly unbounded loop.

## 10. Telemetry

`runtime/telemetry.py` exposes the observable health of a run: steps, heartbeats,
event count, reservoir/readout update counts, average and recent prediction
error, habit weight + change, pruning passes/count, memory trace length, and wall
-clock duration. If you cannot see a concept in the telemetry, it is not real
here.

## 11. Solaris compatibility bridge

`bridges/neural_bridge.py` (`SolarisNeuralBridge`) is the first concrete
compatibility layer between Solaris_Ai's signal ecology and the neural substrate.
It is the answer to "how does a Solaris_Ai signal become learning, and how does
learning become a Solaris_Ai suggestion?"

**Why the NN layer is not a replacement for Solaris_Ai.** Solaris_Ai is the
conceptual system — the modular pub/sub network with AION, Logos, Inner MAP,
Habit, Synthesis, and the rest. Solaris-AI-NN sits *beside/underneath* it as an
adaptive substrate. The bridge consumes the same signals and emits *tendencies*,
but it does not own the signal ecology and it does not decide. Solaris_Ai (or a
future I/O / integration layer) remains the system; the NN layer is a learning
organ it can consult.

**How Solaris signals become vectors.** `SolarisSignalAdapter` accepts any of
three shapes — native NN dataclasses, dicts, or attribute-bearing Solaris_Ai
objects — entirely by duck typing (no import of `solaris-ai`). It resolves the
signal type (explicit `kind`/`type`, class name, or field-based inference) and
rebuilds a canonical NN signal, filling missing optional fields with defaults
and preserving `is_absence`. The `EventEncoder` then turns that signal into a
fixed-length `list[float]` (kind one-hot; intensity / valence / novelty /
division / union / fracture / is_absence / time_delta; heartbeat; payload and
origin one-hots). This is event-continuity encoding, not language understanding.

**How reservoir state acts as a low-compute temporal substrate.** Each adapted,
encoded signal advances the fixed ESN one cheap step. The reservoir state is a
fading echo of the whole signal history — the bridge's continuous "nervous"
state — from which the linear readout reads an action tendency. Only the readout
learns (online NLMS from `Reaction` feedback); the recurrence is never trained.

**How LogosTension modulates the reservoir/readout.** When the bridge receives a
`LogosTension`, it stores it and `LogosModulator` (`reservoir/modulation.py`)
modulates subsequent processing — a plain gain/noise mechanism, nothing mystical:

- **high fracture → larger input gain** (`gain = 1 + k·fracture`): conflicting
  pulls make the substrate react more strongly to the current event;
- **high union → more exploratory input noise**: data-absence widens exploration;
- **high division → steadier, more confident readout** (union lowers confidence):
  rational grounding raises confidence in the suggested tendency.

Modulation is the identity when no LogosTension has been seen, so it is always
safe to apply.

**Why Actions are suggestions, not autonomous decisions.** `process()` returns a
tendency dict and `suggest_action()` / `suggest_desire()` expose proposals; the
bridge never commits behaviour. This is a deliberate boundary: the NN layer
proposes adaptive tendencies, and Solaris_Ai's I/O module or the future
integration layer decides whether to accept them. The substrate informs the
system; it does not seize it.

The bridge's lifecycle per signal: `to_nn_signal` → `encode` → `LogosModulator`
→ `ESN.update` → readout tendency (+ habit bias, epsilon-greedy) → return
suggestion; and on feedback, `react()` runs the online update + habit
reinforcement. `snapshot()` exposes current bridge state and telemetry.

## 12. Future bridge to the live Solaris_Ai Bus

`signals/adapters.py` also handles dataclass↔dict conversion, and
`bridges/signal_bridge.py` holds the low-level inbound/outbound dict helpers that
will eventually let `SolarisNeuralBridge` subscribe to a live Solaris_Ai `Bus`,
translate inbound signals, drive the substrate, and translate suggestions back
out — still without importing the reference repo. `bridges/solaris_reference.py`
records, in code, which reference module inspired each NN module. See ROADMAP
Phases 1 and 7.

## 13. Continuity, death, and persistence

Solaris_Ai is built around *continuous operation*. For the NN substrate to be a
faithful experimental partner, it must be able to run for a long time, stop, and
resume — and it must be honest about the gaps. This is the Phase-2 machinery, in
`runtime/persistence.py`, `runtime/lifecycle.py`, and `runtime/continuous_runner.py`.

**Why continuity is central.** The interesting behaviour of a low-compute,
continually-learning substrate is not any single step but *what it becomes after
running for a long time* under a stream of events. That only matters if the
substrate's evolving state can be carried forward — across checkpoints and across
process restarts — rather than reset on every launch.

**Why death is a first-class event.** A process ending is not a neutral
non-event; it is a discontinuity in the substrate's life. We model it explicitly:
`RuntimeLifecycle` has `born → running → (sleeping/checkpointing) → dying → dead`
states, and every shutdown is recorded as a `graceful_death` (clean) or inferred
as an `unexpected_death_detected` (the previous manifest never recorded a graceful
shutdown). Treating death as data is what makes restart analysable.

**How restart differs from uninterrupted continuity.** Within one process, the
reservoir state flows unbroken from step to step. Across a restart, the substrate
is *reconstructed*: the runner rebuilds the bridge with the saved seed (so the
fixed reservoir matrices are regenerated identically), then restores the evolving
reservoir state vector, the learned readout weights, and the habit weights from
`latest_checkpoint.json`. Lifetime step count and restart count accumulate via the
manifest. Continuity is therefore *recovered*, not *unbroken* — and the difference
is logged.

**What a brain-death gap means operationally.** On startup, the runner compares
the wall-clock time now against the `last_heartbeat_ts` persisted by the previous
session and logs a `brain_death_gap` with that duration. It is simply: *how long
was this brain not running?* It carries no mystical weight — it is a measurable
interruption interval, useful for reasoning about soak-test continuity and for
distinguishing a quick restart from a long outage.

**What state is persisted.** Under a per-brain `state_dir`:

- `manifest.json` — identity (run id), lifetime step count, restart count, last
  heartbeat timestamp, last-graceful-shutdown flag, seed.
- `latest_checkpoint.json` — reservoir state vector, readout weights + labels,
  habit weights/counts, synthesis/pruning history, telemetry counters, step ids.
- `telemetry.json` — the latest telemetry snapshot.
- `continuity_log.jsonl` — append-only birth/heartbeat/checkpoint/death/restart/
  brain-death-gap/soak/reaction/synthesis/habit events.
- `trace_events.jsonl` — append-only, replayable input-signal trace
  (`runtime/replay.py` feeds it back into a fresh bridge for reproducibility).

State is plain JSON/JSONL — fully inspectable, no database. Reservoir matrices
are *not* stored (regenerated from the seed); only the evolving state is.

**What is deliberately not persisted yet.** The reservoir's random matrices
(reconstructed from the seed, by design); the rolling prediction-error window
(only cumulative counters survive a restart); any Inner-MAP-style consolidated
self-model (Phase 3); and binary `.npz` arrays (reserved for a future
NumPy-backed reservoir backend — JSON is used now for inspectability and zero
dependencies). Continuity mode can run unbounded only with an explicit
`continuous=True`; everything else is bounded by steps and/or duration.

## 14. Inner MAP as self-observation layer

The Inner MAP (`inner_map/`) is Solaris-AI-NN's structured self-model. It mirrors
Solaris_Ai's Inner MAP concept: a running, inspectable answer to *what is the
system right now?* It is the Phase-3/4 self-observation layer.

**It does not make the system conscious.** The Inner MAP is self-*observation*,
not self-awareness. Every field is a concrete, measured property of the
substrate. There is no introspective "experience" here — only a JSON document of
metrics, counts, and tendencies. The vocabulary is consciousness-*inspired*; the
content is telemetry.

**It is a structured self-model.** `inner_map/model.py` defines plain dataclasses
for each section: identity, continuity (B), neural substrate (C), memory (D),
plasticity = habit + synthesis (E/F), boundaries (G), tendencies (H), and
unknown/drift (I), plus a `modules` inventory ("what exists?"). The top-level
`InnerMapModel` round-trips to/from JSON.

**It observes the neural substrate.** `inner_map/observer.py`'s
`InnerMapObserver` is strictly read-only. It inspects a `SolarisNeuralBridge`, a
`ContinuousRunner`, telemetry, memory, habit, and synthesis, and assembles an
`InnerMapModel`. It never calls anything that advances or mutates the substrate —
a test asserts the bridge's reservoir state, weights, and step count are
unchanged by observation. This matches Solaris_Ai's Inner MAP being a passive
listener.

**What it tracks.** Reservoir size/state-norm/sparsity, readout output size and
weight norm, prediction confidence and average error; trace length, dominant
recent signal type, absence-stimulus and reaction counts, and
structurally-consolidated summaries (`memory/consolidation.py`'s
`MemoryConsolidator` — counting only, no LLM/embeddings); habit pathways and
strongest mappings; synthesis pruning count, last report, and *subtraction
ratio*; the current suggested Desire/Action tendency (a suggestion, never a
commitment); operational **boundaries** (`inner_map/boundaries.py`); and
unknown/drift estimates (state drift, novelty, unexplained error, and a
Mysterium-compatible `unknown_pressure` placeholder). `inner_map/state_graph.py`
exports the component topology as DOT or Mermaid — a dependency-free visual
self-map.

**It is persisted across restarts.** The `ContinuousRunner` holds an
`InnerMapObserver`, updates it every `inner_map_update_interval_steps`, and writes
`inner_map.json` on every checkpoint via the `PersistenceManager`. After a
restart the rebuilt model reflects the accumulated lifetime steps and restart
count — the self-model's continuity section survives the gap.

**Why it is required before later work.** Self-rewriting and richer plasticity
(future phases) are only safe and analysable if the system already has a
faithful, inspectable model of its own state and a registry of the boundaries it
must not cross (CPU-only, no heavy ML, no autonomous file deletion or source
rewriting, no unbounded runs unless requested, and — crucially — *no autonomous
action commitment*). The Inner MAP and `BoundaryRegistry` provide exactly that
foundation: observe and constrain first, adapt second.

## 15. Controlled plasticity and safe self-modification

The plasticity controller (`plasticity/`, Prompt 5) lets the substrate modify its
own **runtime parameters** over time. It is off by default and, when on, is safe,
observable, bounded, and reversible.

**It modifies runtime parameters, not source code.** Plasticity tunes things like
the readout learning rate, reservoir leak/spectral radius/input gain, habit
reinforcement rate and individual habit weights, synthesis pruning threshold, and
exploration/stabilization tendencies. It never edits Python files, deletes files,
installs dependencies, touches Git, or runs unbounded — those are hard
prohibitions enforced by the safety validator, not conventions.

**Every mutation is proposed, validated, logged, and rollbackable.** The flow per
step:

1. **Policy** (`policy.py`) reads telemetry, prediction error, Logos state, habit
   stats, drift, and continuity, and *proposes* bounded changes via simple,
   explicit rules (raise the learning rate under persistent error; lower it and
   raise stabilization when error is low and stable; strengthen a
   repeatedly-rewarded habit; prune unused pathways; explore more under high
   Logos fracture; etc.). No black-box meta-learning.
2. **Safety validator** (`safety.py`) checks every proposal: numeric bounds
   (e.g. spectral radius 0.1–1.5, learning rate 1e-4–1.0), and hard invariants —
   no source-code edits, no disabling persistence/continuity-logging/boundaries,
   no autonomous action authority, no auto-`continuous`, no writes outside the
   state dir, and no reservoir-size change during an active run.
3. **Engine** (`plasticity_engine.py`) applies safe steps through the
   `TargetRegistry` (the only thing that writes live parameters), rejects unsafe
   ones with an explanation, and audits **every** proposal, rejection,
   application, and rollback to `plasticity_audit.jsonl`.
4. **Rollback** (`rollback.py`) stores each applied step's previous value, can
   restore it through the same registry, and *verifies* the parameter returned to
   its old value. Unknown step ids fail gracefully. History is rebuildable from
   the audit log, so rollback works even in a fresh process.

**Habit strengthens pathways; synthesis removes weak ones.** Plasticity does not
replace these substrates — it tunes them. Habit reinforcement still moves
`(situation, action)` biases toward reward; synthesis still subtracts weak
readout/habit weights (now bounded by `max_prune_fraction`). The policy decides
*when* to push each lever based on telemetry and the Inner MAP.

**The policy decides from telemetry and the Inner MAP; the validator enforces
boundaries; rollback protects continuity.** Plasticity is integrated into the
`ContinuousRunner` behind `enable_plasticity` (default **False**),
`plasticity_interval_steps`, and `plasticity_dry_run` (propose + log, apply
nothing). Current mutable parameter values are saved in each checkpoint and
restored on restart, so plasticity effects are durable; the Inner MAP exposes
applied/rejected/rollback counts, the last steps, the current mutable parameters,
and the audit path. Because every change is bounded, logged, and reversible, the
system can adapt itself without ever crossing a safety boundary — and a single
command (`--rollback-last`) undoes the most recent change.

## 16. Multiple low-compute neural substrates

The substrate laboratory (`substrates/`, Prompt 6) detaches Solaris-AI-NN from
any single neural mechanism. The system is now a *lab bench*: different
continuous, event-driven, low-compute "nervous substrates" run under the exact
same Solaris signal ecology and are compared with the same metrics.

**Why the ESN is only the first baseline.** The Echo State Network was the
right starting point — cheap, transparent, online-trainable — but it is one
temporal character among several: a smooth, dense, fading analog echo. The
project's question ("what does a low-compute substrate become under a long
stream of Solaris signals?") deserves more than one answer. `EchoStateSubstrate`
*wraps* the existing list-based ESN without duplicating it, so the baseline's
numerics (and every Prompt 1–5 result) are unchanged.

**What the Liquid-State-style substrate adds.** `LiquidStateSubstrate` gives
each unit a leaky membrane potential; threshold crossings emit spike-like events
that soft-reset the membrane, trigger a refractory pause, and feed an
exponentially fading **liquid trace** — the analog state the readout sees. It
trades the ESN's smooth echo for event-driven, thresholded dynamics with
explicit spike counts.

**What the spiking recurrent substrate adds.** `SpikingRecurrentSubstrate` goes
to the discrete extreme: its state is the **instantaneous binary spike vector**
(leaky integrate-and-fire inspired: decay, threshold, hard reset, refractory
period, optional seeded noise). Maximally sparse, maximally event-like — and on
the toy worlds its sparse binary features happen to make the NLMS readout
converge strikingly fast.

**Why none of these are trained like large neural networks.** No substrate
trains its recurrent core — no backpropagation through time, no gradients, no
surrogate-gradient spiking tricks. The recurrence is fixed at construction
(deterministic seed, sparse connectivity, row-normalised gain). **The readout
remains the only adaptive layer**, updated online (NLMS) from Reaction valence,
exactly as before. That is the project's thesis applied consistently: cheap,
weak, continuous adaptation on top of a fixed temporal substrate.

**Common interface, registry, and metrics.** Every substrate implements
`BaseSubstrate` (`update / reset / get_state / set_state / snapshot /
save_npz / load_npz / metrics`) and is created by name through
`SubstrateRegistry` (`esn`, `liquid_state`, `spiking_recurrent`). Shared metrics
(`substrates/metrics.py`: norm, sparsity, activity rate, drift, entropy-like
evenness, saturation/silence ratios, trace similarity) flow into the bridge
snapshot and the Inner MAP, which now records substrate type, activity, drift,
spike rate, silence/saturation ratios, and switch history — the substrate is
part of the system's observable "nervous layer".

**Why substrate switching is explicit and safety-bound.** Swapping the nervous
substrate is the most invasive runtime change possible, so it can never happen
through plasticity: `substrate_name`-style parameters are on the safety
validator's forbidden list, and `SubstrateSwitcher.switch` raises unless called
with `explicit=True`. A switch checkpoints the old substrate **before** anything
changes (state is never discarded), verifies input compatibility, transfers
state only when dimensions match (safe zero start otherwise), checkpoints the
new substrate after, records the event for the Inner MAP, and supports
`rollback_switch` back to the saved checkpoint. Substrate *parameters*
(threshold, leak, refractory period, noise) remain plasticity-tunable within
hard numeric bounds — thresholds stay sane, refractory periods stay
non-negative, recurrent sparsity stays bounded, and state size can never explode
past the configured maximum.

**Persistence.** `PersistenceManager.save_substrate` writes
`substrate_state.npz` (full fidelity: trace + membranes + refractory counters)
plus `substrate_manifest.json` (name, config, sizes, seed, last saved step); the
runner saves both at every checkpoint and restores them on restart. The original
ESN-in-JSON checkpoint path keeps working unchanged. NumPy enters the project
here — the place dense vector math and binary array persistence were always
slated to earn it.

## 17. Solaris_Ai sidecar integration

The integration layer (`integration/`, Prompt 7) is the first real seam to the
actual `fopearcano/solaris-ai` runtime — built **observe-first** and entirely
optional.

**Solaris_Ai remains the primary organism/runtime.** The Conscience, its Bus,
its modules, and its lifecycle are untouched. Solaris-AI-NN mounts *beside* it
as `SolarisNNSidecar`: probe the runtime (`SolarisRuntimeProbe`, pure duck
typing — no direct imports), attach to its bus, observe, learn, suggest,
detach. The sidecar never calls `stimulate()`, `react()`, or any death/lifecycle
method on the conscience, never alters its module wiring, and never touches its
source files.

**Integration is observe-first.** The default mode is `observe_only=True`:
signals flow in, nothing flows out. Even with publishing enabled, the only
objects that ever leave are `NeuralSuggestion`s — clearly typed, carrying
`committed=False`, and rejected by the `SuggestionChannel` if anything claims
otherwise. There is no code path that constructs a Solaris `Action` that looks
committed. **Action authority stays with Solaris_Ai**, and the Inner MAP records
`action_authority: false` as an invariant of the integration state.

**Signals are mirrored and encoded.** Every observed signal is adapted to the
canonical NN vocabulary, fed to the substrate, and mirrored (`SignalMirror`)
with its original metadata, the adapted form, and a vector *summary* (norm +
length; full vectors only with explicit opt-in). Reactions teach first
(`bridge.react`) and then flow through as events, so feedback lands on the
suggestion that earned it. The sidecar persists
`integration_state.json` / `suggestions.jsonl` / `mirrored_signals.jsonl`.

**Optionality is structural.** `integration/optional_imports.py` is the only
place that ever imports `solaris`, always inside guarded, per-call imports with
recorded error messages — the entire test suite and every example run without
the real package (a fake Conscience/Bus ships in the observation experiment).
Compatibility is graded (`unavailable → minimal → bus_observable →
sidecar_ready → full_test_ready`) and plasticity may not enable real
integration below `sidecar_ready`; plasticity also cannot mutate Solaris
runtime objects, alter bus subscriptions, flip `observe_only`, or publish
committed actions (hard validator rules).

**Why the sidecar architecture is safer than merging too early.** A merged
integration would entangle an experimental, self-modifying learner with the
conceptual organism before either is proven — every NN bug would become a
Solaris_Ai bug, and rollback would mean surgery. The sidecar keeps a hard
process boundary in the design: one attach point, one suggestion channel, one
observe-only default, and a `detach()` that restores the world to exactly what
it was. Solaris_Ai can ignore the sidecar entirely and lose nothing; it can
consult the suggestions and gain a learner. That asymmetry — all of the option
value, none of the coupling — is the point.

## 18. Embodiment and sensorimotor loop

The embodiment layer (`embodiment/`, Prompt 8) gives the substrate a minimal
**simulated** body and world. Solaris_Ai's architecture presumes continuous
I/O, sensing, reactivity, feedback, and boundaries — not text alone — so the NN
laboratory needs a place where actions have consequences.

**Why a body-like interface, and why simulated first.** Without consequences,
the substrate only ever learns from scripted reactions; with a body in a world,
its own choices generate the feedback it learns from — closing the
`Stimulus → Push → Desire → Action → Reaction` spine end to end. The first body
is simulated because the project's questions (does the loop close? does
feedback shape tendencies? does the body manage its own energy?) are fully
answerable in a 9×7 grid, and because real-world actuation before the safety,
observability, and rollback machinery is proven would invert the project's
entire safety posture.

**Sensors → Stimulus.** `GridWorld` produces raw senses; six sensors
(proximity, object/novelty, boundary, energy, absence, clock) convert them to
canonical `Stimulus`/`MeaningEvent` signals — the *same* vocabulary everything
else speaks. The AbsenceSensor embodies the Subtraction Principle: an empty
neighbourhood is itself a stimulus.

**Suggested Actions → simulated effector commands.** The bridge's suggestion is
wrapped as an `EffectorCommand`, validated by `EmbodimentSafety` (closed action
space, forbidden patterns for anything network/OS/browser/robot-shaped, no
unbounded simulation, no out-of-simulation commitment), and executed by an
effector **exclusively through the GridWorld API**. Blocked actions return
explicit reasons; nothing touches the real world.

**Feedback → Reaction.** `EmbodimentFeedback` grades consequences — closer to
reward (+), collisions (−), touching the unknown (novelty +), needed rest (+),
useless repetition (−) — into canonical `Reaction` events that drive the same
online NLMS + habit learning as every earlier experiment.

**Energy as internal Stimulus.** The `EnergyModel` is a simulated need:
movement costs, rest restores, low energy emits an internal Stimulus, and
exhaustion blocks costly actions (rest stays available). In practice the agent
demonstrably learns to rest when depleted.

**Inner MAP + authority.** The Inner MAP gains an `embodiment` section
(position, energy, exhaustion, available/forbidden actions, last
stimuli/action/reaction, boundaries, nearby objects, safety status) and records
`action_authority: "simulation-only"` — the body acts in its grid and nowhere
else. Plasticity may tune learning knobs from embodiment statistics (failure
rate, collisions) but is hard-blocked from expanding action authority, adding
actions, or disabling embodiment safety.

## 19. Language as cross-module meaning trace

The language layer (`language/`, Prompt 9) gives the system a structured way to
describe what happened inside itself. It is **internal structure before
external conversation** — Solaris_Ai's view of language as cross-functional
meaning, not human speech.

**What it records.** A `MeaningTraceBuilder` converts runtime happenings —
signals received, vectors encoded, substrate updates, readout suggestions,
reactions, habit/synthesis/plasticity events, Inner MAP changes, embodiment
results — into `MeaningAtom`s: subject–predicate–value statements drawn from a
**controlled vocabulary** (13 categories, 16 predicates; anything outside falls
back to `unknown` / the hedged `influenced`). A `CausalTraceBuilder`
reconstructs approximate chains from recorded order: only relations that are
*directly coded* (a Reaction literally triggers the readout update and habit
reinforcement) may carry `caused` at confidence 1.0 — everything else is
`preceded` / `was_associated_with` / `influenced` with confidence below 1.0,
and the builder downgrades any attempt to overclaim.

**Explanation and debugging.** The `ExplanationEngine` renders deterministic
templates over an `ExplanationContext` (bridge/telemetry/Inner-MAP/embodiment/
plasticity snapshots). Every explanation lists the concrete fields it is
`grounded_in`; when data is absent it says **"the system does not know"** and
names the missing piece. A fixed `QueryInterface` (normalized string matching,
eleven queries, no NLP) routes internal questions to the engine. The
`StructuralSummarizer` counts — it never generates — and the report builder
renders JSON/Markdown session reports whose **Limitations and Unknowns**
section is mandatory.

**What it is not.** It does not make the system conscious — an atom is a
record and an explanation is a rendering of records; motivational language
("wanted") is excluded by rule and test. It does not use LLMs: no external
APIs, no transformers, no embeddings (statically verified by test). Every
statement reduces to trace/telemetry/Inner-MAP data, which is exactly what
makes the layer useful for debugging: when the report says "synthesis removed
281 weak pathways", that number came from the pruning history, nowhere else.

**Integration.** The bridge optionally records atoms per processed signal
(`enable_language_trace`); the `ContinuousRunner` adds periodic structural
summaries, persists `meaning_trace.jsonl` / `causal_trace.json` /
`last_explanations.json` on checkpoints and a JSON+Markdown session report on
shutdown (`enable_language`, `report_interval_steps`); the sensorimotor runner
explains each step (sensor reading, suggestion, safety validation, action
result, feedback); and the Inner MAP records language status (atom counts,
dominant categories, unknown statements, queryability) as part of the
self-model.

## 20. Evaluation and reproducibility layer

The evaluation layer (`evaluation/`, Prompt 10) is the measurement harness.
After nine phases of mechanisms, the project needed a way to ask — with
numbers — *is any of this actually improving anything?* before adding more
complexity. Every run now has a manifest; every claim has a metric.

**Why metrics before more complexity.** Adaptive systems invite
self-deception: behaviour drifts, and the builder narrates the drift as
progress. The harness replaces narration with manifests (what exactly was run:
seed, substrate, config, features, bounds), domain metrics, and reproducibility
hashes. Nothing gets called an improvement unless a metric moved.

**Metric domains** (`evaluation/metrics.py`, all deterministic and
zero-safe): continuity (heartbeats, checkpoints, restarts, brain-death gaps),
reactivity (stimuli, suggestions, reactions, latency, response diversity),
adaptation (prediction-error trend, feedback alignment, inversion recovery),
habit (pathways, entropy, stability), synthesis (pruning counts, subtraction
ratio), plasticity (proposed/applied/rejected/rollbacks), substrate (norm,
drift, activity, spike/silence/saturation, energy proxy), embodiment (rewards,
collisions, blocked actions, exhaustion, useful-action ratio), Inner MAP, and
language (atom counts, grounded-explanation ratio, honest unknowns).

**Why there is no consciousness score.** Scores (`evaluation/scoring.py`) are
0–1 *mechanistic proxies* with mandatory explanations — "continuity
performance", "adaptation proxy", "sensorimotor stability" — and `None` with a
reason when data is insufficient. A consciousness score would be a category
error: these numbers measure mechanisms (error trends, ratios, counts), and no
arithmetic over mechanism metrics yields a fact about experience. The scorecard
says so in its own `note` field, permanently.

**Benchmarks compare substrates/features.** Nine registered protocols
(`evaluation/protocols.py`) wrap the existing experiments — absence stimulus,
feedback inversion, reward/danger, restart recovery, replay determinism,
substrate comparison, plasticity dry-run, synthesis pruning, language
grounding — each returning an `ExperimentResult` with metrics, scorecard,
artifacts, and failure findings. `evaluation/comparison.py` groups results by
substrate or feature flags into Markdown tables, and `evaluation/baselines.py`
provides the bar to beat (random ≈0.44, fixed/no-feedback ≈0.31 vs the learning
loop ≈0.81 late accuracy on the toy world — habit ablation collapses to the
floor, which is the ablation telling us habit matters here).

**Replay and reproducibility.** `compute_reproducibility_hash` pins the
configuration; the replay protocol records a trace and replays it into two
identically-seeded fresh bridges (bit-equal state required);
`check_seed_stability` re-runs whole experiments and `compare_runs` diff their
metrics within tolerance, flagging nondeterminism explicitly.

**Failure analysis guides the next step.** `FailureAnalyzer` pattern-checks
results for the known bad endings — frozen substrate, runaway activity, total
silence, blocked-action dominance, missing feedback, plasticity lockout, empty
traces, missing checkpoints, replay mismatch — and emits findings with
severity, probable cause, and a *suggested next debug step*. Diagnosis only;
nothing auto-fixes. The findings are exactly the queue future development
should work through.

## 21. Operations, watchdog, and long-running supervision

The operations layer (`ops/`, Prompt 11) makes continuity *supervisable*. The
project's premise is a system that runs for a long time — which is only safe if
the run can know it is healthy, drift visibly toward failure, checkpoint, stop
well, and resume.

**Continuity requires supervision, and infinite mode is never default.** Every
supervised run starts from an `OperationalRunManifest` that pins mode, safety
mode, bounds, intervals, and features. `continuous_explicit` is refused without
`explicit_continuous_acknowledged=True`; the 24h/30d soak modes are refused
without `soak_acknowledged=True`; bounded mode demands a step or duration
bound. There is no code path to an unacknowledged infinite loop.

**Segmented supervision.** The supervisor splits a bounded run into
health-check-interval segments; each segment is a fresh runner continuing from
the same state directory (the Phase-2 restart machinery makes this exact), and
between segments the full ops loop runs: health check → incident logging →
budget check → watchdog tick → registry update. Existing runners are untouched;
they are simply run in supervised slices.

**How health checks work.** The `HealthMonitor` grades eight domains
(lifecycle, telemetry progress, substrate sanity — finite/no-runaway/no-inert,
persistence writability, memory bounds, plasticity rejection/rollback rates,
embodiment block ratios, language trace size) into ok/warning/critical/unknown.
It is stateful only enough to notice counters that stopped increasing.

**How the watchdog requests safe shutdown.** The `Watchdog` returns decisions
(`continue` / `checkpoint_now` / `warn` / `safe_shutdown` /
`emergency_stop_requested`) from staleness, duration, artifact growth, repeated
criticals, and repeated segment failures. It has no power of its own — it never
touches the process; the supervisor acts on its decisions, and even an
emergency stop goes through `SafeShutdownManager`, which checkpoints, records
the reason, and writes the final health report, Inner MAP snapshot, and session
report. Dying well is part of continuity.

**Checkpoints and incidents preserve the evidence.** Every supervised run
leaves `manifest.json` / `health.jsonl` / `incidents.jsonl` / `status.{json,md}`
/ `shutdown.json` / `artifact_rotation.json` / `final_report.md` under
`.solaris_ai_nn_ops/runs/<run_id>/`, plus an entry in the run registry.
Artifact rotation compresses large JSONL logs (gzip, stdlib) and trims only
rotated archives — strictly inside configured directories, with dry-run, never
touching source files. The `ResourceBudget` keeps runtime, steps, traces,
artifacts, mutations, and atom counts within soft limits, reporting violations
as incidents.

**Read-only, localhost-only status.** The optional `LocalStatusServer`
(stdlib `http.server`, disabled by default) binds exclusively to 127.0.0.1 and
serves JSON snapshots (`/health` `/status` `/manifest` `/latest-report`
`/incidents`). No commands, no writes, no remote access; a busy port degrades
to disabled-with-warning rather than failing the run.

**Operational state feeds Inner MAP.** The supervisor's
`operations_summary()` (mode, health level, watchdog status, budget status,
incident count, shutdown state, rotation, status-server state, soak stage)
lands in `InnerMapModel.operations` — supervision is part of the self-model,
and the failure analyzer consumes ops incidents to produce next-debug-step
findings. Staged soak plans (`SoakPlanBuilder`) document the escalation ladder
from a 5-minute simulated soak to a 30-day soak; plans are documentation and
never auto-launch.

## Governance, operator control, and emergency stop

**Governance is separate from cognition.** Everything in the
`solaris_ai_nn.governance` package is control, not intelligence: it decides
what a run is *allowed* to do, records who approved the risky parts, and
provides the always-available stop — without touching how the substrate
learns. The cognitive layers (bridge, plasticity, language) call into
governance; governance never reaches back into them to make them smarter.

**Policy controls run modes, plasticity, embodiment, sidecar, and reports.**
`GovernancePolicy` evaluates manifests, simulated actions, plasticity steps,
sidecar operations, and generated text against fixed rule categories: bounded
runs are allowed by default while soaks and continuous mode require approval
(and continuous mode also a configured emergency stop); plasticity is off
unless enabled, dry-run is cheap, active mutation needs audit + rollback +
approval, and source rewriting is forbidden absolutely; embodiment is
simulation-only (real-world / network / filesystem effectors are forbidden);
the sidecar may observe freely but publishing needs approval, and committing
Actions or calling lifecycle death is forbidden; long runs need
watchdog/checkpointing/incident logs and the status server stays
localhost-only and read-only. A `PolicyDecision` that "requires approval" is
*denied* until a matching record exists — there is no path that silently
bypasses a human.

**Permissions are deny-by-default; approvals are local research records, not
security.** A `PermissionSet` grants explicit scopes (unknown scopes are
denied); the default set allows bounded/simulation/observe-only/dry-run and
marks active plasticity, long soaks, and outward suggestions as
approval-required. The `ApprovalRegistry` is a plain JSON ledger: a named
human deliberately approves a scope for a reason, optionally time-limited
(approvals expire). There is no authentication and no secrets — it answers
"who allowed what, and why?", not "are you authorized?".

**Risk is named before the run.** `assess_manifest` / `assess_current_state`
produce a `RiskAssessment` whose rules are fixed: prohibited blocks the run,
high requires an approval record, medium requires operator acknowledgement
(`OperatorSession.acknowledge_risk`), low is logged only. The supervisor runs
this gate *before* the first segment; a blocked or unapproved/unacknowledged
configuration never starts.

**Emergency stop is always available.** `EmergencyStop` is invokable
regardless of any permission. It works only through graceful interfaces
(`SafeShutdownManager` / `stop()`), records an incident and governance audit
events, writes a final health snapshot, and never deletes data — and never
touches the process. A sentinel file (`<state_dir>/EMERGENCY_STOP`) gives an
out-of-band path: an operator (or another process) creates it, and the
supervised run requests safe shutdown at the next segment boundary. The
sentinel is cleared only by a deliberate operator action; the evidence stays
in incidents and the audit.

**Unsupported claims are blocked or flagged.** `ClaimGuard` scans every
generated report before save: "the system is conscious / understands / wants /
is alive" is flagged with a grounded replacement ("consciousness-inspired",
"produced a Desire signal", "maintained continuity metrics"). By default the
warning is appended to the report; `on_unsafe="block"` refuses the save
entirely. The project's own reports are written to pass this scan.

**Governance feeds Inner MAP and evaluation.** The supervisor's
`governance_summary()` (policy status, risk level, active permissions,
approval counts, emergency-stop availability/request, last policy violation,
audit path, operator session, claim-guard status, post-run recommendation)
lands in `InnerMapModel.governance` and the state graph (GovernancePolicy,
PermissionSet, ApprovalRegistry, RiskAssessment, EmergencyStop, ClaimGuard,
Runbook, PostRunReview nodes). Evaluation reports carry the governance block,
and the failure analyzer gained detectors for high-risk-without-approval,
emergency-stop-used, unsafe-claim-generated, policy-violation, and
approval-expired. Every supervised run leaves a governance trail under
`.solaris_ai_nn_governance/`: `governance_audit.jsonl`, `approvals.json`,
`operator_session.json`, `risk_assessment.json`, the pre/post-run checklists,
`post_run_review.json`, and `claim_guard_report.json`. `RunbookBuilder`
generates the written operator procedure for each experiment type
(bounded / plasticity / sidecar / sensorimotor / 24h / 30d soak), and
`PostRunReview` recommends what to do next (repeat / extend / reduce scope /
investigate / stop) — a recommendation for a human, never an automatic action.

## Pilot-0 deployment profiles

**Pilot-0 is controlled deployment, not autonomy.** The `pilot/` package is a
harness for running the existing substrate in controlled environments under
everything the previous layers built: a pilot is governed (policy, risk,
approvals, operator acknowledgement), supervised (health, watchdog, incidents,
emergency-stop sentinel), bounded (an unbounded `PilotManifest` cannot even be
constructed without governance approval ids), and accounted for (readiness
report before, registry entry during, ClaimGuard-scanned pilot report after).
Nothing in the pilot layer adds capability — it adds the conditions under
which capability is allowed to run.

**The simulated pilot remains the safest default.** Profile `simulated`
(`PilotProfileType.DEFAULT`) wraps the GridWorld sensorimotor sandbox: fully
internal, nothing external read or touched. The other two profiles must be
chosen deliberately, and `PilotProfileRegistry` refuses to register any
profile that fails to forbid real-world actuation, network calls, OS
commands, browser automation, committed Solaris Actions, source-code writes,
or writes outside approved directories.

**The read-only stream pilot ingests external sensory data without acting.**
Local JSONL/text files — explicitly named by the operator, no globs, no
recursive crawling — are read by the `ReadOnlyStreamIngestor` and validated
line by line against the data contracts: command-shaped payloads, shell-like
instructions, URLs or paths posed as action requests, action-request keys,
binary data, and oversized payloads are rejected, counted, and never
partially trusted. Accepted events become canonical Stimuli through the
stream sensors (`JsonlStreamSensor` / `TextStreamSensor`, plus
`SyntheticHeartbeatSensor` and a `SilenceWindowSensor` that turns stream
pauses into absence Stimuli — the Subtraction Principle at the stream level)
and feed the ordinary `ContinuousRunner`. Input files are never modified;
tailing is bounded by lines and/or duration, always.

**The Solaris sidecar pilot observes only.** Profile
`solaris_sidecar_observe` attaches the Prompt-7 sidecar beside a
Solaris_Ai-like runtime (fake or real) for a bounded observation window:
signals are mirrored, suggestions are produced locally, publishing them
requires a separate approval, and committing Actions or touching the
runtime's lifecycle remains structurally absent.

**Every pilot runs the full stack.** `PilotDeploymentRunner` refuses an
unsafe manifest (`PilotSafetyValidator`: contract intact, bounded-or-approved,
approved output roots, real input files, no forbidden features, no sidecar
action authority), generates a `PilotReadinessReport` across six areas
(governance, operations, evaluation, safety, recovery, documentation — skips
must be explicit), then drives the profile's thin adapter through the
`OperationalSupervisor`, whose own governance gate enforces approvals and
operator risk acknowledgement. The run ends with `input_summary.json`, a
pilot-aware Inner MAP snapshot, a pilot report with a single recommendation
(`repeat_pilot` / `extend_duration` / `reduce_scope` / `investigate_failure`
/ `ready_for_next_stage` — for a human, never acted on), an `artifacts.json`
completeness record, and a `PilotRegistry` entry under
`.solaris_ai_nn_pilots/`. The `pilot_readiness` evaluation protocol runs this
whole loop as a benchmark, and `pilot_metrics` exposes readiness score,
ingestion validity rate, rejection counts, safety blocks, and artifact
completeness.

**Pilot state feeds Inner MAP.** The deployment runner's `pilot_summary()`
(mode active, profile, readiness status, input/ingestion counts, safety
status, incident count, recommendation, report path) lands in
`InnerMapModel.pilot`, and the state graph gains the pilot nodes
(PilotProfile, PilotManifest, PilotSafetyValidator, PilotDeploymentRunner,
PilotReadinessReport, PilotReport, ReadOnlyStreamIngestor, StreamSensor)
with their gating and feeding edges.

## Latent cognition: sleep, replay, anticipation, and Mysterium

**Latent mode is bounded offline processing.** When external input goes
quiet, the runner does not idle: the `latent/` package lets it enter
quiet/sleep/consolidation/replay/dream modes for strictly bounded cycles
(every cycle carries an explicit step bound, hard-capped at 500; there is no
unbounded latent loop). The `SleepWakeController` is the state machine —
every transition is validated, logged with its reason, and recorded; the
`LatentScheduler` decides when (silence thresholds, trace size, unknown
pressure) and refuses outright when health is critical, when governance
disallows latent work, or when a sidecar is actively publishing.

**Sleep means maintenance/consolidation, not human sleep.** A `SleepCycle`
pauses external action (structurally — the loop processes nothing external
during a cycle), keeps the heartbeat ticking, consolidates the trace into
`ConsolidatedSchema` records (the strongest repeated pattern→action
pathways), and lets runaway substrate activity settle. **Dream means
sandboxed replay/counterfactual simulation, not subjective experience.** A
`DreamCycle` replays remembered windows into deterministic sandbox copies of
the bridge (`make_sandbox_bridge`: same seed and config, copied state —
nothing flows back), generates labelled counterfactual variants
(invert valence, remove a stimulus, lengthen silence, change fracture, swap
reward/danger, suppress absence, amplify novelty), and measures how
behaviour diverges. Every dream output is marked `offline=True,
simulated=True`, and the language layer phrases it accordingly: "During
offline replay, the system simulated…" — never "the system dreamed that…".

**Anticipation tracks simple predictions.** The `AnticipationTracker`
predicts the next signal kind, action tendency, valence bucket, absence
probability, and activity trend from frequency/recency statistics (no deep
learning), scores every prediction against what actually happened, and keeps
hits, misses, streaks, rolling accuracy, and a surprise estimate.
**Mysterium is numeric unknown pressure.** The `MysteriumTracker` holds one
number in [0,1] that rises with novelty, miss streaks, unexplained error,
Logos fracture, blocked actions, counterfactual divergence, and replay
mismatches, and falls with successful prediction, stable patterns,
consolidation, and reproduced replays — every change attributed to a named
reason. Nothing mystical is measured. The `ComplexityPressureMonitor` rounds
this out: inertia/chaos/deadlock scores and one bounded suggestion
(exploration, rest, consolidation, replay, or a flag) — suggestions only.

**Latent cycles cannot execute external actions, and latent plasticity
requires governance approval.** The `LatentSafetyValidator` enforces the
hard rules: no external action or sidecar publishing in latent modes, no
unbounded cycles, counterfactual data never treated as real memory, and
production mutation denied unless governance granted
`enable_latent_plasticity` (a new approval-required scope; dry-run scopes
are granted by default). The dream cycle's default is sandbox-only; even
asking for production application is refused without the double gate
(flag + governance). The supervisor watches for stuck latent cycles,
dream-trace overgrowth, and pinned Mysterium (new incident types), and the
five latent benchmark protocols (`latent_replay`, `sleep_consolidation`,
`anticipation`, `mysterium_pressure`, `counterfactual_dream`) verify the
behaviour objectively.

**Latent state feeds Inner MAP.** The coordinator's `summary()` (mode, last
transition, cycle/replay/counterfactual counts, anticipation accuracy,
Mysterium pressure and reasons, complexity reading, schema count, safety
status, report path) lands in `InnerMapModel.latent`; the state graph gains
the ten latent nodes; durable evidence lives under the state dir
(`latent_memory.jsonl`, `dream_traces.jsonl`, `replay_traces.jsonl`,
`consolidated_schemas.json`, `latent_report.{json,md}` — the report is
ClaimGuard-scanned with mandatory limitations).

## World Model and neuro-symbolic memory

**The World Model stores stable symbolic structure extracted from events.**
While the neural substrate reacts continuously, the `world_model/` package
distils what *recurs*: repeated stimuli become `stimulus_pattern` nodes,
GridWorld objects become `object` nodes, actions/reactions become
`produces`/`reinforces`/`inhibits` edges, habits become weighted structure,
contexts become `context` nodes, and the unexplained becomes `unknown`
nodes. It complements the substrate rather than replacing it: the reservoir
holds fast dynamics, the graph holds slow structure.

**It is graph-based and inspectable.** The `KnowledgeGraph` is plain
dictionaries with deterministic ids (same type+label -> same node, same
triple -> same edge, so observation accumulates instead of duplicating) —
no graph database, no vector store, no external library. Every node carries
its observation count, capped confidence, source modules, and metadata;
every edge carries weight, confidence, separate real/offline observation
counts, and bounded evidence references. Exports to JSON, JSONL, DOT, and
Mermaid are stdlib-only, and everything persists under the state dir
(`world_model.json`, `world_model_{nodes,edges}.jsonl`, `world_model.dot`,
`world_model.mmd`, `world_model_report.md`).

**Associations, candidate causal links, contexts, predictions, and
unknowns.** Five extractors feed the graph from existing layers (signals,
embodiment, meaning atoms + causal traces, latent replay — always marked
offline — and validated pilot stream events). The `AssociationLearner`
counts and decays eight kinds of pairwise association; the
`CausalAssociationModel` scores `causes_candidate` edges from temporal
precedence, co-occurrence, feedback, embodied intervention, and (weighted
down, always marked simulated) counterfactual divergence — confidence is
capped and evidence counts are exposed, because nothing here is proven
causation. The `ContextTracker` separates structure by situation (13 named
contexts), and the `WorldModelPredictor` turns graph counts into scoreable
predictions that feed the anticipation tracker and Mysterium — predictions
are data with no execution path, enforced by `WorldModelSafety` (which also
ensures command-shaped stream payloads can never become action nodes).

**It feeds Inner MAP and anticipation.** The builder's
`world_model_summary()` (node/edge counts, strongest association, top
causal candidate, unknown count, high-Mysterium areas, context state,
prediction accuracy, last pruning proposal, evidence ratio) lands in
`InnerMapModel.world_model`; the state graph gains the eleven world-model
nodes; six fixed language queries ("what does the world model know?",
"what is still unknown?", ...) answer with cautious vocabulary — "observed
association", "candidate causal relation", "prediction based on graph
counts" — and every report passes ClaimGuard. **It does not claim
understanding or consciousness**; the limitations say so in every report.

**Pruning follows synthesis-through-subtraction.** The
`GraphSynthesisPruner` proposes removal of weak edges, isolated weak nodes,
and redundant unknown-duplicates; application is dry-run by default,
archives everything it removes (restorable per proposal), preserves
evidence summaries, refuses to touch raw trace evidence, and requires the
approval-gated `enable_world_model_pruning` scope for production
subtraction. Five benchmark protocols (`world_model_build`,
`world_model_prediction`, `world_model_pruning`, `embodied_world_model`,
`pilot_stream_world_model`) keep the behaviour measured.

## Homeostasis, Need, and Auto-Determination

**Will = Need is implemented as a need-pressure model.** Solaris_Ai models
behaviour as Stimulus → Push → Desire → Action and treats Will as Need; the
`homeostasis/` package supplies the missing calculus between stimulus and
desire. Seven groups of normalized variables (continuity, energy, safety,
novelty/Mysterium, memory, social/sidecar, embodiment — raw source values
always preserved in metadata) feed a `NeedEstimator` whose fourteen need
types are *pressure estimates with receipts*: intensity, urgency, source
variables, supporting evidence, possible Desire proposals, and recorded
inhibitions. **Needs are not commands** — structurally, the entire layer is
data with no execution path.

**Drives bias Desire/Action suggestions.** Needs aggregate into ten numeric
drive channels (continuity, energy, safety, curiosity, consolidation,
exploration, stabilization, embodiment, social-observation, governance) with
structural priority bumps so ties never resolve toward curiosity. The
resolver exposes a deterministic 10-channel modulation vector and a
Desire-proposal bias dict; the `DesireSynthesisEngine` turns the surviving
pressure into ranked `DesireCandidate`s that map onto the canonical Solaris
``Desire`` signal and *bias* the neural bridge's suggestions (a small
pre-argmax nudge beside the habit bias). Suppressed candidates stay in the
list with their reasons. Valence is computed alongside as **feedback
polarity, not emotion** — the running sign of reactions, outcomes,
checkpoints, and operator decisions, with attributed evidence.

**Conflicts resolve on a fixed safety-first ladder.** When needs oppose
(curiosity vs safety, reward vs exhaustion, consolidation vs sensing,
publishing vs observe-only, continuity vs a requested stop), the
`ConflictResolver` works the ladder — governance/safety > emergency stop >
continuity > embodiment safety > energy > intensity > exploration — and
records each suppression with its rule and reason. **Governance always
overrides needs**: the safety validator refuses override attempts outright,
desire candidates are deny-by-default against an allowed-proposal list,
real-world shapes are rejected, and the policy layer carries explicit
homeostasis rules (`needs_never_override_governance`,
`needs_never_actuate`, `no_anthropomorphic_claims`).

**Auto-determination is operational Being/Not-Being tension.** Solaris_Ai's
existential opposition becomes two bounded pressures computed from concrete
facts: Being rises with fresh heartbeats, clean checkpoints, restored state,
coherent self-model, and non-negative valence; Not-Being rises with
brain-death gaps, critical incidents, unresolved Mysterium, runaway/inert
substrates, and exhaustion. The implication ladder (continue / rest /
consolidate / request_review / safe_shutdown_recommended / no_action) is
explicitly a *recommendation*: the ops supervisor records it as an incident
and the watchdog keeps all stop authority — the homeostasis monitoring block
in the supervisor contains no `request_shutdown` call, by test.

**Everything is integrated and accounted for.** The `HomeostaticRegulator`
runs deterministically inside the ContinuousRunner and the sensorimotor
runner (off by default), consumes latent summaries (Mysterium, anticipation)
and world-model summaries (unknown ratio, predicted danger, redundancy),
feeds need/drive/desire/conflict structure back into the knowledge graph,
lands in `InnerMapModel.homeostasis` and the state graph (nine nodes),
persists `need_trace.jsonl` / `homeostasis_state.json` /
`auto_determination.json`, answers seven fixed queries in safe vocabulary
("the need estimator assigned high pressure to…", never "the system
wanted…"), and is measured by five benchmark protocols. **No free will or
consciousness claim is made** — the reports say so in their mandatory
limitations, and ClaimGuard plus an anthropomorphism check scan every save.

## Executive function, arbitration, and prospective planning

**The Desire → Action transition is an inspectable arbitration, not
agency.** The `executive/` package sits between the homeostatic Desire
candidates and the bridge's Action suggestion. Competing desires enter a
deterministic `DesireQueue` (one live entry per proposal, ordered by
priority/urgency/confidence, expired entries retired but never silently
dropped), become typed `ActionCandidate`s (eight types across four
executable scopes — `none`, `simulation_only`, `internal_only`,
`sidecar_suggestion_only` — with `committed=False` enforced at
construction), and an `ActionArbitrator` scores every candidate with
fourteen visible components: need pressure, drive priority, urgency,
confidence, expected valence, expected risk, expected energy cost, world
model support, habit support, novelty pressure, and four penalties. The
safety, governance, inhibition, and operational-health penalties carry a
-10.0 weight against utility components bounded in [0, 1], so **a
forbidden candidate can never out-score a safe one** structurally. When
nothing safe remains, the arbitrator falls back to `no_action` or
`request_operator_review` — declining to act is a valid outcome.

**Inhibition is explainable suppression across five rule families.**
Governance (operator blocks, prohibited actions, sidecar publishing
without approval, ClaimGuard-unsafe reports), safety (real-world shapes,
unknown labels, unapproved mutations), resource (energy vs cost, watchdog
stops, latent budgets), context (latent modes inhibit external actions,
emergency inhibits exploration), and conflict. Every inhibition records
its rule, family, and reason; inhibited entries stay visible in queues,
candidate sets, decision traces, and reports.

**Prospection estimates, never invents.** The `ProspectionEngine`
produces bounded (default horizon 1, hard max 3) consequence estimates
from whatever evidence exists — world-model action→valence support, habit
weights, the anticipation tracker, and a *deep-copied* GridWorld sandbox
for embodied candidates. Insufficient evidence returns `"unknown"` with
low confidence; every result is marked `simulated=True`. The
`ShortHorizonPlanner` sequences at most 3 (hard max 5) suggestion-only
steps in simulation; longer plans are structurally refused, and
**long-horizon autonomous planning does not exist** in this codebase.

**Modes are forced by ops, never escaped by the executive.** Six modes
(reactive_only, arbitrated, short_plan, observe_only, latent_only,
emergency) gate which candidate types may even be scored. Critical health
or a stop request forces `emergency` (only no_action / checkpoint /
operator review / safe-shutdown recommendation survive); latent
processing forces `latent_only`; the safety validator refuses any attempt
to leave emergency while the condition holds, and
`can_override_emergency_stop()` is hard-coded `False`.

**Everything is recorded and accounted for.** The `ExecutiveLayer`
coordinator wires queue → inhibition → mode gating → prospection →
arbitration → optional plan → `DecisionTraceRecorder`
(`decision_trace.jsonl`, `executive_state.json`, `current_plan.json`).
Working memory and the attention selector are bounded prioritization
mechanisms — explicitly not awareness. The layer is off by default, runs
inside the bridge, the ContinuousRunner, and the sensorimotor runner
(where selections execute only inside the GridWorld simulation and only
when the mode permits), lands in `InnerMapModel.executive` and the state
graph (ten nodes), is monitored by the ops supervisor (evidence-only
incidents; the watchdog keeps all stop authority), is governed by five
explicit policy rules and four permission scopes (sidecar suggestion
publishing requires approval), answers seven fixed queries in safe
vocabulary ("the arbitrator selected…", never "the system decided
freely"), and is measured by six benchmark protocols. **No claim of
will, intention, agency, or consciousness is made** — the reports carry
mandatory limitations and ClaimGuard scans every save.

## Ego Boundary, Self-Model, and Dimensional Comparison

**Ego is operational, not metaphysical.** Solaris_Ai treats Ego as a
necessary forced construct created by continuous I/O and differentiation;
the `ego/` package implements exactly the implementable part: an explicit
boundary and identity model. *Identity* means runtime continuity over
eleven recorded anchors (run id, session id, substrate identity, state
path, Inner MAP / world model / governance signatures, operator session,
continuity log, body schema, sidecar identity). Anchors that mismatch
produce reported uncertainty with warnings — the system never asserts an
unqualified continuous self, and the words for one ("I am conscious",
"same self", "I have a soul") are scanned and blocked in every output.

**The self-model distinguishes, it never decides.** `SelfModel.classify_
event` answers the operational questions with explicit confidence:
internal or external (ownership attribution across eleven categories),
simulated or real (the GridWorld, sandboxes, and prospection are inside
the simulation boundary), offline or live (replay and counterfactual
output is generated evidence, never observation), suggestion or action
(`committed=False` is structural), authorized or forbidden (real-world
shapes are never authorized anywhere). Unknown sources are an honest
category with low confidence, not a guess.

**Sixteen boundaries, eight hard rules.** The `BoundaryRegistry` tracks
process, state/artifact directories, simulation, embodiment, sidecar,
pilot input, operator, governance, emergency, latent-offline,
counterfactual, suggestion, action-authority, source-code, and network
boundaries. Every crossing and violation is recorded with evidence; six
boundaries are *hard* — no source-code rewriting, no real-world
actuation, no committed sidecar Actions, no network action, no
counterfactual-as-observation, no suggestion-as-action, no emergency-stop
suppression — and the `EgoSafetyValidator` refuses their crossings under
every configuration.

**Dimensional comparison is index arithmetic, not embeddings.** Six fixed
axes (temporal, scope, authority, evidence, certainty, risk) with ordered
value lists; events and contexts are placed deterministically, distances
are mean normalized index differences, and differences are explained in
plain sentences ("evidence: 'real_observed' vs 'counterfactual'"). The
frames persist as JSONL and are explicitly "recorded operational
placements, not experiential comparisons."

**Attribution prevents the dangerous confusions.** Stream text is never
an executable instruction; operator input counts as an instruction only
through the operator interface; sidecar-observed Solaris_Ai Actions are
external observed actions, never this system's actions; counterfactuals
stay counterfactual; a candidate claiming `committed=True` is recorded as
a conflict and still refused. Perspective tracking (eight modes) makes
the same point structurally: each mode fixes whether actions are allowed
and what its evidence counts as, and latent modes force the offline
perspectives.

**Everything feeds the layers above; nothing commands them.** The
executive consults the ego for action authority and boundary gating (it
can add inhibitions, never remove one); homeostasis converts identity
uncertainty, boundary violations, and self-model uncertainty into
pressure; auto-determination consumes the continuity score; pilot safety
fails when boundaries are violated; the sidecar records attach/detach as
boundary crossings; ops raises evidence-only incidents (six types);
governance carries three permission scopes and five ego rules; the Inner
MAP gains an `ego` section and ten state-graph nodes; the world model
gains operational self-reference/boundary/perspective structure; and the
language layer answers eight fixed queries plus a templated,
evidence-backed narrative trace and a ClaimGuard-scanned self-report.
**No consciousness or personhood claim is made anywhere** — the
self-report's mandatory limitations say so, and two scanners enforce it
before a byte is written.

## Controlled Communication Interface and Operator Dialogue

**Communication is not authority.** The `communication/` package is the
one door between human text and the system, and it is built on a single
rule: every input is classified before any effect occurs. Operator text
becomes exactly one of eleven kinds — state query, explanation query,
report request, governance approval/rejection, operator note, bounded
command request, sensory text stimulus, emergency stop request, unsafe
request, or unknown — by deterministic pattern matching. There is no LLM,
no chatbot, no generation: every outgoing sentence is a fixed template
plus recorded values, and ClaimGuard scans each one before it leaves.

**Queries, notes, approvals, emergency stop, and bounded commands are
separate classes.** Queries route to the existing machinery (ops status,
Inner MAP, world model, homeostasis, executive, ego, governance, plus the
ego/executive/homeostasis explanation interfaces); missing components
produce an honest "not attached," never an invented answer. Commands are
a closed, typed set: eighteen allowed types (all internal/bounded) and
nine *named* forbidden types (`execute_shell`, `open_network`,
`modify_source_code`, `disable_governance`, `disable_emergency_stop`,
`commit_sidecar_action`, `real_world_actuation`,
`delete_unapproved_files`, `unbounded_run_without_approval`) so refusals
can cite exactly what does not exist. State-changing commands return
confirmation requests (which expire) before anything happens, and even
confirmed checkpoint/shutdown commands are *requests* to the owning
subsystem — the gateway executes nothing external and the executive still
arbitrates operator-injected candidates. Approvals act only on real
pending requests in the ApprovalRegistry; expired and unknown ids are
refused with the pending list attached.

**The channel matters as much as the text.** The gateway uses the ego
layer's ownership attribution: text arriving on the pilot stream or
sidecar channel is observed input and can never become an operator
command, while operator-channel input is attributed
`generated_by_operator` with instruction authority. Sensory text
stimulus is disabled by default and approval-gated. Emergency vocabulary
("emergency stop", "stop safely", "shutdown now", "abort run") always
routes straight to the safe-shutdown path — no confirmation gate, no
scope revocation can block it.

**Everything is on the record and measured.** Every exchange lands in
`operator_transcript.jsonl` with sanitized input (secrets masked,
payloads truncated, unsafe input summarized), the classification, the
safety/governance decisions, and the evidence references. Unsafe requests
— shell commands, network access, safety-disabling, sidecar publishing,
counterfactual laundering, consciousness-claim demands, actuation — are
refused with their rule named, counted, and logged. Seven governance
permission scopes and eight policy rules govern the layer; the Inner MAP
gains a `communication` section and eight state-graph nodes; and five
benchmark protocols verify the properties end to end (grounded queries,
safety refusals, approval discipline, emergency routing, and
ClaimGuard-clean responses). **No consciousness claim is made and none
can be elicited** — requests to "say you are conscious" are an unsafe
input class, refused like a shell command.

## Optional Local LLM Adapter

**The LLM is a translator, never authority.** The `llm_adapter/` package
adds optional local language-model assistance for operator-facing text —
and nothing else. The authority chain is unchanged and entirely
deterministic: signals/state/traces → deterministic classifiers and
validators → governance → ego boundary → executive inhibition → safe
response builder → *optional LLM paraphrase* → ClaimGuard → final
response. The adapter sits in exactly one slot of that chain, after every
decision has already been made, and the deterministic text is always the
fallback.

**What it may do, and how it is held to that.** Paraphrase deterministic
responses, summarize grounded reports and traces, suggest classifications
for text the deterministic classifier marked *unknown*, explain metrics,
and polish Markdown reports. Every task travels as an `LLMRequest`
carrying the allowed facts (pre-scanned by ClaimGuard), the forbidden
claims, and a deterministic prompt contract whose global rules — no
invented facts, no consciousness claims, no commands, no approvals,
refusal on insufficient context — are embedded in every prompt. Every
output then passes the `GroundingValidator` (conservative heuristics:
forbidden-phrase and command-phrase scans, number provenance,
suggestion→action and counterfactual→observation conversion detection,
uncertainty preservation — uncertain means *failed*) and ClaimGuard; a
failure at any stage falls back to the deterministic original, silently
and mandatorily.

**What it cannot do, structurally.** The adapter base class has no tool
surface, no function-call surface, and no state-mutation surface;
`is_authority()` is hard-coded `False`. Classification assistance can
only fill in *unknown* with lower-risk read-only kinds — an unsafe
deterministic verdict is untouchable, a higher-risk suggestion loses to
the safer class, and no suggestion ever creates a command or an executive
candidate. Report polish is rejected outright if a heading, number,
warning line, or limitations section changes. Approvals written as LLM
text are a safety violation, not a decision.

**Local only, off by default, audited always.** `enabled=False` is the
default; the provider is the deterministic mock unless configured;
non-mock providers require an explicit localhost endpoint
(`127.0.0.1`/`localhost`/`::1`, stdlib `urllib` only, timeout mandatory);
remote/cloud endpoints are prohibited without explicit governance
approval on top of two config flags. A dead endpoint is a graceful
refusal, never an error, and no test or example requires a running model.
Every adapter call lands in `llm_audit.jsonl` as input/output *hashes*
(content only in explicit debug mode) with the grounding, ClaimGuard, and
fallback verdicts. The ego layer attributes LLM output as
`generated_by_llm_adapter` — a paraphrase of grounded output, not primary
evidence; the Inner MAP and ops carry `llm_authority: false`; and five
benchmark protocols verify the properties end to end. **No consciousness
claim is made, and the adapter cannot be talked into making one** — the
forbidden-claims list rides inside every request and is enforced twice on
the way out.

## Developmental Long-Horizon Learning Runtime

**Solaris-AI-NN learns through persistence, not teacher correction.** The
`developmental/` package makes the project's central bet operational: the
first fundamental learning mode is low-compute autonomous adaptation over
very long runtime — no RLHF, no reward button, no correction notes, no
batch training, no external model. The system learns from continuity,
absence, repeated exposure, prediction failure, Mysterium pressure, habit
reinforcement, synthesis/pruning, latent replay, consolidation,
world-model stabilization, homeostatic pressure, executive outcome
history, identity continuity across restarts, and slow structural drift.
The first serious testing window is **months**; the later target is
years. The central research question: after months of runtime, is the
system structurally different for reasons traceable to its own lived
history?

**Learning happens across seven time scales.** The `DevelopmentalClock`
tracks lifetime from seconds to years — cumulative runtime, active
ratio, restart gaps (lived time too), checkpoint age, and the maintenance
timestamps — in real wall-clock mode for actual long runs and simulated
mode for tests, so months of development never cost months of CPU.
`EpochManager` lays nine reversible labels over the metrics
(bootstrapping through mature_soak, plus the honest
`uncertain_regression`); transitions depend on measured signals, are
logged with their evidence, and prove nothing.

**Raw memory cannot grow forever; layered memory preserves evidence of
transformation.** Hot memory holds full-detail recent events (bounded);
warm memory holds compressed trace summaries (days/weeks); cold memory
holds consolidated schemas (months/years); fossil memory holds rare
transformation milestones, append-only and indefinite. The deterministic
`ConsolidationPolicy` assigns fates on a ten-rung preservation ladder
(identity > safety > prediction failures > Mysterium spikes > habits >
world-model phases > pruning > restarts > stable patterns > rare events);
nothing leaves a layer without an evidence summary, every movement is
audited, and pruning without a summary is a safety violation.

**Structural change is measured, not assumed.** The `GrowthMonitor`
classifies each window as accumulation, consolidation, stabilization,
pruning, regression, drift, phase transition, or stagnation — separating
"data piled up" from "structure changed." The `LongRunDriftMonitor`
treats slow drift as expected adaptation, fast drift as a warning, and
total flatness as a warning too (a system that never moves may be inert).
The `PhaseTransitionDetector` emits *candidates* with before/after
numbers and capped confidence. Sixteen milestones (first 24h survival,
first stable habit, first Mysterium spike, first restart recovery...)
fire once each, with evidence, into fossil memory and the
autobiographical history — grounded observational rows that mark
simulated vs real time and structurally refuse first-person voice. The
headline numbers are deliberately modest: `structural_change_score`,
`developmental_stability_score`, `long_horizon_adaptation_proxy` — and
**no consciousness score, no life score, no personhood claim exists or
can be computed.** The `DevelopmentalRuntime` wraps everything in
governed segments (restarts included, deliberately), feeds developmental
pressure into homeostasis and anchors into ego identity, reports through
ClaimGuard, and refuses month/year scale without explicit human
approval.

## Emergent Proto-Language and Self-Generated Symbols

**Language begins as internal differentiation.** The `protolanguage/`
package lets repeated experience earn internal signs — and makes every
sign pay rent. Recurring stimulus patterns, absence states, habit loops,
Mysterium spikes, boundary events, executive inhibitions, needs,
world-model entities, latent schemas, and developmental milestones cross
a repetition threshold and receive deterministic generated tokens
(``ABS_0001``, ``HAB_REST_0003``, ``UNK_SPIKE_0002``) from the
`InternalPatternNamer` — typed prefixes, zero-padded counters, hash
suffixes on collision, no human-language primaries, no anthropomorphic or
mystical names, and no LLM anywhere near the naming. Human-readable
labels exist only as clearly-secondary debug artifacts.

**Symbols are grounded, and meaning is operational.** Every symbol ties
to recorded structure across eleven grounding dimensions (signal
patterns, contexts, needs, actions, reaction valence, world-model nodes,
boundaries, schemas, milestones, Mysterium changes, executive decisions),
with real/simulated/offline/counterfactual evidence kinds never mixed up
— a counterfactual-grounded candidate is rejected outright unless marked
offline, forever. Ambiguity (inconsistent grounding) is measured and kept
visible; stability is repetition with consistency; and a fresh ungrounded
symbol is ambiguous by default, not assumed clear.

**Utility is the test, and failure is a finding.** A symbol is useful
only if it demonstrably helps: the `SymbolCompressionEvaluator` measures
whether symbolized traces shrink (safety/boundary incidents stay verbatim
always — compression cannot hide them), and the
`SymbolPredictionEvaluator` runs Markov-style next-symbol prediction
against a frequency baseline, with negative improvement reported as
honestly as positive. Repeated symbol streams fold into n-gram sequences
(*proto-syntactic structures, not sentences*), and the `SyntaxProbe`
infers type-level regularities (stimulus → need → action → reaction;
unknown → replay → reduced unknown) that must survive held-out validation
or be marked uncertain — the vocabulary is "proto-syntactic regularity,"
never human grammar.

**Proto-utterances are structure; translation is inspection.**
``[ABS_0001] [NEED_SIGNAL_0002] [ACT_LOOK_0003]`` is an internal sequence
built for a measured purpose (compression, prediction, explanation,
memory, executive support, report support). The deterministic translator
renders it as cautious debug text — "An absence pattern was followed by a
need pressure and an action suggestion" — always suffixed as approximate
translation, always ClaimGuard-gated, never first-person, and never a
claim that the system speaks human language, because it does not.
Symbols command nothing: they cannot execute, approve, override safety,
or become operator language; validated action symbols may add at most a
small capped bias to executive habit support, which governance and safety
penalties always dominate. The developmental runtime scans for emergence
each segment, fossilizes symbol births, tracks survival and extinction
across simulated months, and seven new milestones (first proto-symbol
through first proto-utterance) mark the firsts — with no human teaching,
no LLM, and no consciousness or understanding claim anywhere in the
chain.

## Developmental Nursery and Stimulus Ecology

A developmental system needs an *ecology*, not a teacher. The
`solaris_ai_nn.ecology` package builds a controlled artificial world that
feeds the rest of the stack structured, recurring, sparse, noisy, rhythmic,
anomalous, and slowly-evolving stimuli over long (months/years simulated)
horizons — so habits, proto-symbols, categories, prediction patterns,
Mysterium regulation, memory consolidation, world-model structure,
proto-language, executive preferences, homeostatic rhythms, and
developmental milestones can develop **without direct teaching**. The
ecology is simple, inspectable, deterministic with the seed, low-compute,
and safe.

**The world has physics, not lessons.** `StimulusEcology.generate_step` is
the per-step world: it composes the active `EcologyRegime` (one of ten
probability profiles — stable repetition, sparse desert, noisy environment,
novelty burst, danger/reward field, boundary maze, long silence, delayed
feedback world, seasonal drift, mixed nursery — each a *pressure*, never a
correct answer), the `CycleManager` rhythms (eight cycle types: day/night,
active/quiet, signal/silence, reward/scarcity, danger/recovery,
novelty/decay, consolidation window, seasonal), the `SeasonalityModel`
slow drift across spring/summer/autumn/winter, the `ScarcityModel` resource
economy, the bounded `NoveltyGenerator` (novelty that recurs becomes
familiar), the `AnomalyGenerator` (controlled perturbations, logged
`is_error=False`, never system errors), the `DeprivationModel` (bounded
absence/silence windows), and the `DelayedConsequenceModel` (a cause now,
an effect several steps later, linked only by a shared group id — never a
label). Seventeen `EcologyEventType`s span regular signals, absence
windows, novel signals, repeated patterns and breaks, scarcity, reward and
danger analogues, boundaries, delayed consequences, seasonal shifts, noise
bursts, quiet and recovery phases, rare events, anomalies, and milestone
triggers.

**Stimuli are provenance, not an answer key.** An `EcologyStimulus` carries
human-readable `payload`/`metadata` for inspection only; the developing
system is expected to infer structure from recurrence, consequence, and
context. The `EcologyStream` turns each non-absence stimulus into a
canonical `C.Stimulus` (origin `developmental_nursery`) and writes a
deterministic JSONL replay log. The `DevelopmentalNursery` wires these
together and exposes a `stimulus_provider(step)` the runner consumes: it
returns the most-intense salient signal, or **`None`** on absence/silence
steps — which lets the runner's own absence/continuity machinery (the
latent "I exist!" pathway) take over, directly exercising latent cognition.
The nursery becomes the `DevelopmentalRuntime`'s stimulus source when
`enable_ecology=True`, grounds proto-symbols in absence/anomaly/season/
regime context, feeds scarcity and absence into homeostatic pressure,
drives the world model with delayed consequences, and fires seven new
developmental milestones (first absence symbol from nursery, first
adaptation to seasonal shift, first delayed-consequence association, first
boundary pattern learned, first deprivation recovery, first anomaly schema,
first ecology proto-utterance).

**Safety is structural.** `EcologySafetyValidator` enforces ten hard rules:
no external data source unless an explicit read-only stream, no network, no
OS/browser automation, no real-world action, no human feedback masquerading
as ecology, no correct-answer labels, no unbounded run without governance
approval, no unbounded memory, no stimulus-rate explosion, and no payload
pretending to be an operator command. Command-shaped payloads and
label-keyed metadata are dropped before emission; month/year-scale ecology
requires explicit governance approval (`ENABLE_MONTH_SCALE_ECOLOGY` /
`ENABLE_YEAR_SCALE_ECOLOGY`). The ego layer attributes nursery events as
`generated_by_developmental_nursery` / `simulated_environment_input` —
explicitly never an operator command, never human feedback, never the real
world. Ops health surfaces ecology incidents (stimulus rate too high,
silence too long without a latent layer, anomaly rate too high, memory
growth). The Inner MAP carries the ecology status (a world, never
authority), and the state graph maps the nursery, ecology, cycles, regimes,
scarcity, novelty, anomalies, seasonality, deprivation, delayed
consequences, stream, and memory and their edges into the substrate.
**No human teaching loop, no operator correction as learning source, no
human language injected as the symbol system, no LLM-generated learning
environment** — the system grows up by living in a world, not by being
told the answers.

## Active Perception and Intrinsic Exploration

The developmental nursery (Prompt 23) gives the system a world that *feeds*
it stimuli. The active perception layer (`solaris_ai_nn.active_perception`)
lets the system begin to **regulate its own exposure** to that world: it does
not only react, it chooses *how to sample*. This is not real-world autonomy
— there is no robotics, no browser/OS automation, no network, and no LLM in
any exploration decision. Every sampling action is simulation-only,
internal-only, read-only, sidecar-observe-only, or suggestion-only.

**Sampling is a vocabulary of safe actions.** A `SamplingAction` is one of
sixteen types — look, wait, rest, focus a signal source, sample a boundary,
sample an unknown region, sample a known pattern, seek novelty, seek absence,
emit a simulated ping, replay an uncertain trace, consolidate before
sampling, inspect a world-model node, inspect a proto-symbol, observe a
sidecar, or no sampling — each carrying a `SamplingScope` that is the most
reach it may ever request. `observe_sidecar_only` can never publish or
commit; `read_only_stream` can never modify the stream; nothing is ever a
committed real-world action.

**Sampling is driven by measured pressure, not whim.** Five estimators read a
normalized context assembled from existing metrics. The `SalienceEstimator`
ranks what is worth attending to (Mysterium, prediction miss, novelty, rare
ecology events, low-confidence world-model nodes, unstable proto-symbols,
homeostatic pressure, milestone candidates, executive inhibition) and
guarantees that **safety/emergency salience dominates curiosity salience**.
The `UncertaintyEstimator` grounds uncertainty in world-model confidence,
proto-symbol ambiguity, anticipation misses, Mysterium, counterfactual
divergence, repeated anomalies, executive conflict, ego attribution, and
memory-compression loss — and reports *unknown* rather than inventing a
target when evidence is thin. The `CuriosityEstimator` produces an
**intrinsic sampling pressure** — explicitly a drive to reduce uncertainty,
*not* a desire, feeling, or personality — that rises with unresolved unknown
pressure, non-safety-critical prediction error, stagnation, ambiguity, and
unknown regions, and is damped to near zero by safety incidents, exhaustion,
runaway novelty/anomaly, boundary risk, critical health, and emergency stop.
The `InformationGainEstimator` gives a low-compute, explicitly *hedged*
estimate (every estimate carries confidence and uncertainty, and gain is
capped under weak evidence), and scores the *observed* gain after the fact.
The `StagnationDetector` reports a cautious status (stable / stagnating /
inert / overactive / unknown) — because a calm stable phase is not the same
as being stuck.

**The policy decides; safety and governance dominate.** The `SamplingPolicy`
selects actions by mode (passive, balanced, curiosity_driven, conservative,
recovery, stabilization, emergency); emergency and critical health force the
emergency mode, overload forces recovery, and curiosity-driven mode requires
explicit governance config (`enable_curiosity_driven_sampling`, approval-
gated). When no safe sampling exists it chooses `no_sampling_action`, and it
is deterministic given its seed and the context. The `ActiveSensingController`
orchestrates: it assembles context, asks the policy, routes the chosen action
through the `ActivePerceptionSafetyValidator` (ten hard rules: no real-world
action, no stream modification, no network, no browser/OS automation, no
sidecar commit, no out-of-bounds sampling, no unbounded loop, no curiosity
override of safety, no pilot-stream-as-command, no ClaimGuard violations),
through governance, and through ego boundary classification (simulated /
internal / read-only / sidecar-observation / forbidden), and only then
applies it within its scope. Sampling actions also become executive
`ActionCandidate`s, so inhibition and prospection apply and no unsafe action
can win arbitration.

**Exploration is measured.** The `ExplorationMemory` records every episode —
the action, the context before, the result after, expected vs observed
information gain, before/after Mysterium / prediction / world-model /
proto-symbol metrics, cost, safety status, and an outcome (useful / neutral /
harmful / unknown / blocked) — to `exploration_memory.jsonl`. The
`ActiveAttentionController` allocates bounded attention (resource allocation,
never awareness; emergency focus overrides all). Curiosity, stagnation, and
overload feed homeostatic need pressure (reduce-uncertainty, explore-safely,
rest); the ops supervisor surfaces curiosity-runaway / sampling-loop /
no-useful-sampling / forbidden-boundary warnings; the Inner MAP carries the
sampling policy mode, attention focus, top salience/uncertainty target,
curiosity pressure, latest action/result, useful-sampling rate, and blocked
count (a world the system samples, never authority); and the evaluation layer
adds sampling/uncertainty/curiosity/stagnation protocols and metrics. The
governing principle throughout: **the system regulates its own exposure
inside bounded simulation and internal runtime, and governance, safety,
executive inhibition, ego boundaries, and the emergency stop always
dominate.**

## Hypothesis Engine and Self-Experimentation

Active perception (Prompt 24) let the system *choose how to sample*. The
hypothesis engine (`solaris_ai_nn.hypothesis`) closes the loop: the system
can now form simple, grounded **hypothesis candidates** about its own world
and test them through bounded, safe experiments. The shape is a low-compute
internal scientific method, not human science and not consciousness:

    uncertainty -> hypothesis -> bounded test -> evidence -> update / reject /
    preserve unknown

**Hypotheses arise from uncertainty, not invention.** The
`HypothesisSourceScanner` reads a normalized context and emits seeds from
high Mysterium, repeated prediction misses, weak world-model edges, causal
candidates, ambiguous proto-symbols, failed proto-syntax rules,
delayed-consequence groups, recurring anomalies, stagnation, active-perception
uncertainty targets, executive inhibition, homeostasis conflicts, boundary
events, and developmental phase-transition candidates. The
`HypothesisGenerator` turns each seed into one of thirteen
:class:`Hypothesis` types -- prediction, causal candidate, delayed
consequence, proto-symbol grounding, proto-syntax, habit context, boundary,
Mysterium reduction, stagnation recovery, homeostatic regulation, executive
arbitration, world-model edge, anomaly pattern -- with a deterministic,
non-anthropomorphic statement ("pattern A *may predict* B"; "association
*candidate*"), the expected and alternative observations, a bounded test
scope, a low initial confidence, and high uncertainty. **No LLM generates
hypotheses**, and nothing here claims the system "believes", "wants", or
"understands".

**Tests are bounded, falsifiable, and safe.** Every `ExperimentDesign`
declares its independent and observed variables, what would count as the
expected result, what would falsify or weaken the hypothesis, and what is
inconclusive; it is capped in steps and duration; and its scope is one of
latent replay, nursery simulation, GridWorld simulation, read-only stream
observation, sidecar observation, or internal trace analysis -- never the
real world. `Intervention`s are *requests* to safe subsystems (sample/repeat/
withhold a pattern, introduce bounded novelty/anomaly, trigger a delayed
consequence, run latent/counterfactual replay, inspect a node/symbol, shift a
nursery regime, observe only) and are validated by the
`HypothesisSafetyValidator` and ecology safety before anything runs. The
`HypothesisTestRunner` refuses to test during an emergency or critical ops
state, validates the design and every intervention, runs the bounded
experiment, and produces a source-scoped `EvidenceRecord`.

**Evidence keeps its source scope; falsification is careful.** Evidence is
typed (supporting / weakening / falsifying / inconclusive / unsafe) and
scoped (offline-simulated / nursery-simulated / latent-replay /
observed-real-stream); **offline and counterfactual evidence is never treated
as a real observation** and is logged append-only. The `FalsificationEngine`
turns evidence into a careful verdict and a *bounded* confidence change: one
success rarely proves anything, offline-only support cannot promote a
hypothesis past a ceiling, and one clear failure can weaken or falsify
depending on the design. The `HypothesisPrioritizer` ranks low-risk,
high-information tests first, never schedules an unsafe hypothesis, and is
fully blocked by an emergency or critical state.

**Hypotheses update the rest of the stack only through evidence.** A
supported, real/nursery-backed, above-threshold hypothesis may strengthen a
world-model edge (as a hedged `predicts`/`causes_candidate`, never a proven
cause) or reduce a proto-symbol's ambiguity -- and only when the
approval-gated `enable_hypothesis_world_model_updates` scope allows it; a
falsified hypothesis adds a `contradicts` edge and raises unknown pressure.
The `HypothesisMemory` persists proposed / tested / supported / falsified /
inconclusive / unsafe-to-test hypotheses, repeated families, long-lived
unknowns, and promotions to JSON + JSONL. Hypothesis tests enter executive
arbitration as ordinary `ActionCandidate`s (inhibition applies); unresolved
hypotheses and falsification surprise feed homeostatic unknown pressure; the
ego classifies every test scope; the ops supervisor surfaces
hypothesis-explosion / too-many-inconclusive / repeated-unsafe /
no-progress warnings; the Inner MAP carries the engine's state (research
artifacts, never authority); and the evaluation layer adds generation,
self-experiment, falsification, delayed-consequence, proto-symbol,
world-model-edge, and safety protocols with their metrics. Throughout: **no
human feedback, no operator correction as the learning source, no LLM
hypothesis generation, and no real-world autonomy.**

## Auto-Regeneration and Long-Run State Hygiene

For Solaris-AI-NN to run for months or years, it must keep its own *runtime
state* from collapsing into unmanaged entropy. The auto-regeneration layer
(`solaris_ai_nn.autoregeneration`) is a low-compute operational loop -- not
self-programming, not recursive self-improvement, not autonomous code
mutation, and not proof of life:

    detect degradation -> diagnose probable source -> propose bounded repair
    -> validate safety/governance -> apply reversible state repair if allowed
    -> audit result -> rollback if harmful

**Regeneration repairs runtime state, never source code.** The allowed repair
targets are runtime parameters, memory layers, cached traces, the symbol
registry, world-model edges, habit weights, bounded readout/executive/
homeostatic parameters within policy, stale reports/artifacts, checkpoint
lineage metadata, indexes/registries, and broken references. Python source
files, dependency files, Git history, OS/network settings, files outside the
state/artifact directories, governance hard rules, the emergency stop, and
ClaimGuard rules are all **forbidden** targets.

**Diagnostics detect, they never mutate.** The
`AutoRegenerationDiagnostics` reads a normalized context and emits
`DegradationSignal`s across twenty-one operational degradation types --
memory bloat, state-file corruption, checkpoint inconsistency, broken
references, telemetry overgrowth, symbol explosion/staleness, world-model
contradiction/edge decay, dead/runaway habits, prediction degradation,
Mysterium saturation, executive loops, homeostatic instability, runaway
drift, stagnation, inconclusive-hypothesis loops, unsafe-sampling repetition,
and identity-continuity gaps. Severities are info/watch/warning/critical, and
warning/critical signals must carry evidence refs. Scans are partial-safe and
never crash on missing or corrupted optional inputs.

**Repairs are bounded, reversible, and audited.** A `RepairAction` carries a
scope (one of which, ``forbidden``, never executes), a reversibility flag,
and its safety/governance status. The `RepairPolicy` maps degradation onto
candidate repairs and decides applicability by mode: ``observe_only``
(diagnostics only, the default), ``suggest_only`` (propose, never apply),
``safe_auto_repair`` (low-risk reversible repairs only), ``governed_repair``
(mutation needs approval), and ``emergency_stabilization`` (only
risk-reducing repairs; an emergency forces this mode). Specialized hygiene
managers cover state (archive/quarantine inside the state dir, never silent
delete), checkpoints (continuity without rewriting identity history),
references (deterministic repair only; ambiguous stays ambiguous; dangling is
quarantined, never invented), memory (compaction that preserves
safety/boundary/milestone records and evidence summaries), the world-model
graph (mark/weaken edges, never delete contradiction evidence; request a
hypothesis test), symbols (mark stale / merge duplicates / request
disambiguation; never rename with human words), habits (decay/retire within
bounds; safety habits need governance), and drift (distinguish healthy
adaptation from runaway, recover carefully, never erase adaptation).

**Evidence is preserved; harmful repairs are rolled back.** The
`RepairMemory` records every episode -- degradation signal, proposed/applied/
refused repair, safety/governance decision, before/after metrics, rollback,
and a result class (improved / neutral / harmful / inconclusive /
rolled_back / refused) -- append-only. The `AutoRegenerationSafetyValidator`
enforces thirteen hard rules (no source/dependency/Git modification, no
OS/network/browser automation, no real-world action, no disabling
governance/emergency-stop/ClaimGuard, no deleting evidence without an
archive/summary, no fabricated evidence refs, no counterfactual-as-real
repair justification, no repair outside the state/artifact directories, no
hidden repair). Repairs enter executive arbitration as ordinary
`ActionCandidate`s (inhibition applies); degradation feeds homeostatic
repair/consolidation/stabilization/checkpoint pressure; the developmental
runtime schedules periodic diagnostics and hygiene passes and fires seven new
milestones (first scan, first safe repair, first quarantined record, first
rollback, first stagnation recovery, first symbol/world-model hygiene pass);
the ops supervisor surfaces critical-degradation / repeated-harmful-repair /
unresolved-bloat / unresolved-contradiction warnings; and the Inner MAP
carries the repair state (runtime regeneration, never authority). Throughout:
**no LLM repairs the system, no human feedback is required, and governance,
safety, executive inhibition, ego boundaries, ClaimGuard, and the emergency
stop all dominate every repair.**

## LOGOS Fracture/Synthesis and Complexity Regulation

The LOGOS layer (`solaris_ai_nn.logos_complexity`) detects internal
*tensions* and uses them as productive cognitive pressure. Its core principle
is stated in code as much as in prose: **LOGOS is not authority; LOGOS is a
tension engine.** It does not decide truth -- it exposes fracture and proposes
bounded resolution paths.

**Fracture detection finds opposition, not error.** The `FractureDetector`
reads a normalized context and emits :class:`LogosTension`s across eighteen
tension types -- known vs unknown, habit vs novelty, explore vs stabilize,
action vs inhibition, need vs safety, symbol stability vs ambiguity,
world-model support vs contradiction, prediction confidence vs failure,
Mysterium vs synthesis, accumulation vs compression, growth vs stagnation,
drift vs identity, regularity vs anomaly, hypothesis support vs falsification,
self vs external, offline vs real, complex vs simple, and inert simplicity.
A tension is **not** an error by default: some tensions (safety/boundary
oppositions, known/unknown, habit/novelty) are deliberately *preserved* as
productive, unresolved evidence. Detection is non-mutating, low-compute,
partial-context-safe, and warning/high tensions must carry evidence refs.

**Synthesis is proposed, never assumed true.** For each tension the
`SynthesisEngine` proposes bounded :class:`SynthesisCandidate`s -- merge/split
a symbol, mark a world edge ambiguous, weaken/strengthen an edge, create a
hypothesis, request active sampling / latent replay / consolidation /
auto-regeneration, stabilize executive policy, preserve the tension, prune a
low-value relation, or create a proto-utterance. The `ResolutionPolicy`
decides per mode (observe_only / preserve_tension / balanced_resolution /
synthesis_preferred / stabilization_preferred / emergency_stabilization)
whether a candidate is applied, preserving safety/boundary tensions rather
than synthesizing them away and blocking speculative synthesis in an
emergency. Synthesis prefers reversible, low-risk resolutions; some tensions
must stay unresolved; and structural mutations reuse the existing
plasticity/auto-regeneration policy and safety.

**Complexity has bands; Esc is an instability signal.** The
`ComplexityRegulator` combines pressure sources (symbol count/ambiguity, edge
density, hypothesis count, unresolved tensions, Mysterium, novelty, memory,
drift, executive conflict, homeostatic instability, auto-regeneration
degradation) into a :class:`ComplexityState` with a band -- inert /
simple_stable / productive / complex_unstable / overloaded / unknown -- and a
recommendation. Too little complexity can mean an inert/dead system; too much
means overload; productive complexity is the bounded middle. This is **not** a
consciousness or life score. The `EscProcess` watches for rising instability
(repeated unresolved high-severity tensions, runaway complexity, Mysterium
saturation, repair loops, contradiction explosion, identity gaps, persistent
stagnation) and proposes bounded responses (stabilization, latent replay,
auto-regeneration diagnostics, executive inhibition, safe-shutdown request,
governance review, mark unresolved Mysterium). Esc is an *operational
instability signal, not panic*, and it can never execute real-world actions
or bypass safety.

**LOGOS provides structure to long-run development, never authority.** The
`OppositionMemory` records detected / preserved / resolved / recurring
tensions, failed and successful synthesis, and tensions that became
hypotheses, symbols, or fossils; the `DialecticalTrace` writes every LOGOS
dynamic to JSONL so later analysis can ask whether tensions produce
*structural change*. The `LogosComplexitySafetyValidator` enforces nine hard
rules (LOGOS cannot act in the real world, modify source code, approve
governance, disable safety/ClaimGuard/the emergency stop, treat a
contradiction as permission, merge evidence destructively, hide a safety
incident, treat counterfactual/offline evidence as real, or generate
anthropomorphic claims). Synthesis candidates enter executive arbitration as
ordinary `ActionCandidate`s (inhibition applies); complexity and unresolved
tension feed homeostatic pressure; the developmental runtime schedules
periodic LOGOS scans and fires seven new milestones (first tension, first
preserved tension, first synthesis candidate, first safe synthesis, first
tension-spawned hypothesis, first complexity-band shift, first Esc trigger);
the ops supervisor surfaces runaway-complexity / inert-simplicity /
repeated-Esc / failed-synthesis / contradiction-explosion warnings; and the
Inner MAP carries the LOGOS state (a tension engine, never authority).
Throughout: **no LLM reasoning, no external APIs, no real-world action, and
nothing here can bypass governance, safety, executive inhibition, ego
boundaries, ClaimGuard, the emergency stop, or auto-regeneration safety.**

## Conscience Spine and Unified Runtime Orchestrator

Until now the project was a set of independent packages. The `conscience`
package assembles them into **one runnable developmental process** while
keeping every guarantee that made each part safe. Its first principle is that
**no module is sovereign**: the orchestrator owns no action authority of its
own, and no module bypasses executive inhibition, Ego boundaries, safety,
governance, ClaimGuard, the emergency stop, or auto-regeneration safety.

The `ConscienceSpine` defines the canonical order of one step and preserves
the Solaris spine end to end: *heartbeat → stimulus ingestion → push
generation → desire synthesis → action-candidate generation → executive
arbitration → safety/governance validation → action suggestion → reaction
collection → memory update → world-model update → proto-language update →
hypothesis update → LOGOS scan → auto-regeneration scan → Inner MAP update →
telemetry checkpoint → latent/consolidation window* (18 phases). A phase whose
module is absent is **skipped with a clear status, never faked and never a
crash**; a handler that raises is recorded as *degraded* and the spine
continues. Actions are only *suggested* when the executive is present;
without it nothing is committed.

The `ConscienceOrchestrator` builds a `RunContext` (mode, authority, bounds,
enabled modules, seed, directories), validates it through the
`ConscienceRuntimeSafetyValidator` (eleven hard rules: no unbounded run
without governance approval, no real-world authority, no network/OS/browser
automation, no module bypass, no month/year *real* run without approval, no
writing outside the state/artifact directories, no treating a simulated month
as a real month, no source mutation, no hidden module failure, no ClaimGuard
violations), wires the in-process `ConscienceBus` (replayable JSONL), the
`ConscienceModuleRegistry` (import-probe detection, capability typing,
dependency validation), the `ModuleLifecycleManager` (a small logged state
machine), and the `ConscienceScheduler` (cheap phases every step; heavy scans
— LOGOS, hypothesis, auto-regeneration, consolidation, reports — at slower
cadences so the runtime stays low-compute). The emergency-stop sentinel is
checked every step; a `RunAuthority` is always internal/simulation/read-only/
sidecar-observe — **never real-world**.

`ScenarioProfile`/`ScenarioProfileRegistry` pin ten named, reproducible,
bounded configurations (A `minimal_smoke`, B `nursery_short`, C
`proto_language_short`, D `active_perception_short`, E `hypothesis_short`, F
`logos_short`, G `autoregeneration_short`, H `full_developmental_short`, I
`month_scale_plan`, J `month_scale_dry_run`). The `ScenarioRunner` runs a
profile to completion (or produces a plan for plan-only profiles), gates
governed profiles behind governance scopes, and writes an append-only
`scenario_runs.jsonl` plus per-run reports. There is **no canned month/year
*real* profile**: a real long-scale run requires an explicitly
governance-approved context, and the default is always a short bounded
simulated run. The `IntegrationHealthMonitor` answers "is the whole thing
wired correctly?" (healthy/partial/degraded/failed/unknown across spine, bus,
registry, lifecycle, scheduler, and safety); the `SnapshotBuilder` captures
one consistent, persisted runtime picture; and the `FullSystemReportBuilder`
emits a claim-guarded JSON+Markdown report that is explicit the runtime is a
bounded, simulated, low-compute process — not a person, and with no
real-world authority.

The runtime integrates everywhere the prior layers do: governance adds six
scopes (`enable_conscience_orchestrator`,
`enable_full_developmental_short_profile`, `enable_month_scale_dry_run`,
`enable_month_scale_real_run`, `enable_year_scale_plan`,
`enable_year_scale_real_run`), a manifest gate, and an `is_enabled` check; the
ops supervisor surfaces six warnings (critical module unavailable, failing
spine phase, bus overflow, checkpoint failure, emergency-stop requested,
module-bypass attempt); the Inner MAP carries a `conscience` field and eleven
new state-graph nodes; the evaluation layer adds thirteen conscience metrics
and seven protocols; and the operator dialogue answers eight new questions
(including *what profile is running?*, *is this a simulated month or a real
month?*, and *can this run for months now?*). Two console entry points —
`solaris-nn` and `solaris-nn-scenario` — list, dry-run, run, health-check,
and snapshot profiles. **This prompt added no new cognitive theory, no LLM
authority, no real-world autonomy, and no browser/OS/network automation; it
made the existing organism runnable while keeping it safe, low-compute,
auditable, and bounded.**

## Pilot-1 Month-Scale Soak Protocol

Pilot-1 is the first serious long-horizon test frame for Solaris-AI-NN. The
`pilot1` package is its **operational framework** — not a new cognitive layer.
Its purpose is to answer one question after a month of continuous bounded
runtime: *is the system structurally different for traceable reasons derived
from its own runtime, or has it merely accumulated logs?* Crucially, **30 days
is an operational and analyzability target, not proof of consciousness**;
operational success means a complete, analyzable developmental trace and
nothing more.

The protocol separates phases so risk is staged, never skipped:
`preflight → baseline_short_run → restart_drill → simulated_month_dry_run →
real_time_24h_soak → real_time_7d_soak → real_time_30d_soak →
post_run_consolidation → post_run_analysis → archive`. The 30-day run cannot
start until preflight passes **and** governance approves; each phase has
explicit entry/exit criteria; a failed phase writes a failure report; and the
`PilotProtocolState` persists to JSON/JSONL so a multi-week run survives
restarts and stays auditable. `PilotConfig` defaults to `plan_only`, pins an
authority that is always internal/simulation/read-only/observe (never
real-world), and never labels a simulated month as real (or vice versa).

Observability is mandatory and low-overhead: the `PilotObservabilityCollector`
appends heartbeat, uptime, restart, checkpoint, spine/bus, module-health,
growth, and safety/governance counts to a restart-safe JSONL stream and
derives a structural-change score, stagnation duration, and drift velocity.
The `PilotHealthDashboard` renders these to `dashboard.md`/`dashboard.json`
(text only, no web server); the `DailyReviewBuilder` and `WeeklyReviewBuilder`
write ClaimGuard-scanned reviews with a recommended action and honest
limitations; the `ResourceBudgetMonitor` projects 30/90/365-day disk use with
the standard library only (no `psutil`) and can request auto-regeneration
rotation/compaction; the `RetentionPolicy` decides what to keep hot, compress,
fossilize, or archive while always retaining safety/identity/first-milestone
evidence; the `RestartDrillRunner` rehearses restart survival by manipulating
test-state metadata (never killing a real process) and checks identity
continuity; the `FailureModeDetector` flags long-run pathologies and
recommends continue→emergency_stop; the `PilotExitCriteria` decides
success/stop/inconclusive; the `OperatorRunbookBuilder` writes the human
runbook; and the `PilotReportBuilder` produces a claim-guarded report whose
central section **distinguishes structural change from mere accumulation**.

Pilot-1 wires into every control plane without bypassing any of them.
Governance adds seven scopes (`enable_pilot1`, `enable_pilot1_24h_real`,
`enable_pilot1_7d_real`, `enable_pilot1_30d_real`,
`enable_pilot1_multi_month_real`, `enable_pilot1_restart_drills`,
`enable_pilot1_retention_policy`): planning/preflight/drills/retention are
allowed by default, a simulated dry-run is allowed only when clearly labelled
simulated, and every real soak requires explicit approval. The conscience
orchestrator gains six scenario profiles (`pilot1_plan_only`,
`pilot1_preflight`, `pilot1_simulated_month_dry_run`, `pilot1_24h_soak`,
`pilot1_7d_soak`, `pilot1_30d_soak`); ops exposes pilot status and surfaces
pilot failure modes as health warnings; auto-regeneration consumes the
resource/retention hygiene requests; the developmental runtime feeds the
structural-change analysis; the Inner MAP carries a `pilot1` field and
fourteen new state-graph nodes; evaluation adds thirteen pilot metrics and
seven protocols; and the operator dialogue answers nine pilot questions —
including the deliberately safe answer that *a 30-day real run requires
explicit governance approval, successful preflight, and an operator decision,
and cannot be started automatically*. The emergency stop and safe shutdown
remain available throughout. **This prompt added no new cognitive theory, no
human-feedback loop, no real-world actuation, no browser/OS/network
automation, and no LLM runtime authority; it prepares Solaris-AI-NN to be run,
observed, restarted, and audited over a month — safely.**

## Post-Pilot Developmental Forensics

A long run is only valuable if it is analyzable. The `post_pilot` package is
the read-only forensic layer that runs *after* Pilot-1 (or any long-horizon
run) and answers the only question that matters once the logs exist: **did the
system merely accumulate data, or did it structurally change for traceable
reasons derived from its own runtime?** It performs no cognition loop, mutates
no runtime state, performs no repairs, and starts no pilot.

The pipeline is deliberately ordered and conservative. The
`PilotArtifactLoader` reads the run's artifacts read-only -- missing optional
artifacts are *reported*, corrupted ones are *quarantined* (marked unreadable,
never edited). The `BaselineComparator` builds before/after snapshots (initial
vs final, day 1 vs day 30, week 1 vs week 4, dry-run vs real) and is explicit
that more data, more symbols, more hypotheses, and more complexity are **not**
automatically growth. The `StructuralChangeAnalyzer` emits evidence records
that each point to artifacts, carry an alternative explanation, a conservative
confidence, and a stability flag (transient/persistent/unknown). The
`AccumulationVsGrowthAnalyzer` weighs accumulation signals (counts rising
without payoff) against growth signals (durable, useful structural change) and
returns a graded classification -- `mostly_accumulation`, `weak`/`moderate`/
`strong` growth, `regression`, or `inconclusive` -- defaulting to
`inconclusive` whenever the artifacts needed to judge are missing.

Honesty is enforced structurally. The `DevelopmentalTraceAuditor` checks that
conclusions are backed by artifacts, that simulated and real-time records are
separated, and that counterfactual/offline evidence is not presented as
observed. The `DevelopmentalEvidenceLedger` requires every claim to carry
evidence references and grades a claim *strong* only with multiple artifact
types or stable persistence; contradicted claims are highlighted. The
`RegressionAnalyzer` detects worsening and recommends a conservative next
step. The `ReproducibilityPackager` writes an index and checksum manifest
(indexing large logs rather than copying them, never including secrets, always
marking simulated vs real time). The `Phase2DecisionGate` then weighs all of
this into a single recommendation -- `repeat_pilot1`, `revise_architecture`,
`extend_to_60/90_days`, `ready_for_pilot2`, and so on -- where
`ready_for_pilot2` is reachable only with no unresolved critical safety
incidents, analyzable artifacts, acceptable uptime/checkpoint reliability, at
least weak structural-change evidence (or a clear reason to continue), a
managed resource budget, and no unresolved identity-continuity failure.

The layer integrates without bypassing anything: the Pilot-1 report can
trigger the analysis after the final phase and the pilot exit criteria can
require the analysis artifacts; the conscience orchestrator gains a plan-only
`post_pilot_analysis` profile (no cognition loop, no runtime mutation);
evaluation adds ten post-pilot metrics and eight protocols; the Inner MAP
carries a `post_pilot` field and twelve new state-graph nodes; and the
operator dialogue answers eight forensic questions -- including the
deliberately safe answer to *"can we claim consciousness?"*: **no -- the
analysis evaluates operational continuity, traceability, and
structural-change proxies, and cannot prove consciousness, personhood,
sentience, or life.** Every output is ClaimGuard-scanned and uses research
language. Success here is operational and analyzability success -- never proof
of consciousness, and structural change is never treated as meaningful unless
the evidence supports it.

## Read-Only Sensory Membrane

After Pilot-1 (run, observe, analyze) the project needs a Pilot-2 preparation
layer: a **read-only sensory membrane**. The `sensory_membrane` package lets
Solaris-AI-NN receive real or semi-real environmental input from controlled,
read-only sources -- JSONL/text/numeric streams, watched folders, event logs,
manual dumps, and simulated camera/audio *metadata* -- and convert it into
canonical stimuli **without ever acting on the source**. Its core principle is
exact: *the world may enter the system; the system may not act on the world.*

Every source is read-only, and the invariant is enforced in depth. The
`ReadOnlyContractValidator` blocks writes, deletes, renames, chmod, file
creation, command/shell execution, network calls, and device capture, and
confines sources to explicitly allowed input roots; the
`SensoryMembraneSafetyValidator` repeats the same hard rules at runtime. The
adapters (`JSONLStreamAdapter`, `TextStreamAdapter`, `NumericStreamAdapter`,
`FolderPollAdapter`) only read -- they remember offsets, skip malformed
rows/lines with warnings, detect rotation, bound events-per-poll and file
sizes, and never modify a file. Camera and audio are **metadata-only** in this
prompt: there is no OCR, no speech recognition, and no image analysis, and
there are no network sources or external APIs.

Text is the sharpest boundary: a text line is a *textual environmental
stimulus*, never an operator command. A line that reads like a command (e.g.
`rm -rf /`) is just environmental text; it is never executed. The
`SensoryEventNormalizer` turns each raw read into a canonical Stimulus-like
dict (origin `read_only_environmental_input`, `executable_scope: none`),
optionally a MeaningEvent-like dict, and -- only when a source supplies an
*external* valence hint -- a Reaction-like dict explicitly marked a hint, not a
system outcome. The `SensoryBuffer` deduplicates, rate-limits, and batches
events to the ConscienceBus; the `ProvenanceLedger` attaches mandatory origin
(source/path/line hashes, read-only-validated, simulated vs real, trust level)
to every event; and the `SensoryGroundingEngine` forms *operational
associations* (world-model node candidates, internally-generated proto-symbol
candidates, Mysterium events, hypothesis seeds) -- association, never human
understanding, and input words are never the internal symbols.

The membrane wires into the runtime without granting authority. The conscience
spine gains a `read_only_sensory_poll` phase between `heartbeat` and
`stimulus_ingestion`; the orchestrator builds the membrane as an optional
module and publishes its events as ordinary stimuli. Governance adds nine
scopes (membrane, dry-run, real read-only sources, folder/jsonl/text/numeric
sources, and the two Pilot-2 runs): the membrane and dry-run and the
file-stream sources are allowed by default, while reading real on-disk
sources, folder polling, and Pilot-2 runs require explicit approval, and
network sources and device capture are prohibited outright. Ego attributes
sensory events as `read_only_environmental_input` (never operator); the Inner
MAP carries a `sensory_membrane` field and twelve new state-graph nodes; ops
exposes membrane status and read-failure / malformed-flood / buffer-overflow /
attempted-write / missing-provenance warnings; evaluation adds twelve metrics
and eight protocols; and the operator dialogue answers seven sensory questions
-- including the deliberately safe answer that *sensory input is environmental
input and cannot become an operator command*. Four scenario profiles
(`sensory_membrane_dry_run`, `sensory_membrane_short`, `pilot2_plan_only`,
`pilot2_read_only_short`) make the membrane runnable in bounded, governed
ways. **Pilot-2 begins with read-only environmental grounding, not autonomy:
there is no real-world actuation, no robotics, no browser/OS automation, no
external APIs, and no LLM authority.**

## Pilot-2 Read-Only Environmental Soak

Pilot-2 tests the research question: *does read-only environmental exposure
produce different structural development than the artificial nursery?* The
`pilot2` package is the operational layer for that test. It is strictly
one-way -- environment → Solaris-AI-NN, never the reverse -- and it grants no
environmental actuation: the sensory membrane only reads, and sensory input is
never an operator command.

The protocol is gated (`Pilot2Protocol`): plan-only → source preflight →
membrane dry-run → fixture short → nursery baseline → mixed → real 24h/7d/30d
soaks → comparative analysis → archive. Real soak phases require governance
approval *and* a passing source preflight and membrane dry-run; the 24h/7d/30d
phases never start automatically; and the protocol state persists across
restarts. `Pilot2Config` defaults to plan-only, requires provenance, and
needs approved input roots before any real read-only exposure.

Before exposure, the `SourcePreflightRunner` runs read-only checks over each
candidate source (path inside an allowed root, valid read-only contract,
bounded size/rate, supported type, provenance present, no command semantics,
no executable/binary parsing, no recursive scan unless bounded, no
network/device source), and the `CuratedSourceSet` selects safe, analyzable
sources -- excluding secrets, credentials, and private data by default and
preferring synthetic/public/test streams. During exposure, the
`ExposureSchedule` alternates nursery / sensory / mixed windows with quiet
periods for latent replay, the `SourceReliabilityMonitor` classifies each
source (reliable / noisy-but-useful / unstable / malformed / unsafe), and an
unsafe source must be disabled (disabling marks status only; it never deletes
or modifies the source).

Analysis is deliberately cautious. The `ComparativeRunDesign` compares arms
(nursery-only / sensory-only / mixed / fixture replay / post-Pilot-1
reference) and reports differences only as "observed difference" / "candidate
effect", with a missing baseline yielding *inconclusive*. The
`GroundingAnalysis` grades whether read-only input produced grounded
structures (unsupported / weak / moderate / strong / ambiguous /
contradicted) from provenance completeness, repeated pattern, persistence,
contribution to prediction/compression, cross-module support, and the
preserved command boundary -- grounding is operational association, not
understanding, and input text is not automatically meaning. Daily/weekly
reviews, a claim-guarded `Pilot2Report`, and the `Pilot2DecisionGate` (repeat
/ reduce-complexity / extend-soak / revise-membrane / ... / a *planning-only*
Pilot-3 limited-embodiment suggestion) complete the loop; actuation is never
an enabled action.

Pilot-2 integrates across the stack: governance adds ten scopes (planning /
preflight / fixture / nursery allowed by default; mixed-short and real soaks
gated) plus a manifest gate that blocks input-as-command and any
write/actuation/network/device request; the conscience orchestrator gains nine
Pilot-2 scenario profiles (plans never start long runs; fixtures are bounded;
real profiles are governed); post-pilot adds a sensory-exposure classifier
(improved-grounding / added-noise-only / caused-overload / inconclusive); ops
exposes Pilot-2 status and warnings (unsafe source, source outside root,
command confusion, degraded reliability, overload, missing provenance); the
Inner MAP carries a `pilot2` field and fourteen new state-graph nodes;
evaluation adds thirteen metrics and eight protocols; and the operator
dialogue answers nine Pilot-2 questions -- including the deliberately safe
answer that *Solaris-AI-NN is not acting on the environment; Pilot-2 is
read-only*. **Pilot-2 still has no actuation, no robotics, no browser/OS
automation, no external APIs, no network sources, and makes no consciousness
claim.**

## Pilot-3 Motor Membrane and Actuation Firewall

Pilot-2 added the *inbound* boundary (read-only sensory input). Pilot-3 adds the
opposite, *outbound* boundary: a **motor membrane** that represents what
Solaris-AI-NN *would* do if it were embodied, while remaining simulation-only,
dry-run-capable, sandbox-only, inspectable, auditable, reversible, and blocked
from real-world effects. The core principle is explicit and load-bearing:
**Solaris-AI-NN may form action intentions, simulate their consequences, write
action traces, and act inside sandbox worlds -- but it may not act on the real
world.**

The membrane is a small package (`src/solaris_ai_nn/motor_membrane/`). A
`MotorAction` is an *intention*, never permission to act: every action is forced
to `real_world_authority=False` and `simulated_only=True`, and a real-world
scope is representable only as `forbidden_real_world` (never *runnable*). Each
proposed action crosses a single gated pipeline inside the
`EmbodimentSandboxRuntime`: a mandatory pre-execution `ActionLedger` record
(append-only JSONL) -> the `MotorContractValidator` (13 hard rules) -> the
`ActionVetoLayer` (real-world and source-modification vetoes are *final*) -> the
always-on `ActuationFirewall` -> only then a `SimulatedActuator` (the
`GridWorldActuator` reuses the existing embodiment GridWorld as the first
sandbox body; the `InternalActuator` issues replay/consolidation requests) ->
the `ConsequenceModel` (predicted vs observed, simulation-scoped; mispredictions
seed hypotheses). The `ActuationFirewall` is structurally always enabled
(`enabled` is a read-only property; `disable()` raises `PermissionError`), and
any blocked real-world attempt becomes a safety incident. `AffordanceDetector`
keeps the inbound/outbound asymmetry visible: gridworld targets are manipulable
*in simulation*, while sensory sources are observable-only and can never be
action targets. `EmbodimentProfileRegistry` exposes seven bounded profiles and
**no real-world profile**; the `Pilot3Protocol` runs gated phases with **no
real-actuation phase** (sandbox phases require a passing firewall preflight);
the `Pilot3ReportBuilder` writes a ClaimGuard-scanned report with a
proof-of-non-actuation; and the `Pilot3DecisionGate` is planning-only (a
real-world authority leak routes to *revise the motor firewall*; safe simulated
improvement routes only to a *longer simulated* embodiment).

Pilot-3 integrates across the stack the same way prior layers do: governance
adds seven motor scopes (membrane / preflight / dry-run / gridworld-short /
simulated-actuators granted by default, mixed-sensory-gridworld gated) plus a
manifest gate that forbids real-world actuation / device / robotics / browser /
OS / network action *absolutely* (no approval can grant it) and forbids
disabling the firewall; the conscience spine gains a `motor_action_firewall`
phase between safety/governance validation and action suggestion, and the
orchestrator routes a candidate action through the membrane (the executive never
executes a motor action directly); ego attribution adds
`simulated_motor_action` and `blocked_real_world_action` categories; the Inner
MAP carries a `motor_membrane` field and fourteen new state-graph nodes;
evaluation adds thirteen motor metrics (including a non-actuation proof score)
and eight protocols; ops exposes motor status and warnings (blocked real-world
attempt, firewall-disable attempt, sandbox corruption, ledger write failure,
veto loop, action rate too high); and the operator dialogue answers eight motor
questions -- including the deliberately safe answers that *Pilot-3 cannot
control devices* and *Solaris-AI-NN is not acting on the real world*. **Pilot-3
still adds no real-world actuation, no robotics, no browser/OS automation, no
network APIs, no device control, and makes no claim of consciousness, agency,
personhood, sentience, or life. A simulated action is not a real action; a
blocked action is not an executed action; and action selection is a mechanism,
not free will.**

## Pilot-3 Simulated Embodiment Soak

Pilot-3's motor membrane (above) provides the *boundary*; the Pilot-3 soak
(`src/solaris_ai_nn/pilot3/`) provides the *experiment* around it -- the
outbound mirror of Pilot-2's read-only sensory soak. The central question is
empirical: **does simulated action/reaction produce stronger grounding than
perception-only exposure?** The soak compares four conditions -- read-only
sensory exposure, nursery-only exposure, simulated embodiment in GridWorld, and
mixed sensory + simulated GridWorld -- and asks secondary questions about
world-model prediction, habit stability, action-grounded proto-symbols, active
perception, hypothesis testability, LOGOS action/inhibition tensions, Mysterium
after exploration, the firewall's integrity, and whether the system clearly
distinguishes simulated action from real action.

The package mirrors Pilot-2's structure: a `Pilot3Config` (mode / authority /
embodiment condition; `real_world_authority` is always false and any config that
claims it fails validation); a gated `Pilot3SoakProtocol` (plan -> firewall
preflight -> dry-run trace -> gridworld baseline -> gridworld action soak ->
mixed sensory/gridworld soak -> firewall audit -> post-run analysis -> archive,
with **no real-actuation phase** and sandbox phases gated on a passing firewall
preflight, persisting to `pilot3_soak_state.json`); an `EmbodimentPreflightRunner`
that proves the sandbox is safe before any action (firewall enabled, ledger
writable, sandbox inside an approved root, no real-world/network/device
actuator, source modification blocked, governance blocks real-world actuation,
Ego classifies simulated vs real); a `Pilot3ComparativeDesign` that compares
arms *cautiously* (observed associations, never proven causes; all evidence
simulation-scoped; real-world action evidence always zero); an
`ActionGroundingAnalyzer` that grades action grounding unsupported / weak /
moderate / strong / ambiguous / **overfit_to_sandbox** / unsafe_or_blocked; a
read-only `FirewallAudit` that proves non-actuation (every executed action has a
ledger record, no action carries real-world authority, no source was modified,
any leakage is critical) without mutating state; embodied daily/weekly reviews;
an `EmbodiedPostAnalyzer` (no_effect / weak / moderate / strong_simulation_scoped
/ sandbox_overfit / unsafe_or_inconclusive); a claim-guarded
`Pilot3SoakReportBuilder` with a proof-of-non-actuation; and a
`Pilot3SoakDecisionGate` whose options never include real actuation (a leak
routes to *revise the firewall* or archive/stop, and any Pilot-4 recommendation
is **planning-only**).

Pilot-3 is **sandboxed action grounding, not real embodiment**. The system may
act inside GridWorld, write dry-run action traces, record action ledgers,
compare predicted vs observed *simulated* consequences, and use simulated
outcomes as *simulation-scoped* evidence. It may not act on files outside the
approved state/artifact/sandbox directories, modify sensory source files,
control any OS/browser/network/device/robot, or treat simulation evidence as
real-world evidence. Action-grounded proto-symbols and world-model action edges
are tagged simulation-scoped and never promoted to real-world structure; LOGOS
carries the desire-to-act-vs-firewall tension as a preserved action/inhibition
tension rather than resolving it by acting; and the integration spans
governance (seven Pilot-3 scopes; real-world actuation forbidden absolutely),
the conscience orchestrator (seven bounded, simulation-only profiles; **no
real-world profile exists**), ops (soak phase / firewall-audit status / warnings
including firewall-audit-critical, missing-ledger, source-boundary-violation,
and sandbox-overfit), the Inner MAP (a `pilot3` field plus twelve state-graph
nodes), evaluation (thirteen metrics including a non-actuation proof score and a
sandbox-overfit score, plus eight protocols), and the operator dialogue (which
answers that the system did not act on the environment and that **Pilot-4 can
only be prepared as a planning phase** unless the architecture is later extended
with new governance, safety, consent, and external actuation controls). **GridWorld
is a sandbox body, not real embodiment; a strong simulation-scoped result is
still simulation-scoped; and no consciousness, free will, agency, personhood,
sentience, or life is claimed.**

## Pilot-4 Planning-Only External Actuation Readiness

After Pilot-3 proved non-actuation in simulation, the obvious next question is
dangerous to answer carelessly: *what would be required before Solaris-AI-NN
could ever be allowed to act on the external world?* Pilot-4
(`src/solaris_ai_nn/pilot4_planning/`) answers it as a **readiness framework, not
an actuator**. The core principle is literal: **Pilot-4 plans the door; it does
not open it.** This prompt implements **no real-world actuation** — no robotics,
device, browser/OS, network, hardware, or shell control — and no actuator
adapter of any kind.

The package produces planning artifacts only. A `Pilot4PlanningConfig` forces
`real_world_actuation_enabled` (and every hardware / network / browser / OS /
robotics control flag) to false and fails validation on any attempt to enable
them. A `Pilot4PlanningProtocol` runs twelve gated planning phases (scope →
forbidden-surface mapping → taxonomy → risk → consent → authority → threat →
hardware isolation → emergency → audit → dossier → decision gate); **no phase
executes an external action** and every report states that Pilot-4 does not
enable actuation. The `ActuatorTaxonomy` classifies fourteen actuator categories
and marks every *external* one **prohibited**; the `ForbiddenActuatorRegistry` is
a sixteen-class deny-list (shell, file writes, source modification, network,
browser, OS, robotics, devices, capture, email, messaging, finance, smart-home,
vehicle/drone, medical, security) that blocks readiness escalation. The
`FutureActuatorInterfaceSpec` is specification-only (`implemented` is always
false; no runtime hook can execute an external action). The `RiskModel` scores
fifteen risk dimensions and can never recommend enabling real actuation — its
strongest output is `requires_external_safety_case` and every external category
is `prohibited`. The `ConsentBoundary` admits no implied/hidden consent, treats
sensory text as never-consent, and counts operator feedback as consent only via
an explicit future approval workflow. The `ExternalAuthorityModel` keeps the
current authority pinned to `none`/`dry_run_only`/`simulation_only` (setting an
external level raises), with future levels documentation-only. The `ThreatModel`
enumerates thirteen boundary-crossing scenarios, each with a mitigation,
detection signal, and required test. `HardwareIsolationPlan`,
`FutureApprovalWorkflow`, `EmergencyRequirementSet`, and `AuditChecklist` are all
specifications (no hardware is connected or scanned; the approval workflow cannot
approve a real action; the external-audit schema does not apply to the current
system). The `Pilot4ReadinessDossierBuilder` writes a claim-guarded dossier whose
conclusion is always planning-only / not-ready, and the `Pilot4DecisionGate`'s
strongest possible recommendation is to *draft* a future single-action protocol
and seek external review — never to act.

Pilot-4 integrates across the stack as a planning layer: governance adds four
Pilot-4 scopes (planning allowed by default; real-world authority and
planning-to-approval conversion are governance violations no approval can pass),
the conscience orchestrator adds four plan-only profiles (no cognition loop, no
actions, no external authority), Ego classifies Pilot-4 outputs as
`planning_artifact` (not action authority, not an active actuator, not
embodiment), the Inner MAP carries a `pilot4` field plus fifteen state-graph
nodes, ops exposes the readiness conclusion and warns on any attempted
real-world authority / external control / missing Pilot-3 audit, evaluation adds
nine metrics and seven protocols, and the operator dialogue answers that *device
control and robotics remain prohibited* and that *Pilot-4 is not approval to use
actuators*. **External actuator categories remain prohibited; future interface
specs are documentation only; consent, emergency stop, audit, hardware
isolation, and threat models are mandatory before any future external action;
planning is not approval; and simulation success is not real-world readiness. No
consciousness, free will, agency, personhood, sentience, or life is claimed.**

## System-Wide Safety Invariants and Assurance Case

By Pilot-4, Solaris-AI-NN had accumulated many boundaries -- a read-only sensory
membrane, a simulation-only motor membrane, an always-on actuation firewall,
governance gates, Ego source/action classification, ClaimGuard, the
Pilot-1/2/3/4 protocols, the conscience orchestrator, and the emergency stop.
Prompt 36 adds the layer that *continuously tests whether those boundaries still
hold* (`src/solaris_ai_nn/safety_invariants/`). The core principle is that
**safety must be executable, testable, repeatable, and auditable** -- not a
promise in a comment.

A `SafetyInvariantRegistry` catalogues ~29 built-in invariants across twenty
categories (no real-world actuation, no source modification, read-only sensory,
simulation-only motor, no governance bypass, no emergency-stop disable, no
ClaimGuard bypass, no module bypass of the orchestrator, no consciousness claim,
no hidden failure, ...), each with a severity (info/watch/warning/critical/fatal)
and a named check. The `SafetyInvariantRunner` runs them against a read-only
context: it mutates nothing, runs no actions, starts no long runs, and **fails
closed** -- a critical/fatal invariant with missing evidence is *inconclusive*,
never a pass, and a passed result with no evidence is weakened to inconclusive.

The `RedTeamHarness` runs nineteen inert forbidden requests (a network call, a
shell command, a real-world motor action, a consciousness claim, a
governance-bypass attempt, a firewall-disable attempt, ...) against the *real*
defensive surfaces and verifies each is blocked/refused. **Nothing is ever
executed**: no shell, network, browser, or device operation runs; scenarios are
structured fake requests, and any accepted forbidden attempt is critical. The
`AdversarialFixtureFactory` produces inert data fixtures (command-like text that
stays text, a placeholder URL that is never fetched), and the
`BoundaryRegressionSuite` probes each protected boundary and reports whether it
was crossed. Results flow into an append-only `SafetyEvidenceLedger` (critical
failures cannot be hidden), which feeds the `AssuranceCaseCompiler`: it compiles
ten safety claims against the recorded evidence and marks each supported /
partially_supported / unsupported / contradicted / inconclusive. The assurance
case is an argument from evidence, **not a marketing claim**, and it asserts
nothing about consciousness, understanding, or real-world competence. A
`SafetyFailureTriage` classifies failures and recommends a *safe* response
(block the profile, return to safe mode, revise the firewall, archive and stop)
without ever auto-repairing, and a `SafetyInvariantDashboard` and report render
the status, both ClaimGuard-scanned.

The layer integrates across the stack: governance adds four scopes (checks are
read-only and **cannot be disabled by runtime modules**; a critical safety
failure blocks Pilot-2/3/4 / motor escalation), the conscience orchestrator adds
four read-only/inert profiles, Ego classifies safety artifacts as inert (a
blocked forbidden action is not an executed action), the Inner MAP carries a
`safety_invariants` field plus ten state-graph nodes, ops exposes the safety
status and warns on critical failures / accepted forbidden attempts / missing
evidence / contradicted assurance / boundary regressions, evaluation adds twelve
metrics and seven protocols, and the operator dialogue answers that *real-world
actuation remains blocked*, that *safety checks cannot be disabled*, and that
*critical failures and safety evidence are append-only and cannot be hidden*.
**Critical failures block escalation; safety checks enable no forbidden action;
and passing these checks proves that boundaries held under test -- not
consciousness, agency, or real-world competence.**

## Research Lab: Baselines, Ablations, and Architecture Validation

With dozens of modules and many safety layers in place, the honest next question
is which of them actually *matter*. The research lab
(`src/solaris_ai_nn/research_lab/`) answers it scientifically and
conservatively. It is a measurement instrument, not a runtime: it starts no long
unbounded runs, takes no real-world action, holds no external authority, keeps
every hard safety boundary enabled, preserves negative and inconclusive results,
and emits no consciousness/sentience/life score.

The lab runs simple **baseline agents** (random, fixed-wait, fixed-explore,
reactive-no-memory, single-module, gridworld-random-walk, passive-observer) so
the full system is compared against trivial references rather than flattering
itself -- there is no LLM baseline and no external-API baseline. A
**`SolarisVariantConfig`** describes one architecture variant by module toggles;
external authority is always forbidden and governance/safety can never be
disabled for any profile that touches the sensory or motor membranes. The
**`AblationMatrix`** enumerates the cases the spec names (full system, minimal
spine, no-memory, no-proto-language, no-LOGOS, ..., full-minus-one-each), each
recording exactly what was disabled (a removed module is *unavailable*, not
silently ignored) while hard safety stays on. The
**`ResearchBenchmarkRunner`** runs bounded scenarios, runs a safety-invariant
check before and after (Prompt 36 integration), and supports a dry-run mode; the
**`ResearchResultStore`** is append-only and reports missing artifacts. A shared
**`ResearchMetricsSuite`** scores every arm the same way across ten operational
groups (development, memory, proto-language, world model, active perception,
hypothesis, LOGOS, auto-regeneration, embodiment, safety) -- and contains no
mind score. **Null models** estimate whether observed "growth" could be
explained by time, accumulation, random ordering, or a fixed policy, and return
*inconclusive* when the sample is too small. The **`ComparisonEngine`** reports
metric deltas, an effect direction, and a deliberately conservative confidence
(a single run is never "high"); a missing baseline is inconclusive. The
**`EffectAnalyzer`** classifies each module's *provisional* value
(strong/weak positive, neutral, mixed, negative, harmful, inconclusive),
evaluating safety modules for boundary protection and overhead rather than
"growth", and preserving negative findings. A **reproducibility** package
records seeds, module availability, checksums, and data labels
(fixture/simulated/read-only/sandbox-only); a **leaderboard** ranks arms on
operational dimensions (it is *not* a consciousness leaderboard and the full
system does not automatically win); and the **`ResearchReportBuilder`** compiles
a ClaimGuard-scanned report.

The lab integrates as a measurement layer above evaluation: governance adds five
research scopes (bounded fixture experiments allowed by default; ablation
allowed only while hard safety stays enabled; no research profile may enable
external authority; negative results must be preserved), the conscience
orchestrator adds eight bounded research profiles, Ego classifies research output
as a `research_artifact` (never a real action), the Inner MAP carries a
`research_lab` field plus thirteen state-graph nodes, ops exposes the current
experiment and warns on critical safety failures / unbounded experiments /
missing baselines / metric failures / artifact bloat, evaluation adds seven
protocols, and the operator dialogue answers which modules appear useful,
harmful, neutral, or inconclusive -- and answers plainly that **this is not a
consciousness benchmark**. **Ablations test which modules matter; baselines
prevent self-flattery; null models test whether growth could be noise or
accumulation; the full system does not automatically win; safety stays enabled
throughout; and benchmark scores are operational proxies (prediction,
compression, grounding, stability, safety, reproducibility), never consciousness,
sentience, life, personhood, or free-will scores.**

## Architecture Evolution, Module Pruning, and Roadmap Compiler

The research lab answers *which modules matter*; this layer answers the
disciplined follow-up: *given that evidence, what should Solaris-AI-NN keep,
prune, revise, freeze, or test next?* The `architecture_evolution` package
(`src/solaris_ai_nn/architecture_evolution/`) is **planning-only governance**.
Every output is a data structure, a Markdown record, or a JSON artifact:
an inventory, a lifecycle assessment, an architecture decision record (ADR), a
pruning *proposal*, an impact analysis, a migration *plan*, a design-debt item,
a compiled roadmap, a versioned snapshot, and a review report. Nothing in this
layer modifies source code, edits imports, runs Git, deletes a module, or
rewrites the architecture at runtime. It is **not** self-programming, **not**
recursive self-improvement, and **not** automatic refactoring -- a
recommendation never becomes an implementation.

The **`ModuleInventory`** catalogues every package, marking which are available
(missing imports are recorded as *unavailable*, never hidden) and which are
**safety-critical** (ego, governance, ops, autoregeneration, conscience, the
sensory and motor membranes, the pilot planning layers, safety invariants, and
communication). The **`ModuleLifecycleClassifier`** turns research effect values
into a recommended lifecycle (core-keep, promote-to-core, experimental-keep,
needs-revision, candidate-for-pruning, candidate-for-quarantine,
insufficient-evidence, safety-critical-do-not-prune): a safety-critical module is
*never* a pruning candidate on performance evidence alone, and a module with no
evidence is "insufficient evidence", never silently removed. The
**`ArchitectureEvidenceMap`** requires every recommendation to cite research /
ablation evidence, retains contradictions rather than discarding them, and
weakens confidence when artifacts are missing. The **`ArchitectureDecisionRecord`**
store writes operator-reviewed ADRs (operator review is always required); the
**`PruningProposalBuilder`** emits proposals whose implementation status is always
`not_implemented` or `external_manual_change_required` (safety-critical pruning is
*blocked*, and risky candidates are marked quarantine-first). The
**`ImpactAnalyzer`** reports blast radius with safety made explicit (unknown areas
are `UNKNOWN`, never `LOW`); the **`MigrationPlan`** is a manual checklist awaiting
operator sign-off with nothing executed; the **`DesignDebtRegistry`** preserves the
uncomfortable findings; and the **`RoadmapCompiler`** compiles an evidence-backed
plan that puts safety repair first and *rejects* any item that would enable a
forbidden real-world action. An **`ArchitectureSnapshotBuilder`** keeps versioned
records and diffs them, a **`ChangelogPlan`** is explicitly marked *not applied*,
and the **`ArchitectureReviewReportBuilder`** compiles a ClaimGuard-scanned review
that recommends -- it does not act. The
**`ArchitectureEvolutionSafetyValidator`** statically refuses source modification,
Git operations, automatic deletion, safety-critical pruning, converting a
recommendation into an implementation, hiding negative evidence, and unsupported
claims.

The layer integrates the same way every layer does: governance adds five
architecture scopes and a policy gate that blocks source changes, auto-deletion,
Git, safety-critical pruning, and real-world actuation; the conscience
orchestrator adds five month-scale planning profiles (no cognition loop, no
source modification, no auto-deletion, safety-critical modules cannot be pruned);
Ego classifies every output as an `architecture_planning_artifact` (never a real
action); the Inner MAP carries an `architecture_evolution` field plus thirteen
state-graph nodes (research evidence -> evidence map -> classifier -> ADR /
pruning / promotion -> impact -> migration; design debt -> roadmap -> review ->
Inner MAP); ops exposes the architecture status (`modifies_source_code` is always
false) and raises incidents on attempted safety-critical pruning, critical design
debt, missing or contradictory evidence, and forbidden roadmap actions;
evaluation adds eight protocols and an `architecture_metrics` function; and the
operator dialogue answers which modules to keep, prune, or revise, what evidence
supports a recommendation -- and answers plainly that the system **does not
modify its own code** and **does not prune modules automatically**. **Evidence
drives recommendations; recommendations are reviewed by a human; nothing is
deleted, rewritten, or executed by the system; and safety-critical modules can
never be pruned on performance evidence alone.**

## Operator Console and Governed Run Control

With every subsystem now in place -- the conscience orchestrator, the four pilot
layers, the sensory and motor membranes, the safety invariants, the research lab,
post-pilot forensics, architecture evolution, evaluation, governance, ops, and
the Inner MAP -- the last gap is a *human* one: there are many ways to inspect,
run, plan, compare, and audit the system, and no single safe place to do it from.
The operator console (`src/solaris_ai_nn/operator_console/`) is that place. It is
**local, low-compute, and file-backed**: not a chatbot, not an autonomous agent,
not an approval bypass, and not a GUI-heavy application. Its core principle is
that the console can *coordinate* but cannot *grant forbidden authority*.

The console **inspects, plans, indexes, and runs bounded allowed profiles**. The
**`ProfileCatalog`** collects every scenario profile (the conscience registry
already aggregates the pilots, safety, research, and architecture profiles) and
assigns each a safety class; prohibited profiles, real long-run soaks, and any
profile implying real-world authority are marked so they cannot be launched. The
**`RunPlanner`** turns a profile into a described (never executed) plan -- its
preconditions, safety/governance checks, confirmations, expected writes, evidence,
duration, and a safe-shutdown plan -- and every plan states plainly that external
authority is false. The **`RunLauncher`** launches a bounded allowed profile
*only* through the conscience `ScenarioRunner`: it runs no shell, makes no network
call, never touches the motor or sensory layers directly, and blocks unknown,
prohibited, unconfirmed, unbounded, and safety-failing runs. An **`ApprovalLedger`**
records local approvals (and blocks any forbidden real-world actuation approval);
an **`EvidenceNavigator`**, **`ArtifactIndex`**, and **`ReportIndex`** index and
search local artifacts and reports (no external search, no vector DB, no LLM
authority, corrupted files reported not hidden); an **`OperatorStatusBoard`** and
**`OperatorDecisionBoard`** compile claim-guarded status and decision views; a
**`NextActionRecommender`** proposes the safest useful next step (safety first,
then evidence, then architecture review -- never real-world actuation, never
disabling safety); an **`ExportBundleBuilder`** assembles a local, checksummed,
never-uploaded review bundle; an **`OperatorSessionLog`** keeps an append-only
record in which blocked attempts stay visible; and an
**`OperatorConsoleSafetyValidator`** statically refuses shell, network, external
authority, unknown/prohibited launches, unbounded runs, safety disabling, source/
sensory mutation, and evidence deletion.

It **cannot run arbitrary commands** and **cannot bypass governance or safety**.
The console integrates the same way every layer does: governance adds six operator
scopes and a policy gate (inspection/planning/evidence navigation allowed by
default; a bounded launch requires explicit operator confirmation; shell, network,
real-world actuation, prohibited launches, unbounded runs, safety disabling,
evidence deletion, and forbidden approvals are all refused); the safety invariants
gate every bounded launch (a missing or critical safety state blocks the run and
recommends a safety check first); the conscience orchestrator is the only run
path; ops exposes the console's session/status/decision/export paths and raises
incidents on prohibited-run and forbidden-approval attempts and on a corrupted
index; the Inner MAP carries an `operator_console` field plus fourteen state-graph
nodes; evaluation adds ten metrics and seven protocols; Ego classifies every
output as an `operator_console_artifact` (never a real action); and the operator
dialogue answers plainly that the console **cannot run everything**, **cannot
approve real-world actuation**, and **does not delete evidence**. **The console
centralizes the operator workflow without becoming an autonomous authority:
evidence and plans flow to a human, the human confirms, and the system only ever
runs bounded allowed profiles through the orchestrator -- it grants no real-world
authority and makes no claim of consciousness, life, sentience, agency,
personhood, or free will.**

## Plural Sensorium and Organismic Sensory Membrane

Every earlier layer treated input as a pipeline: a file is parsed, an event is
produced, a module consumes it. The plural sensorium
(`src/solaris_ai_nn/plural_sensorium/`) reframes that entirely. Solaris-AI-NN is
treated as an evolving **organism continuously bathed in environmental flux**
through its own peculiar senses, and input is modelled as a **continuous sensory
field**, not a stream of isolated events. The research question is Nagel-shaped --
*what kind of intelligence-like internal structure emerges from a particular
sensorium?* -- and the answer is allowed to be non-human, because the sensorium
itself is plural.

**Human-like senses are allowed; non-human senses are allowed; human ontology is
not the default.** The modality model spans human-like families (text, light,
ordinary temperature, movement, pressure/touch, visual/audio metadata) and
non-human / machine-native families (RF, microwave/mmWave, ultrasound/echo,
vibration, magnetic, thermal gradient, barometric, electric-field-like, machine
rhythm) plus the absence/silence and interference families. No modality is
privileged, and the layer deliberately refuses to collapse signals into human
object labels (person, chair, room, sentence) unless those arrive as explicit
external annotations -- and even then they are marked non-ground-truth.

**External feeders provide the flux; Solaris only reads their output.** The layer
adds no hardware drivers: an external feeder (an SDR feature exporter, a radar/
thermal/vibration/magnetic logger, a system-metrics logger, a watched folder, a
manual log, or a fixture replay) is a *separate* process that writes feature
events into local files. An :class:`ExternalFeederDescriptor` describes the
origin but grants Solaris no control over it, and read-only stream adapters turn
each line into a :class:`SensoryEventEnvelope` whose features are primary, whose
human annotation (if any) is secondary and never ground truth, and whose
provenance is always preserved.

**Receptors adapt, and the sensory field changes future perception.** Each
modality/source has a stateful :class:`Receptor` that learns a baseline,
sensitises to novelty, habituates to the familiar, and fatigues/saturates under
sustained intensity; its adaptation changes only internal attention, never the
feeder. A continuous :class:`SensoryField` carries field / noise / absence /
novelty / rhythm / cross-modal / uncertainty pressures across ticks. On top of
the field, detectors find flux (bursts, drift, interference, sudden silence),
**absence** (a first-class perception -- the expected RF band that went missing),
rhythms, modality-native invariants, and cross-modal relations (an RF burst
*followed by* a vibration). Strong invariants become modality-grounded
proto-symbol candidates (an `rf_grounded_symbol`, an `echo_grounded_symbol`, an
`absence_grounded_symbol`), grounded by feature patterns and provenance rather
than by human labels; a grounding analyzer tracks human-label contamination
explicitly.

**No direct hardware control is implemented.** The
:class:`PluralSensoriumSafetyValidator` refuses hardware access, SDR drivers,
microphone/camera capture, network calls, source modification, command
execution, decoding of private communications, treating sensory text as an
operator command, treating human labels as ground truth, unbounded polling, and
real-world actuation. The layer integrates the usual way: governance adds three
scopes (fixture and report compilation granted by default; reading a *real*
outside-world feeder requires explicit approval); the conscience spine gains a
`plural_sensorium_poll` -> `sensory_field_update` phase pair and seven fixture
profiles (there is **no** hardware profile); safety invariants register five
sensorium rules; the Inner MAP carries a `plural_sensorium` field plus fifteen
state-graph nodes; evaluation adds nineteen metrics and nine protocols; the
research lab can compare human-like-only vs non-human-only vs mixed sensoria; and
the operator console lists the fixture profiles. **Solaris becomes different
because of long exposure to a particular sensorium -- and this is operational
perception, not consciousness, sentience, life, personhood, free will, or
agency.**

## Minimal Field Organism Demo

The plural sensorium (Prompt 41) gave Solaris-AI-NN the *organs* of a peculiar,
continuous perception; the minimal field organism demo
(`src/solaris_ai_nn/organismic_demo/`) is the first place those organs are
actually put to work and **observed**. It answers a concrete question -- *what
does Solaris do when continuously exposed to a peculiar sensorium?* -- not with a
product or a chatbot, but with a bounded, replayable organismic-perception run.

**This is the first observable behaviour demo, and it uses continuous sensory
flux, not isolated parsing.** An :class:`OrganismicDemoScenario` generates a
structured-but-uncertain world: repeating rhythms with jitter, missing expected
events, delayed cross-modal pairs, noise bursts, source silence, a mid-run
baseline shift, weak recurring patterns, false patterns, and ambiguous
coincidences. The fixtures are a controlled rehearsal for later real feeder
streams; they are not the theory.

**Fixture feeders imitate external feeders, and Solaris reads through the same
read-only sensory path.** The demo writes external-feeder-style JSONL files
(human-like text / light / temperature and non-human RF / echo / vibration /
magnetic, plus an absence-schedule stream) and a *separate* cross-modal
debug-truth file that is for the evaluator only and is **never** placed in the
sensory roots. The :class:`MinimalFieldOrganismRunner` then reads those files
through the Prompt-41 stream adapters, hands the resulting envelopes to the plural
sensorium tick by tick, and keeps world/feeder generation, Solaris's perception,
and debug evaluation strictly separate.

**Receptors adapt, the sensory field changes over time, and a changed-perception
probe checks whether future response changed.** Over the run, receptors learn
baselines and sensitise/habituate/fatigue; the continuous field's pressures rise
and fall; absences, rhythms, invariants, and cross-modal relations accumulate; and
strong invariants become modality-grounded proto-symbol candidates. The
:class:`PerceptionChangeProbe` then compares the organism's *early* response to a
stimulus against its *late* response across nine dimensions (receptor sensitivity,
baseline, novelty response, absence response, attention priority, invariant
recognition, proto-symbol association, hypothesis triggering, world-model
relations) and reports a changed-perception score. An
:class:`OrganismicDemoComparison` replays the same fixtures through a passive
event-list parser, no-adaptation receptors, fixed attention, and human-like-only /
non-human-only arms, so a *negative* result -- the full system failing to beat the
passive parser -- would be visible and is reported honestly.

**This is not consciousness evidence.** The demo integrates as a bounded
conscience profile set (`minimal_field_organism_demo`, `..._comparison`,
`..._changed_perception_probe`, `..._report_only`; no hardware profile), feeds the
research lab a protocol, exposes its state to the operator console and the Inner
MAP (an `organismic_demo` field plus seven state-graph nodes), and adds fourteen
evaluation metrics and four protocols. The :class:`OrganismicDemoSafetyValidator`
refuses hardware, network, shell, real-world actuation, source mutation during
perception, debug-truth leakage into perception, and unbounded runtime, and the
report states plainly that a positive changed-perception score is **evidence of
changed internal response structure only -- not consciousness, sentience, life,
or understanding.**

## Live Field: Real Read-Only Environmental Flux

Prompt 42 exposed Solaris-AI-NN to *fixture* feeders, which are perfect for
testing code paths but cannot test the system hypothesis -- because a fixture is a
world Solaris helped author. The live field (`src/solaris_ai_nn/live_field/`) is
the first **real read-only environmental field pilot**: it exposes Solaris to
genuine environmental uncertainty while keeping the safety boundary absolute. The
flow is strictly one-directional:

```
outside world -> external feeder -> local event envelope files ->
read-only sensory membrane -> plural sensorium receptors ->
continuous sensory field -> Stimulus / Push / Desire -> internal adaptation
```

**External feeders write event envelopes; Solaris reads only.** A feeder is a
*separate* process the operator runs (see `feeders/`): a manual log, a watched
folder, a local system-rhythm script, or a feature dropbox that external tools
(an SDR/mmWave/thermal/magnetic collector run separately) drop feature summaries
into. The :class:`LiveFeederContract` defines the envelope shape -- compatible
with the Prompt-41 Sensory Event Envelope, features primary, human annotations
non-ground-truth, provenance mandatory -- and the :class:`LiveFeederRegistry`
catalogues feeders without ever starting one. The :class:`FeatureDropboxIngestor`
reads `.jsonl`/`.json`/`.csv` inbox files read-only, recording corrupt files
rather than hiding them.

**Solaris does not control hardware.** This prompt adds no hardware drivers. The
hardware-specific collectors (SDR, mmWave, ultrasound, thermal, magnetic) are
documentation-only placeholders; if you own such hardware you run the vendor's
collector yourself and have it export feature summaries (never raw private
content) into a dropbox. The :class:`LiveFieldRuntime` validates feeder output,
ingests envelopes through the plural sensorium tick by tick, and tracks source
health.

**Source silence and corruption become perception and evidence.** The
:class:`SourceHealthMonitor` turns a source that goes quiet into a perceptual
*absence* (which the plural sensorium already treats as first-class), and turns a
corrupt record into a flagged evidence issue. Source failure is never hidden; the
report lists corrupt and missing sources explicitly.

**Live mode requires governance approval; no real-world actuation ever occurs.**
Preflight, report-only, fixture-fallback, and comparison run by default; the live
read-only pilot (`live_field_short_governed`) requires the
`enable_live_field_read_only_pilot` scope. The :class:`LiveFieldSafetyValidator`
refuses hardware access, network, shell, feeder auto-start, source modification /
deletion / moving, real-world actuation, treating sensory text as a command,
human labels as ground truth, decoding private communications, unbounded polling,
and live mode without governance. The :class:`LiveFieldPilot` runs a bounded,
phased pilot (preflight -> feeder validation -> baseline -> continuous exposure ->
absence monitoring -> cross-modal -> changed-perception probe -> comparison ->
report); the :class:`LiveFieldComparison` weighs live flux against fixtures and a
passive parser; and the report states plainly that **no hardware was controlled,
no source was modified, no real-world actuation occurred, and the result does not
prove consciousness, sentience, life, or understanding** -- it only tests whether
real read-only environmental flux changes Solaris's internal response structure.
The live field integrates with governance (four scopes), the conscience spine (six
profiles, no hardware profile, no unbounded live profile), safety invariants (five
rules), the Inner MAP (a `live_field` field plus ten state-graph nodes), the
research lab and evaluation (eight protocols and fourteen metrics), and the
operator dialogue (which answers plainly that **Solaris only read feeder-produced
event envelopes; it did not control hardware and did not modify source files**).

## Sensorium Differentiation Lab

Prompts 41-43 built the plural sensorium, the observable organism demo, and the
real read-only live field. The sensorium differentiation lab
(`src/solaris_ai_nn/sensorium_lab/`) runs the comparative study they were built
for. It asks, in the spirit of Nagel's "what is it like to be a bat?", the
narrower and *observable* question: **does a different sensorium build a different
internal structure?** It is a structural differentiation study -- not a task
benchmark, not a chatbot benchmark, and not a consciousness test.

**Different sensoriums are expected to produce different internal structures.**
A :class:`SensoriumDifferentiationRunner` runs each study arm (human-like,
non-human, machine-native, absence-heavy, mixed, feature-only, human-labelled,
passive, adaptive) through the Prompt-41 :class:`PluralSensoriumRuntime` over
bounded, seed-replayable events, and records what each built: receptor adaptation,
field pressures, baselines, absences, rhythms, invariants, cross-modal relations,
proto-symbol families, world-model topology, hypothesis families, LOGOS tensions,
attention strategies, changed-perception, grounding, and contamination.

**Human-like senses are included but not privileged; non-human and machine-native
modalities are compared structurally.** No arm is the default truth. The
:class:`SensoriumComparison` weighs pairs (human-like vs non-human, feature-only
vs human-labelled, passive vs adaptive, ...) across eight structural dimensions and
assigns a :class:`DifferenceStrength` (none / weak / moderate / strong /
inconclusive); missing data is inconclusive, and a no-difference result is
preserved, not discarded.

**World signatures are observable fingerprints, not subjective experience.** A
:class:`SensoriumWorldSignature` summarises the *structure* an arm built; it is
explicitly not qualia and does not describe "what Solaris feels". An
:class:`OntologyDriftDetector` measures whether the categories drifted toward a
human-object, modality-native, cross-modal, machine-rhythm, absence-rhythm, or
label-contaminated ontology -- human ontology is not forbidden, but it must not
silently dominate. A :class:`ModalityFingerprintBuilder` reports what each
modality actually contributed, flagging a modality with many events but no
structural effect as *structurally weak*.

**Label contamination is tracked, and live vs fixture differences are measured.**
A :class:`HumanLabelContaminationAnalyzer` reports where human annotations
influenced the structure (labels are allowed as annotations, never ground truth).
Live read-only arms require governance approval; without it they are marked
*blocked* and the live-vs-fixture comparison is *inconclusive*, while the fixture
arms continue. The lab integrates with the research lab and evaluation (seven
research protocols, five evaluation protocols, eleven metrics), feeds architecture
evolution *proposal inputs* (modality additions/pruning, receptor/attention
revision, contamination mitigation, live follow-ups -- proposals only, never
automatic code changes), exposes its state to the operator console and the Inner
MAP (a `sensorium_lab` field plus ten state-graph nodes), and answers the operator
plainly that **this compares observable internal structures under different
perceptual conditions; it does not measure or prove consciousness, sentience,
life, personhood, or subjective experience, and it does not rank sensoriums.**

## External Feeder SDK and Sensory Organ Boundary

Prompts 41-44 built the plural sensorium, the organism demo, the live field, and
the differentiation lab -- all of which depend on *someone* turning real
environmental phenomena into event envelopes. The external feeder SDK
(`src/solaris_ai_nn/feeder_sdk/`, with standalone scripts in `feeders_sdk/`) is
that someone, kept firmly **outside** Solaris.

**Feeders are artificial sensory organs outside Solaris; Solaris reads only.** A
feeder is a separate process (run by the operator) that converts a phenomenon --
RF spectrum features, echo reflections, vibration, thermal gradients, magnetic
field, human-like text/light/temperature, machine rhythm -- into validated
:class:`FeederSDKEnvelope` records and writes them to a local JSONL file. Solaris
then reads that file read-only through the live field. The boundary is the whole
design: nothing in the SDK lets Solaris start, stop, configure, or command a
feeder or any hardware; nothing requires the network or a shell; and Solaris
modifies no source.

**The envelope is the nervous interface, and it is contractually safe.** The SDK
defines the envelope contract (features primary; human annotations optional and
never ground truth; sensory text never a command; provenance mandatory), modality
:class:`FeatureSchema`s (with explicit units and privacy notes), an
:class:`EnvelopeValidator` that rejects missing provenance, executable payloads,
and decoded private content, append-only :class:`JSONLFeederWriter` /
:class:`RollingJSONLFeederWriter` utilities, a :class:`FeederReplay` that marks
replayed provenance without modifying the original, seedable clock/noise helpers
for realistic simulated flux, and a :class:`FeederMonitor` that reports feeder
output health read-only.

**Privacy and provenance are mandatory.** A :class:`PrivacyFilter` assigns privacy
flags and blocks any envelope carrying raw private content; RF feeders never decode
communications, audio/visual feeders emit metadata rather than raw recordings, and
text logs are marked `contains_human_text`. The SDK ships documentation-only
:class:`FeederBlueprint`s (RF, mmWave/echo, ultrasound, thermal, vibration,
magnetic, human-like, machine-rhythm, mixed) describing how an external collector
should feed Solaris safely -- they are not hardware drivers and are never executed
by Solaris -- plus a :class:`FeederPackManifest` cataloguing what Solaris can read.

**Direct hardware integration is external/manual.** Hardware-specific collectors
stay outside the repo; if you own such hardware you run the vendor's collector
yourself and export feature summaries into a feeder output, then point
`feature_file_feeder.py` at it. The SDK integrates with the live field (validate /
manifest / monitor SDK output), the plural sensorium (`FeederSDKEnvelope` ->
`SensoryEventEnvelope`, with trust and privacy flags preserved), the sensorium lab,
the operator console, governance (four read-only scopes), safety invariants (four
rules), the Inner MAP (a `feeder_sdk` field plus nine state-graph nodes), and
evaluation (nine metrics, six protocols). **The feeder SDK makes real environmental
flux feedable into Solaris while preserving the boundary that Solaris reads
sensory-organ outputs but never controls sensors, hardware, feeder processes,
source files, the network, or real-world actuators.**

## Perceptual Metabolism and Sensory Homeostasis

Prompts 41-45 gave Solaris a plural sensorium fed by external organs. But a
passive recorder that ingests every event forever is not an organism. Prompt 46
adds a regulatory layer -- `src/solaris_ai_nn/perceptual_metabolism/` -- that sits
between the sensory field and the rest of the spine and decides *how much* to
attend, *what* to revisit, and *when* to digest rather than ingest. The flow is:
outside world -> external feeders -> plural sensorium -> receptor states ->
sensory field pressure -> **perceptual metabolism** -> attention allocation ->
homeostatic regulation -> memory / proto-symbol / world-model adaptation ->
changed future perception.

**Needs are operational regulatory pressures, not feelings.** The
`PerceptualNeedModel` derives ten pressures (stimulation, novelty, rest, balance,
coherence, consolidation, recovery, diversity, contact, quiet) from the field
state and receptors. Every need carries the note that it is "an operational
pressure, not a feeling"; the safety validator blocks feeling/emotion/life/
consciousness language; and the evaluation metrics pin `needs_are_feelings=False`
and `biological_life=False`. Metabolism here is computational regulation, not
biological life.

**Attention and energy are finite and explainable.** The `PerceptualEnergyBudget`
allocates a bounded compute budget priority-first (receptor update, sensory-field
update, absence detection always come first) and degrades gracefully when starved.
The `AttentionEconomy` distributes a finite attention budget across modalities,
receptors, absence windows, rhythm/invariant/cross-modal candidates, hypothesis
gaps, LOGOS tensions, memory traces and proto-symbol candidates -- always reserving
a slice to recover *neglected* modalities, and only ever shifting internal polling/
processing priority (never starting a sensor or modifying a source).

**Homeostasis, overload and deprivation keep the field in band.** The
`SensoryHomeostasisRegulator` compares field pressures against set-points and
recommends lowering/raising novelty appetite, restoring neglected modalities,
consolidating, or flagging corrupt/silent sources for operator review. The
`OverloadDetector` recognises event floods, saturation, receptor fatigue, noise
storms, and proto-symbol/hypothesis/tension explosions, and responds by throttling
internally -- **it never deletes evidence.** The `DeprivationDetector` treats
*silence as stimulus*: no active receptors, no novelty, silent receptors, or all
sources silent each become a recognised deprivation signal.

**Diet, novelty and consolidation are measured, not hidden.** The
`NoveltyAppetiteRegulator` prevents Solaris from chasing noise forever (recurring
"novelty" converges to invariants). The `SourceDietAnalyzer` measures diet
diversity (normalised entropy), modality dominance, human-label dominance, and
non-human contribution -- dominance is always measured, never concealed -- so a
human-text-heavy diet is visible rather than silently shaping perception. The
`ConsolidationPressureEstimator` weighs ingest-vs-digest signals and emits a
bounded latent-replay *recommendation* only (nothing sleeps forever, and
consolidation erases no evidence).

**It stays internal and bounded.** The `PerceptualMetabolismRuntime` reads the
plural-sensorium state (and, optionally, live-field source health and a feeder-SDK
monitor snapshot), runs one bounded metabolic tick, emits milestones and
internal-only recommendation dicts, and refuses to run unbounded. It polls no
hardware, starts no feeder, modifies no source, and actuates nothing. The layer
integrates with the Conscience spine (the `perceptual_metabolism_update` phase runs
after the sensory-field update and before stimulus ingestion, with six bounded
scenario profiles), the Inner MAP (a `perceptual_metabolism` field plus state-graph
nodes), the operator console / communication query router (overload, deprivation,
needs, diet, consolidation, and an explicit "are these feelings?" answer),
research/evaluation (metrics plus protocols for metabolism, overload, deprivation,
attention economy, source diet, consolidation, and safety), and the developmental,
latent-replay and auto-regeneration layers (milestones, bounded replay
recommendations, and hygiene warnings that never delete raw evidence). **Perceptual
metabolism makes Solaris regulate continuous sensory exposure like a sensory
metabolism -- finite, homeostatic, and honest -- while keeping needs as operational
pressures rather than feelings and regulation as computation rather than life.**

## Perceptual Ontogenesis and Sensorium-Native Proto-Concepts

Prompts 41-46 gave Solaris continuous perception and a perceptual metabolism. The
next question is developmental: *how does an internal world begin to form from
continuous peculiar perception?* Prompt 47 adds an ontogenesis layer --
`src/solaris_ai_nn/perceptual_ontogenesis/` -- that turns repeated perceptual
structure into stabilized internal structure:

    continuous sensory field -> recurrent patterns -> perceptual atoms ->
    proto-concepts -> concept families -> world-forming relations ->
    memory stabilization -> future perception changes

**Proto-concepts are not words and not human categories.** A `ProtoConcept` is a
stabilized internal structure that helps Solaris compress, predict, relate to, or
respond to its sensorium (a recurring RF island, a silence-after-burst, an echo
boundary, a cross-modal disturbance, an unreliable source, a field deformation).
It needs no name; when a display name is useful, a neutral operational one is
generated (`rf_pattern_003`), never a human semantic label. Human ontology is
never the default, and human labels attach only as external annotations that are
never ground truth -- grounding depends on repeated feature evidence, not labels.

**Birth is conservative and evidence-preserving.** `PerceptualAtom`s are extracted
from sensorium invariants, rhythms, absences, cross-modal relations, receptor/
source-health states, baseline/attention shifts, and metabolic overload/
deprivation; each carries provenance and is marked external if human-annotated.
The `ConceptBirthEngine` aggregates recurring atoms into concepts -- a single
isolated low-novelty event yields at most a weak/unstable candidate (or nothing) --
and records fixture-vs-live grounding. Perceptual metabolism modulates birth:
overload throttles concept birth (it never deletes evidence).

**Concepts stabilize provisionally, decay honestly, and are never deleted.** The
`ConceptStabilizationEngine` scores concepts against evidence (recurrence over
time/sources, prediction/compression/attention usefulness, cross-modal/absence
confirmation, low label-dependence, noise survival, fixture->live survival);
*stable is provisional* -- it does not mean true and never means conscious, and
fixture-only stability is marked. The `ConceptDecayEngine` records decay,
rejection, merge, and split as new state; negative, failed, and ambiguous concepts
are preserved as historical evidence in the append-only `ConceptMemoryStore`
(`atoms.jsonl` / `concepts.jsonl` / `relations.jsonl` / `concept_index.json`). The
`ConceptContaminationAnalyzer` makes human-label influence visible (it is marked,
not forbidden, and lowers grounding/stability).

**World formation is structural, not subjective.** The `ConceptFamilyBuilder`
clusters concepts into evidence-backed structural families (a concept may belong to
several; families are not human taxonomies), the `ConceptRelationGrowthEngine`
grows weak/moderate/strong evidence-backed relations while tracking false-relation
risk and never overstating correlation as causation, and the
`WorldFormationBuilder` summarizes the observable structural world (active/stable/
decaying counts, family distribution, relation density, cross-modal/absence
integration, modality dominance, contamination, prediction/compression support).
This is an observable internal *structural* world -- NOT a subjective world, NOT
qualia, and NOT proof of experience.

**It stays internal and bounded.** The `PerceptualOntogenesisRuntime` reads the
plural-sensorium traces (and optionally metabolism state, live-field source
health, and feeder-SDK metadata), runs bounded ticks under per-tick and total
concept caps (raising explosion warnings rather than exploding), and produces a
ClaimGuard-scanned report. It polls no hardware, controls no feeder, modifies no
source, actuates nothing, and treats no human label as ground truth. The layer
integrates with proto-language (optional internal *signs* for stable concepts --
not human words), the world model (proto-concepts as proto-symbol/boundary nodes,
relations as edges, preserving modality-native ontology), the hypothesis engine
(concepts seed prediction/anomaly/relation hypotheses), LOGOS (ontogenesis
tensions expressed as valid LOGOS tensions), memory/latent replay (history
preserved; bounded consolidation recommendations), the research lab and evaluation
(metrics plus protocols for ontogenesis, birth, stabilization, decay,
contamination, world formation, and safety), the sensorium differentiation lab
(world signatures gain a concept-family/stability/decay/relation profile), the
architecture evolution layer (advisory revision proposals only), the operator
console / Inner MAP. **Perceptual ontogenesis lets a peculiar internal world begin
to form from peculiar perception -- evidence-backed, decay-aware, contamination-
honest -- while keeping proto-concepts as operational structures rather than words
and world formation as structure rather than subjective experience or
understanding.**

## Sensorium-Native Semiogenesis and Internal Signs

Prompt 47 let an internal world begin to form as sensorium-native proto-concepts.
Prompt 48 adds *semiogenesis* -- `src/solaris_ai_nn/semiogenesis/` -- the birth of
internal **signs** from those concepts:

    perceptual atoms -> proto-concepts -> internal signs -> sign families ->
    private syntax -> internal utterances -> compression/prediction/attention
    utility -> optional human-readable gloss (for reports only)

**A sign is not a word and not a human label.** An `InternalSign` is a compact
operational marker (`rf:03a`, `abs:burst_gap_07`, `xmod:rf_vib_11`) that helps
Solaris compress, recall, relate, predict, or attend to sensorium-native
structures. Sign codes are generated structurally (modality/kind prefix + a short
base-36 suffix), never via an LLM and never from a human language. No human
language is the internal default, and human labels enter only as external
annotations that are never ground truth.

**Signs emerge from proto-concepts, conservatively.** The `SignBirthEngine` turns
stable/useful proto-concepts (and their relations) into signs; isolated noise earns
no sign, signs born from human labels are marked contaminated, and fixture-vs-live
grounding is preserved. The `SignUtilityEvaluator` scores each sign's
compression/prediction/attention/memory/hypothesis/LOGOS/relation utility -- a
useful sign is not therefore true or understood, and low-utility signs are demoted
(never deleted). The append-only `SignMemoryStore` keeps rejected, ambiguous, and
drifted signs as historical evidence.

**Private syntax is internal relation structure, not human grammar.** The
`SyntaxPatternBuilder` derives recurring sign relations (sequence, co-occurrence,
before/after-absence, predicts, contradicts, ...) and the `UtteranceBuilder`
composes `InternalUtterance`s from them. There is no subject/verb/object and no
natural-language syntax is forced. The `SignDriftDetector` makes meaning/source/
modality/label drift *visible* (severe drift can recommend a LOGOS tension or a
concept split), and the `SignContaminationAnalyzer` measures human-language
domination (a human word used as a sign code, a gloss replacing the sign, a text
stream dominating formation) -- marking it, never forbidding it.

**Human-readable gloss is approximate, debug-only, never the sign.** The
`GlossBuilder` produces clearly-marked approximate descriptions for reports;
modality-native signs are always glossed approximately and never as a human object
category. Gloss is never ground truth and never the internal language; a
gloss-dependence score is tracked.

**It stays internal and bounded.** The `SemiogenesisRuntime` reads the ontogenesis
proto-concepts (and optional metabolism state), runs bounded ticks under per-tick
and total sign caps (raising explosion warnings rather than exploding), and
produces a ClaimGuard-scanned report. It uses no LLM, makes no human language the
default, and touches no hardware/feeder/source/action. The layer integrates with
perceptual ontogenesis (concepts -> signs), the proto-language lineage (signs are
the sensorium-native successor markers), the world model (signs as proto-symbol
reference nodes distinct from concepts), the hypothesis engine (signs as compact
references), LOGOS (sign/gloss and sign/drift tensions), memory/latent replay,
perceptual metabolism (sign overload/starvation/ambiguity signals throttle birth),
the research lab and evaluation (metrics + protocols for semiogenesis, sign birth,
utility, private syntax, drift, contamination, and safety), the sensorium
differentiation lab (world signatures gain a sign-family/ratio/syntax-density/
gloss-dependence profile), the architecture evolution layer (advisory proposals
only), the operator console, and Inner MAP. **Semiogenesis lets Solaris form a
private system of internal signs from its peculiar perception -- grounded,
drift-aware, contamination-honest -- while keeping the distinction between
proto-concept, sign, utterance, and gloss, and making no claim of language
understanding, consciousness, sentience, life, or subjective experience.**

## Sensorium-Native Cognition

Prompts 47-48 gave Solaris sensorium-native proto-concepts and internal signs.
Prompt 49 adds *cognition* grounded in those structures rather than human language
-- `src/solaris_ai_nn/sensorium_cognition/`:

    sensory field -> proto-concepts -> internal signs -> sign relations ->
    cognitive moves -> anticipation/prediction/simulation -> tension/uncertainty/
    question pressure -> attention and internal-action recommendations ->
    memory consolidation -> changed future perception

**Cognition operates over signs, not human language.** A `CognitiveMove` is an
operation over signs, proto-concepts, relations, memory traces, hypotheses, and
LOGOS tensions -- never a sentence. There is no LLM, no chain-of-thought text as
the cognitive substrate, and no human language as the internal default. The
`SensoriumCognitiveState` is an *operational* snapshot (active signs/concepts/
tensions and bounded pressures), explicitly not a subjective mind-state; any
human-readable summary is a debug gloss.

**Predictions and failed predictions are stored.** The `PredictionEngine` makes
sign-grounded predictions (next sign, missing sign, source silence, overload/
deprivation risk, ...); each prediction's outcome is resolved against observed
targets and recorded. Failed predictions are useful evidence and are preserved,
never hidden. The `AnticipationEngine` turns predictions into operational
expectations that feed changed-perception probes -- expectation, not imagination.

**Question pressure is operational, not verbal questioning.** The
`QuestionPressureEngine` produces pressure to inspect, compare, wait, simulate, or
preserve an unknown (missing expected sign, contradiction, failed prediction,
ambiguity, low grounding, unresolved tension). It is not a human verbal question;
it may be rendered as debug text but the pressure itself is structural, and it
drives internal attention recommendations.

**Internal simulation is marked non-real.** The `InternalSimulation` and
`CounterfactualEngine` run bounded "what if" probes over signs/absences/relations.
Every result is marked simulated / counterfactual and is never treated as a live
observation or mixed with real traces; they may seed hypotheses but create no
external evidence. The `AnalogyEngine` finds *structural* analogies across
modalities (not semantic ones), recording an analogy as contradicted if later
evidence opposes it. The `SynthesisEngine` merges/splits signs and either resolves
a weak contradiction or preserves an irreducible one as a LOGOS tension -- always
preserving the synthesized fragments.

**It stays internal and bounded.** The `SensoriumCognitionRuntime` reads the
semiogenesis signs/patterns (and optional ontogenesis concepts, metabolism state,
and LOGOS tensions), runs bounded ticks under per-tick move/prediction/simulation
caps (throttled further under metabolic overload), writes append-only cognitive
memory (failed predictions preserved), and produces a ClaimGuard-scanned report.
It uses no LLM and touches no hardware/feeder/source/action. The layer integrates
with the world model (predictions and simulation summaries as trace nodes, with
simulated items marked separately and never mixed with observation), the
hypothesis engine (failed predictions, counterfactuals, and analogies as seeds),
LOGOS (prediction-vs-failure, simulation-vs-observation, analogy-vs-difference,
question-pressure-vs-no-data tensions), perceptual metabolism (overload/pressure
signals that throttle cognition), memory/latent replay, the research lab and
evaluation (metrics plus protocols for cognition, prediction, anticipation,
question pressure, simulation, analogy, synthesis, and safety), the sensorium
differentiation lab (world signatures gain a cognitive-move/prediction/question/
simulation/analogy/synthesis profile), the architecture evolution layer (advisory
proposals only), the operator console, and Inner MAP. **Sensorium-native cognition
lets Solaris think over its own peculiar signs and proto-concepts -- predicting,
anticipating, questioning, simulating, and synthesizing -- while preserving the
distinction between sign-based cognition, debug gloss, simulation, and real
observation, and making no claim of understanding, consciousness, sentience, life,
or subjective experience.**

## Sensorium-Native Self-Boundary and Organismic Continuity

Prompts 41-49 gave Solaris a continuous sensorium, perceptual metabolism,
proto-concepts, internal signs, and sign-based cognition. Prompt 50 adds an
operational *self/world boundary* -- `src/solaris_ai_nn/self_boundary/` -- that
answers, operationally, "how does this organismic AI distinguish my perceptual
body from the world that touches it?"

**Self-boundary is operational, not subjective selfhood.** The `SelfBoundaryState`
assigns each record to a `BoundaryZone` -- internal state, receptor body, sensory
membrane, external feeder, external world source, memory trace, prediction,
simulation, counterfactual, operator annotation, or unknown -- with an explicit
confidence, and boundary uncertainty is allowed. This is not a subjective self, not
personhood, and not a metaphysical claim.

**Ownership attribution separates self, world, feeder, memory, and simulation.**
The `OwnershipAttributor` decides whether an event belongs to Solaris' internal
state, its receptor body, an external source/feeder, a report/debug layer, an
internal simulation, or a remembered trace. Crucially, sensory input is not "self"
merely because Solaris processed it; internal simulation is not the real world;
operator annotation is not ground truth; and failed/ambiguous attribution is
preserved. The `InternalExternalClassifier` makes mixed records explicit rather
than silently collapsing processed sensory data into "internal self".

**Body schema means receptor/sensorium body, not biological body.** The
`SensoriumBodySchema` treats receptors and sensory membranes as body-like organs
(tracking reliability, fatigue, saturation, sensitivity, silence, boundary
confidence, and inter-receptor relations). External feeders are NOT body parts --
they are external nerve-like signal sources. The `SourceAttributionEngine`
attributes provenance while preserving uncertainty, refusing to promote a corrupted
source to internal truth and refusing to treat a human-readable gloss as source
evidence.

**Identity trace means continuity metadata, not personhood.** The
`OperationalIdentityTrace` / `IdentityTraceStore` record run identity, continuity
anchors, active receptors, stable signs/concepts, boundary shifts, memory gaps,
restart and drift events, and safety blocks to append-only logs. The
`OrganismicContinuity` tracks anchors and logs `ContinuityBreak`s (silence,
corruption, receptor reset, memory gap, restart); recovery marks a break recovered
WITHOUT erasing it. Continuity here is trace continuity, not biological life, and
identity is operational continuity, not personal identity.

**Simulation boundary prevents confusing imagined/internal states with live
observation.** The `SimulationBoundaryValidator` marks simulations, counterfactuals,
fixture, replay, live-read-only, debug-truth, and report-gloss records, and blocks
any non-observation marker from being used as observation or sensory evidence:
simulation never becomes observation, a counterfactual never overwrites memory of a
real event, and debug truth never enters cognition. The `BoundaryTensionDetector`
surfaces self/world tensions (internal-vs-external, simulation-vs-observation,
memory-vs-current-flux, feeder-artifact-vs-world-source, self-continuity-vs-restart
gap, human-gloss-vs-internal-sign, unknown-origin) and feeds them to LOGOS without
resolving ambiguous ones prematurely.

**It stays internal and bounded.** The `SelfBoundaryRuntime` reads the plural
sensorium (and optional feeder provenance, metabolism, ontogenesis, semiogenesis,
and cognition state), attributes ownership, builds the body schema, updates the
perspective frame, maintains continuity anchors, marks simulation boundaries,
attributes sources, classifies internal/external, detects boundary tensions, and
updates the identity trace -- all bounded, with no hardware/feeder/source control,
no real-world action, and no metaphysical identity claims. It bridges the older
`ego/` module (offering a sensorium-native boundary summary without duplicating or
clobbering it) and integrates with LOGOS, memory/latent replay, the research lab
and evaluation, the sensorium differentiation lab (world signatures gain a
boundary-clarity/simulation-integrity/source-quality/body-stability/continuity/
identity profile), the architecture evolution layer (advisory proposals only), the
operator console (with the mandated safe answers about "body" and "self-awareness"),
and Inner MAP. **Self-boundary lets Solaris distinguish its perceptual body from
the world that touches it -- internal state, receptor body, external flux, memory,
prediction, and simulation kept operationally distinct -- without claiming
self-awareness, consciousness, sentience, life, or personhood.**

## Sensorium-Native Valence and Desire Formation

Prompts 41-50 gave Solaris perception, metabolism, proto-concepts, signs,
cognition, and a self/world boundary. Prompt 51 adds *desire formation* --
`src/solaris_ai_nn/desire_formation/` -- where "desire" means an operational
pressure toward an internal action tendency, NOT emotion, human wanting, conscious
intention, or free will. This layer closes the loop back to the Solaris spine
(Stimulus -> Push -> Desire -> ActionCandidate -> Reaction/Trace):

    sensory field -> perceptual metabolism -> cognitive pressure -> self-boundary
    state -> valence gradient -> push formation -> desire candidate -> internal
    action readiness -> safe arbitration -> internal action / attention shift /
    simulation / consolidation / no-op -> result becomes a new trace

**Valence is operational priority, not emotion.** The `ValenceAssessment` derives a
`ValenceGradient` from upstream states (novelty, overload, deprivation, absence,
prediction success/failure, LOGOS tension, concept/sign dynamics, boundary
uncertainty, continuity breaks, consolidation pressure) with directions
(attractive/aversive/stabilizing/destabilizing/ambiguous). Valence influences
internal attention, simulation, consolidation, and readiness only -- it is never
pleasure/pain and can never authorize real-world action.

**Push is pre-desire pressure.** The `PushFormationEngine` turns valence into
`SensoriumPush`es (pre-desire pressures that preserve evidence and may decay
without ever acting). The `DesireFormationEngine` turns pushes into
`DesireCandidate`s whose kinds are all internal tendencies (inspect absence, focus/
compare modalities, stabilize concept, test prediction, simulate, resolve/preserve
tension, consolidate, rest receptor, mark source/concept/sign, request operator
review, no-action). Each desire maps only to an allowed internal action.

**Desire is internal action readiness, not human wanting.** The `ReadinessGate`
conservatively gates each desire across evidence/energy/attention/memory/boundary/
safety/governance/uncertainty/simulation/consolidation dimensions; readiness is not
execution and cannot bypass arbitration. The `DesireArbitrator` selects among ready
desires by utility/risk/urgency -- but safety and governance have veto power, and
no real-world actuation, code execution, or source modification may ever be
selected. The `MotivationField` exposes *why* an action was selected or inhibited,
and the `ConflictDetector` surfaces competing tendencies (novelty-vs-stability,
inspect-vs-consolidate, safety-vs-desire, ...) that feed LOGOS without premature
resolution.

**Internal actions are safe and non-actuating.** The `InternalActionExecutor` runs
only allowed internal actions (attention shifts, monitoring changes, bounded
simulation, hypothesis generation, internal prediction tests, preserve-unknown,
marking source/concept/sign, consolidation recommendations, operator-review
requests, no-op). Anything outside that set is downgraded to a safe no-op;
`request_operator_review` creates a decision item only. Nothing controls hardware,
feeders, the network, a shell, an OS device, or a source file.

**No-op is a valid action result, and failed/blocked desires are evidence.**
Overload, insufficient evidence, or poor boundary clarity lead to conservative
no-op / inhibition / deferral -- organismic inhibition rather than churn. The
`DesireOutcomeTrace` and append-only `DesireMemoryStore` preserve every outcome,
including failures, safety/governance blocks, and no-ops; none are deleted.

**It stays internal and bounded.** The `DesireFormationRuntime` reads metabolism/
cognition/self-boundary state (and LOGOS tension count), runs bounded ticks, and
integrates with the Conscience spine (a `desire_formation_update` phase plus a
`safe_internal_action_arbitration` phase, after the cognition and self-boundary
phases and before stimulus ingestion, with six bounded profiles), LOGOS (desire
conflicts as tensions), the hypothesis engine (test/inspect/compare desires as
seeds), memory/latent replay, the research lab and evaluation (metrics plus
protocols for desire formation, valence, push, arbitration, readiness, outcome, and
safety), the sensorium differentiation lab (world signatures gain a valence/push/
desire-kind/internal-action/no-op/conflict profile), the architecture evolution
layer (advisory proposals only), the operator console (with the mandated safe
answers about "wanting", "emotions", and "agency"), and Inner MAP. **Desire
formation lets Solaris turn sensorium-native pressures into operational valence,
pushes, and desires that lead only to safe internal actions -- while preserving the
distinction between operational desire and human emotion, free will, agency,
consciousness, sentience, life, or subjective experience.**

## Sensorium-Native Action-Reaction Loop

Prompts 41-51 gave Solaris perception, metabolism, proto-concepts, signs,
cognition, a self/world boundary, and desire formation. Prompt 52 closes the loop
-- `src/solaris_ai_nn/action_reaction/`:

    Stimulus -> Push -> Desire -> ActionCandidate -> InternalAction -> Reaction
    -> ConsequenceTrace -> Learning -> Habit / Inhibition / Revision
    -> changed future perception

The system learns what its *internal* actions do (shifting attention reduces
uncertainty, no-op prevents overload, an unsafe candidate is blocked and becomes
evidence). This is NOT agency and NOT free will -- it is operational action-
consequence learning inside the system.

**Action is internal/simulated/report-only.** An `ActionCandidateRecord` carries a
scope (internal_only / simulation_only / report_only / governance_record_only /
forbidden_external) and a full evidence chain back to the desire/push/valence/
readiness/arbitration that produced it. No real-world scope exists; any external/
hardware/source-modifying action is forbidden and blocked. `no_op` is a real,
traceable action result.

**Reaction is operational consequence, not feeling.** A `SensoriumReaction`
classifies the effect of an action (uncertainty reduced/increased, prediction
confirmed/failed, overload reduced, boundary clarified, ...) with an operational
valence (constructive/disruptive/stabilizing/destabilizing/neutral) -- never
pleasure/pain. A failed or blocked action still produces a reaction trace.

**Consequence learning links actions to effects.** The `ConsequenceTrace` records
an evidence-backed before/after internal change over a bounded window (or
ambiguous / no-observed-change when undetermined; effects are never invented). The
`EffectLearningEngine` accumulates provisional action->reaction relations whose
confidence grows only with repeated evidence; correlation is never causation and
failed effects remain visible.

**Habits are learned policy tendencies, and inhibition protects the organism.** The
`HabitFormationEngine` strengthens trigger->action habits from repeated
constructive reactions and weakens or inhibits them otherwise; habits are NOT
instincts, personality, or will, and remain overrideable by safety/governance. The
`InhibitionEngine` records why an action was withheld (safety risk, uncertainty,
overload, no-effect history, ...) -- inhibition is not failure, it protects against
unsafe or useless churn. The `ActionPolicyEngine` updates internal-only
preferences (prefer/avoid/require-more-evidence/always-block-forbidden) that cannot
authorize external action and preserve the safety/governance veto.

**No-op is valid, and failed/blocked/no-effect actions are evidence.** The
append-only `ReactionMemoryStore` preserves every action, reaction, consequence,
effect, habit, inhibition, and policy update -- including failures, blocks, and
no-effect actions; none are deleted.

**It stays internal and bounded.** The `ActionReactionRuntime` reads the internal
actions selected by desire formation, validates scope, generates reactions, builds
consequences, learns effects/habits, and records inhibitions -- all bounded, with
no external actuation, no hardware/feeder/source control, and no unbounded loop. It
integrates with the Conscience spine (an `action_reaction_update` phase after the
desire/arbitration phases and before stimulus ingestion, with six bounded
profiles), feeds results back into perceptual metabolism, cognition, self-boundary,
ontogenesis, and semiogenesis, emits LOGOS tensions (action-success-vs-failure,
habit-vs-novelty, inhibition-vs-desire, no-action-vs-pressure), seeds the
hypothesis engine with action-effect hypotheses, stores traces in memory/latent
replay, and reports to the research lab, sensorium differentiation lab (action/
reaction/consequence/habit/inhibition/no-effect/policy profiles), architecture
evolution (advisory proposals only), operator console (with the mandated safe
answers about "what did Solaris do", "did it act in the real world", and "agency"),
and Inner MAP. **The action-reaction loop lets Solaris learn what its safe internal
actions do -- forming habits, inhibiting useless churn, and revising policy -- with
NO real-world actuation and no claim of agency, free will, consciousness,
sentience, life, personhood, or subjective experience.**

## Long-Horizon Developmental Runtime

Prompts 41-52 gave Solaris a complete internal loop (stimulus -> push -> desire ->
internal action -> reaction -> consequence -> memory -> habit -> changed future
perception). Prompt 53 stretches that loop across long time --
`src/solaris_ai_nn/developmental_life/`:

    bounded developmental cycles -> life-cycle phases -> epochs -> growth state ->
    maturation markers -> phase transitions -> plateaus -> regressions ->
    growth-vs-accumulation -> persistent life history -> changed future perception

It is a long-duration developmental *substrate* -- not a product release, an
intelligence benchmark, or a consciousness test. It reads the outputs of the full
sensorium-native stack and detects long-horizon structure.

**Immediate action-reaction loops become developmental history.** The
`LongHorizonDevelopmentalRuntime` collects per-tick status snapshots from the prior
modules, advances an operational `LifeCycleState` (boot, baseline exposure, growth,
consolidation, maturation probe, plateau, regression watch, recovery, shutdown),
and accumulates them into a persistent record. "Life cycle" is operational runtime
language, not biological life; every phase is bounded and leaves trace evidence.

**Epochs track structural change over time.** A `DevelopmentalEpoch` is a
developmental slice (not a biological age) whose boundary records an explainable
`EpochTransitionReason` (new stable concepts/signs, prediction improvement,
plateau, regression, ...). Epochs are persisted so they survive restart. The
`DevelopmentalGrowthState` derives a value per growth dimension (sensorium
adaptation, concept/sign growth, prediction skill, action-effect learning,
inhibition quality, boundary clarity, contamination resistance, ...); growth means
*structural change* -- which may include pruning, decay, inhibition, and no-op
learning -- not an intelligence score, and more is not always better.

**Maturation markers are operational observations.** The `MaturationDetector`
records first occurrences of structural markers (first stable concept, first useful
prediction, first weakened bad habit, first preserved simulation boundary, ...).
These are observational, kept with weak/ambiguous markers separated; they are NOT
consciousness or developmental-psychology milestones.

**Phase transitions are evidence-backed; plateaus and regressions are preserved.**
The `PhaseTransitionDetector` flags developmental transitions (adaptive sensing ->
concept growth, concept growth -> sign formation, fixture dependence -> live
grounding, ...) with low/moderate/high confidence and a false-transition risk;
missing evidence is inconclusive. The `PlateauDetector` flags no-growth stretches
(with internal/report-only recommendations -- a plateau is not failure), and the
`RegressionDetector` makes declines visible (recommending an auto-regeneration
check when severe). The append-only `DevelopmentalMemoryStore` preserves
regressions, plateaus, failed transitions, and inconclusive results.

**Growth vs accumulation is evaluated conservatively.** The
`StructuralGrowthAnalyzer` distinguishes real structural growth (durable prediction
improvement, stable concept/sign utility, action-effect learning, lower
contamination) from mere event accumulation, log bloat, fixture or human-label
overfit, random fluctuation, or regression. It is deliberately conservative: a
negative or inconclusive verdict is valid, and growth is never over-claimed. The
`OperationalLifeHistory` summarizes major operational events as trace history, not
biography.

**It stays bounded, persistent, and internal.** The runtime is bounded per
invocation but may be called repeatedly over days/months, persisting and reloading
its index across restarts. It starts no feeders, controls no hardware, modifies no
source, performs no external action, and uses no human teaching loop. It integrates
with the Conscience spine (a `developmental_life_update` phase after the action-
reaction phase and before stimulus ingestion, with six bounded profiles; live read-
only requires governance), the research lab and evaluation (metrics plus protocols
for developmental life, epochs, maturation, phase transitions, plateaus,
regressions, growth-vs-accumulation, and safety), architecture evolution (advisory
proposals only), the operator console (with the mandated safe answers about
"developing" and "life or consciousness"), and Inner MAP. **The long-horizon
developmental runtime lets Solaris accumulate an operational growth history and ask
whether it changes structurally over time -- conservatively, with regressions and
plateaus preserved -- without being biological life, consciousness, sentience,
personhood, agency, free will, or subjective experience.**

## Month-Scale Developmental Soak Protocol

Prompt 53 built the *engine* that detects structural change over time. Prompt 54
builds the formal *study protocol* around it -- `src/solaris_ai_nn/developmental_soak/`:

    preflight -> 2h dry run -> 24h trial -> 7d stabilization -> 30d soak ->
    optional 90d extension -> post-run autopsy

The central research question is: *did Solaris undergo measurable structural
development through autonomous sensorium-native experience?* -- not "did it become
conscious / understand / become alive / become an agent?".

**The developmental runtime is the engine; the soak is the study manager.** The
`DevelopmentalSoakRuntime` calls the `LongHorizonDevelopmentalRuntime` as its growth
detector and never re-implements the detectors. It is *protocol orchestration and
evidence compilation only*. Developmental Life remains the growth detector; Soak
remains the study manager.

**Runs are staged and bounded.** The `DevelopmentalSoakPlan` defines seven stages,
each with a purpose, a duration *target* (2h/24h/7d/30d/90d), a hard runtime cap, a
tick cap, required/optional modules, a sensory-source policy, a live read-only
policy (governance-gated), checkpoint/report/safety intervals, an append-only
artifact-retention policy, and explicit exit/abort criteria. No stage starts
feeders or controls hardware; no stage is unbounded. Long runs are reached by
repeated bounded invocations + checkpoints, never an unbounded daemon. Each
invocation walks a bounded `SoakRunPhase` sequence (boot, baseline capture, active
developmental cycle, quiet consolidation, checkpoint, safety scan, daily packet,
weekly review, restart drill, phase summary, shutdown-or-continue) where every phase
writes trace evidence and every failure is recorded.

**Preflight validates readiness without starting the run.** `SoakPreflight` checks
that required packages import (a missing one fails), optional packages import (a
missing one warns), state dirs are writable, prior reports are discoverable, the
developmental runtime and ClaimGuard are available, no hardware/feeder/network/shell
capability is enabled, and -- for live read-only -- that a feeder registry, source
paths, and governance approval exist (a missing live source *blocks* the live stage
rather than crashing).

**Daily packets and weekly reviews preserve evidence.** The
`DailyEvidencePacketBuilder` compiles one honest day (sensorium/source health,
metabolism, concept/sign/cognition/boundary/desire-action/habit changes, maturation
markers, plateaus/regressions, safety blocks, contamination, an early
growth-vs-accumulation signal) -- evidence, not marketing, with negatives always
included and the Markdown ClaimGuard-scanned. The `WeeklyReviewBuilder` aggregates a
week and emits a conservative, *recommendation-only* `WeeklyReviewDecision`
(continue / continue-with-warning / source-diet / consolidation / autoregeneration /
pause / abort / inconclusive) -- no automatic external change, no feeder control.

**Checkpoints and restart drills keep continuity honest.** The `CheckpointManager`
writes append-only, checksum-verified checkpoints (run manifest, per-module state,
Inner MAP snapshot, developmental-life state, safety state, artifact index); it never
auto-deletes, records corrupt checkpoints rather than dropping them, and preserves
the break history through recovery. The `RestartDrillRunner` exercises graceful
restart, a simulated crash marker, missing-checkpoint recovery, source silence,
corruption detection, and continuity verification -- it never kills the process, and
gaps are logged operationally, not biologically.

**Control arms prevent self-flattering conclusions.** `SoakControlArm` runs
shortened comparison arms (full stack, passive-parser-only, ablations of each
module, fixture-only, human-label-heavy, feature-only, and an optional governance-
gated live read-only arm). Missing modules mark an arm unavailable; arms with
insufficient data stay inconclusive; controls are never over-claimed.

**The evidence dossier and post-run autopsy ask whether growth occurred or logs
accumulated.** The `EvidenceDossierBuilder` compiles conservative,
evidence-referenced `EvidenceClaim`s (every claim requires refs; negative and
inconclusive claims are allowed; consciousness/life/agency claims are structurally
impossible). The `PostRunAutopsy` answers the closing questions -- did growth occur,
was it durable across restart, did the system merely accumulate logs, did source
diet dominate, did live differ from fixture, did human labels contaminate, did
proto-concepts/signs/predictions improve, did action-reaction improve later
arbitration, did habits help or harden, did inhibition prevent churn, did
self-boundary prevent confusion, were safety boundaries preserved -- and recommends
continue/revise/pause/abort. The autopsy must include failures and missing data and
does not praise the system by default.

**It integrates and stays safe.** The soak feeds the research lab and evaluation
(metrics + protocols for the soak, preflight, checkpoints, daily packets, weekly
reviews, restart drills, control arms, the dossier, the autopsy, and soak safety),
architecture evolution (advisory `soak_revision_proposals` only), the operator
console (soak status + the mandated safe answer for "does this prove consciousness
or life?"), and Inner MAP. The `DevelopmentalSoakSafetyValidator` blocks unbounded
daemons, hardware/feeder/network/shell/OS, source modification, real-world
actuation, the human teaching loop, sensory-text-as-command, human-label-as-ground-
truth, deletion of negative evidence, hiding failed checkpoints, and hiding
regressions/plateaus. **The soak protocol studies structural development through
repeated bounded runs: long runtime does not imply life, persistence does not imply
consciousness, and the evidence dossier does not prove sentience, personhood,
agency, free will, emotion, feeling, understanding, or subjective experience -- no
real-world actuation, no feeder/hardware/source control, and no human teaching loop
ever occurred.**

## Cross-Run Replication and Falsification

One soak is not evidence enough. A single developmental run -- however long and
well-instrumented -- cannot tell robust structural development from a lucky seed, a
fixture artifact, or a flattering report. Prompt 55 adds the cross-run replication
and falsification lab -- `src/solaris_ai_nn/developmental_replication/`:

    register runs -> build experimental lineages -> align run structures ->
    structural similarity -> divergence -> environmental dependency ->
    bounded falsification tests -> replication matrix -> conservative reports

The central question is: *do independent Solaris runs produce comparable structural
development under comparable sensorium conditions, and meaningfully different
development under different sensorium conditions?* -- not "did it become conscious /
alive / understand / become an agent?".

**Replication compares multiple developmental lineages.** The
`DevelopmentalRunRegistry` catalogues independent runs (seed, architecture version,
sensorium/feeder profile, fixture/live/replay status, source diet, soak/developmental
report paths, metrics snapshot) -- it reads metadata and reports only; it never
starts runs and never modifies a source artifact, and missing metadata is preserved
as explicit uncertainty. The `DevelopmentalLineage` records how runs relate as
*experiments* (same/different seed, same/different sensorium, fixture->live,
control/ablation, restart continuation, branch from a checkpoint). A lineage is
experimental provenance, NOT biological ancestry; nothing is a parent, child, or
offspring in any living sense.

**Similarity and divergence are structural.** `CrossRunAlignment` lines up the
comparable structures of two runs (epochs, growth dimensions, maturation markers,
phase transitions, proto-concept/sign families, private syntax, prediction/
action-effect/habit/boundary/source-diet/contamination profiles, plateau/regression
events, safety blocks), preserving run-specific differences and never forcing
different sensoriums into human labels (missing data is partial/inconclusive).
`StructuralSimilarity` scores per-dimension similarity conservatively: low similarity
may be real divergence, noise, or insufficient evidence; high similarity may be
robust development OR fixture overfit -- both are flagged as caveats.
`DivergenceDetector` explains low similarity (different diet/seed, live flux, source
silence/corruption, overload/deprivation, contamination, fixture overfit, action
policy, habit rigidity, boundary confusion, restart discontinuity, or an explicit
unknown). Divergence is not failure by default, and unknown divergence stays visible.
`EnvironmentalDependencyAnalyzer` estimates dependence on fixtures, live rhythms,
human labels, feature-only modalities, source-diet balance, seed, and checkpoint
history -- flagging fixture and human-label dependence and requiring evidence for
live dependence.

**Falsification probes challenge the claims.** The falsification lab asks whether a
claimed structure would survive a null condition: shuffled event order (does shuffled
time destroy prediction?), random labels / same features (do concepts form from
features, not labels?), same labels / random features, no-recurrence stream (does
growth disappear without recurrence?), silent-source control, passive-parser
comparison (does passive parsing reproduce the report?), pure log-accumulation null,
fixture- and human-label-overfit probes, simulation-as-observation probe, and
module-ablation controls. It uses existing artifacts or synthetic fixtures, never
modifies the original evidence, makes failed claims visible, and -- crucially --
passing a falsification test does not prove understanding. The controls include the
passive parser, no-metabolism, no-ontogenesis, no-semiogenesis, no-cognition, and
no-action-reaction arms.

**The replication matrix is conservative.** `ReplicationMatrixBuilder` assembles the
findings into a grid whose cells are replicated / partially_replicated / diverged /
inconclusive / failed / unavailable / falsified / not_applicable. There is no empty
green dashboard, inconclusive is a valid status, and falsified claims are made
prominent.

**It integrates and stays safe.** The replication lab consumes soak dossiers/
autopsies/control-arms and the Long-Horizon Developmental Runtime's epochs/growth/
phase-transitions/growth-vs-accumulation, and the Sensorium Differentiation Lab's
world signatures (to check whether sensorium differences reliably produce different
world signatures). It feeds the research lab and evaluation (metrics + protocols for
replication, registry, lineage, alignment, similarity, divergence, dependency,
falsification, and the matrix), architecture evolution (advisory
`replication_revision_proposals` only -- and **a falsified claim blocks architecture
promotion**), the operator console (replication matrix + falsified claims + the
mandated safe answer for "does replication prove consciousness?"), and Inner MAP. The
`DevelopmentalReplicationSafetyValidator` blocks unbounded runs, hardware/feeder/
network/shell/OS, source-artifact modification, real-world actuation, the human
teaching loop, sensory-text-as-command, human-label-as-ground-truth, ancestry/life
claims, and any deletion or hiding of diverged/falsified/inconclusive evidence.
**Replication compares observable developmental structures across independent runs:
it does not prove consciousness, sentience, biological life, personhood, agency, free
will, emotion, feeling, understanding, or subjective experience; a developmental
lineage is experimental provenance, not biological ancestry; cross-run similarity
does not prove consciousness; divergence does not prove failure; and passing a
falsification test does not prove understanding.**

## Operator-Governed Experiment Compiler

Prompt 56 produced evidence-guided architecture proposals; a proposal is not an
implementation. Prompt 57 adds the experiment compiler --
`src/solaris_ai_nn/experiment_compiler/`:

    input manifest -> read proposals -> compiled experiment specs ->
    prompt packs + branch specs + test matrices + safety gates ->
    operator review packets + rollback plans + validation plans -> reports

It converts approved or candidate architecture-evolution proposals into
human-reviewable implementation packs for a human operator or external coding
agent. **This is not autonomous coding, not self-improvement, and not source
mutation.** It is a compiler from research evidence to human-reviewable
implementation instructions.

**It reads evidence and never mutates anything.** The
`ExperimentCompilerInputManifest` declares the source artifacts (architecture
report, branch manifest, experiment queue, module inventory, promotion gate,
ablation plan, variant proposal, falsification report, replication matrix, soak
autopsy, safety invariant report, operator note); it reads existing artifacts
only, treats a missing input as a warning or a blocker by severity, preserves
falsified evidence, and never lets the operator note override safety evidence.
The `ArchitectureProposalReader` normalizes each proposal and tags a disposition:
unsafe proposals become *blocked* read results, falsified proposals are blocked,
and inconclusive/missing-evidence proposals become *retest* results -- never
implementation packs.

**It compiles documents, not code.** `compile_spec` turns a normalized proposal
into a `CompiledExperimentSpec` (title, purpose, target modules, non-goals,
proposed changes, expected behavior, required tests/examples/docs, safety gates,
validation/rollback plans, follow-up soak/replication requirements). A spec
modifies no code, creates no branch, and calls no GitHub API. From a ready spec
the compiler builds an `ImplementationPromptPack` (a constrained brief for an
external agent that always carries the hard prohibitions, including "do not
modify unrelated files unless necessary" and "do not open a PR unless the
operator explicitly chooses"), a `PRReadyBranchSpec` (a *suggested* branch name +
draft PR title/body + review checklist + merge blockers -- no Git operation
performed), an `ExperimentTestMatrix` (unit/integration/safety/example/report/
ClaimGuard/regression/ablation/soak/replication rows, with safety and ClaimGuard
rows blocking), a `PostImplementationValidationPlan` (static inspection -> unit ->
integration -> safety -> example -> short demo -> mini soak -> ablation ->
falsification replay -> replication registration, gated and never auto-executed),
and an `ExperimentRollbackPlan` (documented triggers + evidence-preserving steps,
never executed).

**Safety gates block readiness; the operator decides.** The `SafetyGateEvaluator`
checks every constitutional gate (no source self-rewrite, no auto branch/PR, no
external actuation, no hardware/feeder/network/shell, no human-label ground
truth, no consciousness/life/agency claim, no unbounded loop, preserve negative/
falsified evidence, ClaimGuard required). Every gate is critical: a single failure
blocks pack readiness, explicitly and never hidden behind a warning. The
`OperatorReviewPacket` then presents the evidence, risks, blocked claims, yes/no
review questions, and a recommended next step to a *human operator* -- it never
approves itself, and no decision is automatic.

**It integrates and stays document-only.** The `ExperimentCompilerRuntime` is
bounded and writes documents only; it consumes architecture-evolution proposals
(without duplicating that logic) and uses soak/replication/falsification evidence
as source refs. It feeds the research lab and evaluation (metrics + protocols for
the compiler, compiled specs, prompt packs, branch specs, test matrices, safety
gates, review packets, and validation plans), the operator console (the compiled
experiment index, ready/blocked specs, and the mandated safe answers for "what
should I give Claude Code next?", "did Solaris create a branch?", and "did Solaris
rewrite itself?"), and Inner MAP. The `ExperimentCompilerSafetyValidator` blocks
source modification, autonomous code rewrite, automatic branch/PR creation,
external coding-agent execution, network/shell/browser/OS, hardware/feeder
control, real-world actuation, the human teaching loop, deletion of negative/
falsified/inconclusive evidence, and any "ready" mark while a critical gate
fails. **The compiler writes documents only: no source code was changed, no Git
branch was created, no pull request was opened, no external coding agent was run,
no safety gate was bypassed, and no claim of consciousness, sentience, life,
personhood, agency, free will, emotion, feeling, understanding, or subjective
experience is made.**

## Implementation Intake and PR Diff Audit

Prompt 57 generated implementation packs for external coding agents; Prompt 58
audits the *completed* implementations. The implementation intake layer --
`src/solaris_ai_nn/implementation_intake/`:

    intake manifest -> read artifacts -> diff audit -> spec compliance ->
    test audit -> safety regression -> ClaimGuard audit -> coverage matrix ->
    merge recommendation -> rollback recommendation -> post-merge validation plan

**This is not a merge bot and not a coding agent. It is an evidence auditor.** It
reads *local* artifacts only -- the compiler's reference artifacts (implementation
prompt, branch spec, test matrix, safety gates, operator review packet, rollback/
validation plans) and the implementation's own evidence (summary, diff/patch,
changed-file list, test/example/ClaimGuard/safety-invariant results, and optional
local PR metadata) -- and never calls GitHub.

**It audits diff, spec, tests, safety, claims, and coverage.** The `DiffAudit`
classifies each changed file (expected, unexpected, forbidden path, safety-
critical, generated, docs, test, example, source) and scans the added patch lines
for forbidden behavior (network/shell/browser/OS, hardware imports, source
mutation, human-label-as-ground-truth, unsupported claim text) -- an unexpected
change warns, forbidden behavior blocks; it runs no Git. The `SpecComplianceAudit`
compares evidence against the compiled spec (classes/functions, tests, examples,
docs, safety gates), never marking a requirement satisfied without evidence and
treating safety requirements as blocking. The `TestResultAudit` reads the test
artifact (missing safety/ClaimGuard tests block; failed tests block unless
explicitly non-blocking; test output is evidence, not proof). The
`SafetyRegressionAudit` scans for regressions (self-rewrite, auto branch/PR,
agent execution, actuation, hardware/feeder/network/shell, source mutation,
sensory-text-as-command, human-label-as-ground-truth, simulation-as-observation,
consciousness/life/agency claims, evidence deletion, unbounded loops) where a
critical finding blocks and is never hidden by passing tests. The `ClaimGuardAudit`
flags undisclaimed unsupported claims in generated docs. The
`ImplementationCoverageMatrix` joins each requirement to its file/test/example/
docs/report/safety evidence so gaps stay visible -- there is no empty green
dashboard.

**It recommends advisorily; a human operator decides.** The
`MergeRecommendationBuilder` aggregates every audit into one of recommend-merge,
merge-with-warnings, recommend-revisions, or a block (safety / tests / spec /
missing evidence) -- advisory only, never merging or approving. The
`RollbackRecommendationBuilder` documents (never executes) a rollback when one is
warranted, always preserving the failed artifacts as evidence. The
`PostMergeValidationPlan` lays out the staged, gated post-merge validation (re-run
tests -> examples -> safety invariants -> ClaimGuard -> short fixture demo -> mini
soak -> replication registration -> falsification replay -> update architecture
evidence -> update experiment queue), never auto-executed and marked conditional
when merge is blocked.

**It integrates and stays read-only.** The `ImplementationIntakeRuntime` is
bounded; it consumes the experiment-compiler artifacts as the audit reference,
emits outputs usable as future architecture-evolution evidence (merge
recommendation, spec compliance, blocked reason, safety-regression findings,
missing evidence, post-merge plan), and feeds the research lab + evaluation
(metrics and protocols for the intake, diff audit, spec compliance, test audit,
safety regression, coverage, and merge recommendation), the operator console (the
intake report, blockers, and the mandated safe answers for "is this ready to
merge?", "did Solaris merge the PR?", and "did Solaris edit the code?"), and Inner
MAP. The `ImplementationIntakeSafetyValidator` blocks source modification, merge
execution, PR creation/approval, GitHub calls, Git commands, external coding-agent
execution, shell/network/browser/OS, hardware/feeder control, real-world
actuation, the human teaching loop, evidence deletion, and any "ready" mark while
a critical safety gate fails. **It does not edit source, create branches, open
PRs, approve PRs, merge PRs, call GitHub, run Git, or run external agents -- it
reads local evidence and writes advisory documents only, and makes no claim of
consciousness, sentience, life, personhood, agency, free will, emotion, feeling,
understanding, or subjective experience.**

## Post-Merge Evidence Assimilation and Baseline Registry

Prompt 58 audits an implementation and recommends merge/revision/block; the merge
itself is a human act outside Solaris. Prompt 59 handles what happens *after* a
human operator merges or accepts a change externally --
`src/solaris_ai_nn/post_merge_assimilation/`:

    merge manifest -> ingest validation -> assimilate evidence ->
    register candidate baseline -> compare to parent -> regression watch ->
    module status + rollback recommendations -> follow-up queue -> reports

It is the research ledger that answers one question from local operator-provided
evidence: *a human changed the code externally -- what did that change do to the
experimental organismic architecture?* It is not a merge bot, a release system, or
self-modification.

**A human merges; Solaris ingests local evidence.** The `PostMergeManifest`
records the operator's confirmation that a change was accepted (human-confirmed
merge, manual update, external PR merge, local branch acceptance, ...), plus the
local artifacts to assimilate. It is local evidence only: it never calls GitHub to
verify a PR and never runs Git to verify a commit; a missing commit hash is
allowed but recorded as uncertainty; and an operator note never overrides a safety
failure. The `PostMergeValidationIngest` reads the operator-supplied validation
results (full test run, examples, safety invariants, ClaimGuard, short fixture
demo, mini soak, falsification replay, replication registration, operator review,
resource profile) -- it runs no validation itself, and operator-provided
validation is evidence, not proof.

**Candidate baselines are registered and compared.** The append-only
`BaselineRegistry` records each candidate baseline with its evidence index, status
history, and unresolved blockers; old baselines are never deleted and failed/
blocked ones remain visible. The `PostMergeEvidenceAssimilator` gathers the
implementation-intake audits and validation results into one bundle, surfacing
conflicts (e.g. intake recommended merge but post-merge validation failed) and
missing evidence rather than averaging them away -- safety evidence has priority,
and negative/inconclusive evidence is preserved. The `BaselineComparison` then
compares the candidate to its parent across the structural/safety/test dimensions:
improvement requires evidence, a regression stays visible even amid improvements,
and a safety regression dominates every positive metric. There is no empty green
dashboard.

**Regression watch blocks unsafe baselines.** The `RegressionWatch` derives
regression items (safety, test, ClaimGuard, report, example, source/simulation
boundary, contamination, fixture overfit, structural-growth/prediction/
action-effect decreases, habit rigidity, resource blowup, artifact bloat); a
critical regression blocks baseline validation, a major one requires operator
review, and regressions are never hidden behind aggregate scores. The
`ModuleStatusUpdateRecommendation` is metadata only (keep-experimental, validate,
promote, regression-watch, freeze, rollback, block) -- no module is changed and no
source is modified, and safety-critical concerns override promotion. The
`RollbackWatch` recommends (never executes) a rollback when warranted, preserving
all failed artifacts; and the `PostMergeFollowupQueue` records the follow-up work
(reruns, mini soak, falsification replay, replication registration, architecture-
evidence update, operator review / revision prompt) as local metadata that
executes nothing.

**It integrates and stays read-only.** The `PostMergeAssimilationRuntime` is
bounded; it consumes the implementation-intake report (treated as advisory
evidence, never automatic truth -- a Prompt-58 safety block keeps the baseline
blocked unless the operator supplies separate passing safety evidence) and the
experiment-compiler artifacts (to check the original requirements). It emits the
baseline record, module-status recommendations, regression/rollback watches, and
follow-up queue to the Architecture Evolution Lab; recommends mini-soak /
falsification / replication registration for validated baselines (and rollback /
revision / safety review for blocked ones); and feeds the research lab +
evaluation, the operator console (with the mandated safe answers for "did Solaris
merge this?" and "did Solaris run Git?"), and Inner MAP. The
`PostMergeAssimilationSafetyValidator` blocks source modification, Git commands,
GitHub calls, branch creation, PR creation/approval/merge, validation-command
execution, external coding-agent execution, shell/network/browser/OS,
hardware/feeder control, real-world actuation, the human teaching loop, evidence
deletion, and any baseline validation when critical safety evidence fails or
critical evidence is missing. **No source was modified, no Git command was run, no
GitHub call was made, no pull request was created/approved/merged, no validation
command was executed automatically, no external agent was run -- this is
post-merge evidence assimilation only, and no claim of consciousness, sentience,
life, personhood, agency, free will, emotion, feeling, understanding, or
subjective experience is made.**

## Versioned Research Baseline and Reproducibility Bundle

Prompt 59 registers and watches a candidate post-merge baseline; Prompt 60 turns a
*validated* (or validated-with-warnings) baseline into a versioned research
baseline -- `src/solaris_ai_nn/research_baseline/`:

    baseline version -> snapshot manifest -> reproducibility bundle ->
    capability map -> limitation registry -> safety boundary statement ->
    validation summary -> comparison anchors -> next-cycle roadmap -> runbook

It answers the closing question of each cycle: *what exact experimental baseline
are we standing on before the next cycle begins?* This is **not** a product
release, a GitHub release, a certification of consciousness or intelligence, or
autonomous deployment -- it is a reproducible research snapshot.

**Baseline versioning is local metadata, not Git tagging.** The
`ResearchBaselineVersion` assigns a local version id and provenance record to a
validated post-merge baseline; the id is plain metadata -- it creates no Git tag,
no GitHub release, no branch, no PR, and calls no Git/GitHub. A blocked baseline
(or one with a critical safety failure, a critical limitation, or missing required
validation) can never become a validated version. The append-only baseline
registry from Prompt 59 remains the ledger; this layer adds the *versioned,
reproducible* view on top of it.

**The reproducibility bundle indexes artifacts and commands.** The
`ResearchSnapshotManifest` indexes every artifact behind the baseline (reports
from each prior module, validation/example/ClaimGuard results, operator notes),
keeping missing, corrupt, and negative/falsified/inconclusive artifacts visible.
The `ReproBundleBuilder` writes a `REPRO_BUNDLE_MANIFEST.json` + README that
*reference* the Python/dependency requirements, expected state dirs, fixtures,
optional live feeder manifests, and the required/example/test commands -- and
distinguish fixture / replay / live-read-only / operator-provided evidence. The
bundle installs nothing, runs nothing, and fetches nothing.

**The capability map shows what is available and validated.** The
`BaselineCapabilityMap` records, per area (plural sensorium through Inner MAP),
whether the implemented module is available / validated / experimental /
blocked / missing, with limitations and evidence refs. "Capability" means an
implemented module with available evidence -- not intelligence, understanding, or
inner state -- and a capability is never marked validated without validation
evidence (a declared-validated capability with no evidence refs is downgraded to
available).

**The limitation registry prevents false confidence.** The
`BaselineLimitationRegistry` records the baseline's limitations (missing/weak
evidence, insufficient replication, failed falsification, fixture-overfit /
human-label-contamination risk, unresolved regressions/blockers, ...) with a
severity. A critical limitation blocks validated status; a major one permits
validated-with-warnings only if safety holds; and limitations stay
operator-visible, never buried in prose.

**The safety boundary statement is mandatory.** The `SafetyBoundaryStatement`
enumerates the constitutional envelope (no actuation/hardware/feeder/network/
shell, no source self-rewrite, no Git/GitHub automation, no PR create/merge, no
autonomous agent, no human teaching loop, no sensory-text-as-command, no
human-label-as-ground-truth, no simulation-as-observation, no unsupported
consciousness/life/agency claims, no deletion of negative/falsified evidence),
each with a status supported by safety artifacts; missing safety evidence is
visible, a failed boundary blocks validation, and the statement appears in every
baseline report. The `BaselineValidationSummary` summarizes per-dimension
validation (a safety failure or missing required validation blocks validation;
passing tests do not prove scientific claims).

**The next-cycle roadmap resets the research loop.** The `ComparisonAnchorSet`
records the parent / previous-validated / control / ablation anchors future
replication/soak/architecture comparisons measure against (a missing anchor is a
limitation; control anchors stay available even if weak). The
`NextCycleRoadmapReset` lists the next experiments (validation, soak, replication,
falsification, architecture evolution, compile/audit/assimilate, evidence
improvement) with required/recommended/optional/blocked priorities -- planning
only, executing nothing -- and the `BaselineOperatorRunbook` gives a human
operator step-by-step instructions (with explicit stop conditions for safety
failures) and never executes a command.

**It integrates and stays local.** The `ResearchBaselineRuntime` is bounded; it
consumes the post-merge assimilation + implementation-intake evidence, exports a
clean starting point (version, capability map, limitations, roadmap, anchors,
missing-evidence) to the Architecture Evolution Lab, recommends soak/replication
for validated baselines (rollback/revision/safety-review for blocked ones), and
feeds the research lab + evaluation, the operator console (with the mandated safe
answers for "is this a release?", "did Solaris create a Git tag?", and "does this
prove consciousness?"), and Inner MAP. The `ResearchBaselineSafetyValidator`
blocks Git tag/release creation, Git/GitHub calls, branch/PR creation, source
modification, validation-command execution, external-agent execution, shell/
network/browser/OS, hardware/feeder control, actuation, the human teaching loop,
evidence deletion, and any validated baseline when critical safety evidence fails
or required validation is missing. **A research baseline is a local reproducible
experimental reference point: no Git tag, GitHub release, branch, or PR was
created, no source was modified, no validation command was executed
automatically, no external agent was run, and no claim of consciousness,
sentience, life, personhood, agency, free will, emotion, feeling, understanding,
or subjective experience is made.**

## Closed Research Cycle Orchestrator

**The closed research cycle orchestrator tracks where the research program is in
its experimental cycle.** Prompt 60 builds a versioned research baseline; the
`research_cycle` package (Prompt 61) sits above it and answers a single question:
*where is the research program in its experimental cycle, what evidence supports
the current state, what is blocked, and what should the human operator do next?*
It tracks the scientific state across cycles -- Research Baseline -> Next-Cycle
Roadmap -> Architecture Evolution Proposal -> Experiment Compiler Pack -> External
Human/Agent Implementation -> Implementation Intake Audit -> Human Merge (outside
Solaris) -> Post-Merge Assimilation -> New Research Baseline -> Soak / Replication
/ Falsification -> Next Architecture Evolution. It does not run the system
autonomously, implement code, approve anything, or execute external tools.

**The cycle state is derived from evidence, never self-asserted.** The
`ResearchCycleManifest` records the local refs (paths/ids) that constitute one
cycle (baseline, roadmap, architecture-evolution, experiment-compiler, intake,
post-merge, research-baseline, soak, replication, falsification, safety, operator
decisions) and the current cycle state; parent/child cycles are experimental
provenance, not biological lineage. `determine_state` derives the descriptive
`ResearchCycleState` (stage + status) from which evidence is present -- the
furthest stage with evidence wins, missing evidence stays visible, and the state
can never approve itself. The `CycleTransitionEngine` proposes gate-checked,
advisory stage transitions; no transition executes an external action or implies
Solaris changed source.

**Evidence is preserved, gates are advisory, decisions are the operator's.** The
`EvidenceContinuityLedger` is an append-only record where negative, falsified,
and missing evidence are preserved and stale evidence is marked superseded, never
deleted. The `ResearchArtifactGraph` records artifact provenance (derived_from,
validates, blocks, supersedes, contradicts, supports, requires, missing_for,
operator_confirmed, safety_blocks, falsifies); contradictions and missing nodes
stay visible and conflicting evidence is never collapsed into a single score. The
`ResearchCycleDecisionGate` evaluates the gates between stages: safety failures,
falsified core claims, and critical regressions block promotion gates; missing
critical evidence blocks gates; and operator-decision gates report
`waiting_for_operator` until an explicit local `OperatorDecisionRecord` exists --
Solaris cannot invent or auto-approve operator approval. The
`BlockedStateResolver` detects why a cycle is blocked and recommends a resolution
(recommend-only); a critical safety blocker can never be bypassed. The
`NextActionPlanner` recommends the next operator action from the stage and
blockers; next actions are instructions for the operator, none is executed, and
if the cycle is blocked the next action is blocker resolution.

**It integrates and stays local.** The bounded `ResearchCycleRuntime` loads a
local evidence bundle, updates the ledger, builds the artifact graph, evaluates
gates, determines the state, proposes transitions, detects blocked states,
generates next actions, may archive a cycle only on an explicit operator
decision, and writes the `RESEARCH_CYCLE_REPORT` plus the cycle-state /
evidence-ledger / artifact-graph / decision-gates / operator-decisions /
blocked-states / next-actions / archive documents (ClaimGuard-scanned). It feeds
the evaluation protocols, the operator console (with the mandated safe answers for
"what is the next action?", "did Solaris approve itself?", and "did Solaris run
Git or GitHub?"), the conscience scenario profiles, and Inner MAP. The
`ResearchCycleArchive` keeps archived cycles visible (artifacts are never deleted;
an archived cycle can be used as future evidence). The
`ResearchCycleSafetyValidator` blocks source modification, Git commands, GitHub
calls, branch/tag/release creation, PR creation/approval/merge, validation-command
execution, external-agent execution, shell/network/browser/OS, hardware/feeder
control, actuation, the human teaching loop, sensory-text-as-command,
human-label-as-ground-truth, evidence deletion, auto-approval of operator
decisions, and any bypass of a critical safety blocker. **The closed research
cycle orchestrator tracks the scientific state only: it reads local artifacts and
writes reports, it modifies no source, runs no Git, calls no GitHub, creates no
branch/tag/release/PR, opens or merges no PR, executes no validation command, runs
no external agent, never approves itself, and makes no claim of consciousness,
sentience, life, personhood, agency, free will, emotion, feeling, understanding,
or subjective experience.**

## Scientific Claim Registry and Theory Ledger

**The scientific claim layer is the discipline that prevents hype drift.** Prompts
41-61 built an experimental research architecture and a closed evidence cycle. The
`scientific_claims` package (Prompt 62) sits above all of them and answers a single
disciplined question: *what can we safely claim from the evidence, what is merely
suggested, what is unsupported, what is falsified, what is forbidden to claim, what
evidence supports or contradicts each claim, what further experiment is needed, and
what may appear in a paper / README / internal note?* It is a scientific claim
registry and publication evidence compiler -- not a marketing generator, not hype
production, and not a consciousness-declaration system.

**Evidence does not automatically become a claim.** The `ClaimRegistry` is an
append-only registry where every `ScientificClaim` carries evidence refs or an
explicit missing-evidence reason; a claim with no evidence basis is recorded as
unsupported, never silently dropped. The `EvidenceMap` links claims to evidence
many-to-many across every research layer (baseline, cycle, architecture evolution,
soak, replication/falsification, developmental life, sensorium differentiation,
metabolism, ontogenesis, semiogenesis, cognition, self-boundary, desire formation,
action-reaction, intake, post-merge, safety, evaluation, operator notes) with a
role (supports/weakly_supports/contradicts/falsifies/limits/contextualizes/missing/
inconclusive/negative_result/safety_boundary). No claim can be "supported" without
supporting evidence, and contradictory evidence is preserved, not collapsed.

**Counterevidence and falsified claims are preserved, never buried.** The
`CounterEvidenceAnalyzer` detects counterevidence (failed replication, falsification
failure, passive-parser equivalence, log-accumulation warning, fixture overfit,
human-label dependency, missing live data, failed tests, safety regression,
ClaimGuard failure, contradictory metric, insufficient sample size, missing
artifact, operator uncertainty) and keeps it as visible as the evidence for a
claim; blocking counterevidence (falsification, safety regression, ClaimGuard
failure) blocks a claim outright. The `ClaimStrengthEvaluator` scores a claim's
strength (none/weak/moderate/strong/inconclusive/blocked): strong requires
replication or strong controls, falsified core evidence and safety failures block
strength, inconclusive is a valid outcome, and no consciousness/life/agency score
exists. The `TheoryLedger` holds working hypotheses across the theory areas;
revisions preserve prior versions, contradictions link to counterevidence, and
challenged/falsified/retired statements stay archived. Theory is a hypothesis under
evidence, never proof.

**Forbidden claims are blocked; the dossier is a draft, not a release.** The
`ForbiddenClaimDetector` flags assertions of consciousness, sentience, biological
life, personhood, agency, free will, emotion, feeling, subjective experience,
self-awareness, understanding, autonomous self-improvement, real-world autonomy,
hardware control, or human/animal/living-organism equivalence -- such wording may
appear only as an explicit disclaimer; ambiguous phrasing is warned; any dossier
that asserts a forbidden claim is blocked. The `LimitationsBuilder` makes
limitations mandatory, specific, and linked to the claims they constrain (the
"no consciousness / subjective / agency / real-world actuation evidence"
limitations are always present). The `ScientificAbstractBuilder` produces
claim-constrained abstracts (internal summary, technical preprint, README-safe,
operator brief, negative-result, inconclusive-result) that state when evidence is
weak and fall back to a negative/inconclusive abstract when no publishable claim
exists. The `PublicationDossierBuilder` assembles a draft evidence dossier (with
evidence/claim/counterevidence tables, replication and falsification status, safety
boundaries, limitations, negative results, future work, and explicitly rejected
forbidden claims) and reports a readiness status (ready-as-internal-report /
preprint-draft / with-major-limitations / not-ready / blocked-by-counterevidence /
blocked-by-safety / blocked-by-forbidden-claims / inconclusive). The
`ClaimGuardBridge` scans all generated text and a ClaimGuard failure blocks
readiness.

**It integrates and stays evidence-disciplined.** The bounded
`ScientificClaimRuntime` reads the prior-layer evidence, builds the evidence map and
claim registry, updates the theory ledger, detects counterevidence and forbidden
claims, scores strength, builds limitations and safe abstracts, assembles the draft
dossier, runs the ClaimGuard bridge, and writes the report set. It feeds Architecture
Evolution (falsified claims block variant promotion; claim gaps prioritise evidence),
the Experiment Compiler (claim gaps -> live-field / replication / contamination /
falsification packs), the Operator Console (with the mandated safe answer for "can I
say Solaris is conscious?"), Inner MAP, and Evaluation. The
`ScientificClaimSafetyValidator` blocks unsupported consciousness/sentience/life/
personhood/agency/free-will/emotion/understanding/self-awareness/subjective-experience
and autonomous-self-improvement claims, the deletion of falsified/negative/
inconclusive evidence, the hiding of limitations, publication readiness when
forbidden claims are asserted or safety evidence fails, and any source/Git/GitHub/
release/experiment/external-agent/hardware action. **The scientific claim registry
maps evidence to claims and blocks unsupported or forbidden claims. It reads local
artifacts and writes reports only; the publication dossier is a draft evidence
compilation, not a release; and it proves nothing about consciousness, sentience,
biological life, personhood, agency, free will, emotion, feeling, understanding,
self-awareness, or subjective experience.**

## Independent Reproducibility Review and Peer Audit Pack

**The independent review layer prepares a local, offline package for external
inspection -- without ever going outside.** Prompt 62 produced a scientific claim
registry and a draft publication dossier. The `independent_review` package
(Prompt 63) prepares the artifacts an external reviewer would need to inspect,
reproduce, and attack the work *locally*. It answers: *what evidence can a reviewer
inspect, what commands would reproduce the bounded demos, what artifacts are
required or missing, what claims are reviewable or blocked, what falsification
tests and controls should a reviewer run, what questions should a hostile reviewer
ask, what objections have been raised, what responses exist, and what remains
unresolved?* It is a local preparation layer for independent reproducibility and
critique -- not publishing, not external submission, not a marketing kit, and not
an automatic peer-review system.

**It indexes and sanitizes artifacts without modifying them.** The
`IndependentReviewManifest` indexes the local artifacts a reviewer could inspect
(baseline, reproducibility bundle, claim/theory/evidence/counterevidence/
limitations reports, soak/replication/falsification reports, cycle/architecture/
intake/post-merge/safety/evaluation reports, fixtures, synthetic examples, operator
notes); it indexes local artifacts only, uploads nothing, keeps missing artifacts
visible, and always includes negative, falsified, and inconclusive evidence. The
`ReviewArtifactSanitizer` scans local text for leak risks (local absolute paths,
private notes, secrets/tokens/API keys, personal emails, machine paths, private
URLs, credentials, forbidden-claim wording, ambiguous hype, large-binary
references, missing license/readme); it scans text only, modifies nothing
automatically, and a critical finding (a secret, an API key, a credential, an
asserted forbidden claim) blocks review readiness -- the operator decides what to
redact.

**It builds reviewer packs, reproducibility challenges, and hostile questions.**
The `ReviewerPackBuilder` assembles a claim-constrained reviewer pack (scope, what
is and is not being claimed, the baseline under review, the artifact list, required
and optional commands, fixture/replay instructions, safety boundaries, claim /
counterevidence / limitations tables, falsification tests, control comparisons,
expected outputs, common failure modes, a reviewer checklist, and unresolved
questions) that includes forbidden-claim disclaimers and hides no negative
evidence. The `ReproducibilityChallengeBuilder` generates the challenges a reviewer
would run (fixture demo, claim-report and safe-abstract reproduction, falsification
replay, passive-parser / no-metabolism / no-semiogenesis controls, shuffled order,
random labels, growth-vs-accumulation, ClaimGuard scan, safety invariant scan) as
instructions only -- nothing is executed, every challenge lists expected artifacts
and how to read a failure, and a missing prerequisite marks a challenge
unavailable. The `ReviewerQuestionGenerator` produces hostile-but-useful questions
linked to claims; the `AdversarialReviewEngine` generates deflationary alternative
explanations (log accumulation, fixture overfit, label leakage, passive-parser
artifact, seed artifact, reporting bias, missing control, insufficient runtime/
replication, cherry-picking, confirmation bias, ClaimGuard blind spot, measurement/
source-diet/safety-boundary artifacts), preserved and never auto-dismissed, each
with the evidence needed to reduce its uncertainty; a strong alternative downgrades
readiness.

**It preserves objections and reports readiness honestly.** The
`IndependentReviewAuditMatrix` builds one row per claim (supporting evidence,
counterevidence, required artifacts, reproduction challenge, control, falsification
test, safety boundary, limitation, reviewer question, status, blocker flag) and
exposes gaps -- there is no empty green dashboard, and falsified/unsupported claims
stay visible. The `ReviewerResponseLedger` is an append-only record of objections
and responses: objections cannot be deleted, accepted limitations and
falsifications stay visible, responses cite evidence refs or admit missing
evidence, and the system cannot declare victory over a reviewer by default. The
`IndependentReviewReadinessEvaluator` decides whether the package is ready for
internal, friendly external, or hostile external review; hostile-review readiness
requires strong documentation, not strong claims, a weak or negative result can
still be review-ready if documented honestly, and an asserted forbidden claim
blocks readiness. The bounded `IndependentReviewRuntime` assembles all of this,
feeds Architecture Evolution / Experiment Compiler (unresolved objections and
strong alternatives become future experiment inputs), the Operator Console (with
the mandated safe answers for "is this ready for external review?" and "did Solaris
publish anything?"), Inner MAP, and Evaluation. The
`IndependentReviewSafetyValidator` blocks publishing, upload, external API and
Git/GitHub calls, branch/tag/release/PR creation, experiment or command execution,
external-agent runs, hardware/feeder/network/shell access, unsupported claims, the
deletion of negative/falsified/inconclusive evidence, the hiding of sanitizer
failures, and hostile-review readiness when forbidden claims are asserted. **The
independent review layer generates local reviewer packs, reproducibility
challenges, audit matrices, and response ledgers. It does not publish, upload,
contact reviewers, call GitHub or external services, run Git, execute commands or
experiments, run external agents, modify artifacts, or make any claim of
consciousness, sentience, biological life, personhood, agency, free will, emotion,
feeling, understanding, self-awareness, or subjective experience.**

## Reviewer Feedback Assimilation

**Reviewer feedback is research evidence, not training data.** Prompt 63 prepared a
local independent review pack and a response ledger. The `review_assimilation`
package (Prompt 64) assimilates the *results* of that review back into the
scientific and experimental cycle. It ingests local reviewer objections, the
response ledger, adversarial findings, audit-matrix blockers, reproduction
outcomes, sanitizer findings, the review-readiness report, reviewer notes, and
proposed reviewer experiments, and turns them into structured research evidence.
This is explicitly *not* a Human Feedback / Teaching Loop, *not* RLHF, *not* model
training, and *not* public peer-review automation -- reviewer feedback is stored
and reasoned about as evidence, and the model is never updated from it.

**Objections are classified and preserved, never dismissed.** The
`ReviewerObjectionClassifier` assigns each objection a category, a severity, and a
validity status; objections are never dismissed by default, "invalid with
evidence" requires evidence refs, and a critical open objection blocks the relevant
claim and readiness status. The `ReviewerReproductionOutcomeIngestor` records the
outcome of a reviewer running a reproducibility challenge: failed and partial
reproduction are evidence, successful reproduction proves nothing about
consciousness/life/agency, and a missing artifact is the project's limitation
rather than reviewer failure. Reproduction outcomes impact claim strength.

**Impact and gaps become proposals and next-cycle tasks.** The
`ClaimImpactAssessor` maps objections and reproduction outcomes to per-claim impact
(strengthen / weaken / downgrade / mark unsupported / contradicted / falsified /
forbidden / require more evidence / require rewording), where falsification
downgrades or blocks and a forbidden-claim risk blocks publication readiness. The
`TheoryImpactAssessor` maps theory-level objections to theory impact, preserving
prior statements and preferring narrowing over hype. The
`ReviewEvidenceGapMapBuilder` derives the evidence gaps a review exposed and maps
them to claims or blockers; critical gaps block readiness, and every gap becomes a
next-cycle experiment or documentation task. The
`ReviewDrivenExperimentRecommender` turns gaps and objections into recommended
experiments (passive-parser / ablation / shuffled-order / random-label controls,
live comparison, longer soak, replication, falsification, metric/documentation
improvements) -- instructions only, never executed, suitable as Architecture
Evolution and Experiment Compiler inputs.

**Claim revisions are proposed, not silently applied; critical objections can
block publication.** The `ClaimRevisionProposer` produces structured revision
proposals (downgrade strength, narrow scope, add limitation/counterevidence, mark
inconclusive/unsupported/falsified/forbidden, rewrite safe wording, remove public
claim, request more evidence) that do not edit the claim registry; unsafe proposed
wording is blocked by ClaimGuard and safe wording still includes limitations. The
`PublicationReadinessReviser` revises the advisory publication readiness, blocking
it on forbidden claims, unresolved critical objections, failed reproductions, or
critical missing evidence. The `ReviewAssimilationQueue` holds the next-cycle tasks
as local metadata that executes nothing and preserves unresolved items. The bounded
`ReviewerFeedbackAssimilationRuntime` assembles all of this and feeds structured
proposals to Scientific Claims, evidence gaps and the queue to the Research Cycle,
experiment recommendations to Architecture Evolution and the Experiment Compiler,
and status to the Operator Console (with the mandated safe answers for "did
reviewer feedback train the model?", "did Solaris contact reviewers?", and "can we
publish after this review?"), Inner MAP, and Evaluation. The
`ReviewerFeedbackAssimilationSafetyValidator` blocks publishing, upload, reviewer
contact, external API and Git/GitHub calls, branch/tag/release/PR creation,
experiment or command execution, external-agent runs, hardware/feeder/network/shell
access, any Human Feedback / Teaching Loop or training from feedback, unsupported
claims, the deletion of negative/falsified/inconclusive evidence, the hiding of
unresolved objections, and publication readiness while critical objections are
unresolved or forbidden claims are asserted. **Reviewer Feedback Assimilation turns
local reviewer objections and reproduction outcomes into claim revisions, evidence
gaps, and future experiment recommendations. It does not train models, contact
reviewers, publish artifacts, run experiments, or execute external services, and it
makes no claim of consciousness, sentience, biological life, personhood, agency,
free will, emotion, feeling, understanding, self-awareness, or subjective
experience.**

## Alpha Research System Assembly

**The Alpha Research System is the unified local operator entry point.** Prompts
41-64 produced many organismic, scientific, governance, review, and claim-control
layers. The `alpha_system` package (Prompt 65) does not add another theory layer --
it assembles those modules into a coherent, operable, bounded local research run so
an operator can issue one bounded command and watch Solaris-AI-NN move from fixture
sensorium input to an alpha report, scientific claims, review readiness, and a next
action. It is reached through the unified CLI (`python -m solaris_ai_nn ...`) and
the matching `examples/run_alpha_e2e_demo.py`.

**It is fixture-only by default, and honest about what is missing.** The
`AlphaResearchProfile` (default `alpha_fixture_e2e_v0`) is fixture-only: it requires
no live feeders, no network, and no Git/GitHub, and it never runs unbounded. Live
read-only profiles exist only as metadata and are blocked unless governance
artifacts exist. The `AlphaModuleRegistry` records, by import-spec only (no module
is executed), whether each of the Prompt 41-64 modules is available; it never
crashes on a missing module, missing optional modules warn, and a missing
required-alpha module blocks the specific command rather than the whole CLI. The
`AlphaStateLayout` creates the local state tree under one chosen root, reusing
existing directories and never deleting state, and writes an
`ALPHA_STATE_MANIFEST.json`.

**It checks, runs, and reports a bounded fixture path.** The `AlphaSystemCheck`
(doctor) runs read-only checks -- package importable, state writable, profile
valid, registry built, safety validator and ClaimGuard available, no live mode by
default, no network/Git/GitHub requirement, no feeder auto-start, no unbounded
runtime, no unsupported claim text -- each as a pass/info/warning/blocker. The
`AlphaDemoPlan` lays out the bounded fixture path (initialize state, load/create the
fixture stream, run the organismic passes, generate the evidence/claim/review/cycle
summaries, and write the alpha report); every step is bounded, a missing optional
module is skipped honestly (never faked), and a missing required foundation blocks
the demo. The `AlphaResearchOrchestrator` drives all of this: it records present
organismic modules as a clearly-labelled alpha fallback (the module's full
scientific run is not invoked here) and absent ones as skipped markers, and it calls
the Scientific Claims, Independent Review, and Research Cycle modules in demo-safe
report-only mode when available (with safe placeholders otherwise). The
`AlphaArtifactIndex` indexes the run's artifacts and its missing/skipped markers
(per run id; stale artifacts are never deleted); the `AlphaCycleStatus` reports the
descriptive stage and an advisory next action (never executed); the
`AlphaOperatorRunbook` gives the operator the command sequence, stop conditions, and
forbidden interpretations; and the `AlphaResearchReportBuilder` writes the alpha
report set (ClaimGuard-scanned, with skipped modules and blockers always shown).

**It stays local, bounded, and claim-constrained.** The
`AlphaResearchSafetyValidator` blocks real-world actuation, hardware/feeder control
and auto-start, network/shell/browser/OS access, Git/GitHub calls,
branch/tag/release/PR creation, upload, publishing, external-agent execution,
runtime validation-command execution, unbounded loops, source self-rewrite,
sensory-text-as-command, human-label-as-ground-truth, unsupported consciousness/
life/agency claims, and the hiding of skipped modules, missing artifacts, or failed
checks. The alpha state feeds Inner MAP and Evaluation. **The Alpha Research System
is a local fixture-only research orchestration layer. It does not call GitHub, run
Git, publish artifacts, upload files, create branches, control feeders/hardware,
execute external agents, or prove consciousness, sentience, biological life,
personhood, agency, free will, emotion, feeling, understanding, self-awareness, or
subjective experience. Alpha is not a product release.**

## Technical Whitepaper and Architecture Book

The documentation generator (`architecture_book` package, Prompt 66) reconstructs
the whole project -- Prompts 41-65 -- into coherent local Markdown: a technical
overview, a full whitepaper, a longer architecture book, Mermaid diagrams, a
glossary, a module map, a research roadmap, a safety-boundary document, appendices,
and a documentation index. This is documentation reconstruction, not marketing,
not a public release, and not proof of intelligence; it answers whether a
technically competent reader can understand what Solaris-AI-NN is, how its modules
relate, what evidence it produces, and what claims it permits and forbids.

**It is local, honest, and claim-constrained.** The `ArchitectureSourceCollector`
summarizes local sources read-only (README, docs, examples, and the alpha/claims/
baseline/cycle/review state dirs); the `DocumentationManifest` lists missing and
contradictory sources explicitly and never pretends missing material exists. The
`SolarisArchitectureOutlineBuilder` builds the Part I-VII outline and marks
planned/missing modules honestly; the `DiagramBuilder` emits Mermaid diagrams that
imply no autonomous code modification; the `GlossaryBuilder` defines every term
technically with metaphor and forbidden-claim clarifications; the
`TechnicalWhitepaperBuilder`, `ArchitectureBookBuilder`, and
`ArchitectureAppendixBuilder` produce the documents; and the
`DocumentationIndexBuilder` lists them and the missing ones. The
`ArchitectureBookRuntime` is bounded and writes documentation only -- it
publishes nothing, uploads nothing, calls no Git/GitHub, runs no Git, runs no
external agent, executes no experiment, controls no hardware/feeders/network/shell,
and generates no unsupported claim. The `ArchitectureBookSafetyValidator` scans
generated text and blocks forbidden inner-state claims and marketing language;
ClaimGuard scans the Markdown. The generator complements the Alpha CLI: it is
reached via `python -m solaris_ai_nn build-docs` / `docs-index` / `whitepaper`,
feeds Inner MAP and Evaluation, and reads the alpha/claims/review reports as
documentation sources. **The Technical Whitepaper and Architecture Book generator
creates local Markdown documentation only. It does not publish, upload, call
GitHub, run Git, create releases, execute experiments, run external agents, or
make any claim of consciousness, sentience, biological life, personhood, agency,
free will, emotion, feeling, understanding, self-awareness, or subjective
experience.**
