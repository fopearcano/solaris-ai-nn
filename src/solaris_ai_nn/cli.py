"""Unified local CLI for the Solaris-AI-NN Alpha Research System.

A bounded, local-only operator entry point built on the standard-library
``argparse``. It exposes the alpha commands (``doctor``, ``init``, ``modules``,
``run-demo``, ``artifact-index``, ``cycle-status``, ``build-runbook``,
``build-report``) and an optional ``alpha`` command group that mirrors them.

The CLI is local-only: it never calls shell commands, the network, Git, or GitHub;
it never publishes, uploads, or controls feeders/hardware; and it prints concise,
operator-readable summaries. In ``--strict`` mode it returns a nonzero exit code
when a blocker is present.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, List, Optional

from .alpha_system.alpha_orchestrator import AlphaResearchOrchestrator
from .alpha_system.alpha_profile import available_profiles
from .alpha_system.module_registry import AlphaModuleRegistry
from .alpha_system.state_layout import AlphaStateLayout

_ALPHA_COMMANDS = ("doctor", "init", "modules", "run-demo", "artifact-index",
                   "cycle-status", "build-runbook", "build-report")


def _orchestrator(args: argparse.Namespace) -> AlphaResearchOrchestrator:
    return AlphaResearchOrchestrator(
        state_dir=args.state_dir, profile=args.profile,
        max_runtime_s=args.max_runtime_s, max_ticks=args.max_ticks,
        fixture_mode=args.fixture_mode, report_only=args.report_only,
        dry_run=args.dry_run, strict=args.strict,
        require_claimguard=args.require_claimguard)


def _print(line: str = "") -> None:
    sys.stdout.write(line + "\n")


# -- command handlers --------------------------------------------------------

def cmd_init(args: argparse.Namespace) -> int:
    layout = AlphaStateLayout(state_root=args.state_dir)
    manifest = layout.initialize()
    _print(f"alpha state initialized at: {args.state_dir}")
    _print(f"  directories: {manifest['directories'].__len__()} "
           "(existing reused; none deleted)")
    _print(f"  manifest: {layout.manifest_path}")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    orch = _orchestrator(args)
    orch.initialize()
    orch.build_registry()
    summary = orch.run_doctor()
    _print("alpha doctor:")
    for r in summary["results"]:
        _print(f"  [{r['severity']}] {r['name']}: {r['detail']}")
    _print(f"  -> {summary['pass_count']} pass, {summary['warning_count']} "
           f"warning(s), {summary['blocker_count']} blocker(s)")
    if summary["blocker_count"] and args.strict:
        _print("  STRICT: blockers present -> nonzero exit")
        return 2
    return 0


def cmd_modules(args: argparse.Namespace) -> int:
    registry = AlphaModuleRegistry.build()
    idx = registry.index()
    _print("alpha module registry:")
    for m in registry.records:
        flag = " (required)" if m.required_for_alpha else ""
        _print(f"  [{m.status}] {m.label}{flag}")
    _print(f"  -> {idx['alpha_available_module_count']}/"
           f"{idx['alpha_module_count']} available, "
           f"{idx['alpha_missing_module_count']} missing, "
           f"{idx['alpha_blocked_module_count']} blocked")
    if registry.blocking_alpha() and args.strict:
        return 2
    return 0


def cmd_run_demo(args: argparse.Namespace) -> int:
    orch = _orchestrator(args)
    result = orch.run()
    if result.get("refused"):
        _print(f"alpha run refused: {result.get('reason')}")
        return 2
    status = orch.alpha_status()
    _print("alpha end-to-end demo:")
    _print(f"  profile: {status['alpha_profile_id']}")
    _print(f"  modules available: {status['alpha_available_module_count']}/"
           f"{status['alpha_module_count']}")
    _print(f"  demo steps: {status['alpha_demo_step_completed_count']} completed, "
           f"{status['alpha_demo_step_skipped_count']} skipped")
    _print(f"  artifacts: {status['alpha_artifact_count']}")
    _print(f"  stage: {status['alpha_cycle_stage']} -> next: "
           f"{status['alpha_next_action']}")
    _print(f"  blockers: {result['blocker_count']}; warnings: "
           f"{result['warning_count']}")
    _print(f"  report: {status['latest_alpha_report_path']}")
    if result["blocker_count"] and args.strict:
        return 2
    return 0


def cmd_artifact_index(args: argparse.Namespace) -> int:
    orch = _orchestrator(args)
    orch.report_only = True
    orch.run()
    idx = orch.artifact_index.to_dict() if orch.artifact_index else {}
    _print("alpha artifact index:")
    _print(f"  run id: {idx.get('run_id')}")
    for r in idx.get("records", []):
        _print(f"  [{'present' if r['present'] else 'missing'}] "
               f"{r['kind']}: {r['ref']}")
    _print(f"  -> {idx.get('alpha_artifact_count', 0)} artifact(s)")
    return 0


def cmd_cycle_status(args: argparse.Namespace) -> int:
    orch = _orchestrator(args)
    orch.report_only = True
    orch.run()
    c = orch.cycle
    _print("alpha cycle status:")
    _print(f"  stage: {c.get('stage')}")
    _print(f"  next action: {c.get('next_action')}")
    _print(f"  blockers: {c.get('blocker_count', 0)}; warnings: "
           f"{c.get('warning_count', 0)}")
    for b in c.get("blockers", []):
        _print(f"    blocker: {b}")
    if c.get("blocker_count", 0) and args.strict:
        return 2
    return 0


def cmd_build_runbook(args: argparse.Namespace) -> int:
    from .alpha_system.operator_runbook import AlphaRunbookBuilder

    layout = AlphaStateLayout(state_root=args.state_dir)
    layout.initialize()
    runbook = AlphaRunbookBuilder().build(args.state_dir)
    import os

    path = os.path.join(layout.subdir("reports"), "ALPHA_OPERATOR_RUNBOOK.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(runbook.render_md())
    _print(f"alpha operator runbook written: {path}")
    return 0


def cmd_build_report(args: argparse.Namespace) -> int:
    orch = _orchestrator(args)
    orch.report_only = True
    orch.run()
    out = orch.write_artifacts()
    _print("alpha report built from current artifacts:")
    for p in out["documents"]:
        _print(f"  {p}")
    if not out["report"]["sections"]["claimguard_available"] \
            and args.require_claimguard:
        _print("  STRICT: ClaimGuard unavailable")
        return 2
    return 0


_HANDLERS = {
    "init": cmd_init,
    "doctor": cmd_doctor,
    "modules": cmd_modules,
    "run-demo": cmd_run_demo,
    "artifact-index": cmd_artifact_index,
    "cycle-status": cmd_cycle_status,
    "build-runbook": cmd_build_runbook,
    "build-report": cmd_build_report,
}


# -- argument parsing --------------------------------------------------------

def _add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--state-dir", type=str, default=".solaris_ai_nn_alpha",
                        help="local alpha state directory root")
    parser.add_argument("--profile", type=str, default=None,
                        help=f"alpha profile id ({', '.join(available_profiles())})")
    parser.add_argument("--max-runtime-s", type=float, default=60.0,
                        dest="max_runtime_s", help="bounded max runtime seconds")
    parser.add_argument("--max-ticks", type=int, default=50, dest="max_ticks",
                        help="bounded max ticks")
    parser.add_argument("--fixture-mode", action="store_true", default=True,
                        dest="fixture_mode", help="fixture-only mode (default)")
    parser.add_argument("--dry-run", action="store_true", default=False,
                        dest="dry_run", help="do not write artifacts")
    parser.add_argument("--report-only", action="store_true", default=False,
                        dest="report_only",
                        help="skip the demo; build reports from state only")
    parser.add_argument("--strict", action="store_true", default=False,
                        help="nonzero exit code on blockers")
    parser.add_argument("--require-claimguard", action="store_true",
                        default=False, dest="require_claimguard",
                        help="treat a missing ClaimGuard as a blocker")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="solaris_ai_nn",
        description="Solaris-AI-NN Alpha Research System (local, bounded, "
                    "fixture-only). It does not call Git/GitHub, publish, "
                    "control hardware/feeders, or prove consciousness/life/"
                    "agency.")
    sub = parser.add_subparsers(dest="command")
    for name in _ALPHA_COMMANDS:
        p = sub.add_parser(name, help=f"alpha {name} command")
        _add_common_args(p)
    # Optional `alpha` group mirroring the same commands.
    alpha = sub.add_parser("alpha", help="alpha command group")
    alpha_sub = alpha.add_subparsers(dest="alpha_command")
    for name in _ALPHA_COMMANDS:
        p = alpha_sub.add_parser(name, help=f"alpha {name} command")
        _add_common_args(p)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    command = getattr(args, "command", None)
    if command == "alpha":
        command = getattr(args, "alpha_command", None)
    if not command:
        parser.print_help()
        return 0
    handler = _HANDLERS.get(command)
    if handler is None:
        parser.print_help()
        return 0
    return handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
