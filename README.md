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

This first version deliberately uses **only the Python standard library** — *no
NumPy*. The reservoir is small (64–128 units) and the priority is transparency
and zero-dependency portability, so the linear algebra lives in
`solaris_ai_nn/utils/math.py` (including a power-iteration spectral-radius
estimator, which avoids needing an eigensolver). A NumPy-backed accelerated
backend is a deliberate, optional future step (ROADMAP Phase 4), not a
requirement for the substrate's logic.

---

## Install

Requires **Python 3.11+**. No runtime dependencies.

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
```

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
  memory/       chronological trace (JSONL), reservoir-state snapshots, consolidation
  runtime/      adaptive loop, telemetry, persistence, lifecycle, continuous runner, replay
  bridges/      SolarisNeuralBridge + seam to the conceptual Solaris_Ai reference
  experiments/  minimal ESN, absence bridge, soak continuity, restart recovery
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
