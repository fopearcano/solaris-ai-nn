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
