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
