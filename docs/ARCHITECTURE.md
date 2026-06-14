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
