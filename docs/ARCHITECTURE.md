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

## 11. Future bridge to the real Solaris_Ai runtime

`bridges/` is the integration seam. `signals/adapters.py` handles dataclass↔dict
conversion; `bridges/signal_bridge.py` is the runtime-facing bridge that will
eventually subscribe to a live Solaris_Ai `Bus`, translate inbound signals into
the NN vocabulary, drive an `ExperimentLoop`, and translate Actions/Desires back
out. Today it operates on plain dicts so no dependency on the reference repo is
introduced. `bridges/solaris_reference.py` records, in code, which reference
module inspired each NN module. See ROADMAP Phases 1 and 7.
