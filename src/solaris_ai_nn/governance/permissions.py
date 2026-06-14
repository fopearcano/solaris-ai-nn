"""Permissions -- what the system is allowed to do, scope by scope.

A :class:`PermissionSet` is a local, explicit ledger of capabilities. It is not
a security mechanism (there is no authentication); it is a research control
that makes "what was this run allowed to do?" answerable and auditable.

Two invariants are structural, not configurable:

* unknown scopes are never granted (deny by default, approval required);
* ``perform_emergency_stop`` is always allowed and can never be revoked.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


class PermissionScope:
    """Canonical permission scopes."""

    RUN_BOUNDED = "run_bounded"
    RUN_SOAK_24H = "run_soak_24h"
    RUN_SOAK_30D = "run_soak_30d"
    ENABLE_PLASTICITY = "enable_plasticity"
    ENABLE_PLASTICITY_APPLY = "enable_plasticity_apply"
    ENABLE_PLASTICITY_DRY_RUN = "enable_plasticity_dry_run"
    ENABLE_EMBODIMENT_SIMULATION = "enable_embodiment_simulation"
    ENABLE_SIDECAR_OBSERVE = "enable_sidecar_observe"
    ENABLE_SIDECAR_SUGGESTIONS = "enable_sidecar_suggestions"
    ENABLE_LOCAL_STATUS_SERVER = "enable_local_status_server"
    PERFORM_ARTIFACT_ROTATION = "perform_artifact_rotation"
    PERFORM_ROLLBACK = "perform_rollback"
    PERFORM_EMERGENCY_STOP = "perform_emergency_stop"
    # Latent cognition (Prompt 14).
    ENABLE_LATENT = "enable_latent"
    ENABLE_LATENT_DRY_RUN = "enable_latent_dry_run"
    ENABLE_LATENT_PLASTICITY = "enable_latent_plasticity"
    RUN_DREAM_CYCLE = "run_dream_cycle"
    RUN_COUNTERFACTUAL_REPLAY = "run_counterfactual_replay"
    # World model (Prompt 15).
    ENABLE_WORLD_MODEL = "enable_world_model"
    ENABLE_WORLD_MODEL_PRUNING = "enable_world_model_pruning"
    ENABLE_WORLD_MODEL_PREDICTION = "enable_world_model_prediction"
    # Homeostasis (Prompt 16).
    ENABLE_HOMEOSTASIS = "enable_homeostasis"
    ENABLE_NEED_DRIVEN_SUGGESTIONS = "enable_need_driven_suggestions"
    ENABLE_AUTO_DETERMINATION = "enable_auto_determination"
    ALLOW_SAFE_SHUTDOWN_RECOMMENDATION = "allow_safe_shutdown_recommendation"
    # Executive (Prompt 17).
    ENABLE_EXECUTIVE = "enable_executive"
    ENABLE_SHORT_HORIZON_PLANNING = "enable_short_horizon_planning"
    ENABLE_PROSPECTION = "enable_prospection"
    ENABLE_EXECUTIVE_SIDECAR_SUGGESTIONS = (
        "enable_executive_sidecar_suggestions")
    # Ego / self-model (Prompt 18).
    ENABLE_EGO_MODEL = "enable_ego_model"
    ENABLE_DIMENSIONAL_COMPARISON = "enable_dimensional_comparison"
    ENABLE_SELF_REPORT = "enable_self_report"
    # Communication / operator dialogue (Prompt 19).
    ENABLE_OPERATOR_DIALOGUE = "enable_operator_dialogue"
    OPERATOR_GENERATE_REPORTS = "operator_generate_reports"
    OPERATOR_REQUEST_CHECKPOINT = "operator_request_checkpoint"
    OPERATOR_REQUEST_SAFE_SHUTDOWN = "operator_request_safe_shutdown"
    OPERATOR_RUN_BOUNDED_BENCHMARK = "operator_run_bounded_benchmark"
    OPERATOR_APPROVE_REQUESTS = "operator_approve_requests"
    OPERATOR_SEND_SENSORY_TEXT = "operator_send_sensory_text"
    # Local LLM adapter (Prompt 20).
    ENABLE_LOCAL_LLM_ADAPTER = "enable_local_llm_adapter"
    ALLOW_LOCALHOST_LLM_ENDPOINT = "allow_localhost_llm_endpoint"
    ALLOW_REMOTE_LLM_ENDPOINT = "allow_remote_llm_endpoint"
    ALLOW_LLM_CLASSIFICATION_ASSIST = "allow_llm_classification_assist"
    ALLOW_LLM_REPORT_POLISH = "allow_llm_report_polish"
    # Developmental runtime (Prompt 21).
    ENABLE_DEVELOPMENTAL_RUNTIME = "enable_developmental_runtime"
    ENABLE_MONTH_SCALE_TESTING = "enable_month_scale_testing"
    ENABLE_YEAR_SCALE_TESTING = "enable_year_scale_testing"
    ENABLE_MEMORY_COMPRESSION = "enable_memory_compression"
    ENABLE_FOSSIL_MEMORY = "enable_fossil_memory"
    ENABLE_DEVELOPMENTAL_PRUNING = "enable_developmental_pruning"
    # Proto-language (Prompt 22).
    ENABLE_PROTO_LANGUAGE = "enable_proto_language"
    ENABLE_SYMBOL_EMERGENCE = "enable_symbol_emergence"
    ENABLE_SYMBOLIC_COMPRESSION = "enable_symbolic_compression"
    ENABLE_PROTO_LANGUAGE_TRANSLATION = (
        "enable_proto_language_translation")
    # Developmental nursery / stimulus ecology (Prompt 23).
    ENABLE_DEVELOPMENTAL_NURSERY = "enable_developmental_nursery"
    ENABLE_ECOLOGY_STREAM = "enable_ecology_stream"
    ENABLE_MONTH_SCALE_ECOLOGY = "enable_month_scale_ecology"
    ENABLE_YEAR_SCALE_ECOLOGY = "enable_year_scale_ecology"
    ENABLE_DEPRIVATION_WINDOWS = "enable_deprivation_windows"
    ENABLE_ANOMALY_GENERATION = "enable_anomaly_generation"
    # Active perception / intrinsic exploration (Prompt 24).
    ENABLE_ACTIVE_PERCEPTION = "enable_active_perception"
    ENABLE_CURIOSITY_DRIVEN_SAMPLING = "enable_curiosity_driven_sampling"
    ENABLE_NURSERY_SAMPLING_REQUESTS = "enable_nursery_sampling_requests"
    ENABLE_READ_ONLY_STREAM_SAMPLING = "enable_read_only_stream_sampling"
    ENABLE_SIDECAR_OBSERVATION_SAMPLING = (
        "enable_sidecar_observation_sampling")
    # Hypothesis engine / self-experimentation (Prompt 25).
    ENABLE_HYPOTHESIS_ENGINE = "enable_hypothesis_engine"
    ENABLE_SELF_EXPERIMENTATION = "enable_self_experimentation"
    ENABLE_NURSERY_INTERVENTIONS = "enable_nursery_interventions"
    ENABLE_LATENT_HYPOTHESIS_TESTS = "enable_latent_hypothesis_tests"
    ENABLE_COUNTERFACTUAL_HYPOTHESIS_TESTS = (
        "enable_counterfactual_hypothesis_tests")
    ENABLE_HYPOTHESIS_WORLD_MODEL_UPDATES = (
        "enable_hypothesis_world_model_updates")
    # Auto-regeneration / self-repair (Prompt 26).
    ENABLE_AUTOREGENERATION = "enable_autoregeneration"
    ENABLE_STATE_HYGIENE = "enable_state_hygiene"
    ENABLE_SAFE_AUTO_REPAIR = "enable_safe_auto_repair"
    ENABLE_CHECKPOINT_REPAIR = "enable_checkpoint_repair"
    ENABLE_MEMORY_COMPACTION = "enable_memory_compaction"
    ENABLE_SYMBOL_HYGIENE = "enable_symbol_hygiene"
    ENABLE_WORLD_MODEL_HYGIENE = "enable_world_model_hygiene"
    ENABLE_HABIT_HYGIENE = "enable_habit_hygiene"
    ENABLE_REPAIR_ROLLBACK = "enable_repair_rollback"
    # LOGOS fracture/synthesis and complexity regulation (Prompt 27).
    ENABLE_LOGOS_COMPLEXITY = "enable_logos_complexity"
    ENABLE_FRACTURE_DETECTION = "enable_fracture_detection"
    ENABLE_SYNTHESIS_CANDIDATES = "enable_synthesis_candidates"
    ENABLE_SAFE_SYNTHESIS = "enable_safe_synthesis"
    ENABLE_ESC_PROCESS = "enable_esc_process"
    ENABLE_COMPLEXITY_REGULATION = "enable_complexity_regulation"
    # Conscience spine / unified runtime orchestrator (Prompt 28).
    ENABLE_CONSCIENCE_ORCHESTRATOR = "enable_conscience_orchestrator"
    ENABLE_FULL_DEVELOPMENTAL_SHORT_PROFILE = (
        "enable_full_developmental_short_profile")
    ENABLE_MONTH_SCALE_DRY_RUN = "enable_month_scale_dry_run"
    ENABLE_MONTH_SCALE_REAL_RUN = "enable_month_scale_real_run"
    ENABLE_YEAR_SCALE_PLAN = "enable_year_scale_plan"
    ENABLE_YEAR_SCALE_REAL_RUN = "enable_year_scale_real_run"

    ALL = (
        RUN_BOUNDED, RUN_SOAK_24H, RUN_SOAK_30D,
        ENABLE_PLASTICITY, ENABLE_PLASTICITY_APPLY, ENABLE_PLASTICITY_DRY_RUN,
        ENABLE_EMBODIMENT_SIMULATION,
        ENABLE_SIDECAR_OBSERVE, ENABLE_SIDECAR_SUGGESTIONS,
        ENABLE_LOCAL_STATUS_SERVER,
        PERFORM_ARTIFACT_ROTATION, PERFORM_ROLLBACK, PERFORM_EMERGENCY_STOP,
        ENABLE_LATENT, ENABLE_LATENT_DRY_RUN, ENABLE_LATENT_PLASTICITY,
        RUN_DREAM_CYCLE, RUN_COUNTERFACTUAL_REPLAY,
        ENABLE_WORLD_MODEL, ENABLE_WORLD_MODEL_PRUNING,
        ENABLE_WORLD_MODEL_PREDICTION,
        ENABLE_HOMEOSTASIS, ENABLE_NEED_DRIVEN_SUGGESTIONS,
        ENABLE_AUTO_DETERMINATION, ALLOW_SAFE_SHUTDOWN_RECOMMENDATION,
        ENABLE_EXECUTIVE, ENABLE_SHORT_HORIZON_PLANNING,
        ENABLE_PROSPECTION, ENABLE_EXECUTIVE_SIDECAR_SUGGESTIONS,
        ENABLE_EGO_MODEL, ENABLE_DIMENSIONAL_COMPARISON,
        ENABLE_SELF_REPORT,
        ENABLE_OPERATOR_DIALOGUE, OPERATOR_GENERATE_REPORTS,
        OPERATOR_REQUEST_CHECKPOINT, OPERATOR_REQUEST_SAFE_SHUTDOWN,
        OPERATOR_RUN_BOUNDED_BENCHMARK, OPERATOR_APPROVE_REQUESTS,
        OPERATOR_SEND_SENSORY_TEXT,
        ENABLE_LOCAL_LLM_ADAPTER, ALLOW_LOCALHOST_LLM_ENDPOINT,
        ALLOW_REMOTE_LLM_ENDPOINT, ALLOW_LLM_CLASSIFICATION_ASSIST,
        ALLOW_LLM_REPORT_POLISH,
        ENABLE_DEVELOPMENTAL_RUNTIME, ENABLE_MONTH_SCALE_TESTING,
        ENABLE_YEAR_SCALE_TESTING, ENABLE_MEMORY_COMPRESSION,
        ENABLE_FOSSIL_MEMORY, ENABLE_DEVELOPMENTAL_PRUNING,
        ENABLE_PROTO_LANGUAGE, ENABLE_SYMBOL_EMERGENCE,
        ENABLE_SYMBOLIC_COMPRESSION, ENABLE_PROTO_LANGUAGE_TRANSLATION,
        ENABLE_DEVELOPMENTAL_NURSERY, ENABLE_ECOLOGY_STREAM,
        ENABLE_MONTH_SCALE_ECOLOGY, ENABLE_YEAR_SCALE_ECOLOGY,
        ENABLE_DEPRIVATION_WINDOWS, ENABLE_ANOMALY_GENERATION,
        ENABLE_ACTIVE_PERCEPTION, ENABLE_CURIOSITY_DRIVEN_SAMPLING,
        ENABLE_NURSERY_SAMPLING_REQUESTS, ENABLE_READ_ONLY_STREAM_SAMPLING,
        ENABLE_SIDECAR_OBSERVATION_SAMPLING,
        ENABLE_HYPOTHESIS_ENGINE, ENABLE_SELF_EXPERIMENTATION,
        ENABLE_NURSERY_INTERVENTIONS, ENABLE_LATENT_HYPOTHESIS_TESTS,
        ENABLE_COUNTERFACTUAL_HYPOTHESIS_TESTS,
        ENABLE_HYPOTHESIS_WORLD_MODEL_UPDATES,
        ENABLE_AUTOREGENERATION, ENABLE_STATE_HYGIENE,
        ENABLE_SAFE_AUTO_REPAIR, ENABLE_CHECKPOINT_REPAIR,
        ENABLE_MEMORY_COMPACTION, ENABLE_SYMBOL_HYGIENE,
        ENABLE_WORLD_MODEL_HYGIENE, ENABLE_HABIT_HYGIENE,
        ENABLE_REPAIR_ROLLBACK,
        ENABLE_LOGOS_COMPLEXITY, ENABLE_FRACTURE_DETECTION,
        ENABLE_SYNTHESIS_CANDIDATES, ENABLE_SAFE_SYNTHESIS,
        ENABLE_ESC_PROCESS, ENABLE_COMPLEXITY_REGULATION,
        ENABLE_CONSCIENCE_ORCHESTRATOR,
        ENABLE_FULL_DEVELOPMENTAL_SHORT_PROFILE,
        ENABLE_MONTH_SCALE_DRY_RUN, ENABLE_MONTH_SCALE_REAL_RUN,
        ENABLE_YEAR_SCALE_PLAN, ENABLE_YEAR_SCALE_REAL_RUN,
    )


# Scopes that are always allowed, no matter how the set was configured.
ALWAYS_ALLOWED = frozenset({PermissionScope.PERFORM_EMERGENCY_STOP})


@dataclass
class Permission:
    """One scope: is it granted outright, and does it need human approval?"""

    scope: str
    granted: bool = False
    requires_approval: bool = False
    note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class PermissionSet:
    """An explicit set of permissions; unknown scopes are denied."""

    permissions: Dict[str, Permission] = field(default_factory=dict)

    @classmethod
    def default(cls) -> "PermissionSet":
        """The safe baseline: bounded, simulated, observe-only, dry-run."""
        S = PermissionScope
        rows = [
            Permission(S.RUN_BOUNDED, granted=True,
                       note="bounded runs are the default safe mode"),
            Permission(S.RUN_SOAK_24H, requires_approval=True,
                       note="long soaks are opt-in and need approval"),
            Permission(S.RUN_SOAK_30D, requires_approval=True,
                       note="long soaks are opt-in and need approval"),
            Permission(S.ENABLE_PLASTICITY, granted=True,
                       note="the feature flag; applying mutations is gated "
                            "separately"),
            Permission(S.ENABLE_PLASTICITY_APPLY, requires_approval=True,
                       note="active self-modification needs human approval"),
            Permission(S.ENABLE_PLASTICITY_DRY_RUN, granted=True,
                       note="proposals are logged, never applied"),
            Permission(S.ENABLE_EMBODIMENT_SIMULATION, granted=True,
                       note="simulation-only; real-world actuation is "
                            "forbidden by policy, not permission"),
            Permission(S.ENABLE_SIDECAR_OBSERVE, granted=True,
                       note="read-only observation of a Solaris_Ai bus"),
            Permission(S.ENABLE_SIDECAR_SUGGESTIONS, requires_approval=True,
                       note="publishing suggestions outward needs approval"),
            Permission(S.ENABLE_LOCAL_STATUS_SERVER, granted=True,
                       note="localhost-only, read-only"),
            Permission(S.PERFORM_ARTIFACT_ROTATION, granted=True,
                       note="rotation compresses/archives, never silently "
                            "destroys evidence"),
            Permission(S.PERFORM_ROLLBACK, granted=True,
                       note="undoing a mutation is always allowed"),
            Permission(S.PERFORM_EMERGENCY_STOP, granted=True,
                       note="always allowed; cannot be revoked"),
            Permission(S.ENABLE_LATENT, granted=True,
                       note="bounded offline cycles; never external "
                            "actions"),
            Permission(S.ENABLE_LATENT_DRY_RUN, granted=True,
                       note="sandboxed replay/consolidation, nothing "
                            "applied"),
            Permission(S.ENABLE_LATENT_PLASTICITY, requires_approval=True,
                       note="latent cycles mutating production state need "
                            "human approval"),
            Permission(S.RUN_DREAM_CYCLE, granted=True,
                       note="sandboxed counterfactual replay; offline only"),
            Permission(S.RUN_COUNTERFACTUAL_REPLAY, granted=True,
                       note="labelled simulations, never real "
                            "observations"),
            Permission(S.ENABLE_WORLD_MODEL, granted=True,
                       note="graph observation of recorded events; "
                            "inspectable, no execution path"),
            Permission(S.ENABLE_WORLD_MODEL_PRUNING, requires_approval=True,
                       note="production graph subtraction needs approval; "
                            "dry-run proposals are always allowed"),
            Permission(S.ENABLE_WORLD_MODEL_PREDICTION, granted=True,
                       note="predictions from graph counts; data only, "
                            "never executed"),
            Permission(S.ENABLE_HOMEOSTASIS, granted=True,
                       note="need-pressure regulation; biases, never "
                            "commands"),
            Permission(S.ENABLE_NEED_DRIVEN_SUGGESTIONS, granted=True,
                       note="Desire candidates are clearly suggestions"),
            Permission(S.ENABLE_AUTO_DETERMINATION, granted=True,
                       note="an operational continuity metric, not "
                            "authority"),
            Permission(S.ALLOW_SAFE_SHUTDOWN_RECOMMENDATION, granted=True,
                       note="a recommendation only; ops "
                            "supervisor/watchdog decides"),
            Permission(S.ENABLE_EXECUTIVE, granted=True,
                       note="arbitration in bounded simulation; "
                            "suggestions only"),
            Permission(S.ENABLE_SHORT_HORIZON_PLANNING, granted=True,
                       note="plans capped at 3 steps (hard max 5); "
                            "suggestion-only"),
            Permission(S.ENABLE_PROSPECTION, granted=True,
                       note="bounded simulated estimates, never facts"),
            Permission(S.ENABLE_EXECUTIVE_SIDECAR_SUGGESTIONS,
                       requires_approval=True,
                       note="executive-ranked sidecar publishing needs "
                            "approval; observe-only stands"),
            Permission(S.ENABLE_EGO_MODEL, granted=True,
                       note="an operational continuity/boundary model; "
                            "observes only, grants nothing"),
            Permission(S.ENABLE_DIMENSIONAL_COMPARISON, granted=True,
                       note="deterministic frame comparison on six fixed "
                            "axes"),
            Permission(S.ENABLE_SELF_REPORT, granted=True,
                       note="self-reports must pass ClaimGuard and the "
                            "identity-claim scan"),
            Permission(S.ENABLE_OPERATOR_DIALOGUE, granted=True,
                       note="classified, transcribed, ClaimGuard-scanned "
                            "operator dialogue; no LLM, no authority"),
            Permission(S.OPERATOR_GENERATE_REPORTS, granted=True,
                       note="report generation runs through ClaimGuard"),
            Permission(S.OPERATOR_REQUEST_CHECKPOINT, granted=True,
                       note="a request to the runtime/ops layer, not a "
                            "direct write"),
            Permission(S.OPERATOR_REQUEST_SAFE_SHUTDOWN, granted=True,
                       note="safe shutdown is always allowed; the ops "
                            "layer performs it"),
            Permission(S.OPERATOR_RUN_BOUNDED_BENCHMARK, granted=True,
                       note="bounded protocol runs only; the step cap is "
                            "structural"),
            Permission(S.OPERATOR_APPROVE_REQUESTS, granted=True,
                       note="approvals act only on real pending requests "
                            "and bypass nothing prohibited"),
            Permission(S.OPERATOR_SEND_SENSORY_TEXT,
                       requires_approval=True,
                       note="injecting text as a sensory stimulus is "
                            "off by default and approval-gated"),
            Permission(S.ENABLE_LOCAL_LLM_ADAPTER, granted=True,
                       note="mock/local translator only; disabled in "
                            "config by default and never authoritative"),
            Permission(S.ALLOW_LOCALHOST_LLM_ENDPOINT, granted=True,
                       note="localhost endpoints only, and only with "
                            "explicit adapter config"),
            Permission(S.ALLOW_REMOTE_LLM_ENDPOINT,
                       requires_approval=True,
                       note="remote/cloud endpoints are prohibited "
                            "without explicit human approval"),
            Permission(S.ALLOW_LLM_CLASSIFICATION_ASSIST, granted=True,
                       note="suggestions only; the deterministic "
                            "classifier remains authoritative"),
            Permission(S.ALLOW_LLM_REPORT_POLISH, granted=True,
                       note="wording only; structure, numbers, warnings, "
                            "and limitations are preserved or refused"),
            Permission(S.ENABLE_DEVELOPMENTAL_RUNTIME, granted=True,
                       note="bounded simulated developmental runs; "
                            "month/year scale gated separately"),
            Permission(S.ENABLE_MONTH_SCALE_TESTING,
                       requires_approval=True,
                       note="real month-scale runs need explicit human "
                            "approval"),
            Permission(S.ENABLE_YEAR_SCALE_TESTING,
                       requires_approval=True,
                       note="real year-scale runs need explicit human "
                            "approval"),
            Permission(S.ENABLE_MEMORY_COMPRESSION, granted=True,
                       note="allowed because evidence summaries are "
                            "structurally preserved"),
            Permission(S.ENABLE_FOSSIL_MEMORY, granted=True,
                       note="append-only milestone archive; deletion is "
                            "operator maintenance only"),
            Permission(S.ENABLE_DEVELOPMENTAL_PRUNING,
                       requires_approval=True,
                       note="pruning production memory needs approval "
                            "unless dry-run"),
            Permission(S.ENABLE_PROTO_LANGUAGE, granted=True,
                       note="internal symbols in bounded/developmental "
                            "runs; never authority, never commands"),
            Permission(S.ENABLE_SYMBOL_EMERGENCE, granted=True,
                       note="repetition-based naming; deterministic, "
                            "no LLM, no human feedback"),
            Permission(S.ENABLE_SYMBOLIC_COMPRESSION, granted=True,
                       note="allowed because safety incidents stay "
                            "verbatim and evidence refs survive"),
            Permission(S.ENABLE_PROTO_LANGUAGE_TRANSLATION,
                       granted=True,
                       note="debug translations only; ClaimGuard gates "
                            "every rendering"),
            Permission(S.ENABLE_DEVELOPMENTAL_NURSERY, granted=True,
                       note="a bounded simulated stimulus world; no "
                            "teaching, no real-world input"),
            Permission(S.ENABLE_ECOLOGY_STREAM, granted=True,
                       note="canonical-signal stream from the nursery; "
                            "deterministic and replayable"),
            Permission(S.ENABLE_MONTH_SCALE_ECOLOGY,
                       requires_approval=True,
                       note="month-scale ecology requires explicit "
                            "human approval"),
            Permission(S.ENABLE_YEAR_SCALE_ECOLOGY,
                       requires_approval=True,
                       note="year-scale ecology requires explicit "
                            "human approval"),
            Permission(S.ENABLE_DEPRIVATION_WINDOWS, granted=True,
                       note="bounded silence windows; tests latent "
                            "activation, never starves the system"),
            Permission(S.ENABLE_ANOMALY_GENERATION, granted=True,
                       note="bounded controlled perturbations, not "
                            "errors"),
            Permission(S.ENABLE_ACTIVE_PERCEPTION, granted=True,
                       note="self-directed sampling in bounded "
                            "simulation/internal/read-only scope; "
                            "suggestion-only, never real-world"),
            Permission(S.ENABLE_CURIOSITY_DRIVEN_SAMPLING,
                       requires_approval=True,
                       note="curiosity-driven mode is off by default and "
                            "needs explicit config/approval"),
            Permission(S.ENABLE_NURSERY_SAMPLING_REQUESTS, granted=True,
                       note="active perception may request (never command) "
                            "bounded ecology shifts; ecology safety "
                            "validates them"),
            Permission(S.ENABLE_READ_ONLY_STREAM_SAMPLING, granted=True,
                       note="read-only stream sampling cannot modify the "
                            "stream"),
            Permission(S.ENABLE_SIDECAR_OBSERVATION_SAMPLING, granted=True,
                       note="sidecar sampling is observe-only; it can "
                            "neither publish nor commit"),
            Permission(S.ENABLE_HYPOTHESIS_ENGINE, granted=True,
                       note="grounded internal hypothesis candidates in "
                            "bounded runs; never authority, never a belief"),
            Permission(S.ENABLE_SELF_EXPERIMENTATION, granted=True,
                       note="bounded simulation/internal/read-only "
                            "experiments only; no real-world test"),
            Permission(S.ENABLE_NURSERY_INTERVENTIONS, granted=True,
                       note="hypothesis tests may request bounded ecology "
                            "interventions; ecology safety validates them"),
            Permission(S.ENABLE_LATENT_HYPOTHESIS_TESTS, granted=True,
                       note="bounded latent-replay tests; evidence is "
                            "offline and never treated as real"),
            Permission(S.ENABLE_COUNTERFACTUAL_HYPOTHESIS_TESTS, granted=True,
                       note="counterfactual tests are allowed but their "
                            "evidence stays offline by construction"),
            Permission(S.ENABLE_HYPOTHESIS_WORLD_MODEL_UPDATES,
                       requires_approval=True,
                       note="updating the world model from supported "
                            "hypotheses needs approval and an evidence "
                            "threshold; offline support never promotes"),
            Permission(S.ENABLE_AUTOREGENERATION, granted=True,
                       note="diagnostics + state hygiene in bounded runs; "
                            "repairs runtime state, never source code"),
            Permission(S.ENABLE_STATE_HYGIENE, granted=True,
                       note="archive/quarantine inside the state dir; "
                            "evidence is preserved, never silently deleted"),
            Permission(S.ENABLE_SAFE_AUTO_REPAIR, requires_approval=True,
                       note="applying low-risk reversible repairs "
                            "automatically is off by default and needs "
                            "explicit config/approval"),
            Permission(S.ENABLE_CHECKPOINT_REPAIR, requires_approval=True,
                       note="checkpoint/identity-affecting repair needs "
                            "governance; history is never rewritten "
                            "silently"),
            Permission(S.ENABLE_MEMORY_COMPACTION, granted=True,
                       note="compaction preserves evidence summaries; "
                            "safety events are never compacted away"),
            Permission(S.ENABLE_SYMBOL_HYGIENE, granted=True,
                       note="mark stale/merge duplicates; symbols are never "
                            "renamed with human language"),
            Permission(S.ENABLE_WORLD_MODEL_HYGIENE, granted=True,
                       note="mark/weaken edges; contradiction evidence is "
                            "never deleted silently"),
            Permission(S.ENABLE_HABIT_HYGIENE, granted=True,
                       note="decay/retire within bounds; safety habits need "
                            "governance to weaken"),
            Permission(S.ENABLE_REPAIR_ROLLBACK, granted=True,
                       note="rolling back a harmful repair is always "
                            "allowed"),
            Permission(S.ENABLE_LOGOS_COMPLEXITY, granted=True,
                       note="LOGOS is a tension engine, not authority; "
                            "fracture/synthesis proposals only"),
            Permission(S.ENABLE_FRACTURE_DETECTION, granted=True,
                       note="non-mutating detection of internal tensions in "
                            "bounded runs"),
            Permission(S.ENABLE_SYNTHESIS_CANDIDATES, granted=True,
                       note="synthesis candidates are proposed, not assumed "
                            "true"),
            Permission(S.ENABLE_SAFE_SYNTHESIS, requires_approval=True,
                       note="applying synthesis automatically is off by "
                            "default and needs explicit config; structural "
                            "mutations reuse plasticity/auto-regeneration "
                            "policy"),
            Permission(S.ENABLE_ESC_PROCESS, granted=True,
                       note="Esc is an instability signal; it can request "
                            "stabilization but never execute real-world "
                            "actions"),
            Permission(S.ENABLE_COMPLEXITY_REGULATION, granted=True,
                       note="complexity bands are an operational signal, "
                            "never a consciousness/life score"),
            Permission(S.ENABLE_CONSCIENCE_ORCHESTRATOR, granted=True,
                       note="the unified runtime spine may assemble enabled "
                            "modules; no module is sovereign and nothing "
                            "actuates the real world"),
            Permission(S.ENABLE_FULL_DEVELOPMENTAL_SHORT_PROFILE,
                       requires_approval=True,
                       note="wiring every module into one bounded run is "
                            "opt-in and needs explicit acknowledgement"),
            Permission(S.ENABLE_MONTH_SCALE_DRY_RUN, requires_approval=True,
                       note="a simulated month-scale slice/plan is opt-in; it "
                            "is never a real month"),
            Permission(S.ENABLE_MONTH_SCALE_REAL_RUN, granted=False,
                       requires_approval=True,
                       note="a real month-scale run is off by default and "
                            "requires explicit human approval"),
            Permission(S.ENABLE_YEAR_SCALE_PLAN, requires_approval=True,
                       note="planning a year-scale run is opt-in; planning "
                            "never starts a run"),
            Permission(S.ENABLE_YEAR_SCALE_REAL_RUN, granted=False,
                       requires_approval=True,
                       note="a real year-scale run is off by default and "
                            "requires explicit human approval"),
        ]
        return cls(permissions={p.scope: p for p in rows})

    # -- queries -------------------------------------------------------------

    def get(self, scope: str) -> Permission:
        """The permission for ``scope`` (a denied placeholder if unknown)."""
        if scope in self.permissions:
            return self.permissions[scope]
        return Permission(scope, granted=False, requires_approval=True,
                          note="unknown scope: denied by default")

    def allows(self, scope: str) -> bool:
        """Is ``scope`` allowed outright (no approval needed)?"""
        if scope in ALWAYS_ALLOWED:
            return True
        perm = self.get(scope)
        return perm.granted and not perm.requires_approval

    def requires_approval(self, scope: str) -> bool:
        """Does ``scope`` need an explicit human approval record?"""
        if scope in ALWAYS_ALLOWED:
            return False
        return self.get(scope).requires_approval or not self.get(scope).granted

    def known_scopes(self) -> List[str]:
        return sorted(self.permissions)

    def granted_scopes(self) -> List[str]:
        return sorted(s for s in self.permissions if self.allows(s))

    # -- mutation (operator actions) ------------------------------------------

    def grant(self, scope: str, requires_approval: bool = False,
              note: str = "") -> Permission:
        perm = Permission(scope, granted=True,
                          requires_approval=requires_approval, note=note)
        self.permissions[scope] = perm
        return perm

    def revoke(self, scope: str) -> None:
        """Revoke a scope. The emergency stop can never be revoked."""
        if scope in ALWAYS_ALLOWED:
            raise ValueError(
                f"{scope!r} is always allowed and cannot be revoked")
        self.permissions[scope] = Permission(scope, granted=False)

    # -- serialization --------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "permissions": {s: p.to_dict()
                            for s, p in sorted(self.permissions.items())},
            "always_allowed": sorted(ALWAYS_ALLOWED),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PermissionSet":
        perms = {}
        for scope, row in (data.get("permissions") or {}).items():
            valid = {k: v for k, v in row.items()
                     if k in Permission.__dataclass_fields__}  # type: ignore[attr-defined]
            valid["scope"] = scope
            perms[scope] = Permission(**valid)
        return cls(permissions=perms)
