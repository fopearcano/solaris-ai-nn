# Experiments

Every claim in Solaris-AI-NN must reduce to a runnable experiment with metrics.
This document defines the experiment catalogue. Phase-0 ships the first one;
the rest are specified here as the next concrete steps.

A note on honesty: these experiments test *mechanisms*, not minds. "Learning",
"habit", and "anticipation" here name measurable changes in weights, biases, and
prediction error — never subjective experience.

---

## 1. Minimal continuous ESN experiment ✅ (implemented)

**File:** `src/solaris_ai_nn/experiments/minimal_continuous_esn.py`
**Run:** `python examples/run_minimal_continuous_esn.py`

**Setup.** A tiny world maps three stimulus payloads to one correct action each
(`light→approach`, `noise→withdraw`, `food→consume`). The loop runs heartbeats,
receives cycling stimuli (with periodic silence), produces actions, and gets
`+1/−1` reactions. The readout starts at zero (no prior knowledge).

**What it demonstrates.**
- Behaviour changes over time: late-window accuracy ≫ early-window accuracy
  (~55% → ~95%).
- Online NLMS readout updates drive prediction error down (~1.0 → ~0.17).
- Habit weights strengthen on rewarded `(situation, action)` pathways.
- Synthesis subtracts weak readout weights (non-empty `SubtractionReport`).

**Metrics.** early/late accuracy, average & recent prediction error, habit
pathway count + strong count, pruned-pathway count, readout non-zero weights.

**Pass criteria (asserted in tests).** completes promptly (no infinite loop),
`late_accuracy > early_accuracy`, habit pathways learned, deterministic per seed.

---

## 2. Repeated stimulus / changing reaction experiment (specified)

**Goal.** Test plasticity when the world *changes its mind*: a pattern that
rewarded `approach` for N steps suddenly rewards `withdraw`.

**Setup.** Same world, but flip one pattern's correct action at the midpoint.

**Expected.** Accuracy dips at the flip, then recovers as online updates and
habit re-reinforcement adapt — quantifying *adaptation latency* and confirming
the substrate is not frozen. Watch habit bias for the old pathway decay and the
new one grow.

**Metrics.** post-flip recovery time (steps to regain threshold accuracy), habit
bias trajectories, drift spike at the flip.

---

## 3. Absence-stimulus experiment (specified)

**Goal.** Characterise the Subtraction Principle in isolation.

**Setup.** Long stretches of silence (no external stimulus) so the loop
synthesises escalating absence stimuli ("I exist!").

**Expected.** The reservoir stays active during silence; absence-intensity
escalates then resets; the substrate forms a distinct internal-state signature
for absence vs presence.

**Metrics.** absence-event count, reservoir state energy during silence vs
stimulation, separability of absence vs presence states.

> **Now realised through the bridge** — see *§7 Absence-Stimulus Bridge
> Experiment* below for the implemented version driving `SolarisNeuralBridge`.

---

## 4. LogosTension-driven adaptation experiment (specified)

**Goal.** Use `LogosTension` (division/union/fracture) as an input feature and
test whether the substrate's behaviour tracks fracture.

**Setup.** Inject `LogosTension` signals alongside stimuli; vary fracture; make
the correct action depend on fracture level (high fracture ⇒ different response).

**Expected.** The readout learns to condition action choice on the fracture
slot — a concrete bridge from Logos's "fracture is the substrate of choice" to a
measurable decision boundary.

**Metrics.** accuracy conditioned on fracture band; weight magnitude on the
fracture input slot.

---

## 5. Habit vs synthesis experiment (specified)

**Goal.** Make the habit↔synthesis tension explicit and measurable.

**Setup.** Run four ablations: {habit on/off} × {synthesis on/off} on the same
world and seed.

**Expected.** Habit accelerates exploitation of rewarded pathways; synthesis
keeps the readout sparse and discards stale pathways. Together they should retain
accuracy while reducing non-zero weights. Quantifies the claim that *synthesis
proceeds by subtraction* without destroying competence.

**Metrics.** accuracy, non-zero readout weights, habit mass, pruned count — per
ablation.

---

## 6. 24-hour soak test plan (specified)

**Goal.** Validate the central thesis: *long-running weak adaptation > expensive
one-shot intelligence*, and prove the substrate is stable over very long runs.

**Setup.**
- Drive an `ExperimentLoop` via `run_until(stop=deadline, safety_limit=…)`.
- Stream a non-stationary mixture of the above worlds (occasional rule flips,
  silence periods, varying intensity, injected `LogosTension`).
- Bound memory: `TraceMemory.capacity`, `StateMemory.capacity`, and rotating
  JSONL via `JsonlWriter`.

**Instrumentation (sampled to JSONL every K steps).** step/heartbeat counts,
average & recent prediction error, habit mass + change, pruning passes/count,
state energy, weight drift, reservoir-state snapshots, wall-clock duration and
steps-per-second.

**Pass criteria.**
- Runs the full duration without crash, unbounded memory growth, or state
  saturation.
- Prediction error stays low on stationary segments and recovers after each rule
  flip within a bounded latency.
- Weight drift remains nonzero (still adapting) but bounded (not thrashing).
- Throughput stays comfortably real-time on a single CPU core.

**Failure modes to document.** state saturation (|state|→1 everywhere), weight
collapse to zero from over-aggressive synthesis, and habit lock-in (exploration
too low to recover from a flip).

---

# Phase-1 bridge experiments

These exercise the `SolarisNeuralBridge` compatibility layer (Prompt 2): the NN
substrate consuming Solaris_Ai-style signals and emitting suggestions.

## 7. Absence-Stimulus Bridge Experiment ✅ (implemented)

**File:** `src/solaris_ai_nn/experiments/absence_stimulus_bridge.py`
**Run:** `python examples/run_absence_stimulus_bridge.py`

**Setup.** Two phases through the bridge. *Presence:* external stimuli arrive and
the bridge learns from `+1/−1` reactions. *Silence:* no external input; we
synthesise escalating "I exist!" **absence** stimuli (`is_absence=True`) and feed
them to the bridge, mirroring `core/aion_impulse.py`.

**What it demonstrates.** The reservoir keeps evolving during silence — the
substrate does **not** go inert without external drive.

**Metrics.** presence/silence event counts, mean reservoir energy per phase,
reservoir **state drift across silence**, `went_inert` flag, per-step silence
energy trace.

**Pass criteria (asserted in tests).** runs bounded (no infinite loop),
`silence_state_drift > 0`, `energy_silence_mean > 0`, `went_inert is False`,
silence energy trace is non-constant, and results are deterministic per seed.

## 8. LogosTension Modulation Experiment (specified)

**Goal.** Show that `LogosModulator` (`reservoir/modulation.py`) changes substrate
behaviour as a function of Logos state — without any mysticism.

**Setup.** Process the same stimulus stream through the bridge under three Logos
regimes: (a) none, (b) high `division`, (c) high `union` / high `fracture`. Send
a `LogosTension` to set the regime, then identical stimuli.

**Expected.**
- High **fracture** ⇒ larger input gain ⇒ higher reservoir state energy for the
  same stimulus.
- High **union** ⇒ more exploratory input noise ⇒ more variable tendencies.
- High **division** ⇒ higher reported readout **confidence**;
  high **union** ⇒ lower confidence.

**Metrics.** reservoir energy vs fracture; tendency variance vs union; reported
confidence vs division/union. (Modulation is the identity with no LogosTension,
giving a clean control.)

## 9. Reaction Feedback Experiment (specified)

**Goal.** Isolate that `SolarisNeuralBridge.react()` is what drives learning —
the bridge's analogue of Solaris_Ai's conceptual backpropagation.

**Setup.** Run two matched bridges on the same stimulus stream and seed. One
calls `react()` with informative `+1/−1` valence; the other never reacts (or
reacts with `0.0`).

**Expected.** The reacting bridge's readout weights move and its suggestions
align with rewarded actions; the non-reacting bridge's readout stays at its
initial state and its suggestions do not improve. Habit pathways grow only in the
reacting bridge.

**Metrics.** readout weight drift, suggestion accuracy over time, habit pathway
count and mass — reacting vs non-reacting.

---

# Phase-2 continuity experiments

These exercise the continuity / persistence / restart machinery (Prompt 3):
`ContinuousRunner`, `RuntimeLifecycle`, `PersistenceManager`, `EventReplay`. All
are bounded; only an explicit `continuous=True` removes the bound.

## 10. Soak Continuity Experiment ✅ (implemented)

**File:** `src/solaris_ai_nn/experiments/soak_continuity.py`
**Run:** `python examples/run_soak_continuity.py --steps 500 --state-dir .solaris_ai_nn_state/dev_soak`

**Setup.** A bounded `ContinuousRunner` drives the bridge over the tiny world,
with periodic external stimuli, silence windows (the runner synthesises
continuity/absence stimuli), `+1/−1` reactions, periodic checkpoints, and
occasional synthesis pruning. Telemetry and a continuity log are written to a
state directory.

**What it demonstrates.** A long-running, low-compute substrate that persists its
state and logs its life events — the seed of the 24-hour / 30-day soak tests.

**Metrics.** session/lifetime steps, checkpoints, pruning passes, habit pathways,
reservoir norm, recent prediction error, events/sec, continuity event count.

**Pass criteria (tested).** runs bounded, checkpoint files created, lifecycle ends
`dead`/graceful, snapshot exposes the expected fields.

## 11. Restart Recovery Experiment ✅ (implemented)

**File:** `src/solaris_ai_nn/experiments/restart_recovery.py`
**Run:** `python examples/run_restart_demo.py --state-dir .solaris_ai_nn_state/restart_demo`

**Setup.** Run a bounded session and checkpoint; then construct a *new* runner
over the same state directory, which restores the persisted substrate and
continues.

**What it demonstrates.** The reservoir state, readout weights, and habit weights
survive shutdown/restart; lifetime steps and restart count accumulate.

**Metrics.** restart count, total lifetime steps, restored reservoir norm,
restored habit-weight count, continuity log path.

**Pass criteria (tested).** `lifetime == session1 + session2`, restored reservoir
norm > 0, restored habit count > 0, and a clean restart logs no unexpected death.

## 12. Simulated Brain-Death Gap Experiment ✅ (implemented)

**Run:** `python examples/run_restart_demo.py --simulate-crash`

**Setup.** Identical to the restart demo, but between sessions the first
session's manifest is rewritten to look like an ungraceful exit (no graceful
flag, backdated last heartbeat). This reproduces a crash's *on-disk condition
without killing the Python process*.

**What it demonstrates.** On the next startup the runner logs
`unexpected_death_detected` and a `brain_death_gap` whose duration is the time
since the last heartbeat — death treated as a first-class, measurable event.

**Pass criteria (tested).** unexpected death detected, brain-death gap ≈ the
backdated interval, both events present in the continuity log, and the process
returns normally (never killed).

## 13. Replay Experiment ✅ (implemented)

**File:** `src/solaris_ai_nn/runtime/replay.py`

**Setup.** A recorded `trace_events.jsonl` (written during a soak/restart run) is
loaded by `EventReplay` and fed back into a fresh, identically-seeded bridge.

**What it demonstrates.** Long-running behaviour is reproducible enough to study:
replaying the same trace into two identically-seeded fresh bridges yields
identical telemetry and identical reservoir state.

**Metrics.** events replayed, equality of telemetry (events, readout updates,
average prediction error) and of final reservoir state across replays.

**Pass criteria (tested).** deterministic telemetry within tolerance, `max_events`
honoured, replayed event count matches the trace's signal rows.
