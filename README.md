# Solaris-AI-NN

**A low-compute, continuous-learning neural laboratory for [`fopearcano/solaris-ai`](https://github.com/fopearcano/solaris-ai).**

Solaris-AI-NN is the experimental neural substrate for Solaris_Ai. It explores
how the existing Solaris_Ai architecture — the conceptual spine
`Stimulus → Push → Desire → Action` plus the `MeaningEvent`, `MapUpdate`,
`LogosTension`, and `Reaction` side streams — can gain **adaptive, neural-like
behaviour** without becoming a conventional large deep-learning chatbot.

This is a *continuous cognition prototype*. It is **consciousness-inspired**, not
conscious. Every philosophical idea here maps to a concrete software object, a
metric, or an experiment. There are no mystical claims in this repository.

---

## What Solaris-AI-NN *is*

- A **reservoir-computing** substrate (Echo State Network) that gives Solaris_Ai
  a cheap, continuous "nervous" state shaped by its whole event history.
- An **online-learning** layer: a single linear readout trained one event at a
  time, so behaviour adapts continuously rather than in expensive batch retrains.
- A set of **plasticity mechanisms** — habit reinforcement, synthesis through
  subtraction (pruning), drift monitoring — layered on top of the substrate.
- A **long-running, event-driven** experiment loop with full telemetry.
- **Self-contained and dependency-free**: pure Python standard library.

## What Solaris-AI-NN *is not*

- It is **not** a large language model, transformer, or chatbot.
- It is **not** a claim that any software here is conscious or sentient.
- It does **not** import, vendor, mutate, or overwrite `fopearcano/solaris-ai`.
  That repo is the canonical *conceptual* reference; this one is the *neural
  laboratory* around it.
- It is **not** a heavy ML framework. There is no PyTorch / TensorFlow / JAX /
  transformers / LangChain / agent framework, and no database or web service.

## How it relates to `fopearcano/solaris-ai`

Solaris_Ai is the canonical, executable conceptual system (a modular pub/sub
network with AION/Impulse, Logos, Inner MAP, Habit, Synthesis, and more).
Solaris-AI-NN **mirrors its signal vocabulary** (see `signals/canonical.py`) and
builds **neural/learning substrates** that can consume and emit compatible
events — without duplicating the reference modules. The precise correspondence
is documented in [`docs/SOLARIS_REFERENCE_MAP.md`](docs/SOLARIS_REFERENCE_MAP.md)
and encoded in `solaris_ai_nn.bridges.solaris_reference`.

## Why reservoir computing instead of large deep learning?

A reservoir (a fixed, random recurrent network with only a trained linear
readout) is the right *first* substrate because it is:

- **low-compute** — no backpropagation through time; one cheap matrix step and
  one linear update per event;
- **continuous** — its state is a fading echo of the entire input history, which
  matches Solaris_Ai's continuous, heartbeat-driven cognition;
- **online-trainable** — the readout learns event-by-event, testing the project's
  central bet: *long-running weak adaptation beats expensive one-shot
  intelligence*;
- **transparent** — every weight and state value can be printed and inspected;
  no opaque billion-parameter black box.

Transformers are *not* excluded forever — they are simply the wrong starting
point for a system whose thesis is continuous, low-compute, lifelong adaptation.
See [`docs/RESEARCH_NOTES.md`](docs/RESEARCH_NOTES.md).

## Why continuous / event-driven, and why low compute + long runtime?

Solaris_Ai never stops: AION/Impulse emits a heartbeat and, in silence,
synthesises an *absence* stimulus ("I exist!"). Solaris-AI-NN preserves this. The
interesting behaviour is not a single forward pass but **what the substrate
becomes after running for a long time** under a stream of events. Keeping each
step cheap is what makes very long runs (soak tests, see the roadmap) feasible
on a plain CPU.

## A note on NumPy

The core layers (signals, the list-based ESN, readout, runtime, plasticity)
deliberately use **only the Python standard library** — the linear algebra lives
in `solaris_ai_nn/utils/math.py` (including a power-iteration spectral-radius
estimator). **NumPy joined in Phase 6 for the substrate laboratory**
(`substrates/`): the liquid-state and spiking substrates are dense
membrane/spike vector loops, and substrate state persists as `.npz` — exactly
the workload NumPy exists for, and the place the roadmap always reserved for
it. The original stdlib code paths are unchanged.

---

## Install

Requires **Python 3.11+**. One runtime dependency: NumPy.

```bash
# From a checkout — no install needed to run the example or tests:
python examples/run_minimal_continuous_esn.py

# Or install (editable) with the test extra:
pip install -e ".[test]"
```

## Run the tests

```bash
python -m pytest
```

(`pyproject.toml` sets `pythonpath = ["src"]`, so tests run without installing.)

## Run the minimal experiment

```bash
python examples/run_minimal_continuous_esn.py            # default 1500 steps
python examples/run_minimal_continuous_esn.py 3000       # custom step count

# Or, if installed:
solaris-nn-demo
```

You should see the loop start near chance and climb toward ~95% accuracy on a
tiny stimulus→action world, habit weights strengthening on rewarded pathways,
and synthesis subtracting weak readout weights — all on CPU, in well under a
second.

Example output (abridged):

```
early accuracy (first 20% of graded events): ~55%
late  accuracy (last 20% of graded events):  ~95%
habit pathways learned: 9 (strong: 9)
synthesis subtracted pathways: 62
```

## Run the bridge, soak, and restart experiments

The neural bridge consumes Solaris-style signals; the continuity machinery lets a
run checkpoint, persist, and resume across restarts (all bounded by default).

```bash
# Solaris-compatible signal bridge: keeps evolving through silence (absence stimuli)
python examples/run_absence_stimulus_bridge.py

# Bounded soak run: checkpoints + continuity log under a per-brain state dir
python examples/run_soak_continuity.py
python examples/run_soak_continuity.py --steps 500 --state-dir .solaris_ai_nn_state/dev_soak

# Restart recovery: run, persist, restart, and continue from saved state
python examples/run_restart_demo.py
python examples/run_restart_demo.py --state-dir .solaris_ai_nn_state/restart_demo

# Simulate a crash: the restart then detects an ungraceful death + brain-death gap
python examples/run_restart_demo.py --simulate-crash

# Inner MAP: observe the substrate's evolving self-model; persists inner_map.json
python examples/run_inner_map_evolution.py
python examples/run_inner_map_evolution.py --steps 300 --state-dir .solaris_ai_nn_state/inner_map_demo

# Controlled plasticity: propose-only dry run (applies nothing), and a real run
python examples/run_plasticity_dry_run.py
python examples/run_plasticity_adaptation.py --enable-plasticity --steps 500
python examples/run_plasticity_adaptation.py --rollback-last   # undo the last applied step

# Substrate laboratory: compare ESN / liquid-state / spiking on the same trace,
# and test that spike-based substrates stay alive through silence
python examples/run_substrate_comparison.py --steps 300
python examples/run_spiking_silence.py --steps 300

# Solaris_Ai sidecar integration (works WITHOUT solaris-ai installed):
python examples/run_fake_solaris_integration.py          # fake Conscience/Bus demo
python examples/run_solaris_sidecar_observation.py       # bounded observation experiment
python examples/run_real_solaris_integration_if_available.py  # see note below

# Embodiment: a simulated body in a bounded GridWorld (simulation-only actions)
python examples/run_sensorimotor_gridworld.py --steps 300
python examples/run_embodied_absence.py --steps 300
python examples/run_reward_danger_adaptation.py --steps 300
```

The **embodiment sandbox** (`embodiment/`) closes the sensorimotor loop: sensors
emit canonical Stimuli, the bridge suggests actions, a safety layer admits only
the declared simulated action space (no network/OS/browser/robotics — ever),
effectors act inside the GridWorld, and consequences return as Reactions the
substrate learns from. Energy is a simulated need (movement costs, rest
restores, exhaustion blocks). Action authority is **simulation-only**.

The **sidecar integration** (`integration/`) attaches Solaris-AI-NN beside a
Solaris_Ai-like runtime as an *optional, observe-first* adaptive substrate: it
mirrors bus signals, learns from Reactions, and emits clearly-marked
**suggestions** (`committed=False`, always) — action authority never leaves
Solaris_Ai. The real-integration example only does anything if
`fopearcano/solaris-ai` is importable (e.g. `pip install -e /path/to/solaris-ai`);
otherwise it prints instructions and exits 0. Nothing in this repo requires the
real package — all tests and examples run against a shape-compatible fake.

The **substrate laboratory** (`substrates/`) makes the nervous layer selectable:
the same bridge runs on the ESN baseline, a Liquid-State-inspired substrate, or
a binary spiking recurrent substrate (`--substrates esn,liquid_state,spiking_recurrent`).
All consume the same encoded Solaris signals; only the readout learns. Substrate
switching is explicit-only, checkpointed, and rollbackable — never automatic.

**Controlled plasticity** (`plasticity/`, off by default) lets the substrate tune
its own *runtime parameters* — learning rate, habit weights, pruning threshold,
exploration — based on telemetry and the Inner MAP. Every change is **proposed,
safety-validated, logged (`plasticity_audit.jsonl`), and rollbackable**. It never
edits source code, never runs unbounded, and never commits actions autonomously.

The **Inner MAP** (`inner_map/`) is a read-only, persisted self-model: it observes
the reservoir, readout tendencies, habits, synthesis/pruning, memory, continuity,
boundaries, and drift, and can export a self-state graph (DOT/Mermaid). It does
not make the system conscious — it is structured self-*observation*.

Runtime state (manifest, checkpoint, telemetry, continuity log, replayable trace)
is written under `state_dir` as plain JSON/JSONL — fully inspectable, no database,
and git-ignored. A continuous (unbounded) run requires an explicit `--continuous`
flag and must be stopped manually.

---

## Repository layout

```
src/solaris_ai_nn/
  signals/      canonical signal vocabulary, event encoder, adapters
  reservoir/    ESN substrate, linear readout, online (NLMS) learning, LogosModulator
  plasticity/   habit reinforcement, synthesis-through-subtraction, drift
  memory/       chronological trace (JSONL), state snapshots, structural consolidation
  runtime/      adaptive loop, telemetry, persistence, lifecycle, continuous runner, replay
  bridges/      SolarisNeuralBridge + seam to the conceptual Solaris_Ai reference
  inner_map/    self-model (model, observer, boundaries, state graph, serialization)
  plasticity/   habit, synthesis + controlled self-mod (engine, policy, safety, rollback, audit)
  substrates/   substrate lab: ESN wrapper, liquid-state, spiking, registry, switching (NumPy)
  integration/  optional Solaris_Ai sidecar: probe, bus connector, mirror, suggestions
  embodiment/   simulated body + GridWorld: sensors, effectors, energy, safety, runner
  experiments/  minimal ESN, absence bridge, soak, restart, inner map, plasticity,
                substrates, sidecar, sensorimotor/absence/reward-danger embodiment
  utils/        pure-stdlib math, logging
tests/          pytest suite
examples/       runnable scripts
docs/           ARCHITECTURE, SOLARIS_REFERENCE_MAP, ROADMAP, EXPERIMENTS, RESEARCH_NOTES
```

## Current limitations

- One small experiment only (Phase 0). The world is tiny and synthetic.
- The readout is linear and the reservoir is fixed (by design). Capacity is
  intentionally small.
- The signal bridge to a live Solaris_Ai runtime is a dict-level stub
  (Phase 1).
- Memory consolidation and Inner-MAP coupling are stubs (Phase 3).
- Persistence is opt-in JSONL only; there is no database (by design).
- No spiking / liquid-state substrate yet (Phase 5).

See [`docs/ROADMAP.md`](docs/ROADMAP.md) for what comes next.

## License

MIT.
