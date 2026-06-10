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

    ALL = (
        RUN_BOUNDED, RUN_SOAK_24H, RUN_SOAK_30D,
        ENABLE_PLASTICITY, ENABLE_PLASTICITY_APPLY, ENABLE_PLASTICITY_DRY_RUN,
        ENABLE_EMBODIMENT_SIMULATION,
        ENABLE_SIDECAR_OBSERVE, ENABLE_SIDECAR_SUGGESTIONS,
        ENABLE_LOCAL_STATUS_SERVER,
        PERFORM_ARTIFACT_ROTATION, PERFORM_ROLLBACK, PERFORM_EMERGENCY_STOP,
        ENABLE_LATENT, ENABLE_LATENT_DRY_RUN, ENABLE_LATENT_PLASTICITY,
        RUN_DREAM_CYCLE, RUN_COUNTERFACTUAL_REPLAY,
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
