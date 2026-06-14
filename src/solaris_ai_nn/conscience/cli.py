"""Stdlib-only CLI for the unified conscience runtime.

Subcommands:

* ``list-profiles``    -- show the built-in scenario profiles A--J.
* ``dry-run-profile``  -- initialize a profile and report integration health
                          without running it (or run a plan-only profile).
* ``run-profile``      -- run a bounded profile to completion.
* ``health-check``     -- initialize a profile and print its health report.
* ``snapshot``         -- initialize a profile and print one runtime snapshot.

Every command is bounded, internal/simulation-only, and writes only under the
chosen state/output directories. Governed profiles refuse to run without an
explicit ``--governance-approved`` acknowledgement.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, List, Optional

from .full_system_report import FullSystemReportBuilder
from .integration_health import IntegrationHealthMonitor
from .orchestrator import ConscienceOrchestrator
from .scenario_profiles import ScenarioProfileRegistry
from .scenario_runner import ScenarioRunner
from .snapshots import SnapshotBuilder


def _print(obj: Any) -> None:
    print(json.dumps(obj, indent=2, default=str))


def _build_governance(approved: bool) -> Any:
    """Return a governance policy when one is available, else None."""
    try:
        from ..governance.policy import GovernancePolicy

        return GovernancePolicy()
    except Exception:
        return None


def cmd_list_profiles(args: argparse.Namespace) -> int:
    registry = ScenarioProfileRegistry()
    if args.verbose:
        _print(registry.list_profiles())
    else:
        rows = []
        for pid in registry.ids():
            p = registry.profiles[pid]
            rows.append({
                "profile_id": pid,
                "description": p.description,
                "plan_only": p.is_plan_only,
                "requires_governance": p.requires_governance,
                "max_steps": p.run_context.max_steps,
            })
        _print(rows)
    return 0


def _prepare(args: argparse.Namespace) -> Optional[ConscienceOrchestrator]:
    registry = ScenarioProfileRegistry()
    profile = registry.get(args.profile)
    if profile is None:
        print(f"unknown profile {args.profile!r}; known: "
              f"{', '.join(registry.ids())}", file=sys.stderr)
        return None
    if args.state_dir:
        profile.run_context.state_dir = args.state_dir
    if getattr(args, "output_dir", None):
        profile.run_context.artifact_dir = args.output_dir
    governance = _build_governance(args.governance_approved)
    orch = ConscienceOrchestrator(governance=governance,
                                  governance_approved=args.governance_approved)
    orch.configure(profile)
    orch.initialize()
    return orch


def cmd_dry_run_profile(args: argparse.Namespace) -> int:
    orch = _prepare(args)
    if orch is None:
        return 2
    monitor = IntegrationHealthMonitor()
    report = monitor.check(orch)
    _print({
        "profile": args.profile,
        "initialized": orch.initialized,
        "refusal_reasons": orch.refusal_reasons or None,
        "plan_only": orch.context.is_plan_only,
        "integration_health": report.to_dict(),
    })
    return 0


def cmd_run_profile(args: argparse.Namespace) -> int:
    governance = _build_governance(args.governance_approved)
    runner = ScenarioRunner(state_dir=args.state_dir,
                            output_dir=args.output_dir or args.state_dir,
                            governance=governance)
    result = runner.run_profile(
        args.profile, governance_approved=args.governance_approved)
    # Attach a full-system report for completed runs when an output dir exists.
    out = result.to_dict()
    out.pop("summary", None)
    _print(out)
    return 0 if result.ok else 1


def cmd_health_check(args: argparse.Namespace) -> int:
    orch = _prepare(args)
    if orch is None:
        return 2
    monitor = IntegrationHealthMonitor()
    report = monitor.check(orch)
    _print(report.to_dict())
    return 0 if report.healthy else 1


def cmd_snapshot(args: argparse.Namespace) -> int:
    orch = _prepare(args)
    if orch is None:
        return 2
    # Take a few steps so the snapshot is non-trivial (unless plan-only).
    if not orch.context.is_plan_only:
        for _ in range(min(args.steps, orch.context.max_steps or args.steps)):
            orch.step()
    builder = SnapshotBuilder(state_dir=args.state_dir)
    monitor = IntegrationHealthMonitor()
    snap = builder.build_and_persist(orch, monitor, args.state_dir)
    _print(snap.to_dict())
    return 0


def _add_common(sub: argparse.ArgumentParser, profile: bool = True) -> None:
    if profile:
        sub.add_argument("--profile", required=True,
                         help="scenario profile id (see list-profiles)")
    sub.add_argument("--state-dir", default=None,
                     help="directory for state/logs (created if needed)")
    sub.add_argument("--output-dir", default=None,
                     help="directory for reports/artifacts")
    sub.add_argument("--governance-approved", action="store_true",
                     help="acknowledge governance approval for governed "
                          "profiles (still internal/simulation only)")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="solaris-nn",
        description="Unified conscience runtime (bounded, simulation-only).")
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list-profiles",
                            help="list the built-in scenario profiles")
    p_list.add_argument("--verbose", action="store_true",
                        help="print the full profile definitions")
    p_list.set_defaults(func=cmd_list_profiles)

    p_dry = sub.add_parser("dry-run-profile",
                           help="initialize and check a profile without "
                                "running it")
    _add_common(p_dry)
    p_dry.set_defaults(func=cmd_dry_run_profile)

    p_run = sub.add_parser("run-profile", help="run a bounded profile")
    _add_common(p_run)
    p_run.set_defaults(func=cmd_run_profile)

    p_health = sub.add_parser("health-check",
                              help="print a profile's integration health")
    _add_common(p_health)
    p_health.set_defaults(func=cmd_health_check)

    p_snap = sub.add_parser("snapshot",
                            help="initialize, step, and snapshot a profile")
    _add_common(p_snap)
    p_snap.add_argument("--steps", type=int, default=10,
                        help="steps to run before snapshotting")
    p_snap.set_defaults(func=cmd_snapshot)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


def scenario_main(argv: Optional[List[str]] = None) -> int:
    """Entry point for ``solaris-nn-scenario`` -- defaults to run-profile."""
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and not argv[0].startswith("-") \
            and argv[0] not in ("list-profiles", "dry-run-profile",
                                "run-profile", "health-check", "snapshot"):
        argv = ["run-profile", "--profile", *argv]
    elif argv and argv[0].startswith("-"):
        argv = ["run-profile", *argv]
    return main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
