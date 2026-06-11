"""WorldModelSafety -- the graph stores observations, never capabilities.

Hard rules: command-like payloads, URLs, and filesystem paths can never
become action nodes (they may at most become labelled unknown/safety nodes
for the audit trail); counterfactual/dream evidence stays marked offline;
graph predictions are data, with no execution path; pruning never touches
raw trace evidence; and reports stay claim-safe (ClaimGuard at save time).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..pilot.data_contracts import _payload_problems
from .nodes import NodeType


@dataclass
class WorldModelSafetyReport:
    safe: bool
    violations: List[str] = field(default_factory=list)
    fallback_node_type: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "violations": list(self.violations),
                "fallback_node_type": self.fallback_node_type}


@dataclass
class WorldModelSafety:
    """Validates what may enter the graph, and as what."""

    rejected_count: int = field(default=0, init=False)
    decisions: List[Dict[str, Any]] = field(default_factory=list, init=False)

    def _finish(self, check: str, violations: List[str],
                fallback: Optional[str] = None) -> WorldModelSafetyReport:
        report = WorldModelSafetyReport(safe=not violations,
                                        violations=violations,
                                        fallback_node_type=fallback)
        if violations:
            self.rejected_count += 1
        self.decisions.append({"check": check, **report.to_dict()})
        self.decisions = self.decisions[-100:]
        return report

    def validate_node(self, node_type: str, label: str,
                      ) -> WorldModelSafetyReport:
        """May this label become a node of this type?

        Command/URL/path-shaped labels may never become action (or
        action-adjacent) nodes; at most they become ``unknown`` nodes so the
        rejection itself is auditable.
        """
        violations: List[str] = []
        problems = _payload_problems(label)
        if problems and node_type in (NodeType.ACTION, NodeType.HABIT,
                                      NodeType.ENTITY, NodeType.OBJECT):
            violations.append(
                f"label {str(label)[:60]!r} is command/URL/path-shaped and "
                f"cannot become a {node_type} node: {problems[0]}")
            return self._finish("node", violations,
                                fallback=NodeType.UNKNOWN)
        if len(str(label)) > 200:
            violations.append("node labels are bounded at 200 chars")
            return self._finish("node", violations,
                                fallback=NodeType.UNKNOWN)
        return self._finish("node", violations)

    def validate_evidence(self, evidence: Any,
                          offline: bool) -> WorldModelSafetyReport:
        """Offline evidence must say so; nothing may pose as real."""
        violations: List[str] = []
        if isinstance(evidence, dict):
            is_simulated = bool(evidence.get("offline")
                                or evidence.get("simulated"))
            if is_simulated and not offline:
                violations.append(
                    "counterfactual/dream evidence must be recorded with "
                    "offline=True; it is never a real observation")
            if evidence.get("treat_as_real"):
                violations.append(
                    "evidence may never be force-marked as real")
        return self._finish("evidence", violations)

    def validate_prediction_use(self, use: str) -> WorldModelSafetyReport:
        """Predictions inform; they never execute."""
        violations: List[str] = []
        if str(use).lower() in ("execute", "act", "commit", "publish"):
            violations.append(
                "graph predictions are data for schedulers and trackers; "
                "they have no execution path")
        return self._finish("prediction_use", violations)

    def validate_pruning(self, proposal: Dict[str, Any], dry_run: bool,
                         context: Optional[Dict[str, Any]] = None,
                         ) -> WorldModelSafetyReport:
        """Production pruning needs governance; evidence stays preserved."""
        ctx = context or {}
        violations: List[str] = []
        if proposal.get("delete_trace_evidence"):
            violations.append(
                "graph pruning may never delete raw trace evidence")
        if not dry_run:
            if not ctx.get("pruning_allowed", False):
                violations.append(
                    "production graph pruning requires governance "
                    "permission (enable_world_model_pruning); default is "
                    "dry-run")
            governance = ctx.get("governance")
            if governance is not None and hasattr(governance,
                                                  "permissions"):
                if not governance.permissions.allows(
                        "enable_world_model_pruning") and not (
                        governance.approvals is not None
                        and governance.approvals.is_approved(
                            "enable_world_model_pruning",
                            {"run_id": ctx.get("run_id", "")})):
                    violations.append(
                        "governance denied production graph pruning")
        return self._finish("pruning", violations)

    def snapshot(self) -> Dict[str, Any]:
        return {"rejected_count": self.rejected_count,
                "recent_decisions": self.decisions[-5:],
                "note": "the graph stores observed structure; no claim of "
                        "understanding is made"}
