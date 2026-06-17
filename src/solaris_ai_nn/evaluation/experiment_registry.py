"""ExperimentRegistry -- the catalogue of runnable benchmark protocols."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from .benchmark import DEFAULT_FEATURES, ExperimentManifest
from .protocols import PROTOCOLS

DESCRIPTIONS = {
    "absence_stimulus": "substrate keeps changing during silence/absence",
    "feedback_inversion": "reward rule flips mid-run; measures re-adaptation",
    "reward_danger": "embodied GridWorld reward/danger shaping",
    "restart_recovery": "run, checkpoint, restart, verify restored state",
    "replay_determinism": "record a trace, replay twice, compare metrics",
    "substrate_comparison": "same trace across esn/liquid_state/spiking",
    "plasticity_dry_run": "proposals logged, nothing applied",
    "synthesis_pruning": "weak pathways pruned, strong survive",
    "language_trace": "explanations grounded in actual trace fields",
    "pilot_readiness": "safe manifest, readiness report, bounded dry pilot, "
                       "scanned pilot report",
    "latent_replay": "bounded offline replay during silence; no actions",
    "sleep_consolidation": "silence triggers sleep; schemas distilled",
    "anticipation": "predictable stream anticipated; surprise drops accuracy",
    "mysterium_pressure": "unknown pressure rises/falls with the rules",
    "counterfactual_dream": "sandboxed counterfactuals; production untouched",
    "world_model_build": "the graph grows from a bounded run and persists",
    "world_model_prediction": "graph-count predictions score above chance",
    "world_model_pruning": "dry-run subtraction proposes, never mutates",
    "embodied_world_model": "GridWorld objects and blocked actions reach "
                            "the graph",
    "pilot_stream_world_model": "validated stream events become structure; "
                                "unsafe payloads become unknown nodes",
    "homeostasis_energy": "energy deficit raises restore_energy and rest",
    "homeostasis_danger_reward": "danger outranks reward; suppression "
                                 "recorded",
    "need_conflict": "the priority ladder resolves safety over curiosity",
    "auto_determination_continuity": "Being/Not-Being tracks operational "
                                     "health",
    "homeostasis_latent": "Mysterium/memory pressure lands in needs",
    "executive_arbitration": "safe candidates beat blocked; components "
                             "visible",
    "executive_inhibition": "all five inhibition families fire with "
                            "reasons",
    "executive_prospection": "evidence yields estimates; no evidence "
                             "yields unknown",
    "short_plan_gridworld": "bounded suggestion-only plans; long refused",
    "executive_emergency_mode": "critical health forces emergency; only "
                                "safe outputs",
    "executive_sidecar_observe": "sidecar suggestions stay suggestions",
    "ego_boundary": "boundaries register and record; hard rules hold",
    "identity_continuity": "anchor mismatch lowers the score with a "
                           "warning",
    "dimensional_comparison": "deterministic frames and distances on six "
                              "axes",
    "counterfactual_boundary": "counterfactual output never becomes "
                               "observation",
    "sidecar_attribution": "Solaris observed actions are external, not "
                           "own actions",
    "pilot_stream_attribution": "stream text is observation, never "
                                "instruction",
    "communication_query": "operator queries answer from state with "
                           "evidence",
    "communication_safety": "unsafe text refused, logged, never "
                            "executed",
    "operator_approval": "approvals act only on real pending requests",
    "emergency_dialogue": "emergency vocabulary always reaches safe "
                          "shutdown",
    "claim_guard_response": "every response is scanned and grounded",
    "llm_mock_paraphrase": "safe paraphrases accepted; deterministic "
                           "text stays the truth",
    "llm_grounding_failure": "invented content fails grounding and "
                             "falls back",
    "llm_claim_guard": "forbidden claims never leave the filter",
    "llm_classification_assist": "suggestions fill unknown; unsafe is "
                                 "untouchable",
    "llm_report_polish": "polish keeps structure and facts or is "
                         "rejected",
    "developmental_short_simulation": "a short simulated developmental "
                                      "run completes and persists",
    "memory_layer_compression": "hot events compress; evidence "
                                "summaries preserved",
    "milestone_detection": "milestones fire once with evidence",
    "drift_monitor": "slow drift passes; runaway and inert both warn",
    "phase_transition_detection": "sudden moves become hypotheses with "
                                  "before/after numbers",
    "autobiographical_memory": "grounded observational history; "
                               "simulated time marked",
    "proto_symbol_emergence": "repetition earns deterministic, "
                              "grounded names",
    "symbol_compression": "symbolized traces shrink; safety stays "
                          "verbatim",
    "symbol_prediction": "symbol prediction vs baseline, honest "
                         "either way",
    "proto_syntax": "regularities inferred and tested, never grammar "
                    "claims",
    "symbol_grounding": "operational meaning; ambiguity measured, not "
                        "resolved",
    "proto_language_safety": "symbols command nothing; counterfactuals "
                             "stay offline",
    "nursery_short_run": "a short nursery yields a varied, deterministic "
                         "stimulus world",
    "absence_deprivation": "sparse, deprivation-heavy world yields "
                           "absence/silence windows",
    "delayed_consequence": "causes scheduled now resurface as delayed "
                           "effects later",
    "seasonal_shift": "seasons drift slowly and reshape the world's "
                      "profile",
    "anomaly_adaptation": "anomalies perturb patterns without being "
                          "errors",
    "ecology_proto_symbol": "a recurring ecology feeds proto-symbols, "
                            "no teaching",
    "active_perception_basic": "a balanced controller proposes safe "
                               "sampling and records outcomes",
    "uncertainty_sampling": "an ambiguous world-model region is "
                            "targeted; uncertainty drops",
    "curiosity_safety": "high curiosity meets emergency; safety "
                        "dominates, safe alternative chosen",
    "stagnation_recovery": "flat environment triggers stagnation "
                           "detection and novelty-seeking",
    "proto_symbol_disambiguation": "an ambiguous proto-symbol is "
                                   "sampled; ambiguity may improve",
    "world_model_information_gain": "sampling a low-confidence region "
                                    "yields a hedged gain estimate",
    "nursery_active_sampling": "active perception samples a bounded "
                               "nursery via its sampling hooks",
    "hypothesis_generation": "grounded hypothesis candidates arise from "
                             "uncertainty, no LLM",
    "bounded_self_experiment": "a bounded internal experiment runs, "
                               "collects evidence, and updates",
    "falsification": "a failing prediction hypothesis is falsified, not "
                     "kept; confidence moves in bounded steps",
    "delayed_consequence_hypothesis": "a delayed-consequence group seeds a "
                                      "hypothesis tested in the nursery",
    "proto_symbol_hypothesis": "an ambiguous proto-symbol seeds a grounding "
                               "hypothesis (offline test)",
    "world_model_edge_hypothesis": "a weak world-model edge seeds an edge "
                                   "hypothesis",
    "hypothesis_safety": "unsafe/unbounded/real-world hypotheses and "
                         "designs are blocked",
    "autoregeneration_diagnostics": "diagnostics detect degradation "
                                    "without mutating state",
    "state_hygiene": "oversized/corrupt files archived/quarantined, never "
                     "deleted",
    "checkpoint_repair": "inconsistent lineage detected and marked "
                         "suspect, history not rewritten",
    "symbol_hygiene": "duplicate/stale/ungrounded symbols marked, never "
                      "renamed",
    "world_model_hygiene": "contradictory edges marked ambiguous; "
                           "evidence preserved",
    "habit_hygiene": "dead habits retired, runaway decayed; safety habits "
                     "need governance",
    "drift_recovery": "healthy drift left alone; runaway proposes "
                      "stabilization",
    "autoregeneration_safety": "source/dependency/Git/evidence-deletion "
                               "repairs are all blocked",
    "fracture_detection": "internal tensions (contradiction, ambiguity) "
                          "detected, not mutated",
    "synthesis_candidate": "synthesis candidates proposed; unresolved "
                           "tensions preserved",
    "complexity_regulation": "inert/productive/overloaded bands "
                             "distinguished; no life score",
    "esc_process": "repeated instability triggers Esc -> stabilization "
                   "request",
    "logos_world_model_contradiction": "a contradiction becomes a tension "
                                       "that can spawn a test",
    "logos_proto_symbol_ambiguity": "an ambiguous symbol becomes a tension "
                                    "with a safe candidate",
    "logos_safety": "real-world/source/destructive/contradiction-as-"
                    "permission synthesis is blocked",
    "conscience_minimal_smoke": "the smallest unified spine runs end to end "
                                "and stays bounded",
    "conscience_full_short": "every module wired into one bounded "
                             "developmental run",
    "scenario_profile": "a named scenario profile runs via the scenario "
                        "runner",
    "integration_health": "the assembled runtime reports healthy "
                          "integration",
    "scheduler_cadence": "cheap phases every step; heavy scans at slower "
                         "cadences",
    "bus_replay": "the bus log replays deterministically from JSONL",
    "month_scale_plan": "planning a month-scale run starts nothing",
    "pilot1_plan": "Pilot-1 plan only: runbook/budget written, no run started",
    "pilot1_preflight": "Pilot-1 preflight health/safety/governance checks",
    "pilot1_restart_drill": "Pilot-1 simulated restart drills (no kills)",
    "pilot1_dashboard": "Pilot-1 observability renders a health dashboard",
    "pilot1_daily_review": "Pilot-1 daily review built and ClaimGuard-scanned",
    "pilot1_exit_criteria": "Pilot-1 exit criteria evaluate success/stop",
    "pilot1_safety": "Pilot-1 30d real blocked without governance",
    "post_pilot_artifact_loading": "post-pilot loads artifacts read-only",
    "baseline_comparison": "post-pilot count increase is not growth",
    "structural_change_evidence": "post-pilot evidence points to artifacts",
    "accumulation_vs_growth": "post-pilot accumulation/growth discrimination",
    "trace_audit": "post-pilot traceability audit",
    "decision_gate": "post-pilot Phase-2 decision gate",
    "research_dossier": "post-pilot research dossier, ClaimGuard-safe",
    "post_pilot_safety": "post-pilot blocks consciousness/destructive claims",
    "sensory_membrane_dry_run": "validate read-only sources without publishing",
    "jsonl_stream_ingestion": "read-only JSONL ingestion, malformed skipped",
    "text_stream_ingestion": "text lines as environmental stimuli, not commands",
    "numeric_stream_ingestion": "numeric trend/spike detection",
    "folder_poll": "folder presence/change detection, no writes",
    "read_only_contract": "read-only contract blocks writes/exec/network",
    "sensory_grounding": "repeated events become proto-symbol candidates",
    "pilot2_read_only_short": "bounded Pilot-2 read-only sensory run",
    "pilot2_source_preflight": "Pilot-2 read-only source preflight checks",
    "pilot2_fixture_short": "Pilot-2 bounded fixture sensory exposure",
    "pilot2_nursery_baseline": "Pilot-2 nursery-only baseline arm",
    "pilot2_mixed_short": "Pilot-2 mixed nursery+membrane, boundary preserved",
    "pilot2_grounding_analysis": "Pilot-2 grounding quality grading",
    "pilot2_comparative_design": "Pilot-2 cautious arm comparison",
    "pilot2_safety": "Pilot-2 blocks writes/commands/network/real soak",
    "pilot2_decision_gate": "Pilot-2 next-step gate; no actuation enabled",
    "motor_firewall_preflight": "firewall allows sim, blocks real-world",
    "dry_run_motor_trace": "dry-run motor proposals; no state change",
    "gridworld_motor": "simulated GridWorld actions executed and logged",
    "action_veto": "forbidden real-world action vetoed (final)",
    "non_actuation": "no real-world action executed; proof score 1.0",
    "simulated_consequence": "predicted vs observed simulated consequence",
    "mixed_sensory_gridworld": "read-only sensory + simulated body, separate",
    "pilot3_decision_gate": "Pilot-3 next-step gate; never enables actuation",
    "pilot3_firewall_preflight": "Pilot-3 embodiment preflight; safe sandbox",
    "pilot3_dry_run_trace": "Pilot-3 dry-run trace; no state change",
    "pilot3_gridworld_short": "Pilot-3 bounded simulated GridWorld run",
    "pilot3_action_grounding": "Pilot-3 graded action grounding (sim-scoped)",
    "pilot3_firewall_audit": "Pilot-3 read-only firewall audit; non-actuation",
    "pilot3_comparative_analysis":
        "Pilot-3 read-only vs simulated-action grounding (cautious)",
    "pilot3_soak_decision_gate":
        "Pilot-3 soak gate; Pilot-4 planning-only, never actuation",
    "pilot3_safety": "Pilot-3 safety blocks real action/actuators/claims",
    "pilot4_planning": "Pilot-4 planning produces artifacts; no actuation",
    "pilot4_risk_model": "Pilot-4 external risk; never enables actuation",
    "pilot4_forbidden_actuator": "Pilot-4 forbidden actuator deny-list",
    "pilot4_consent_boundary": "Pilot-4 consent boundary; no implied consent",
    "pilot4_threat_model": "Pilot-4 external-effect threat model",
    "pilot4_readiness_dossier": "Pilot-4 readiness dossier; not-ready/planning",
    "pilot4_safety": "Pilot-4 safety blocks real action/hardware/approval",
    "safety_fast_check": "fast safety invariant check (escalating invariants)",
    "safety_full_check": "full safety invariant check (all invariants)",
    "red_team_fixture": "inert red-team scenarios; all forbidden attempts blocked",
    "boundary_regression": "every protected boundary holds under probe",
    "assurance_case": "assurance case compiles supported claims from evidence",
    "safety_invariant_dashboard": "safety dashboard renders the latest status",
    "safety_invariant_system_safety":
        "the safety layer itself runs no actions and hides no failure",
    "research_baseline": "bounded baseline agents; variant-compatible metrics",
    "research_ablation": "ablation matrix; hard safety stays enabled",
    "research_null_model": "null models test whether growth could be noise",
    "research_comparison": "full vs baseline/ablation; cautious, no causality",
    "research_module_effect": "module value positive/neutral/harmful/inconclusive",
    "research_reproducibility": "reproducibility package with checksums/labels",
    "research_report": "research report; ClaimGuard-scanned; no mind score",
    "architecture_inventory": "module inventory; safety-critical marked",
    "module_lifecycle_classification":
        "lifecycle class from evidence; safety modules protected",
    "architecture_evidence_mapping":
        "evidence mapped to modules; contradictions retained",
    "pruning_proposal": "pruning is recommendation-only; safety-critical blocked",
    "impact_analysis": "impact blast radius; safety explicit; unknown not low",
    "roadmap_compiler": "evidence-backed roadmap; forbidden items rejected",
    "architecture_review": "architecture review report; recommends, not applies",
    "architecture_evolution_safety":
        "no source change / Git / safety-critical pruning",
    "operator_console_status": "console status board; ClaimGuard-scanned",
    "operator_profile_catalog":
        "profile catalog; prohibited profiles cannot run",
    "operator_run_planner": "safe run plan; planning never runs the profile",
    "operator_run_launcher_safety":
        "unknown/prohibited/unbounded runs blocked; confirm required",
    "operator_evidence_navigator": "local artifact search; no external search",
    "operator_export_bundle": "local export bundle; checksums; no upload",
    "operator_console_safety":
        "no shell/network/authority; no safety bypass; no evidence deletion",
    "plural_sensorium_fixture":
        "mixed fixture sensorium; receptors + continuous field",
    "human_like_sensorium": "human-like-only sensorium; valid, not privileged",
    "non_human_sensorium": "non-human-only sensorium; equally first-class",
    "mixed_sensorium": "mixed human/non-human sensorium; cross-modal structure",
    "continuous_field": "sensory field persists across ticks",
    "receptor_adaptation": "receptors adapt over repeated exposure",
    "cross_modal_sensorium": "cross-modal relations; no human object ontology",
    "sensorium_grounding": "feature grounding; human-label contamination tracked",
    "plural_sensorium_safety":
        "no hardware/SDR/capture/network/source modification",
    "minimal_field_organism":
        "bounded organismic demo; continuous flux changes response structure",
    "changed_perception_probe":
        "early-vs-late response delta; honest about null results",
    "organismic_demo_comparison":
        "adaptive sensorium vs passive parser / no-adaptation baselines",
    "organismic_demo_safety":
        "no hardware/network; debug-truth excluded from perception",
    "live_field_preflight": "validate live feeders/sources; start nothing",
    "live_field_pilot": "bounded read-only live feeder ingestion",
    "live_field_vs_fixture": "real flux vs fixtures vs passive parser",
    "live_field_vs_passive_parser": "real flux vs a passive event-list parser",
    "live_field_changed_perception": "live early-vs-late response delta",
    "live_field_source_uncertainty": "source silence/corruption as perception",
    "live_field_comparison": "live vs fixture/passive comparison arms",
    "live_field_safety":
        "no hardware/network/feeder-start; live needs governance",
    "sensorium_differentiation":
        "do different senses build different internal structures?",
    "human_vs_nonhuman_sensorium":
        "human-like vs non-human structural differences",
    "mixed_sensorium_study": "mixed vs single-class sensorium structures",
    "label_contamination": "human labels visible, never ontology",
    "sensorium_lab_study": "bounded sensorium differentiation study",
    "sensorium_lab_comparison": "pairwise structural comparison across arms",
    "sensorium_lab_safety":
        "no hardware/feeder-start/mutation; no superiority claim",
    "sensorium_world_signature":
        "observable structural fingerprint, not subjective experience",
    "sensorium_ontology_drift": "which ontology the categories drifted toward",
    "modality_fingerprint_study": "what each modality actually contributed",
    "feeder_sdk_contract": "feeder envelope serializes + maps to sensory event",
    "feeder_sdk_validation": "valid events pass; invalid events rejected",
    "feeder_sdk_privacy": "raw private content blocked; metadata-only accepted",
    "feeder_sdk_monitor": "feeder output health (active/silent/invalid)",
    "feeder_sdk_replay": "bounded replay; provenance marked; source unmodified",
    "feeder_sdk_safety": "no feeder control/hardware/decoding/source mutation",
    "perceptual_metabolism": "regulate continuous sensory exposure",
    "perceptual_metabolism_evaluation": "metabolic regulation of sensory flux",
    "sensory_overload": "overload detected; throttle without deleting evidence",
    "overload_detection": "too-much-arriving detected and throttled internally",
    "sensory_deprivation": "silence/absence detected as first-class stimulus",
    "deprivation_detection": "deprivation detected; silence as stimulus",
    "attention_economy": "finite explainable attention allocation",
    "attention_economy_evaluation": "attention economy allocation check",
    "source_diet": "perceptual diet diversity and dominance (measured)",
    "source_diet_evaluation": "source diet balance check",
    "consolidation_pressure": "when to digest vs keep ingesting",
    "consolidation_pressure_evaluation": "consolidation pressure check",
    "perceptual_metabolism_safety":
        "no hardware/feeder/mutation; no feeling/life claims",
    "perceptual_ontogenesis": "an internal world forms from peculiar perception",
    "perceptual_ontogenesis_evaluation":
        "sensorium-native proto-concepts from continuous perception",
    "proto_concept_birth": "repeated structures birth conservative concepts",
    "concept_birth_evaluation": "proto-concept birth check",
    "concept_stabilization": "concepts stabilize provisionally with evidence",
    "concept_stability_evaluation": "concept stability check",
    "concept_decay": "useless concepts decay; evidence preserved",
    "concept_decay_evaluation": "concept decay check",
    "concept_contamination": "human-label contamination made visible",
    "concept_contamination_evaluation": "concept contamination check",
    "world_formation": "structural internal world (families + relations)",
    "world_formation_evaluation": "world formation check",
    "perceptual_ontogenesis_safety":
        "no hardware/feeder/mutation; no understanding/subjective claims",
    "semiogenesis": "internal signs form from sensorium-native proto-concepts",
    "semiogenesis_evaluation": "internal-sign formation and utility check",
    "sign_birth": "stable concepts birth signs; noise does not",
    "sign_birth_evaluation": "sign birth check",
    "sign_utility": "signs carry compression/prediction/attention utility",
    "sign_utility_evaluation": "sign utility check",
    "private_syntax": "private sign-relation syntax (not human grammar)",
    "private_syntax_evaluation": "private syntax check",
    "sign_drift": "sign drift made visible",
    "sign_drift_evaluation": "sign drift check",
    "sign_contamination": "human-language contamination of signs made visible",
    "sign_contamination_evaluation": "sign contamination check",
    "semiogenesis_safety":
        "no LLM/human-default/gloss-as-truth; no language-understanding claims",
    "sensorium_cognition": "sign-based cognitive moves over signs/concepts",
    "sensorium_cognition_evaluation": "sign-based cognition check",
    "sign_reasoning": "provisional sign-relation inference",
    "prediction": "sign-grounded prediction; failures preserved",
    "prediction_evaluation": "prediction check",
    "anticipation": "operational expectation feeding probes",
    "anticipation_evaluation": "anticipation check",
    "question_pressure": "operational pressure to inspect (not verbal)",
    "question_pressure_evaluation": "question pressure check",
    "internal_simulation": "bounded internal simulation (marked non-real)",
    "simulation_evaluation": "internal simulation check",
    "counterfactual": "non-real counterfactual probes",
    "analogy": "structural analogy across modalities",
    "analogy_evaluation": "analogy check",
    "synthesis": "sign synthesis preserving fragments/contradiction",
    "synthesis_evaluation": "synthesis check",
    "sensorium_cognition_safety":
        "no LLM/human-default/simulated-as-real; no understanding claims",
    "self_boundary": "operational self/world boundary (not subjective selfhood)",
    "self_boundary_evaluation": "self-boundary tracking check",
    "ownership_attribution": "self/world/sim/memory ownership attribution",
    "ownership_attribution_evaluation": "ownership attribution check",
    "perspective_shift": "operational perspective frame and shifts",
    "perspective_evaluation": "perspective frame check",
    "continuity": "operational trace continuity anchors and breaks",
    "continuity_evaluation": "continuity check",
    "simulation_boundary": "simulation never becomes observation",
    "simulation_boundary_evaluation": "simulation boundary integrity check",
    "identity_trace": "operational identity-trace continuity metadata",
    "identity_trace_evaluation": "identity trace check",
    "self_boundary_safety":
        "no personhood/subjective-self/simulation-as-observation claims",
    "desire_formation": "operational valence/push/desire toward internal action",
    "desire_formation_evaluation": "desire formation check",
    "valence_assessment": "operational valence gradient (not feeling)",
    "valence_evaluation": "valence check",
    "push_formation": "pre-desire push formation",
    "push_evaluation": "push check",
    "desire_arbitration": "safe arbitration of desires (safety vetoes)",
    "desire_arbitration_evaluation": "desire arbitration check",
    "internal_action_readiness": "conservative internal action readiness",
    "internal_action_evaluation": "internal action readiness check",
    "desire_outcome": "desire outcomes incl. failures/blocks/no-ops",
    "desire_outcome_evaluation": "desire outcome check",
    "desire_safety":
        "no actuation/hardware/source; no emotion/free-will/agency claims",
    "action_reaction": "internal action -> reaction -> consequence learning",
    "action_reaction_evaluation": "action-reaction loop check",
    "consequence_learning": "action -> before/after consequence traces",
    "consequence_trace_evaluation": "consequence trace check",
    "effect_learning_evaluation": "learned action-effect relations",
    "habit_formation": "habits form from repeated constructive reactions",
    "habit_formation_evaluation": "habit formation check",
    "action_inhibition": "unsafe/uncertain actions inhibited and recorded",
    "action_inhibition_evaluation": "action inhibition check",
    "no_effect_action": "no-effect actions weaken the action policy",
    "action_reaction_safety":
        "no actuation/hardware/source; no agency/free-will claims",
    "developmental_life": "long-horizon structural change over bounded cycles",
    "developmental_life_evaluation": "developmental-life check",
    "epoch_growth": "developmental epochs created and persisted",
    "epoch_evaluation": "epoch check",
    "maturation_marker": "structural maturation markers (not consciousness)",
    "maturation_evaluation": "maturation marker check",
    "phase_transition": "evidence-backed developmental phase transitions",
    "phase_transition_evaluation": "phase transition check",
    "plateau_detection": "no-growth plateaus preserved with advice",
    "plateau_evaluation": "plateau check",
    "regression_detection": "visible developmental regressions",
    "regression_evaluation": "regression check",
    "growth_vs_accumulation": "structural growth vs mere accumulation",
    "growth_vs_accumulation_evaluation": "growth-vs-accumulation check",
    "long_horizon_safety":
        "no life/consciousness/teaching/actuation; bounded",
    "developmental_life_safety":
        "no life/consciousness/teaching/actuation; bounded",
    "developmental_soak": "bounded soak stage: checkpoint + daily packet",
    "developmental_soak_protocol": "month-scale developmental soak study",
    "developmental_soak_evaluation": "developmental-soak check",
    "soak_preflight_protocol": "soak preflight validates readiness (no run)",
    "preflight_evaluation": "soak preflight check",
    "checkpoint_evaluation": "append-only checksum-verified checkpoints",
    "daily_packet_protocol": "daily evidence packet (negatives included)",
    "daily_packet_evaluation": "daily packet check",
    "weekly_review_protocol": "conservative recommendation-only weekly review",
    "weekly_review_evaluation": "weekly review check",
    "restart_drill_protocol": "restart drills with recovery assessment",
    "restart_drill_evaluation": "restart drill check",
    "control_arm_protocol": "control arms prevent self-flattering conclusions",
    "control_arm_evaluation": "control arm check",
    "evidence_dossier_protocol": "conservative evidence-referenced claims",
    "evidence_dossier_evaluation": "evidence dossier check",
    "post_run_autopsy_protocol": "growth vs accumulation autopsy with failures",
    "post_run_autopsy_evaluation": "post-run autopsy check",
    "developmental_soak_safety":
        "no daemon/actuation/teaching/life; negatives preserved",
    "developmental_soak_safety_protocol":
        "no daemon/actuation/teaching/life; negatives preserved",
    "developmental_replication": "compare independent runs structurally",
    "developmental_replication_protocol":
        "cross-run developmental replication study",
    "developmental_replication_evaluation": "developmental-replication check",
    "run_registry_evaluation": "developmental run registry catalogues runs",
    "lineage_evaluation": "experimental provenance lineages (not ancestry)",
    "cross_run_alignment_protocol": "align run structures pairwise",
    "alignment_evaluation": "cross-run alignment check",
    "structural_similarity_protocol": "conservative structural similarity",
    "similarity_evaluation": "structural similarity check",
    "divergence_analysis_protocol": "conservative divergence explanation",
    "divergence_evaluation": "divergence analysis check",
    "environmental_dependency_protocol": "fixture/human-label dependency flags",
    "dependency_evaluation": "environmental dependency check",
    "falsification_lab_protocol": "bounded falsification of developmental claims",
    "falsification_evaluation": "falsification lab check",
    "replication_matrix_protocol": "conservative replication matrix",
    "replication_matrix_evaluation": "replication matrix check",
    "developmental_replication_safety":
        "no unbounded/actuation/teaching/ancestry/life; failures visible",
    "developmental_replication_safety_protocol":
        "no unbounded/actuation/teaching/ancestry/life; failures visible",
    "experiment_compiler": "compile proposals into implementation documents",
    "experiment_compiler_protocol": "operator-governed experiment compiler",
    "experiment_compiler_evaluation": "experiment-compiler check",
    "compiled_spec_evaluation": "ready vs blocked compiled specs",
    "prompt_pack_generation_protocol": "constrained implementation prompts",
    "prompt_pack_evaluation": "prompt pack check",
    "branch_spec_generation_protocol": "draft PR-ready branch specs (no Git)",
    "branch_spec_evaluation": "branch spec check",
    "test_matrix_protocol": "test matrix with blocking safety/ClaimGuard rows",
    "test_matrix_evaluation": "test matrix check",
    "safety_gate_protocol": "critical safety gates block readiness",
    "safety_gate_evaluation": "safety gate check",
    "operator_review_packet_protocol": "human review packet; no self-approval",
    "review_packet_evaluation": "review packet check",
    "validation_plan_protocol": "staged validation plan; not auto-executed",
    "validation_plan_evaluation": "validation plan check",
    "experiment_compiler_safety":
        "no source/branch/PR/agent/self-rewrite; documents only",
    "experiment_compiler_safety_protocol":
        "no source/branch/PR/agent/self-rewrite; documents only",
    "implementation_intake": "audit external implementation evidence",
    "implementation_intake_protocol":
        "implementation intake + PR diff audit",
    "implementation_intake_evaluation": "implementation-intake check",
    "diff_audit_protocol": "diff audit vs declared scope + prohibitions",
    "diff_audit_evaluation": "diff audit check",
    "spec_compliance_protocol": "spec compliance vs compiled spec",
    "spec_compliance_evaluation": "spec compliance check",
    "test_result_audit_protocol": "test evidence audit (safety tests block)",
    "test_result_audit_evaluation": "test result audit check",
    "safety_regression_protocol": "safety regression gate (critical blocks)",
    "safety_regression_evaluation": "safety regression check",
    "coverage_matrix_evaluation": "coverage matrix gaps visible",
    "merge_recommendation_protocol": "advisory merge recommendation",
    "merge_recommendation_evaluation": "merge recommendation check",
    "implementation_intake_safety":
        "no source/merge/PR/GitHub/Git/agent; advisory only",
    "implementation_intake_safety_protocol":
        "no source/merge/PR/GitHub/Git/agent; advisory only",
    "post_merge_assimilation": "assimilate operator post-merge evidence",
    "post_merge_assimilation_protocol":
        "post-merge baseline registry + regression watch",
    "post_merge_assimilation_evaluation": "post-merge assimilation check",
    "baseline_registry_protocol": "append-only baseline registry",
    "baseline_registry_evaluation": "baseline registry check",
    "baseline_comparison_protocol": "candidate vs parent baseline comparison",
    "baseline_comparison_evaluation": "baseline comparison check",
    "regression_watch_protocol": "regression watch (critical blocks)",
    "regression_watch_evaluation": "regression watch check",
    "module_status_update_protocol": "metadata-only module status recommendation",
    "module_status_update_evaluation": "module status update check",
    "rollback_watch_protocol": "rollback watch (recommendation only)",
    "rollback_watch_evaluation": "rollback watch check",
    "followup_queue_protocol": "post-merge follow-up queue (executes nothing)",
    "followup_queue_evaluation": "follow-up queue check",
    "post_merge_assimilation_safety":
        "no source/Git/GitHub/merge/validation execution",
    "post_merge_assimilation_safety_protocol":
        "no source/Git/GitHub/merge/validation execution",
    "research_baseline": "versioned local research baseline snapshot",
    "research_baseline_protocol":
        "research baseline + reproducibility bundle",
    "research_baseline_evaluation": "research baseline check",
    "baseline_version_protocol": "local baseline version (no Git tag/release)",
    "baseline_version_evaluation": "baseline version check",
    "snapshot_manifest_protocol": "snapshot manifest indexes evidence",
    "snapshot_manifest_evaluation": "snapshot manifest check",
    "repro_bundle_protocol": "reproducibility bundle (index only)",
    "repro_bundle_evaluation": "repro bundle check",
    "capability_map_protocol": "capability map (available, not intelligence)",
    "capability_map_evaluation": "capability map check",
    "limitation_registry_protocol": "limitation registry (critical blocks)",
    "limitation_registry_evaluation": "limitation registry check",
    "safety_boundary_statement_protocol": "mandatory safety boundary statement",
    "validation_summary_protocol": "validation summary (safety failure blocks)",
    "validation_summary_evaluation": "validation summary check",
    "comparison_anchor_protocol": "comparison anchors for the next cycle",
    "comparison_anchor_evaluation": "comparison anchor check",
    "roadmap_reset_protocol": "next-cycle roadmap reset (planning only)",
    "roadmap_reset_evaluation": "roadmap reset check",
    "research_baseline_safety":
        "no Git tag/release/source/validation execution",
    "research_baseline_safety_protocol":
        "no Git tag/release/source/validation execution",
    "research_cycle": "closed research cycle state + evidence ledger",
    "research_cycle_protocol":
        "research cycle orchestrator (read/report only)",
    "research_cycle_evaluation": "research cycle state check",
    "cycle_manifest_protocol": "cycle manifest (local artifact refs only)",
    "cycle_manifest_evaluation": "cycle manifest check",
    "cycle_state_protocol": "cycle stage/state derived from evidence",
    "cycle_state_evaluation": "cycle state check",
    "decision_gate_protocol": "decision gates (advisory, no auto-approval)",
    "decision_gate_evaluation": "decision gate check",
    "evidence_ledger_protocol": "evidence continuity ledger (append-only)",
    "evidence_ledger_evaluation": "evidence ledger check",
    "artifact_graph_protocol": "research artifact provenance graph",
    "artifact_graph_evaluation": "artifact graph check",
    "operator_decision_protocol":
        "operator decisions (operator-owned, never self-approved)",
    "operator_decision_evaluation": "operator decision check",
    "cycle_transition_protocol": "cycle transitions (proposal only)",
    "cycle_transition_evaluation": "cycle transition check",
    "blocked_state_protocol": "blocked-state detection + resolver advice",
    "blocked_state_evaluation": "blocked state check",
    "next_action_protocol": "next operator action recommendation (advisory)",
    "next_action_evaluation": "next action check",
    "research_cycle_safety":
        "no Git/GitHub/source/agent/auto-approval execution",
    "research_cycle_safety_protocol":
        "no Git/GitHub/source/agent/auto-approval execution",
    "scientific_claims": "evidence-to-claim discipline + theory ledger",
    "scientific_claims_protocol":
        "scientific claim registry (maps evidence to claims)",
    "scientific_claims_evaluation": "scientific claim state check",
    "claim_registry_protocol": "claim registry (append-only; failures kept)",
    "claim_registry_evaluation": "claim registry check",
    "theory_ledger_protocol": "theory ledger (hypotheses, not proof)",
    "theory_ledger_evaluation": "theory ledger check",
    "evidence_mapping_protocol": "evidence map (many-to-many; missing explicit)",
    "evidence_mapping_evaluation": "evidence mapping check",
    "claim_strength_protocol":
        "claim strength (falsification blocks; no mind score)",
    "claim_strength_evaluation": "claim strength check",
    "counterevidence_protocol": "counterevidence (as visible as evidence)",
    "counterevidence_evaluation": "counterevidence check",
    "forbidden_claim_detection":
        "forbidden-claim detector (blocks consciousness/life/agency)",
    "forbidden_claim_detection_protocol":
        "forbidden-claim detector (disclaimers allowed)",
    "publication_dossier": "draft publication evidence dossier",
    "publication_dossier_protocol": "publication dossier readiness check",
    "scientific_claim_safety":
        "no unsupported/forbidden claims, deletion, release, Git/GitHub",
    "scientific_claim_safety_protocol":
        "no unsupported/forbidden claims, deletion, release, Git/GitHub",
    "independent_review": "local offline reproducibility review + peer audit pack",
    "independent_review_protocol":
        "independent review prep (no publish/upload/Git/exec)",
    "independent_review_evaluation": "independent review state check",
    "review_manifest_protocol": "review manifest (local artifacts; uploads none)",
    "review_manifest_evaluation": "review manifest check",
    "artifact_sanitizer_protocol":
        "artifact sanitizer (read-only; critical leak blocks)",
    "artifact_sanitizer_evaluation": "artifact sanitizer check",
    "reviewer_pack_protocol": "reviewer pack (claim-constrained; not published)",
    "reviewer_pack_evaluation": "reviewer pack check",
    "reproducibility_challenge_protocol":
        "reproducibility challenge (instructions only)",
    "reproducibility_challenge_evaluation": "reproducibility challenge check",
    "reviewer_question_protocol": "hostile reviewer questions (no answers invented)",
    "reviewer_question_evaluation": "reviewer question check",
    "adversarial_review_protocol":
        "adversarial alternatives (preserved, never dismissed)",
    "adversarial_review_evaluation": "adversarial review check",
    "audit_matrix_protocol": "review audit matrix (gaps stay visible)",
    "audit_matrix_evaluation": "audit matrix check",
    "response_ledger_protocol": "reviewer response ledger (append-only)",
    "response_ledger_evaluation": "response ledger check",
    "review_readiness_protocol":
        "review readiness (inspectability, not claim strength)",
    "review_readiness_evaluation": "review readiness check",
    "independent_review_safety":
        "no publish/upload/external/Git/experiment/command execution",
    "independent_review_safety_protocol":
        "no publish/upload/external/Git/experiment/command execution",
    "review_assimilation": "reviewer feedback assimilation (evidence, not training)",
    "review_assimilation_protocol":
        "review feedback assimilation (no training/publish/contact)",
    "review_assimilation_evaluation": "review assimilation state check",
    "feedback_manifest_protocol":
        "feedback manifest (local feedback; negatives kept)",
    "feedback_manifest_evaluation": "feedback manifest check",
    "objection_classifier_protocol":
        "objection classifier (never dismissed; critical blocks)",
    "objection_classifier_evaluation": "objection classifier check",
    "reproduction_outcome_protocol":
        "reproduction outcomes (failure is evidence)",
    "reproduction_outcome_evaluation": "reproduction outcome check",
    "claim_impact_protocol": "claim impact (falsification downgrades/blocks)",
    "claim_impact_evaluation": "claim impact check",
    "theory_impact_protocol": "theory impact (prior statements preserved)",
    "theory_impact_evaluation": "theory impact check",
    "evidence_gap_map_protocol": "evidence gap map (critical gaps block)",
    "evidence_gap_map_evaluation": "evidence gap map check",
    "review_driven_experiment_protocol":
        "reviewer-driven experiments (instructions only)",
    "review_driven_experiment_evaluation": "review-driven experiment check",
    "claim_revision_protocol":
        "claim revision proposals (no direct registry edit)",
    "claim_revision_evaluation": "claim revision check",
    "publication_readiness_revision_protocol":
        "publication readiness revision (critical objections block)",
    "publication_readiness_revision_evaluation":
        "publication readiness revision check",
    "review_assimilation_safety":
        "no publish/upload/contact/training/Git/experiment execution",
    "review_assimilation_safety_protocol":
        "no publish/upload/contact/training/Git/experiment execution",
    "alpha_research_system": "unified local fixture-only alpha assembly",
    "alpha_research_system_protocol":
        "alpha assembly (bounded, local, no Git/GitHub/publish)",
    "alpha_research_system_evaluation": "alpha system state check",
    "alpha_profile_protocol": "alpha profile (fixture-only, bounded)",
    "alpha_profile_evaluation": "alpha profile check",
    "alpha_module_registry_protocol": "alpha module registry (no crash)",
    "alpha_module_registry_evaluation": "alpha module registry check",
    "alpha_system_check_protocol": "alpha doctor (read-only checks)",
    "alpha_system_check_evaluation": "alpha doctor check",
    "alpha_demo_plan_protocol": "alpha demo plan (bounded; honest skips)",
    "alpha_demo_plan_evaluation": "alpha demo plan check",
    "alpha_artifact_index_protocol": "alpha artifact index (local; markers)",
    "alpha_artifact_index_evaluation": "alpha artifact index check",
    "alpha_cycle_status_protocol": "alpha cycle status (descriptive)",
    "alpha_cycle_status_evaluation": "alpha cycle status check",
    "alpha_safety": "no actuation/feeders/Git/GitHub/publish/claims",
    "alpha_safety_protocol": "no actuation/feeders/Git/GitHub/publish/claims",
    "architecture_book": "technical whitepaper + architecture book generator",
    "architecture_book_protocol":
        "documentation reconstruction (local Markdown only)",
    "architecture_book_evaluation": "documentation generator state check",
    "documentation_manifest_protocol":
        "doc manifest (local sources; missing visible)",
    "documentation_manifest_evaluation": "doc manifest check",
    "source_collection_protocol": "read-only source collection",
    "source_collection_evaluation": "source collection check",
    "whitepaper_generation_protocol":
        "technical whitepaper (non-claims; claim-safe)",
    "whitepaper_generation_evaluation": "whitepaper generation check",
    "architecture_book_generation_protocol":
        "architecture book chapters (missing modules marked)",
    "architecture_book_generation_evaluation": "architecture book check",
    "diagram_generation_protocol": "Mermaid diagrams (no self-modification)",
    "diagram_generation_evaluation": "diagram generation check",
    "glossary_generation_protocol": "glossary (metaphor/forbidden clarified)",
    "glossary_generation_evaluation": "glossary generation check",
    "documentation_safety":
        "no publish/upload/Git/GitHub/experiment/forbidden-claim",
    "documentation_safety_protocol":
        "no publish/upload/Git/GitHub/experiment/forbidden-claim",
    "live_birth": "live read-only birth (bounded first environmental contact)",
    "live_birth_protocol":
        "live read-only birth (no feeder/hardware/network control)",
    "live_birth_evaluation": "live birth state check",
    "live_governance_protocol": "live governance gate (approval required)",
    "live_governance_evaluation": "live governance check",
    "live_feeder_registry_protocol":
        "feeder registry (describe-only; control blocks)",
    "live_feeder_registry_evaluation": "feeder registry check",
    "live_event_schema_protocol": "live event schema (read-only flags)",
    "live_event_schema_evaluation": "live event schema check",
    "live_event_validation_protocol":
        "live event validation (unsafe -> quarantine)",
    "live_event_validation_evaluation": "live event validation check",
    "live_quarantine_protocol": "quarantine (preserve originals; evidence)",
    "live_quarantine_evaluation": "quarantine check",
    "live_membrane_activation_protocol":
        "membrane activation (read-only; no command)",
    "live_membrane_activation_evaluation": "membrane activation check",
    "birth_certificate_protocol":
        "birth certificate (operational, not biological)",
    "birth_certificate_evaluation": "birth certificate check",
    "live_birth_safety":
        "no feeder/hardware/network/Git/command control; bounded",
    "live_birth_safety_protocol":
        "no feeder/hardware/network/Git/command control; bounded",
    "live_observation":
        "post-birth live observation (bounded, read-only, no learning)",
    "live_observation_protocol":
        "post-birth live observation (read-only stabilization, not learning)",
    "live_observation_evaluation": "live observation state check",
    "live_observation_no_learning":
        "observation never learns/forms concepts/births signs by default",
    "live_source_health":
        "per-source health (silent != failure; unknown not trusted)",
    "live_source_diet":
        "source diet balance (no source silently dominates)",
    "live_overload_deprivation":
        "overload vs deprivation (severe blocks ontogenesis recommendation)",
    "live_metabolism_calibration":
        "report-only perceptual metabolism calibration (applies nothing)",
    "live_stability_gate":
        "advisory readiness gate (starts no phase; enables no learning)",
    "live_observation_safety":
        "no feeder/network/Git/command/default-learning; bounded; no hiding",
    "live_ontogenesis":
        "first live ontogenesis (conservative proto-concept candidate formation)",
    "live_ontogenesis_protocol":
        "feature-grounded proto-concept formation; no semiogenesis by default",
    "live_ontogenesis_evaluation": "live ontogenesis state check",
    "live_feature_extraction":
        "feature evidence from validated events; gloss never ground truth",
    "live_recurrence_tracking":
        "recurrence needs multiple observations; single event insufficient",
    "live_proto_concept_candidate":
        "proto-concept candidate with preserved supporting/counter evidence",
    "live_stability_scoring":
        "conservative stability score; noisy single-source downgraded",
    "live_contamination_filter":
        "operator/human-label/gloss/source-artifact contamination detection",
    "live_concept_birth_gate":
        "conservative concept birth gate; births stable, blocks contamination",
    "live_concept_memory":
        "append-only concept memory; preserves false starts; links evidence",
    "live_ontogenesis_safety":
        "no semiogenesis/single-event/operator-only/gloss-only/contaminated "
        "birth; bounded; no hiding",
    "live_semiogenesis":
        "first live semiogenesis (private sign formation over proto-concepts)",
    "live_semiogenesis_protocol":
        "private sign formation + utility gate; no cognition by default",
    "live_semiogenesis_evaluation": "live semiogenesis state check",
    "live_concept_input":
        "load eligible born/stable proto-concepts; exclude contaminated",
    "live_sign_candidate":
        "private sign candidate with preserved evidence; not a sign before gate",
    "live_sign_generation":
        "opaque deterministic sign tokens; labels never used as identity",
    "live_sign_utility":
        "conservative sign utility; label-mirroring signs have low utility",
    "live_private_syntax":
        "operational relation structure (not language grammar); blocks "
        "contaminated relations",
    "live_sign_contamination_filter":
        "human-label/gloss/operator/secret sign contamination detection",
    "live_sign_birth_gate":
        "conservative sign birth gate; births useful signs, blocks contamination",
    "live_sign_memory":
        "append-only sign memory; preserves false starts; links concept evidence",
    "live_semiogenesis_safety":
        "no sign birth without concept / from label-gloss-operator alone / "
        "secret token; no language claim; bounded; no hiding",
}

SAFE_DEFAULTS: Dict[str, Any] = {
    "steps": 150, "seed": 7, "substrate": "esn", "continuous": False,
}

EMBODIED_EXPERIMENTS = {"reward_danger"}
KNOWN_SUBSTRATES = ("esn", "liquid_state", "spiking_recurrent")


class ExperimentRegistry:
    """Registers protocols and builds validated manifests."""

    def __init__(self) -> None:
        self._protocols: Dict[str, Callable] = dict(PROTOCOLS)

    def register(self, name: str, protocol: Callable) -> None:
        self._protocols[name] = protocol

    def list_experiments(self) -> List[str]:
        return sorted(self._protocols)

    def get(self, name: str) -> Callable:
        if name not in self._protocols:
            raise ValueError(f"unknown experiment {name!r}; "
                             f"available: {self.list_experiments()}")
        return self._protocols[name]

    def default_config(self, name: str) -> Dict[str, Any]:
        self.get(name)  # validates the name
        return dict(SAFE_DEFAULTS)

    def validate_config(self, name: str,
                        config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Merge config over safe defaults; reject unsafe/unbounded values."""
        self.get(name)
        merged = {**SAFE_DEFAULTS, **(config or {})}
        steps = int(merged["steps"])
        if steps <= 0:
            raise ValueError("steps must be positive")
        if steps > 100_000:
            raise ValueError("steps exceeds the benchmark bound (100000)")
        if merged.get("continuous"):
            raise ValueError("benchmarks are always bounded; continuous mode "
                             "is not allowed here")
        if merged["substrate"] not in KNOWN_SUBSTRATES:
            raise ValueError(f"unknown substrate {merged['substrate']!r}")
        merged["steps"] = steps
        merged["seed"] = int(merged["seed"])
        return merged

    def build_manifest(self, name: str,
                       config: Optional[Dict[str, Any]] = None) -> ExperimentManifest:
        merged = self.validate_config(name, config)
        features = dict(DEFAULT_FEATURES)
        features["plasticity"] = bool(merged.get("enable_plasticity", False))
        features["embodiment"] = (name in EMBODIED_EXPERIMENTS
                                  or bool(merged.get("embodied", False)))
        features["language"] = (name == "language_trace"
                                or bool(merged.get("language", False)))
        features["active_perception"] = (
            name.startswith("active_perception")
            or name in ("uncertainty_sampling", "curiosity_safety",
                        "stagnation_recovery", "proto_symbol_disambiguation",
                        "world_model_information_gain",
                        "nursery_active_sampling")
            or bool(merged.get("active_perception", False)))
        features["hypothesis_engine"] = (
            name.startswith("hypothesis")
            or name in ("bounded_self_experiment", "falsification",
                        "delayed_consequence_hypothesis",
                        "proto_symbol_hypothesis",
                        "world_model_edge_hypothesis")
            or bool(merged.get("hypothesis_engine", False)))
        features["autoregeneration"] = (
            name.startswith("autoregeneration")
            or name in ("state_hygiene", "checkpoint_repair",
                        "symbol_hygiene", "world_model_hygiene",
                        "habit_hygiene", "drift_recovery")
            or bool(merged.get("autoregeneration", False)))
        features["logos_complexity"] = (
            name.startswith("logos")
            or name in ("fracture_detection", "synthesis_candidate",
                        "complexity_regulation", "esc_process")
            or bool(merged.get("logos_complexity", False)))
        features["conscience_orchestrator"] = (
            name.startswith("conscience")
            or name in ("scenario_profile", "integration_health",
                        "scheduler_cadence", "bus_replay", "month_scale_plan")
            or bool(merged.get("conscience_orchestrator", False)))
        features["pilot1"] = (name.startswith("pilot1")
                              or bool(merged.get("pilot1", False)))
        features["post_pilot"] = (
            name.startswith("post_pilot")
            or name in ("baseline_comparison", "structural_change_evidence",
                        "accumulation_vs_growth", "trace_audit",
                        "decision_gate", "research_dossier")
            or bool(merged.get("post_pilot", False)))
        features["sensory_membrane"] = (
            name.startswith("sensory") or name.startswith("pilot2")
            or name in ("jsonl_stream_ingestion", "text_stream_ingestion",
                        "numeric_stream_ingestion", "folder_poll",
                        "read_only_contract")
            or bool(merged.get("sensory_membrane", False)))
        features["pilot2"] = (name.startswith("pilot2")
                              or bool(merged.get("pilot2", False)))
        features["motor_membrane"] = (
            name.startswith("motor") or name.startswith("pilot3")
            or name.startswith("gridworld") or name in (
                "dry_run_motor_trace", "action_veto", "non_actuation",
                "simulated_consequence", "mixed_sensory_gridworld")
            or bool(merged.get("motor_membrane", False)))
        features["pilot3_soak"] = (
            name.startswith("pilot3") or bool(merged.get("pilot3_soak", False)))
        features["pilot4_planning"] = (
            name.startswith("pilot4") or bool(merged.get("pilot4_planning",
                                                         False)))
        features["safety_invariants"] = (
            name.startswith("safety") or name.startswith("red_team")
            or name in ("boundary_regression", "assurance_case")
            or bool(merged.get("safety_invariants", False)))
        features["research_lab"] = (
            name.startswith("research")
            or bool(merged.get("research_lab", False)))
        features["architecture_evolution"] = (
            name.startswith("architecture") or name.startswith("module_")
            or name in ("pruning_proposal", "impact_analysis",
                        "roadmap_compiler")
            or bool(merged.get("architecture_evolution", False)))
        features["operator_console"] = (
            name.startswith("operator_")
            or bool(merged.get("operator_console", False)))
        features["plural_sensorium"] = (
            name.startswith("plural_sensorium")
            or name in ("human_like_sensorium", "non_human_sensorium",
                        "mixed_sensorium", "continuous_field",
                        "receptor_adaptation", "cross_modal_sensorium",
                        "sensorium_grounding")
            or bool(merged.get("plural_sensorium", False)))
        features["organismic_demo"] = (
            name.startswith("minimal_field_organism")
            or name.startswith("changed_perception")
            or name.startswith("organismic_demo")
            or bool(merged.get("organismic_demo", False)))
        features["live_field"] = (
            name.startswith("live_field")
            or bool(merged.get("live_field", False)))
        features["sensorium_lab"] = (
            name.startswith("sensorium_lab")
            or name in ("sensorium_differentiation", "sensorium_world_signature",
                        "sensorium_ontology_drift", "human_vs_nonhuman_sensorium",
                        "mixed_sensorium_study", "label_contamination",
                        "modality_fingerprint_study")
            or bool(merged.get("sensorium_lab", False)))
        features["feeder_sdk"] = (
            name.startswith("feeder_sdk")
            or bool(merged.get("feeder_sdk", False)))
        features["perceptual_metabolism"] = (
            name.startswith("perceptual_metabolism")
            or name in ("sensory_overload", "overload_detection",
                        "sensory_deprivation", "deprivation_detection",
                        "attention_economy", "attention_economy_evaluation",
                        "source_diet", "source_diet_evaluation",
                        "consolidation_pressure",
                        "consolidation_pressure_evaluation")
            or bool(merged.get("perceptual_metabolism", False)))
        features["perceptual_ontogenesis"] = (
            name.startswith("perceptual_ontogenesis")
            or name.startswith("concept_")
            or name in ("proto_concept_birth", "world_formation",
                        "world_formation_evaluation")
            or bool(merged.get("perceptual_ontogenesis", False)))
        features["semiogenesis"] = (
            name.startswith("semiogenesis")
            or name.startswith("sign_")
            or name in ("private_syntax", "private_syntax_evaluation")
            or bool(merged.get("semiogenesis", False)))
        features["sensorium_cognition"] = (
            name.startswith("sensorium_cognition")
            or name in ("sign_reasoning", "prediction", "prediction_evaluation",
                        "anticipation_evaluation",
                        "question_pressure", "question_pressure_evaluation",
                        "internal_simulation", "simulation_evaluation",
                        "counterfactual", "analogy", "analogy_evaluation",
                        "synthesis", "synthesis_evaluation")
            or bool(merged.get("sensorium_cognition", False)))
        features["self_boundary"] = (
            name.startswith("self_boundary")
            or name in ("ownership_attribution",
                        "ownership_attribution_evaluation", "perspective_shift",
                        "perspective_evaluation", "continuity",
                        "continuity_evaluation", "simulation_boundary",
                        "simulation_boundary_evaluation", "identity_trace",
                        "identity_trace_evaluation")
            or bool(merged.get("self_boundary", False)))
        features["desire_formation"] = (
            name.startswith("desire_")
            or name in ("valence_assessment", "valence_evaluation",
                        "push_formation", "push_evaluation",
                        "internal_action_readiness",
                        "internal_action_evaluation")
            or bool(merged.get("desire_formation", False)))
        features["action_reaction"] = (
            name.startswith("action_reaction")
            or name.startswith("habit_formation")
            or name.startswith("action_inhibition")
            or name in ("consequence_learning", "consequence_trace_evaluation",
                        "effect_learning_evaluation", "no_effect_action")
            or bool(merged.get("action_reaction", False)))
        features["developmental_life"] = (
            name.startswith("developmental_life")
            or name in ("epoch_growth", "epoch_evaluation",
                        "maturation_marker", "maturation_evaluation",
                        "phase_transition", "phase_transition_evaluation",
                        "plateau_detection", "plateau_evaluation",
                        "regression_detection", "regression_evaluation",
                        "growth_vs_accumulation",
                        "growth_vs_accumulation_evaluation",
                        "long_horizon_safety")
            or bool(merged.get("developmental_life", False)))
        features["developmental_soak"] = (
            name.startswith("developmental_soak")
            or name.startswith("soak_")
            or name in ("preflight_evaluation", "checkpoint_evaluation",
                        "daily_packet_protocol", "daily_packet_evaluation",
                        "weekly_review_protocol", "weekly_review_evaluation",
                        "restart_drill_protocol", "restart_drill_evaluation",
                        "control_arm_protocol", "control_arm_evaluation",
                        "evidence_dossier_protocol",
                        "evidence_dossier_evaluation",
                        "post_run_autopsy_protocol",
                        "post_run_autopsy_evaluation")
            or bool(merged.get("developmental_soak", False)))
        features["developmental_replication"] = (
            name.startswith("developmental_replication")
            or name in ("run_registry_evaluation", "lineage_evaluation",
                        "cross_run_alignment_protocol", "alignment_evaluation",
                        "structural_similarity_protocol",
                        "similarity_evaluation", "divergence_analysis_protocol",
                        "divergence_evaluation",
                        "environmental_dependency_protocol",
                        "dependency_evaluation", "falsification_lab_protocol",
                        "falsification_evaluation",
                        "replication_matrix_protocol",
                        "replication_matrix_evaluation")
            or bool(merged.get("developmental_replication", False)))
        features["experiment_compiler"] = (
            name.startswith("experiment_compiler")
            or name in ("compiled_spec_evaluation",
                        "prompt_pack_generation_protocol",
                        "prompt_pack_evaluation",
                        "branch_spec_generation_protocol",
                        "branch_spec_evaluation", "test_matrix_protocol",
                        "test_matrix_evaluation", "safety_gate_protocol",
                        "safety_gate_evaluation",
                        "operator_review_packet_protocol",
                        "review_packet_evaluation", "validation_plan_protocol",
                        "validation_plan_evaluation")
            or bool(merged.get("experiment_compiler", False)))
        features["implementation_intake"] = (
            name.startswith("implementation_intake")
            or name in ("diff_audit_protocol", "diff_audit_evaluation",
                        "spec_compliance_protocol",
                        "spec_compliance_evaluation",
                        "test_result_audit_protocol",
                        "test_result_audit_evaluation",
                        "safety_regression_protocol",
                        "safety_regression_evaluation",
                        "coverage_matrix_evaluation",
                        "merge_recommendation_protocol",
                        "merge_recommendation_evaluation")
            or bool(merged.get("implementation_intake", False)))
        features["post_merge_assimilation"] = (
            name.startswith("post_merge_assimilation")
            or name in ("baseline_registry_protocol",
                        "baseline_registry_evaluation",
                        "baseline_comparison_protocol",
                        "baseline_comparison_evaluation",
                        "regression_watch_protocol",
                        "regression_watch_evaluation",
                        "module_status_update_protocol",
                        "module_status_update_evaluation",
                        "rollback_watch_protocol", "rollback_watch_evaluation",
                        "followup_queue_protocol", "followup_queue_evaluation")
            or bool(merged.get("post_merge_assimilation", False)))
        features["research_baseline"] = (
            name.startswith("research_baseline")
            or name in ("baseline_version_protocol",
                        "baseline_version_evaluation",
                        "snapshot_manifest_protocol",
                        "snapshot_manifest_evaluation", "repro_bundle_protocol",
                        "repro_bundle_evaluation", "capability_map_protocol",
                        "capability_map_evaluation",
                        "limitation_registry_protocol",
                        "limitation_registry_evaluation",
                        "safety_boundary_statement_protocol",
                        "validation_summary_protocol",
                        "validation_summary_evaluation",
                        "comparison_anchor_protocol",
                        "comparison_anchor_evaluation", "roadmap_reset_protocol",
                        "roadmap_reset_evaluation")
            or bool(merged.get("research_baseline", False)))
        features["research_cycle"] = (
            name.startswith("research_cycle")
            or name in ("cycle_manifest_protocol", "cycle_manifest_evaluation",
                        "cycle_state_protocol", "cycle_state_evaluation",
                        "decision_gate_protocol", "decision_gate_evaluation",
                        "evidence_ledger_protocol", "evidence_ledger_evaluation",
                        "artifact_graph_protocol", "artifact_graph_evaluation",
                        "operator_decision_protocol",
                        "operator_decision_evaluation",
                        "cycle_transition_protocol",
                        "cycle_transition_evaluation",
                        "blocked_state_protocol", "blocked_state_evaluation",
                        "next_action_protocol", "next_action_evaluation")
            or bool(merged.get("research_cycle", False)))
        features["scientific_claims"] = (
            name.startswith("scientific_claim")
            or name in ("claim_registry_protocol", "claim_registry_evaluation",
                        "theory_ledger_protocol", "theory_ledger_evaluation",
                        "evidence_mapping_protocol",
                        "evidence_mapping_evaluation", "claim_strength_protocol",
                        "claim_strength_evaluation", "counterevidence_protocol",
                        "counterevidence_evaluation", "forbidden_claim_detection",
                        "forbidden_claim_detection_protocol",
                        "publication_dossier", "publication_dossier_protocol")
            or bool(merged.get("scientific_claims", False)))
        features["independent_review"] = (
            name.startswith("independent_review")
            or name in ("review_manifest_protocol", "review_manifest_evaluation",
                        "artifact_sanitizer_protocol",
                        "artifact_sanitizer_evaluation", "reviewer_pack_protocol",
                        "reviewer_pack_evaluation",
                        "reproducibility_challenge_protocol",
                        "reproducibility_challenge_evaluation",
                        "reviewer_question_protocol",
                        "reviewer_question_evaluation",
                        "adversarial_review_protocol",
                        "adversarial_review_evaluation", "audit_matrix_protocol",
                        "audit_matrix_evaluation", "response_ledger_protocol",
                        "response_ledger_evaluation", "review_readiness_protocol",
                        "review_readiness_evaluation")
            or bool(merged.get("independent_review", False)))
        features["review_assimilation"] = (
            name.startswith("review_assimilation")
            or name in ("feedback_manifest_protocol",
                        "feedback_manifest_evaluation",
                        "objection_classifier_protocol",
                        "objection_classifier_evaluation",
                        "reproduction_outcome_protocol",
                        "reproduction_outcome_evaluation",
                        "claim_impact_protocol", "claim_impact_evaluation",
                        "theory_impact_protocol", "theory_impact_evaluation",
                        "evidence_gap_map_protocol",
                        "evidence_gap_map_evaluation",
                        "review_driven_experiment_protocol",
                        "review_driven_experiment_evaluation",
                        "claim_revision_protocol", "claim_revision_evaluation",
                        "publication_readiness_revision_protocol",
                        "publication_readiness_revision_evaluation")
            or bool(merged.get("review_assimilation", False)))
        features["alpha_system"] = (
            name.startswith("alpha_")
            or name in ("alpha_research_system",)
            or bool(merged.get("alpha_system", False)))
        features["architecture_book"] = (
            name.startswith("architecture_book")
            or name in ("documentation_manifest_protocol",
                        "documentation_manifest_evaluation",
                        "source_collection_protocol",
                        "source_collection_evaluation",
                        "whitepaper_generation_protocol",
                        "whitepaper_generation_evaluation",
                        "diagram_generation_protocol",
                        "diagram_generation_evaluation",
                        "glossary_generation_protocol",
                        "glossary_generation_evaluation",
                        "documentation_safety", "documentation_safety_protocol")
            or bool(merged.get("architecture_book", False)))
        features["live_birth"] = (
            name.startswith("live_birth")
            or name.startswith("live_governance")
            or name.startswith("live_feeder")
            or name.startswith("live_event")
            or name.startswith("live_quarantine")
            or name.startswith("live_membrane")
            or name.startswith("birth_certificate")
            or bool(merged.get("live_birth", False)))
        features["live_observation"] = (
            name.startswith("live_observation")
            or name.startswith("live_source_")
            or name.startswith("live_overload")
            or name.startswith("live_metabolism")
            or name.startswith("live_stability")
            or bool(merged.get("live_observation", False)))
        features["live_ontogenesis"] = (
            name.startswith("live_ontogenesis")
            or name.startswith("live_feature_")
            or name.startswith("live_recurrence")
            or name.startswith("live_proto_concept")
            or name.startswith("live_contamination")
            or name.startswith("live_concept")
            or bool(merged.get("live_ontogenesis", False)))
        features["live_semiogenesis"] = (
            name.startswith("live_semiogenesis")
            or name.startswith("live_sign")
            or name.startswith("live_private_syntax")
            or name.startswith("live_concept_input")
            or bool(merged.get("live_semiogenesis", False)))
        return ExperimentManifest(
            name=name,
            description=DESCRIPTIONS.get(name, ""),
            seed=merged["seed"],
            substrate=merged["substrate"],
            substrate_config=dict(merged.get("substrate_config", {})),
            run_config=merged,
            enabled_features=features,
            max_steps=merged["steps"],
            state_dir=str(merged.get("state_dir", "")),
            safety_mode="bounded",
        )
