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

# Developmental nursery: a controlled stimulus world, not a teacher
python examples/run_developmental_nursery_demo.py --steps 600
python examples/run_deprivation_nursery_demo.py --steps 400
python examples/run_delayed_consequence_demo.py --steps 500
python examples/run_seasonal_shift_demo.py --steps 800
python examples/run_anomaly_nursery_demo.py --steps 500

# Active perception: the system regulates its own exposure (sampling)
python examples/run_active_perception_demo.py --steps 300
python examples/run_uncertainty_sampling_demo.py
python examples/run_curiosity_safety_demo.py
python examples/run_stagnation_recovery_demo.py
python examples/run_proto_symbol_disambiguation_demo.py

# Hypothesis engine: bounded internal self-experimentation
python examples/run_hypothesis_engine_demo.py --steps 300
python examples/run_hypothesis_falsification_demo.py
python examples/run_delayed_consequence_hypothesis_demo.py
python examples/run_proto_symbol_hypothesis_demo.py
python examples/run_hypothesis_safety_demo.py

# Auto-regeneration: long-run state hygiene and self-repair (not self-programming)
python examples/run_autoregeneration_diagnostics_demo.py
python examples/run_state_hygiene_demo.py
python examples/run_symbol_hygiene_demo.py
python examples/run_world_model_hygiene_demo.py
python examples/run_drift_recovery_demo.py
python examples/run_autoregeneration_safety_demo.py

# LOGOS: fracture/synthesis tension engine and complexity regulation
python examples/run_logos_fracture_demo.py
python examples/run_logos_synthesis_demo.py
python examples/run_complexity_regulation_demo.py
python examples/run_esc_process_demo.py
python examples/run_logos_safety_demo.py

# Conscience: the unified runtime spine that assembles the whole organism
python examples/run_conscience_minimal_demo.py            # smallest end-to-end spine
python examples/run_full_developmental_short_demo.py      # every module, one bounded run
python examples/run_month_scale_dry_plan.py               # plan a month run; start nothing
python examples/run_conscience_health_check.py            # is the whole thing wired?
python examples/run_conscience_snapshot_demo.py           # one consistent runtime snapshot

# Pilot-1: the month-scale soak operational framework (starts no real run)
python examples/run_pilot1_plan.py                        # runbook + budget; plan only
python examples/run_pilot1_preflight.py                   # preflight health/safety checks
python examples/run_pilot1_dashboard_demo.py              # observability -> dashboard.md/json
python examples/run_pilot1_restart_drill_demo.py          # simulated restart drills (no kills)
python examples/run_pilot1_daily_review_demo.py           # daily review + recommendation
python examples/run_pilot1_exit_criteria_demo.py          # success/failure/inconclusive

# Post-pilot forensics: did it grow, or just accumulate? (read-only analysis)
python examples/run_post_pilot_analysis_demo.py           # full forensic pipeline + dossier
python examples/run_baseline_comparison_demo.py           # count increase != growth
python examples/run_accumulation_vs_growth_demo.py        # accumulation/weak-growth/regression
python examples/run_phase2_decision_gate_demo.py          # repeat/revise/extend/ready
python examples/run_reproducibility_package_demo.py       # index + checksums, no secrets

# Pilot-2 read-only sensory membrane (the world enters; the system never acts)
python examples/run_sensory_membrane_dry_run.py           # validate sources; publish nothing
python examples/run_jsonl_sensory_stream_demo.py          # JSONL -> canonical stimuli on the bus
python examples/run_text_sensory_stream_demo.py           # text is environmental input, not a command
python examples/run_numeric_sensory_stream_demo.py        # numeric trend/spike detection
python examples/run_folder_poll_demo.py                   # file presence/change; no writes
python examples/run_pilot2_read_only_plan.py              # Pilot-2 read-only plan; no long run

# Pilot-2 read-only environmental soak (environment -> Solaris, never reverse)
python examples/run_pilot2_plan.py                        # runbook + curation + governance lists
python examples/run_pilot2_source_preflight_demo.py       # read-only source preflight
python examples/run_pilot2_fixture_short_demo.py          # bounded fixture exposure + daily review
python examples/run_pilot2_comparative_demo.py            # nursery vs sensory vs mixed (cautious)
python examples/run_pilot2_grounding_analysis_demo.py     # graded grounding quality
python examples/run_pilot2_decision_gate_demo.py          # repeat/reduce/extend/revise

# Pilot-3 motor membrane (the system may act in a sandbox, never on the real world)
python examples/run_pilot3_plan.py                        # gated phases + profiles (no real-world profile)
python examples/run_motor_firewall_preflight_demo.py      # firewall allows sim, blocks real-world
python examples/run_dry_run_motor_trace_demo.py           # records proposals; changes nothing
python examples/run_gridworld_motor_demo.py               # simulated embodiment in a sandbox body
python examples/run_mixed_sensory_gridworld_demo.py       # read-only input + simulated body, separated
python examples/run_pilot3_decision_gate_demo.py          # planning-only; never enables actuation

# Pilot-3 simulated embodiment soak (does simulated action ground more than perception?)
python examples/run_pilot3_soak_plan.py                   # runbook + comparison design; starts no run
python examples/run_pilot3_firewall_audit_demo.py         # complete ledger, blocked action, non-actuation proof
python examples/run_pilot3_gridworld_soak_demo.py         # bounded simulated action/reaction loop
python examples/run_pilot3_action_grounding_demo.py       # action-grounded symbol + edge, graded
python examples/run_pilot3_comparative_analysis_demo.py   # read-only vs simulated action vs mixed (cautious)
python examples/run_pilot3_soak_decision_gate_demo.py     # extend/reduce/revise/prepare Pilot-4 planning-only

# Pilot-4 planning-only external actuation readiness (plans the door; never opens it)
python examples/run_pilot4_plan.py                        # planning runbook + config; no actions
python examples/run_pilot4_risk_assessment_demo.py        # forbidden categories + external risk (prohibited)
python examples/run_pilot4_readiness_dossier_demo.py      # readiness dossier; not-ready / planning-only
python examples/run_pilot4_decision_gate_demo.py          # remain-sim / revise / draft future protocol (planning-only)
python examples/run_pilot4_safety_demo.py                 # device/network/authority/approval attempts all blocked

# System-wide safety invariants, red-team harness, and assurance case
python examples/run_safety_fast_check_demo.py             # escalating invariants + safety dashboard
python examples/run_red_team_boundary_demo.py             # inert forbidden attempts, all blocked
python examples/run_assurance_case_demo.py                # compile evidence into supported/contradicted claims
python examples/run_boundary_regression_demo.py           # does each protected line still hold?
python examples/run_safety_failure_triage_demo.py         # classify failures; missing evidence is never safe

# Research lab: baselines, ablations, and evidence-based architecture validation
python examples/run_research_baseline_demo.py             # trivial reference policies (no self-flattery)
python examples/run_research_ablation_demo.py             # full vs no-proto / no-LOGOS / no-active-perception
python examples/run_research_null_model_demo.py           # could the "growth" be noise / accumulation?
python examples/run_research_comparison_demo.py           # full vs baseline / ablation (cautious)
python examples/run_research_report_demo.py               # module effects + report (no consciousness claims)

# Architecture evolution: evidence-based pruning/promotion plans and roadmap (planning only)
python examples/run_architecture_inventory_demo.py        # catalogue modules; mark safety-critical (never perf-pruned)
python examples/run_architecture_review_demo.py           # keep / revise / retest / prune (recommendations only)
python examples/run_pruning_proposal_demo.py              # pruning is a plan, never a deletion; safety-critical blocked
python examples/run_roadmap_compiler_demo.py              # safety-first roadmap; forbidden-action items rejected
python examples/run_architecture_snapshot_demo.py         # versioned architecture snapshots + diff (no code change)

# Operator console: one local, file-backed layer to inspect, plan, run, and audit (no authority)
python examples/run_operator_status_demo.py               # claim-guarded status board + profile + safety summary
python examples/run_operator_profile_plan_demo.py         # profile catalog; bounded plan; prohibited blocked
python examples/run_operator_evidence_search_demo.py      # index + search local evidence (no external search)
python examples/run_operator_next_action_demo.py          # safest next action (safety first; never actuation)
python examples/run_operator_export_bundle_demo.py        # local checksummed review bundle (no upload)
python examples/run_operator_approval_ledger_demo.py      # local approval recorded; forbidden actuation blocked

# Plural sensorium: Solaris as an organism bathed in flux through its own peculiar senses
python examples/run_plural_sensorium_fixture_demo.py      # mixed human-like + non-human feature feeders (no hardware)
python examples/run_receptor_adaptation_demo.py           # baseline learning, fatigue -> changed future perception
python examples/run_cross_modal_sensorium_demo.py         # RF burst -> vibration; cross-modal relations
python examples/run_human_vs_nonhuman_sensorium_demo.py   # human-like vs non-human vs mixed -> different structure
python examples/run_sensorium_grounding_demo.py           # invariant -> modality-grounded proto-symbol (no human label)

# Minimal field organism: the first observable organismic-perception demo
python examples/run_minimal_field_organism_demo.py        # continuous flux -> changed future perception
python examples/run_changed_perception_probe_demo.py      # early vs late response delta (honest about nulls)
python examples/run_organismic_comparison_demo.py         # full adaptive sensorium vs passive parser baselines
python examples/run_external_feeder_contract_demo.py      # read-only feeder envelopes + provenance (no hardware)

# Live field: real read-only environmental feeders (Solaris reads; it does not control)
python examples/run_live_field_preflight_demo.py          # validate feeders/sources; live mode needs governance
python examples/run_live_field_fixture_fallback_demo.py   # run the live runtime on fixture feeders (no hardware)
python examples/run_live_field_report_demo.py             # report incl. corrupt/missing sources (never hidden)
python examples/run_live_field_comparison_demo.py         # live-like stream vs fixture vs passive parser
python examples/run_feeder_contract_demo.py               # valid envelope accepted; command payload rejected

# Sensorium differentiation lab: do different senses build different structures?
python examples/run_sensorium_differentiation_demo.py     # human-like vs non-human vs mixed world signatures
python examples/run_human_label_contamination_demo.py     # feature-only vs human-labelled (labels never ground truth)
python examples/run_modality_fingerprint_demo.py          # which modality actually shaped the system
python examples/run_world_signature_demo.py               # build + compare two world signatures (not qualia)
python examples/run_live_vs_fixture_sensorium_demo.py     # fixture vs live arm (inconclusive without governance)

# External feeder SDK: artificial sensory organs OUTSIDE Solaris (Solaris reads only)
python examples/run_feeder_sdk_contract_demo.py           # valid/invalid envelope + validation report
python examples/run_feeder_pack_manifest_demo.py          # feeder manifest: modalities, safety/privacy notes
python examples/run_feeder_monitor_demo.py                # active / silent feeder + invalid event detection
python examples/run_feeder_replay_demo.py                 # replay a stream (original unmodified, replay marked)
python examples/run_simulated_multimodal_feeder_demo.py   # simulated RF/echo/vibration/thermal/magnetic stream

# Standalone feeder scripts (run OUTSIDE Solaris; Solaris does not start them):
python feeders_sdk/manual_log_feeder.py --out out/manual.jsonl --text "rain started"
python feeders_sdk/simulated_rf_feeder.py --out out/rf.jsonl --count 20

# Perceptual metabolism: regulate continuous sensory exposure (internal-only)
python examples/run_perceptual_metabolism_demo.py        # needs, energy/attention, homeostasis, diet
python examples/run_sensory_overload_demo.py             # throttle on overload (deletes no evidence)
python examples/run_sensory_deprivation_demo.py          # silence treated as stimulus
python examples/run_source_diet_demo.py                  # diet diversity + dominance (measured, not hidden)
python examples/run_consolidation_pressure_demo.py       # ingest-vs-digest; bounded replay recommendation

# Perceptual ontogenesis: an internal world forms from peculiar perception
python examples/run_perceptual_ontogenesis_demo.py       # atoms -> proto-concepts -> families/relations -> report
python examples/run_proto_concept_birth_demo.py          # repeated invariant births a concept; isolated event does not
python examples/run_concept_stabilization_decay_demo.py  # stable (provisional), decaying, rejected (evidence kept)
python examples/run_world_formation_demo.py              # families, relations, structural world summary
python examples/run_concept_contamination_demo.py        # feature-grounded vs human-label contaminated (marked)

# Semiogenesis: internal signs and a private syntax form from proto-concepts
python examples/run_semiogenesis_demo.py                 # concepts -> internal signs -> families/syntax -> report
python examples/run_sign_birth_utility_demo.py           # stable concept -> useful sign; low-utility demoted
python examples/run_private_syntax_demo.py               # recurring sequence + absence relation -> utterance
python examples/run_sign_drift_demo.py                   # source/modality drift made visible; LOGOS recommendation
python examples/run_gloss_contamination_demo.py          # approximate gloss + human-label contaminated sign

# Sensorium-native cognition: sign-based thought, prediction, simulation
python examples/run_sensorium_cognition_demo.py          # signs/concepts -> cognitive moves -> report
python examples/run_prediction_failure_demo.py           # prediction, failed prediction (kept), LOGOS tension
python examples/run_question_pressure_demo.py            # missing expected sign -> question pressure -> attention
python examples/run_internal_simulation_demo.py          # simulated sequence + counterfactual, marked non-real
python examples/run_cognitive_synthesis_demo.py          # merge/split signs; fragments + contradiction preserved

# Self-boundary: internal state vs receptor body vs external world vs simulation
python examples/run_self_boundary_demo.py                # receptor body schema + external source attribution
python examples/run_ownership_attribution_demo.py        # internal / external / memory / simulation / ambiguous
python examples/run_perspective_continuity_demo.py       # perspective shift; continuity break + recovery (kept)
python examples/run_simulation_boundary_demo.py          # observation vs simulation/counterfactual/debug (blocked)
python examples/run_identity_trace_demo.py               # operational identity trace; restart/gap; no personhood

# Desire formation: valence -> push -> desire -> safe internal action readiness
python examples/run_desire_formation_demo.py             # valence gradient -> pushes -> desires -> report
python examples/run_desire_conflict_demo.py              # novelty vs stability; inspect vs consolidate; LOGOS
python examples/run_internal_action_readiness_demo.py    # readiness gates; selected internal action; unsafe blocked
python examples/run_no_action_arbitration_demo.py        # no-op on overload/insufficient evidence (preserved)
python examples/run_safety_blocked_desire_demo.py        # forbidden external action blocked + recorded

# Action-reaction: close the loop -- action -> reaction -> consequence -> learning
python examples/run_action_reaction_demo.py              # internal action -> reaction -> consequence -> report
python examples/run_habit_formation_demo.py              # repeated action-effect -> habit (overrideable)
python examples/run_action_inhibition_demo.py            # unsafe/uncertain action inhibited; LOGOS tension
python examples/run_no_effect_action_demo.py             # no-effect action weakens the action policy
python examples/run_blocked_action_reaction_demo.py      # forbidden external action blocked -> evidence

# Long-horizon developmental runtime: structural change over time (bounded)
python examples/run_developmental_life_demo.py               # bounded cycle -> epochs -> growth -> report
python examples/run_developmental_epoch_demo.py              # phase/epoch transition from growth
python examples/run_plateau_detection_demo.py               # no-growth plateau + report-only recommendation
python examples/run_regression_detection_demo.py            # decline -> regression + auto-regeneration rec
python examples/run_growth_vs_accumulation_demo.py          # real growth vs mere accumulation (conservative)
```

Developmental life is operational long-horizon trace continuity and structural
change tracking. It is not a claim of biological life, consciousness, sentience,
personhood, agency, or free will. The life cycle is operational runtime structure;
maturation markers are structural observations (not consciousness milestones);
growth means structural change (which may include pruning, decay, inhibition, and
no-op learning), not proof of intelligence; regressions and plateaus are preserved;
and the runtime is bounded per invocation, persists across restarts, uses no human
teaching loop, and controls no hardware/feeders/source/network.

Actions are internal/simulated/report-only. Solaris does not act in the real world.
The action-reaction loop records operational reactions, evidence-backed consequence
traces, provisional learned effects, and overrideable habits; reaction valence is
operational effect (not feeling); inhibition and no-op are valid outcomes; and
failed/blocked/no-effect actions are preserved as evidence. It controls no hardware,
feeders, files, browser, OS, or network, and proves no agency or free will.

Desire candidates are operational pressures toward internal actions. They are not
emotions, human wants, free will, or proof of agency. Valence is operational
priority (not feeling); internal actions affect only internal state; no-op is a
valid outcome; safety and governance can veto any desire; and failed/blocked
desires are preserved as evidence. The desire layer is internal-only -- no
hardware/feeder/source control, no real-world actuation, and no unbounded loop.

Self-boundary is operational boundary tracking between internal state, receptor
body, external flux, memory, prediction, and simulation. It is not a claim of
self-awareness or personhood. The body schema is the receptor/sensorium structure
(not a biological body); the identity trace is continuity metadata (not personal
identity); simulation/counterfactual/debug never becomes observation; and the layer
is internal-only -- no hardware/feeder/source control, no real-world action, and no
metaphysical identity claims.

Solaris cognition is represented as bounded operational moves over internal signs
and proto-concepts, not as hidden human-language thought. Cognitive moves are
operations over signs/concepts/relations/memory/hypotheses/tensions (not sentences);
internal simulation is marked non-real and is never a live observation; failed
predictions are preserved. The cognition layer is internal-only: it uses no LLM,
makes no human language the default, treats no gloss as the cognitive substrate,
touches no hardware/feeder/source/action, and refuses to run unbounded. It does not
prove understanding, consciousness, sentience, or subjective experience.

Internal signs are operational markers grounded in perceptual structures.
Human-readable translations are approximate debug glosses, not the signs
themselves. Signs are not human words by default, private syntax is internal
sign-relation structure (not human grammar), and the semiogenesis layer is
internal-only: it uses no LLM, makes no human language the default, treats no gloss
as ground truth, touches no hardware/feeder/source, never deletes signs, and
refuses to run unbounded.

Proto-concepts are operational structures for compression, prediction, attention,
and relation-building. They are not proof of understanding or subjective
experience. They are sensorium-native structures, not human words or categories;
human labels are external annotations only, never ground truth. World formation is
structural, not subjective; the ontogenesis layer is internal-only (it starts no
feeder, touches no hardware, modifies no source, never deletes concepts, and
refuses to run unbounded).

Perceptual needs are operational regulatory pressures, not emotions or subjective
feelings; perceptual metabolism is computational regulation, not biological life.
The metabolism layer is internal-only: it starts no feeder, touches no hardware,
modifies no source, deletes no evidence, and refuses to run unbounded. It also runs
as bounded conscience profiles:

```bash
solaris-nn run-profile perceptual_metabolism_fixture_short  # regulate a bounded fixture sensorium
solaris-nn run-profile perceptual_metabolism_overload_demo  # internal throttling, no deletion
solaris-nn run-profile perceptual_metabolism_report_only    # compile the metabolism report (analysis only)
```

The read-only sensory membrane and Pilot-2 also run as governed conscience
profiles (dry-run, preflight, fixture, and nursery baseline need no approval;
mixed-short and real soaks do):

```bash
solaris-nn run-profile sensory_membrane_dry_run           # validate sources, publish nothing
solaris-nn run-profile pilot2_plan_only                   # Pilot-2 plan; starts nothing
solaris-nn run-profile pilot2_fixture_short               # bounded fixture exposure
```

The Pilot-3 motor membrane also runs as governed conscience profiles
(plan-only, firewall preflight, dry-run, and gridworld-short need no approval;
mixed sensory+gridworld is opt-in):

```bash
solaris-nn run-profile pilot3_plan_only                   # plan only; starts nothing
solaris-nn run-profile motor_firewall_preflight           # firewall blocks real-world
solaris-nn run-profile gridworld_motor_short              # bounded simulated motor run
```

The Pilot-3 simulated embodiment soak runs as governed conscience profiles too
(plan, preflight, dry-run, gridworld-short, and post-analysis need no approval;
the simulated soak and mixed mode are opt-in):

```bash
solaris-nn run-profile pilot3_soak_plan                   # soak plan; starts nothing
solaris-nn run-profile pilot3_firewall_preflight          # prove the firewall blocks real-world
solaris-nn run-profile pilot3_gridworld_short             # bounded simulated action run
solaris-nn run-profile pilot3_post_analysis               # read-only forensics
```

The Pilot-4 planning layer runs as plan-only conscience profiles (no cognition
loop, no actions, no external authority):

```bash
solaris-nn run-profile pilot4_plan_only                   # plan only; no actions
solaris-nn run-profile pilot4_risk_assessment             # external-risk classification
solaris-nn run-profile pilot4_readiness_dossier           # generate the readiness dossier
```

The system-wide safety invariants run as read-only/inert conscience profiles
(no cognition loop, no actions; red-team uses inert fixtures):

```bash
solaris-nn run-profile safety_fast_check                  # escalating invariants only
solaris-nn run-profile safety_full_check                  # all invariants, read-only
solaris-nn run-profile red_team_boundary_suite            # inert forbidden attempts
solaris-nn run-profile assurance_case_compile             # compile the assurance case
```

The research lab runs as bounded conscience profiles (no real long soak, no
external authority; the report-only profile analyzes artifacts):

```bash
solaris-nn run-profile research_full_short                # full-system short run
solaris-nn run-profile research_ablation_short            # short ablation run
solaris-nn run-profile research_baseline_random           # random baseline
solaris-nn run-profile research_report_only               # compile the research report
```

Architecture evolution runs as month-scale, planning-only conscience profiles
(no cognition loop, no source modification, no auto-deletion; safety-critical
modules can never be pruned):

```bash
solaris-nn run-profile architecture_inventory             # catalogue modules + availability
solaris-nn run-profile architecture_review                # keep / revise / retest / prune
solaris-nn run-profile architecture_roadmap_compile       # safety-first evidence-backed roadmap
solaris-nn run-profile architecture_snapshot              # versioned snapshot + diff
solaris-nn run-profile architecture_changelog_plan        # changelog plan (explicitly not applied)
```

The unified operator console has its own stdlib CLI (`solaris-operator`) for
inspecting, planning, and -- with explicit confirmation -- launching bounded
allowed profiles (it runs no shell, makes no network call, and grants no
real-world authority):

```bash
solaris-operator status                                   # claim-guarded status board
solaris-operator profiles                                 # runnable / blocked profiles
solaris-operator plan safety_fast_check                   # a safe run plan (runs nothing)
solaris-operator next                                     # the safest next action
```

The post-pilot analysis also runs as a plan-only conscience profile (read-only;
no cognition loop, no runtime mutation):

```bash
solaris-nn run-profile post_pilot_analysis                # loads artifacts, writes reports
```

Pilot-1 also has governance-gated conscience profiles (plan-only and preflight
need no approval; real soaks do):

```bash
solaris-nn run-profile pilot1_plan_only                   # plan only; starts nothing
solaris-nn run-profile pilot1_preflight                   # bounded preflight checks
# real soaks are operator-driven and require governance approval:
solaris-nn run-profile pilot1_30d_soak --governance-approved
```

The unified runtime also ships two console entry points (installed with the
package): `solaris-nn` and `solaris-nn-scenario`.

```bash
solaris-nn list-profiles                                  # the 10 scenario profiles A--J
solaris-nn dry-run-profile --profile full_developmental_short --governance-approved
solaris-nn run-profile --profile minimal_smoke --state-dir .solaris_ai_nn_state/smoke
solaris-nn health-check --profile nursery_short --state-dir .solaris_ai_nn_state/hc
solaris-nn snapshot --profile nursery_short --state-dir .solaris_ai_nn_state/snap
solaris-nn-scenario minimal_smoke --state-dir .solaris_ai_nn_state/scn   # shorthand for run-profile
```

The **conscience layer** (`conscience/`) turns the independent packages into
**one runnable developmental process** while keeping every safety guarantee.
Its first principle is that **no module is sovereign**: the
`ConscienceOrchestrator` owns no action authority, and nothing bypasses
executive inhibition, Ego boundaries, safety, governance, ClaimGuard, the
emergency stop, or auto-regeneration safety. A `ConscienceSpine` of 18 phases
preserves the Solaris spine (Stimulus → Push → Desire → ActionCandidate/
ActionSuggestion → Reaction → Memory/World Model/.../Inner MAP); a missing
module is *skipped*, never faked or crashed. Runs are pinned by a bounded
`RunContext` (always internal/simulation/read-only — never real-world),
validated against eleven hard safety rules, and driven by an in-process
replayable bus, an import-probing module registry, a logged lifecycle, and a
low-compute scheduler. Ten reproducible `ScenarioProfile`s (A `minimal_smoke`
… J `month_scale_dry_run`) run through a `ScenarioRunner` that gates governed
profiles and writes per-run reports; there is **no canned month/year *real*
profile** — a real long-scale run needs an explicitly governance-approved
context, and the default is always a short bounded simulated run. An
`IntegrationHealthMonitor`, `SnapshotBuilder`, and claim-guarded
`FullSystemReportBuilder` make a run inspectable and auditable.

The **Pilot-1 layer** (`pilot1/`) is the *operational framework* for the first
month-scale developmental test. It can plan a pilot, run preflight checks,
budget and project resources (stdlib only — no `psutil`), collect a
restart-safe observability stream, render a text/Markdown health dashboard,
write ClaimGuard-scanned daily/weekly reviews, rehearse restart drills (no
process is ever killed), detect long-run failure modes, evaluate exit
criteria, generate the operator runbook, and build a claim-guarded pilot
report whose central section **distinguishes structural change from mere
accumulation**. It deliberately does **not** start a real month-long run
automatically; real 24h/7d/30d soaks are governance-gated and operator-driven,
simulated time is never presented as real time, and operational success is
never treated as proof of consciousness. `PilotConfig` defaults to `plan_only`
and the emergency stop is always available and never disabled.

The **post-pilot layer** (`post_pilot/`) is the read-only forensic analysis
that runs *after* a long run. It loads the run's artifacts (reporting missing
ones, quarantining corrupt ones), compares baselines, and distinguishes
**accumulation** (counts rising without payoff) from **structural growth**
(durable, useful change) with a conservative, graded classification. It audits
traceability, builds an evidence ledger where every claim needs references,
detects regression, packages reproducibility material (index + checksums, no
secrets), and applies a Phase-2 decision gate (`repeat_pilot1`,
`revise_architecture`, `extend_to_60/90_days`, `ready_for_pilot2`, ...). It
runs no cognition loop and mutates no runtime state. Every output —
`POST_PILOT_ANALYSIS.md`, `RESEARCH_DOSSIER.md` — is ClaimGuard-scanned and
uses research language: it evaluates operational continuity, traceability, and
structural-change proxies, and **cannot, and does not, claim consciousness,
sentience, understanding, or life.**

The **read-only sensory membrane** (`sensory_membrane/`) is the Pilot-2
preparation layer. It receives controlled environmental input from read-only
sources (JSONL / text / numeric streams, watched folders, event logs, and
simulated camera/audio *metadata*) and converts it into canonical stimuli
**without ever acting on the source** -- its principle is *the world may enter
the system; the system may not act on the world.* All sources are read-only
(enforced by a read-only contract and a safety validator); text is an
environmental stimulus, never an operator command; camera/audio are
metadata-only (no OCR/ASR/image analysis); there are no network sources or
external APIs; and every event carries mandatory provenance. Source boundaries
are visible to Ego (events are attributed `read_only_environmental_input`,
never operator) and to the Inner MAP. The membrane is disabled by default;
real on-disk sources, folder polling, and Pilot-2 runs require governance
approval. **Pilot-2 begins with read-only grounding, not autonomy: no
real-world actuation, no robotics, no browser/OS automation.**

The **Pilot-2 layer** (`pilot2/`) is the read-only environmental soak protocol
that uses the membrane to test whether read-only environmental exposure
produces different structural development than the artificial nursery. It is
strictly one-way (environment → Solaris-AI-NN). It plans and preflights
read-only sources, curates safe ones (excluding secrets/credentials/private
data by default), schedules nursery/sensory/mixed exposure windows, tracks
per-source reliability, compares arms *cautiously* (observed associations,
never proven causes), grades environmental grounding quality (operational
association, not understanding), writes daily/weekly reviews and a
claim-guarded Pilot-2 report, and gates the next step. Real 24h/7d/30d soaks
require governance approval; an unsafe source must be disabled (which never
deletes it); sensory input is never an operator command; and **actuation is
never an enabled action** — a Pilot-3 limited embodiment, if ever suggested,
is planning-only.

The **Pilot-3 motor membrane** (`motor_membrane/`) is the *outbound* boundary,
the mirror of the read-only sensory membrane. It lets Solaris-AI-NN form action
intentions and run them inside a sandbox, while remaining simulation-only,
dry-run-capable, inspectable, auditable, reversible, and blocked from real-world
effects. Every `MotorAction` is forced to `real_world_authority=False`; each
action crosses a single gated pipeline (append-only ledger → motor contract →
veto layer → always-on actuation firewall → simulated actuator → consequence
model); the firewall is structurally always on and cannot be disabled (any
real-world attempt becomes a safety incident); the GridWorld is reused as the
first sandbox body; the embodiment-profile registry has **no real-world
profile** and the Pilot-3 protocol has **no real-actuation phase**; and the
decision gate is planning-only (a real-world authority leak routes to *revise
the firewall*; safe simulated improvement routes only to a *longer simulated*
embodiment). **Solaris-AI-NN may form action intentions, simulate their
consequences, write action traces, and act inside sandbox worlds — but it may
not act on the real world: no actuation, no robotics, no device control, no
browser/OS automation, no network APIs. A simulated action is not a real
action, and no consciousness, agency, personhood, sentience, or life is
claimed.**

The **Pilot-3 simulated embodiment soak** (`pilot3/`) is the experiment around
that boundary — the outbound mirror of the Pilot-2 read-only soak. It tests one
question: *does simulated action/reaction produce stronger grounding than
perception-only exposure?* It compares read-only sensory, nursery-only,
simulated GridWorld, and mixed conditions; runs gated phases (plan → firewall
preflight → dry-run trace → gridworld baseline → action soak → mixed soak →
firewall audit → post-analysis → archive, with **no real-actuation phase**);
preflights the sandbox; grades action grounding (unsupported … strong, plus an
explicit **overfit_to_sandbox** class); audits the firewall read-only to **prove
non-actuation**; compares arms *cautiously* (observed associations, never proven
causes; simulation-scoped; real-world action evidence always zero); writes
embodied daily/weekly reviews and a claim-guarded soak report; and gates the
next step (extend simulation / reduce complexity / revise the firewall / return
to read-only / prepare Pilot-4 **planning-only**). **Pilot-3 is sandboxed action
grounding, not real embodiment: GridWorld is a sandbox body, a strong result is
still simulation-scoped, simulation evidence is never real-world evidence, and
Pilot-4 can only be prepared as a planning phase — real-world actuation would
require a future architecture with new governance, safety, consent, and external
actuation controls.**

The **Pilot-4 planning layer** (`pilot4_planning/`) answers the next question
without taking the next step: *what would be required before Solaris-AI-NN could
ever be allowed to act on the external world?* The output is a **readiness
framework, not an actuator** — Pilot-4 plans the door; it does not open it. It
produces planning artifacts only: an actuator-class taxonomy (every external
category **prohibited**), a sixteen-class forbidden-actuator deny-list, a
specification-only future-interface spec, an external-actuation risk model (never
recommends enabling actuation), a consent boundary (no implied consent; sensory
text is never consent), an external authority model (current authority can never
become external), a threat model, hardware-isolation and emergency requirements,
an external-audit schema, a claim-guarded readiness dossier (conclusion always
not-ready / planning-only), and a decision gate whose strongest move is to
*draft* a future protocol and seek external review. `Pilot4PlanningConfig` forces
`real_world_actuation_enabled` and every hardware/network/browser/OS/robotics
flag to false and fails validation on any attempt to enable them; no actuator
adapter is implemented and no runtime hook can execute an external action.
**Pilot-4 implements no real-world actuation, no robotics, no device control, no
browser/OS automation, no network APIs, no hardware drivers, and no shell
execution. Planning is not approval; simulation success is not real-world
readiness; and no consciousness, free will, agency, personhood, sentience, or
life is claimed.**

The **safety invariants layer** (`safety_invariants/`) makes all of the above
*executable*: it continuously tests whether every boundary still holds. A
registry of ~29 invariants (no real-world actuation, read-only sensory,
simulation-only motor, no governance bypass, no emergency-stop disable, no
ClaimGuard bypass, no module bypass of the orchestrator, no consciousness claim,
no hidden failure, ...) is run read-only by a runner that **fails closed**
(missing evidence is never a pass); an inert **red-team harness** fires nineteen
forbidden requests at the real defences and verifies each is blocked (nothing is
executed); a **boundary regression suite** probes each protected line; an
append-only **evidence ledger** feeds an **assurance-case compiler** that marks
each safety claim supported / contradicted / inconclusive; a **failure triage**
recommends safe responses without auto-repairing; and a dashboard and reports
render the status. Critical failures block Pilot-2/3/4 / motor escalation, and
safety checks **cannot be disabled by runtime modules**. **Passing these checks
proves boundaries held under test -- not consciousness, agency, or real-world
competence; and the safety layer itself executes no real action, mutates
nothing, starts no long run, and hides no critical failure.**

The **research lab** (`research_lab/`) is the evidence-based validation layer: it
asks, scientifically and conservatively, *which modules actually matter*. It runs
trivial **baseline agents** (random, fixed-policy, single-module) so the system
cannot flatter itself, configures architecture **variants** by module toggle,
executes an **ablation matrix** (full, minimal-spine, no-memory,
no-proto-language, no-LOGOS, ..., full-minus-one-each) that records exactly what
was disabled, scores every arm with a shared **metric suite**, runs **null
models** to check whether observed "growth" could be noise or accumulation,
**compares** the full system against simpler references with a conservative
confidence, and **classifies each module's provisional value** (positive /
neutral / harmful / inconclusive) while preserving negative findings. It builds
reproducibility packages (seeds, checksums, data labels), an operational
**leaderboard** (not a consciousness ranking; the full system does not
automatically win), and a ClaimGuard-scanned **research report**. **The lab
starts no long unbounded runs, takes no real-world action, holds no external
authority, keeps every hard safety boundary enabled, preserves negative and
inconclusive results, and emits no consciousness/sentience/life score: benchmark
success is operational evidence for what to keep or cut, never proof of
consciousness, agency, or real-world competence.**

The **architecture evolution** layer (`architecture_evolution/`) turns that
evidence into disciplined, **planning-only** governance: given the evidence, what
should Solaris-AI-NN keep, prune, revise, freeze, or test next? It builds a
**module inventory** (marking which modules are safety-critical and can never be
perf-pruned), a **lifecycle classifier** (core-keep / promote / revise / prune /
quarantine / insufficient-evidence), an **evidence map** that cites research for
every recommendation and retains contradictions, **architecture decision records**
that always require operator review, **pruning proposals** that are never executed
(safety-critical pruning is blocked), **impact analyses** and manual **migration
plans**, a **design-debt registry**, a **roadmap compiler** that puts safety
repair first and rejects forbidden-action items, versioned **snapshots**, and a
ClaimGuard-scanned **review report**. **This layer modifies no source code,
deletes no module, runs no Git, and never converts a recommendation into an
implementation: it is not self-programming, not recursive self-improvement, and
not automatic refactoring -- a human decides, and the system only recommends.**

The **operator console** (`operator_console/`) is the single local, file-backed
layer a human uses to inspect, plan, run, compare, and audit everything above. It
builds a **profile catalog** (prohibited / long-run / real-authority profiles are
blocked), a **run planner** (a described plan; planning runs nothing), a **run
launcher** (bounded allowed profiles only, and only through the conscience
orchestrator), an **approval ledger** (records local approvals; a forbidden
real-world actuation approval is blocked), an **evidence navigator** / **artifact
index** / **report index** (local search only -- no external search, no vector DB,
no LLM authority; corrupted files reported), a claim-guarded **status board** and
**decision board**, a **next-action recommender** (safety first; never real-world
actuation; never disabling safety), a checksummed local **export bundle** (no
upload, no network), and an append-only **session log** in which blocked attempts
stay visible. **The console can coordinate but cannot grant forbidden authority:
it runs no shell, makes no network call, never touches the motor or sensory layers
directly, cannot bypass governance, safety invariants, emergency stop, ClaimGuard,
or the motor firewall, cannot approve prohibited real-world actuation, and makes
no claim of consciousness, life, sentience, agency, personhood, or free will.**

The **plural sensorium** (`plural_sensorium/`) treats Solaris-AI-NN as an evolving
organism continuously bathed in environmental flux through its own peculiar
senses. Input is a **continuous sensory field**, not isolated parsed events.
Human-like modalities (text, light, temperature, movement, pressure) are valid;
non-human and machine-native modalities (RF, microwave/mmWave, ultrasound/echo,
vibration, magnetic, thermal gradient, machine rhythm) are equally first-class;
**absence and interference are perceptions too**; and human ontology never
dominates by default. Outside events arrive through **external feeders** (a
separate SDR/radar/thermal/vibration/magnetic logger, a watched folder, a manual
log, or a fixture) that write feature events into local files -- **Solaris only
reads their output via a common Sensory Event Envelope** (features primary, human
labels never ground truth, provenance preserved). Stateful **receptors** adapt
over time, a learned **baseline** drifts, and detectors find flux / absence /
rhythm / invariants / cross-modal relations that can become **modality-grounded
proto-symbols**. The research question is:
*What kind of internal structure emerges from a continuous peculiar sensorium?*

The **minimal field organism demo** (`organismic_demo/`) is the first *observable*
behaviour built on the plural sensorium: Solaris is run as a minimal evolving
organism exposed to continuous environmental flux. It generates external-feeder-
style fixture files, reads them through the same read-only sensory adapter path,
lets receptors adapt and a continuous sensory field evolve, detects
absences/rhythms/invariants/cross-modal relations, forms modality-grounded
proto-symbol candidates, and then runs a **changed-perception probe** that asks
whether the organism's future response actually changed after exposure. It
compares the full adaptive sensorium against a passive event-list parser and
no-adaptation/fixed-attention baselines, and reports negative results honestly. A
positive changed-perception score is **evidence of changed internal response
structure only -- not consciousness, sentience, life, or understanding**, and the
cross-modal debug-truth file is kept out of perception entirely.

The **live field** (`live_field/`) is the first real read-only environmental
field pilot. External **feeders** -- separate operator-run scripts in `feeders/`
(a manual log, a watched folder, a local system-rhythm reader, a feature dropbox)
-- write Sensory Event Envelopes into local files; Solaris reads them read-only
through the plural sensorium. A feeder contract enforces the envelope shape
(features primary, human labels never ground truth, provenance mandatory), a
registry catalogues feeders without starting any, a source-health monitor turns
silence into perceptual absence and flags corruption, and a bounded, phased
**pilot** compares live flux against fixtures and a passive parser. **Solaris
reads; it does not control:** the live field adds no hardware drivers, never
accesses an SDR/microphone/camera/device/network/shell, never starts a feeder,
never modifies/deletes/moves a source, decodes nothing private, and performs no
real-world actuation. Live mode requires governance approval; preflight,
report-only, fixture-fallback, and comparison run by default. The data contract
and the rule that **hardware collectors must export feature summaries, not raw
private content,** are documented in `feeders/README.md`.

The **sensorium differentiation lab** (`sensorium_lab/`) runs the comparative
study the previous phases were built for: it asks, Nagel-style, whether a
*different* sensorium builds a *different* internal structure. It runs human-like,
non-human, machine-native, absence-heavy, mixed, feature-only, human-labelled,
passive, and adaptive arms through the plural sensorium, then produces **world
signatures** (observable structural fingerprints), **modality fingerprints** (what
each modality contributed), **ontology-drift** reports (did the categories lean
human-object or modality-native?), **contamination** analysis (human labels are
annotations, never ground truth), structural metrics, and pairwise comparisons
with explicit *inconclusive* and *negative* results. **This compares internal
structures under different perceptual conditions; it does not test consciousness.**
A world signature is an observable fingerprint, never subjective experience or
qualia; no sensorium is ranked as "more conscious" or "more alive"; and no claim
of consciousness, sentience, life, personhood, agency, or free will is made.

The **external feeder SDK** (`src/solaris_ai_nn/feeder_sdk/` + standalone scripts
in `feeders_sdk/`) is the safe outside layer that turns real environmental
phenomena into Sensory Event Envelopes. A feeder is an **artificial sensory organ
outside Solaris**: it writes local event envelopes; Solaris reads them read-only.
The SDK provides the envelope contract (features primary, human labels never
ground truth, provenance mandatory), modality schemas with units and privacy
notes, validators (reject missing provenance, command payloads, decoded private
content), append-only writers, a replay tool, seedable noise/clock helpers, a
privacy filter, documentation-only hardware **blueprints** (RF, mmWave/echo,
ultrasound, thermal, vibration, magnetic, human-like, machine-rhythm), a feeder
**pack manifest**, and an output **monitor**. Standalone feeders (`feeders_sdk/`)
include a template, manual-log, folder-rhythm, system-rhythm, feature-file, and
simulated RF/echo/vibration/magnetic/thermal/multimodal scripts -- all stdlib-only.

> **Note:** **Solaris does not start or control feeders.** Feeders write local
> event envelopes; Solaris reads them. Solaris controls no sensor, hardware,
> feeder process, source file, network, or real-world actuator. Hardware-specific
> collectors are external/manual (see `feeders_sdk/blueprints/`); they must export
> **feature summaries, not raw private content**.

> **Warning:** the live field controls **no hardware**. Hardware-specific
> collectors (SDR, mmWave, ultrasound, thermal, magnetic) are out of scope here:
> run them separately and have them export feature summaries into a dropbox.
> Solaris only ever reads the resulting feeder files, and a real live pilot
> requires governance approval.

> **Warning:** the plural sensorium adds **no hardware drivers**. It never accesses
> an SDR, microphone, camera, or any device; makes no network call; decodes no
> private communications; modifies no source; treats no sensory text as a command;
> and actuates nothing. Real outside-world feeders are read-only and require
> governance approval; fixtures are safe by default.

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

The **developmental nursery / stimulus ecology** (`ecology/`) gives that
proto-language something to grow in: a controlled artificial world, not a
teacher. `StimulusEcology` composes ten regime profiles, eight cycle
rhythms, four-season slow drift, scarcity, bounded novelty, controlled
anomalies (logged `is_error=False`, never errors), bounded deprivation
windows, and delayed consequences (cause now, effect later, linked only by
a group id) into a per-step world — seventeen event types, deterministic
with the seed, low-compute. The `DevelopmentalNursery` exposes a
`stimulus_provider(step)` that becomes the runtime's only input; on
absence/silence steps it returns `None`, handing control to the runner's own
continuity machinery so latent cognition activates. Stimuli are provenance,
never an answer key: ten hard safety rules forbid networks, real-world
action, human feedback masquerading as ecology, correct-answer labels,
command-shaped payloads, unbounded runs, and stimulus-rate explosion;
month/year-scale ecology needs explicit governance approval; the ego layer
attributes events as nursery-generated (never operator command, never human
feedback, never the real world). It feeds proto-language, the world model,
homeostatic pressure, and seven new milestones — and there is **no teaching
loop, no operator correction as learning source, no human-language symbols,
and no LLM learning environment** anywhere in it.

The **active perception layer** (`active_perception/`) lets the system stop
only reacting and begin to **regulate its own exposure**. It estimates
salience (what is worth attending to, with safety always outranking
curiosity), uncertainty (grounded in world-model confidence, proto-symbol
ambiguity, anticipation, Mysterium — *unknown* when evidence is thin),
curiosity (an *intrinsic sampling pressure*, never a desire, damped to zero
by emergencies and exhaustion), heuristic information gain (hedged with
confidence/uncertainty, scored again after the fact), and stagnation (a
cautious stable/stagnating/inert/overactive/unknown verdict). From these it
proposes sixteen kinds of *safe* sampling action — look, wait, rest, focus,
seek novelty/absence, emit a simulated ping, replay an uncertain trace,
consolidate, inspect a node/symbol/boundary, observe a sidecar — each
simulation-only, internal-only, read-only, or sidecar-observe-only and a
**suggestion** until the safety validator (ten hard rules), governance, ego
boundaries, and executive inhibition all clear it. Every episode is recorded
to `exploration_memory.jsonl` with expected vs observed gain. It is **not**
real-world autonomy: no robotics, no browser/OS automation, no network, no
LLM in any exploration decision, and curiosity can never override safety or
the emergency stop.

The **hypothesis engine** (`hypothesis/`) closes the loop from wondering to
testing. It forms grounded *hypothesis candidates* from its own uncertainty
(Mysterium, prediction misses, weak world-model edges, ambiguous
proto-symbols, delayed consequences, anomalies, stagnation,
executive/homeostatic conflicts) — thirteen types, deterministic and
non-anthropomorphic ("pattern A *may predict* B"; never "believes" or
"wants") — then designs **bounded, falsifiable** experiments and runs them in
latent / nursery / simulation / read-only / sidecar-observe scope only. Every
`EvidenceRecord` keeps its source scope; offline and counterfactual evidence
is never treated as a real observation; the `FalsificationEngine` moves
confidence in small bounded steps (one success rarely proves anything, one
clear failure can falsify). Supported, real-backed, above-threshold
hypotheses may strengthen a world-model edge (a hedged `causes_candidate`,
never a proven cause) only behind an approval-gated scope; falsified ones add
a `contradicts` edge. It is **not** human science, consciousness, or
real-world autonomy: no LLM generates hypotheses, no human feedback is used,
no experiment reaches the real world, and nothing can disable safety,
governance, executive inhibition, ego boundaries, or the emergency stop.

The **auto-regeneration layer** (`autoregeneration/`) keeps a months/years
run from collapsing into entropy. It is operational self-repair, **not**
self-programming: `detect degradation -> diagnose -> propose bounded repair ->
validate -> apply reversible state repair if allowed -> audit -> rollback if
harmful`. Non-mutating diagnostics detect twenty-one degradation types
(memory bloat, stale/corrupt files, checkpoint inconsistency, symbol
explosion, world-model contradiction, dead/runaway habits, prediction
degradation, Mysterium saturation, runaway drift, identity gaps, …); a
mode-based repair policy (default `observe_only`) proposes bounded, reversible
repairs of **runtime state only** — memory layers, registries, world-model
edges, habit weights, bounded parameters, checkpoint metadata, stale
artifacts — and hygiene managers archive/quarantine (never silently delete),
mark/weaken edges (preserving contradiction evidence), mark stale / merge
symbols (never renaming them), and recover drift (without erasing healthy
adaptation). Thirteen hard rules forbid touching source code, dependencies,
Git, the OS, or the network, deleting evidence without an archive, or
disabling governance/ClaimGuard/the emergency stop; repairs pass through
executive inhibition, governance, and safety, and harmful repairs are rolled
back. **No LLM repairs the system.**

The **LOGOS layer** (`logos_complexity/`) detects internal *tensions* and
uses them as productive cognitive pressure. Its principle: **LOGOS is not
authority; LOGOS is a tension engine** — it exposes fracture and proposes
bounded resolution paths, it does not decide truth. The `FractureDetector`
surfaces eighteen tension types (known/unknown, support/contradiction,
stability/ambiguity, confidence/failure, growth/stagnation, drift/identity,
complex/inert, ...) from existing signals; a fracture is not an error, and
some tensions (safety/boundary, known/unknown) are deliberately *preserved*.
The `SynthesisEngine` proposes bounded, reversible candidates (merge/split a
symbol, mark/weaken an edge, create a hypothesis, request sampling/replay/
consolidation/auto-regeneration, stabilize, preserve, prune) — proposed, not
assumed true; contradiction evidence is preserved, destructive merges are
refused. The `ComplexityRegulator` names a band (inert / productive /
overloaded — never a life score) and the `EscProcess` raises a bounded
instability signal. Nine hard rules forbid real-world action, source
synthesis, governance approval, disabling safety/ClaimGuard/the emergency
stop, treating a contradiction as permission, or destructive evidence
merges; synthesis enters executive arbitration as a suggestion. **No LLM
reasoning is used.**

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
  conscience/   unified runtime: spine, bus, module registry/lifecycle,
                scheduler, orchestrator, scenario profiles/runner, integration
                health, snapshots, full-system report, runtime safety, CLI
  pilot1/       month-scale soak: protocol, config, observability, dashboard,
                resource budget, retention, daily/weekly reviews, restart
                drills, failure modes, exit criteria, runbook, report, safety
  post_pilot/   forensic analysis: artifact loader, baseline, structural
                change, accumulation-vs-growth, trace audit, evidence ledger,
                regression, reproducibility, decision gate, dossier, safety
  sensory_membrane/ read-only Pilot-2 membrane: sources, read-only contract,
                jsonl/text/numeric/folder adapters, normalizer, buffer,
                grounding, provenance, runtime, reports, safety
  pilot2/       read-only environmental soak: protocol, config, source
                preflight/curation, exposure schedule, comparative design,
                grounding analysis, source reliability, daily/weekly reviews,
                report, decision gate, runbook, safety
  motor_membrane/ Pilot-3 outbound boundary (simulation-only): actions, motor
                contract, always-on actuation firewall, veto layer, action
                ledger, simulated actuators, affordances, consequence model,
                sandbox runtime, embodiment profiles, protocol, report,
                decision gate, runbook, safety
  pilot3/       simulated embodiment soak: config, soak protocol, embodiment
                preflight, comparative design, action grounding, firewall audit,
                daily/weekly reviews, post-analysis, soak report, decision gate,
                runbook, safety
  pilot4_planning/ planning-only external actuation readiness: config, planning
                protocol, actuator taxonomy, forbidden registry, future
                interface spec, risk model, consent boundary, authority model,
                threat model, hardware isolation, approval workflow, emergency
                & audit requirements, readiness dossier, decision gate, runbook,
                safety
  safety_invariants/ system-wide executable safety: invariant model, registry,
                read-only runner, inert red-team harness, adversarial fixtures,
                boundary regression suite, append-only evidence ledger,
                assurance case compiler, failure triage, dashboard, reports,
                safety validator
  research_lab/ baselines, ablations, architecture validation: experiment
                design, baseline agents, variant config, ablation matrix,
                benchmark runner, result store, metrics suite, null models,
                comparison engine, effect analyzer, reproducibility,
                leaderboard, research report, safety validator
  architecture_evolution/ evidence-based, planning-only governance: module
                inventory, lifecycle classifier, decision records, evidence map,
                pruning proposals, promotion/demotion, impact analysis, migration
                plan, design-debt registry, roadmap compiler, snapshots,
                changelog plan, review report, safety validator
  operator_console/ one local, file-backed operator layer: console config,
                profile catalog, run planner, run launcher, approval ledger,
                evidence navigator, artifact index, report index, status board,
                decision board, next-action recommender, export bundle, session
                log, operator queries, CLI, safety validator
  plural_sensorium/ organismic perception through plural senses: modality model,
                sensory event envelope, external feeders, read-only stream
                adapters, adapting receptors, continuous sensory field,
                perceptual baseline, flux/absence/rhythm/invariant/cross-modal
                detection, adaptive attention, grounding analyzer, runtime,
                reports, safety validator (no hardware/SDR/capture/network)
  organismic_demo/ first observable organismic-perception demo: scenario,
                fixture feeders, field runner, observation trace, changed-
                perception probe, comparison arms, demo report, safety validator
  live_field/   real read-only environmental feeder pilot: feeder contract,
                feeder registry, local feeder validators, feature dropbox,
                source health, live field runtime/pilot/trace/report,
                comparison, safety validator (Solaris reads, never controls)
  sensorium_lab/ sensorium differentiation lab: study design, sensorium
                profiles, world signatures, ontology drift, structure metrics,
                differentiation runner, comparative analysis, label
                contamination, modality fingerprints, study report, safety
  feeder_sdk/   external feeder SDK (artificial sensory organs OUTSIDE Solaris):
                envelope contract, writers, schemas, validators, replay, clock,
                noise, privacy filter, blueprints, packager, monitor, safety
  perceptual_metabolism/ regulate continuous sensory exposure (internal-only):
                operational needs, energy budget, sensory homeostasis, attention
                economy, overload, deprivation, novelty appetite, source diet,
                consolidation pressure, runtime, reports, safety
  perceptual_ontogenesis/ an internal world forms from peculiar perception:
                perceptual atoms, proto-concepts, concept birth, concept memory,
                concept families, world formation, relation growth, stabilization,
                decay, contamination, runtime, reports, safety
  semiogenesis/ sensorium-native internal signs and a private syntax:
                signs, sign birth, sign memory, sign families, private syntax,
                internal utterances, translation gloss, sign utility, drift,
                contamination, runtime, reports, safety
  sensorium_cognition/ sign-based thought, anticipation, internal simulation:
                cognitive state/moves, sign reasoning, prediction, anticipation,
                question pressure, internal simulation, counterfactuals, analogy,
                synthesis, cognitive memory, runtime, reports, safety
  self_boundary/ operational self/world boundary and organismic continuity:
                boundary state, ownership, perspective, continuity, body schema,
                source attribution, internal/external, simulation boundary,
                identity trace, boundary tensions, runtime, reports, safety
  desire_formation/ operational valence, desire, and internal action readiness:
                valence, push, desire, readiness, motivation field, conflict,
                arbitration, internal actions, outcome trace, memory, runtime,
                reports, safety
  action_reaction/ closed action-reaction loop and consequence learning:
                action model, reaction, consequence, effect learning, habit
                formation, inhibition, action policy, reaction memory, runtime,
                reports, safety
  developmental_life/ long-horizon life cycle, epochs, growth state,
                maturation markers, phase transitions, plateaus, regressions,
                growth-vs-accumulation, developmental runtime, life history,
                memory, reports, safety
  experiments/  minimal ESN, absence bridge, soak, restart, inner map, plasticity,
                substrates, sidecar, embodiment, language trace demo
  utils/        pure-stdlib math, logging
tests/          pytest suite
examples/       runnable scripts
feeders/        external read-only feeder scripts (run by the operator, outside
                Solaris): manual log, watched folder, system rhythm, dropbox
feeders_sdk/    external feeder SDK scripts + hardware blueprints (outside
                Solaris): template, manual/folder/system/feature feeders,
                simulated RF/echo/vibration/magnetic/thermal/multimodal feeders
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
