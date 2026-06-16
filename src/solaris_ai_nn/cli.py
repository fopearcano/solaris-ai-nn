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
                   "cycle-status", "build-runbook", "build-report",
                   "build-docs", "docs-index", "whitepaper",
                   "live-init", "live-doctor", "live-birth", "live-quarantine",
                   "birth-certificate")


def _birth_runtime(args: argparse.Namespace):
    from .live_birth.birth_runtime import LiveReadOnlyBirthRuntime

    state_dir = args.state_dir
    if state_dir == ".solaris_ai_nn_alpha":
        state_dir = ".solaris_ai_nn_live"
    return LiveReadOnlyBirthRuntime(
        state_dir=state_dir, profile=args.profile,
        max_runtime_s=args.max_runtime_s, max_files=args.max_files,
        max_events=args.max_events, max_bytes=args.max_bytes,
        strict=args.strict, dry_run=args.dry_run, report_only=args.report_only,
        require_governance=args.require_governance,
        require_feeder_registry=args.require_feeder_registry,
        allow_operator_pulse=not args.no_operator_pulse,
        require_claimguard=args.require_claimguard,
        operator_note=args.operator_note)


def _book_runtime(args: argparse.Namespace):
    from .architecture_book.book_runtime import ArchitectureBookRuntime

    return ArchitectureBookRuntime(
        state_dir=args.state_dir, docs_dir=args.docs_dir,
        report_only=args.report_only, dry_run=args.dry_run,
        max_runtime_s=args.max_runtime_s, strict=args.strict,
        require_claimguard=args.require_claimguard)


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


def cmd_build_docs(args: argparse.Namespace) -> int:
    rt = _book_runtime(args)
    result = rt.run()
    if result.get("refused"):
        _print(f"docs build refused: {result.get('reason')}")
        return 2
    rt.write_artifacts()
    status = rt.documentation_status()
    _print("alpha documentation build:")
    _print(f"  sources: {status['documentation_source_count']} "
           f"(missing {status['missing_documentation_source_count']})")
    _print(f"  documents: {status['generated_document_count']}")
    _print(f"  chapters: {status['generated_chapter_count']} "
           f"(skipped {status['skipped_chapter_count']})")
    _print(f"  diagrams: {status['generated_diagram_count']}; glossary: "
           f"{status['glossary_entry_count']}")
    _print(f"  ClaimGuard available: {status['claimguard_available']}; "
           f"doc blocks: {status['claimguard_documentation_block_count']}")
    _print(f"  whitepaper: {status['latest_whitepaper_path']}")
    _print(f"  architecture book: {status['latest_architecture_book_path']}")
    if status["claimguard_documentation_block_count"] and args.strict:
        _print("  STRICT: documentation safety blockers present")
        return 2
    if not status["claimguard_available"] and args.require_claimguard:
        _print("  STRICT: ClaimGuard unavailable")
        return 2
    return 0


def cmd_docs_index(args: argparse.Namespace) -> int:
    from .architecture_book.doc_index import DocumentationIndexBuilder

    index = DocumentationIndexBuilder(docs_dir=args.docs_dir).build()
    d = index.to_dict()
    _print("alpha documentation index:")
    for e in d["entries"]:
        _print(f"  [{'present' if e['present'] else 'missing'}] {e['label']}: "
               f"{e['path']}")
    _print(f"  -> {d['present_document_count']} present, "
           f"{d['missing_document_count']} missing")
    return 0


def cmd_whitepaper(args: argparse.Namespace) -> int:
    import os

    path = os.path.join(args.docs_dir, "SOLARIS_AI_NN_WHITEPAPER.md")
    if os.path.isfile(path):
        _print(f"technical whitepaper: {path} (already built)")
        return 0
    rt = _book_runtime(args)
    result = rt.run()
    if result.get("refused"):
        _print(f"whitepaper build refused: {result.get('reason')}")
        return 2
    _print(f"technical whitepaper: "
           f"{rt.documentation_status()['latest_whitepaper_path']}")
    return 0


def cmd_live_init(args: argparse.Namespace) -> int:
    rt = _birth_runtime(args)
    rt.initialize()
    paths = rt.write_templates()
    _print(f"live state initialized at: {rt.state_dir}")
    _print(f"  governance template: {paths['governance']}")
    _print(f"  feeder registry template: {paths['feeder_registry']}")
    _print("  note: governance is SAFE-OFF by default (live_readonly_enabled and "
           "operator_approved are false); the operator must approve it.")
    return 0


def cmd_live_doctor(args: argparse.Namespace) -> int:
    rt = _birth_runtime(args)
    summary = rt.run_doctor()
    _print("live doctor:")
    _print(f"  governance: {summary['governance_status']} "
           f"(passed {summary['governance_passed']})")
    _print(f"  feeder registry present: {summary['feeder_registry_present']} "
           f"(blockers {summary['feeder_blocker_count']})")
    _print(f"  inbox has events: {summary['inbox_has_events']}")
    for b in summary["blockers"]:
        _print(f"  blocker: {b}")
    if summary["blockers"] and args.strict:
        _print("  STRICT: live safety blockers present -> nonzero exit")
        return 2
    return 0


def cmd_live_birth(args: argparse.Namespace) -> int:
    rt = _birth_runtime(args)
    result = rt.run()
    if result.get("refused"):
        _print(f"live birth refused: {result.get('reason')}")
        return 2
    st = rt.live_birth_status()
    _print("live read-only birth:")
    _print(f"  run id: {st['birth_run_id']}")
    _print(f"  governance: {st['governance_status']} (passed "
           f"{st['governance_passed']})")
    _print(f"  blocked: {result['blocked']}")
    for b in result["blockers"]:
        _print(f"    blocker: {b}")
    _print(f"  events: {st['live_event_count']} (accepted "
           f"{st['live_event_accepted_count']}, quarantined "
           f"{st['live_event_quarantined_count']})")
    _print(f"  membrane: {st['membrane_activation_status']}")
    _print(f"  birth certificate: {st['latest_birth_certificate_path']}")
    _print(f"  starts feeders / network: {st['starts_feeders']} / "
           f"{st['accesses_network']}")
    if result["blocked"] and args.strict:
        return 2
    return 0


def cmd_live_quarantine(args: argparse.Namespace) -> int:
    import json as _json
    import os as _os

    state_dir = args.state_dir
    if state_dir == ".solaris_ai_nn_alpha":
        state_dir = ".solaris_ai_nn_live"
    path = _os.path.join(state_dir, "quarantine", "QUARANTINE_INDEX.json")
    _print("live quarantine summary:")
    if not _os.path.isfile(path):
        _print("  (no quarantine index yet; run live-birth first)")
        return 0
    with open(path, encoding="utf-8") as fh:
        data = _json.load(fh)
    _print(f"  quarantined events: {data.get('quarantined_event_count', 0)}")
    for reason, count in (data.get("reasons", {}) or {}).items():
        _print(f"    {reason}: {count}")
    return 0


def cmd_birth_certificate(args: argparse.Namespace) -> int:
    import os as _os

    state_dir = args.state_dir
    if state_dir == ".solaris_ai_nn_alpha":
        state_dir = ".solaris_ai_nn_live"
    cert_dir = _os.path.join(state_dir, "certificates")
    existing = []
    if _os.path.isdir(cert_dir):
        existing = sorted(f for f in _os.listdir(cert_dir)
                          if f.startswith("BIRTH_CERTIFICATE_")
                          and f.endswith(".md"))
    if existing:
        _print(f"latest birth certificate: "
               f"{_os.path.join(cert_dir, existing[-1])}")
        return 0
    # Generate from a fresh run if none exists.
    rt = _birth_runtime(args)
    rt.run()
    st = rt.live_birth_status()
    _print(f"birth certificate: {st['latest_birth_certificate_path']}")
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
    "build-docs": cmd_build_docs,
    "docs-index": cmd_docs_index,
    "whitepaper": cmd_whitepaper,
    "live-init": cmd_live_init,
    "live-doctor": cmd_live_doctor,
    "live-birth": cmd_live_birth,
    "live-quarantine": cmd_live_quarantine,
    "birth-certificate": cmd_birth_certificate,
}


# -- argument parsing --------------------------------------------------------

def _add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--state-dir", type=str, default=".solaris_ai_nn_alpha",
                        help="local alpha state directory root")
    parser.add_argument("--docs-dir", type=str, default="docs/whitepaper",
                        dest="docs_dir",
                        help="output directory for generated documentation")
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
    # Live read-only birth arguments (Prompt 67).
    parser.add_argument("--max-events", type=int, default=500, dest="max_events",
                        help="bounded max live events read")
    parser.add_argument("--max-files", type=int, default=50, dest="max_files",
                        help="bounded max inbox files read")
    parser.add_argument("--max-bytes", type=int, default=5_000_000,
                        dest="max_bytes", help="bounded max bytes read")
    parser.add_argument("--require-governance", action="store_true",
                        default=False, dest="require_governance",
                        help="require approved live governance before birth")
    parser.add_argument("--require-feeder-registry", action="store_true",
                        default=False, dest="require_feeder_registry",
                        help="require a feeder registry before birth")
    parser.add_argument("--no-operator-pulse", action="store_true",
                        default=False, dest="no_operator_pulse",
                        help="exclude the operator_pulse source")
    parser.add_argument("--operator-note", type=str, default="",
                        dest="operator_note",
                        help="optional operator note for the birth certificate")


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
