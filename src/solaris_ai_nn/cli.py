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
                   "birth-certificate", "live-observe", "live-source-health",
                   "live-source-diet", "live-metabolism-calibration",
                   "live-stability-gate", "live-ontogenesis", "live-concepts",
                   "live-concept-candidates", "live-concept-birth-gate",
                   "live-semiogenesis", "live-signs", "live-sign-candidates",
                   "live-sign-birth-gate", "live-private-syntax",
                   "live-cognition", "live-cognition-traces",
                   "live-anticipations", "live-predictions",
                   "live-cognition-gate", "membrane-doctor", "membrane-run",
                   "membrane-impressions", "membrane-report", "membrane-memory",
                   "membrane-integrate", "membrane-audit", "membrane-bypass",
                   "membrane-ancestry", "membrane-contracts",
                   "tester-demo", "tester-golden", "tester-bundle",
                   "tester-repro", "tester-regression", "tester-fixtures",
                   "tester-live-init", "tester-live-doctor",
                   "tester-live-samples", "tester-live-run",
                   "tester-live-bundle", "tester-live-checklist",
                   "tester-console", "tester-console-md", "tester-console-html",
                   "tester-console-status", "tester-console-runs",
                   "tester-feedback-init", "tester-feedback-ingest",
                   "tester-feedback-report", "tester-feedback-ledger",
                   "tester-feedback-bundle", "tester-feedback-blockers",
                   "tester-packaging", "tester-install-guide",
                   "tester-release-manifest", "tester-clean-machine",
                   "tester-command-check",
                   "tester-safety-freeze", "tester-claim-freeze",
                   "tester-capability-freeze", "tester-redteam",
                   "tester-release-blockers", "tester-safety-scan")


def _integration_runtime(args: argparse.Namespace):
    from .membrane_integration.integration_runtime import (
        MembraneIntegrationRuntime,
    )

    state_dir = args.state_dir
    if state_dir == ".solaris_ai_nn_alpha":
        state_dir = ".solaris_ai_nn_live"
    return MembraneIntegrationRuntime(
        state_dir=state_dir, profile=args.profile,
        max_runtime_s=args.max_runtime_s, report_only=args.report_only,
        dry_run=args.dry_run, strict=args.strict,
        require_membrane=args.require_membrane,
        require_impressions=args.require_impressions,
        require_ancestry=args.require_ancestry,
        allow_raw_fallback=args.allow_raw_fallback,
        require_claimguard=args.require_claimguard,
        operator_note=args.operator_note)


def _tester_safety_freeze_runtime(args: argparse.Namespace, **overrides):
    from .tester_safety_freeze import TesterSafetyFreezeRuntime

    kwargs = dict(
        tester_state_dir=args.tester_state_dir,
        safety_freeze_dir=args.safety_freeze_dir, profile=args.profile,
        max_runtime_s=args.max_runtime_s, strict=args.strict,
        dry_run=args.dry_run, report_only=args.report_only,
        require_claimguard=args.require_claimguard)
    kwargs.update(overrides)
    return TesterSafetyFreezeRuntime(**kwargs)


def _tester_packaging_runtime(args: argparse.Namespace, **overrides):
    from .tester_packaging import TesterPackagingRuntime

    state_dir = args.state_dir
    if state_dir == ".solaris_ai_nn_alpha":
        state_dir = ".solaris_ai_nn_live"
    kwargs = dict(
        state_dir=state_dir, tester_state_dir=args.tester_state_dir,
        packaging_dir=args.packaging_dir, profile=args.profile,
        max_runtime_s=args.max_runtime_s, strict=args.strict,
        dry_run=args.dry_run, report_only=args.report_only,
        include_dev_checks=args.include_dev_checks,
        require_claimguard=args.require_claimguard)
    kwargs.update(overrides)
    return TesterPackagingRuntime(**kwargs)


def _tester_feedback_runtime(args: argparse.Namespace, **overrides):
    from .tester_feedback import TesterFeedbackRuntime

    kwargs = dict(
        tester_state_dir=args.tester_state_dir, feedback_dir=args.feedback_dir,
        profile=args.profile, max_runtime_s=args.max_runtime_s,
        strict=args.strict, dry_run=args.dry_run, report_only=args.report_only,
        forms_only=args.forms_only, ingest_path=args.ingest_path,
        build_bundle=args.build_bundle, privacy_redact=args.privacy_redact,
        require_claimguard=args.require_claimguard)
    kwargs.update(overrides)
    return TesterFeedbackRuntime(**kwargs)


def _tester_console_runtime(args: argparse.Namespace, **overrides):
    from .tester_console import TesterConsoleRuntime

    state_dir = args.state_dir
    if state_dir == ".solaris_ai_nn_alpha":
        state_dir = ".solaris_ai_nn_live"
    kwargs = dict(
        state_dir=state_dir, tester_state_dir=args.tester_state_dir,
        console_dir=args.console_dir, profile=args.profile,
        max_runtime_s=args.max_runtime_s, strict=args.strict,
        dry_run=args.dry_run, report_only=args.report_only, html=args.html,
        require_claimguard=args.require_claimguard)
    kwargs.update(overrides)
    return TesterConsoleRuntime(**kwargs)


def _tester_live_runtime(args: argparse.Namespace, **overrides):
    from .tester_live_readonly import TesterLiveReadOnlyRuntime

    state_dir = args.state_dir
    if state_dir == ".solaris_ai_nn_alpha":
        state_dir = ".solaris_ai_nn_live"
    kwargs = dict(
        state_dir=state_dir, tester_state_dir=args.tester_state_dir,
        profile=args.profile, max_runtime_s=args.max_runtime_s,
        max_events=args.max_events, strict=args.strict, dry_run=args.dry_run,
        report_only=args.report_only, write_templates=args.write_templates,
        copy_safe_samples_to_inbox=args.copy_safe_samples_to_inbox,
        run_birth=args.run_birth, run_membrane=args.run_membrane,
        run_integration=args.run_integration,
        run_observation=args.run_observation,
        require_claimguard=args.require_claimguard)
    kwargs.update(overrides)
    return TesterLiveReadOnlyRuntime(**kwargs)


def _tester_runtime(args: argparse.Namespace):
    from .tester_fixture_spine import TesterFixtureDemoRuntime

    state_dir = args.state_dir
    if state_dir == ".solaris_ai_nn_alpha":
        state_dir = ".solaris_ai_nn_tester"
    return TesterFixtureDemoRuntime(
        state_dir=state_dir, profile=args.profile,
        fixture_pack_path=args.fixture_pack_path,
        max_runtime_s=args.max_runtime_s, max_events=args.max_events,
        strict=args.strict, dry_run=args.dry_run, report_only=args.report_only,
        regenerate_golden=args.regenerate_golden,
        allow_optional_stages=args.allow_optional_stages,
        require_membrane=not args.allow_raw_fallback,
        require_claimguard=args.require_claimguard,
        operator_note=args.operator_note)


def _membrane_runtime(args: argparse.Namespace):
    from .environmental_membrane.membrane_runtime import (
        EnvironmentalMembraneRuntime,
    )

    state_dir = args.state_dir
    if state_dir == ".solaris_ai_nn_alpha":
        state_dir = ".solaris_ai_nn_live"
    return EnvironmentalMembraneRuntime(
        state_dir=state_dir, profile=args.profile,
        max_runtime_s=args.max_runtime_s, max_events=args.max_events,
        max_files=args.max_files, report_only=args.report_only,
        dry_run=args.dry_run, strict=args.strict,
        require_governance=args.require_governance,
        require_feeder_registry=args.require_feeder_registry,
        require_claimguard=args.require_claimguard,
        operator_note=args.operator_note)


def _cognition_runtime(args: argparse.Namespace):
    from .live_cognition.cognition_runtime import FirstLiveCognitionRuntime

    state_dir = args.state_dir
    if state_dir == ".solaris_ai_nn_alpha":
        state_dir = ".solaris_ai_nn_live"
    return FirstLiveCognitionRuntime(
        state_dir=state_dir, profile=args.profile,
        max_runtime_s=args.max_runtime_s, max_signs=args.max_signs,
        max_traces=args.max_traces,
        max_simulation_steps=args.max_simulation_steps,
        max_traversal_depth=args.max_traversal_depth,
        min_prediction_utility=args.min_prediction_utility,
        max_uncertainty=args.max_uncertainty,
        strict=args.strict, dry_run=args.dry_run, report_only=args.report_only,
        require_governance=args.require_governance,
        require_birth_certificate=args.require_birth_certificate,
        require_observation_stability=args.require_observation_stability,
        require_live_concepts=args.require_live_concepts,
        require_live_signs=args.require_live_signs,
        require_claimguard=args.require_claimguard,
        operator_note=args.operator_note)


def _semiogenesis_runtime(args: argparse.Namespace):
    from .live_semiogenesis.semiogenesis_runtime import (
        FirstLiveSemiogenesisRuntime,
    )

    state_dir = args.state_dir
    if state_dir == ".solaris_ai_nn_alpha":
        state_dir = ".solaris_ai_nn_live"
    return FirstLiveSemiogenesisRuntime(
        state_dir=state_dir, profile=args.profile,
        max_runtime_s=args.max_runtime_s, max_concepts=args.max_concepts,
        max_signs=args.max_signs, min_utility=args.min_utility,
        strict=args.strict, dry_run=args.dry_run, report_only=args.report_only,
        require_governance=args.require_governance,
        require_birth_certificate=args.require_birth_certificate,
        require_observation_stability=args.require_observation_stability,
        require_live_concepts=args.require_live_concepts,
        allow_limited_birth=args.allow_limited_birth,
        require_claimguard=args.require_claimguard,
        operator_note=args.operator_note)


def _ontogenesis_runtime(args: argparse.Namespace):
    from .live_ontogenesis.ontogenesis_runtime import (
        FirstLiveOntogenesisRuntime,
    )

    state_dir = args.state_dir
    if state_dir == ".solaris_ai_nn_alpha":
        state_dir = ".solaris_ai_nn_live"
    return FirstLiveOntogenesisRuntime(
        state_dir=state_dir, profile=args.profile,
        max_runtime_s=args.max_runtime_s, max_files=args.max_files,
        max_events=args.max_events, max_candidates=args.max_candidates,
        min_recurrence=args.min_recurrence, min_stability=args.min_stability,
        strict=args.strict, dry_run=args.dry_run, report_only=args.report_only,
        require_governance=args.require_governance,
        require_birth_certificate=args.require_birth_certificate,
        require_observation_stability=args.require_observation_stability,
        allow_limited_birth=args.allow_limited_birth,
        require_claimguard=args.require_claimguard,
        operator_note=args.operator_note)


def _observation_runtime(args: argparse.Namespace):
    from .live_observation.observation_runtime import (
        PostBirthLiveObservationRuntime,
    )

    state_dir = args.state_dir
    if state_dir == ".solaris_ai_nn_alpha":
        state_dir = ".solaris_ai_nn_live"
    return PostBirthLiveObservationRuntime(
        state_dir=state_dir, profile=args.profile,
        max_runtime_s=args.max_runtime_s, max_files=args.max_files,
        max_events=args.max_events,
        observation_window_minutes=args.observation_window_minutes,
        strict=args.strict, dry_run=args.dry_run, report_only=args.report_only,
        require_governance=args.require_governance,
        require_birth_certificate=args.require_birth_certificate,
        allow_new_inbox_read=not args.no_inbox_read,
        require_claimguard=args.require_claimguard,
        operator_note=args.operator_note)


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


def cmd_live_observe(args: argparse.Namespace) -> int:
    rt = _observation_runtime(args)
    result = rt.run()
    if result.get("refused"):
        _print(f"live observation refused: {result.get('reason')}")
        return 2
    st = rt.observation_status()
    _print("post-birth live observation:")
    _print(f"  run id: {st['observation_run_id']}")
    _print(f"  blocked: {result['blocked']}")
    for b in result["blockers"]:
        _print(f"    blocker: {b}")
    _print(f"  windows: {st['live_observation_window_count']}; accepted events: "
           f"{st['live_observation_accepted_event_count']}")
    _print(f"  quarantine rate: {st['live_observation_quarantine_rate']:.0%}")
    _print(f"  source diet balance: {st['live_source_diet_balance']}")
    _print(f"  load status: {st['live_load_status']}")
    _print(f"  metabolism confidence: "
           f"{st['metabolism_calibration_confidence']}")
    _print(f"  stability status: {st['live_stability_status']}")
    _print(f"  recommended next phase: {st['live_recommended_next_phase']}")
    _print(f"  first-day record: {st['first_day_record_path']}")
    _print(f"  learns / starts feeders: {st['learns']} / "
           f"{st['starts_feeders']}")
    if result["blocked"] and args.strict:
        return 2
    return 0


def cmd_live_source_health(args: argparse.Namespace) -> int:
    rt = _observation_runtime(args)
    rt.run()
    h = rt.source_health_summary
    _print("live source health:")
    _print(f"  sources: {h.get('live_source_count', 0)} (healthy "
           f"{h.get('live_healthy_source_count', 0)}, noisy "
           f"{h.get('live_noisy_source_count', 0)}, silent "
           f"{h.get('live_silent_source_count', 0)}, forbidden "
           f"{h.get('live_forbidden_source_count', 0)})")
    for src in h.get("sources", []):
        _print(f"    {src['source_id']}: {src['status']} "
               f"(events {src['event_count']}, quarantine "
               f"{src['quarantine_rate']:.0%})")
    if h.get("blocks_stability") and args.strict:
        return 2
    return 0


def cmd_live_source_diet(args: argparse.Namespace) -> int:
    rt = _observation_runtime(args)
    rt.run()
    d = rt.source_diet
    _print("live source diet:")
    _print(f"  total events: {d.get('total_events', 0)}")
    _print(f"  balance: {d.get('balance')}")
    _print(f"  dominant source: {d.get('dominant_source') or 'none'}")
    _print(f"  dominance score: {d.get('live_source_diet_dominance_score', 0.0)}")
    _print(f"  operator pulse proportion: "
           f"{d.get('live_operator_pulse_dominance_score', 0.0)}")
    _print(f"  human text proportion: {d.get('human_text_proportion', 0.0)}")
    return 0


def cmd_live_metabolism_calibration(args: argparse.Namespace) -> int:
    rt = _observation_runtime(args)
    rt.run()
    m = rt.metabolism
    _print("live perceptual metabolism calibration (report-only):")
    _print(f"  confidence: {m.get('calibration_confidence')}")
    _print(f"  recommendations: {m.get('recommendation_count', 0)} "
           f"(applied {m.get('applied')})")
    for rec in m.get("recommendations", []):
        unit = f" {rec['unit']}" if rec.get("unit") else ""
        _print(f"    {rec['name']}: {rec['recommended_value']}{unit}")
    return 0


def cmd_live_stability_gate(args: argparse.Namespace) -> int:
    rt = _observation_runtime(args)
    rt.run()
    g = rt.stability
    _print("live stability gate (advisory only):")
    _print(f"  status: {g.get('live_stability_status')}")
    _print(f"  blocked: {g.get('blocked')}")
    _print(f"  recommended next phase: {g.get('recommended_next_phase')}")
    for b in g.get("blockers", []):
        _print(f"    blocker: {b['blocker']} -> {b['correction']}")
    for w in g.get("warnings", []):
        _print(f"    warning: {w}")
    if g.get("blocked") and args.strict:
        return 2
    return 0


def cmd_live_ontogenesis(args: argparse.Namespace) -> int:
    rt = _ontogenesis_runtime(args)
    result = rt.run()
    if result.get("refused"):
        _print(f"live ontogenesis refused: {result.get('reason')}")
        return 2
    st = rt.ontogenesis_status()
    _print("first live ontogenesis:")
    _print(f"  run id: {st['ontogenesis_run_id']}")
    _print(f"  blocked: {result['blocked']}")
    for b in result["blockers"]:
        _print(f"    blocker: {b}")
    _print(f"  feature vectors: {st['live_feature_vector_count']}; recurrence "
           f"patterns: {st['live_recurrence_pattern_count']}")
    _print(f"  candidates: {st['live_candidate_count']} (stable "
           f"{st['live_stable_candidate_count']}, born "
           f"{st['live_born_proto_concept_count']}, contaminated "
           f"{st['live_contaminated_candidate_count']})")
    _print(f"  birth gate status: {st['live_birth_gate_status']}")
    _print(f"  recommended next phase: {st['recommended_next_phase']}")
    _print(f"  concept memory: {st['latest_concept_memory_path']}")
    _print(f"  enables semiogenesis / starts feeders: "
           f"{st['enables_semiogenesis']} / {st['starts_feeders']}")
    if result["blocked"] and args.strict:
        return 2
    return 0


def cmd_live_concepts(args: argparse.Namespace) -> int:
    import os as _os

    state_dir = args.state_dir
    if state_dir == ".solaris_ai_nn_alpha":
        state_dir = ".solaris_ai_nn_live"
    index = _os.path.join(state_dir, "ontogenesis", "concepts",
                          "LIVE_CONCEPT_MEMORY.json")
    _print("live concept memory:")
    if not _os.path.isfile(index):
        _print("  (no concept memory yet; run live-ontogenesis first)")
        return 0
    with open(index, encoding="utf-8") as fh:
        data = json.load(fh)
    _print(f"  concept records: {data.get('live_concept_record_count', 0)}")
    _print(f"  by status: {data.get('by_status', {})}")
    _print(f"  born: {data.get('born_count', 0)}")
    return 0


def cmd_live_concept_candidates(args: argparse.Namespace) -> int:
    rt = _ontogenesis_runtime(args)
    rt.run()
    _print("live proto-concept candidates:")
    if not rt.candidates:
        _print("  (no candidates; field may be blocked or have too few events)")
    for c in sorted(rt.candidates, key=lambda x: -x.stability_score)[:25]:
        _print(f"  - [{c.status}] recurrence={c.recurrence_count} "
               f"stability={c.stability_score:.2f} "
               f"support={c.supporting_count} counter={c.counter_count}")
    return 0


def cmd_live_concept_birth_gate(args: argparse.Namespace) -> int:
    rt = _ontogenesis_runtime(args)
    rt.run()
    _print("live concept birth gate (conservative):")
    born = [g for g in rt.birth_gate_results if g.get("born")]
    blocked = [g for g in rt.birth_gate_results if g.get("blocked")]
    _print(f"  candidates evaluated: {len(rt.birth_gate_results)}")
    _print(f"  born: {len(born)}; blocked/contaminated: {len(blocked)}")
    for g in rt.birth_gate_results[:25]:
        _print(f"  - {g['candidate_id']}: {g['concept_birth_gate_status']} "
               f"(born={g['born']})")
    if rt.blocked and args.strict:
        return 2
    return 0


def cmd_live_semiogenesis(args: argparse.Namespace) -> int:
    rt = _semiogenesis_runtime(args)
    result = rt.run()
    if result.get("refused"):
        _print(f"live semiogenesis refused: {result.get('reason')}")
        return 2
    st = rt.semiogenesis_status()
    _print("first live semiogenesis:")
    _print(f"  run id: {st['semiogenesis_run_id']}")
    _print(f"  blocked: {result['blocked']}")
    for b in result["blockers"]:
        _print(f"    blocker: {b}")
    _print(f"  eligible concepts: {st['live_eligible_concept_count']}")
    _print(f"  sign candidates: {st['live_sign_candidate_count']} (stable "
           f"{st['live_stable_sign_candidate_count']}, born "
           f"{st['live_born_sign_count']}, contaminated "
           f"{st['live_contaminated_sign_count']})")
    _print(f"  private syntax relations: "
           f"{st['live_private_syntax_relation_count']}")
    _print(f"  sign utility mean: {st['live_sign_utility_score_mean']}")
    _print(f"  sign birth gate status: {st['live_sign_birth_gate_status']}")
    _print(f"  recommended next phase: {st['recommended_next_phase']}")
    _print(f"  sign memory: {st['latest_sign_memory_path']}")
    _print(f"  enables cognition / signs=language: {st['enables_cognition']} / "
           f"{st['signs_are_language_understanding']}")
    if result["blocked"] and args.strict:
        return 2
    return 0


def cmd_live_signs(args: argparse.Namespace) -> int:
    import os as _os

    state_dir = args.state_dir
    if state_dir == ".solaris_ai_nn_alpha":
        state_dir = ".solaris_ai_nn_live"
    index = _os.path.join(state_dir, "semiogenesis", "signs",
                          "LIVE_SIGN_MEMORY.json")
    _print("live sign memory:")
    if not _os.path.isfile(index):
        _print("  (no sign memory yet; run live-semiogenesis first)")
        return 0
    with open(index, encoding="utf-8") as fh:
        data = json.load(fh)
    _print(f"  sign records: {data.get('live_sign_record_count', 0)}")
    _print(f"  by status: {data.get('by_status', {})}")
    _print(f"  born: {data.get('born_count', 0)}")
    return 0


def cmd_live_sign_candidates(args: argparse.Namespace) -> int:
    rt = _semiogenesis_runtime(args)
    rt.run()
    _print("live sign candidates:")
    if not rt.candidates:
        _print("  (no candidates; field may be blocked or lack eligible "
               "concepts)")
    for c in sorted(rt.candidates, key=lambda x: -x.utility_score)[:25]:
        _print(f"  - [{c.status}] token={c.private_token} "
               f"utility={c.utility_score:.2f} "
               f"concepts={len(c.linked_concept_ids)}")
    return 0


def cmd_live_sign_birth_gate(args: argparse.Namespace) -> int:
    rt = _semiogenesis_runtime(args)
    rt.run()
    _print("live sign birth gate (conservative):")
    born = [g for g in rt.birth_gate_results if g.get("born")]
    blocked = [g for g in rt.birth_gate_results if g.get("blocked")]
    _print(f"  candidates evaluated: {len(rt.birth_gate_results)}")
    _print(f"  born: {len(born)}; blocked/contaminated: {len(blocked)}")
    for g in rt.birth_gate_results[:25]:
        _print(f"  - {g['sign_id']}: {g['sign_birth_gate_status']} "
               f"(born={g['born']})")
    if rt.blocked and args.strict:
        return 2
    return 0


def cmd_live_private_syntax(args: argparse.Namespace) -> int:
    rt = _semiogenesis_runtime(args)
    rt.run()
    g = rt.syntax_graph
    _print("live private syntax (operational relation structure, not language):")
    _print(f"  relations: {g.get('live_private_syntax_relation_count', 0)} "
           f"(blocked {g.get('blocked_relation_count', 0)})")
    _print(f"  co-occurs: {g.get('co_occurs_count', 0)}; contrasts: "
           f"{g.get('contrasts_count', 0)}; absence-linked: "
           f"{g.get('absence_linked_count', 0)}")
    for rel in g.get("relations", [])[:25]:
        _print(f"  - {rel['relation_type']} ({rel['strength']}) "
               f"blocked={rel['blocked']}")
    return 0


def cmd_live_cognition(args: argparse.Namespace) -> int:
    rt = _cognition_runtime(args)
    result = rt.run()
    if result.get("refused"):
        _print(f"live cognition refused: {result.get('reason')}")
        return 2
    st = rt.cognition_status()
    _print("first live cognition:")
    _print(f"  run id: {st['cognition_run_id']}")
    _print(f"  blocked: {result['blocked']}")
    for b in result["blockers"]:
        _print(f"    blocker: {b}")
    _print(f"  eligible signs: {st['live_eligible_sign_count']}")
    _print(f"  cognition traces: {st['live_cognition_trace_count']} (useful "
           f"{st['live_useful_trace_count']}, contaminated "
           f"{st['live_contaminated_trace_count']})")
    _print(f"  anticipations: {st['live_anticipation_count']}; internal "
           f"simulations: {st['live_internal_simulation_count']}")
    _print(f"  predictions: {st['live_prediction_assessment_count']} (matched "
           f"{st['live_prediction_matched_count']}, contradicted "
           f"{st['live_prediction_contradicted_count']})")
    _print(f"  mean uncertainty: {st['live_uncertainty_mean']}")
    _print(f"  readiness gate: {st['live_cognition_readiness_status']}")
    _print(f"  recommended next phase: {st['recommended_next_phase']}")
    _print(f"  cognition memory: {st['latest_cognition_memory_path']}")
    _print(f"  enables action / traces=reasoning: {st['enables_action']} / "
           f"{st['traces_prove_reasoning']}")
    if result["blocked"] and args.strict:
        return 2
    return 0


def cmd_live_cognition_traces(args: argparse.Namespace) -> int:
    rt = _cognition_runtime(args)
    rt.run()
    _print("live cognition traces:")
    if not rt.traces:
        _print("  (no traces; field may be blocked or lack eligible signs)")
    for t in sorted(rt.traces, key=lambda x: x.uncertainty)[:25]:
        _print(f"  - [{t.status}] kind={t.kind} "
               f"uncertainty={t.uncertainty:.2f} "
               f"support={t.supporting_count} counter={t.counter_count}")
    return 0


def cmd_live_anticipations(args: argparse.Namespace) -> int:
    rt = _cognition_runtime(args)
    rt.run()
    _print("live anticipations:")
    if not rt.anticipations:
        _print("  (no anticipations; profile may be trace-only or field blocked)")
    for a in rt.anticipations[:25]:
        d = a.to_dict()
        _print(f"  - {d['anticipation_type']} (horizon {d['horizon']}, "
               f"uncertainty {d['uncertainty']:.2f}, {d['status']})")
    return 0


def cmd_live_predictions(args: argparse.Namespace) -> int:
    rt = _cognition_runtime(args)
    rt.run()
    p = rt.prediction
    _print("live prediction assessment:")
    _print(f"  assessed: {p.get('live_prediction_assessment_count', 0)}")
    _print(f"  matched: {p.get('live_prediction_matched_count', 0)}; "
           f"partially: {p.get('partially_matched_count', 0)}; "
           f"contradicted: {p.get('live_prediction_contradicted_count', 0)}")
    _print(f"  not yet observed: {p.get('not_yet_observed_count', 0)}; "
           f"ambiguous: {p.get('ambiguous_count', 0)}")
    _print(f"  prediction utility: {p.get('prediction_utility', 0.0)}")
    return 0


def cmd_live_cognition_gate(args: argparse.Namespace) -> int:
    rt = _cognition_runtime(args)
    rt.run()
    g = rt.readiness
    _print("live cognition readiness gate (advisory only):")
    _print(f"  status: {g.get('cognition_readiness_status')}")
    _print(f"  blocked: {g.get('blocked')}; ready: {g.get('ready')}")
    _print(f"  recommended next phase: {g.get('recommended_next_phase')}")
    for b in g.get("blockers", []):
        _print(f"    blocker: {b['blocker']} -> {b['correction']}")
    for w in g.get("warnings", []):
        _print(f"    warning: {w}")
    if g.get("blocked") and args.strict:
        return 2
    return 0


def cmd_membrane_doctor(args: argparse.Namespace) -> int:
    rt = _membrane_runtime(args)
    doctor = rt.run_doctor()
    _print("environmental membrane doctor:")
    _print(f"  profile: {doctor['membrane_profile']}")
    _print(f"  governance: {doctor['governance_status']} (passed "
           f"{doctor['governance_passed']})")
    _print(f"  feeder registry present: {doctor['feeder_registry_present']}")
    _print(f"  inbox has events: {doctor['inbox_has_events']}")
    _print(f"  bounded: {doctor['bounded']}")
    for b in doctor["blockers"]:
        _print(f"    blocker: {b}")
    _print(f"  passed: {doctor['passed']}")
    if not doctor["passed"] and args.strict:
        return 2
    return 0


def cmd_membrane_run(args: argparse.Namespace) -> int:
    rt = _membrane_runtime(args)
    result = rt.run()
    if result.get("refused"):
        _print(f"membrane run refused: {result.get('reason')}")
        return 2
    st = rt.membrane_status()
    _print("environmental membrane run:")
    _print(f"  run id: {st['membrane_run_id']}")
    _print(f"  blocked: {result['blocked']}")
    for b in result["blockers"]:
        _print(f"    blocker: {b}")
    _print(f"  receptors: {st['membrane_receptor_count']}")
    _print(f"  events in: {st['membrane_event_input_count']}; impressions: "
           f"{st['membrane_impression_count']}")
    _print(f"  allowed: {st['membrane_allowed_count']}; attenuated: "
           f"{st['membrane_attenuated_count']}; blocked: "
           f"{st['membrane_blocked_count']}; quarantined: "
           f"{st['membrane_quarantined_count']}")
    _print(f"  source pressure: {st['source_pressure_status']}")
    _print(f"  latest report: {st['latest_membrane_report_path']}")
    if result["blocked"] and args.strict:
        return 2
    return 0


def cmd_membrane_impressions(args: argparse.Namespace) -> int:
    import os as _os

    state_dir = args.state_dir
    if state_dir == ".solaris_ai_nn_alpha":
        state_dir = ".solaris_ai_nn_live"
    index = _os.path.join(state_dir, "membrane", "impressions",
                          "SENSORY_IMPRESSION_INDEX.json")
    _print("sensory impression index:")
    if not _os.path.isfile(index):
        _print("  (no impressions yet; run membrane-run first)")
        return 0
    with open(index, encoding="utf-8") as fh:
        data = json.load(fh)
    _print(f"  impressions: {data.get('membrane_impression_count', 0)}")
    _print(f"  by kind: {data.get('by_kind', {})}")
    _print(f"  by permeability status: "
           f"{data.get('by_permeability_status', {})}")
    _print(f"  blocked: {data.get('blocked_impression_count', 0)}")
    return 0


def cmd_membrane_report(args: argparse.Namespace) -> int:
    import os as _os

    state_dir = args.state_dir
    if state_dir == ".solaris_ai_nn_alpha":
        state_dir = ".solaris_ai_nn_live"
    report = _os.path.join(state_dir, "membrane", "reports",
                           "ENVIRONMENTAL_MEMBRANE_REPORT.md")
    if _os.path.isfile(report):
        _print(f"environmental membrane report: {report}")
        return 0
    rt = _membrane_runtime(args)
    rt.run()
    _print(f"environmental membrane report: "
           f"{rt.reports.get('markdown')}")
    return 0


def cmd_membrane_memory(args: argparse.Namespace) -> int:
    import os as _os

    state_dir = args.state_dir
    if state_dir == ".solaris_ai_nn_alpha":
        state_dir = ".solaris_ai_nn_live"
    mem = _os.path.join(state_dir, "membrane", "memory", "MEMBRANE_MEMORY.json")
    _print("membrane memory:")
    if not _os.path.isfile(mem):
        _print("  (no membrane memory yet; run membrane-run first)")
        return 0
    with open(mem, encoding="utf-8") as fh:
        data = json.load(fh)
    _print(f"  sources: {data.get('membrane_memory_source_count', 0)}")
    _print(f"  toxic sources: {data.get('toxic_source_count', 0)}")
    for sid, m in (data.get("sources", {}) or {}).items():
        _print(f"    {sid}: reliability {m.get('reliability')} toxicity "
               f"{m.get('toxicity')} (review {m.get('recommend_review')})")
    return 0


def cmd_membrane_integrate(args: argparse.Namespace) -> int:
    rt = _integration_runtime(args)
    result = rt.run()
    if result.get("refused"):
        _print(f"membrane integration refused: {result.get('reason')}")
        return 2
    st = rt.integration_status()
    _print("membrane integration:")
    _print(f"  run id: {st['integration_run_id']} ({st['integration_profile']})")
    _print(f"  blocked: {result['blocked']}")
    for b in result["blockers"]:
        _print(f"    blocker: {b}")
    _print(f"  membrane present: {st['membrane_present']}; impressions: "
           f"{st['impression_count']}")
    _print(f"  ancestry chains: {st['ancestry_chain_count']} (with ancestry "
           f"{st['with_impression_ancestry']}, missing {st['missing_ancestry']})")
    _print(f"  bypass findings: {st['bypass_finding_count']} (critical "
           f"{st['critical_bypass_count']})")
    _print(f"  raw fallback: {st['raw_fallback_count']}; pipeline: "
           f"{st['pipeline_status']}")
    _print(f"  recommended next action: {rt.recommended_next_action()}")
    if (result["blocked"] or st["critical_bypass_count"]) and args.strict:
        return 2
    return 0


def cmd_membrane_audit(args: argparse.Namespace) -> int:
    rt = _integration_runtime(args)
    rt.run()
    au = rt.audit.to_dict() if rt.audit else {}
    _print("membrane pipeline audit:")
    _print(f"  overall status: {au.get('overall_status')}")
    for stg in au.get("stages", []):
        _print(f"  - {stg['stage']}: {stg['status']} "
               f"(impressions {stg['impression_count']}, fallback "
               f"{stg['fallback_count']}, bypass {stg['bypass_findings']})")
    if rt.blocked and args.strict:
        return 2
    return 0


def cmd_membrane_bypass(args: argparse.Namespace) -> int:
    from .membrane_integration import MembraneBypassDetector

    rt = _integration_runtime(args)
    rt.run()
    summ = MembraneBypassDetector.summary(rt.bypass_findings)
    _print("membrane bypass report:")
    _print(f"  findings: {summ['bypass_finding_count']} (worst "
           f"{summ['worst_severity']})")
    _print(f"  by severity: {summ['by_severity']}")
    for f in summ["findings"][:25]:
        _print(f"  - [{f['severity']}] {f['finding']}: {f['detail']}")
    if MembraneBypassDetector.has_blocking(rt.bypass_findings) and args.strict:
        return 2
    return 0


def cmd_membrane_ancestry(args: argparse.Namespace) -> int:
    rt = _integration_runtime(args)
    rt.run()
    a = rt.ancestry.to_dict() if rt.ancestry else {}
    _print("membrane ancestry index:")
    _print(f"  chains: {a.get('ancestry_chain_count', 0)}")
    _print(f"  with impression ancestry: {a.get('with_impression_ancestry', 0)}")
    _print(f"  missing ancestry: {a.get('missing_ancestry', 0)}")
    _print(f"  contaminated ancestry: {a.get('contaminated_ancestry', 0)}")
    _print(f"  by artifact type: {a.get('by_artifact_type', {})}")
    return 0


def cmd_membrane_contracts(args: argparse.Namespace) -> int:
    from .membrane_integration.downstream_contracts import summary

    rt = _integration_runtime(args)
    rt.run()
    s = summary(rt.contracts) if rt.contracts else {}
    _print("membrane downstream contracts:")
    _print(f"  contracts: {s.get('contract_count', 0)}; violated: "
           f"{s.get('violated_count', 0)}")
    for c in s.get("contracts", []):
        _print(f"  - {c['module']}: {c['status']}")
    if s.get("violated_count", 0) and args.strict:
        return 2
    return 0


def cmd_tester_demo(args: argparse.Namespace) -> int:
    rt = _tester_runtime(args)
    result = rt.run()
    if result.get("refused"):
        _print(f"tester demo refused: {result.get('reason')}")
        return 2
    st = rt.tester_status()
    _print("tester fixture demo:")
    _print(f"  run id: {st['tester_run_id']} ({st['tester_profile']})")
    _print(f"  fixture-only: {st['fixture_only']}; requires live data: "
           f"{st['requires_live_data']}")
    _print(f"  fixture events: {st['fixture_event_count']} (quarantined "
           f"{st['fixture_quarantined_count']})")
    _print(f"  membrane impressions: {st['membrane_impression_count']}")
    _print(f"  golden run: {st['golden_run_status']}")
    _print(f"  reproducibility: {st['reproducibility_status']}")
    _print(f"  regression: {st['regression_status']}")
    _print(f"  skipped optional stages: "
           f"{', '.join(st['skipped_optional_stages']) or 'none'}")
    _print(f"  blocked: {st['tester_blocked']}")
    for b in result["blockers"]:
        _print(f"    blocker: {b}")
    _print(f"  tester report: {st['latest_tester_report_path']}")
    _print(f"  tester bundle: {st['latest_tester_bundle_path']}")
    _print(f"  next action: {rt.recommended_next_action()}")
    if result["blocked"] and args.strict:
        return 2
    return 0


def cmd_tester_golden(args: argparse.Namespace) -> int:
    from .tester_fixture_spine.golden_manifest import GoldenRunManifest

    rt = _tester_runtime(args)
    state_dir = rt.state_dir
    existing = GoldenRunManifest.load(state_dir)
    if existing is None or args.regenerate_golden:
        rt.regenerate_golden = True
        rt.run()
        manifest = GoldenRunManifest.load(state_dir)
        _print("tester golden manifest built:")
    else:
        manifest = existing
        _print("tester golden manifest validated:")
    d = manifest.to_dict() if manifest else {}
    _print(f"  profile: {d.get('profile_id')}")
    _print(f"  fixture hash: {d.get('fixture_hash', '')[:16]}")
    _print(f"  artifacts: {d.get('artifact_count', 0)} (required "
           f"{d.get('required_artifact_count', 0)}, missing required "
           f"{d.get('missing_required_artifact_count', 0)})")
    if d.get("missing_required_artifact_count", 0) and args.strict:
        return 2
    return 0


def cmd_tester_bundle(args: argparse.Namespace) -> int:
    rt = _tester_runtime(args)
    rt.run()
    m = rt.bundle.manifest.to_dict() if rt.bundle else {}
    _print("tester artifact bundle:")
    _print(f"  bundle dir: {m.get('bundle_dir')}")
    _print(f"  entries: {m.get('entry_count', 0)}")
    _print(f"  missing optional: "
           f"{', '.join(m.get('missing_optional_artifacts', [])) or 'none'}")
    _print(f"  local only: {m.get('local_only')}; uploaded: "
           f"{m.get('uploaded')}; published: {m.get('published')}")
    return 0


def cmd_tester_repro(args: argparse.Namespace) -> int:
    rt = _tester_runtime(args)
    rt.run()
    r = rt.reproducibility
    _print("tester reproducibility check:")
    _print(f"  status: {r.get('reproducibility_status')}")
    _print(f"  findings: {r.get('finding_count', 0)} (fail "
           f"{r.get('fail_count', 0)}, warn {r.get('warning_count', 0)})")
    for f in r.get("findings", []):
        if not f["passed"]:
            _print(f"    [{f['severity']}] {f['check']}: {f['detail']}")
    if r.get("reproducibility_status") in ("fail", "blocked") and args.strict:
        return 2
    return 0


def cmd_tester_regression(args: argparse.Namespace) -> int:
    rt = _tester_runtime(args)
    rt.run()
    r = rt.regression
    _print("tester regression check:")
    _print(f"  status: {r.get('regression_status')}")
    _print(f"  findings: {r.get('finding_count', 0)} (regression "
           f"{r.get('regression_count', 0)})")
    for f in r.get("findings", []):
        if f["regressed"]:
            _print(f"    [{f['severity']}] {f['check']}: {f['detail']}")
    if r.get("regression_status") in ("regression", "blocked") and args.strict:
        return 2
    return 0


def cmd_tester_fixtures(args: argparse.Namespace) -> int:
    from .tester_fixture_spine.fixture_pack import (
        FixturePackBuilder, FixturePackValidator)

    rt = _tester_runtime(args)
    path = rt._fixture_path()
    pack = FixturePackBuilder().load(path)
    validation = FixturePackValidator().validate(pack)
    d = pack.to_dict()
    _print("tester fixture pack:")
    _print(f"  source: {pack.source_path}")
    _print(f"  events: {d['fixture_event_count']} (unsafe "
           f"{d['fixture_unsafe_event_count']})")
    _print(f"  fixture hash: {d['fixture_hash'][:16]}")
    _print(f"  kinds: {d['kind_histogram']}")
    _print(f"  valid: {validation['valid']}; has unsafe-for-quarantine: "
           f"{validation['has_unsafe_event_for_quarantine']}")
    if not validation["valid"] and args.strict:
        return 2
    return 0


def cmd_tester_live_init(args: argparse.Namespace) -> int:
    rt = _tester_live_runtime(
        args, profile="tester_live_init_only_v0", write_templates=True,
        run_birth=False, run_membrane=False, run_integration=False,
        run_observation=False)
    result = rt.run()
    if result.get("refused"):
        _print(f"tester live init refused: {result.get('reason')}")
        return 2
    st = rt.tester_live_status()
    _print("tester live-read-only init:")
    _print(f"  run id: {st['tester_live_run_id']} ({st['tester_live_profile']})")
    _print(f"  state dir: {rt.state_dir}; tester state: {rt.tester_state_dir}")
    _print(f"  governance: {st['governance_status']} (templates written; edit "
           "by hand to enable)")
    _print(f"  feeder registry present: {st['feeder_registry_present']}")
    _print(f"  live doctor: {st['live_doctor_status']}")
    for step in result["recommended_next_steps"]:
        _print(f"  next: {step}")
    return 0


def cmd_tester_live_doctor(args: argparse.Namespace) -> int:
    rt = _tester_live_runtime(args, write_templates=False, run_birth=False,
                              run_membrane=False, run_integration=False,
                              run_observation=False)
    doc = rt.run_doctor()
    _print("tester live doctor:")
    _print(f"  overall status: {doc.get('overall_status')}")
    _print(f"  blockers: {doc.get('blocker_count', 0)}; warnings: "
           f"{doc.get('warning_count', 0)}")
    for f in doc.get("findings", []):
        if f["status"] in ("blocked", "unsafe", "missing"):
            _print(f"    [{f['status']}] {f['check']}: {f['detail']}")
    if not doc.get("passed") and args.strict:
        return 2
    return 0


def cmd_tester_live_samples(args: argparse.Namespace) -> int:
    from .tester_live_readonly import SafeEventPackBuilder, SafeEventPackValidator

    res = SafeEventPackValidator(strict=True).validate_pack(
        SafeEventPackBuilder().build())
    _print("tester live sample event packs:")
    _print(f"  safe accepted: {res['safe']['accepted_count']}/"
           f"{res['safe']['event_count']} (all accepted "
           f"{bool(res['safe']['all_accepted'])})")
    _print(f"  unsafe quarantined: {res['unsafe']['quarantined_count']}/"
           f"{res['unsafe']['event_count']} (all quarantined "
           f"{bool(res['unsafe']['all_quarantined'])})")
    _print(f"  mixed: accepted {res['mixed']['accepted_count']}, quarantined "
           f"{res['mixed']['quarantined_count']} (partial "
           f"{res['mixed']['partially_accepted']})")
    ok = (res["safe"]["all_accepted"] and res["unsafe"]["all_quarantined"]
          and res["mixed"]["partially_accepted"])
    if not ok and args.strict:
        return 2
    return 0


def cmd_tester_live_run(args: argparse.Namespace) -> int:
    rt = _tester_live_runtime(args)
    result = rt.run()
    if result.get("refused"):
        _print(f"tester live run refused: {result.get('reason')}")
        return 2
    st = rt.tester_live_status()
    _print("tester live-read-only run:")
    _print(f"  run id: {st['tester_live_run_id']} ({st['tester_live_profile']})")
    _print(f"  governance: {st['governance_status']} (enabled+approved "
           f"{st['governance_enabled_and_approved']})")
    _print(f"  live doctor: {st['live_doctor_status']}")
    _print(f"  membrane impressions: {st['membrane_impression_count']}; "
           f"quarantined: {st['quarantine_count']}")
    _print(f"  solaris controls any feeder: "
           f"{st['solaris_controls_any_feeder']}")
    _print(f"  blocked: {st['tester_live_blocked']}")
    for b in result["blockers"]:
        _print(f"    blocker: {b}")
    _print(f"  tester report: {result['tester_live_report']}")
    _print(f"  tester bundle: {result['tester_live_bundle']}")
    for step in result["recommended_next_steps"]:
        _print(f"  next: {step}")
    if result["blocked"] and args.strict:
        return 2
    return 0


def cmd_tester_live_bundle(args: argparse.Namespace) -> int:
    rt = _tester_live_runtime(args, write_templates=False, run_birth=False,
                              run_membrane=False, run_integration=False,
                              run_observation=False)
    rt.run()
    m = rt.bundle.manifest.to_dict() if rt.bundle else {}
    _print("tester live bundle:")
    _print(f"  bundle dir: {m.get('bundle_dir', rt.bundle_dir)}")
    _print(f"  entries: {m.get('entry_count', 0)}")
    _print(f"  redactions: {', '.join(m.get('redactions', [])) or 'none'}")
    _print(f"  missing artifacts: "
           f"{', '.join(m.get('missing_artifacts', [])) or 'none'}")
    _print(f"  local only: {m.get('local_only')}; uploaded: {m.get('uploaded')}; "
           f"published: {m.get('published')}")
    return 0


def cmd_tester_live_checklist(args: argparse.Namespace) -> int:
    import os

    from .tester_live_readonly import TesterLiveChecklist

    checklist = TesterLiveChecklist.build()
    base = os.path.join(args.tester_state_dir, "checklists")
    os.makedirs(base, exist_ok=True)
    path = os.path.join(base, "TESTER_LIVE_CHECKLIST.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(checklist.to_markdown())
    _print("tester live checklist:")
    _print(f"  written: {path}")
    _print(f"  sections: {len(checklist.sections)}; stop conditions: "
           f"{len(checklist.stop_conditions())}")
    for sc in checklist.stop_conditions():
        _print(f"    STOP: {sc}")
    return 0


def _print_console_summary(rt, result) -> None:
    _print("tester console:")
    _print(f"  run id: {result['run_id']} ({result['console_profile']})")
    _print(f"  overall health: {result['overall_health']}")
    _print(f"  safety: {result['safety_status']} (blockers "
           f"{result['blocker_count']}, warnings {result['warning_count']})")
    _print(f"  artifacts: {result['artifact_count']} (missing required "
           f"{result['missing_artifact_count']})")
    _print(f"  next action: {result['latest_next_action']}")
    if result.get("latest_console_index_path"):
        _print(f"  INDEX.md: {result['latest_console_index_path']}")
    if result.get("latest_console_html_path"):
        _print(f"  INDEX.html: {result['latest_console_html_path']}")


def cmd_tester_console(args: argparse.Namespace) -> int:
    rt = _tester_console_runtime(args)
    result = rt.run()
    if result.get("refused"):
        _print(f"tester console refused: {result.get('reason')}")
        return 2
    _print_console_summary(rt, result)
    if result["safety_status"] == "blocked" and args.strict:
        return 2
    return 0


def cmd_tester_console_md(args: argparse.Namespace) -> int:
    rt = _tester_console_runtime(args, profile="tester_console_markdown_only_v0",
                                 html=False)
    result = rt.run()
    if result.get("refused"):
        _print(f"tester console refused: {result.get('reason')}")
        return 2
    _print_console_summary(rt, result)
    if result["safety_status"] == "blocked" and args.strict:
        return 2
    return 0


def cmd_tester_console_html(args: argparse.Namespace) -> int:
    rt = _tester_console_runtime(args, profile="tester_console_html_static_v0",
                                 html=True)
    result = rt.run()
    if result.get("refused"):
        _print(f"tester console refused: {result.get('reason')}")
        return 2
    _print("tester console (static HTML):")
    _print(f"  INDEX.html: {result.get('latest_console_html_path')}")
    _print(f"  overall health: {result['overall_health']}; safety: "
           f"{result['safety_status']}")
    if result["safety_status"] == "blocked" and args.strict:
        return 2
    return 0


def cmd_tester_console_status(args: argparse.Namespace) -> int:
    rt = _tester_console_runtime(args, profile="tester_console_status_only_v0",
                                 html=False, dry_run=True)
    rt.run()
    st = rt.console_status()
    _print("tester console status:")
    _print(f"  overall health: {st['overall_health']}; release ready: "
           f"{st['release_ready']}")
    _print(f"  safety: {st['safety_status']} (blockers "
           f"{st['safety_block_count']})")
    _print(f"  artifacts: {st['artifact_count']}; missing required: "
           f"{st['missing_artifact_count']}")
    _print(f"  cards: {st['card_count']}; runs: {st['run_index_count']}")
    _print(f"  next action: {st['latest_next_action']}")
    if st["safety_status"] == "blocked" and args.strict:
        return 2
    return 0


def cmd_tester_console_runs(args: argparse.Namespace) -> int:
    rt = _tester_console_runtime(args, html=False, dry_run=True)
    rt.run()
    idx = rt.run_index.to_dict() if rt.run_index else {}
    _print("tester console runs:")
    _print(f"  runs: {idx.get('run_count', 0)}; latest: "
           f"{idx.get('latest_run_id', '-')}")
    for r in idx.get("runs", [])[:25]:
        _print(f"  - {r['run_id']} [{r['run_type']}] {r['status']}"
               + ("  (latest)" if r["latest"] else ""))
    return 0


def _print_feedback_summary(result) -> None:
    _print(f"  entries: {result['entry_count']} (bugs "
           f"{result['bug_report_count']}, safety "
           f"{result['safety_concern_count']})")
    _print(f"  release blockers: {result['release_blocker_count']} "
           f"(stop-testing {result['stop_testing_count']})")
    _print(f"  redactions: {result['redaction_count']}")
    _print(f"  next action: {result['recommended_next_action']}")


def cmd_tester_feedback_init(args: argparse.Namespace) -> int:
    import os

    rt = _tester_feedback_runtime(args, profile="tester_feedback_forms_only_v0",
                                  forms_only=True)
    result = rt.run()
    if result.get("refused"):
        _print(f"tester feedback init refused: {result.get('reason')}")
        return 2
    _print("tester feedback init:")
    _print(f"  forms: {os.path.join(rt.feedback_dir, 'forms')}")
    _print(f"  ledger: {rt.ledger.jsonl_path}")
    _print("  feedback is LOCAL QA evidence only -- not training, not RLHF, "
           "not ground truth, not a command.")
    return 0


def cmd_tester_feedback_ingest(args: argparse.Namespace) -> int:
    if not args.ingest_path:
        _print("tester feedback ingest: --ingest-path is required")
        return 2
    rt = _tester_feedback_runtime(args)
    result = rt.run()
    if result.get("refused"):
        _print(f"tester feedback ingest refused: {result.get('reason')}")
        return 2
    _print("tester feedback ingest:")
    _print(f"  ingested: {args.ingest_path}")
    _print_feedback_summary(result)
    for w in rt.warnings:
        _print(f"  warning: {w}")
    if result["stop_testing_count"] and args.strict:
        return 2
    if result["release_blocker_count"] and args.strict:
        return 2
    return 0


def cmd_tester_feedback_report(args: argparse.Namespace) -> int:
    rt = _tester_feedback_runtime(args)
    result = rt.run()
    if result.get("refused"):
        _print(f"tester feedback report refused: {result.get('reason')}")
        return 2
    _print("tester feedback report:")
    _print(f"  report: {result['latest_feedback_report_path']}")
    _print_feedback_summary(result)
    if result["release_blocker_count"] and args.strict:
        return 2
    return 0


def cmd_tester_feedback_ledger(args: argparse.Namespace) -> int:
    rt = _tester_feedback_runtime(args, profile="tester_feedback_ledger_v0",
                                  dry_run=True)
    rt.run()
    index = rt.ledger_index().to_dict()
    _print("tester feedback ledger:")
    _print(f"  entries: {index['entry_count']}; by type: {index['by_type']}")
    _print(f"  release blockers: {index['release_blocker_count']} "
           f"(stop-testing {index['stop_testing_count']})")
    _print(f"  safety concerns: {index['safety_concern_count']}; redactions: "
           f"{index['redaction_count']}")
    _print(f"  ledger: {rt.ledger.jsonl_path}")
    return 0


def cmd_tester_feedback_bundle(args: argparse.Namespace) -> int:
    rt = _tester_feedback_runtime(args, build_bundle=True)
    result = rt.run()
    if result.get("refused"):
        _print(f"tester feedback bundle refused: {result.get('reason')}")
        return 2
    m = rt.bundle.manifest.to_dict() if rt.bundle else {}
    _print("tester feedback bundle:")
    _print(f"  bundle dir: {m.get('bundle_dir', rt.bundle_dir)}")
    _print(f"  entries: {m.get('entry_count', 0)}; redactions: "
           f"{m.get('redaction_count', 0)}")
    _print(f"  local only: {m.get('local_only')}; uploaded: {m.get('uploaded')}; "
           f"published: {m.get('published')}")
    return 0


def cmd_tester_feedback_blockers(args: argparse.Namespace) -> int:
    rt = _tester_feedback_runtime(args, dry_run=True)
    rt.run()
    index = rt.ledger_index()
    _print("tester feedback release blockers:")
    _print(f"  release blockers: {index.release_blocker_count} "
           f"(stop-testing {index.stop_testing_count})")
    for e in index.entries:
        if e.release_blocker_status in ("release_blocker", "stop_testing"):
            _print(f"  - [{e.release_blocker_status}] {e.feedback_id} "
                   f"({e.release_blocker_reason})")
    _print(f"  next action: {rt.recommended_next_action()}")
    if index.release_blocker_count and args.strict:
        return 2
    return 0


def cmd_tester_packaging(args: argparse.Namespace) -> int:
    rt = _tester_packaging_runtime(args)
    result = rt.run()
    if result.get("refused"):
        _print(f"tester packaging refused: {result.get('reason')}")
        return 2
    _print("tester packaging:")
    _print(f"  run id: {result['run_id']} ({result['packaging_profile']})")
    _print(f"  readiness: {result['readiness']}")
    _print(f"  doctor: {result['doctor_status']}; dependency blockers: "
           f"{result['dependency_blocker_count']}")
    _print(f"  missing required commands: "
           f"{result['missing_required_command_count']}")
    _print(f"  clean-machine: {result['clean_machine_status']}; release: "
           f"{result['release_readiness']}")
    for b in result["blockers"]:
        _print(f"    blocker: {b}")
    _print(f"  report: {result['latest_packaging_report_path']}")
    _print(f"  install guide: {result['latest_install_guide_path']}")
    for a in result["next_actions"]:
        _print(f"  next: {a}")
    if result["blocked"] and args.strict:
        return 2
    return 0


def cmd_tester_install_guide(args: argparse.Namespace) -> int:
    rt = _tester_packaging_runtime(args, profile="tester_packaging_guides_v0")
    result = rt.run()
    if result.get("refused"):
        _print(f"tester install guide refused: {result.get('reason')}")
        return 2
    _print("tester install guide:")
    for label, path in rt.guide_paths.items():
        _print(f"  {label}: {path}")
    for kind, path in rt.platform_paths.items():
        _print(f"  platform {kind}: {path}")
    return 0


def cmd_tester_release_manifest(args: argparse.Namespace) -> int:
    rt = _tester_packaging_runtime(args, profile="tester_packaging_manifest_v0")
    rt.run()
    m = rt.manifest.to_dict() if rt.manifest else {}
    _print("tester release manifest:")
    _print(f"  package: {m.get('package_name')} {m.get('version')} "
           f"(commit {m.get('commit', 'unknown')[:12]})")
    _print(f"  readiness: {m.get('readiness')}")
    _print(f"  artifacts: {m.get('artifact_count', 0)}; missing required: "
           f"{m.get('missing_required', [])}")
    _print(f"  missing optional: {m.get('missing_optional', [])}")
    _print(f"  manifest: {rt.packaging_status()['latest_release_manifest_path']}")
    if m.get("missing_required") and args.strict:
        return 2
    return 0


def cmd_tester_clean_machine(args: argparse.Namespace) -> int:
    rt = _tester_packaging_runtime(args,
                                   profile="tester_packaging_clean_machine_v0")
    rt.run()
    c = rt.clean_machine_result.to_dict() if rt.clean_machine_result else {}
    _print("tester clean-machine readiness:")
    _print(f"  status: {c.get('status')}; blockers: {c.get('blocker_count', 0)}")
    for b in c.get("blockers", []):
        _print(f"    blocker: {b}")
    if not c.get("passed", True) and args.strict:
        return 2
    return 0


def cmd_tester_command_check(args: argparse.Namespace) -> int:
    from .tester_packaging import CommandRegistryCheck

    result = CommandRegistryCheck().check()
    d = result.to_dict()
    _print("tester command registry check:")
    _print(f"  registered: {d['registered_count']}/{d['command_count']}")
    _print(f"  missing required: {d['missing_required']}")
    _print(f"  missing optional: {d['missing_optional']}")
    if d["missing_required"] and args.strict:
        return 2
    return 0


def cmd_tester_safety_freeze(args: argparse.Namespace) -> int:
    rt = _tester_safety_freeze_runtime(args)
    result = rt.run()
    if result.get("refused"):
        _print(f"tester safety freeze refused: {result.get('reason')}")
        return 2
    st = rt.safety_freeze_status()
    _print("tester safety freeze:")
    _print(f"  run id: {st['safety_freeze_run_id']} "
           f"({st['safety_freeze_profile']})")
    _print(f"  readiness: {st['readiness']}")
    _print(f"  forbidden claims: {st['forbidden_claim_count']}; capability "
           f"blockers: {st['capability_blocker_count']}")
    _print(f"  release blockers: {st['release_blocker_count']} (critical "
           f"{st['critical_blocker_count']})")
    _print(f"  release candidate allowed: {st['release_candidate_allowed']}")
    for b in rt.blocker_gate.to_dict()["blockers"]:
        if b["is_open"]:
            _print(f"    blocker: [{b['category']}] {b['detail']}")
    _print(f"  report: {st['latest_safety_freeze_report_path']}")
    _print(f"  next action: {rt.recommended_next_action()}")
    if st["release_blocker_count"] and args.strict:
        return 2
    return 0


def cmd_tester_claim_freeze(args: argparse.Namespace) -> int:
    rt = _tester_safety_freeze_runtime(
        args, profile="tester_claim_freeze_only_v0")
    rt.run()
    c = rt.claim_result.to_dict() if rt.claim_result else {}
    _print("tester claim freeze:")
    _print(f"  scanned files: {c.get('scanned_files', 0)}")
    _print(f"  forbidden claims: {c.get('forbidden_claim_count', 0)}; release "
           f"blockers: {c.get('release_blocker_count', 0)}")
    _print(f"  missing disclaimers: {len(c.get('missing_disclaimers', []))}")
    for f in c.get("findings", [])[:20]:
        if f["severity"] in ("blocker", "release_blocker", "critical"):
            _print(f"    [{f['severity']}] {f['category']} {f['path']}:"
                   f"{f['line']}")
    if c.get("release_blocker_count", 0) and args.strict:
        return 2
    return 0


def cmd_tester_capability_freeze(args: argparse.Namespace) -> int:
    rt = _tester_safety_freeze_runtime(
        args, profile="tester_capability_freeze_only_v0")
    rt.run()
    c = rt.capability_result.to_dict() if rt.capability_result else {}
    _print("tester capability freeze:")
    _print(f"  scanned files: {c.get('scanned_files', 0)}")
    _print(f"  blockers: {c.get('blocker_count', 0)}; by category: "
           f"{c.get('by_category', {})}")
    for f in c.get("findings", [])[:20]:
        if f["blocking"]:
            _print(f"    [{f['category']}] {f['path']}:{f['line']} "
                   f"{f['matched_text']}")
    if c.get("blocker_count", 0) and args.strict:
        return 2
    return 0


def cmd_tester_redteam(args: argparse.Namespace) -> int:
    rt = _tester_safety_freeze_runtime(args, profile="tester_red_team_only_v0")
    rt.run()
    r = rt.red_team_result.to_dict() if rt.red_team_result else {}
    _print("tester red-team checklist:")
    _print(f"  checks: {r.get('check_count', 0)} (pass {r.get('pass_count', 0)}, "
           f"fail {r.get('fail_count', 0)}, unknown {r.get('unknown_count', 0)})")
    _print(f"  blockers: {r.get('blocker_count', 0)}")
    for c in r.get("checks", []):
        if c["blocking"]:
            _print(f"    [{c['status']}] {c['check_id']}: {c['question']}")
    if r.get("blocker_count", 0) and args.strict:
        return 2
    return 0


def cmd_tester_release_blockers(args: argparse.Namespace) -> int:
    rt = _tester_safety_freeze_runtime(args)
    rt.run()
    g = rt.blocker_gate.to_dict() if rt.blocker_gate else {}
    _print("tester release blockers:")
    _print(f"  release candidate allowed: "
           f"{g.get('release_candidate_allowed')}")
    _print(f"  open blockers: {g.get('open_blocker_count', 0)} (critical "
           f"{g.get('critical_open_count', 0)}); waived: "
           f"{g.get('waived_count', 0)}")
    for b in g.get("blockers", []):
        if b["is_open"]:
            _print(f"    [{b['category']}] {b['detail']}")
    if g.get("open_blocker_count", 0) and args.strict:
        return 2
    return 0


def cmd_tester_safety_scan(args: argparse.Namespace) -> int:
    rt = _tester_safety_freeze_runtime(
        args, profile="tester_artifact_scan_only_v0")
    rt.run()
    a = rt.artifact_result.to_dict() if rt.artifact_result else {}
    _print("tester artifact safety scan:")
    _print(f"  scanned files: {a.get('scanned_files', 0)}")
    _print(f"  blockers: {a.get('blocker_count', 0)}; warnings: "
           f"{a.get('warning_count', 0)}")
    _print(f"  by kind: {a.get('by_kind', {})}")
    for f in a.get("findings", [])[:20]:
        if f["blocking"]:
            _print(f"    [{f['kind']}] {f['path']}:{f['line']} {f['detail']}")
    if a.get("blocker_count", 0) and args.strict:
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
    "build-docs": cmd_build_docs,
    "docs-index": cmd_docs_index,
    "whitepaper": cmd_whitepaper,
    "live-init": cmd_live_init,
    "live-doctor": cmd_live_doctor,
    "live-birth": cmd_live_birth,
    "live-quarantine": cmd_live_quarantine,
    "birth-certificate": cmd_birth_certificate,
    "live-observe": cmd_live_observe,
    "live-source-health": cmd_live_source_health,
    "live-source-diet": cmd_live_source_diet,
    "live-metabolism-calibration": cmd_live_metabolism_calibration,
    "live-stability-gate": cmd_live_stability_gate,
    "live-ontogenesis": cmd_live_ontogenesis,
    "live-concepts": cmd_live_concepts,
    "live-concept-candidates": cmd_live_concept_candidates,
    "live-concept-birth-gate": cmd_live_concept_birth_gate,
    "live-semiogenesis": cmd_live_semiogenesis,
    "live-signs": cmd_live_signs,
    "live-sign-candidates": cmd_live_sign_candidates,
    "live-sign-birth-gate": cmd_live_sign_birth_gate,
    "live-private-syntax": cmd_live_private_syntax,
    "live-cognition": cmd_live_cognition,
    "live-cognition-traces": cmd_live_cognition_traces,
    "live-anticipations": cmd_live_anticipations,
    "live-predictions": cmd_live_predictions,
    "live-cognition-gate": cmd_live_cognition_gate,
    "membrane-doctor": cmd_membrane_doctor,
    "membrane-run": cmd_membrane_run,
    "membrane-impressions": cmd_membrane_impressions,
    "membrane-report": cmd_membrane_report,
    "membrane-memory": cmd_membrane_memory,
    "membrane-integrate": cmd_membrane_integrate,
    "membrane-audit": cmd_membrane_audit,
    "membrane-bypass": cmd_membrane_bypass,
    "membrane-ancestry": cmd_membrane_ancestry,
    "membrane-contracts": cmd_membrane_contracts,
    "tester-demo": cmd_tester_demo,
    "tester-golden": cmd_tester_golden,
    "tester-bundle": cmd_tester_bundle,
    "tester-repro": cmd_tester_repro,
    "tester-regression": cmd_tester_regression,
    "tester-fixtures": cmd_tester_fixtures,
    "tester-live-init": cmd_tester_live_init,
    "tester-live-doctor": cmd_tester_live_doctor,
    "tester-live-samples": cmd_tester_live_samples,
    "tester-live-run": cmd_tester_live_run,
    "tester-live-bundle": cmd_tester_live_bundle,
    "tester-live-checklist": cmd_tester_live_checklist,
    "tester-console": cmd_tester_console,
    "tester-console-md": cmd_tester_console_md,
    "tester-console-html": cmd_tester_console_html,
    "tester-console-status": cmd_tester_console_status,
    "tester-console-runs": cmd_tester_console_runs,
    "tester-feedback-init": cmd_tester_feedback_init,
    "tester-feedback-ingest": cmd_tester_feedback_ingest,
    "tester-feedback-report": cmd_tester_feedback_report,
    "tester-feedback-ledger": cmd_tester_feedback_ledger,
    "tester-feedback-bundle": cmd_tester_feedback_bundle,
    "tester-feedback-blockers": cmd_tester_feedback_blockers,
    "tester-packaging": cmd_tester_packaging,
    "tester-install-guide": cmd_tester_install_guide,
    "tester-release-manifest": cmd_tester_release_manifest,
    "tester-clean-machine": cmd_tester_clean_machine,
    "tester-command-check": cmd_tester_command_check,
    "tester-safety-freeze": cmd_tester_safety_freeze,
    "tester-claim-freeze": cmd_tester_claim_freeze,
    "tester-capability-freeze": cmd_tester_capability_freeze,
    "tester-redteam": cmd_tester_redteam,
    "tester-release-blockers": cmd_tester_release_blockers,
    "tester-safety-scan": cmd_tester_safety_scan,
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
    # Post-birth live observation arguments (Prompt 68).
    parser.add_argument("--observation-window-minutes", type=int, default=30,
                        dest="observation_window_minutes",
                        help="bounded observation window size in minutes")
    parser.add_argument("--require-birth-certificate", action="store_true",
                        default=False, dest="require_birth_certificate",
                        help="require a birth certificate before observing")
    parser.add_argument("--no-inbox-read", action="store_true", default=False,
                        dest="no_inbox_read",
                        help="do not read new inbox events during observation")
    # First live ontogenesis arguments (Prompt 69).
    parser.add_argument("--max-candidates", type=int, default=200,
                        dest="max_candidates",
                        help="bounded max proto-concept candidates")
    parser.add_argument("--min-recurrence", type=int, default=3,
                        dest="min_recurrence",
                        help="minimum recurrence for a proto-concept candidate")
    parser.add_argument("--min-stability", type=float, default=0.6,
                        dest="min_stability",
                        help="minimum stability score for concept birth")
    parser.add_argument("--require-observation-stability", action="store_true",
                        default=False, dest="require_observation_stability",
                        help="require an unblocked observation stability gate")
    parser.add_argument("--allow-limited-birth", action="store_true",
                        default=False, dest="allow_limited_birth",
                        help="allow conservative proto-concept/sign birth (else "
                             "candidate-only)")
    # First live semiogenesis arguments (Prompt 70).
    parser.add_argument("--max-concepts", type=int, default=200,
                        dest="max_concepts",
                        help="bounded max eligible concepts consumed for signs")
    parser.add_argument("--max-signs", type=int, default=200, dest="max_signs",
                        help="bounded max private sign candidates")
    parser.add_argument("--min-utility", type=float, default=0.6,
                        dest="min_utility",
                        help="minimum sign utility score for sign birth")
    parser.add_argument("--require-live-concepts", action="store_true",
                        default=False, dest="require_live_concepts",
                        help="require eligible live proto-concepts before signs")
    # First live cognition arguments (Prompt 71).
    parser.add_argument("--max-traces", type=int, default=200,
                        dest="max_traces", help="bounded max cognition traces")
    parser.add_argument("--max-simulation-steps", type=int, default=8,
                        dest="max_simulation_steps",
                        help="bounded max internal-simulation steps")
    parser.add_argument("--max-traversal-depth", type=int, default=3,
                        dest="max_traversal_depth",
                        help="bounded max private-syntax traversal depth")
    parser.add_argument("--min-prediction-utility", type=float, default=0.5,
                        dest="min_prediction_utility",
                        help="minimum prediction utility for readiness")
    parser.add_argument("--max-uncertainty", type=float, default=0.6,
                        dest="max_uncertainty",
                        help="max uncertainty for trace promotion")
    parser.add_argument("--require-live-signs", action="store_true",
                        default=False, dest="require_live_signs",
                        help="require eligible live signs before cognition")
    # Membrane integration arguments (Prompt 73).
    parser.add_argument("--require-membrane", action="store_true",
                        default=False, dest="require_membrane",
                        help="require membrane artifacts for integration")
    parser.add_argument("--require-impressions", action="store_true",
                        default=False, dest="require_impressions",
                        help="require sensory impressions for integration")
    parser.add_argument("--require-ancestry", action="store_true",
                        default=False, dest="require_ancestry",
                        help="require impression ancestry for promoted artifacts")
    parser.add_argument("--allow-raw-fallback", action="store_true",
                        default=False, dest="allow_raw_fallback",
                        help="permit raw-event fallback (loudly reported)")
    # Tester fixture spine arguments (Prompt 74).
    parser.add_argument("--fixture-pack-path", type=str, default="",
                        dest="fixture_pack_path",
                        help="path to a fixture events JSONL (default: canonical)")
    parser.add_argument("--regenerate-golden", action="store_true",
                        default=False, dest="regenerate_golden",
                        help="rebuild the golden run manifest from this run")
    parser.add_argument("--no-optional-stages", action="store_false",
                        default=True, dest="allow_optional_stages",
                        help="skip optional ontogenesis/semiogenesis/cognition")
    # Tester live-read-only arguments (Prompt 75).
    parser.add_argument("--tester-state-dir", type=str,
                        default=".solaris_ai_nn_tester/live",
                        dest="tester_state_dir",
                        help="tester live state directory root")
    parser.add_argument("--no-write-templates", action="store_false",
                        default=True, dest="write_templates",
                        help="do not write governance/feeder templates")
    parser.add_argument("--copy-safe-samples", action="store_true",
                        default=False, dest="copy_safe_samples_to_inbox",
                        help="copy safe sample events into the local inbox")
    parser.add_argument("--run-birth", action="store_true", default=False,
                        dest="run_birth", help="run Live Birth over the inbox")
    parser.add_argument("--run-membrane", action="store_true", default=False,
                        dest="run_membrane", help="run the Environmental Membrane")
    parser.add_argument("--run-integration", action="store_true", default=False,
                        dest="run_integration", help="run the membrane integration")
    parser.add_argument("--run-observation", action="store_true", default=False,
                        dest="run_observation", help="run Live Observation")
    # Tester console arguments (Prompt 76).
    parser.add_argument("--console-dir", type=str,
                        default=".solaris_ai_nn_tester/console",
                        dest="console_dir",
                        help="tester console output directory")
    parser.add_argument("--no-html", action="store_false", default=True,
                        dest="html", help="do not generate the static HTML page")
    # Tester feedback arguments (Prompt 77).
    parser.add_argument("--feedback-dir", type=str, default="",
                        dest="feedback_dir",
                        help="feedback directory (default: <tester>/feedback)")
    parser.add_argument("--ingest-path", type=str, default="",
                        dest="ingest_path",
                        help="local feedback JSON/Markdown file to ingest")
    parser.add_argument("--forms-only", action="store_true", default=False,
                        dest="forms_only", help="generate feedback forms only")
    parser.add_argument("--build-bundle", action="store_true", default=False,
                        dest="build_bundle", help="build the local feedback bundle")
    parser.add_argument("--no-privacy-redact", action="store_false",
                        default=True, dest="privacy_redact",
                        help="do not redact obvious secret markers (not advised)")
    # Tester packaging arguments (Prompt 78).
    parser.add_argument("--packaging-dir", type=str, default="",
                        dest="packaging_dir",
                        help="packaging dir (default: <tester>/packaging)")
    parser.add_argument("--include-dev-checks", action="store_true",
                        default=False, dest="include_dev_checks",
                        help="include dev-dependency (pytest) checks")
    # Tester safety freeze arguments (Prompt 79).
    parser.add_argument("--safety-freeze-dir", type=str, default="",
                        dest="safety_freeze_dir",
                        help="safety freeze dir (default: <tester>/safety_freeze)")


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
