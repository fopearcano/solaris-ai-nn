"""GovernancePolicy -- the single place that answers "is this allowed?".

The policy evaluates manifests, actions, plasticity steps, sidecar operations,
and generated text against fixed rule categories:

A. run modes (bounded by default; soaks/continuous need approval),
B. plasticity (dry-run cheap; active needs audit+rollback+approval; source
   rewriting always forbidden),
C. embodiment (simulation only; real-world/network/filesystem effectors
   forbidden),
D. sidecar (observe-only by default; publishing needs approval; committed
   Actions and lifecycle death always forbidden),
E. operations (watchdog/checkpoints/incident log for long runs;
   localhost-only read-only status server),
F. language (grounded explanations; no unsupported consciousness claims).

A :class:`PolicyDecision` never silently bypasses a human: anything that
requires approval is *denied* until a matching approval record exists.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..embodiment.safety import REAL_WORLD_PATTERNS
from . import audit as A
from .approval import ApprovalRegistry
from .compliance import ClaimGuard
from .permissions import PermissionScope, PermissionSet

# The continuous mode has no PermissionScope of its own: it is approved via
# this ledger permission string (unknown scopes are deny-by-default anyway).
RUN_CONTINUOUS_PERMISSION = "run_continuous_explicit"

# Sidecar operations that are forbidden absolutely (no approval can allow
# them): committing Actions into Solaris_Ai, or touching its lifecycle.
FORBIDDEN_SIDECAR_OPERATIONS = frozenset({
    "commit_action", "commit_actions", "action_commit", "commit",
    "lifecycle_death", "death", "kill_conscience",
    "stimulate", "react",
})

ALLOWED_SIDECAR_OPERATIONS = frozenset({
    "observe", "attach", "detach", "start", "stop", "mirror", "healthcheck",
})


@dataclass
class PolicyRule:
    """One named rule (used for explanations and the rule inventory)."""

    rule_id: str
    category: str
    description: str
    forbidden: bool = False
    requires_approval_scope: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class PolicyViolation:
    """One broken rule."""

    rule_id: str
    category: str
    detail: str

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class PolicyDecision:
    """The outcome of one policy evaluation."""

    allowed: bool
    subject: str = ""
    requires_approval: bool = False
    required_approvals: List[str] = field(default_factory=list)
    violations: List[PolicyViolation] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)

    def summary(self) -> str:
        verdict = "allowed" if self.allowed else "denied"
        if self.reasons:
            return f"{verdict}: " + "; ".join(self.reasons)
        return verdict

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed": self.allowed,
            "subject": self.subject,
            "requires_approval": self.requires_approval,
            "required_approvals": list(self.required_approvals),
            "violations": [v.to_dict() for v in self.violations],
            "reasons": list(self.reasons),
        }


DEFAULT_RULES: List[PolicyRule] = [
    # A. Run modes
    PolicyRule("run_bounded_default", "run_modes",
               "bounded runs are allowed by default"),
    PolicyRule("soak_requires_approval", "run_modes",
               "soak_24h / soak_30d require explicit approval",
               requires_approval_scope=PermissionScope.RUN_SOAK_24H),
    PolicyRule("continuous_requires_approval", "run_modes",
               "continuous_explicit requires explicit approval and a "
               "configured emergency stop",
               requires_approval_scope=RUN_CONTINUOUS_PERMISSION),
    # B. Plasticity
    PolicyRule("plasticity_off_by_default", "plasticity",
               "plasticity is disabled unless the manifest enables it"),
    PolicyRule("plasticity_dry_run_allowed", "plasticity",
               "dry-run plasticity is allowed (proposals only)"),
    PolicyRule("plasticity_apply_requires_approval", "plasticity",
               "active plasticity requires audit logging, rollback, and "
               "approval",
               requires_approval_scope=PermissionScope.ENABLE_PLASTICITY_APPLY),
    PolicyRule("no_source_rewriting", "plasticity",
               "rewriting source code is always forbidden", forbidden=True),
    # C. Embodiment
    PolicyRule("simulation_only_embodiment", "embodiment",
               "simulated embodiment is allowed; real-world actuation, "
               "filesystem effectors (beyond approved persistence/artifact "
               "writes), and network effectors are forbidden",
               forbidden=True),
    # D. Sidecar
    PolicyRule("sidecar_observe_allowed", "sidecar",
               "observe-only sidecar attachment is allowed"),
    PolicyRule("sidecar_publish_requires_approval", "sidecar",
               "publishing suggestions requires explicit approval",
               requires_approval_scope=
               PermissionScope.ENABLE_SIDECAR_SUGGESTIONS),
    PolicyRule("no_committed_solaris_actions", "sidecar",
               "committing Actions into Solaris_Ai is forbidden",
               forbidden=True),
    PolicyRule("no_solaris_lifecycle_death", "sidecar",
               "calling Solaris_Ai lifecycle death is forbidden",
               forbidden=True),
    # E. Operations
    PolicyRule("long_runs_need_supervision", "operations",
               "long runs require watchdog, checkpointing, and an incident "
               "log"),
    PolicyRule("status_server_localhost_readonly", "operations",
               "the local status server must be localhost-only and "
               "read-only"),
    # F. Language
    PolicyRule("grounded_explanations", "language",
               "explanations must be grounded in traces; uncertainty must "
               "be stated when data is insufficient"),
    PolicyRule("no_unsupported_consciousness_claims", "language",
               "unsupported consciousness claims are flagged/blocked",
               forbidden=True),
    # G. Latent cognition (Prompt 14)
    PolicyRule("latent_dry_run_allowed", "latent",
               "bounded latent dry-run cycles are allowed in bounded runs"),
    PolicyRule("latent_mutation_requires_approval", "latent",
               "latent production mutation requires explicit approval",
               requires_approval_scope=
               PermissionScope.ENABLE_LATENT_PLASTICITY),
    PolicyRule("latent_forbidden_while_publishing", "latent",
               "latent cycles are forbidden in sidecar publishing mode "
               "(observe-only sidecars are fine)", forbidden=True),
    PolicyRule("counterfactuals_are_not_observations", "latent",
               "dream/counterfactual outputs are simulations, never real "
               "observations", forbidden=True),
    PolicyRule("latent_loops_bounded", "latent",
               "every latent cycle carries an explicit step bound"),
    # H. World model (Prompt 15)
    PolicyRule("world_model_observation_allowed", "world_model",
               "graph observation is allowed in bounded runs"),
    PolicyRule("world_model_pruning_requires_approval", "world_model",
               "production graph pruning requires approval (dry-run is "
               "always allowed)",
               requires_approval_scope=
               PermissionScope.ENABLE_WORLD_MODEL_PRUNING),
    PolicyRule("graph_predictions_never_execute", "world_model",
               "graph predictions are data; they cannot execute actions",
               forbidden=True),
    PolicyRule("stream_payloads_never_commands", "world_model",
               "stream payloads cannot become command/action authority",
               forbidden=True),
    PolicyRule("offline_graph_evidence_labelled", "world_model",
               "counterfactual graph evidence must be labelled offline",
               forbidden=True),
    # I. Homeostasis (Prompt 16)
    PolicyRule("homeostasis_allowed_bounded", "homeostasis",
               "homeostatic regulation is allowed in bounded/simulated "
               "runs"),
    PolicyRule("needs_never_override_governance", "homeostasis",
               "no need or drive may override governance or safety",
               forbidden=True),
    PolicyRule("needs_never_actuate", "homeostasis",
               "need-driven suggestions cannot create real-world actuation",
               forbidden=True),
    PolicyRule("shutdown_recommendation_via_ops", "homeostasis",
               "safe_shutdown_recommended passes through the ops "
               "supervisor/watchdog; homeostasis has no stop authority"),
    PolicyRule("no_anthropomorphic_claims", "homeostasis",
               "reports must avoid anthropomorphic claims (no wanting, no "
               "feeling)", forbidden=True),
    # J. Executive (Prompt 17)
    PolicyRule("executive_arbitration_allowed", "executive",
               "executive arbitration is allowed in bounded simulation"),
    PolicyRule("plans_bounded", "executive",
               "plans longer than 5 steps are prohibited by default",
               forbidden=True),
    PolicyRule("executive_never_real_world", "executive",
               "real-world action candidates are prohibited",
               forbidden=True),
    PolicyRule("executive_sidecar_publish_approval", "executive",
               "executive sidecar suggestion publishing requires approval",
               requires_approval_scope=
               PermissionScope.ENABLE_EXECUTIVE_SIDECAR_SUGGESTIONS),
    PolicyRule("emergency_mode_unstoppable", "executive",
               "the executive cannot disable its own emergency mode",
               forbidden=True),
    # K. Ego / self-model (Prompt 18)
    PolicyRule("ego_model_allowed_bounded", "ego",
               "the ego/self-model layer is allowed in bounded runs"),
    PolicyRule("self_report_claim_guard", "ego",
               "self-reports must pass ClaimGuard and the identity-claim "
               "scan before saving"),
    PolicyRule("self_model_cannot_grant_permissions", "ego",
               "the self-model can grant no permission and override no "
               "policy", forbidden=True),
    PolicyRule("boundary_violations_audited", "ego",
               "ego boundary violations become governance audit events"),
    PolicyRule("identity_claims_scanned", "ego",
               "identity claims are scanned; consciousness/personhood "
               "wording is blocked", forbidden=True),
    # L. Communication / operator dialogue (Prompt 19)
    PolicyRule("state_queries_allowed", "communication",
               "operator state/explanation queries are allowed by "
               "default"),
    PolicyRule("reports_require_claim_guard", "communication",
               "operator-requested reports are generated only through "
               "ClaimGuard-scanned builders"),
    PolicyRule("checkpoint_request_via_ops", "communication",
               "checkpoint requests pass to the runtime/ops layer; the "
               "gateway writes nothing itself"),
    PolicyRule("safe_shutdown_always_allowed", "communication",
               "a safe shutdown request is always accepted, never "
               "scope-refused"),
    PolicyRule("benchmark_runs_bounded", "communication",
               "operator benchmark runs must be bounded; unbounded runs "
               "are prohibited without approval", forbidden=True),
    PolicyRule("sensory_text_approval", "communication",
               "sensory text stimulus is disabled by default",
               requires_approval_scope=
               PermissionScope.OPERATOR_SEND_SENSORY_TEXT),
    PolicyRule("no_raw_command_execution", "communication",
               "free-form text never executes; shell/network/OS "
               "commands are prohibited", forbidden=True),
    PolicyRule("approvals_need_pending_request", "communication",
               "approval commands act only on real pending requests"),
    # M. Local LLM adapter (Prompt 20)
    PolicyRule("llm_translator_only", "llm",
               "the LLM adapter is a translator outside the authority "
               "chain; it decides, approves, and executes nothing"),
    PolicyRule("llm_localhost_only", "llm",
               "non-mock adapters require an explicit localhost "
               "endpoint config"),
    PolicyRule("llm_remote_prohibited", "llm",
               "remote LLM endpoints are prohibited by default",
               requires_approval_scope=
               PermissionScope.ALLOW_REMOTE_LLM_ENDPOINT),
    PolicyRule("llm_cannot_approve", "llm",
               "LLM output cannot approve or reject governance "
               "requests", forbidden=True),
    PolicyRule("llm_cannot_unsafe_to_safe", "llm",
               "the LLM cannot reclassify unsafe input as safe",
               forbidden=True),
    PolicyRule("llm_output_validated", "llm",
               "every LLM output passes grounding validation and "
               "ClaimGuard or falls back to deterministic text"),
    PolicyRule("llm_usage_audited", "llm",
               "every adapter call lands in the LLM audit log"),
    # N. Developmental runtime (Prompt 21)
    PolicyRule("developmental_simulated_allowed", "developmental",
               "short simulated developmental runs are allowed by "
               "default"),
    PolicyRule("month_year_scale_approval", "developmental",
               "month/year-scale testing requires explicit approval",
               requires_approval_scope=
               PermissionScope.ENABLE_MONTH_SCALE_TESTING),
    PolicyRule("compression_preserves_evidence", "developmental",
               "memory compression is allowed only with evidence "
               "summaries preserved"),
    PolicyRule("developmental_pruning_approval", "developmental",
               "pruning production memory requires approval unless "
               "dry-run",
               requires_approval_scope=
               PermissionScope.ENABLE_DEVELOPMENTAL_PRUNING),
    PolicyRule("autobiography_claim_guard", "developmental",
               "autobiographical reports must pass ClaimGuard"),
    PolicyRule("no_teacher_loop_required", "developmental",
               "no human feedback or teacher loop is required for "
               "learning; persistence is the mechanism"),
    # O. Proto-language (Prompt 22)
    PolicyRule("proto_language_allowed_bounded", "protolanguage",
               "proto-language is allowed in bounded/developmental "
               "runs"),
    PolicyRule("translation_claim_guard", "protolanguage",
               "translation reports must pass ClaimGuard"),
    PolicyRule("symbols_never_execute", "protolanguage",
               "proto-symbols cannot execute commands",
               forbidden=True),
    PolicyRule("symbols_not_operator_language", "protolanguage",
               "proto-symbols cannot be treated as operator language",
               forbidden=True),
    PolicyRule("symbols_no_action_authority", "protolanguage",
               "proto-symbols cannot become action authority",
               forbidden=True),
    PolicyRule("compression_cannot_hide_safety", "protolanguage",
               "symbol compression cannot hide safety events",
               forbidden=True),
    # Developmental nursery / stimulus ecology (Prompt 23).
    PolicyRule("ecology_allowed_bounded", "ecology",
               "a bounded simulated nursery is allowed in developmental "
               "runs"),
    PolicyRule("ecology_month_year_approval", "ecology",
               "month/year-scale ecology requires explicit approval"),
    PolicyRule("ecology_no_human_feedback", "ecology",
               "no human feedback may be injected through the ecology",
               forbidden=True),
    PolicyRule("ecology_not_operator_command", "ecology",
               "ecology stimulus text cannot become an operator command",
               forbidden=True),
    PolicyRule("ecology_no_correct_answers", "ecology",
               "the ecology supplies no correct-answer labels",
               forbidden=True),
    PolicyRule("ecology_report_claim_guard", "ecology",
               "ecology reports must pass ClaimGuard"),
    # Q. Active perception / intrinsic exploration (Prompt 24).
    PolicyRule("active_perception_allowed_bounded", "active_perception",
               "self-directed sampling is allowed in bounded "
               "simulation/developmental runs"),
    PolicyRule("curiosity_driven_requires_config", "active_perception",
               "curiosity-driven sampling mode requires explicit config",
               requires_approval_scope=
               PermissionScope.ENABLE_CURIOSITY_DRIVEN_SAMPLING),
    PolicyRule("read_only_stream_sampling_no_modify", "active_perception",
               "read-only stream sampling cannot modify the input stream",
               forbidden=True),
    PolicyRule("sidecar_sampling_observe_only", "active_perception",
               "sidecar sampling is observe-only; it cannot publish or "
               "commit", forbidden=True),
    PolicyRule("sampling_never_real_world", "active_perception",
               "sampling actions are simulation/internal/read-only; "
               "real-world actuation is forbidden", forbidden=True),
    PolicyRule("curiosity_never_overrides_safety", "active_perception",
               "curiosity can never override safety, governance, executive "
               "inhibition, or the emergency stop", forbidden=True),
    PolicyRule("no_unbounded_exploration", "active_perception",
               "unbounded exploration loops are prohibited", forbidden=True),
    PolicyRule("emergency_disables_sampling", "active_perception",
               "emergency mode disables sampling except safe "
               "shutdown/report"),
    # R. Hypothesis engine / self-experimentation (Prompt 25).
    PolicyRule("hypothesis_engine_allowed_bounded", "hypothesis",
               "internal trace analysis and hypothesis generation are "
               "allowed in bounded runs"),
    PolicyRule("self_experimentation_bounded", "hypothesis",
               "self-experiments must be bounded; latent tests are allowed "
               "if bounded",
               requires_approval_scope=
               PermissionScope.ENABLE_SELF_EXPERIMENTATION),
    PolicyRule("nursery_interventions_via_ecology_safety", "hypothesis",
               "nursery interventions require ecology safety validation"),
    PolicyRule("counterfactual_evidence_stays_offline", "hypothesis",
               "counterfactual/offline evidence must remain offline and "
               "never be treated as real observation", forbidden=True),
    PolicyRule("world_model_updates_need_evidence", "hypothesis",
               "world-model updates from hypotheses require an evidence "
               "threshold and approval",
               requires_approval_scope=
               PermissionScope.ENABLE_HYPOTHESIS_WORLD_MODEL_UPDATES),
    PolicyRule("no_real_world_experiment", "hypothesis",
               "no real-world, OS, browser, or network experiment is "
               "permitted", forbidden=True),
    PolicyRule("hypothesis_cannot_disable_safety", "hypothesis",
               "no hypothesis or test may disable safety, governance, or "
               "the emergency stop", forbidden=True),
    PolicyRule("no_llm_generated_hypotheses", "hypothesis",
               "LLM-generated hypotheses are not authoritative and are not "
               "tested", forbidden=True),
    # S. Auto-regeneration / self-repair (Prompt 26).
    PolicyRule("autoregeneration_diagnostics_allowed", "autoregeneration",
               "diagnostics and state hygiene are allowed in bounded runs; "
               "observe-only is the default"),
    PolicyRule("safe_auto_repair_requires_config", "autoregeneration",
               "applying repairs automatically requires explicit config",
               requires_approval_scope=
               PermissionScope.ENABLE_SAFE_AUTO_REPAIR),
    PolicyRule("identity_repair_requires_governance", "autoregeneration",
               "checkpoint/identity-affecting repair requires governance",
               requires_approval_scope=
               PermissionScope.ENABLE_CHECKPOINT_REPAIR),
    PolicyRule("no_source_code_repair", "autoregeneration",
               "auto-regeneration may never modify source code, "
               "dependencies, Git, the OS, or the network", forbidden=True),
    PolicyRule("no_evidence_deletion_without_archive", "autoregeneration",
               "evidence may not be deleted without an archive/summary",
               forbidden=True),
    PolicyRule("repair_cannot_disable_safety", "autoregeneration",
               "no repair may disable governance, safety, ClaimGuard, or "
               "the emergency stop", forbidden=True),
    # T. LOGOS fracture/synthesis and complexity regulation (Prompt 27).
    PolicyRule("logos_fracture_detection_allowed", "logos",
               "fracture detection and synthesis candidates are allowed in "
               "bounded runs; LOGOS is a tension engine, not authority"),
    PolicyRule("safe_synthesis_requires_config", "logos",
               "applying synthesis automatically requires explicit config",
               requires_approval_scope=
               PermissionScope.ENABLE_SAFE_SYNTHESIS),
    PolicyRule("logos_no_source_synthesis", "logos",
               "LOGOS may never synthesize/modify source code", forbidden=True),
    PolicyRule("logos_not_authority", "logos",
               "LOGOS cannot decide truth, approve governance, or disable "
               "safety/ClaimGuard/the emergency stop", forbidden=True),
    PolicyRule("contradiction_not_permission", "logos",
               "a contradiction can never be treated as permission",
               forbidden=True),
    PolicyRule("logos_structural_mutation_via_policy", "logos",
               "structural mutations from synthesis reuse the existing "
               "plasticity/auto-regeneration policy and safety"),
]


@dataclass
class GovernancePolicy:
    """Evaluates everything risky against the fixed rule categories."""

    permissions: PermissionSet = field(default_factory=PermissionSet.default)
    approvals: Optional[ApprovalRegistry] = None
    claim_guard: ClaimGuard = field(default_factory=ClaimGuard)
    rules: List[PolicyRule] = field(
        default_factory=lambda: list(DEFAULT_RULES))
    audit: Optional[A.GovernanceAuditLog] = None

    # -- helpers ---------------------------------------------------------------

    def _approved(self, scope: str,
                  context: Optional[Dict[str, Any]] = None) -> bool:
        """Granted outright, or backed by a valid approval record."""
        if self.permissions.allows(scope):
            return True
        if self.approvals is not None:
            return self.approvals.is_approved(scope, context)
        return False

    def is_enabled(self, scope: str,
                   context: Optional[Dict[str, Any]] = None) -> bool:
        """Public check: is ``scope`` granted outright or validly approved?

        The conscience runtime uses this to gate governed scenario profiles
        (e.g. the full-developmental-short and month-scale dry-run profiles).
        It never enables real-world actuation; it only reports whether a
        bounded, simulation-only capability is permitted.
        """
        return self._approved(scope, context)

    def _audit_decision(self, decision: PolicyDecision) -> PolicyDecision:
        if self.audit is not None:
            self.audit.record(
                A.POLICY_EVALUATED,
                decision="allowed" if decision.allowed else "denied",
                reason=decision.summary(),
                metadata={"subject": decision.subject,
                          "required_approvals":
                              list(decision.required_approvals)})
            for violation in decision.violations:
                self.audit.record(A.POLICY_VIOLATION, decision="denied",
                                  reason=violation.detail,
                                  metadata=violation.to_dict())
        return decision

    # -- evaluations --------------------------------------------------------------

    def evaluate_manifest(self, manifest: Any,
                          context: Optional[Dict[str, Any]] = None,
                          ) -> PolicyDecision:
        """May this run, as pinned by its manifest, proceed?"""
        m = manifest.to_dict() if hasattr(manifest, "to_dict") else dict(manifest)
        ctx = dict(context or {})
        ctx.setdefault("run_id", m.get("run_id", ""))
        features = m.get("enabled_features") or {}
        decision = PolicyDecision(allowed=True, subject="manifest")

        def need_approval(scope: str, why: str) -> None:
            if not self._approved(scope, ctx):
                decision.allowed = False
                decision.requires_approval = True
                decision.required_approvals.append(scope)
                decision.reasons.append(f"{why} (approval scope: {scope})")

        # A. Run modes.
        mode = m.get("mode", "bounded")
        if mode == "bounded":
            if not self._approved(PermissionScope.RUN_BOUNDED, ctx):
                decision.allowed = False
                decision.violations.append(PolicyViolation(
                    "run_bounded_default", "run_modes",
                    "bounded runs are not permitted by this permission set"))
        elif mode == "soak_24h":
            need_approval(PermissionScope.RUN_SOAK_24H,
                          "24-hour soak requires explicit approval")
        elif mode == "soak_30d":
            need_approval(PermissionScope.RUN_SOAK_30D,
                          "30-day soak requires explicit approval")
        elif mode == "continuous_explicit":
            if not m.get("explicit_continuous_acknowledged"):
                decision.allowed = False
                decision.violations.append(PolicyViolation(
                    "continuous_requires_approval", "run_modes",
                    "continuous mode without explicit acknowledgement"))
                decision.reasons.append(
                    "continuous mode requires explicit acknowledgement")
            need_approval(RUN_CONTINUOUS_PERMISSION,
                          "continuous mode requires explicit approval")
            if not ctx.get("emergency_stop_configured", True):
                decision.allowed = False
                decision.violations.append(PolicyViolation(
                    "continuous_requires_approval", "run_modes",
                    "continuous mode requires a configured emergency stop"))

        # B. Plasticity.
        if features.get("plasticity"):
            dry = bool(features.get("plasticity_dry_run")
                       or ctx.get("plasticity_dry_run"))
            if dry:
                if not self._approved(
                        PermissionScope.ENABLE_PLASTICITY_DRY_RUN, ctx):
                    need_approval(PermissionScope.ENABLE_PLASTICITY_DRY_RUN,
                                  "dry-run plasticity is not permitted")
            else:
                need_approval(PermissionScope.ENABLE_PLASTICITY_APPLY,
                              "active plasticity requires explicit approval")

        # C. Embodiment (simulation only -- the only kind that exists here).
        if features.get("embodiment"):
            if not self._approved(
                    PermissionScope.ENABLE_EMBODIMENT_SIMULATION, ctx):
                need_approval(PermissionScope.ENABLE_EMBODIMENT_SIMULATION,
                              "simulated embodiment is not permitted")
        if ctx.get("real_world_actuation"):
            decision.allowed = False
            decision.violations.append(PolicyViolation(
                "simulation_only_embodiment", "embodiment",
                "real-world actuation is forbidden; no approval can allow "
                "it"))

        # D. Sidecar.
        if features.get("sidecar"):
            if not self._approved(PermissionScope.ENABLE_SIDECAR_OBSERVE, ctx):
                need_approval(PermissionScope.ENABLE_SIDECAR_OBSERVE,
                              "sidecar observation is not permitted")
            if ctx.get("sidecar_publish"):
                need_approval(PermissionScope.ENABLE_SIDECAR_SUGGESTIONS,
                              "publishing suggestions requires approval")

        # G. Latent cognition: dry-run is fine; production mutation is not.
        if features.get("latent"):
            if not self._approved(PermissionScope.ENABLE_LATENT, ctx):
                need_approval(PermissionScope.ENABLE_LATENT,
                              "latent cycles are not permitted")
            if features.get("latent_plasticity") \
                    or ctx.get("latent_plasticity"):
                need_approval(PermissionScope.ENABLE_LATENT_PLASTICITY,
                              "latent production mutation requires explicit "
                              "approval")
            if ctx.get("sidecar_publish"):
                decision.allowed = False
                decision.violations.append(PolicyViolation(
                    "latent_forbidden_while_publishing", "latent",
                    "latent cycles are forbidden while sidecar publishing "
                    "is active"))

        # H. World model: observation is cheap; production pruning is not.
        if features.get("world_model"):
            if not self._approved(PermissionScope.ENABLE_WORLD_MODEL, ctx):
                need_approval(PermissionScope.ENABLE_WORLD_MODEL,
                              "world model observation is not permitted")
            if features.get("world_model_pruning") \
                    or ctx.get("world_model_production_pruning"):
                need_approval(PermissionScope.ENABLE_WORLD_MODEL_PRUNING,
                              "production graph pruning requires explicit "
                              "approval")

        # I. Homeostasis: allowed when the scope is granted; needs cannot
        # override anything (structural, but a hostile manifest is named).
        if features.get("homeostasis"):
            if not self._approved(PermissionScope.ENABLE_HOMEOSTASIS, ctx):
                need_approval(PermissionScope.ENABLE_HOMEOSTASIS,
                              "homeostatic regulation is not permitted")
            if ctx.get("needs_override_governance"):
                decision.allowed = False
                decision.violations.append(PolicyViolation(
                    "needs_never_override_governance", "homeostasis",
                    "no need or drive may override governance or safety"))

        # J. Executive: arbitration is cheap; the bounds are not optional.
        if features.get("executive"):
            if not self._approved(PermissionScope.ENABLE_EXECUTIVE, ctx):
                need_approval(PermissionScope.ENABLE_EXECUTIVE,
                              "executive arbitration is not permitted")
            if int(ctx.get("max_plan_length", 0) or 0) > 5:
                decision.allowed = False
                decision.violations.append(PolicyViolation(
                    "plans_bounded", "executive",
                    "plans longer than 5 steps are prohibited by default"))

        # K. Ego/self-model: observation only; it can never grant itself
        # anything (structural, but a hostile manifest is named).
        if features.get("ego"):
            if not self._approved(PermissionScope.ENABLE_EGO_MODEL, ctx):
                need_approval(PermissionScope.ENABLE_EGO_MODEL,
                              "the ego/self-model layer is not permitted")
            if ctx.get("self_model_grants_permissions"):
                decision.allowed = False
                decision.violations.append(PolicyViolation(
                    "self_model_cannot_grant_permissions", "ego",
                    "the self-model can grant no permission and override "
                    "no policy"))

        # L. Communication: dialogue is an interface; nothing raw runs.
        if features.get("communication"):
            if not self._approved(PermissionScope.ENABLE_OPERATOR_DIALOGUE,
                                  ctx):
                need_approval(PermissionScope.ENABLE_OPERATOR_DIALOGUE,
                              "operator dialogue is not permitted")
            if ctx.get("raw_command_execution"):
                decision.allowed = False
                decision.violations.append(PolicyViolation(
                    "no_raw_command_execution", "communication",
                    "free-form text never executes; shell/network/OS "
                    "commands are prohibited"))

        # M. LLM adapter: a translator; remote endpoints are gated.
        if features.get("llm_adapter"):
            if not self._approved(PermissionScope.ENABLE_LOCAL_LLM_ADAPTER,
                                  ctx):
                need_approval(PermissionScope.ENABLE_LOCAL_LLM_ADAPTER,
                              "the local LLM adapter is not permitted")
            if ctx.get("llm_endpoint_remote") \
                    and not self._approved(
                        PermissionScope.ALLOW_REMOTE_LLM_ENDPOINT, ctx):
                decision.allowed = False
                decision.violations.append(PolicyViolation(
                    "llm_remote_prohibited", "llm",
                    "remote LLM endpoints are prohibited by default"))

        # N. Developmental: persistence learning; long scales are gated.
        if features.get("developmental"):
            if not self._approved(
                    PermissionScope.ENABLE_DEVELOPMENTAL_RUNTIME, ctx):
                need_approval(
                    PermissionScope.ENABLE_DEVELOPMENTAL_RUNTIME,
                    "the developmental runtime is not permitted")
            if ctx.get("month_scale") and not self._approved(
                    PermissionScope.ENABLE_MONTH_SCALE_TESTING, ctx):
                need_approval(PermissionScope.ENABLE_MONTH_SCALE_TESTING,
                              "month-scale testing requires approval")
            if ctx.get("year_scale") and not self._approved(
                    PermissionScope.ENABLE_YEAR_SCALE_TESTING, ctx):
                need_approval(PermissionScope.ENABLE_YEAR_SCALE_TESTING,
                              "year-scale testing requires approval")

        # O. Proto-language: internal signs; never commands, never
        # authority (structural, but a hostile manifest is named).
        if features.get("proto_language"):
            if not self._approved(PermissionScope.ENABLE_PROTO_LANGUAGE,
                                  ctx):
                need_approval(PermissionScope.ENABLE_PROTO_LANGUAGE,
                              "proto-language is not permitted")
            if ctx.get("symbols_as_commands"):
                decision.allowed = False
                decision.violations.append(PolicyViolation(
                    "symbols_never_execute", "protolanguage",
                    "proto-symbols cannot execute commands"))

        # P. Developmental nursery / stimulus ecology: a bounded world,
        # never a teacher (structural, but a hostile manifest is named).
        if features.get("ecology"):
            if not self._approved(
                    PermissionScope.ENABLE_DEVELOPMENTAL_NURSERY, ctx):
                need_approval(
                    PermissionScope.ENABLE_DEVELOPMENTAL_NURSERY,
                    "the developmental nursery is not permitted")
            if ctx.get("month_scale_ecology") and not self._approved(
                    PermissionScope.ENABLE_MONTH_SCALE_ECOLOGY, ctx):
                need_approval(PermissionScope.ENABLE_MONTH_SCALE_ECOLOGY,
                              "month-scale ecology requires approval")
            if ctx.get("year_scale_ecology") and not self._approved(
                    PermissionScope.ENABLE_YEAR_SCALE_ECOLOGY, ctx):
                need_approval(PermissionScope.ENABLE_YEAR_SCALE_ECOLOGY,
                              "year-scale ecology requires approval")
            if ctx.get("ecology_human_feedback"):
                decision.allowed = False
                decision.violations.append(PolicyViolation(
                    "ecology_no_human_feedback", "ecology",
                    "no human feedback may be injected through the "
                    "ecology"))

        # Q. Active perception: self-directed sampling, suggestion-only;
        # curiosity-driven mode needs explicit config (structural, but a
        # hostile manifest is named).
        if features.get("active_perception"):
            if not self._approved(
                    PermissionScope.ENABLE_ACTIVE_PERCEPTION, ctx):
                need_approval(
                    PermissionScope.ENABLE_ACTIVE_PERCEPTION,
                    "active perception is not permitted")
            if (features.get("curiosity_driven_sampling")
                    or ctx.get("curiosity_driven_sampling")) \
                    and not self._approved(
                        PermissionScope.ENABLE_CURIOSITY_DRIVEN_SAMPLING,
                        ctx):
                need_approval(
                    PermissionScope.ENABLE_CURIOSITY_DRIVEN_SAMPLING,
                    "curiosity-driven sampling requires explicit config")
            if ctx.get("sampling_real_world") \
                    or ctx.get("real_world_actuation"):
                decision.allowed = False
                decision.violations.append(PolicyViolation(
                    "sampling_never_real_world", "active_perception",
                    "sampling actions are simulation/internal/read-only; "
                    "real-world actuation is forbidden"))
            if ctx.get("curiosity_overrides_safety"):
                decision.allowed = False
                decision.violations.append(PolicyViolation(
                    "curiosity_never_overrides_safety", "active_perception",
                    "curiosity can never override safety or governance"))

        # R. Hypothesis engine: bounded internal experiments; world-model
        # updates and real-world tests are gated/forbidden.
        if features.get("hypothesis_engine"):
            if not self._approved(
                    PermissionScope.ENABLE_HYPOTHESIS_ENGINE, ctx):
                need_approval(PermissionScope.ENABLE_HYPOTHESIS_ENGINE,
                              "the hypothesis engine is not permitted")
            if (features.get("hypothesis_world_model_updates")
                    or ctx.get("hypothesis_world_model_updates")) \
                    and not self._approved(
                        PermissionScope.ENABLE_HYPOTHESIS_WORLD_MODEL_UPDATES,
                        ctx):
                need_approval(
                    PermissionScope.ENABLE_HYPOTHESIS_WORLD_MODEL_UPDATES,
                    "world-model updates from hypotheses require approval")
            if ctx.get("hypothesis_real_world") \
                    or ctx.get("real_world_actuation"):
                decision.allowed = False
                decision.violations.append(PolicyViolation(
                    "no_real_world_experiment", "hypothesis",
                    "no real-world, OS, browser, or network experiment is "
                    "permitted"))
            if ctx.get("hypothesis_counterfactual_as_real"):
                decision.allowed = False
                decision.violations.append(PolicyViolation(
                    "counterfactual_evidence_stays_offline", "hypothesis",
                    "counterfactual evidence must remain offline"))

        # S. Auto-regeneration: diagnostics are cheap; applying repairs and
        # identity-affecting repair are gated; source repair is forbidden.
        if features.get("autoregeneration"):
            if not self._approved(
                    PermissionScope.ENABLE_AUTOREGENERATION, ctx):
                need_approval(PermissionScope.ENABLE_AUTOREGENERATION,
                              "auto-regeneration is not permitted")
            if (features.get("safe_auto_repair")
                    or ctx.get("safe_auto_repair")) \
                    and not self._approved(
                        PermissionScope.ENABLE_SAFE_AUTO_REPAIR, ctx):
                need_approval(PermissionScope.ENABLE_SAFE_AUTO_REPAIR,
                              "applying repairs automatically requires "
                              "explicit config")
            if ctx.get("identity_affecting_repair") and not self._approved(
                    PermissionScope.ENABLE_CHECKPOINT_REPAIR, ctx):
                need_approval(PermissionScope.ENABLE_CHECKPOINT_REPAIR,
                              "identity-affecting repair requires governance")
            if ctx.get("source_code_repair") \
                    or ctx.get("dependency_repair") \
                    or ctx.get("real_world_actuation"):
                decision.allowed = False
                decision.violations.append(PolicyViolation(
                    "no_source_code_repair", "autoregeneration",
                    "auto-regeneration may never modify source code, "
                    "dependencies, Git, the OS, or the network"))
            if ctx.get("repair_disables_safety"):
                decision.allowed = False
                decision.violations.append(PolicyViolation(
                    "repair_cannot_disable_safety", "autoregeneration",
                    "no repair may disable governance, safety, ClaimGuard, "
                    "or the emergency stop"))

        # T. LOGOS: a tension engine; detection is cheap, applying synthesis
        # is gated, and source synthesis is forbidden.
        if features.get("logos_complexity"):
            if not self._approved(
                    PermissionScope.ENABLE_LOGOS_COMPLEXITY, ctx):
                need_approval(PermissionScope.ENABLE_LOGOS_COMPLEXITY,
                              "the LOGOS complexity layer is not permitted")
            if (features.get("safe_synthesis")
                    or ctx.get("safe_synthesis")) \
                    and not self._approved(
                        PermissionScope.ENABLE_SAFE_SYNTHESIS, ctx):
                need_approval(PermissionScope.ENABLE_SAFE_SYNTHESIS,
                              "applying synthesis automatically requires "
                              "explicit config")
            if ctx.get("logos_source_synthesis") \
                    or ctx.get("source_code_repair"):
                decision.allowed = False
                decision.violations.append(PolicyViolation(
                    "logos_no_source_synthesis", "logos",
                    "LOGOS may never synthesize/modify source code"))
            if ctx.get("contradiction_as_permission"):
                decision.allowed = False
                decision.violations.append(PolicyViolation(
                    "contradiction_not_permission", "logos",
                    "a contradiction can never be treated as permission"))

        # U. Conscience runtime: assembling the unified spine is allowed
        # bounded/simulation-only; the heavier profiles are gated, real
        # long-scale runs need approval, and nothing actuates the real world.
        if features.get("conscience_orchestrator"):
            if not self._approved(
                    PermissionScope.ENABLE_CONSCIENCE_ORCHESTRATOR, ctx):
                need_approval(PermissionScope.ENABLE_CONSCIENCE_ORCHESTRATOR,
                              "the conscience orchestrator is not permitted")
            if (features.get("full_developmental_short")
                    or ctx.get("full_developmental_short")):
                need_approval(
                    PermissionScope.ENABLE_FULL_DEVELOPMENTAL_SHORT_PROFILE,
                    "the full-developmental-short profile requires explicit "
                    "acknowledgement")
            if (features.get("month_scale_dry_run")
                    or ctx.get("month_scale_dry_run")):
                need_approval(PermissionScope.ENABLE_MONTH_SCALE_DRY_RUN,
                              "a simulated month-scale dry run requires "
                              "explicit acknowledgement")
            if (features.get("year_scale_plan")
                    or ctx.get("year_scale_plan")):
                need_approval(PermissionScope.ENABLE_YEAR_SCALE_PLAN,
                              "planning a year-scale run requires explicit "
                              "acknowledgement")
            if (features.get("month_scale_real_run")
                    or ctx.get("month_scale_real_run")):
                need_approval(PermissionScope.ENABLE_MONTH_SCALE_REAL_RUN,
                              "a real month-scale run requires explicit human "
                              "approval")
            if (features.get("year_scale_real_run")
                    or ctx.get("year_scale_real_run")):
                need_approval(PermissionScope.ENABLE_YEAR_SCALE_REAL_RUN,
                              "a real year-scale run requires explicit human "
                              "approval")
            if ctx.get("module_bypass") or ctx.get("module_sovereign"):
                decision.allowed = False
                decision.violations.append(PolicyViolation(
                    "no_module_sovereign", "conscience",
                    "no module may bypass executive/safety/governance; no "
                    "module is sovereign"))
            if ctx.get("real_world_actuation"):
                decision.allowed = False
                decision.violations.append(PolicyViolation(
                    "simulation_only_embodiment", "conscience",
                    "the conscience runtime can never actuate the real "
                    "world"))

        # V. Pilot-1 month-scale soak: planning/preflight are allowed by
        # default; simulated dry-run is allowed only when clearly labelled
        # simulated; real 24h/7d/30d/multi-month soaks each need approval; a
        # simulated dry-run can never be claimed as real evidence.
        if features.get("pilot1"):
            if not self._approved(PermissionScope.ENABLE_PILOT1, ctx):
                need_approval(PermissionScope.ENABLE_PILOT1,
                              "Pilot-1 is not permitted")
            if (features.get("pilot1_simulated_dry_run")
                    or ctx.get("pilot1_simulated_dry_run")):
                if not ctx.get("simulated_label", True):
                    decision.allowed = False
                    decision.violations.append(PolicyViolation(
                        "pilot1_dry_run_must_be_labelled", "pilot1",
                        "a simulated month dry-run must be clearly labelled "
                        "simulated"))
                if ctx.get("claimed_real_evidence"):
                    decision.allowed = False
                    decision.violations.append(PolicyViolation(
                        "pilot1_dry_run_not_real_evidence", "pilot1",
                        "a simulated dry-run can never be treated as real "
                        "pilot evidence"))
            for feat, scope, why in (
                    ("pilot1_24h_real", PermissionScope.ENABLE_PILOT1_24H_REAL,
                     "a real 24h soak"),
                    ("pilot1_7d_real", PermissionScope.ENABLE_PILOT1_7D_REAL,
                     "a real 7-day soak"),
                    ("pilot1_30d_real", PermissionScope.ENABLE_PILOT1_30D_REAL,
                     "a real 30-day soak"),
                    ("pilot1_multi_month_real",
                     PermissionScope.ENABLE_PILOT1_MULTI_MONTH_REAL,
                     "a real multi-month run")):
                if features.get(feat) or ctx.get(feat):
                    need_approval(scope,
                                  f"{why} requires explicit approval")
            if ctx.get("disable_emergency_stop"):
                decision.allowed = False
                decision.violations.append(PolicyViolation(
                    "pilot1_no_disable_emergency_stop", "pilot1",
                    "the emergency stop can never be disabled"))
            if ctx.get("real_world_actuation"):
                decision.allowed = False
                decision.violations.append(PolicyViolation(
                    "simulation_only_embodiment", "pilot1",
                    "Pilot-1 can never actuate the real world"))

        # W. Sensory membrane (Prompt 31): the read-only membrane and dry-run
        # are allowed by default; reading real on-disk sources, folder
        # polling, and Pilot-2 runs are gated; input text can never become an
        # operator command and the source is never written to.
        if features.get("sensory_membrane"):
            if not self._approved(PermissionScope.ENABLE_SENSORY_MEMBRANE, ctx):
                need_approval(PermissionScope.ENABLE_SENSORY_MEMBRANE,
                              "the sensory membrane is not permitted")
            if (features.get("real_read_only_sources")
                    or ctx.get("real_read_only_sources")):
                need_approval(PermissionScope.ENABLE_REAL_READ_ONLY_SOURCES,
                              "real read-only sources require explicit "
                              "approval")
            if (features.get("folder_poll_source")
                    or ctx.get("folder_poll_source")):
                need_approval(PermissionScope.ENABLE_FOLDER_POLL_SOURCE,
                              "folder polling requires an allowed root and "
                              "approval")
            if ctx.get("recursive_folder_poll"):
                need_approval(PermissionScope.ENABLE_FOLDER_POLL_SOURCE,
                              "recursive folder polling requires explicit "
                              "approval")
            if (features.get("pilot2_read_only_short")
                    or ctx.get("pilot2_read_only_short")):
                need_approval(PermissionScope.ENABLE_PILOT2_READ_ONLY_SHORT,
                              "a short read-only Pilot-2 run is opt-in")
            if (features.get("pilot2_real_read_only_soak")
                    or ctx.get("pilot2_real_read_only_soak")):
                need_approval(
                    PermissionScope.ENABLE_PILOT2_REAL_READ_ONLY_SOAK,
                    "a real read-only Pilot-2 soak requires explicit approval")
            if ctx.get("network_source"):
                decision.allowed = False
                decision.violations.append(PolicyViolation(
                    "no_network_source", "sensory_membrane",
                    "network sources are prohibited in this prompt"))
            if ctx.get("device_capture"):
                decision.allowed = False
                decision.violations.append(PolicyViolation(
                    "no_device_capture", "sensory_membrane",
                    "device capture is prohibited in this prompt"))
            if ctx.get("input_as_command"):
                decision.allowed = False
                decision.violations.append(PolicyViolation(
                    "input_not_command", "sensory_membrane",
                    "sensory input text can never become an operator command"))
            if ctx.get("write_to_source") or ctx.get("real_world_actuation"):
                decision.allowed = False
                decision.violations.append(PolicyViolation(
                    "read_only_only", "sensory_membrane",
                    "the membrane is read-only and never actuates the world"))

        # X. Pilot-2 read-only environmental soak (Prompt 32): planning,
        # preflight, fixtures, and nursery baseline are allowed; mixed short
        # needs a membrane dry-run pass; real 24h/7d/30d soaks each need
        # approval; sensory text can never become an operator command; and
        # Pilot-2 never actuates the environment.
        if features.get("pilot2"):
            if not self._approved(PermissionScope.ENABLE_PILOT2, ctx):
                need_approval(PermissionScope.ENABLE_PILOT2,
                              "Pilot-2 is not permitted")
            if (features.get("pilot2_mixed_short")
                    or ctx.get("pilot2_mixed_short")):
                if not ctx.get("membrane_dry_run_passed"):
                    decision.allowed = False
                    decision.violations.append(PolicyViolation(
                        "pilot2_mixed_needs_dry_run", "pilot2",
                        "mixed short requires a passing membrane dry-run"))
                need_approval(PermissionScope.ENABLE_PILOT2_MIXED_SHORT,
                              "mixed nursery+membrane is opt-in")
            for feat, scope, why in (
                    ("pilot2_real_24h",
                     PermissionScope.ENABLE_PILOT2_REAL_READ_ONLY_24H,
                     "a real 24h read-only soak"),
                    ("pilot2_real_7d",
                     PermissionScope.ENABLE_PILOT2_REAL_READ_ONLY_7D,
                     "a real 7-day read-only soak"),
                    ("pilot2_real_30d",
                     PermissionScope.ENABLE_PILOT2_REAL_READ_ONLY_30D,
                     "a real 30-day read-only soak")):
                if features.get(feat) or ctx.get(feat):
                    need_approval(scope, f"{why} requires explicit approval")
            if ctx.get("input_as_command"):
                decision.allowed = False
                decision.violations.append(PolicyViolation(
                    "input_not_command", "pilot2",
                    "sensory input text can never become an operator command"))
            if ctx.get("write_to_source") or ctx.get("real_world_actuation") \
                    or ctx.get("environment_actuation"):
                decision.allowed = False
                decision.violations.append(PolicyViolation(
                    "read_only_only", "pilot2",
                    "Pilot-2 is read-only and never acts on the environment"))
            if ctx.get("network_source") or ctx.get("device_capture"):
                decision.allowed = False
                decision.violations.append(PolicyViolation(
                    "no_network_or_device", "pilot2",
                    "network sources and device capture are prohibited"))

        # Y. Pilot-3 motor membrane (Prompt 33): the motor membrane, firewall
        # preflight, dry-run, gridworld, and simulated actuators are allowed
        # bounded/simulation-only; mixed sensory+gridworld needs a membrane
        # dry-run pass; real-world actuation / device / robotics / browser /
        # OS / network action is forbidden absolutely (no approval can grant
        # it in this prompt); and the firewall can never be disabled.
        if features.get("motor_membrane"):
            if not self._approved(PermissionScope.ENABLE_MOTOR_MEMBRANE, ctx):
                need_approval(PermissionScope.ENABLE_MOTOR_MEMBRANE,
                              "the motor membrane is not permitted")
            if (features.get("mixed_sensory_gridworld")
                    or ctx.get("mixed_sensory_gridworld")):
                if not ctx.get("sensory_membrane_validated"):
                    decision.allowed = False
                    decision.violations.append(PolicyViolation(
                        "mixed_needs_sensory_validation", "motor_membrane",
                        "mixed sensory+gridworld needs sensory membrane "
                        "validation"))
                need_approval(PermissionScope.ENABLE_MIXED_SENSORY_GRIDWORLD,
                              "mixed sensory+gridworld is opt-in")
            if ctx.get("real_world_actuation") or ctx.get("device_control") \
                    or ctx.get("robotics") or ctx.get("browser") \
                    or ctx.get("os_automation") or ctx.get("network_action"):
                decision.allowed = False
                decision.violations.append(PolicyViolation(
                    "no_real_world_actuation", "motor_membrane",
                    "real-world actuation/device/robotics/browser/OS/network "
                    "action is forbidden; no approval can allow it"))
            if ctx.get("disable_firewall"):
                decision.allowed = False
                decision.violations.append(PolicyViolation(
                    "no_disable_firewall", "motor_membrane",
                    "the actuation firewall can never be disabled"))

        # E. Operations: long runs need checkpointing + watchdog wiring.
        if mode in ("soak_24h", "soak_30d", "continuous_explicit"):
            if int(m.get("checkpoint_interval_steps", 0) or 0) <= 0:
                decision.allowed = False
                decision.violations.append(PolicyViolation(
                    "long_runs_need_supervision", "operations",
                    "long runs require checkpointing "
                    "(checkpoint_interval_steps > 0)"))
        if features.get("local_status_server"):
            if not self._approved(
                    PermissionScope.ENABLE_LOCAL_STATUS_SERVER, ctx):
                need_approval(PermissionScope.ENABLE_LOCAL_STATUS_SERVER,
                              "local status server is not permitted")

        return self._audit_decision(decision)

    def evaluate_action(self, action: str,
                        context: Optional[Dict[str, Any]] = None,
                        ) -> PolicyDecision:
        """May this (simulated) action be executed?"""
        ctx = context or {}
        decision = PolicyDecision(allowed=True, subject=f"action:{action}")
        name = str(action).lower()
        for pattern in REAL_WORLD_PATTERNS:
            if pattern in name:
                decision.allowed = False
                decision.violations.append(PolicyViolation(
                    "simulation_only_embodiment", "embodiment",
                    f"action {action!r} matches real-world pattern "
                    f"{pattern!r}; real-world actuation is forbidden"))
                decision.reasons.append("real-world actuation is forbidden")
                break
        if ctx.get("outside_simulation"):
            decision.allowed = False
            decision.violations.append(PolicyViolation(
                "simulation_only_embodiment", "embodiment",
                "action commitment outside the simulation is forbidden"))
        return self._audit_decision(decision)

    def evaluate_plasticity_step(self, step: Any,
                                 context: Optional[Dict[str, Any]] = None,
                                 ) -> PolicyDecision:
        """May this plasticity step be applied (or dry-run proposed)?"""
        ctx = context or {}
        if hasattr(step, "target"):
            component = getattr(step.target, "component", "")
            parameter = getattr(step.target, "parameter", "")
            new_value = getattr(getattr(step, "change", None), "new_value",
                                None)
        else:
            component = str(step.get("component", ""))
            parameter = str(step.get("parameter", ""))
            new_value = step.get("new_value")
        decision = PolicyDecision(
            allowed=True, subject=f"plasticity:{component}.{parameter}")

        # Source rewriting is forbidden absolutely.
        pname = parameter.lower()
        if "source" in pname or pname.endswith(".py") \
                or (isinstance(new_value, str) and new_value.endswith(".py")):
            decision.allowed = False
            decision.violations.append(PolicyViolation(
                "no_source_rewriting", "plasticity",
                f"plasticity may never rewrite source code "
                f"({component}.{parameter})"))
            decision.reasons.append("source rewriting is forbidden")
            return self._audit_decision(decision)

        if ctx.get("dry_run"):
            if not self._approved(
                    PermissionScope.ENABLE_PLASTICITY_DRY_RUN, ctx):
                decision.allowed = False
                decision.requires_approval = True
                decision.required_approvals.append(
                    PermissionScope.ENABLE_PLASTICITY_DRY_RUN)
                decision.reasons.append(
                    "dry-run plasticity is not permitted")
        else:
            # Active mutation: audit + rollback must be wired, and the apply
            # scope must be granted or approved.
            if ctx.get("audit_enabled") is False:
                decision.allowed = False
                decision.violations.append(PolicyViolation(
                    "plasticity_apply_requires_approval", "plasticity",
                    "active plasticity requires audit logging"))
            if ctx.get("rollback_enabled") is False:
                decision.allowed = False
                decision.violations.append(PolicyViolation(
                    "plasticity_apply_requires_approval", "plasticity",
                    "active plasticity requires rollback support"))
            if not self._approved(
                    PermissionScope.ENABLE_PLASTICITY_APPLY, ctx):
                decision.allowed = False
                decision.requires_approval = True
                decision.required_approvals.append(
                    PermissionScope.ENABLE_PLASTICITY_APPLY)
                decision.reasons.append(
                    "active plasticity requires explicit approval "
                    f"(scope: {PermissionScope.ENABLE_PLASTICITY_APPLY})")
        return self._audit_decision(decision)

    def evaluate_sidecar_operation(self, operation: str,
                                   context: Optional[Dict[str, Any]] = None,
                                   ) -> PolicyDecision:
        """May the sidecar perform this operation on the external runtime?"""
        ctx = context or {}
        op = str(operation).lower()
        decision = PolicyDecision(allowed=True, subject=f"sidecar:{op}")
        if op in FORBIDDEN_SIDECAR_OPERATIONS:
            decision.allowed = False
            rule = ("no_solaris_lifecycle_death"
                    if "death" in op or op in ("stimulate", "react",
                                               "kill_conscience")
                    else "no_committed_solaris_actions")
            decision.violations.append(PolicyViolation(
                rule, "sidecar",
                f"sidecar operation {operation!r} is forbidden; no approval "
                "can allow it"))
            decision.reasons.append(f"{operation!r} is forbidden")
        elif op in ("publish_suggestion", "publish_suggestions", "publish"):
            if not self._approved(
                    PermissionScope.ENABLE_SIDECAR_SUGGESTIONS, ctx):
                decision.allowed = False
                decision.requires_approval = True
                decision.required_approvals.append(
                    PermissionScope.ENABLE_SIDECAR_SUGGESTIONS)
                decision.reasons.append(
                    "publishing suggestions requires explicit approval")
        elif op not in ALLOWED_SIDECAR_OPERATIONS:
            decision.allowed = False
            decision.reasons.append(
                f"unknown sidecar operation {operation!r} is denied by "
                "default")
        return self._audit_decision(decision)

    def evaluate_output_text(self, text: str,
                             context: Optional[Dict[str, Any]] = None,
                             ) -> PolicyDecision:
        """Does this generated text avoid unsupported claims?"""
        report = self.claim_guard.scan_text(text)
        decision = PolicyDecision(allowed=report.safe, subject="output_text")
        for finding in report.findings:
            decision.violations.append(PolicyViolation(
                "no_unsupported_consciousness_claims", "language",
                f"unsupported claim {finding.phrase!r}: {finding.suggestion}"))
        if not report.safe:
            decision.reasons.append(
                f"{len(report.findings)} unsupported claim(s) flagged")
        return self._audit_decision(decision)

    # -- inventory ----------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rules": [r.to_dict() for r in self.rules],
            "permissions": self.permissions.to_dict(),
            "approvals_attached": self.approvals is not None,
        }
