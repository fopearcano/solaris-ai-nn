"""Operator console CLI -- stdlib argparse, no shell, clear exit codes.

Commands: ``status``, ``profiles``, ``profile <id>``, ``plan <id>``,
``run <id> --confirm``, ``safety``, ``evidence search <query>``, ``reports``,
``decisions``, ``next``, ``export <bundle_type>``, ``approvals``,
``approve <scope> --note "..."``, ``index-artifacts``, ``index-reports``.

The CLI is stdlib-only and uses no subprocess/shell. ``run`` requires an explicit
``--confirm`` and still blocks unsafe or prohibited profiles; ``approve`` cannot
approve forbidden scopes. Exit codes: 0 success, 1 error, 2 blocked/refused.
"""

from __future__ import annotations

import argparse
import json
from typing import List, Optional

from .approval_ledger import ApprovalLedger
from .console_config import OperatorConsoleConfig
from .decision_board import OperatorDecisionBoard
from .evidence_navigator import EvidenceNavigator
from .next_action import NextActionRecommender
from .profile_catalog import ProfileCatalog
from .report_index import ReportIndexer
from .run_launcher import RunLauncher
from .run_planner import RunPlanner
from .status_board import OperatorStatusBoard

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_BLOCKED = 2


def _print(obj) -> None:
    print(json.dumps(obj, indent=2, default=str))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="solaris-operator",
        description="Local operator console for Solaris-AI-NN (coordinates; "
                    "grants no real-world authority).")
    parser.add_argument("--state-dir", default=".solaris_ai_nn_operator")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("status", help="show the status board")
    sub.add_parser("profiles", help="list runnable / blocked profiles")
    p_profile = sub.add_parser("profile", help="show one profile")
    p_profile.add_argument("profile_id")
    p_plan = sub.add_parser("plan", help="plan one profile (runs nothing)")
    p_plan.add_argument("profile_id")
    p_run = sub.add_parser("run", help="launch a bounded allowed profile")
    p_run.add_argument("profile_id")
    p_run.add_argument("--confirm", action="store_true",
                       help="explicit operator confirmation (required)")
    sub.add_parser("safety", help="show safety status (from indexes)")
    p_ev = sub.add_parser("evidence", help="evidence navigation")
    ev_sub = p_ev.add_subparsers(dest="evidence_command")
    p_search = ev_sub.add_parser("search", help="search local evidence")
    p_search.add_argument("query")
    sub.add_parser("reports", help="list indexed reports")
    sub.add_parser("decisions", help="show the decision board")
    sub.add_parser("next", help="show the recommended next action")
    p_export = sub.add_parser("export", help="generate a local export bundle")
    p_export.add_argument("bundle_type")
    sub.add_parser("approvals", help="show the approval ledger")
    p_approve = sub.add_parser("approve", help="record an approval")
    p_approve.add_argument("scope")
    p_approve.add_argument("--note", default="")
    sub.add_parser("index-artifacts", help="index local artifacts")
    sub.add_parser("index-reports", help="index local reports")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return EXIT_OK

    cfg = OperatorConsoleConfig(state_dir=args.state_dir)
    catalog = ProfileCatalog()

    if args.command == "status":
        result = OperatorStatusBoard(config=cfg, catalog=catalog).write()
        _print(result["snapshot"].to_dict())
        return EXIT_OK

    if args.command == "profiles":
        _print({"runnable": [e.profile_id
                             for e in catalog.runnable_entries()],
                "blocked": [e.profile_id for e in catalog.blocked_entries()],
                "summary": catalog.summary()})
        return EXIT_OK

    if args.command == "profile":
        entry = catalog.get(args.profile_id)
        if entry is None:
            _print({"error": f"unknown profile {args.profile_id!r}"})
            return EXIT_ERROR
        _print(entry.to_dict())
        return EXIT_OK

    if args.command == "plan":
        plan = RunPlanner(catalog).plan(args.profile_id)
        _print(plan.to_dict())
        return EXIT_OK if plan.validation and plan.validation.valid \
            else EXIT_BLOCKED

    if args.command == "run":
        if not args.confirm:
            _print({"blocked": True,
                    "reason": "run requires explicit --confirm"})
            return EXIT_BLOCKED
        launcher = RunLauncher(cfg, catalog)
        result = launcher.launch(args.profile_id, operator_confirmed=True)
        _print(result.to_dict())
        return EXIT_OK if result.launched else EXIT_BLOCKED

    if args.command == "safety":
        _print({"status": "unknown",
                "note": "attach live safety state for a real status; index "
                        "shows recorded safety reports",
                "reports": [r.to_dict() for r in ReportIndexer().index().records
                            if r.report_type == "safety_invariant_report"]})
        return EXIT_OK

    if args.command == "evidence":
        if args.evidence_command == "search":
            nav = EvidenceNavigator([args.state_dir])
            nav.index()
            results = nav.search(args.query)
            _print({"results": [r.to_dict() for r in results],
                    "external_search": False})
            return EXIT_OK
        parser.parse_args(["evidence", "--help"])
        return EXIT_ERROR

    if args.command == "reports":
        _print(ReportIndexer().index().to_dict())
        return EXIT_OK

    if args.command == "decisions":
        board = OperatorDecisionBoard(state_dir=cfg.state_dir).build()
        board.write()
        _print(board.to_dict())
        return EXIT_OK

    if args.command == "next":
        recs = NextActionRecommender().recommend()
        _print([r.to_dict() for r in recs])
        return EXIT_OK

    if args.command == "export":
        from .export_bundle import BUNDLE_TYPES, ExportBundleBuilder

        if args.bundle_type not in BUNDLE_TYPES:
            _print({"error": f"unknown bundle type {args.bundle_type!r}",
                    "known": list(BUNDLE_TYPES)})
            return EXIT_ERROR
        bundle = ExportBundleBuilder(config=cfg).build(args.bundle_type)
        _print(bundle.to_dict())
        return EXIT_OK

    if args.command == "approvals":
        _print(ApprovalLedger(state_dir=cfg.state_dir).snapshot())
        return EXIT_OK

    if args.command == "approve":
        record = ApprovalLedger(state_dir=cfg.state_dir).record(
            args.scope, args.note)
        _print(record.to_dict())
        return EXIT_OK if record.recorded else EXIT_BLOCKED

    if args.command == "index-artifacts":
        from .artifact_index import ArtifactIndexer

        _print(ArtifactIndexer().index().to_dict())
        return EXIT_OK

    if args.command == "index-reports":
        _print(ReportIndexer().index().to_dict())
        return EXIT_OK

    parser.print_help()
    return EXIT_ERROR


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
