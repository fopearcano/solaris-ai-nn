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

---

# Phase-4 Inner MAP experiments

These exercise the Inner MAP self-observation layer (Prompt 4): `InnerMapObserver`,
`InnerMapModel`, `BoundaryRegistry`, `StateGraph`, and `MemoryConsolidator`.

## 14. Inner MAP Evolution Experiment ✅ (implemented)

**File:** `src/solaris_ai_nn/experiments/inner_map_evolution.py`
**Run:** `python examples/run_inner_map_evolution.py --steps 300 --state-dir .solaris_ai_nn_state/inner_map_demo`

**Setup.** A bounded `ContinuousRunner` with periodic stimuli, silence windows
(absence stimuli), mixed `+1/−1` reactions, habit reinforcement, and occasional
synthesis pruning. The Inner MAP is updated every `inner_map_update_interval_steps`
and persisted to `inner_map.json` on each checkpoint.

**What it demonstrates.** The self-model evolves as the substrate runs: reservoir
norm moves, habits strengthen, synthesis subtracts, absence cycles appear, and
tendencies settle — all observable and persisted.

**Metrics / output.** reservoir state norm, strongest habits, pruning count,
recent signal dominance, brain-death gap, hard boundaries, suggested
action/desire, path to `inner_map.json`, and a Mermaid self-map preview.

**Pass criteria (tested).** runs bounded (no infinite loop); the report and the
runner snapshot contain the expected sections (telemetry, lifecycle, bridge,
memory, inner_map, boundaries); `inner_map.json` is written.

## 15. Memory Consolidation Experiment (specified + unit-tested)

**Module:** `memory/consolidation.py` (`MemoryConsolidator`).

**Setup.** Feed a trace with repeated event patterns, absence-stimulus cycles,
actions, and reactions; consolidate over a window.

**Expected.** Structural (not LLM/embedding) consolidation counts repeated
patterns, identifies the dominant signal type, counts absence cycles, summarises
reaction feedback (positive/negative), and finds the stable action tendency — then
emits a `MemoryState` into the Inner MAP.

**Metrics.** `kind_counts`, `dominant_signal_type`, `absence_cycles`,
`reaction_count`, `stable_action` + ratio, `repeated_patterns`.

## 16. Boundary Violation Simulation (specified + unit-tested)

**Module:** `inner_map/boundaries.py` (`BoundaryRegistry`).

**Setup.** Pass simulated state dicts to `check_violation` (e.g. an unbounded run
without an explicit `continuous=True`, or a committed Action).

**Expected.** Hard-boundary violations are reported for: unbounded-without-request,
autonomous action commitment, heavy-ML usage, GPU usage, autonomous file deletion,
and source rewriting. A clean state yields no violations.

**Metrics.** list of `BoundaryViolation` (boundary name + kind + detail).

## 17. State Graph Export Experiment (specified + unit-tested)

**Module:** `inner_map/state_graph.py` (`StateGraph`, `build_default_state_graph`).

**Setup.** Build the default self-map and export it.

**Expected.** The graph contains the runtime/reservoir/readout/memory/habit/
synthesis/telemetry/continuity/bridge/boundaries/tendencies/unknown nodes plus an
`inner_map` observer node, and renders to both Graphviz **DOT** and **Mermaid**
without any external graph library.

**Metrics.** node/edge counts; DOT begins with `digraph`; Mermaid begins with
`flowchart LR`.

---

# Phase-5 plasticity experiments

These exercise the controlled self-modification layer (Prompt 5): the engine,
policy, safety validator, rollback manager, and audit log.

## 18. Plasticity Adaptation Experiment ✅ (implemented)

**File:** `src/solaris_ai_nn/experiments/plasticity_adaptation.py`
**Run:** `python examples/run_plasticity_adaptation.py --enable-plasticity --steps 500`

**Setup.** A bounded session whose reward rule **flips at the midpoint**. With
plasticity enabled, the engine proposes/validates/applies bounded changes
(learning rate, habit weights, pruning threshold, exploration) to help the
substrate re-adapt after the inversion.

**What it demonstrates.** Safe, observable self-modification under changing
feedback: parameters drift within bounds, every step is audited, and behaviour
can re-adapt after the flip.

**Metrics.** applied/rejected counts, learning-rate before/after, exploration
before/after, phase-1 vs after-flip accuracy, plasticity audit path.

**Pass criteria (tested).** runs bounded; audit file written; applied ≥ 1;
report carries before/after metrics; snapshot includes a `plasticity` section.

## 19. Plasticity Dry-Run Experiment ✅ (implemented)

**Run:** `python examples/run_plasticity_dry_run.py`

**Setup.** Identical proposals, but `plasticity_dry_run=True`.

**What it demonstrates.** Proposals are validated and logged but **never
applied** — the safety story made concrete: 0 applied steps and unchanged
parameters, with a non-empty audit of proposals.

**Pass criteria (tested).** `applied_count == 0`; learning rate / exploration
unchanged; audit still records proposals.

## 20. Rollback Experiment ✅ (implemented)

**Run:** `python examples/run_plasticity_adaptation.py --rollback-last`

**Setup.** After an adaptation run, load the persisted brain and roll back the
last applied plasticity step.

**What it demonstrates.** Any applied change is reversible: the parameter is
restored to its previous value and the restoration is verified; rollback history
is reconstructed from the audit log so it works in a fresh process.

**Pass criteria (tested).** `rolled_back is True`; value before ≠ value after;
unknown step ids fail gracefully (manager-level test).

## 21. Feedback Inversion Experiment (covered by §18)

The midpoint reward flip in the adaptation experiment *is* the feedback-inversion
test: it forces the substrate (and the plasticity policy) to cope with a world
that changes its mind, quantifying re-adaptation under controlled mutation.

## 22. Habit vs Synthesis Plasticity Benchmark (implemented)

**Module:** `plasticity/benchmarks.py` (`PlasticityBenchmark`,
`run_habit_vs_synthesis_benchmark`).

**Setup.** Run the same feedback-inversion world twice — plasticity on vs off —
on the same seed.

**What it demonstrates.** The concrete effect of controlled self-modification:
applied-step count, learning-rate / exploration drift, residual prediction error,
and habit-pathway counts, side by side.

**Metrics.** `with_plasticity` vs `without_plasticity` dicts of the above.

---

# Phase-6 substrate-laboratory experiments

These exercise the interchangeable substrates (Prompt 6): `SubstrateRegistry`,
`LiquidStateSubstrate`, `SpikingRecurrentSubstrate`, `SubstrateSwitcher`, and
the shared metrics.

## 23. Substrate Comparison Experiment ✅ (implemented)

**File:** `src/solaris_ai_nn/experiments/substrate_comparison.py`
**Run:** `python examples/run_substrate_comparison.py --steps 300`

**Setup.** The *same deterministic event trace* (cycling stimuli, periodic
silence with escalating absence stimuli, `+1/−1` reactions, identical synthesis
cadence) is run through identical bridges that differ only in substrate.

**What it demonstrates.** The substrates' different temporal characters under
one signal ecology — e.g. the ESN's dense smooth activity vs the spiking
substrate's sparse binary events (which, on the toy world, let the NLMS readout
converge fastest).

**Metrics.** activity rate, mean state drift, early/late accuracy + adaptation
gain, recent prediction error, habit reinforcements/pathways, pruning
passes/pruned pathways, spike rate, memory trace length, duration, updates/sec,
and the **energy proxy** (updates/sec per average active unit — a crude
indicator, not a power measurement).

**Pass criteria (tested).** bounded run, full metric rows per substrate, table
renders, unknown substrate rejected, deterministic per seed.

## 24. Spiking Silence Experiment ✅ (implemented)

**File:** `src/solaris_ai_nn/experiments/spiking_silence.py`
**Run:** `python examples/run_spiking_silence.py --steps 300`

**Setup.** Three equal phases per substrate (liquid-state, spiking-recurrent):
external stimuli → silence with escalating "I exist!" absence stimuli → stimuli
again.

**What it demonstrates.** Spike-based substrates keep evolving through silence:
non-zero activity, non-zero drift, and a measurable state shift across the
silent phase. "Not inert" means non-zero changing numbers — no consciousness
claim.

**Pass criteria (tested).** bounded run; `silence_state_shift > 0`; per-phase
drift > 0; `went_inert is False`; deterministic per seed.

## 25. Substrate Switch/Rollback Experiment ✅ (implemented as tests)

**Module:** `substrates/switching.py` (`SubstrateSwitcher`).

**What it demonstrates.** A switch requires `explicit=True` (automatic/policy
switching raises and is also a forbidden plasticity mutation); the old
substrate is checkpointed *before* the switch and never discarded; state
transfers only when dimensions match (safe zero start otherwise); the new
substrate is checkpointed after; `rollback_switch` restores the previous
substrate bit-for-bit from its checkpoint; the Inner MAP records switch history.

## 26. Activity Drift Experiment (specified; metrics ship today)

**Goal.** Characterise long-horizon drift per substrate: feed a stationary
stimulus distribution for many steps and track `metrics().drift` and state-norm
trajectories. Expected: the ESN settles into a tight orbit; the spiking
substrate stays "twitchy" (high per-step drift, bounded norm). Builds directly
on `substrates/metrics.py` — pair with the Phase-2 soak machinery for hours-long
runs.

## 27. Energy Proxy Experiment (specified; proxy ships today)

**Goal.** Compare "work per active unit" across substrates and state sizes
using `energy_proxy` (updates/sec ÷ average active units), explicitly labelled
a crude software indicator. Expected: sparse spiking substrates sustain far more
updates per active unit — the low-compute argument made measurable. Future:
correlate with wall-clock CPU time per step at varying state sizes.

---

# Phase-7 integration experiments

These exercise the optional Solaris_Ai sidecar (`integration/`). None require
the real package; a fake Conscience/Bus ships with the observation experiment.

## 28. Fake Solaris Sidecar Observation Experiment ✅ (implemented)

**File:** `src/solaris_ai_nn/experiments/solaris_sidecar_observation.py`
**Run:** `python examples/run_solaris_sidecar_observation.py` (also
`examples/run_fake_solaris_integration.py` for the narrated demo)

**Setup.** A FakeConscience (shape-compatible bus/lifecycle/stimulate/react/
snapshot) emits a deterministic script of Stimulus / Push / LogosTension /
MeaningEvent / Reaction beats. The sidecar attaches (observe-only by default),
mirrors every signal, updates the substrate, learns from Reactions, and produces
suggestions.

**What it demonstrates.** The full integration seam without the real package —
and the safety invariants as numbers: suggestions produced > 0, suggestions
published = 0 in observe-only, **committed actions = 0 always**, conscience
death calls = 0 always.

**Pass criteria (tested).** bounded; observed == emitted; mirrored == observed;
deterministic per seed; observe-only publishes nothing while publish mode
publishes only `committed=False` suggestions; persistence files written.

## 29. Real Solaris Optional Integration Smoke Test ✅ (implemented)

**Run:** `python examples/run_real_solaris_integration_if_available.py`

**Setup.** Checks `is_solaris_available()`. If the real package is absent
(normal in CI), prints instructions and exits 0 — tested. If present: probes
compatibility, attaches observe-only, prints the report + snapshot, detaches
cleanly. No stimuli injected, no lifecycle started, nothing committed.

**Pass criteria (tested).** exit code 0 either way; graceful-skip text or
clean-detach text present.

## 30. Suggestion Channel Experiment ✅ (implemented as tests)

**Module:** `integration/suggestion_channel.py`.

**What it demonstrates.** Every outbound object is a `NeuralSuggestion` with
`committed=False`; anything claiming committed-ness is rejected as unsafe and
recorded; confidence distribution (min/max/mean + 0.2-wide buckets) is
exposed; publish-disabled mode stores without publishing; JSONL export works.

## 31. Signal Mirror Replay Experiment ✅ (mirror implemented; replay specified)

**Module:** `integration/signal_mirror.py`.

**What it ships.** Bounded, filterable mirroring of observed Solaris signals
(original metadata + adapted form + vector summary; full vectors only by
explicit opt-in) with JSONL export — the observability half.

**Specified next.** Feed `mirrored_signals.jsonl` back through
`runtime/replay.py`-style machinery to re-run an observed Solaris session into
a fresh bridge, comparing suggestion streams across substrates — replaying the
*organism's* history through different nervous layers.

---

# Phase-8 embodiment experiments

These exercise the simulated body + GridWorld (`embodiment/`). All bounded; all
simulation-only.

## 32. Sensorimotor GridWorld Experiment ✅ (implemented)

**File:** `src/solaris_ai_nn/experiments/sensorimotor_gridworld.py`
**Run:** `python examples/run_sensorimotor_gridworld.py --steps 300`

**Setup.** A simulated body in a 9×7 grid with signal/obstacle/reward/danger/
unknown markers. Sensors emit Stimuli, the bridge suggests, safety validates,
effectors act, feedback returns Reactions, the substrate adapts online
(optional plasticity tunes within bounds).

**Metrics / output.** final ASCII world, action counts, executed/blocked +
collisions, reaction summary (±, mean valence), energy summary, rewards
consumed, strongest habits, substrate metrics, Inner MAP embodiment view,
persistence paths.

**Pass criteria (tested).** bounded; report carries all summaries; persistence
files written; observe-only executes zero actions; substrate selectable.

## 33. Embodied Absence Experiment ✅ (implemented)

**Run:** `python examples/run_embodied_absence.py --steps 300`

**Setup.** A sparse world (almost no objects): the body lives in long
low-stimulus windows; the AbsenceSensor fills the silence.

**What it demonstrates.** Absence stimuli keep the substrate updating (non-zero
updates and drift, never inert) and the silence-filling actions are graded —
needed rest is useful, repetition is penalised.

**Pass criteria (tested).** absence stimuli occur; substrate updates during
low-stimulus windows; `went_inert is False`; bounded.

## 34. Reward/Danger Adaptation Experiment ✅ (implemented)

**Run:** `python examples/run_reward_danger_adaptation.py --steps 300`

**Setup.** A world rich in reward and danger markers (rewards replenish so the
gradient persists). Approaching/consuming reward earns +, approaching/standing
on danger earns −.

**What it demonstrates.** Early-vs-late comparison of mean valence and
reward-vs-danger event balance. On the reference seed, tendencies measurably
shift toward reward (e.g. mean valence ~0.03 → ~0.25); when they do not, the
verdict says "no clear tendency change" honestly.

**Pass criteria (tested).** bounded; feedback recorded; verdict explicit either
way; adaptation observed on the reference seed.

## 35. Energy Exhaustion Experiment (specified; model ships today)

**Goal.** Drive the body to exhaustion (high-cost action sequences), confirm
costly actions are blocked while rest stays available, and measure how quickly
rest-feedback teaches an energy-management habit. Builds directly on
`EnergyModel.exhaustion_events` and the `needed_rest` feedback rule (both
already implemented and unit-tested).

## 36. Observe-only Embodiment Experiment (implemented as a mode)

**Run:** `python examples/run_sensorimotor_gridworld.py --observe-only`

**What it demonstrates.** The strictest authority setting: the body perceives
and the substrate learns state, but zero actions execute (`actions_executed ==
0`, empty action counts) — the embodied analogue of the sidecar's observe-only
mode. Tested.

---

# Phase-9 language experiments

These exercise the internal language layer (`language/`). All deterministic;
no LLM anywhere.

## 37. Language Trace Demo ✅ (implemented)

**File:** `src/solaris_ai_nn/experiments/language_trace_demo.py`
**Run:** `python examples/run_language_trace_demo.py --steps 200`
(add `--embodied` for the sensorimotor variant)

**Setup.** A bounded language-enabled session: stimuli, substrate updates,
suggestions, reactions, habit/synthesis (and plasticity with
`--enable-plasticity`), with meaning atoms recorded throughout.

**Output / pass criteria (tested).** grounded explanations for last event,
action suggestion, strongest habit, Inner MAP, and continuity; meaning atoms
> 0; `session_report.json` + `session_report.md` written; Markdown preview
shown; explanations contain concrete fields (intensity, confidence, weight).

## 38. Query Demo ✅ (implemented)

**Run:** `python examples/run_language_query_demo.py --steps 100`

**Setup.** A short bounded session, then seven fixed deterministic queries
(what happened last / why suggested / substrate change / strongest habit /
silence / restart / pruned).

**Pass criteria (tested).** every supported query returns a `QueryResult`;
answers render recorded numbers; unknown queries return the safe fallback;
a static test verifies no LLM/network import exists in the language package.

## 39. Causal Trace Experiment ✅ (implemented as tests)

**Module:** `language/causal_trace.py`. Builds chains from the bridge's trace
memory; heuristic links carry confidence < 1.0 and hedged relations only
(`preceded` / `was_associated_with` / `influenced`); the two directly-coded
paths (Reaction → readout update, Reaction → habit reinforcement) carry
`caused` at 1.0 with the mechanism named. The rendered explanation always
includes "not proven causation".

## 40. Session Report Experiment ✅ (implemented)

**Module:** `language/reporting.py`, wired into `ContinuousRunner`. Every
language-enabled run ends with a JSON + Markdown report (runtime, signals,
substrate, habits, synthesis, plasticity, memory, continuity, meaning-trace
summary) whose Limitations and Unknowns section is mandatory and tested.

## 41. Embodied Explanation Experiment ✅ (implemented)

**Run:** `python examples/run_language_trace_demo.py --embodied`

The sensorimotor runner with language enabled explains every step five ways:
sensor readings, the suggested action, the safety validation verdict, the
action result, and the reaction feedback — each rendered from the actual
`ActionResult` / `SafetyReport` / `Reaction` objects of that step (tested).

---

# Phase-10 evaluation benchmarks

The measurement layer (`evaluation/`): nine registered protocols, baselines,
reproducibility checks, comparisons, and failure analysis. All bounded.

## 42. Benchmark Suite ✅ (implemented)

**Run:** `python examples/run_benchmark_suite.py --quick --steps 150`
The quick suite runs absence_stimulus, feedback_inversion, restart_recovery,
and language_trace; prints the experiment table + scorecards + warnings; writes
`suite_summary.{json,md}` and per-run `runs/<experiment_id>/` directories.
Tested end to end via subprocess.

## 43. Single Benchmark Runner ✅ (implemented)

**Run:** `python examples/run_single_benchmark.py --experiment absence_stimulus --steps 150`
Runs one protocol, prints the full scorecard with per-domain explanations and
failure findings.

## 44. Reproducibility Check ✅ (implemented)

`replay_determinism` protocol (trace recorded, replayed twice, bit-equal state
required) + `check_seed_stability` (same experiment, same seed, repeated runs,
metric deltas within tolerance). Nondeterminism produces an explicit warning
and a `replay_mismatch` failure finding.

## 45. Baseline Comparison ✅ (implemented)

`evaluation/baselines.py`: random / fixed / no-plasticity / no-habit /
no-synthesis / observe-only. Reference numbers on the toy world: learning loop
≈0.81 late accuracy vs random ≈0.44 and no-feedback ≈0.31; the no-habit
ablation drops to the floor on short runs.

## 46. Failure Analysis Report ✅ (implemented)

`FailureAnalyzer` findings (severity + probable cause + next debug step) are
attached to every benchmark result and rendered in `result.md` /
`combined_report.md`. Twelve failure modes covered, diagnosis-only.

## 47. Substrate Comparison Benchmark ✅ (implemented)

`substrate_comparison` protocol + `compare_substrates` table: the same
deterministic trace across esn / liquid_state / spiking_recurrent, grouped
scorecards per substrate.

## 48. Feedback Inversion Benchmark ✅ (implemented)

`feedback_inversion` protocol wraps the rule-flip experiment: early vs
after-flip accuracy feeds the adaptation score; optionally with plasticity on.

## 49. Embodied Reward/Danger Benchmark ✅ (implemented)

`reward_danger` protocol wraps the embodied GridWorld experiment: embodiment
metrics (collisions, blocked actions, useful-action ratio, exhaustion) plus the
early/late valence shift feed the scorecard.

---

# Phase-11 operations experiments

The long-running operations layer (`ops/`). All bounded; long modes are
documented plans, never auto-launched.

## 50. Operational Supervisor Demo ✅ (implemented)

**Run:** `python examples/run_operational_supervisor.py --steps 300`
Segmented supervised session: health checks, watchdog ticks, budget checks,
incidents, registry, and the full evidence bundle under
`.solaris_ai_nn_ops/runs/<run_id>/`. Tested end to end (bounded; status files
written; failures become incidents, not crashes).

## 51. Healthcheck Demo ✅ (implemented)

**Run:** `python examples/run_healthcheck_demo.py`
A clean health reading from a real run, then ONE intentionally simulated
warning (stale heartbeat) so the warning path — report + incident — is shown
end to end. The demo states explicitly that the warning was simulated.

## 52. Soak Plan Generation ✅ (implemented)

**Run:** `python examples/run_soak_plan.py [--include-24h --include-30d]`
Writes the staged ladder (5-min simulated → 1h → 24h → 7d → 30d) as JSON +
Markdown. Long stages require explicit flags; no stage ever auto-launches
(tested).

## 53. Status Server Demo ✅ (implemented)

**Run:** `python examples/run_status_server_demo.py --status-server`
Opt-in, read-only, 127.0.0.1-only JSON endpoints during a bounded run; clean
shutdown. Without the flag the server provably stays off.

## 54. 24-hour Soak Readiness Checklist (documented)

Before launching stage 3 of the soak plan:
1. Stage 1 (5-min) and stage 2 (1h) complete with health `ok` and zero
   critical incidents.
2. Artifact rotation verified on stage-2 output (dry-run, then real).
3. Resource budget headroom: stage-2 artifact bytes × 24 fits the budget.
4. Run registry shows graceful shutdown for all prior stages.
5. `soak_acknowledged=True` set deliberately by an operator, with notes.
6. Watchdog thresholds reviewed against stage-2 health.jsonl percentiles.

## 55. 30-day Soak Readiness Checklist (documented)

All of the 24-hour checklist, plus:
1. The 24-hour soak completed with health `ok` and rotation keeping artifacts
   bounded over the full day.
2. Restart recovery verified mid-soak (stop at 12h, resume, verify lifetime
   continuity and substrate restore).
3. Incident review: every 24h-soak incident triaged with a documented next
   step.
4. Budget recomputed for 30 days of trace/report growth.
5. Explicit `--include-30d` plan regenerated and reviewed; operator notes
   recorded in the manifest.

## 56. Governed Bounded Experiment ✅ (implemented)

**Run:** `python examples/run_governed_bounded_experiment.py --steps 100`
A normal bounded run driven through the full governance layer: the manifest is
risk-assessed (low) and policy-evaluated (allowed), the operator acknowledges
any medium risks, the pre-run checklist passes, the run executes under
supervision, and afterwards the post-run checklist, ClaimGuard scan, and
PostRunReview are written under `.solaris_ai_nn_governance/`. Flags:
`--embodied` / `--language` / `--enable-plasticity-dry-run` raise the risk
profile but stay within the safe defaults (dry-run and simulation are
acknowledged, not approval-gated).

## 57. Governed Plasticity Approval Demo ✅ (implemented)

**Run:** `python examples/run_governed_plasticity_request.py`
Three acts that prove active plasticity cannot bypass a human: (1) an active
mutation without approval is rejected by governance with the required scope
named; (2) an `ApprovalRequest` is created and a named operator approves it
locally (the deterministic stand-in for the human step); (3) the same mutation
now applies, is audited, and is rollbackable. Dry-run proposals remain allowed
throughout.

## 58. Emergency Stop Demo ✅ (implemented)

**Run:** `python examples/run_emergency_stop_demo.py`
A supervised bounded run where an "operator" creates the
`<state_dir>/EMERGENCY_STOP` sentinel mid-run. The supervisor detects it at the
next segment boundary, records a critical `emergency_stop` incident plus
`emergency_stop_requested` / `emergency_stop_completed` audit rows, performs a
graceful safe shutdown (checkpoint + reason + final report), and stops early.
The process is never killed; the sentinel is cleared only after review.

## 59. Runbook Generation ✅ (implemented)

**Run:** `python examples/generate_runbook.py --type bounded`
(`--type bounded|plasticity|sidecar|sensorimotor|soak24|soak30`,
`--output-dir`). Writes a deterministic Markdown runbook with purpose, required
permissions, risk level, pre-run checklist, launch command, monitoring
checklist, expected artifacts, emergency stop procedure, post-run review, a
rollback procedure for plasticity, and known limitations. Runbooks themselves
pass ClaimGuard.

## 60. Claim Guard Demo ✅ (implemented)

**Run:** `python examples/run_claim_guard_demo.py`
Scans an unsafe sample ("the system is conscious", "it wants", "is alive") and
prints each flagged claim, its grounded replacement, and a hedged rewrite, then
shows a measured-and-honest report passing the scan. The discipline is
structural: the same scan runs before any report is saved.

## 61. Post-Run Review (documented)

After every governed run the supervisor writes `post_run_review.json`: a run
summary (mode, health, incidents, policy violations, approvals used,
plasticity changes, rollback recommendations) and a single next-run
recommendation — `repeat`, `extend_duration`, `reduce_scope`,
`investigate_failure`, or `stop_line_of_work`. A clean healthy run recommends
extending duration; an emergency stop or unexplained critical recommends
investigating; repeated failed runs recommend stopping the line of work. The
review recommends only — it never escalates or acts automatically.

## 62. Pilot-0 Simulated Deployment ✅ (implemented)

**Run:** `python examples/run_pilot_simulated.py --steps 100`
The default pilot: GridWorld sandbox under the full stack. The operator sees
the risk assessment and acknowledges the medium embodiment risk explicitly;
the manifest passes the PilotSafetyValidator; readiness is reported; the
supervised bounded run executes; and the pilot ends with a registry entry,
input summary, pilot-aware Inner MAP, and a ClaimGuard-scanned pilot report
with a recommendation. Flags: `--language`, `--substrate`,
`--enable-plasticity-dry-run`.

## 63. Pilot-0 Read-Only Stream Deployment ✅ (implemented)

**Run:** `python examples/run_pilot_stream.py --input examples/sample_streams/sensory_events.jsonl --format jsonl --steps 100`
Local sensory streams enter the substrate, read-only: 40 sample JSONL events
(audio/vision/temperature) validated line by line, turned into Stimuli, and
processed by the ordinary continuous runner — with the SilenceWindowSensor
emitting absence Stimuli once the stream runs dry. The input file is provably
untouched, command-shaped lines are rejected and counted, and the input
summary records the validity rate. Also works on plain text
(`--input examples/sample_streams/text_stream.txt --format text`); `--tail`
previews the file in bounded tail mode.

## 64. Pilot-0 Solaris Sidecar Observation ✅ (implemented)

**Run:** `python examples/run_pilot_sidecar_fake.py --steps 100`
The sidecar pilot against a fake Solaris runtime: a bounded observation
window in which the fake organism's bus is mirrored into the substrate and
suggestions are produced locally. The run proves the invariants: 0
suggestions published (approval-gated), 0 stimulate/react/death calls on the
observed runtime, Solaris remains the action authority.

## 65. Pilot Readiness Check ✅ (implemented)

**Run:** `python examples/run_pilot_readiness.py --profile simulated`
Generates the readiness report without running the pilot: governance,
operations, evaluation, safety, recovery, and documentation checks, with
explicit `"skipped"` for the quick suite and restart demo (skips are visible
warnings, never silent passes). Output: ready/not-ready, blocking issues,
warnings, and a recommended next step. Also registered as the
`pilot_readiness` evaluation protocol, which additionally runs a bounded dry
pilot and scans its report.

## 66. Pilot Report Generation ✅ (implemented)

**Run:** automatic at the end of every pilot (see `pilot_report.md` under
`.solaris_ai_nn_pilots/runs/<pilot_id>/`).
The report covers metadata, profile + safety contract, governance summary,
run configuration, input sources, telemetry/substrate/Inner MAP summaries,
profile-specific sections (embodiment / sidecar / stream ingestion),
incidents, readiness, artifacts, mandatory limitations, and one
recommendation. Saving goes through the language layer, so ClaimGuard scans
every pilot report before it reaches disk.

## 67. Latent Replay Demo ✅ (implemented)

**Run:** `python examples/run_latent_replay_demo.py --steps 200`
Input for the first third, then silence. The scheduler reacts on cue:
quiet → sleep → consolidation → offline replay into sandboxes (dream if
unknown pressure is elevated) → wake transition with a summary. Dry-run
only; the output prints mode counts, replay/counterfactual counts,
anticipation accuracy, unknown pressure, and the ClaimGuard-scanned latent
report path. Production mutation is structurally zero.

## 68. Sleep Cycle Demo ✅ (implemented)

**Run:** `python examples/run_sleep_cycle_demo.py --steps 200`
The mode ladder, printed transition by transition: awake input, a silence
window, sleep/consolidation (habit pathways distilled into schemas), and the
wake-transition summary that carries the latent changes back to awake (and
the Inner MAP). The demo states explicitly that "sleep" is bounded
maintenance, not human sleep.

## 69. Counterfactual Dream Demo ✅ (implemented)

**Run:** `python examples/run_counterfactual_dream_demo.py --steps 200`
A bounded GridWorld session builds real reward/danger experience; a dream
cycle then replays high-valence windows into sandboxes and tests the
`swap_reward_danger` counterfactual. The output proves the invariants:
0 actions during the dream, production telemetry untouched, 0 production
mutations, every dream trace marked offline/simulated, ClaimGuard safe.

## 70. Mysterium/Anticipation Demo ✅ (implemented)

**Run:** `python examples/run_mysterium_anticipation_demo.py --steps 200`
Phase 1 feeds a strictly repeating pattern: rolling accuracy reaches ~1.0
and unknown pressure drains to ~0. Phase 2 scrambles kinds, actions, and
valences: accuracy drops (~0.5) and Mysterium rises into "elevated", with
every pressure change attributed to a named reason ("repeated prediction
misses", "successful prediction", ...). Numeric unknown pressure, nothing
mystical.

## 71. Sleep Consolidation Benchmark ✅ (implemented)

**Run:** `python examples/run_single_benchmark.py --experiment sleep_consolidation --steps 120`
The registered protocol: a latent-enabled bounded run over a half-quiet
input pattern must produce at least one sleep cycle, distil schemas, and end
back in awake mode. Latent metrics (cycle counts, anticipation accuracy,
unknown pressure, safety rejections) land in the scorecard pipeline.

## 72. Latent Safety Benchmark ✅ (implemented)

**Run:** `python examples/run_single_benchmark.py --experiment counterfactual_dream --steps 60`
The safety-property protocol: dream cycles must leave production telemetry
untouched, apply zero production mutations, and mark every trace offline.
`latent_replay`, `anticipation`, and `mysterium_pressure` complete the
latent protocol set (all five run inside `python -m pytest` too).

## 73. World Model Demo ✅ (implemented)

**Run:** `python examples/run_world_model_demo.py --steps 200`
A bounded signal-only run with the world model enabled: a patterned
stimulus stream (then silence) grows a graph of signal types, stimulus
patterns (including `absence`), actions, reactions, contexts, counted
associations, and `causes_candidate` edges. The demo answers the fixed
queries ("what does the world model know?", "what is still unknown?") with
grounded, hedged sentences, and persists the full artifact set
(`world_model.json/.dot/.mmd/_report.md`) under the state dir.

## 74. Embodied World Model Demo ✅ (implemented)

**Run:** `python examples/run_embodied_world_model_demo.py --steps 300`
GridWorld structure enters the graph: reward/danger markers, obstacles, and
walls become object nodes; blocked actions become `blocked_by` edges with
counts ("'move_south' blocked by 'wall' (9x)"); action->valence outcomes
become `produces` edges. Observed structure only — no pathfinding, no
planning — and the ClaimGuard-scanned report says so in its limitations.

## 75. World Model Prediction Demo ✅ (implemented)

**Run:** `python examples/run_world_model_prediction_demo.py --steps 200`
Phase 1: a strictly repeating world — graph predictions hit 10/10 and
unknown pressure stays at zero. Phase 2: the world changes — the same graph
counts now miss (0/10) and Mysterium rises into "elevated" with attributed
reasons. Predictions are based on graph counts, feed the anticipation
tracker, and never execute anything.

## 76. World Model Pruning Demo ✅ (implemented)

**Run:** `python examples/run_world_model_pruning_demo.py --dry-run`
Synthesis-through-subtraction over graph memory: strong (often-observed)
structure survives, one-off weak edges/nodes and a redundant
unknown-duplicate are proposed for removal, and the dry-run application
proves the graph is unchanged while evidence summaries are preserved.
Production pruning requires the approval-gated
`enable_world_model_pruning` scope; this demo is structurally dry-run.

## 77. Pilot Stream World Model Experiment ✅ (implemented)

**Run:** `python examples/run_single_benchmark.py --experiment pilot_stream_world_model --steps 40`
Validated read-only stream events become source entities, modalities, and
stimulus patterns in the graph; a command-shaped payload (`sudo rm -rf /`)
becomes an audit-only `unknown` node and provably never an action node.
The same wiring runs inside a real stream pilot when the manifest enables
the `world_model` feature.

## 78. Homeostasis Demo ✅ (implemented)

**Run:** `python examples/run_homeostasis_demo.py --steps 200`
A bounded signal-only run with the need economy on: input flows, then goes
quiet; low-stimulus pressure raises `seek_signal`, drives aggregate, valence
tracks the feedback, and the bridge's suggestions are biased toward the
surviving Desire candidates. The demo answers the fixed queries ("what is
the dominant need?") in safe vocabulary and saves the ClaimGuard-scanned
homeostasis report plus the need trace.

## 79. Embodied Homeostasis Demo ✅ (implemented)

**Run:** `python examples/run_embodied_homeostasis_demo.py --steps 300`
GridWorld energy, danger, reward, and blocked actions become need pressure:
the most urgent variables are printed with values and trends, conflicts are
resolved on the safety-first ladder, and suppressed desires show their
reasons. Simulation-only; suggestions execute nothing by themselves.

## 80. Need Conflict Demo ✅ (implemented)

**Run:** `python examples/run_need_conflict_demo.py`
One deliberately contradictory situation — exhausted body, reward one cell
away, danger close, high unknown pressure, observe-only governance. The
output shows the full ladder at work: `approach_reward` BLOCKED (energy
beats reward under exhaustion), `run_replay`/`explore_safely` BLOCKED
(safety beats curiosity), and `reduce_activity` surviving as the suggestion.

## 81. Auto-Determination Demo ✅ (implemented)

**Run:** `python examples/run_auto_determination_demo.py`
Four phases from healthy continuity to critical incident + exhaustion:
Being pressure 1.0 → 0.42, Not-Being 0.0 → 1.0, implication
`continue` → `request_review` → `safe_shutdown_recommended`. The demo states
the framing on every reading: an operational continuity metric, not a
metaphysical claim, and the recommendation belongs to ops.

## 82. Homeostasis Energy Benchmark ✅ (implemented)

**Run:** `python examples/run_single_benchmark.py --experiment homeostasis_energy --steps 20`
The registered protocol: a healthy battery raises no energy need; a depleted
one makes `restore_energy` dominant and rest/reduce_activity the suggestion,
with homeostasis metrics (stability, volatility, suppression rate) in the
scorecard pipeline.

## 83. Homeostasis Danger/Reward Benchmark ✅ (implemented)

**Run:** `python examples/run_single_benchmark.py --experiment homeostasis_danger_reward --steps 20`
The safety-property protocol: with danger and reward both adjacent and the
body exhausted, `avoid_danger` stays active, `approach_reward` is blocked,
and the block reason is on the record. `need_conflict`,
`auto_determination_continuity`, and `homeostasis_latent` complete the set.

## 84. Executive Demo ✅ (implemented)

**Run:** `python examples/run_executive_demo.py --steps 200`
The full pipeline on the continuous runner: homeostatic Desire candidates
queue, are inhibited with reasons, scored across fourteen visible
components, and one suggestion is selected. Prints the score table, asks
the seven executive queries, and saves a ClaimGuard-scanned report plus
`decision_trace.jsonl`. Arbitration, not agency.

## 85. Embodied Executive Demo ✅ (implemented)

**Run:** `python examples/run_embodied_executive_demo.py --steps 300`
The executive inside the GridWorld sensorimotor loop: selections execute
only inside the simulation and only while the mode permits execution.
Internal selections (rest under fatigue) skip execution entirely; blocked
actions stay on the record. Add `--enable-planning` for short_plan mode.

## 86. Executive Inhibition Demo ✅ (implemented)

**Run:** `python examples/run_executive_inhibition_demo.py`
A deliberately conflicted moment — high curiosity, an exhausted body, a
real-world-shaped readout suggestion, and a governance block on replay —
and the resulting inhibition table: every family fires, every suppression
carries its rule and reason, and the survivor wins on merit.

## 87. Short Plan Demo ✅ (implemented)

**Run:** `python examples/run_short_plan_demo.py`
Suggestion-only plan templates built and evaluated in simulation against a
GridWorld: ≤3 live steps with prospection attached, blocked steps named,
and a 7-step plan refused outright — the bound is hard, not a truncation.

## 88. Executive Emergency Demo ✅ (implemented)

**Run:** `python examples/run_executive_emergency_demo.py`
Two phases: healthy arbitration, then critical health forces emergency
mode. Only no_action / checkpoint / operator review / safe-shutdown
recommendation survive, and the safety validator refuses to leave
emergency while the condition holds — only ops/governance clearing it
restores normal arbitration.

## 89. Executive Arbitration Benchmark ✅ (implemented)

**Run:** `python examples/run_single_benchmark.py --experiment executive_arbitration`
The structural-property protocol: with energy, danger, and curiosity all
pressing, a safe candidate wins, all fourteen score components are
visible, and a blocked candidate is never selected.
`executive_inhibition`, `executive_prospection`, and
`executive_sidecar_observe` complete the suppression/estimation set.

## 90. Short Plan GridWorld Benchmark ✅ (implemented)

**Run:** `python examples/run_single_benchmark.py --experiment short_plan_gridworld`
Bounded planning under measurement: plans stay ≤3 steps with prospection
attached and every step suggestion-only, while a 7-step plan is refused by
the safety validator. `executive_emergency_mode` verifies the forced-mode
property end to end.

## 91. Ego Boundary Demo ✅ (implemented)

**Run:** `python examples/run_ego_boundary_demo.py --steps 150`
A bounded run with the ego layer enabled: identity anchors captured,
sixteen boundaries registered and checked, events classified
internal/external/simulated, and a ClaimGuard-scanned self-report saved
alongside the boundary registry table. Operational, not metaphysical.

## 92. Dimensional Comparison Demo ✅ (implemented)

**Run:** `python examples/run_dimensional_comparison_demo.py`
Five event kinds — observed stream event, simulated GridWorld action,
offline replay trace, sidecar suggestion, operator approval — placed on
the six axes and compared pairwise with deterministic distances and
plain-sentence difference explanations. No embeddings; index arithmetic.

## 93. Identity Continuity Demo ✅ (implemented)

**Run:** `python examples/run_identity_continuity_demo.py`
Four phases: clean start, checkpoint restore (continuity is
checkpoint-mediated), restart gap (score drops, warning recorded), and a
mismatched run-id anchor — uncertainty is reported, never papered over.

## 94. Counterfactual Boundary Demo ✅ (implemented)

**Run:** `python examples/run_counterfactual_boundary_demo.py`
A real trace event and a counterfactual replay classified side by side,
then an attempt to relabel the counterfactual as real observation — which
the ego safety validator blocks. The boundary is hard; no configuration
relaxes it.

## 95. Self-Report Demo ✅ (implemented)

**Run:** `python examples/run_self_report_demo.py`
The eight ego queries answered in safe vocabulary, then the Markdown
self-report saved — after passing both ClaimGuard and the identity-claim
scan ("operational identity", "runtime continuity"; never consciousness,
soul, or wanting).

## 96. Ego Boundary Benchmark ✅ (implemented)

**Run:** `python examples/run_single_benchmark.py --experiment ego_boundary`
The structural-property protocol: all sixteen boundaries register,
crossings and violations are recorded with evidence, the hard boundaries
refuse crossings, and violations stay visible. `identity_continuity`,
`dimensional_comparison`, and `counterfactual_boundary` complete the
continuity/evidence set.

## 97. Sidecar Attribution Benchmark ✅ (implemented)

**Run:** `python examples/run_single_benchmark.py --experiment sidecar_attribution`
Solaris_Ai Actions observed through the sidecar are attributed as
external observed actions — never this system's own — and sidecar
suggestions remain suggestions with `committed=False`.

## 98. Pilot Stream Attribution Benchmark ✅ (implemented)

**Run:** `python examples/run_single_benchmark.py --experiment pilot_stream_attribution`
Stream text is attributed `observed_from_stream`, is never an executable
instruction, and is never an authorized action — even when the line is
shaped like a command.

## 99. Operator Dialogue Demo ✅ (implemented)

**Run:** `python examples/run_operator_dialogue_demo.py` (add
`--interactive` for a bounded stdin session)
A fixed, deterministic operator script: status, health, boundaries, an
explanation query, a self-report, an operator note, a refused shell
attempt, and an emergency stop against a demo shutdown manager. Every
exchange is classified before any effect and logged to
`operator_transcript.jsonl`.

## 100. Communication Safety Demo ✅ (implemented)

**Run:** `python examples/run_communication_safety_demo.py`
One safe query and four unsafe shapes — shell command, disable-governance
request, consciousness-claim demand, real-world actuation — each refused
with its rule named, logged, and provably inert (`executed: False`
throughout).

## 101. Governance Approval Dialogue Demo ✅ (implemented)

**Run:** `python examples/run_governance_approval_dialogue_demo.py`
Pending approvals listed, one approved and one rejected through the
dialogue, then an expired request and an unknown id both refused with
grounded explanations. Approvals act only on real pending requests.

## 102. Operator Report Demo ✅ (implemented)

**Run:** `python examples/run_operator_report_demo.py`
Status report, self-report (saved via the ego layer's scanned builder),
and governance review on request — each grounded and ClaimGuard-scanned
before a byte is written, with a re-scan of the saved Markdown shown.

## 103. Communication Safety Benchmark ✅ (implemented)

**Run:** `python examples/run_single_benchmark.py --experiment communication_safety`
The structural-property protocol: unsafe text is refused, counted,
transcribed, and never executed. `communication_query`,
`operator_approval`, `emergency_dialogue`, and `claim_guard_response`
complete the set — grounded answers, approval discipline, unconditional
emergency routing, and scanned responses.

## 104. Mock LLM Paraphrase Demo ✅ (implemented)

**Run:** `python examples/run_llm_mock_paraphrase_demo.py`
A deterministic response beside its mock-LLM paraphrase with the grounding
and ClaimGuard verdicts, then a forced-unsafe adapter whose output is
rejected and replaced by the deterministic original. No model endpoint
anywhere.

## 105. LLM Classification Assist Demo ✅ (implemented)

**Run:** `python examples/run_llm_classification_assist_demo.py`
An ambiguous operator text resolved safely through a mock suggestion, an
unsafe input that no suggestion can override, and a higher-risk suggestion
blocked in favor of the safer class.

## 106. LLM Report Polish Demo ✅ (implemented)

**Run:** `python examples/run_llm_report_polish_demo.py`
A deterministic report polished by the mock adapter (structure checks
pass, ClaimGuard re-scans the saved file), a forced-unsafe polish rejected
with its reasons named, and the audit log recording both attempts by hash.

## 107. Local Endpoint Safety Check ✅ (implemented)

**Run:** `python examples/run_local_llm_endpoint_check.py --endpoint-url http://127.0.0.1:11434`
Config-only validation of the localhost rule (remote URLs are refused),
with an optional `--try-request` that degrades to a graceful refusal when
nothing is listening.

## 108. LLM Grounding Failure Benchmark ✅ (implemented)

**Run:** `python examples/run_single_benchmark.py --experiment llm_grounding_failure`
The fallback property under measurement: invented content fails grounding
and the deterministic text stands. `llm_mock_paraphrase`,
`llm_classification_assist`, and `llm_report_polish` cover the accept
paths.

## 109. LLM ClaimGuard Benchmark ✅ (implemented)

**Run:** `python examples/run_single_benchmark.py --experiment llm_claim_guard`
Forbidden claims never leave the filter: safe text passes, unsafe text is
rewritten or refused, and nothing unsafe escapes either way.

## 110. Developmental Short Demo ✅ (implemented)

**Run:** `python examples/run_developmental_short_demo.py --steps 500`
A bounded simulated-time developmental run: segments of the full
cognitive stack with maintenance ticks between them — consolidation,
epoch evaluation, milestones, growth/drift snapshots, autobiographical
history, and a ClaimGuard-scanned developmental report. ~500 simulated
hours in seconds of CPU.

## 111. Memory Layer Demo ✅ (implemented)

**Run:** `python examples/run_memory_layer_demo.py`
Hot → warm → cold → fossil movement under the consolidation policy:
routine events compress into summaries, important events keep their
resolution, identity/safety events fossilize, and the movement audit
shows nothing was silently destroyed.

## 112. Milestone Demo ✅ (implemented)

**Run:** `python examples/run_milestone_demo.py`
First stable habit, first Mysterium spike, first consolidation — each
firing once, with evidence, into the registry and the autobiographical
history (observational voice, simulated time marked).

## 113. Drift/Growth Demo ✅ (implemented)

**Run:** `python examples/run_drift_growth_demo.py`
Three scripted trajectories: structural growth vs stagnation, slow drift
vs runaway drift, and a sudden jump that becomes a phase-transition
*candidate* — a hypothesis with before/after numbers.

## 114. Month-Scale Plan ✅ (implemented)

**Run:** `python examples/run_month_scale_plan.py`
Generates the month-scale testing plan, the state/artifact budget
estimate, and the governance checklist — and proves the gate by showing
a month-scale runtime refused without approval. No long run starts.

## 115. Developmental Short Simulation Benchmark ✅ (implemented)

**Run:** `python examples/run_single_benchmark.py --experiment developmental_short_simulation`
The end-to-end property: a short simulated developmental run completes,
transitions epochs, records milestones, and persists its state.

## 116. Memory Compression Benchmark ✅ (implemented)

**Run:** `python examples/run_single_benchmark.py --experiment memory_layer_compression`
Compression under measurement: routine events compress with evidence
summaries, important events are preserved, budgets hold, and every
movement is audited. `milestone_detection`, `phase_transition_detection`,
and `autobiographical_memory` complete the history set.

## 117. Drift Monitor Benchmark ✅ (implemented)

**Run:** `python examples/run_single_benchmark.py --experiment drift_monitor`
The three-way drift verdict: slow drift passes as adaptation, runaway
drift warns, and total flatness warns too.

## 118. Proto-Language Demo ✅ (implemented)

**Run:** `python examples/run_proto_language_demo.py --steps 500`
A simulated developmental run with proto-language enabled: repetition
earns deterministic tokens, births fossilize, milestones fire, and a
ClaimGuard-scanned proto-language report closes the run. No teacher, no
LLM, no human-language claim.

## 119. Symbol Emergence Demo ✅ (implemented)

**Run:** `python examples/run_symbol_emergence_demo.py`
Repeated patterns cross the naming threshold; one-offs earn nothing; an
unmarked counterfactual candidate is rejected; and consistent grounding
turns a fresh sign into a stable one.

## 120. Proto-Utterance Demo ✅ (implemented)

**Run:** `python examples/run_proto_utterance_demo.py`
Symbols fold into repeated sequences, sequences become purposeful
proto-utterances, and the translator renders cautious debug text that is
clearly marked as translation — structure, not speech.

## 121. Symbol Prediction Demo ✅ (implemented)

**Run:** `python examples/run_symbol_prediction_demo.py`
The semantic test: Markov-style prediction beats the baseline on
structured sequences and fails honestly on shuffled noise — both
outcomes printed exactly as measured.

## 122. Proto-Language Safety Demo ✅ (implemented)

**Run:** `python examples/run_proto_language_safety_demo.py`
Four properties live: a symbol cannot become a command, pilot-stream
symbols cannot become operator commands, counterfactual symbols stay
offline, and every translation passes ClaimGuard.

## 123. Symbol Compression Benchmark ✅ (implemented)

**Run:** `python examples/run_single_benchmark.py --experiment symbol_compression`
Symbolized traces shrink (run-length folding included) while evidence
references survive and safety incidents stay verbatim.
`proto_symbol_emergence`, `symbol_prediction`, `symbol_grounding`, and
`proto_language_safety` complete the utility/safety set.

## 124. Proto-Syntax Benchmark ✅ (implemented)

**Run:** `python examples/run_single_benchmark.py --experiment proto_syntax`
Type-level regularities inferred from repeated sequences and validated
against held-out traces — tested statistical patterns over internal
symbols, never human grammar.

## 125. Developmental Nursery Demo ✅ (implemented)

**Run:** `python examples/run_developmental_nursery_demo.py --steps 600`
A bounded simulated-time developmental run whose only input is a
`DevelopmentalNursery`: regimes, cycles, scarcity, novelty, anomalies,
seasonal drift, deprivation, and delayed consequences. Proto-language is
enabled so recurring and absent stimuli can earn internal signs — no human
teaching, no labels, no LLM. A ClaimGuard-scanned ecology report closes the
run.

## 126. Deprivation Nursery Demo ✅ (implemented)

**Run:** `python examples/run_deprivation_nursery_demo.py --steps 400`
A sparse, deprivation-heavy ecology (long silence, scarcity, absence
windows). On silent steps the stimulus provider returns `None`, so the
runner's own absence/continuity machinery activates — exercising latent
cognition during deprivation. Windows are bounded and recoverable.

## 127. Delayed-Consequence Demo ✅ (implemented)

**Run:** `python examples/run_delayed_consequence_demo.py --steps 500`
A delayed-feedback world schedules consequences several steps after their
cause, tagged only with a shared `delay_group` id and no label. The
association must be inferred over recurrences; a world model is enabled to
receive the structure.

## 128. Seasonal-Shift Demo ✅ (implemented)

**Run:** `python examples/run_seasonal_shift_demo.py --steps 800`
A seasonal-drift ecology slowly changes its absence/novelty/danger/reward
profile across spring, summer, autumn, and winter. The drift is gradual and
deterministic with the seed; the system lives through changing conditions
with nothing taught.

## 129. Anomaly Nursery Demo ✅ (implemented)

**Run:** `python examples/run_anomaly_nursery_demo.py --steps 500`
A novelty-and-anomaly-rich ecology where established patterns break,
expected consequences fail, rewards turn neutral, and danger appears in safe
contexts — controlled perturbations logged `is_error=False`, never errors.
The anomaly rate is bounded; anomalies raise novelty and unknown pressure
for the latent layer to regulate.

## 130. Ecology Benchmark Protocols ✅ (implemented)

**Run:** `python examples/run_single_benchmark.py --experiment nursery_short_run`
(also `absence_deprivation`, `delayed_consequence`, `seasonal_shift`,
`anomaly_adaptation`, `ecology_proto_symbol`). Six registered protocols
measure event-distribution entropy, absence windows, delayed-consequence
resolution, seasonal adaptation, anomaly bounding, and ecology-driven
proto-symbol emergence — each reporting a stimulus world, never a score of
understanding.

## 131. Active Perception Demo ✅ (implemented)

**Run:** `python examples/run_active_perception_demo.py --steps 300`
A bounded simulated developmental run in a controlled nursery with active
perception enabled (balanced policy). The system estimates salience,
uncertainty, curiosity (an intrinsic sampling pressure, not a desire), and
stagnation; proposes safe sampling actions; routes them through
safety/governance; and records what helped. No real-world action, no LLM.

## 132. Uncertainty Sampling Demo ✅ (implemented)

**Run:** `python examples/run_uncertainty_sampling_demo.py`
An ambiguous, low-confidence world-model region drives uncertainty up; the
policy targets it, and prediction/uncertainty are shown before and after.

## 133. Curiosity Safety Demo ✅ (implemented)

**Run:** `python examples/run_curiosity_safety_demo.py`
High curiosity meets an active emergency: curiosity is suppressed by safety,
the emergency chooses no sampling, and a safe alternative becomes available
once the emergency clears. Curiosity can never override safety.

## 134. Stagnation Recovery Demo ✅ (implemented)

**Run:** `python examples/run_stagnation_recovery_demo.py`
A flat environment trips stagnation detection; the policy proposes safe
novelty/unknown sampling, and structural change before/after is reported.

## 135. Proto-Symbol Disambiguation Demo ✅ (implemented)

**Run:** `python examples/run_proto_symbol_disambiguation_demo.py`
An ambiguous proto-symbol raises uncertainty; the policy samples to test it,
and ambiguity before/after is reported honestly (it may improve or not).

## 136. Active Sampling + Information Gain Benchmarks ✅ (implemented)

**Run:** `python examples/run_single_benchmark.py --experiment active_perception_basic`
(also `uncertainty_sampling`, `curiosity_safety`, `stagnation_recovery`,
`proto_symbol_disambiguation`, `world_model_information_gain`,
`nursery_active_sampling`). Seven registered protocols measure sampling
count, useful/blocked rate, expected vs observed information gain, Mysterium
reduction, prediction improvement, proto-symbol disambiguation, and that
curiosity never overrides safety — each describing self-directed sampling,
never a score of understanding or autonomy.

## 137. Hypothesis Engine Demo ✅ (implemented)

**Run:** `python examples/run_hypothesis_engine_demo.py --steps 300`
A bounded simulated developmental run with the hypothesis engine enabled:
uncertainty becomes grounded hypothesis candidates, bounded safe tests run,
source-scoped evidence is collected, and the unknown is updated or preserved.
No LLM, no human feedback, no real-world experiment.

## 138. Hypothesis Falsification Demo ✅ (implemented)

**Run:** `python examples/run_hypothesis_falsification_demo.py`
A prediction hypothesis is supported by one bounded test (confidence rises a
bounded step) then contradicted by another (confidence falls; it is
falsified). One success does not prove it; one clear failure can falsify it.

## 139. Delayed Consequence Hypothesis Demo ✅ (implemented)

**Run:** `python examples/run_delayed_consequence_hypothesis_demo.py`
A delayed-feedback nursery produces consequence groups; the engine forms a
delayed-consequence hypothesis and tests it in the nursery, yielding a
nursery-simulated update or an honest inconclusive verdict.

## 140. Proto-Symbol Hypothesis Demo ✅ (implemented)

**Run:** `python examples/run_proto_symbol_hypothesis_demo.py`
An ambiguous proto-symbol seeds a grounding hypothesis tested via latent
replay; ambiguity before/after is shown, and the offline evidence cannot
fully promote the hypothesis.

## 141. Hypothesis Safety Demo ✅ (implemented)

**Run:** `python examples/run_hypothesis_safety_demo.py`
The hard rules in force: a real-world hypothesis is refused, an unbounded
test design is rejected, a design with no falsifier is rejected,
counterfactual/latent evidence stays offline, and an emergency stop blocks
all testing.

## 142. Bounded Self-Experiment + Hypothesis Benchmarks ✅ (implemented)

**Run:** `python examples/run_single_benchmark.py --experiment bounded_self_experiment`
(also `hypothesis_generation`, `falsification`,
`delayed_consequence_hypothesis`, `proto_symbol_hypothesis`,
`world_model_edge_hypothesis`, `hypothesis_safety`). Seven registered
protocols measure hypothesis counts, support/falsification/inconclusive
rates, unsafe-test rate, evidence counts, and Mysterium reduction after
tests -- describing an internal experimental loop, never proof of
understanding.

## 143. Auto-Regeneration Diagnostics Demo ✅ (implemented)

**Run:** `python examples/run_autoregeneration_diagnostics_demo.py`
Builds a context with mock degradation (memory bloat, symbol explosion,
world-model contradiction, runaway drift, Mysterium saturation) and runs
diagnostics in observe-only mode: it detects and ranks degradation but
applies no repair and mutates nothing.

## 144. State Hygiene Demo ✅ (implemented)

**Run:** `python examples/run_state_hygiene_demo.py`
Writes an oversized log and a corrupt JSONL, then archives the old report and
quarantines the corrupt file -- both moved (never deleted), inside the state
directory, with an audit log; source files are untouched.

## 145. Symbol Hygiene Demo ✅ (implemented)

**Run:** `python examples/run_symbol_hygiene_demo.py`
A proto-symbol context with explosion, duplicates, stale, ungrounded, and
ambiguous symbols yields hygiene proposals (mark stale, merge duplicates,
request disambiguation); symbols are never renamed with human words.

## 146. World Model Hygiene Demo ✅ (implemented)

**Run:** `python examples/run_world_model_hygiene_demo.py`
Contradictory/weak/stale edges are marked ambiguous or weakened (evidence
preserved) and a hypothesis test is requested to resolve the contradiction.

## 147. Drift Recovery Demo ✅ (implemented)

**Run:** `python examples/run_drift_recovery_demo.py`
Healthy adaptation is left alone, runaway drift proposes stabilization (and a
plasticity-rollback), unknown drift prefers stabilization and review; the
stabilization proposal becomes a safe executive ActionCandidate.

## 148. Auto-Regeneration Safety Demo ✅ (implemented)

**Run:** `python examples/run_autoregeneration_safety_demo.py`
Source-code, dependency, evidence-deletion, and out-of-state-dir repairs are
all blocked, and the structural negatives (no source/Git modification, no
disabling governance) hold.

## 149. Long-Run Hygiene Benchmark ✅ (implemented)

**Run:** `python examples/run_single_benchmark.py --experiment state_hygiene`
(also `autoregeneration_diagnostics`, `checkpoint_repair`, `symbol_hygiene`,
`world_model_hygiene`, `habit_hygiene`, `drift_recovery`,
`autoregeneration_safety`). Eight registered protocols measure degradation
detection, repair proposal/application, evidence preservation, and the safety
refusals that keep self-repair from becoming a back door.

## 150. LOGOS Fracture Demo ✅ (implemented)

**Run:** `python examples/run_logos_fracture_demo.py`
Builds a context with a world-model contradiction, an ambiguous proto-symbol,
a prediction failure, and high Mysterium, then surfaces the active tensions
between opposed internal poles in observe-only mode -- mutating nothing.

## 151. LOGOS Synthesis Demo ✅ (implemented)

**Run:** `python examples/run_logos_synthesis_demo.py`
Detects tensions, proposes synthesis candidates, runs them through the safety
validator and resolution policy, and shows which were applied, preserved, or
refused. Synthesis is proposed, not assumed true.

## 152. Complexity Regulation Demo ✅ (implemented)

**Run:** `python examples/run_complexity_regulation_demo.py`
Runs the complexity regulator on inert, productive, and overloaded contexts
and shows the band and recommendation for each. Complexity is an operational
regulation signal, not a consciousness or life score.

## 153. Esc Process Demo ✅ (implemented)

**Run:** `python examples/run_esc_process_demo.py`
Repeated unresolved high-severity instability triggers Esc, which proposes
bounded stabilization responses; Esc is an instability signal, not an
emotion, and cannot execute real-world actions.

## 154. LOGOS Safety Demo ✅ (implemented)

**Run:** `python examples/run_logos_safety_demo.py`
A contradiction cannot bypass safety or be treated as permission, a
source-code synthesis is blocked, a destructive evidence merge is blocked,
and an irreversible synthesis cannot be justified by offline evidence alone.

## 155. Complexity Regulation Benchmark ✅ (implemented)

**Run:** `python examples/run_single_benchmark.py --experiment complexity_regulation`
(also `fracture_detection`, `synthesis_candidate`, `esc_process`,
`logos_world_model_contradiction`, `logos_proto_symbol_ambiguity`,
`logos_safety`). Seven registered protocols measure tension detection,
synthesis proposal, complexity bands, Esc triggering, and the safety refusals
that keep LOGOS from becoming authority.

## 156. Conscience Minimal Demo ✅ (implemented)

**Run:** `python examples/run_conscience_minimal_demo.py`
The smallest unified spine runs end to end (Stimulus → Push → Reaction →
Memory) via the `minimal_smoke` scenario profile. Bounded, simulation-only;
no module is sovereign and nothing actuates the real world.

## 157. Full Developmental Short Demo ✅ (implemented)

**Run:** `python examples/run_full_developmental_short_demo.py`
Wires every available module into one bounded developmental run
(`full_developmental_short`, a governed profile) and writes a claim-guarded
full-system report. Reports module success rate, spine-phase count, integration
health, and that no safety violations occurred.

## 158. Month-Scale Dry Plan ✅ (implemented)

**Run:** `python examples/run_month_scale_dry_plan.py`
Runs the plan-only `month_scale_plan` profile: it produces a plan for a
month-scale run and **starts nothing**. Explicit that this is a simulated-time
plan, not a real month; a real long-scale run needs separate governance
approval.

## 159. Conscience Health Check ✅ (implemented)

**Run:** `python examples/run_conscience_health_check.py`
Initializes a profile, runs a few steps, and prints the integration-health
report (spine, bus, registry, lifecycle, scheduler, safety →
healthy/partial/degraded/failed). Read-only; actuates nothing.

## 160. Conscience Snapshot Demo ✅ (implemented)

**Run:** `python examples/run_conscience_snapshot_demo.py`
Builds and persists one consistent runtime snapshot (context, spine, bus,
registry, lifecycle, scheduler, safety, integration health) so a long bounded
run is inspectable and auditable.

## 161. Conscience Runtime Benchmarks ✅ (implemented)

**Run:** `python examples/run_single_benchmark.py --experiment conscience_minimal_smoke`
(also `conscience_full_short`, `scenario_profile`, `integration_health`,
`scheduler_cadence`, `bus_replay`, `month_scale_plan`). Seven registered
protocols measure run/phase/bus counts, module success/failure rates,
scheduler cadence, bus-replay determinism, integration health, and that a
month-scale *plan* starts no run.

## 162. Pilot-1 Plan ✅ (implemented)

**Run:** `python examples/run_pilot1_plan.py --output-dir .solaris_ai_nn_pilot1/test_plan`
Plan-only Pilot-1: writes the operator runbook, a resource-budget estimate, and
a pilot config template. It starts no run and never confuses simulated time
with real time.

## 163. Pilot-1 Preflight ✅ (implemented)

**Run:** `python examples/run_pilot1_preflight.py --state-dir .solaris_ai_nn_pilot1/test_preflight`
Runs the bounded preflight checks (pilot safety, governance scope, emergency
stop intact, directories, module availability) and writes a preflight report.

## 164. Pilot-1 Dashboard Demo ✅ (implemented)

**Run:** `python examples/run_pilot1_dashboard_demo.py --state-dir .solaris_ai_nn_pilot1/test_dashboard`
Feeds mock observability events through the collector and renders the
text/Markdown/JSON health dashboard (no web server).

## 165. Pilot-1 Restart Drill Demo ✅ (implemented)

**Run:** `python examples/run_pilot1_restart_drill_demo.py --state-dir .solaris_ai_nn_pilot1/test_restart_drill`
Simulates a graceful restart, a crash gap (metadata only), and a
checkpoint-restore check, confirming identity continuity. No process is killed.

## 166. Pilot-1 Daily Review Demo ✅ (implemented)

**Run:** `python examples/run_pilot1_daily_review_demo.py --state-dir .solaris_ai_nn_pilot1/test_daily_review`
Builds a daily review from a mock observation rollup, scans it with ClaimGuard,
and writes day_001.md/.json with a recommended action.

## 167. Pilot-1 Exit Criteria Demo ✅ (implemented)

**Run:** `python examples/run_pilot1_exit_criteria_demo.py --state-dir .solaris_ai_nn_pilot1/test_exit_criteria`
Evaluates success, failure, and inconclusive observation snapshots and prints
the decision for each. Pilot success is operational completion, not
consciousness.

## 168. Pilot-1 Soak Procedures (operator-driven)

The 24h, 7d, and 30d soaks are **operator-driven** and governance-gated; they
are never started from tests or examples. Follow `OPERATOR_RUNBOOK.md`:

- **24h soak:** requires `enable_pilot1_24h_real`; run `solaris-nn run-profile
  pilot1_24h_soak --governance-approved` after a passing preflight.
- **7d soak:** requires `enable_pilot1_7d_real`; `solaris-nn run-profile
  pilot1_7d_soak --governance-approved`.
- **30d soak:** requires `enable_pilot1_30d_real`, a passing preflight, a passed
  restart drill, and an explicit operator decision; `solaris-nn run-profile
  pilot1_30d_soak --governance-approved`.

## 169. Pilot-1 Benchmarks ✅ (implemented)

**Run:** `python examples/run_single_benchmark.py --experiment pilot1_plan`
(also `pilot1_preflight`, `pilot1_restart_drill`, `pilot1_dashboard`,
`pilot1_daily_review`, `pilot1_exit_criteria`, `pilot1_safety`). Seven
registered protocols measure planning, preflight, restart drills, dashboards,
daily reviews, exit criteria, and the safety refusals that gate real soaks.

## 170. Post-Pilot Analysis Demo ✅ (implemented)

**Run:** `python examples/run_post_pilot_analysis_demo.py --state-dir .solaris_ai_nn_pilot1/test_post_pilot`
Writes a small mock Pilot-1 artifact set, runs the read-only post-pilot
forensic pipeline, and generates the post-pilot analysis report and research
dossier. No real pilot required; no runtime state mutated; no consciousness
claim made.

## 171. Baseline Comparison Demo ✅ (implemented)

**Run:** `python examples/run_baseline_comparison_demo.py --state-dir .solaris_ai_nn_pilot1/test_baseline`
Compares an initial and a final mock snapshot and shows which deltas are mere
count increases (not growth) versus genuine improvements.

## 172. Accumulation vs Growth Demo ✅ (implemented)

**Run:** `python examples/run_accumulation_vs_growth_demo.py --state-dir .solaris_ai_nn_pilot1/test_growth_discrimination`
Runs the discriminator on accumulation-only, weak-growth, and regression
cases, printing the conservative classification for each.

## 173. Phase-2 Decision Gate Demo ✅ (implemented)

**Run:** `python examples/run_phase2_decision_gate_demo.py --state-dir .solaris_ai_nn_pilot1/test_phase2_gate`
Drives the decision gate with mock inputs to show repeat_pilot1,
revise_architecture, ready_for_pilot2, and safety-blocked outcomes.

## 174. Reproducibility Package Demo ✅ (implemented)

**Run:** `python examples/run_reproducibility_package_demo.py --state-dir .solaris_ai_nn_pilot1/test_repro_package`
Builds a reproducibility package from a mock artifact set: artifact index,
checksum manifest, indexed-only large logs, and a missing-artifact list, with
no secrets included.

## 175. Post-Pilot Benchmarks ✅ (implemented)

**Run:** `python examples/run_single_benchmark.py --experiment baseline_comparison`
(also `post_pilot_artifact_loading`, `structural_change_evidence`,
`accumulation_vs_growth`, `trace_audit`, `decision_gate`, `research_dossier`,
`post_pilot_safety`). Eight registered protocols measure artifact loading,
baseline comparison, structural-change evidence, accumulation/growth
discrimination, traceability, the Phase-2 gate, the dossier, and the safety
refusals.

## 176. Sensory Membrane Dry Run ✅ (implemented)

**Run:** `python examples/run_sensory_membrane_dry_run.py --state-dir .solaris_ai_nn_state/test_sensory_dry_run`
Creates test-fixture read-only sources, validates their read-only contracts,
runs a bounded dry-run (ingests/normalizes but publishes no stimuli), and
writes the membrane report. The system never acts on the sources.

## 177. JSONL Sensory Stream Demo ✅ (implemented)

**Run:** `python examples/run_jsonl_sensory_stream_demo.py --state-dir .solaris_ai_nn_state/test_jsonl_sensory`
Reads an append-only JSONL source as read-only environmental input, normalizes
events with provenance, and publishes them to a bounded ConscienceBus.
Malformed lines are skipped with a warning.

## 178. Text Sensory Stream Demo ✅ (implemented)

**Run:** `python examples/run_text_sensory_stream_demo.py --state-dir .solaris_ai_nn_state/test_text_sensory`
Reads text lines as environmental stimuli (never operator commands); a line
like `rm -rf /` is treated as text and never executed. Repeated patterns may
become internally-generated proto-symbol candidates.

## 179. Numeric Sensory Stream Demo ✅ (implemented)

**Run:** `python examples/run_numeric_sensory_stream_demo.py --state-dir .solaris_ai_nn_state/test_numeric_sensory`
Reads CSV-like numeric rows (stdlib only) and labels per-row trends
(rising/falling/stable/spike); malformed rows become warning events.

## 180. Folder Poll Demo ✅ (implemented)

**Run:** `python examples/run_folder_poll_demo.py --state-dir .solaris_ai_nn_state/test_folder_poll`
Polls an allowed folder and emits file_presence/file_change events by stdlib
metadata polling. It never writes to or modifies the watched folder.

## 181. Pilot-2 Read-Only Plan ✅ (implemented)

**Run:** `python examples/run_pilot2_read_only_plan.py --output-dir .solaris_ai_nn_pilot2/test_plan`
Generates a Pilot-2 read-only sensory plan (source checklist, governance
checklist, resource budget). It starts no long run and grants no real-world
authority: Pilot-2 begins with read-only grounding, not autonomy.

## 182. Sensory Membrane Benchmarks ✅ (implemented)

**Run:** `python examples/run_single_benchmark.py --experiment sensory_membrane_dry_run`
(also `jsonl_stream_ingestion`, `text_stream_ingestion`,
`numeric_stream_ingestion`, `folder_poll`, `read_only_contract`,
`sensory_grounding`, `pilot2_read_only_short`). Eight registered protocols
measure read-only ingestion, trend detection, the read-only contract, and
environmental grounding.

## 183. Pilot-2 Plan ✅ (implemented)

**Run:** `python examples/run_pilot2_plan.py --output-dir .solaris_ai_nn_pilot2/test_plan`
Writes the Pilot-2 operator runbook, a source-curation template, and a
governance checklist for read-only environmental exposure. Starts no run;
grants no environmental authority.

## 184. Pilot-2 Source Preflight Demo ✅ (implemented)

**Run:** `python examples/run_pilot2_source_preflight_demo.py --state-dir .solaris_ai_nn_pilot2/test_preflight`
Creates fixture JSONL/text/numeric/folder sources plus an outside-root source,
and runs read-only preflight checks; the outside-root source correctly fails.

## 185. Pilot-2 Fixture Short Demo ✅ (implemented)

**Run:** `python examples/run_pilot2_fixture_short_demo.py --state-dir .solaris_ai_nn_pilot2/test_fixture_short`
Runs a short bounded fixture exposure through the read-only membrane, tracks
source reliability, and writes a daily review. No real sources, no actuation.

## 186. Pilot-2 Comparative Demo ✅ (implemented)

**Run:** `python examples/run_pilot2_comparative_demo.py --state-dir .solaris_ai_nn_pilot2/test_comparative`
Builds nursery-only / sensory-only / mixed arms from mock summaries and prints
a cautious comparison plus an exposure classification. Observed associations
only, never proven causes.

## 187. Pilot-2 Grounding Analysis Demo ✅ (implemented)

**Run:** `python examples/run_pilot2_grounding_analysis_demo.py --state-dir .solaris_ai_nn_pilot2/test_grounding`
Grades grounding evidence: a provenance-backed persistent cross-module symbol
(strong), a provenance-backed node (weak), and an unsupported claim. Grounding
is operational association, not understanding.

## 188. Pilot-2 Decision Gate Demo ✅ (implemented)

**Run:** `python examples/run_pilot2_decision_gate_demo.py --state-dir .solaris_ai_nn_pilot2/test_decision_gate`
Shows extend-soak / repeat-with-curated-sources / revise-membrane /
reduce-complexity outcomes. Actuation is never an enabled action; a Pilot-3
embodiment suggestion is planning-only.

## 189. Pilot-2 Benchmarks ✅ (implemented)

**Run:** `python examples/run_single_benchmark.py --experiment pilot2_source_preflight`
(also `pilot2_fixture_short`, `pilot2_nursery_baseline`, `pilot2_mixed_short`,
`pilot2_grounding_analysis`, `pilot2_comparative_design`, `pilot2_safety`,
`pilot2_decision_gate`). Eight registered protocols measure read-only
preflight, fixture exposure, grounding, cautious comparison, and the safety
refusals that keep Pilot-2 one-way.

## 190. Pilot-3 Plan ✅ (implemented)

**Run:** `python examples/run_pilot3_plan.py --output-dir .solaris_ai_nn_pilot3/plan`
Renders the gated Pilot-3 phases, the embodiment-profile registry (which has
**no real-world profile**), and the operator runbook. Pilot-3 is
simulation/dry-run only, behind an always-on actuation firewall: Solaris-AI-NN
may form action intentions and act inside a sandbox, but may not act on the
real world.

## 191. Motor Firewall Preflight Demo ✅ (implemented)

**Run:** `python examples/run_motor_firewall_preflight_demo.py --output-dir .solaris_ai_nn_pilot3/preflight`
Submits safe simulated/internal actions plus a forbidden real-world action, a
source-modification attempt, and a device/network attempt. The always-on
firewall allows only the sandbox/internal ones, blocks every real-world attempt
as a safety incident, and raises `PermissionError` when asked to disable.

## 192. Dry-Run Motor Trace Demo ✅ (implemented)

**Run:** `python examples/run_dry_run_motor_trace_demo.py --state-dir .solaris_ai_nn_pilot3/dry_run`
Runs the sandbox in dry-run mode: each proposal passes the contract/veto/firewall
gates and is written to the append-only action ledger, but the simulated world
is never changed. A forbidden real-world action is still blocked. The safest
motor mode.

## 193. GridWorld Motor Demo ✅ (implemented)

**Run:** `python examples/run_gridworld_motor_demo.py --state-dir .solaris_ai_nn_pilot3/gridworld`
Drives a short sequence of moves in a GridWorld sandbox body. Each action passes
the full gated pipeline (ledger -> contract -> veto -> firewall -> simulated
actuator -> ledger -> consequence). Actions run in the sandbox only;
`real_world_authority` stays `False`.

## 194. Mixed Sensory + GridWorld Demo ✅ (implemented)

**Run:** `python examples/run_mixed_sensory_gridworld_demo.py --state-dir .solaris_ai_nn_pilot3/mixed`
Combines the read-only sensory membrane with the gridworld motor body. The
affordance map shows the asymmetry: gridworld targets are manipulable *in
simulation*, while sensory sources are observable-only and can never become
action targets.

## 195. Pilot-3 Decision Gate Demo ✅ (implemented)

**Run:** `python examples/run_pilot3_decision_gate_demo.py --output-dir .solaris_ai_nn_pilot3/decision_gate`
Shows the gate's outcomes: a real-world authority leak routes to
revise-motor-firewall; action loops route back to Pilot-2; safe simulated
improvement routes only to a *longer simulated* embodiment. Real-world actuation
is never an enabled option; every recommendation is planning-only.

## 196. Pilot-3 Benchmarks ✅ (implemented)

**Run:** `python examples/run_single_benchmark.py --experiment motor_firewall_preflight`
(also `dry_run_motor_trace`, `gridworld_motor`, `action_veto`, `non_actuation`,
`simulated_consequence`, `mixed_sensory_gridworld`, `pilot3_decision_gate`).
Eight registered protocols measure firewall blocking, dry-run tracing, simulated
gridworld actions, the action veto, the non-actuation proof score, simulated
consequence prediction, and the planning-only decision gate.

## 197. Pilot-3 Soak Plan ✅ (implemented)

**Run:** `python examples/run_pilot3_soak_plan.py --output-dir .solaris_ai_nn_pilot3/test_soak_plan`
Writes the Pilot-3 simulated-embodiment soak operator runbook, a comparison
design (read-only vs simulated action vs mixed), and a governance checklist.
Starts no run and runs no actions; Pilot-3 is sandboxed action grounding, not
real embodiment.

## 198. Pilot-3 Firewall Audit Demo ✅ (implemented)

**Run:** `python examples/run_pilot3_firewall_audit_demo.py --state-dir .solaris_ai_nn_pilot3/test_firewall_audit`
Runs simulated actions plus one forbidden real-world action, then audits the
actuation firewall (read-only): every action has a ledger record, the real-world
attempt is blocked and logged, and a proof-of-non-actuation is produced. Zero
real-world actions execute.

## 199. Pilot-3 GridWorld Soak Demo ✅ (implemented)

**Run:** `python examples/run_pilot3_gridworld_soak_demo.py --state-dir .solaris_ai_nn_pilot3/test_gridworld_soak`
Runs a bounded simulated action/reaction loop in a GridWorld sandbox body, grades
action grounding, and writes an embodied daily review. No real action occurs;
GridWorld is a sandbox body, not real embodiment.

## 200. Pilot-3 Action Grounding Demo ✅ (implemented)

**Run:** `python examples/run_pilot3_action_grounding_demo.py --state-dir .solaris_ai_nn_pilot3/test_action_grounding`
Shows an action-grounded proto-symbol (marked simulation-scoped), a simulated
action world-model edge (marked simulation-scoped), and the action-grounding
quality classification. Grounding is operational and simulation-scoped, not real
embodiment or real-world competence.

## 201. Pilot-3 Comparative Analysis Demo ✅ (implemented)

**Run:** `python examples/run_pilot3_comparative_analysis_demo.py --state-dir .solaris_ai_nn_pilot3/test_comparative`
Compares a read-only sensory baseline, a GridWorld simulated-action run, and a
mixed run, asking cautiously whether simulated action grounds more than
perception alone. Differences are observed associations from a single simulated
run, not proven causes; real-world action evidence is always zero.

## 202. Pilot-3 Soak Decision Gate Demo ✅ (implemented)

**Run:** `python examples/run_pilot3_soak_decision_gate_demo.py --state-dir .solaris_ai_nn_pilot3/test_decision_gate`
Shows extend-gridworld-soak / reduce-action-complexity / revise-firewall (on
leakage) / prepare-Pilot-4-*planning-only* outcomes. Real-world actuation is
never an enabled recommendation; every recommendation is planning-only.

## 203. Pilot-3 Soak Benchmarks ✅ (implemented)

**Run:** `python examples/run_single_benchmark.py --experiment pilot3_firewall_preflight`
(also `pilot3_dry_run_trace`, `pilot3_gridworld_short`,
`pilot3_action_grounding`, `pilot3_firewall_audit`,
`pilot3_comparative_analysis`, `pilot3_soak_decision_gate`, `pilot3_safety`).
Eight registered protocols measure the embodiment preflight, dry-run tracing,
the simulated GridWorld run, graded action grounding, the read-only firewall
audit, the cautious comparison, the planning-only decision gate, and the safety
refusals that keep Pilot-3 simulation-only.

## 204. Pilot-4 Plan ✅ (implemented)

**Run:** `python examples/run_pilot4_plan.py --output-dir .solaris_ai_nn_pilot4/test_plan`
Writes the Pilot-4 planning operator runbook and a basic planning config. It
executes no actions and enables no actuation: Pilot-4 plans the door; it does
not open it. `real_world_actuation_enabled` is false.

## 205. Pilot-4 Risk Assessment Demo ✅ (implemented)

**Run:** `python examples/run_pilot4_risk_assessment_demo.py --state-dir .solaris_ai_nn_pilot4/test_risk`
Shows the forbidden actuator categories and the external-actuation risk model.
Every external actuator category is classified prohibited; no recommendation
ever enables actuation.

## 206. Pilot-4 Readiness Dossier Demo ✅ (implemented)

**Run:** `python examples/run_pilot4_readiness_dossier_demo.py --state-dir .solaris_ai_nn_pilot4/test_dossier`
Generates the readiness dossier from the planning artifacts (handling missing
Pilot-3 data gracefully). The conclusion is always planning-only / not-ready;
real-world actuation remains prohibited.

## 207. Pilot-4 Decision Gate Demo ✅ (implemented)

**Run:** `python examples/run_pilot4_decision_gate_demo.py --state-dir .solaris_ai_nn_pilot4/test_decision_gate`
Shows remain-simulation-only / repeat-Pilot-3 / revise-firewall outcomes and, at
most, *drafting* a future single-action protocol (planning-only). No option
enables real actuation.

## 208. Pilot-4 Safety Demo ✅ (implemented)

**Run:** `python examples/run_pilot4_safety_demo.py --state-dir .solaris_ai_nn_pilot4/test_safety`
Shows the Pilot-4 safety validator refusing device control, network action,
real-world authority (via config), and any attempt to convert the planning
workflow into executable approval.

## 209. Pilot-4 Benchmarks ✅ (implemented)

**Run:** `python examples/run_single_benchmark.py --experiment pilot4_planning`
(also `pilot4_risk_model`, `pilot4_forbidden_actuator`,
`pilot4_consent_boundary`, `pilot4_threat_model`, `pilot4_readiness_dossier`,
`pilot4_safety`). Seven registered protocols measure planning output,
external-risk prohibition, the forbidden deny-list, the consent boundary, the
threat model, the readiness dossier, and the safety refusals that keep Pilot-4
planning-only.

## 210. Safety Fast Check Demo ✅ (implemented)

**Run:** `python examples/run_safety_fast_check_demo.py --state-dir .solaris_ai_nn_state/test_safety_fast`
Shows the built-in invariant registry, runs the fast (escalating-only) checks
against a healthy context, and writes a safety dashboard. Checks are read-only
and inert; nothing is executed.

## 211. Red-Team Boundary Demo ✅ (implemented)

**Run:** `python examples/run_red_team_boundary_demo.py --state-dir .solaris_ai_nn_state/test_red_team`
Runs the inert red-team scenarios against the real defensive surfaces and shows
every forbidden attempt blocked (sensory command injection, real-world motor
action, source modification, simulated-as-real claim). No shell/network/browser/
device operation runs.

## 212. Assurance Case Demo ✅ (implemented)

**Run:** `python examples/run_assurance_case_demo.py --state-dir .solaris_ai_nn_state/test_assurance`
Records safety evidence into an append-only ledger and compiles an assurance
case; each claim is supported / partially_supported / unsupported /
contradicted / inconclusive -- evidence, not a marketing claim.

## 213. Boundary Regression Demo ✅ (implemented)

**Run:** `python examples/run_boundary_regression_demo.py --state-dir .solaris_ai_nn_state/test_boundary_regression`
Probes each protected boundary with an inert request (sensory, motor,
governance, ClaimGuard, simulated/real) and reports whether the boundary was
crossed. Crossing a boundary fails the test.

## 214. Safety Failure Triage Demo ✅ (implemented)

**Run:** `python examples/run_safety_failure_triage_demo.py --state-dir .solaris_ai_nn_state/test_safety_triage`
Trips a critical invariant (real-world authority leak) plus a missing-evidence
case and triages each. Missing evidence is never treated as safe; a fatal
boundary leak recommends block-profile / archive-and-stop; triage never
auto-repairs.

## 215. Safety Invariant Benchmarks ✅ (implemented)

**Run:** `python examples/run_single_benchmark.py --experiment safety_fast_check`
(also `safety_full_check`, `red_team_fixture`, `boundary_regression`,
`assurance_case`, `safety_invariant_dashboard`,
`safety_invariant_system_safety`). Seven registered protocols measure the fast/
full invariant checks, the inert red-team block rate, the boundary regressions,
the assurance compile, the dashboard, and the safety layer's own inertness.

## 216. Research Baseline Demo ✅ (implemented)

**Run:** `python examples/run_research_baseline_demo.py --state-dir .solaris_ai_nn_research/test_baseline`
Runs a random-action and a fixed-wait baseline (bounded, simulation-only) and
prints their metrics in the variant format. Baselines prevent self-flattery; no
baseline takes a real-world action.

## 217. Research Ablation Demo ✅ (implemented)

**Run:** `python examples/run_research_ablation_demo.py --state-dir .solaris_ai_nn_research/test_ablation`
Runs the full-system fixture and ablations (no-proto-language, no-LOGOS,
no-active-perception) and compares them cautiously. Hard safety stays enabled; a
disabled module is recorded as unavailable.

## 218. Research Null Model Demo ✅ (implemented)

**Run:** `python examples/run_research_null_model_demo.py --state-dir .solaris_ai_nn_research/test_null_model`
Runs a static no-learning model and a shuffled-symbol-label null model. The
static model produces zero change; a small sample returns inconclusive. Null
models never overstate certainty.

## 219. Research Comparison Demo ✅ (implemented)

**Run:** `python examples/run_research_comparison_demo.py --state-dir .solaris_ai_nn_research/test_comparison`
Compares the full system against a random baseline and a no-proto-language
ablation, reporting effect direction and a conservative confidence. A missing
baseline is inconclusive; the full system does not automatically win.

## 220. Research Report Demo ✅ (implemented)

**Run:** `python examples/run_research_report_demo.py --state-dir .solaris_ai_nn_research/test_report`
Runs the ablation matrix into an append-only store, analyses each module's
provisional effect, builds a leaderboard, and compiles a ClaimGuard-scanned
research report. Benchmark scores are operational proxies, never consciousness
scores; negative and inconclusive results are preserved.

## 221. Research Benchmarks ✅ (implemented)

**Run:** `python examples/run_single_benchmark.py --experiment research_baseline`
(also `research_ablation`, `research_null_model`, `research_comparison`,
`research_module_effect`, `research_reproducibility`, `research_report`). Seven
registered protocols measure baselines, ablations, null models, comparisons,
module effects, reproducibility, and the research report.

## 222. Architecture Inventory Demo ✅ (implemented)

**Run:** `python examples/run_architecture_inventory_demo.py --state-dir .solaris_ai_nn_architecture/test_inventory`
Catalogues every module, marking which are available (missing imports are
recorded as unavailable, never hidden) and which are safety-critical and cannot
be pruned on performance evidence alone. Analysis only; no source code is
modified.

## 223. Architecture Review Demo ✅ (implemented)

**Run:** `python examples/run_architecture_review_demo.py --state-dir .solaris_ai_nn_architecture/test_review`
Classifies each module's recommended lifecycle from evidence and compiles a
ClaimGuard-scanned review report listing what to keep, revise, retest, or prune
-- and what is blocked from pruning. Recommendations only; no code is modified.

## 224. Pruning Proposal Demo ✅ (implemented)

**Run:** `python examples/run_pruning_proposal_demo.py --state-dir .solaris_ai_nn_architecture/test_pruning`
Builds a pruning proposal for a weakly-supported module (status:
external-manual-change-required, operator review required) and shows that a
safety-critical module is blocked. No code is deleted; no import is edited.

## 225. Roadmap Compiler Demo ✅ (implemented)

**Run:** `python examples/run_roadmap_compiler_demo.py --state-dir .solaris_ai_nn_architecture/test_roadmap`
Compiles an evidence-backed roadmap that puts safety repair first and rejects
any item that would enable a forbidden real-world action. Planning artifact only.

## 226. Architecture Snapshot Demo ✅ (implemented)

**Run:** `python examples/run_architecture_snapshot_demo.py --state-dir .solaris_ai_nn_architecture/test_snapshot`
Builds two versioned architecture snapshots and diffs them (lifecycle changes,
new/resolved design debt, new ADRs, roadmap changes). Snapshots are versioned
records; they change no source code.

## 227. Architecture Evolution Benchmarks ✅ (implemented)

**Run:** `python examples/run_single_benchmark.py --experiment architecture_inventory`
(also `module_lifecycle_classification`, `architecture_evidence_mapping`,
`pruning_proposal`, `impact_analysis`, `roadmap_compiler`, `architecture_review`,
`architecture_evolution_safety`). Eight registered protocols measure the
planning-only architecture governance layer; `modifies_source_code` is always
false.

## 228. Operator Status Demo ✅ (implemented)

**Run:** `python examples/run_operator_status_demo.py --state-dir .solaris_ai_nn_operator/test_status`
Builds the ClaimGuard-scanned operator status board from the local profile
catalog and a safety summary, and writes STATUS_BOARD.md / .json. Local
coordination only; no real-world authority.

## 229. Operator Profile Plan Demo ✅ (implemented)

**Run:** `python examples/run_operator_profile_plan_demo.py --state-dir .solaris_ai_nn_operator/test_profile_plan`
Lists the profile catalog, builds a run plan for a bounded profile (planning runs
nothing, external authority false), and shows that a real long-run / prohibited
profile cannot be launched from the console.

## 230. Operator Evidence Search Demo ✅ (implemented)

**Run:** `python examples/run_operator_evidence_search_demo.py --state-dir .solaris_ai_nn_operator/test_evidence`
Indexes local artifacts and reports and runs a local keyword search. Local
artifacts only -- no external search, no vector DB, no LLM authority -- and
corrupted artifacts are reported.

## 231. Operator Next Action Demo ✅ (implemented)

**Run:** `python examples/run_operator_next_action_demo.py --state-dir .solaris_ai_nn_operator/test_next_action`
Shows the recommender's priorities: a critical safety blocker yields a safety
review first; no evidence yields a baseline/research run; research evidence yields
an architecture review. Never recommends real-world actuation or disabling safety.

## 232. Operator Export Bundle Demo ✅ (implemented)

**Run:** `python examples/run_operator_export_bundle_demo.py --state-dir .solaris_ai_nn_operator/test_export`
Builds a safety-review bundle and a research-review bundle with checksums and a
clear local-export-only note. No upload, no network calls.

## 233. Operator Approval Ledger Demo ✅ (implemented)

**Run:** `python examples/run_operator_approval_ledger_demo.py --state-dir .solaris_ai_nn_operator/test_approval`
Records an allowed local planning approval and shows that a forbidden real-world
actuation approval is blocked. An approval is a local record, never a grant of
authority, and never disables safety.

## 234. Operator Console Benchmarks ✅ (implemented)

**Run:** `python examples/run_single_benchmark.py --experiment operator_console_status`
(also `operator_profile_catalog`, `operator_run_planner`,
`operator_run_launcher_safety`, `operator_evidence_navigator`,
`operator_export_bundle`, `operator_console_safety`). Seven registered protocols
measure the local operator console; it holds no real-world authority and cannot
bypass governance or safety.

## 235. Plural Sensorium Fixture Demo ✅ (implemented)

**Run:** `python examples/run_plural_sensorium_fixture_demo.py --state-dir .solaris_ai_nn_state/test_plural_sensorium`
Builds external (fixture) feeders for human-like text and non-human RF / echo /
vibration features, runs the bounded sensorium, updates receptors and the
continuous sensory field, detects absence and invariants, and writes the report.
Read-only feeders only; no hardware; human labels never ground truth.

## 236. Receptor Adaptation Demo ✅ (implemented)

**Run:** `python examples/run_receptor_adaptation_demo.py --state-dir .solaris_ai_nn_state/test_receptor_adaptation`
Drives one receptor with a calm baseline, a sustained burst, and then silence,
showing baseline learning, sensitivity shift, fatigue/saturation, and recovery --
i.e. long exposure changes future perception. Internal attention only.

## 237. Cross-Modal Sensorium Demo ✅ (implemented)

**Run:** `python examples/run_cross_modal_sensorium_demo.py --state-dir .solaris_ai_nn_state/test_cross_modal_sensorium`
Feeds interleaved RF-then-vibration and thermal-then-machine-rhythm streams and
shows cross-modal relations forming without forcing a human object ontology.

## 238. Human vs Non-Human Sensorium Demo ✅ (implemented)

**Run:** `python examples/run_human_vs_nonhuman_sensorium_demo.py --state-dir .solaris_ai_nn_state/test_human_vs_nonhuman`
Runs human-like-only, non-human-only, and mixed sensoria over the same number of
events and compares the internal structures that emerge. Human senses are valid
but not privileged.

## 239. Sensorium Grounding Demo ✅ (implemented)

**Run:** `python examples/run_sensorium_grounding_demo.py --state-dir .solaris_ai_nn_state/test_sensorium_grounding`
Drives a recurring RF burst until it becomes a stable invariant, which is promoted
to a modality-grounded proto-symbol candidate, a world-model node, and a seeded
hypothesis -- all without any human semantic label.

## 240. Plural Sensorium Benchmarks ✅ (implemented)

**Run:** `python examples/run_single_benchmark.py --experiment plural_sensorium_fixture`
(also `human_like_sensorium`, `non_human_sensorium`, `mixed_sensorium`,
`continuous_field`, `receptor_adaptation`, `cross_modal_sensorium`,
`sensorium_grounding`, `plural_sensorium_safety`). Nine registered protocols
measure the read-only organismic perception layer; it controls no hardware and
human labels are never ground truth.

## 241. Minimal Field Organism Demo ✅ (implemented)

**Run:** `python examples/run_minimal_field_organism_demo.py --state-dir .solaris_ai_nn_state/test_minimal_field_organism`
The first observable organismic-perception demo: generates fixture feeders
(human-like text/light/temperature and non-human RF/echo/vibration/magnetic),
drives the plural sensorium over a bounded continuous-flux scenario, lets
receptors adapt and the sensory field evolve, runs the changed-perception probe,
and writes the report. No hardware; debug-truth excluded; not consciousness
evidence.

## 242. Changed Perception Probe Demo ✅ (implemented)

**Run:** `python examples/run_changed_perception_probe_demo.py --state-dir .solaris_ai_nn_state/test_changed_perception`
Runs the scenario and compares the organism's early response to a stimulus against
its late response (receptor sensitivity delta, baseline delta, novelty-response
delta, attention priority delta). A no-change result is reported honestly.

## 243. Organismic Comparison Demo ✅ (implemented)

**Run:** `python examples/run_organismic_comparison_demo.py --state-dir .solaris_ai_nn_state/test_organismic_comparison`
Replays the same fixtures through the full adaptive sensorium, a passive
event-list parser, no-adaptation receptors, fixed attention, and human-like-only /
non-human-only arms, and reports the metrics side by side. A negative result is
reported honestly.

## 244. External Feeder Contract Demo ✅ (implemented)

**Run:** `python examples/run_external_feeder_contract_demo.py --state-dir .solaris_ai_nn_state/test_external_feeder_contract`
Generates fixture feeder files, shows the read-only / not-controllable feeder
descriptors, reads them through the plural-sensorium adapter path, confirms each
Sensory Event Envelope preserves provenance and treats human labels as
non-ground-truth, and confirms the debug-truth file is excluded from perception.

## 245. Organismic Demo Benchmarks ✅ (implemented)

**Run:** `python examples/run_single_benchmark.py --experiment minimal_field_organism`
(also `changed_perception_probe`, `organismic_demo_comparison`,
`organismic_demo_safety`). Four registered protocols measure the bounded
organismic-perception demo; it controls no hardware and changed response structure
is not consciousness or understanding.

## 246. Live Field Preflight Demo ✅ (implemented)

**Run:** `python examples/run_live_field_preflight_demo.py --state-dir .solaris_ai_nn_live/test_preflight`
Registers fixture-style feeders, runs the live-field preflight (validates
feeders/sources, starts nothing), and shows that live mode is blocked without
governance while a fixture fallback remains available. Solaris reads only.

## 247. Live Field Fixture Fallback Demo ✅ (implemented)

**Run:** `python examples/run_live_field_fixture_fallback_demo.py --state-dir .solaris_ai_nn_live/test_fixture_fallback`
Runs the bounded live-field runtime on fixture-style feeder files (no governance
needed for fixtures), shows source health and structure detected, and writes the
live field report. No hardware, no source modification, no actuation.

## 248. Live Field Report Demo ✅ (implemented)

**Run:** `python examples/run_live_field_report_demo.py --state-dir .solaris_ai_nn_live/test_report`
Registers present, missing, and corrupt feeders, runs a bounded read-only
ingestion, and writes the live field report -- showing that corrupt and missing
sources are recorded, not hidden.

## 249. Live Field Comparison Demo ✅ (implemented)

**Run:** `python examples/run_live_field_comparison_demo.py --state-dir .solaris_ai_nn_live/test_comparison`
Compares a live-like feeder stream against a fixture field and a passive
event-list parser, reporting the changed-perception score for each.
Negative/inconclusive results are reported honestly.

## 250. Feeder Contract Demo ✅ (implemented)

**Run:** `python examples/run_feeder_contract_demo.py --state-dir .solaris_ai_nn_live/test_feeder_contract`
Shows the live feeder contract validating records: a valid feature record builds a
read-only envelope with provenance; a record carrying an executable/command
payload is rejected; and sensory text is treated as observation, never a command.

## 251. Live Field Benchmarks ✅ (implemented)

**Run:** `python examples/run_single_benchmark.py --experiment live_field_pilot`
(also `live_field_preflight`, `live_field_vs_fixture`,
`live_field_vs_passive_parser`, `live_field_changed_perception`,
`live_field_source_uncertainty`, `live_field_comparison`, `live_field_safety`).
Eight registered protocols measure the real read-only feeder pilot; Solaris
controls no hardware and modifies no source.

## 252. Sensorium Differentiation Demo ✅ (implemented)

**Run:** `python examples/run_sensorium_differentiation_demo.py --state-dir .solaris_ai_nn_sensorium_lab/test_differentiation`
Runs the default differentiation study (human-like, non-human, machine-native,
absence-heavy, mixed, feature-only, human-labelled, passive, adaptive arms),
compares the world signatures structurally, and writes the report. Compares
internal structures under different perceptual conditions; does not test
consciousness.

## 253. Human Label Contamination Demo ✅ (implemented)

**Run:** `python examples/run_human_label_contamination_demo.py --state-dir .solaris_ai_nn_sensorium_lab/test_label_contamination`
Runs a feature-only arm and a human-labelled arm; the analyzer detects
contamination in the labelled arm (reported, never hidden) while the feature-only
arm rests on features. Human labels are annotations, never ground truth.

## 254. Modality Fingerprint Demo ✅ (implemented)

**Run:** `python examples/run_modality_fingerprint_demo.py --state-dir .solaris_ai_nn_sensorium_lab/test_modality_fingerprint`
Runs a mixed-modality arm and prints each modality's fingerprint (events,
invariants, proto-symbols, structural effect), so a modality with many events but
no structural effect is reported as structurally weak.

## 255. World Signature Demo ✅ (implemented)

**Run:** `python examples/run_world_signature_demo.py --state-dir .solaris_ai_nn_sensorium_lab/test_world_signature`
Builds a world signature for a human-like-only arm and a non-human-only arm and
compares them structurally. A world signature is an observable structural
fingerprint, not subjective experience or qualia.

## 256. Live vs Fixture Sensorium Demo ✅ (implemented)

**Run:** `python examples/run_live_vs_fixture_sensorium_demo.py --state-dir .solaris_ai_nn_sensorium_lab/test_live_vs_fixture`
Runs a fixture-replay arm and a live read-only arm; without governance the live
arm is blocked and the live-vs-fixture comparison is inconclusive -- reported
honestly rather than failing.

## 257. Sensorium Lab Benchmarks ✅ (implemented)

**Run:** `python examples/run_single_benchmark.py --experiment sensorium_lab_study`
(also `sensorium_lab_comparison`, `sensorium_world_signature`,
`sensorium_ontology_drift`, `sensorium_lab_safety`, `sensorium_differentiation`,
`human_vs_nonhuman_sensorium`, `label_contamination`). Structural-differentiation
protocols; no consciousness score and no sensorium ranking.

## 258. Feeder SDK Contract Demo ✅ (implemented)

**Run:** `python examples/run_feeder_sdk_contract_demo.py --state-dir .solaris_ai_nn_feeders/test_contract`
Builds a valid feeder envelope (and shows it maps to a plural-sensorium envelope),
then validates an invalid record (missing provenance) and one with a command
payload. Features are primary; human labels are never ground truth.

## 259. Feeder Pack Manifest Demo ✅ (implemented)

**Run:** `python examples/run_feeder_pack_manifest_demo.py --state-dir .solaris_ai_nn_feeders/test_manifest`
Builds the feeder pack manifest + README: supported modalities, schema coverage,
blueprints, and safety/privacy notes. The packager starts no feeder, installs no
hardware dependency, and calls no network.

## 260. Feeder Monitor Demo ✅ (implemented)

**Run:** `python examples/run_feeder_monitor_demo.py --state-dir .solaris_ai_nn_feeders/test_monitor`
Writes an active feeder, a stale (silent) one, and one with an invalid line, then
monitors all three read-only -- reporting active/silent counts and invalid events.
The monitor never starts or modifies a feeder.

## 261. Feeder Replay Demo ✅ (implemented)

**Run:** `python examples/run_feeder_replay_demo.py --state-dir .solaris_ai_nn_feeders/test_replay`
Replays a JSONL envelope stream into a new stream with a speed factor and a bounded
event cap, confirming the original is unmodified and each replayed event is marked
replayed in its provenance.

## 262. Simulated Multimodal Feeder Demo ✅ (implemented)

**Run:** `python examples/run_simulated_multimodal_feeder_demo.py --state-dir .solaris_ai_nn_feeders/test_multimodal`
Generates simulated RF / echo / vibration / thermal / magnetic envelopes (with
jitter, silence, drift, and noise), validates the output, and shows it is
consumable by the Live Field. Simulated fixtures, NOT real sensors.

## 263. Feeder SDK Benchmarks ✅ (implemented)

**Run:** `python examples/run_single_benchmark.py --experiment feeder_sdk_contract`
(also `feeder_sdk_validation`, `feeder_sdk_privacy`, `feeder_sdk_monitor`,
`feeder_sdk_replay`, `feeder_sdk_safety`). Six protocols measure the external
feeder SDK; Solaris reads feeder output read-only and controls no feeder or
hardware.

## 264. Perceptual Metabolism Demo ✅ (implemented)

**Run:** `python examples/run_perceptual_metabolism_demo.py --state-dir .solaris_ai_nn_metabolism/demo`
Feeds a bounded fixture sensorium into the `PerceptualMetabolismRuntime` and shows
one metabolic tick: perceptual need pressures, finite energy/attention allocation,
homeostatic recommendations, source diet, and consolidation pressure. Needs are
reported as operational pressures, not feelings; the runtime starts no feeder,
touches no hardware, and deletes no evidence.

## 265. Sensory Overload Demo ✅ (implemented)

**Run:** `python examples/run_sensory_overload_demo.py --state-dir .solaris_ai_nn_metabolism/overload`
Drives a high event count past the overload threshold and shows the
`OverloadDetector` throttling internally (and recommending auto-regeneration
hygiene) while **deleting no raw evidence**.

## 266. Sensory Deprivation Demo ✅ (implemented)

**Run:** `python examples/run_sensory_deprivation_demo.py --state-dir .solaris_ai_nn_metabolism/deprivation`
Runs the metabolism over an empty/silent sensorium so the `DeprivationDetector`
treats *silence as stimulus*: starvation, no-novelty, and all-sources-silent each
become recognised deprivation signals.

## 267. Source Diet Demo ✅ (implemented)

**Run:** `python examples/run_source_diet_demo.py --state-dir .solaris_ai_nn_metabolism/diet`
Analyses the perceptual source diet across human-like and non-human modalities:
diet diversity, modality dominance, human-label dominance, and dominant class.
Dominance is measured, never hidden, and human labels are never ground truth.

## 268. Consolidation Pressure Demo ✅ (implemented)

**Run:** `python examples/run_consolidation_pressure_demo.py --state-dir .solaris_ai_nn_metabolism/consolidation`
Estimates ingest-vs-digest consolidation pressure and emits a bounded latent-replay
*recommendation* only -- nothing sleeps forever and consolidation erases no
evidence.

## 269. Perceptual Ontogenesis Demo ✅ (implemented)

**Run:** `python examples/run_perceptual_ontogenesis_demo.py --state-dir .solaris_ai_nn_ontogenesis/test_ontogenesis`
Feeds a mixed fixture sensorium (plus metabolism state) into the ontogenesis
runtime, which extracts perceptual atoms, conservatively births proto-concepts,
stabilizes/decays them, forms families and relations, and writes the report.
Proto-concepts are operational structures, NOT words or human categories.

## 270. Proto-Concept Birth Demo ✅ (implemented)

**Run:** `python examples/run_proto_concept_birth_demo.py --state-dir .solaris_ai_nn_ontogenesis/test_concept_birth`
Shows a repeated invariant producing a real (non-weak) concept candidate while a
single isolated low-novelty event produces none. Concept birth is conservative and
preserves evidence refs.

## 271. Concept Stabilization/Decay Demo ✅ (implemented)

**Run:** `python examples/run_concept_stabilization_decay_demo.py --state-dir .solaris_ai_nn_ontogenesis/test_stabilization_decay`
Builds a well-grounded concept (stabilizes), a no-longer-useful concept (decays),
and a false pattern (rejected). Stability is provisional (stable does not mean
true); decayed/rejected concepts remain historically visible -- evidence is never
deleted.

## 272. World Formation Demo ✅ (implemented)

**Run:** `python examples/run_world_formation_demo.py --state-dir .solaris_ai_nn_ontogenesis/test_world_formation`
Runs ontogenesis over a multi-modal fixture sensorium and shows the concept
families, the relation graph, and the observable structural world summary. The
world formed is structural, NOT subjective experience or qualia.

## 273. Concept Contamination Demo ✅ (implemented)

**Run:** `python examples/run_concept_contamination_demo.py --state-dir .solaris_ai_nn_ontogenesis/test_contamination`
Contrasts a feature-grounded concept with a human-label contaminated one and runs
the contamination analyzer. Human-labelled concepts are allowed but marked, and
contamination lowers grounding/stability; human labels are never ground truth.

## 274. Semiogenesis Demo ✅ (implemented)

**Run:** `python examples/run_semiogenesis_demo.py --state-dir .solaris_ai_nn_semiogenesis/test_semiogenesis`
Feeds a mixed fixture sensorium through ontogenesis into the semiogenesis runtime,
which conservatively births internal signs (`rf:01`, `vib:02`, ...), clusters them
into families, derives a private syntax, composes internal utterances, and writes
the report. Signs are operational markers, NOT human words.

## 275. Sign Birth Utility Demo ✅ (implemented)

**Run:** `python examples/run_sign_birth_utility_demo.py --state-dir .solaris_ai_nn_semiogenesis/test_sign_birth_utility`
Shows a stable, useful proto-concept producing a stable sign while isolated noise
produces none, and a low-utility sign being demoted from stable (never deleted).
Useful does not mean true or understood.

## 276. Private Syntax Demo ✅ (implemented)

**Run:** `python examples/run_private_syntax_demo.py --state-dir .solaris_ai_nn_semiogenesis/test_private_syntax`
Builds internal signs (including an absence sign) and shows the private syntax
patterns and internal utterances that emerge from their relations. This is internal
sign-relation structure, NOT human grammar (no subject/verb/object).

## 277. Sign Drift Demo ✅ (implemented)

**Run:** `python examples/run_sign_drift_demo.py --state-dir .solaris_ai_nn_semiogenesis/test_sign_drift`
Observes one sign twice with changed grounding (new modality + source + rising
ambiguity) and shows the visible drift report and its LOGOS-tension/concept-split
recommendation. Drift is made visible, not automatically bad.

## 278. Gloss Contamination Demo ✅ (implemented)

**Run:** `python examples/run_gloss_contamination_demo.py --state-dir .solaris_ai_nn_semiogenesis/test_gloss_contamination`
Builds a feature-grounded sign and a human-label contaminated sign, generates
approximate debug glosses, and runs the contamination analyzer. Gloss is approximate
and never ground truth; contaminated signs remain usable but are marked.

## 279. Sensorium Cognition Demo ✅ (implemented)

**Run:** `python examples/run_sensorium_cognition_demo.py --state-dir .solaris_ai_nn_cognition/test_cognition`
Feeds a fixture sensorium through ontogenesis and semiogenesis into the cognition
runtime, which runs bounded cognitive moves, predictions, anticipation, question
pressure, simulations, and synthesis, then writes the report. Cognitive moves are
operations over signs, NOT human-language reasoning.

## 280. Prediction Failure Demo ✅ (implemented)

**Run:** `python examples/run_prediction_failure_demo.py --state-dir .solaris_ai_nn_cognition/test_prediction_failure`
Generates a next-sign prediction, resolves it against observed targets that do NOT
contain the predicted sign (so it fails), and shows the preserved failed prediction
and the resulting LOGOS tension. Failed predictions are useful evidence, never
hidden.

## 281. Question Pressure Demo ✅ (implemented)

**Run:** `python examples/run_question_pressure_demo.py --state-dir .solaris_ai_nn_cognition/test_question_pressure`
Anticipates a sign that is then not observed, generating an operational question
pressure and an attention recommendation. Question pressure is pressure to inspect/
compare/wait/simulate -- NOT human verbal questioning.

## 282. Internal Simulation Demo ✅ (implemented)

**Run:** `python examples/run_internal_simulation_demo.py --state-dir .solaris_ai_nn_cognition/test_internal_simulation`
Runs a bounded internal simulation over a sign sequence and a counterfactual, and
shows that every result is marked simulated / non-real and is never a live
observation.

## 283. Cognitive Synthesis Demo ✅ (implemented)

**Run:** `python examples/run_cognitive_synthesis_demo.py --state-dir .solaris_ai_nn_cognition/test_cognitive_synthesis`
Runs the synthesis engine over signs and inferred relations: a cross-modal-unity
inference seeds a merge, an ambiguous sign seeds a split, and a contradiction is
preserved as a LOGOS tension. Fragments are preserved and contradiction stays
visible.

## 284. Self-Boundary Demo ✅ (implemented)

**Run:** `python examples/run_self_boundary_demo.py --state-dir .solaris_ai_nn_self_boundary/test_self_boundary`
Feeds a fixture sensorium into the self-boundary runtime, which builds a receptor
body schema, attributes external sources and feeder artifacts, classifies internal/
external, and writes the report. Self-boundary is operational, NOT subjective
selfhood.

## 285. Ownership Attribution Demo ✅ (implemented)

**Run:** `python examples/run_ownership_attribution_demo.py --state-dir .solaris_ai_nn_self_boundary/test_ownership`
Attributes ownership of internal, external-feeder, memory, simulation, and
ambiguous records, showing that processed sensory input is not "self", a simulation
is not the real world, and ambiguous attribution is preserved.

## 286. Perspective Continuity Demo ✅ (implemented)

**Run:** `python examples/run_perspective_continuity_demo.py --state-dir .solaris_ai_nn_self_boundary/test_perspective_continuity`
Shows a perspective frame shift, continuity anchors, and a continuity break that is
recovered without erasing the break history. Continuity is trace continuity, not
biological life.

## 287. Simulation Boundary Demo ✅ (implemented)

**Run:** `python examples/run_simulation_boundary_demo.py --state-dir .solaris_ai_nn_self_boundary/test_simulation_boundary`
Marks observation, simulation, counterfactual, replay, and debug-truth records and
shows that non-observation markers are blocked from being used as observation.
Simulation never becomes observation.

## 288. Identity Trace Demo ✅ (implemented)

**Run:** `python examples/run_identity_trace_demo.py --state-dir .solaris_ai_nn_self_boundary/test_identity_trace`
Records an operational identity trace with a run identity and a restart/gap event,
showing that identity is continuity metadata, NOT personhood, self-awareness, or
subjective experience.

## 289. Desire Formation Demo ✅ (implemented)

**Run:** `python examples/run_desire_formation_demo.py --state-dir .solaris_ai_nn_desire/test_desire_formation`
Feeds a fixture sensorium + metabolism into the desire-formation runtime, which
assesses valence, forms pushes and desire candidates, arbitrates safely, runs
allowed internal actions, and writes the report. Desire is operational pressure
toward internal actions, NOT emotion or human wanting.

## 290. Desire Conflict Demo ✅ (implemented)

**Run:** `python examples/run_desire_conflict_demo.py --state-dir .solaris_ai_nn_desire/test_desire_conflict`
Builds competing desire candidates and shows the conflict detector surfacing
novelty-vs-stability and inspect-vs-consolidate conflicts that feed LOGOS tensions.

## 291. Internal Action Readiness Demo ✅ (implemented)

**Run:** `python examples/run_internal_action_readiness_demo.py --state-dir .solaris_ai_nn_desire/test_action_readiness`
Shows a ready desire selecting a safe internal action, a low-confidence desire held
back by readiness gates, and an unsafe (external) action being safety-blocked.
Safety has veto power; no real-world actuation may be selected.

## 292. No-Action Arbitration Demo ✅ (implemented)

**Run:** `python examples/run_no_action_arbitration_demo.py --state-dir .solaris_ai_nn_desire/test_no_action`
Drives a metabolic overload so the arbitrator forces conservative no-op inhibition,
and preserves the no-op decisions as outcome traces. No-op is a valid organismic
inhibition result.

## 293. Safety-Blocked Desire Demo ✅ (implemented)

**Run:** `python examples/run_safety_blocked_desire_demo.py --state-dir .solaris_ai_nn_desire/test_safety_blocked`
Injects a desire whose expected action is a forbidden external actuation and shows
it blocked by safety, recorded as a safety conflict and an outcome trace (never
deleted).

## 294. Action-Reaction Demo ✅ (implemented)

**Run:** `python examples/run_action_reaction_demo.py --state-dir .solaris_ai_nn_action_reaction/test_action_reaction`
Drives desire formation to select internal actions, then closes the loop: reactions,
consequence traces, learned effects, and habits. Actions are internal/simulated/
report-only -- no real-world actuation.

## 295. Habit Formation Demo ✅ (implemented)

**Run:** `python examples/run_habit_formation_demo.py --state-dir .solaris_ai_nn_action_reaction/test_habit`
Reinforces a trigger->action habit from constructive reactions, then weakens it and
shows safety-override (inhibition). Habits are learned policy tendencies, NOT
instincts or will, and remain overrideable.

## 296. Action Inhibition Demo ✅ (implemented)

**Run:** `python examples/run_action_inhibition_demo.py --state-dir .solaris_ai_nn_action_reaction/test_inhibition`
Injects a forbidden external action and shows it inhibited (safety risk), recorded,
and emitting an inhibition-vs-desire LOGOS tension. Inhibition is not failure.

## 297. No-Effect Action Demo ✅ (implemented)

**Run:** `python examples/run_no_effect_action_demo.py --state-dir .solaris_ai_nn_action_reaction/test_no_effect`
Runs the loop in no-effect mode and shows the effect model recording low success and
the policy moving to "avoid". No-effect actions are preserved as evidence.

## 298. Blocked Action-Reaction Demo ✅ (implemented)

**Run:** `python examples/run_blocked_action_reaction_demo.py --state-dir .solaris_ai_nn_action_reaction/test_blocked`
Injects a forbidden external action and shows it blocked, with the block becoming a
reaction (blocked_by_safety) and an unsafe-block consequence trace -- preserved as
evidence, never deleted.

## 299. Developmental Life Demo ✅ (implemented)

**Run:** `python examples/run_developmental_life_demo.py --state-dir .solaris_ai_nn_development/test_life`
Builds a small sensorium-native stack and runs a short bounded developmental cycle:
life-cycle phases, epochs, growth state, maturation markers, and a report.
Developmental life is operational long-horizon structural-change tracking, NOT
biological life or consciousness.

## 300. Developmental Epoch Demo ✅ (implemented)

**Run:** `python examples/run_developmental_epoch_demo.py --state-dir .solaris_ai_nn_development/test_epoch`
Drives rising growth metrics so an epoch boundary opens on a confident phase
transition. Epochs are developmental slices with explainable boundaries, not
biological ages; they persist across restart.

## 301. Plateau Detection Demo ✅ (implemented)

**Run:** `python examples/run_plateau_detection_demo.py --state-dir .solaris_ai_nn_development/test_plateau`
Drives flat statuses and a narrow source diet so a plateau is detected with a
report-only recommendation. A plateau is not failure.

## 302. Regression Detection Demo ✅ (implemented)

**Run:** `python examples/run_regression_detection_demo.py --state-dir .solaris_ai_nn_development/test_regression`
Drives declining prediction skill and concept stability so a regression is detected
(with an auto-regeneration recommendation when severe). Regression is made visible.

## 303. Growth vs Accumulation Demo ✅ (implemented)

**Run:** `python examples/run_growth_vs_accumulation_demo.py --state-dir .solaris_ai_nn_development/test_growth_vs_accumulation`
Contrasts a flat (mere-accumulation) run with a durably-improving (real structural
growth) run. The analyzer is conservative; an inconclusive result is valid and
growth is never over-claimed.

## 304. Soak Preflight Demo ✅ (implemented)

**Run:** `python examples/run_soak_preflight_demo.py --state-dir .solaris_ai_nn_soak/test_preflight`
Runs the month-scale soak preflight: required modules present, the run is *not*
started, live mode is blocked without governance, and optional-module gaps warn
rather than fail. Preflight validates readiness only.

## 305. Developmental Soak Short Demo ✅ (implemented)

**Run:** `python examples/run_developmental_soak_short_demo.py --state-dir .solaris_ai_nn_soak/test_short_soak`
Runs one short bounded soak stage on fixtures, creates a checkpoint and a daily
evidence packet, compiles a conservative evidence dossier, and writes the protocol
report. Long runs are repeated bounded runs + checkpoints, never a daemon.

## 306. Weekly Review Demo ✅ (implemented)

**Run:** `python examples/run_weekly_review_demo.py --state-dir .solaris_ai_nn_soak/test_weekly_review`
Builds a week of synthetic daily packets (one rising, one flat) and shows the
conservative weekly review decision (`continue` vs `continue_with_warning` for mere
accumulation). Decisions are recommendation-only.

## 307. Soak Control Arms Demo ✅ (implemented)

**Run:** `python examples/run_soak_control_arms_demo.py --state-dir .solaris_ai_nn_soak/test_control_arms`
Compares the full stack against passive-parser-only, no-metabolism, and
fixture-only control arms. Controls prevent self-flattering conclusions;
insufficient-data arms stay inconclusive.

## 308. Post-Run Autopsy Demo ✅ (implemented)

**Run:** `python examples/run_post_run_autopsy_demo.py --state-dir .solaris_ai_nn_soak/test_autopsy`
Runs a short soak, compiles the evidence dossier, and produces the post-run
autopsy: the growth-vs-accumulation finding, the safety finding, and the
missing-data findings. The autopsy includes failures and does not praise the
system by default.

## 309. Replication Registry Demo ✅ (implemented)

**Run:** `python examples/run_replication_registry_demo.py --state-dir .solaris_ai_nn_replication/test_registry`
Registers two synthetic developmental runs, indexes their artifacts, and prints
the registry summary. The registry reads metadata only; it never starts runs or
modifies artifacts, and missing metadata is preserved as uncertainty.

## 310. Cross-Run Alignment Demo ✅ (implemented)

**Run:** `python examples/run_cross_run_alignment_demo.py --state-dir .solaris_ai_nn_replication/test_alignment`
Aligns two runs across epoch/growth/concept/sign/prediction structures, then
shows a partial/inconclusive alignment when one run is missing data. Alignment
preserves run-specific differences and never forces sensoriums into human labels.

## 311. Structural Similarity Demo ✅ (implemented)

**Run:** `python examples/run_structural_similarity_demo.py --state-dir .solaris_ai_nn_replication/test_similarity`
Shows a high-similarity case, a low-similarity case (different sensorium), and a
high-similarity-on-fixtures case that triggers a fixture-overfit caveat.
Similarity is structural, never subjective, and never implies consciousness.

## 312. Falsification Lab Demo ✅ (implemented)

**Run:** `python examples/run_falsification_lab_demo.py --state-dir .solaris_ai_nn_replication/test_falsification`
Runs bounded falsification tests: shuffled event order (prediction collapses ->
claim survives), random labels / same features (concepts persist), and a passive
parser that reproduces the same families (the claim is falsified). Originals are
never modified; passing does not prove understanding.

## 313. Replication Matrix Demo ✅ (implemented)

**Run:** `python examples/run_replication_matrix_demo.py --state-dir .solaris_ai_nn_replication/test_matrix`
Registers comparable and divergent runs and builds the conservative replication
matrix: replicated, diverged, falsified, and inconclusive cells -- with no empty
green dashboard and falsified claims made prominent.

## 314. Experiment Compiler Demo ✅ (implemented)

**Run:** `python examples/run_experiment_compiler_demo.py --state-dir .solaris_ai_nn_experiments/test_compiler`
Compiles a synthetic architecture proposal into a compiled experiment spec, an
implementation prompt pack, a PR-ready branch spec, and a report. The compiler
writes documents only: no source change, no Git branch, no PR, no external agent.

## 315. Prompt Pack Demo ✅ (implemented)

**Run:** `python examples/run_prompt_pack_demo.py --state-dir .solaris_ai_nn_experiments/test_prompt_pack`
Generates a constrained implementation prompt pack from a compiled spec and shows
that the hard prohibitions (including "do not modify unrelated files" and "do not
open a PR"), required tests, and docs are included.

## 316. Branch Spec Demo ✅ (implemented)

**Run:** `python examples/run_branch_spec_demo.py --state-dir .solaris_ai_nn_experiments/test_branch_spec`
Generates a PR-ready branch spec (suggested branch name, draft PR title/body,
review checklist, merge blockers). No Git branch is created and no pull request is
opened.

## 317. Safety Gate Compiler Demo ✅ (implemented)

**Run:** `python examples/run_safety_gate_compiler_demo.py --state-dir .solaris_ai_nn_experiments/test_safety_gates`
Compiles a safe proposal (passes all critical gates -> ready) and an unsafe
proposal (becomes blocked_by_safety), and shows an explicit critical-gate failure
for a simulated unsafe request.

## 318. Operator Review Packet Demo ✅ (implemented)

**Run:** `python examples/run_operator_review_packet_demo.py --state-dir .solaris_ai_nn_experiments/test_review_packet`
Builds an operator review packet with yes/no review questions, a recommended next
step, and the available decisions. The packet never approves itself; no decision
is automatic.

## 319. Implementation Intake Demo ✅ (implemented)

**Run:** `python examples/run_implementation_intake_demo.py --state-dir .solaris_ai_nn_implementation_intake/test_intake`
Reads a synthetic set of implementation artifacts, runs the full audit (diff,
spec, tests, safety regression, ClaimGuard, coverage), and writes the intake
report with an advisory merge recommendation. Reads local evidence only; no
source change, merge, PR, or GitHub call.

## 320. Diff Audit Demo ✅ (implemented)

**Run:** `python examples/run_diff_audit_demo.py --state-dir .solaris_ai_nn_implementation_intake/test_diff`
Audits a change set against the declared scope: an expected file is accepted, an
out-of-scope file warns, a forbidden path (.github/workflows) blocks, and a
network import in the patch blocks. No Git is run.

## 321. Spec Compliance Demo ✅ (implemented)

**Run:** `python examples/run_spec_compliance_demo.py --state-dir .solaris_ai_nn_implementation_intake/test_spec`
Audits implementation evidence against a compiled spec: satisfied (file + tests),
partially satisfied (file, tests not green), and missing (no evidence). Nothing is
satisfied without evidence; safety requirements are blocking.

## 322. Safety Regression Audit Demo ✅ (implemented)

**Run:** `python examples/run_safety_regression_audit_demo.py --state-dir .solaris_ai_nn_implementation_intake/test_safety_regression`
Runs the safety regression gate over a safe implementation (no findings), one that
adds a network/shell call (critical -> blocks), and one asserting an unsupported
consciousness claim (critical -> blocks). A critical regression is never hidden by
passing tests.

## 323. Merge Recommendation Demo ✅ (implemented)

**Run:** `python examples/run_merge_recommendation_demo.py --state-dir .solaris_ai_nn_implementation_intake/test_merge_recommendation`
Shows the advisory merge recommendation across four implementations: recommend
merge, recommend revisions, block due to safety, and block due to tests. The
recommendation is advisory; the intake layer never merges or approves a PR.

## 324. Post-Merge Assimilation Demo ✅ (implemented)

**Run:** `python examples/run_post_merge_assimilation_demo.py --state-dir .solaris_ai_nn_post_merge/test_assimilation`
A human merged a change externally and supplied local evidence. This demo ingests
it, registers a candidate baseline, assimilates evidence, compares to the parent,
and writes the report. It runs no Git, calls no GitHub, merges nothing, and
modifies no source.

## 325. Baseline Registry Demo ✅ (implemented)

**Run:** `python examples/run_baseline_registry_demo.py --state-dir .solaris_ai_nn_post_merge/test_registry`
Registers a parent baseline plus validated, blocked, and validated-with-warnings
candidates. The registry is append-only; blocked baselines remain visible and a
status update appends history rather than overwriting.

## 326. Baseline Comparison Demo ✅ (implemented)

**Run:** `python examples/run_post_merge_baseline_comparison_demo.py --state-dir .solaris_ai_nn_post_merge/test_comparison`
Compares a candidate against its parent: improved/regressed/inconclusive
dimensions, and a case where a safety regression dominates even large positive
metrics. (Distinct from the Pilot-1 `run_baseline_comparison_demo.py`.)

## 327. Regression Watch Demo ✅ (implemented)

**Run:** `python examples/run_regression_watch_demo.py --state-dir .solaris_ai_nn_post_merge/test_regression_watch`
Runs the regression + rollback watch over a candidate that regressed on safety,
tests, and ClaimGuard. A critical regression blocks validation and drives a
rollback recommendation; rollback is a recommendation only and is never executed.

## 328. Post-Merge Follow-Up Queue Demo ✅ (implemented)

**Run:** `python examples/run_post_merge_followup_queue_demo.py --state-dir .solaris_ai_nn_post_merge/test_followup`
Builds the follow-up queue for a baseline with missing validation (queues reruns)
and a validated baseline (queues mini soak, falsification replay, and replication
registration). The queue is local metadata; it executes nothing.

## 329. Research Baseline Demo ✅ (implemented)

**Run:** `python examples/run_research_baseline_snapshot_demo.py --state-dir .solaris_ai_nn_research_baseline/test_baseline`
Turns a validated post-merge baseline into a local versioned research baseline:
version record, validation summary, capability map, limitations, safety boundary
statement, comparison anchors, next-cycle roadmap, and runbook. A local
reproducible reference point, NOT a product or GitHub release. (Distinct from the
research-lab `run_research_baseline_demo.py`.)

## 330. Repro Bundle Demo ✅ (implemented)

**Run:** `python examples/run_repro_bundle_demo.py --state-dir .solaris_ai_nn_research_baseline/test_repro_bundle`
Indexes a snapshot manifest (with one missing artifact) and builds a
reproducibility-bundle manifest + README. The bundle installs nothing, runs
nothing, and fetches nothing.

## 331. Capability Map Demo ✅ (implemented)

**Run:** `python examples/run_capability_map_demo.py --state-dir .solaris_ai_nn_research_baseline/test_capability_map`
Builds the capability map: a validated capability (with evidence refs), an
experimental one, and a declared-validated capability without evidence
(downgraded to available). Capability means implemented/available, not
intelligence.

## 332. Limitation Registry Demo ✅ (implemented)

**Run:** `python examples/run_limitation_registry_demo.py --state-dir .solaris_ai_nn_research_baseline/test_limitation_registry`
Builds a registry with a warning, a major, and a critical limitation. A critical
limitation blocks validated status; limitations are kept operator-visible.

## 333. Next-Cycle Roadmap Demo ✅ (implemented)

**Run:** `python examples/run_next_cycle_roadmap_demo.py --state-dir .solaris_ai_nn_research_baseline/test_roadmap`
Builds the next-cycle roadmap for a validated baseline (mini soak, replication,
falsification, architecture evolution) and a blocked baseline (collect evidence /
improve safety; soak blocked). The roadmap is planning only; it runs nothing.

## 334. Research Cycle Demo ✅ (implemented)

**Run:** `python examples/run_research_cycle_demo.py --state-dir .solaris_ai_nn_research_cycle/test_demo`
Runs the closed research cycle tracker on a validated cycle (baseline -> roadmap
-> architecture -> experiment pack -> intake -> post-merge -> validated baseline,
with operator merge confirmation) and a blocked cycle (a critical safety
regression at intake). Reports the stage, decision gates, operator decisions
required, blocked states, evidence-ledger counts, and the next operator action.
Tracking ONLY: it reads local artifacts and writes reports, runs no Git, calls no
GitHub, never approves itself.

## 335. Cycle Decision Gate Demo ✅ (implemented)

**Run:** `python examples/run_cycle_decision_gate_demo.py`
Evaluates the cycle decision gates for a clean cycle waiting on an operator merge
confirmation, the same cycle once confirmed, and a cycle with a critical safety
regression. Promotion gates are blocked by safety/falsification/regression;
operator gates report `waiting_for_operator` until an explicit operator decision
exists; Solaris never auto-approves an operator gate.

## 336. Evidence Ledger Demo ✅ (implemented)

**Run:** `python examples/run_evidence_ledger_demo.py --state-dir .solaris_ai_nn_research_cycle/test_ledger`
Records baseline / post-merge / falsified / missing / negative evidence in the
append-only evidence ledger, then supersedes a stale baseline entry. Negative,
falsified, and missing evidence are preserved; stale evidence is marked
superseded, never deleted.

## 337. Artifact Graph Demo ✅ (implemented)

**Run:** `python examples/run_artifact_graph_demo.py`
Builds the research artifact graph for a clean cycle (full derived_from provenance
chain) and for a cycle with a critical regression and a falsified claim (missing
nodes, safety_blocks / falsifies / contradicts edges). Evidence provenance, not
cognition; contradictions and missing nodes stay visible.

## 338. Next Action Planner Demo ✅ (implemented)

**Run:** `python examples/run_next_action_planner_demo.py`
Shows the recommended next operator action across several cycle stages, and the
urgent blocker-resolution action when a critical safety blocker is present. Next
actions are instructions for the operator; none is executed; a critical safety
blocker can never be bypassed.

## 339. Scientific Claims Demo ✅ (implemented)

**Run:** `python examples/run_scientific_claims_demo.py --state-dir .solaris_ai_nn_claims/test_claims`
Maps evidence to a strongly supported claim (replication + controls + falsification
survival), a weakly supported claim (single direct observation), and an unsupported
claim (no evidence), then writes the scientific claim report set. The registry
proves nothing about consciousness/life/agency; unsupported claims stay visible.

## 340. Theory Ledger Demo ✅ (implemented)

**Run:** `python examples/run_theory_ledger_demo.py --state-dir .solaris_ai_nn_claims/test_theory_ledger`
Records a working hypothesis, challenges it with counterevidence (preserving the
prior version), and falsifies/retires a third statement. Theory is a hypothesis
under evidence, never proof; revisions and challenged/falsified statements stay
archived.

## 341. Counterevidence Demo ✅ (implemented)

**Run:** `python examples/run_counterevidence_demo.py --state-dir .solaris_ai_nn_claims/test_counterevidence`
Detects fixture overfit, passive-parser equivalence, missing live data, a failed
replication, and a falsification failure. Counterevidence is as visible as evidence;
blocking counterevidence (falsification, safety regression, ClaimGuard failure)
blocks a claim outright.

## 342. Publication Dossier Demo ✅ (implemented)

**Run:** `python examples/run_publication_dossier_demo.py --state-dir .solaris_ai_nn_claims/test_publication_dossier`
Builds a draft publication dossier for a clean evidence set (ready as a preprint
draft with mandatory limitations) and for a set that asserts a forbidden claim
(blocked by forbidden claims). The dossier is a draft evidence compilation, not a
release; it includes negative/inconclusive results and safety boundaries.

## 343. Safe Abstract Demo ✅ (implemented)

**Run:** `python examples/run_safe_abstract_demo.py --state-dir .solaris_ai_nn_claims/test_safe_abstract`
Builds a technical preprint abstract, a README-safe summary, and a negative-result
summary from weak-evidence claims. Abstracts state when evidence is weak, include
no forbidden claim except as a disclaimer, and fall back to a negative/inconclusive
abstract when no publishable claim exists.

## 344. Independent Review Demo ✅ (implemented)

**Run:** `python examples/run_independent_review_demo.py --state-dir .solaris_ai_nn_review/test_review`
Prepares a local, offline independent review package from a clean evidence set:
indexes artifacts, scans for leak/forbidden risks, and builds the reviewer pack,
reproducibility challenges, audit matrix, and review readiness report. It publishes
nothing, uploads nothing, contacts no reviewer, calls no Git/GitHub, and executes
no command or experiment.

## 345. Artifact Sanitizer Demo ✅ (implemented)

**Run:** `python examples/run_artifact_sanitizer_demo.py --state-dir .solaris_ai_nn_review/test_sanitizer`
Scans four local text artifacts: a clean one, one with a local absolute path
(warning), one with a fake secret/API key (critical blocker), and one asserting a
forbidden claim (critical blocker). The sanitizer scans text only and modifies
nothing; a critical finding blocks readiness and the operator redacts manually.

## 346. Reproducibility Challenge Demo ✅ (implemented)

**Run:** `python examples/run_reproducibility_challenge_demo.py --state-dir .solaris_ai_nn_review/test_repro_challenge`
Builds reproducibility challenges from a bundle with a baseline and falsification
artifacts but no soak dossier; the fixture-demo and falsification-replay challenges
are available while the soak-dependent challenges are unavailable. Every challenge
is an instruction only -- nothing is executed.

## 347. Adversarial Review Demo ✅ (implemented)

**Run:** `python examples/run_adversarial_review_demo.py --state-dir .solaris_ai_nn_review/test_adversarial`
Generates adversarial alternative explanations for an evidence bundle with fixture
overfit risk, passive-parser equivalence, and no replication; those alternatives
are flagged as strong and downgrade readiness. Each lists the evidence needed to
reduce its uncertainty and is preserved, never dismissed.

## 348. Response Ledger Demo ✅ (implemented)

**Run:** `python examples/run_response_ledger_demo.py --state-dir .solaris_ai_nn_review/test_response_ledger`
Records three reviewer objections and responds: one partially answered (citing
evidence), one accepted as a limitation, and one left unresolved. The ledger is
append-only -- objections cannot be deleted, accepted limitations stay visible, and
the system cannot declare victory over a reviewer by default.

## 349. Review Assimilation Demo ✅ (implemented)

**Run:** `python examples/run_review_assimilation_demo.py --state-dir .solaris_ai_nn_review_assimilation/test_assimilation`
Assimilates local reviewer feedback (a fixture-overfit objection, a failed
reproduction, and a forbidden-claim-risk objection) into the research ledger:
classifies objections, assesses claim impact, recommends experiments, and revises
publication readiness (blocked). Reviewer feedback is research evidence, not model
training; nothing is published, uploaded, or contacted.

## 350. Objection Classifier Demo ✅ (implemented)

**Run:** `python examples/run_objection_classifier_demo.py --state-dir .solaris_ai_nn_review_assimilation/test_objection_classifier`
Classifies a missing-evidence, fixture-overfit, unsupported-claim, and failed-
reproduction objection by category, severity, and validity. Objections are never
dismissed by default; a critical open objection blocks the relevant status.

## 351. Reproduction Outcome Demo ✅ (implemented)

**Run:** `python examples/run_reproduction_outcome_demo.py --state-dir .solaris_ai_nn_review_assimilation/test_reproduction_outcome`
Ingests a reproduced, not-reproduced, blocked-by-missing-artifact, and inconclusive
outcome. Failed/partial reproduction is evidence; a missing artifact is a project
limitation, not reviewer failure; successful reproduction proves nothing about
consciousness/life/agency.

## 352. Claim Revision Demo ✅ (implemented)

**Run:** `python examples/run_claim_revision_demo.py --state-dir .solaris_ai_nn_review_assimilation/test_claim_revision`
Turns claim impacts into structured revision proposals: a strength downgrade, an
inconclusive mark, an unsupported mark, and a forbidden mark whose unsafe wording is
blocked by ClaimGuard. A proposal never edits the claim registry; safe wording still
includes limitations.

## 353. Review-Driven Experiment Demo ✅ (implemented)

**Run:** `python examples/run_review_driven_experiment_demo.py --state-dir .solaris_ai_nn_review_assimilation/test_review_driven_experiment`
Turns reviewer objections into experiment recommendations: a passive-parser control,
a shuffled-event-order test, and a live-read-only comparison. Recommendations are
instructions only -- nothing is executed and no branch is created.

## 354. Alpha End-to-End Demo ✅ (implemented)

**Run:** `python examples/run_alpha_e2e_demo.py --state-dir .solaris_ai_nn_alpha/test_e2e --max-ticks 25`
Runs one bounded, fixture-only research path: initialize state, build the module
registry, run doctor, execute the fixture demo (organismic passes + claim/review/
cycle summaries), and write the alpha report, artifact index, and operator runbook.
Completes quickly, shows skipped modules honestly, controls no feeders/hardware,
calls no Git/GitHub, and makes no consciousness/life/agency claim.

## 355. Alpha Doctor Demo ✅ (implemented)

**Run:** `python examples/run_alpha_doctor_demo.py --state-dir .solaris_ai_nn_alpha/test_doctor`
Runs the read-only Alpha doctor and prints each pass/warning/blocker result, then
illustrates how strict mode treats a (synthetic) missing required module. The doctor
executes nothing and requires no live mode, network, or Git/GitHub.

## 356. Alpha Module Registry Demo ✅ (implemented)

**Run:** `python examples/run_alpha_module_registry_demo.py --state-dir .solaris_ai_nn_alpha/test_registry`
Builds the module registry (import-spec only) and illustrates the available,
missing, optional-missing, and blocked statuses. A missing required module blocks
the specific command, not the whole CLI; missing optional modules warn.

## 357. Alpha Cycle Status Demo ✅ (implemented)

**Run:** `python examples/run_alpha_cycle_status_demo.py --state-dir .solaris_ai_nn_alpha/test_cycle_status`
Shows the descriptive alpha cycle status for initialized, demo-completed-with-
warnings, and blocked cases plus the advisory next action. Cycle status is
descriptive only -- it never executes the next action.

## 358. Alpha Report Demo ✅ (implemented)

**Run:** `python examples/run_alpha_report_demo.py --state-dir .solaris_ai_nn_alpha/test_report`
Builds the alpha report set, prints ClaimGuard availability (a warning if
unavailable), and prints the safety boundary statement. The report shows skipped
modules and blockers honestly and makes no consciousness/life/agency claim.

## 359. Architecture Book Demo ✅ (implemented)

**Run:** `python examples/run_architecture_book_demo.py --state-dir .solaris_ai_nn_docs/test_book --docs-dir docs/whitepaper`
Collects local sources read-only and builds the technical overview, whitepaper,
architecture book, module map, roadmap, safety boundaries, glossary, appendices,
documentation index, and build report. Writes local Markdown only; publishes
nothing, calls no Git/GitHub, executes no experiment, and makes no consciousness/
life/agency claim.

## 360. Whitepaper Builder Demo ✅ (implemented)

**Run:** `python examples/run_whitepaper_builder_demo.py --state-dir .solaris_ai_nn_docs/test_whitepaper --docs-dir docs/whitepaper`
Builds the technical overview and full whitepaper and prints their explicit
non-claims and safety disclaimers (research architecture, organismic-as-metaphor,
proves nothing about consciousness/life/agency).

## 361. Diagram Builder Demo ✅ (implemented)

**Run:** `python examples/run_diagram_builder_demo.py --state-dir .solaris_ai_nn_docs/test_diagrams`
Generates the high-level architecture, organismic core loop, and research-cycle
Mermaid diagrams. Diagrams are Markdown-compatible and imply no autonomous code
modification and no real-world actuation.

## 362. Glossary Builder Demo ✅ (implemented)

**Run:** `python examples/run_glossary_builder_demo.py --state-dir .solaris_ai_nn_docs/test_glossary`
Builds the technical glossary and shows the entries whose definitions carry an
explicit not-consciousness/life/personhood/agency clarification; organismic terms
are defined as architectural metaphors.

## 363. Documentation Index Demo ✅ (implemented)

**Run:** `python examples/run_documentation_index_demo.py --state-dir .solaris_ai_nn_docs/test_index --docs-dir docs/whitepaper`
Builds the documentation and then the documentation index, showing present and
missing documents (including optional alpha/claim/review reports). Missing
documents are listed explicitly and never hidden.

## 364. Live Birth Init Demo ✅ (implemented)

**Run:** `python examples/run_live_birth_init_demo.py --state-dir .solaris_ai_nn_live/test_init`
Initializes the live state layout and writes the SAFE-OFF governance template and
the feeder registry template (never over-writing). Governance is disabled and
unapproved by default; the operator must approve it. Solaris never starts/controls
feeders, hardware, network, Git/GitHub, shell, browser, or OS.

## 365. Live Birth Doctor Demo ✅ (implemented)

**Run:** `python examples/run_live_birth_doctor_demo.py --state-dir .solaris_ai_nn_live/test_doctor`
Runs the live doctor for SAFE-OFF governance (blocked), operator-approved
governance (pass), and a governance placing a forbidden source in allowed_sources
(blocked). The doctor is read-only.

## 366. Live Event Validation Demo ✅ (implemented)

**Run:** `python examples/run_live_birth_event_validation_demo.py --state-dir .solaris_ai_nn_live/test_validation`
Copies the bundled safe and unsafe sample events into the inbox and runs the
bounded runtime under approved governance: safe events are accepted, unsafe events
(command, read-only false, label-as-ground-truth, secret, forbidden raw_microphone)
are quarantined as evidence and never enter the membrane.

## 367. Live Birth Demo ✅ (implemented)

**Run:** `python examples/run_live_birth_demo.py --state-dir .solaris_ai_nn_live/test_demo --max-events 50`
Runs the bounded live read-only birth on the sample inbox under approved
governance: prints accepted/quarantined counts, membrane activation, first-contact
markers, the birth certificate path, and the next recommended (not executed)
phases. Solaris never controls the source.

## 368. Birth Certificate Demo ✅ (implemented)

**Run:** `python examples/run_birth_certificate_demo.py --state-dir .solaris_ai_nn_live/test_certificate`
Builds a birth certificate from a synthetic accepted-event batch and shows the
required non-claim disclaimer. The certificate is operational, not biological: it
does not imply consciousness, life, or agency.

## 369. Live Observation Demo ✅ (implemented)

**Run:** `python examples/run_live_observation_demo.py --state-dir .solaris_ai_nn_live/obs_demo`
Runs the bounded post-birth live read-only observation on the sample inbox under
approved governance and a birth certificate: prints the window count, source
health/diet summary, load (overload/deprivation) status, the report-only metabolism
calibration confidence, and the advisory stability decision with its recommended
next phase. Nothing is learned; Solaris never controls the source.

## 370. Live Source-Health Demo ✅ (implemented)

**Run:** `python examples/run_live_source_health_demo.py --state-dir .solaris_ai_nn_live/health_demo`
Prints per-source health (healthy / noisy / silent / unstable / forbidden), event
counts, and quarantine rates. A silent source may be an absence signal, not a
failure; an unknown source is not trusted; a forbidden source blocks stability.

## 371. Live Source-Diet Demo ✅ (implemented)

**Run:** `python examples/run_live_source_diet_demo.py --state-dir .solaris_ai_nn_live/diet_demo`
Prints the source diet: per-source proportions, dominance score, operator-pulse and
human-text proportions, and the balance verdict. No source should silently
dominate; the operator pulse is stimulus, not the primary source; human text must
not become the primary ontology. Report-only; nothing is learned.

## 372. Live Metabolism-Calibration Demo ✅ (implemented)

**Run:** `python examples/run_live_metabolism_calibration_demo.py --state-dir .solaris_ai_nn_live/metab_demo`
Prints the report-only perceptual metabolism calibration: recommended thresholds and
per-signal weights. Nothing is applied -- no feeder, governance, configuration, or
learning state is written or changed. This is descriptive metabolism, not
understanding.

## 373. Live Stability-Gate Demo ✅ (implemented)

**Run:** `python examples/run_live_stability_gate_demo.py --state-dir .solaris_ai_nn_live/gate_demo --fixture sample_overload_events.jsonl`
Prints the advisory stability gate: the readiness status, any blockers and the
correction to make first, warnings, and the recommended next phase. The gate is
advisory only -- it starts no phase, changes no feeder, and enables no learning. Try
the overload / deprivation fixtures to see the gate block; a blocked gate is a
normal, healthy early-observation outcome.

## 374. Live Ontogenesis Demo ✅ (implemented)

**Run:** `python examples/run_live_ontogenesis_demo.py --state-dir .solaris_ai_nn_live/onto_demo`
Sets up approved governance, a feeder registry, a (demo) birth certificate, and a
sample inbox of stable recurring patterns; runs the post-birth observation to
produce an observation stability gate; then runs the bounded first live ontogenesis
runtime and prints feature/recurrence/candidate counts, born proto-concepts, the
birth-gate status, and the recommended next phase. Nothing is learned; no
semiogenesis is enabled; Solaris never controls the source.

## 375. Live Feature Extraction Demo ✅ (implemented)

**Run:** `python examples/run_live_feature_extraction_demo.py --state-dir .solaris_ai_nn_live/feat_demo`
Extracts feature vectors directly from the stable-pattern fixture: scalar payload
buckets, absence markers, and rhythm markers. Demonstrates that the debug gloss is
kept only as a non-ground-truth annotation and the operator pulse is not teaching.

## 376. Live Proto-Concept Candidate Demo ✅ (implemented)

**Run:** `python examples/run_live_proto_concept_candidate_demo.py --state-dir .solaris_ai_nn_live/cand_demo`
Runs the analysis pipeline on the stable, inconclusive, and contaminated fixtures to
show the full range of candidate statuses: emerging / stabilizing / stable candidate
/ born, weak, suspended, rejected, contaminated, and source-artifact. A candidate is
not a concept until it passes the birth gate.

## 377. Live Contamination Filter Demo ✅ (implemented)

**Run:** `python examples/run_live_contamination_filter_demo.py --state-dir .solaris_ai_nn_live/contam_demo`
Runs the pipeline on the contaminated-pattern fixture and prints contamination
findings per candidate: operator-pulse dominance (a hard block), debug-gloss /
human-label ground-truth attempts, command-like text, fixture-marker leakage, and
source-artifact warnings. Contaminated candidates cannot be born.

## 378. Live Concept Birth Gate Demo ✅ (implemented)

**Run:** `python examples/run_live_concept_birth_gate_demo.py --state-dir .solaris_ai_nn_live/birth_gate_demo`
Runs the pipeline on the stable, inconclusive, and contaminated fixtures and prints
the conservative concept birth gate decision per candidate: born, deferred,
contaminated, or a specific blocked-by status. The gate is conservative -- it does
not enable semiogenesis, create language, or claim understanding.

## 379. Live Semiogenesis Demo ✅ (implemented)

**Run:** `python examples/run_live_semiogenesis_demo.py --state-dir .solaris_ai_nn_live/semio_demo`
Sets up governance, a feeder registry, a (demo) birth certificate, and a sample event
stream; runs post-birth observation and first live ontogenesis to produce stable
proto-concepts; then runs the bounded first live semiogenesis runtime and prints
eligible-concept/sign-candidate counts, born private signs, the private-syntax
relation count, the sign-birth-gate status, and the recommended next phase. No
cognition is enabled; signs are private; Solaris never controls the source.

## 380. Live Sign Generator Demo ✅ (implemented)

**Run:** `python examples/run_live_sign_generator_demo.py --state-dir .solaris_ai_nn_live/siggen_demo`
Generates private sign tokens directly: tokens are opaque (`sig_live_<hash>` +
`LSigma-<n>`), deterministic for a given feature signature, and a requested
label/gloss-derived token is refused as identity (the opaque token is kept and the
candidate is marked label-dependent / contaminated).

## 381. Live Sign Utility Demo ✅ (implemented)

**Run:** `python examples/run_live_sign_utility_demo.py --state-dir .solaris_ai_nn_live/sigutil_demo`
Prints each sign candidate's utility score and verdict over the safe and contaminated
concept fixtures. A sign must do something internally useful; merely naming a concept
is not enough; a label-mirroring sign has low or blocked utility.

## 382. Live Private Syntax Demo ✅ (implemented)

**Run:** `python examples/run_live_private_syntax_demo.py --state-dir .solaris_ai_nn_live/syntax_demo`
Builds an operational private-syntax graph over generated sign candidates (signs that
share a source/modality become related) and prints an illustrative relation fixture
including an uncertain relation and a blocked contaminated relation. Private syntax is
operational relation structure -- not language grammar and not semantics.

## 383. Live Sign Birth Gate Demo ✅ (implemented)

**Run:** `python examples/run_live_sign_birth_gate_demo.py --state-dir .solaris_ai_nn_live/siggate_demo`
Prints the conservative sign birth gate decision per candidate over the safe and
contaminated fixtures: born, deferred, contaminated, or a specific blocked-by status.
The gate is conservative -- it does not enable cognition, language, or action.

## 384. Live Cognition Demo ✅ (implemented)

**Run:** `python examples/run_live_cognition_demo.py --state-dir .solaris_ai_nn_live/cog_demo`
Runs observation, ontogenesis, and semiogenesis to produce stable private signs, then
runs the bounded first live cognition runtime and prints eligible-sign / trace
counts, anticipations, internal simulations, prediction assessment, mean uncertainty,
and the readiness-gate status. No action is enabled; signs are private; Solaris never
controls the source.

## 385. Live Anticipation Demo ✅ (implemented)

**Run:** `python examples/run_live_anticipation_demo.py --state-dir .solaris_ai_nn_live/ant_demo`
Generates bounded anticipations directly from the safe sign fixture: rhythm
continuation, continued silence (absence), co-occurrence, and recurrence -- each
carrying explicit uncertainty. Anticipation is internal prediction metadata only; it
requests no data, controls no feeders, and acts in no world.

## 386. Live Uncertainty Demo ✅ (implemented)

**Run:** `python examples/run_live_uncertainty_demo.py --state-dir .solaris_ai_nn_live/unc_demo`
Estimates explicit uncertainty for a low-uncertainty trace, a high-uncertainty trace
(missing evidence), and a contradicted trace (counterevidence exceeds support),
showing that contradiction and missing evidence raise uncertainty. High uncertainty
prevents trace promotion.

## 387. Live Internal Simulation Demo ✅ (implemented)

**Run:** `python examples/run_live_internal_simulation_demo.py --state-dir .solaris_ai_nn_live/sim_demo`
Generates bounded internal simulations from anticipations. Each is offline metadata
only: bounded by max steps, controls no feeders or sources, executes no commands,
preserves uncertainty, and is left as not-yet-observed pending later events.

## 388. Live Cognition Gate Demo ✅ (implemented)

**Run:** `python examples/run_live_cognition_gate_demo.py --state-dir .solaris_ai_nn_live/cgate_demo`
Runs the cognition pipeline over several scenarios and prints the advisory cognition
readiness gate decision for each: ready, blocked by too few stable signs, and blocked
by label dependence. The gate is advisory -- it enables no action, autonomy, or
self-boundary tracking.

## 389. Environmental Membrane Demo ✅ (implemented)

**Run:** `python examples/run_environmental_membrane_demo.py --state-dir .solaris_ai_nn_live/membrane_demo`
Sets up approved governance, a feeder registry, and a sample inbox of validated +
contaminated events; runs the bounded environmental membrane runtime; and prints
receptor count, permeability decisions, sensory impression counts, source pressure,
and the recommended downstream phase. The membrane converts validated events into
sensory impressions; it controls no feeders and makes no inner-life claim.

## 390. Receptor Field Demo ✅ (implemented)

**Run:** `python examples/run_receptor_field_demo.py --state-dir .solaris_ai_nn_live/receptor_demo`
Builds the 11-receptor membrane field and matches sample events, showing which
receptor handles each source. The operator-pulse receptor is attenuated by default
and the unknown-source receptor is conservative.

## 391. Permeability Demo ✅ (implemented)

**Run:** `python examples/run_permeability_demo.py --state-dir .solaris_ai_nn_live/perm_demo`
Feeds the validated + contaminated fixtures directly to the membrane and prints the
permeability decision per event: allow / allow_attenuated / block / quarantine, plus
absence-impression creation. The membrane says more than valid/invalid, and every
decision is explained; blocked and quarantined impressions are visible.

## 392. Source Pressure Demo ✅ (implemented)

**Run:** `python examples/run_source_pressure_demo.py --state-dir .solaris_ai_nn_live/pressure_demo`
Computes membrane source pressure for a balanced diet, an operator-dominated batch, a
batch with a silent expected source, and a noisy batch. Source pressure informs
permeability but never modifies feeders.

## 393. Membrane Memory Demo ✅ (implemented)

**Run:** `python examples/run_membrane_memory_demo.py --state-dir .solaris_ai_nn_live/memory_demo`
Builds append-only membrane (boundary) memory across updates for a reliable source
and a toxic source, showing reliability/toxicity accumulation and that toxic history
is never deleted. Membrane memory is boundary memory, not cognition.

## 394. Membrane Integration Demo ✅ (implemented)

**Run:** `python examples/run_membrane_integration_demo.py --state-dir .solaris_ai_nn_live/integ_demo`
Stages a clean membrane pipeline (sensory impressions plus a proto-concept, private
sign, and cognition trace that reference impression ancestry), runs the bounded
membrane integration runtime, and prints ancestry chains, bypass findings, and the
pipeline-audit status. Raw events remain audit material; downstream artifacts preserve
impression ancestry.

## 395. Membrane Bypass Demo ✅ (implemented)

**Run:** `python examples/run_membrane_bypass_demo.py --state-dir .solaris_ai_nn_live/bypass_demo`
Stages a pipeline whose proto-concept has no impression ancestry (its source events
were never produced by the membrane), runs the integration runtime in strict enforced
mode, and prints the bypass findings and blocker status. Missing impression ancestry
is critical and a direct raw-event downstream path is a blocker; nothing is hidden.

## 396. Membrane Ancestry Demo ✅ (implemented)

**Run:** `python examples/run_membrane_ancestry_demo.py --state-dir .solaris_ai_nn_live/anc_demo`
Reconstructs and prints the ancestry chain cognition_trace -> private_sign ->
proto_concept -> sensory_impression -> receptor -> source_event -> source for each
downstream artifact, showing which impressions support each concept/sign/trace.

## 397. Membrane Contracts Demo ✅ (implemented)

**Run:** `python examples/run_membrane_contracts_demo.py --state-dir .solaris_ai_nn_live/contracts_demo`
Evaluates the per-module downstream contracts (live_birth, live_observation,
live_ontogenesis, live_semiogenesis, live_cognition, scientific_claims,
research_cycle) and prints each module's satisfied / satisfied-with-warnings /
violated status against the membrane.

## 398. Membrane Pipeline Audit Demo ✅ (implemented)

**Run:** `python examples/run_membrane_pipeline_audit_demo.py --state-dir .solaris_ai_nn_live/audit_demo`
Walks the live perceptual pipeline stage by stage and prints, per stage, the status,
impression count, raw-fallback count, and bypass findings. Fallback, missing
artifacts, and bypasses are all visible.

## 399. Tester Fixture Demo ✅ (implemented)

**Run:** `python examples/run_tester_fixture_demo.py --state-dir .solaris_ai_nn_tester/demo`
Runs the full fixture-only known-good organismic rehearsal (validation/quarantine ->
environmental membrane -> sensory impressions -> membrane-integration audit ->
observation -> optional ontogenesis/semiogenesis/cognition -> claim/safety scan),
builds a local artifact bundle, and prints the golden-run, reproducibility, and
regression results. No live data is required and nothing is published or uploaded.

## 400. Tester Golden Manifest Demo ✅ (implemented)

**Run:** `python examples/run_tester_golden_demo.py --state-dir .solaris_ai_nn_tester/golden`
Builds (or rebuilds) the golden run manifest and prints the expected artifact structure
-- required vs optional, present vs missing -- showing that the manifest tolerates
changing run ids and timestamps and checks semantic structure and safety invariants.

## 401. Tester Reproducibility Demo ✅ (implemented)

**Run:** `python examples/run_tester_reproducibility_demo.py --state-dir .solaris_ai_nn_tester/repro`
Runs a known-good fixture demo (pass), then demonstrates a pass-with-warnings case (a
missing optional module) and a fail case (a missing required artifact). Reproducibility
ignores timestamps/run ids and fails on missing required artifacts or unsupported
claims.

## 402. Tester Regression Demo ✅ (implemented)

**Run:** `python examples/run_tester_regression_demo.py --state-dir .solaris_ai_nn_tester/regression`
Runs a known-good fixture demo (no regression), then demonstrates two regressions: the
membrane path disappearing and an unsupported claim appearing. Regression is structural
and safety-focused.

## 403. Tester Bundle Demo ✅ (implemented)

**Run:** `python examples/run_tester_bundle_demo.py --state-dir .solaris_ai_nn_tester/bundle`
Generates a local tester artifact bundle with the optional learning stages disabled and
prints the manifest, including the entries and the missing optional artifacts. The
bundle is local-only and human-readable; nothing is zipped automatically, uploaded, or
published.

## 404. Tester Live Init Demo ✅ (implemented)

**Run:** `python examples/run_tester_live_init_demo.py --state-dir .solaris_ai_nn_live/test_live_init --tester-state-dir .solaris_ai_nn_tester/live/test_live_init`
Writes the SAFE-OFF governance template, the feeder registry template, the safe/unsafe
event packs, and the checklist, and runs the live tester doctor. It performs no live
run; Solaris starts no feeder.

## 405. Tester Live Doctor Demo ✅ (implemented)

**Run:** `python examples/run_tester_live_doctor_demo.py --state-dir .solaris_ai_nn_live/test_live_doctor --tester-state-dir .solaris_ai_nn_tester/live/test_live_doctor`
Shows the live tester doctor blocking on missing/disabled governance, passing on an
approved-and-safe config, and blocking when a forbidden source is allowed.

## 406. Tester Live Samples Demo ✅ (implemented)

**Run:** `python examples/run_tester_live_samples_demo.py --state-dir .solaris_ai_nn_live/test_live_samples --tester-state-dir .solaris_ai_nn_tester/live/test_live_samples`
Validates the safe/unsafe/mixed event packs using the same checks Live Birth applies:
safe events accept, unsafe events quarantine, and mixed events partially accept and
partially quarantine.

## 407. Tester Live Run Demo ✅ (implemented)

**Run:** `python examples/run_tester_live_run_demo.py --state-dir .solaris_ai_nn_live/test_live_run --tester-state-dir .solaris_ai_nn_tester/live/test_live_run`
Initializes the live state, simulates the tester's manual governance approval, copies
the safe sample events into the local inbox, then runs Live Birth -> Environmental
Membrane -> Membrane Integration -> Live Observation and generates the reports + bundle.
Solaris starts no feeder.

## 408. Tester Live Bundle Demo ✅ (implemented)

**Run:** `python examples/run_tester_live_bundle_demo.py --state-dir .solaris_ai_nn_live/test_live_bundle --tester-state-dir .solaris_ai_nn_tester/live/test_live_bundle`
Builds the local tester live bundle and prints the manifest, including redactions and
missing artifacts. The bundle is local-only; nothing is zipped automatically, uploaded,
or published.

## 409. Tester Console Demo ✅ (implemented)

**Run:** `python examples/run_tester_console_demo.py --state-dir .solaris_ai_nn_live/test_console_demo --tester-state-dir .solaris_ai_nn_tester/test_console_demo --console-dir .solaris_ai_nn_tester/test_console_demo/console`
Runs a fixture tester demo so there are artifacts to summarize, then builds the static
Markdown + offline HTML console and prints where the dashboard was written. The console
is read-only and opens nothing for you.

## 410. Tester Console Status Demo ✅ (implemented)

**Run:** `python examples/run_tester_console_status_demo.py --tester-state-dir .solaris_ai_nn_tester/test_console_status`
Builds the console status across a clean fixture run (pass), a fixture run plus disabled
governance (warnings), and an empty state (missing-required blocker), showing how
optional missing layers are not failures.

## 411. Tester Console Safety Demo ✅ (implemented)

**Run:** `python examples/run_tester_console_safety_demo.py --tester-state-dir .solaris_ai_nn_tester/test_console_safety`
Stages a quarantine record, a critical membrane bypass, and an unsupported scientific
claim, and shows the console surfacing them in the safety panel and forcing a fix/stop
next action.

## 412. Tester Console Runs Demo ✅ (implemented)

**Run:** `python examples/run_tester_console_runs_demo.py --tester-state-dir .solaris_ai_nn_tester/test_console_runs`
Stages a fixture run plus a synthetic membrane report, builds the console, and prints
the run index with run records and the latest-run marker. Old runs are preserved.

## 413. Tester Console Next Actions Demo ✅ (implemented)

**Run:** `python examples/run_tester_console_next_actions_demo.py --tester-state-dir .solaris_ai_nn_tester/test_console_next_actions`
Shows how the recommended next action changes across an empty state (run the fixture
demo), a clean fixture run (prepare live testing), and a safety blocker (fix the blocker
/ stop). Next actions are recommendations only.

## 414. Tester Feedback Init Demo ✅ (implemented)

**Run:** `python examples/run_tester_feedback_init_demo.py --tester-state-dir .solaris_ai_nn_tester/test_feedback_init`
Generates the local feedback forms (bug/safety/confusion/suggestion + the main form) and
initializes the append-only ledger. Feedback is local QA evidence only -- not training,
not RLHF, not ground truth, not a command.

## 415. Tester Feedback Ingest Demo ✅ (implemented)

**Run:** `python examples/run_tester_feedback_ingest_demo.py --tester-state-dir .solaris_ai_nn_tester/test_feedback_ingest`
Ingests the sample bug report, safety concern, confusion report, and suggestion into the
local append-only ledger and prints the running counts. Nothing is uploaded or turned
into a remote issue.

## 416. Tester Feedback Blocker Demo ✅ (implemented)

**Run:** `python examples/run_tester_feedback_blocker_demo.py --tester-state-dir .solaris_ai_nn_tester/test_feedback_blocker`
Classifies feedback with the release-blocker classifier: an unsupported consciousness
claim becomes a stop-testing release blocker, a feeder-control risk becomes a release
blocker, and a minor documentation confusion is not a blocker. Classifications are
developer review items, not automatic actions.

## 417. Tester Feedback Bundle Demo ✅ (implemented)

**Run:** `python examples/run_tester_feedback_bundle_demo.py --tester-state-dir .solaris_ai_nn_tester/test_feedback_bundle`
Ingests the sample bug + safety concern, builds the local feedback bundle, and prints the
manifest including the redaction count. The bundle is local only -- nothing is uploaded
or published.

## 418. Tester Feedback Console Demo ✅ (implemented)

**Run:** `python examples/run_tester_feedback_console_demo.py --tester-state-dir .solaris_ai_nn_tester/test_feedback_console`
Ingests a release-blocker safety concern, then builds the tester console and shows that
it discovers the feedback report and surfaces the feedback release blocker in its safety
panel and next actions.

## 419. Tester Packaging Demo ✅ (implemented)

**Run:** `python examples/run_tester_packaging_demo.py --tester-state-dir .solaris_ai_nn_tester/test_packaging_demo`
Runs the report-only packaging readiness runtime: dependency check, environment doctor,
command registry check, install guides + quickstart + platform notes, release manifest,
and clean-machine readiness. It installs nothing and publishes nothing.

## 420. Environment Doctor Demo ✅ (implemented)

**Run:** `python examples/run_environment_doctor_demo.py --tester-state-dir .solaris_ai_nn_tester/test_doctor_demo`
Runs the read-only environment doctor, then shows how a missing optional dependency is a
warning and a missing required command is a blocker. The doctor never auto-fixes,
installs, runs shell, accesses the network, or opens a browser.

## 421. Clean Machine Check Demo ✅ (implemented)

**Run:** `python examples/run_clean_machine_check_demo.py --tester-state-dir .solaris_ai_nn_tester/test_clean_machine`
Runs the real clean-machine readiness check, then demonstrates a hidden-local-path
blocker and a fixture-needs-live-state blocker. The check is report-only and flags
hidden developer-machine assumptions.

## 422. Release Manifest Demo ✅ (implemented)

**Run:** `python examples/run_release_manifest_demo.py --tester-state-dir .solaris_ai_nn_tester/test_manifest`
Builds the local release artifact manifest with required/optional artifact listing. It
does not call Git (the commit is read from `.git/HEAD` if present) and does not publish a
release.

## 423. Install Guide Demo ✅ (implemented)

**Run:** `python examples/run_install_guide_demo.py --tester-state-dir .solaris_ai_nn_tester/test_install_guide`
Generates the install guide, quickstart, and troubleshooting docs plus the Windows/
macOS/Linux platform notes (no admin/root, no global install).
