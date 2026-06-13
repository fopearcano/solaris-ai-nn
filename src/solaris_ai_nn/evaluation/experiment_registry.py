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
