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
