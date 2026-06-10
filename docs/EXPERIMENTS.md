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
