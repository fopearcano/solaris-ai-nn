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
