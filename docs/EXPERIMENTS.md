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
