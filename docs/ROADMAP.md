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

## Phase 2 — Long-running soak tests

- Multi-hour runs via `run_until` with bounded memory (ring buffers, JSONL
  rotation).
- Stability metrics: state energy, weight drift, prediction-error trend, pruning
  cadence over time.
- Detect and document failure modes (state saturation, weight collapse,
  habit lock-in).

**Exit criteria:** a documented soak run that stays stable and bounded for hours.

## Phase 3 — Persistent memory and Inner MAP coupling

- Turn `memory/consolidation.py` from a stub into a real consolidation step
  (distil trace/state memory into stabler structure).
- Couple consolidation to an Inner-MAP-like self-representation (facts +
  boundaries), mirroring `solaris/modules/inner_map.py`.
- Durable save/restore of substrate state across process restarts (still no
  database — JSONL/structured files only).

**Exit criteria:** a substrate that can be stopped, restored, and continue
learning where it left off.

## Phase 4 — Online adaptation / habit / synthesis benchmarks

- Benchmark suite quantifying adaptation speed, retention, and forgetting.
- Compare learning rules (NLMS vs recursive least squares) and habit/synthesis
  on/off ablations.
- **Optional NumPy-backed reservoir backend** for larger reservoirs, behind a
  feature flag — the first place NumPy is justified (throughput for benchmarks),
  never required by the core logic.

**Exit criteria:** reproducible benchmark numbers and ablation tables.

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
