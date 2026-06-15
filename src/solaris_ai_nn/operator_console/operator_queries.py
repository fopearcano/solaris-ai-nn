"""Operator query router -- deterministic, local, never an LLM.

:class:`OperatorQueryRouter` answers a fixed set of operator queries by reading
the local indexes and boards. It is fully deterministic, uses no LLM, and
searches local indexes only. An unsafe query (one that would run something
prohibited or grant authority) returns a refusal/blocker rather than executing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .console_config import OperatorConsoleConfig
from .evidence_navigator import EvidenceNavigator
from .next_action import NextActionRecommender
from .profile_catalog import ProfileCatalog
from .report_index import ReportIndexer
from .run_launcher import RunLauncher
from .run_planner import RunPlanner

SUPPORTED_QUERIES = (
    "list_profiles", "show_profile", "plan_profile", "run_profile_if_allowed",
    "show_status", "show_decisions", "show_next_action", "search_evidence",
    "list_reports", "show_report_summary", "generate_export_bundle",
    "show_safety_status", "show_architecture_status", "show_research_status",
    "show_pilot_status",
)


@dataclass
class OperatorQueryResult:
    query: str
    ok: bool
    data: Any = None
    message: str = ""
    refused: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {"query": self.query, "ok": self.ok, "data": self.data,
                "message": self.message, "refused": self.refused}


@dataclass
class OperatorQueryRouter:
    """Routes operator queries to local indexes; deterministic, no LLM."""

    config: OperatorConsoleConfig = field(default_factory=OperatorConsoleConfig)
    catalog: ProfileCatalog = field(default_factory=ProfileCatalog)
    launcher: Optional[RunLauncher] = None
    navigator: Optional[EvidenceNavigator] = None
    safety_status: Optional[Dict[str, Any]] = None
    research_status: Optional[Dict[str, Any]] = None
    architecture_status: Optional[Dict[str, Any]] = None
    pilot_status: Optional[Dict[str, Any]] = None

    def route(self, query: str, **kwargs) -> OperatorQueryResult:
        if query not in SUPPORTED_QUERIES:
            return OperatorQueryResult(
                query=query, ok=False, refused=True,
                message=f"unsupported query {query!r}; the router is "
                        "deterministic and only answers known local queries")
        handler = getattr(self, f"_{query}")
        return handler(**kwargs)

    # -- handlers ------------------------------------------------------------

    def _list_profiles(self, **_kw) -> OperatorQueryResult:
        return OperatorQueryResult(
            "list_profiles", True,
            data={"runnable": [e.profile_id
                               for e in self.catalog.runnable_entries()],
                  "blocked": [e.profile_id
                              for e in self.catalog.blocked_entries()]})

    def _show_profile(self, profile_id: str = "", **_kw) -> OperatorQueryResult:
        entry = self.catalog.get(profile_id)
        if entry is None:
            return OperatorQueryResult("show_profile", False,
                                       message=f"unknown profile {profile_id!r}")
        return OperatorQueryResult("show_profile", True, data=entry.to_dict())

    def _plan_profile(self, profile_id: str = "", **_kw) -> OperatorQueryResult:
        plan = RunPlanner(self.catalog).plan(profile_id)
        return OperatorQueryResult("plan_profile", True, data=plan.to_dict())

    def _run_profile_if_allowed(self, profile_id: str = "",
                                operator_confirmed: bool = False,
                                **kwargs) -> OperatorQueryResult:
        if self.launcher is None:
            return OperatorQueryResult(
                "run_profile_if_allowed", False, refused=True,
                message="no run launcher is attached; the router runs nothing "
                        "on its own")
        result = self.launcher.launch(
            profile_id, operator_confirmed=operator_confirmed,
            safety_state=kwargs.get("safety_state", self.safety_status),
            governance_approved=kwargs.get("governance_approved", False))
        return OperatorQueryResult(
            "run_profile_if_allowed", result.launched, data=result.to_dict(),
            refused=result.blocked,
            message="" if result.launched else "run blocked")

    def _show_status(self, **_kw) -> OperatorQueryResult:
        from .status_board import OperatorStatusBoard

        snap = OperatorStatusBoard(
            config=self.config, catalog=self.catalog,
            safety_status=self.safety_status,
            research_status=self.research_status,
            architecture_status=self.architecture_status,
            pilot_status=self.pilot_status).build()
        return OperatorQueryResult("show_status", True, data=snap.to_dict())

    def _show_decisions(self, **_kw) -> OperatorQueryResult:
        from .decision_board import OperatorDecisionBoard

        board = OperatorDecisionBoard(state_dir=self.config.state_dir).build(
            safety_status=self.safety_status,
            research_findings=self.research_status,
            architecture_status=self.architecture_status,
            pilot_status=self.pilot_status)
        return OperatorQueryResult("show_decisions", True, data=board.to_dict())

    def _show_next_action(self, **_kw) -> OperatorQueryResult:
        recs = NextActionRecommender().recommend(
            safety_status=self.safety_status,
            research_findings=self.research_status,
            architecture_roadmap=self.architecture_status)
        return OperatorQueryResult(
            "show_next_action", True,
            data=[r.to_dict() for r in recs])

    def _search_evidence(self, keyword: str = "", **kwargs
                         ) -> OperatorQueryResult:
        nav = self.navigator or EvidenceNavigator(
            [self.config.state_dir])
        if nav.indexed_count() == 0:
            nav.index()
        results = nav.search(keyword or None,
                             evidence_type=kwargs.get("evidence_type"),
                             module=kwargs.get("module"),
                             profile_id=kwargs.get("profile_id"))
        return OperatorQueryResult(
            "search_evidence", True,
            data={"results": [r.to_dict() for r in results],
                  "external_search": False})

    def _list_reports(self, **_kw) -> OperatorQueryResult:
        index = ReportIndexer().index()
        return OperatorQueryResult("list_reports", True, data=index.to_dict())

    def _show_report_summary(self, report_id: str = "", **_kw
                             ) -> OperatorQueryResult:
        index = ReportIndexer().index()
        for record in index.records:
            if record.report_id == report_id:
                return OperatorQueryResult("show_report_summary", True,
                                           data=record.to_dict())
        return OperatorQueryResult("show_report_summary", False,
                                   message=f"unknown report {report_id!r}")

    def _generate_export_bundle(self, bundle_type: str = "safety_review_bundle",
                                **_kw) -> OperatorQueryResult:
        from .export_bundle import BUNDLE_TYPES, ExportBundleBuilder

        if bundle_type not in BUNDLE_TYPES:
            return OperatorQueryResult("generate_export_bundle", False,
                                       message=f"unknown bundle {bundle_type!r}")
        bundle = ExportBundleBuilder(
            config=self.config, safety_status=self.safety_status).build(
            bundle_type)
        return OperatorQueryResult("generate_export_bundle", True,
                                   data=bundle.to_dict())

    def _show_safety_status(self, **_kw) -> OperatorQueryResult:
        return OperatorQueryResult("show_safety_status", True,
                                   data=self.safety_status or {"status":
                                                               "unknown"})

    def _show_architecture_status(self, **_kw) -> OperatorQueryResult:
        return OperatorQueryResult("show_architecture_status", True,
                                   data=self.architecture_status or {})

    def _show_research_status(self, **_kw) -> OperatorQueryResult:
        return OperatorQueryResult("show_research_status", True,
                                   data=self.research_status or {})

    def _show_pilot_status(self, **_kw) -> OperatorQueryResult:
        return OperatorQueryResult("show_pilot_status", True,
                                   data=self.pilot_status or {})
