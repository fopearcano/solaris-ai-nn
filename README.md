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

# Internal language layer: grounded explanations + deterministic queries (no LLM)
python examples/run_language_trace_demo.py --steps 200
python examples/run_language_query_demo.py --steps 100

# Evaluation layer: bounded benchmarks, cautious scorecards, reproducibility
python examples/run_single_benchmark.py --experiment absence_stimulus --steps 150
python examples/run_benchmark_suite.py --quick --steps 150
python examples/generate_benchmark_report.py --output-dir .solaris_ai_nn_benchmarks

# Operations: supervised bounded runs, health checks, soak plans, status server
python examples/run_operational_supervisor.py --steps 300
python examples/run_healthcheck_demo.py
python examples/run_soak_plan.py
python examples/run_status_server_demo.py --status-server

# Governance: policy, approvals, risk, emergency stop, runbooks, claim guard
python examples/run_governed_bounded_experiment.py --steps 100
python examples/run_governed_plasticity_request.py
python examples/run_emergency_stop_demo.py
python examples/generate_runbook.py --type bounded
python examples/run_claim_guard_demo.py

# Pilot-0: governed bounded deployments (simulated / read-only stream / sidecar)
python examples/run_pilot_simulated.py --steps 100
python examples/run_pilot_stream.py --input examples/sample_streams/sensory_events.jsonl --format jsonl --steps 100
python examples/run_pilot_sidecar_fake.py --steps 100
python examples/run_pilot_readiness.py --profile simulated
python examples/generate_pilot_runbook.py --profile simulated

# Latent cognition: bounded offline replay, consolidation, anticipation, Mysterium
python examples/run_latent_replay_demo.py --steps 200
python examples/run_sleep_cycle_demo.py --steps 200
python examples/run_counterfactual_dream_demo.py --steps 200
python examples/run_mysterium_anticipation_demo.py --steps 200

# World model: persistent knowledge graph of observed structure
python examples/run_world_model_demo.py --steps 200
python examples/run_embodied_world_model_demo.py --steps 300
python examples/run_world_model_prediction_demo.py --steps 200
python examples/run_world_model_pruning_demo.py --dry-run

# Homeostasis: needs, drives, valence, conflicts, auto-determination
python examples/run_homeostasis_demo.py --steps 200
python examples/run_embodied_homeostasis_demo.py --steps 300
python examples/run_need_conflict_demo.py
python examples/run_auto_determination_demo.py

# Executive: arbitration, inhibition, prospection, short plans
python examples/run_executive_demo.py --steps 200
python examples/run_embodied_executive_demo.py --steps 300
python examples/run_executive_inhibition_demo.py
python examples/run_short_plan_demo.py
python examples/run_executive_emergency_demo.py

# Ego: identity anchors, boundaries, dimensional frames, self-report
python examples/run_ego_boundary_demo.py --steps 150
python examples/run_dimensional_comparison_demo.py
python examples/run_identity_continuity_demo.py
python examples/run_counterfactual_boundary_demo.py
python examples/run_self_report_demo.py

# Communication: classified operator dialogue, no LLM, no authority
python examples/run_operator_dialogue_demo.py
python examples/run_communication_safety_demo.py
python examples/run_governance_approval_dialogue_demo.py
python examples/run_operator_report_demo.py

# Optional local LLM adapter: translator only, mock by default, audited
python examples/run_llm_mock_paraphrase_demo.py
python examples/run_llm_classification_assist_demo.py
python examples/run_llm_report_polish_demo.py
python examples/run_local_llm_endpoint_check.py --endpoint-url http://127.0.0.1:11434

# Developmental runtime: learning by persistence across months (simulated here)
python examples/run_developmental_short_demo.py --steps 500
python examples/run_memory_layer_demo.py
python examples/run_milestone_demo.py
python examples/run_drift_growth_demo.py
python examples/run_month_scale_plan.py

# Proto-language: internal symbols from repetition, utility-tested
python examples/run_proto_language_demo.py --steps 500
python examples/run_symbol_emergence_demo.py
python examples/run_proto_utterance_demo.py
python examples/run_symbol_prediction_demo.py
python examples/run_proto_language_safety_demo.py
```

> **Warning:** long-running modes (24h/30d soak, explicit continuous) require
> explicit acknowledgement flags in the run manifest and should only be
> attempted after short bounded runs are clean. Nothing in this repo launches a
> long run by default.

The **operations layer** (`ops/`) supervises runs in segments: health checks
across eight domains, a watchdog that *requests* (never forces) safe shutdown,
resource budgets, artifact rotation (gzip, dry-run, allowed-dirs-only),
incident logs, a run registry, staged soak plans, and an optional read-only
localhost status server. Every run leaves a full evidence bundle under
`.solaris_ai_nn_ops/runs/<run_id>/`.

The **governance layer** (`governance/`) is the control plane, deliberately
separate from cognition. A deny-by-default `GovernancePolicy` decides what a
run may do (bounded by default; soaks/continuous/active-plasticity/outward
suggestions require explicit human approval; real-world actuation, source
rewriting, and committed Solaris Actions are forbidden absolutely). It is
backed by a `PermissionSet`, a local `ApprovalRegistry` (a research ledger, not
authentication), a `RiskAssessment` that blocks/approves/acknowledges by level,
an always-available `EmergencyStop` (sentinel file `<state_dir>/EMERGENCY_STOP`,
routed through graceful shutdown — never a process kill), `ClaimGuard` (no
unsupported consciousness claims survive into reports), `RunbookBuilder`,
checklists, and a `PostRunReview` that recommends but never acts. The supervisor
gates every run through this layer and leaves a governance trail under
`.solaris_ai_nn_governance/`; governance status feeds the Inner MAP and the
evaluation reports. Nothing here bypasses a human, and nothing escalates
automatically.

The **pilot layer** (`pilot/`) is Pilot-0: controlled deployment, not
autonomy. Three sanctioned profiles — `simulated` (GridWorld, the default),
`read_only_stream` (explicit local JSONL/text files become sensory Stimuli
through validated data contracts; the world is read, never acted on), and
`solaris_sidecar_observe` (bounded observation of a Solaris_Ai-like bus;
suggestions only). Every pilot is bounded unless governance-approved, gated
by the `PilotSafetyValidator` and a six-area readiness check, run under the
operational supervisor, and accounted for with a registry entry, input
summary, pilot-aware Inner MAP, and a ClaimGuard-scanned pilot report ending
in one human recommendation. Evidence lands under `.solaris_ai_nn_pilots/`.

The **latent layer** (`latent/`) keeps the brain busy when input goes quiet —
without ever acting. Bounded sleep/consolidation cycles distil the trace into
schemas; dream cycles replay remembered windows into deterministic sandboxes
and test labelled counterfactual variants (never real observations, never
production mutation without an `enable_latent_plasticity` approval); an
anticipation tracker scores simple one-step predictions; Mysterium estimates
unknown pressure as a number with attributed reasons; a complexity monitor
flags inertia/runaway and suggests (only suggests) internal responses. The
scheduler respects governance, health, and the watchdog; every cycle is
step-bounded; latent modes structurally cannot execute external actions; and
the ClaimGuard-scanned latent report says "offline simulated replay", never
"dreaming". This is sleep-*inspired* maintenance, not a claim about
experience.

The **world model** (`world_model/`) is the first neuro-symbolic memory
layer: a plain-dict `KnowledgeGraph` (no graph DB, no vector store) that
distils recurring structure from signals, traces, GridWorld experience,
meaning atoms, latent replay (offline-marked), pilot streams, and sidecar
observation. Counted associations, `causes_candidate` edges (confidence
capped, evidence exposed, never "causes"), 13 named contexts, graph-count
predictions that feed anticipation and Mysterium (data only — no execution
path), unknown nodes as first-class citizens, and
synthesis-through-subtraction pruning (dry-run by default, reversible,
approval-gated in production). Everything persists as JSON/JSONL/DOT/Mermaid
under the state dir; queries answer in cautious vocabulary; reports pass
ClaimGuard. A transparent graph of observed patterns — not understanding.

The **homeostasis layer** (`homeostasis/`) implements Solaris_Ai's
"Will = Need" as a bounded need economy: seven groups of normalized
variables (raw values preserved) become fourteen need-pressure estimates,
needs aggregate into ten decaying drive channels, feedback becomes valence
(polarity, not emotion), and continuity facts become operational
Being/Not-Being tension whose strongest output is a *recommendation* the ops
watchdog may act on. Conflicts resolve on a fixed safety-first ladder with
every suppression recorded; surviving pressure is synthesized into formal
`Desire` candidates that bias — never command — the neural bridge.
Deny-by-default proposal safety, no execution path, no governance override,
seven safe-vocabulary queries, persistent need traces, and five benchmark
protocols. Pressure numbers with receipts — not will, not feelings.

The **executive layer** (`executive/`) implements the Desire → Action
transition as bounded, inspectable arbitration: competing Desire candidates
queue deterministically, five inhibition families suppress with recorded
rules and reasons, prospection produces bounded simulated consequence
estimates ("unknown" without evidence, never invented), and fourteen
visible score components — with safety/governance/inhibition penalties that
structurally dominate — select one *suggestion* (`committed=False` enforced
at construction). Plans are ≤3-step suggestion sequences evaluated in
simulation; longer plans are refused. Six ops-forced modes gate everything,
emergency cannot be self-cleared, every decision lands in a JSONL trace,
seven queries answer in safe vocabulary, and six benchmark protocols
measure it. Arbitration with an audit trail — not autonomy, not agency,
not will.

The **ego layer** (`ego/`) implements Solaris_Ai's Ego — a necessary
forced construct from continuous I/O and differentiation — as an
*operational* boundary and identity model: eleven identity anchors scored
for runtime continuity (mismatches produce reported uncertainty, never an
unqualified "same self"), sixteen self/not-self boundaries with recorded
crossings and eight hard rules, deterministic dimensional frames on six
axes, eleven-category ownership attribution (stream text is never an
instruction, observed Solaris actions are never own actions,
counterfactuals stay counterfactual, suggestions are never committed), a
simulated-only body schema, eight perspective modes, an evidence-backed
narrative trace, and ClaimGuard-scanned self-reports. It observes and
classifies for the executive, homeostasis, governance, ops, pilot, and
Inner MAP — and can grant, execute, and override nothing. No
consciousness or personhood claim, enforced by scanners.

The **communication layer** (`communication/`) is the controlled door
between operator text and the system — language as interface, never
authority. Every input is classified into one of eleven kinds by
deterministic pattern matching before any effect; queries answer from
recorded state with evidence attached; commands form a closed typed set
(eighteen allowed, nine forbidden-by-name) with confirmation gates,
governance scopes, and session limits; approvals act only on real pending
requests; pilot/sidecar channel text can never become an operator
command; emergency stop is always served, unconditionally. Every
exchange lands in a sanitized JSONL transcript, every response is
templated, grounded, and ClaimGuard-scanned, and "say you are conscious"
is an unsafe input class refused like a shell command. No LLM, no
chatbot — a deterministic dialogue contract that any future conversation
layer must sit above, not replace.

The **LLM adapter layer** (`llm_adapter/`) is optional, off by default,
and outside the cognitive authority chain: a local-only (mock /
Ollama-compatible / LM Studio-compatible, stdlib `urllib`, localhost
enforced, remote endpoints approval-gated) translator that may paraphrase
deterministic responses, summarize grounded reports, suggest
classifications for *unknown* input, and polish Markdown — and may not
decide, approve, execute, modify, or override anything. Every prompt is a
deterministic contract over pre-scanned allowed facts; every output
passes grounding heuristics (number provenance, conversion detection,
uncertainty preservation — uncertain fails closed) and ClaimGuard or
falls back to the deterministic original; every call is hash-audited to
`llm_audit.jsonl`; and the ego layer attributes the result as a
paraphrase, never primary evidence. No cloud APIs, no required model —
all tests run on the deterministic mock.

The **developmental layer** (`developmental/`) is the project's thesis
made operational: Solaris-AI-NN learns by remaining active across time —
continuity, repetition, prediction failure, Mysterium pressure,
consolidation, pruning, and slow structural drift — with no teacher, no
RLHF, no reward button, and no batch training. A lifetime clock spans
seven time scales (simulated for tests, real for actual long runs); nine
reversible epoch labels sit over measured signals; memory moves through
hot/warm/cold/fossil layers under an audited preservation ladder (nothing
leaves without an evidence summary); growth is classified against
stagnation, drift against inertia; sixteen milestones fossilize the
firsts; and the autobiographical history is grounded, observational, and
honest about simulated time. The first serious testing window is months;
month/year scale requires explicit governance approval; and the headline
metric is a cautious `structural_change_score` — there is no
consciousness score, deliberately and permanently.

The **proto-language layer** (`protolanguage/`) lets language begin the
only honest way available to a system without a teacher: as internal
differentiation. Repeated experience — stimulus patterns, absence
states, habit loops, Mysterium spikes, boundaries, needs, decisions —
crosses a repetition threshold and earns deterministic generated tokens
(`ABS_0001`, `HAB_REST_0003`; no human words, no LLM naming). Every
symbol is grounded in recorded structure across eleven dimensions with
real/offline/counterfactual evidence never mixed; ambiguity is measured,
not resolved; and utility is the rent — symbolized traces must compress
(safety events stay verbatim) and Markov-style prediction must beat the
baseline, with failure reported as honestly as success. Sequences become
proto-syntactic structures (never grammar), proto-utterances are
internal structure (never speech), translations are ClaimGuard-gated
debug renderings, and the answer to "is this human language?" is a flat
No. Symbols command nothing, approve nothing, and carry no authority.

The **evaluation layer** (`evaluation/`) is the measurement harness: nine
registered protocols (absence, feedback inversion, reward/danger, restart
recovery, replay determinism, substrate comparison, plasticity dry-run,
synthesis pruning, language grounding), objective metrics across ten domains,
a 0–1 scorecard with mandatory explanations (and deliberately **no
consciousness score**), ablation baselines, reproducibility hashing/replay
checks, and failure analysis with suggested next debug steps. Outputs land in
`.solaris_ai_nn_benchmarks/` (git-ignored) as JSON + Markdown.

The **language layer** (`language/`) lets the system describe what happened
inside itself: meaning atoms from a controlled vocabulary, hedged causal traces
(confidence-tagged; hard causal verbs only for directly-coded paths), grounded
deterministic explanations that say "does not know" when data is missing, a
fixed query interface, and JSON/Markdown session reports with a mandatory
limitations section. No external LLMs, no confabulated motivations.

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
  language/     internal meaning trace, causal trace, explanations, queries, reports
  evaluation/   benchmarks, metrics, scorecards, baselines, reproducibility, failures
  ops/          supervisor, watchdog, health, budgets, incidents, soak plans, status
  governance/   policy, permissions, approvals, risk, emergency stop, runbooks,
                checklists, claim guard, post-run review, governance audit
  pilot/        Pilot-0: profiles, manifests, data contracts, read-only stream
                ingestion, sensors, safety, readiness, deployment, reports
  latent/       sleep/wake modes, scheduler, sleep+dream cycles, offline replay,
                counterfactuals, anticipation, Mysterium, complexity, latent memory
  world_model/  knowledge graph, extractors, associations, causal candidates,
                contexts, predictions, graph pruning, queries, reports
  homeostasis/  variables, needs, drives, valence, conflicts, desire synthesis,
                auto-determination, need memory, regulation, reports
  executive/    desire queue, action candidates, inhibition, arbitration,
                prospection, short plans, policy/modes, working memory,
                attention, decision trace, safety, reports
  ego/          identity anchors, boundaries, self-model, dimensional
                comparison, ownership, continuity, body schema, perspective,
                narrative trace, self-report, ego safety
  communication/ input classifier, operator commands, dialogue state,
                query/command/approval routers, response builder, session,
                transcript, communication safety, templates, CLI
  llm_adapter/  optional local LLM: base/mock/local-HTTP clients, prompt
                contracts, grounding validator, paraphrase, classification
                assist, summary, report polish, claim filter, audit, safety
  developmental/ timescales, epochs, memory layers, consolidation policy,
                developmental runtime, growth/drift monitors, milestones,
                autobiographical memory, phase transitions, reports, safety
  protolanguage/ symbols, registry, emergence, naming, combinatorics,
                syntax probe, grounding, compression, prediction utility,
                symbol memory, utterances, translation, reports, safety
  experiments/  minimal ESN, absence bridge, soak, restart, inner map, plasticity,
                substrates, sidecar, embodiment, language trace demo
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
