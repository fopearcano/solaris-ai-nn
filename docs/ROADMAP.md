# Roadmap

Solaris-AI-NN grows in phases, from a transparent minimal substrate toward an
optional learning layer that can be mounted inside the real Solaris_Ai runtime.
Each phase is small, runnable, and measurable. Low compute and long runtime
remain central throughout.

## Phase 0 — Repository foundation and minimal ESN experiment ✅ (this release)

- Repository structure, packaging (`pyproject.toml`), zero runtime dependencies.
- Canonical signal vocabulary (`signals/canonical.py`) + event encoder.
- Echo State Network reservoir (pure stdlib, deterministic, spectral-radius
  normalised) + linear readout + online NLMS learning.
- Plasticity: habit reinforcement, synthesis-through-subtraction, drift.
- Memory trace + reservoir-state snapshots + consolidation stub.
- Adaptive event loop with heartbeat / absence stimuli, telemetry, epsilon-greedy
  action selection.
- `experiments/minimal_continuous_esn.py` showing accuracy climbing from chance
  to ~95%, habits strengthening, and synthesis pruning weak weights.
- Pytest suite covering signals, ESN, readout, habit, synthesis, and the loop.

**Exit criteria:** `python -m pytest` and the minimal example both pass on CPU.

## Phase 1 — Signal bridge compatibility with Solaris_Ai

- Flesh out `bridges/signal_bridge.py` into a real, tested two-way bridge.
- Confirm field-for-field compatibility with `solaris/runtime/signals.py`
  (golden-file tests against serialised reference signals).
- Optional thin adapter that converts real `solaris.runtime.signals` instances to
  dicts (kept behind an optional import so this repo stays self-contained).

**Exit criteria:** a recorded Solaris_Ai signal stream replays through an
`ExperimentLoop` and produces compatible Actions.

## Phase 2 — Continuity, persistence, and restart recovery ✅ (this release)

- Persistent runtime state (`runtime/persistence.py`): `PersistenceManager`,
  `StateCheckpoint`, `ContinuityLog` — manifest, checkpoint, telemetry, and
  append-only logs as plain JSON/JSONL under a per-brain `state_dir`.
- Lifecycle (`runtime/lifecycle.py`): `RuntimeLifecycle` with born/running/
  sleeping/checkpointing/dying/dead states and continuity-event logging.
- Continuous runner (`runtime/continuous_runner.py`): bounded (or explicitly
  `continuous=True`) loop that processes stimuli, heartbeats, checkpoints,
  restores prior state on startup, detects ungraceful shutdowns, and records
  brain-death gaps.
- Replay (`runtime/replay.py`): feed a recorded `trace_events.jsonl` back into a
  fresh bridge; deterministic given the seed.
- Telemetry expanded with lifetime/continuity metrics + `save_json`/`load_json`.
- Trace memory gains JSONL append / load / tail / count / explicit clear.
- Experiments: soak continuity, restart recovery, simulated brain-death gap;
  examples `run_soak_continuity.py` and `run_restart_demo.py`.

**Exit criteria (met):** a bounded soak run checkpoints and logs continuity; a
restart restores reservoir/readout/habit state and accumulates lifetime steps; a
simulated crash is detected with a brain-death gap; a trace replays deterministically.

**Still ahead in this theme:** multi-hour real-time soak runs with JSONL rotation
and documented failure modes (state saturation, weight collapse, habit lock-in).

## Phase 3 — Persistent memory and Inner MAP coupling ✅ (this release)

- `memory/consolidation.py` upgraded from a stub to a real structural
  consolidation step (`MemoryConsolidator`: repeated-pattern / absence-cycle /
  reaction-feedback / stable-action analysis — no LLM, no embeddings).
- Inner MAP self-model implemented (`inner_map/`): `InnerMapObserver` produces an
  `InnerMapModel` (identity, continuity, neural, memory, plasticity, boundaries,
  tendencies, unknown, modules), with a `BoundaryRegistry` and a DOT/Mermaid
  `StateGraph`, mirroring `solaris/modules/inner_map.py`.
- Persistence extended: `inner_map.json` is written on every checkpoint and the
  self-model's continuity section is restored across restarts.

**Exit criteria (met):** the substrate stops, restores, and continues, and a
persisted, inspectable self-model (`inner_map.json`) tracks its continuity,
memory, habits, synthesis, tendencies, boundaries, and unknowns across restarts.

**Still ahead in this theme:** consolidation write-*back* into the substrate
(currently observe-only) and a richer facts/boundaries self-representation.

## Phase 4 — Controlled plasticity + online adaptation benchmarks (in progress)

- ✅ Controlled, safe self-modification: a plasticity engine that proposes,
  validates, applies, logs, and rolls back bounded runtime-parameter changes
  (`plasticity/`), driven by a simple policy over telemetry + Inner MAP, with a
  feedback-inversion adaptation experiment and a habit-vs-synthesis benchmark
  (`plasticity/benchmarks.py`). Off by default; dry-run supported.
- Still ahead: a broader benchmark suite quantifying adaptation speed, retention,
  and forgetting; learning-rule comparison (NLMS vs recursive least squares); and
  an **optional NumPy-backed reservoir backend** for larger reservoirs behind a
  feature flag (the first place NumPy is justified — throughput for benchmarks —
  never required by the core logic).

**Exit criteria:** reproducible benchmark numbers and ablation tables (controlled
plasticity already ships and is fully audited/rollbackable).

## Phase 5 — Alternative substrates: Liquid State Machine / spiking simulation

- Add a Liquid State Machine variant and a simple leaky integrate-and-fire
  spiking reservoir behind the same loop interface.
- Compare temporal-coding substrates against the ESN baseline.

**Exit criteria:** at least one alternative substrate runnable through the
existing loop and telemetry.

## Phase 6 — Optional neuromorphic / edge deployment

- Profile and shrink the substrate for edge / low-power targets.
- Explore neuromorphic-friendly representations (event/spike-driven updates).

**Exit criteria:** a documented edge-profile run within a defined compute budget.

## Phase 7 — Integration back into Solaris_Ai as an optional learning substrate

- Mount Solaris-AI-NN as an *optional* module inside the real Solaris_Ai runtime,
  subscribing to the live `Bus` and emitting compatible Actions/Desires.
- Strictly additive: Solaris_Ai runs unchanged with or without the NN substrate.

**Exit criteria:** Solaris_Ai runs with the NN substrate attached, learning
online from the live signal stream, with no modification to the reference repo.
