"""Language trace demo -- the system describes a bounded session about itself.

Runs a signal-only `ContinuousRunner` session (or an embodied sensorimotor one
with ``embodied=True``) with the language layer enabled, then renders the
grounded explanations and the JSON/Markdown session report. Every statement in
the output reduces to recorded runtime state -- no LLM, no invention, no
consciousness claims.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from ..runtime.continuous_runner import ContinuousRunner
from .soak_continuity import ACTIONS, WORLD, _make_providers


@dataclass
class LanguageTraceResult:
    """Outcome of the demo: explanations + report paths + previews."""

    steps: int
    meaning_atoms: int
    explanations: Dict[str, str] = field(default_factory=dict)
    report_json_path: Optional[str] = None
    report_md_path: Optional[str] = None
    report_preview: str = ""
    snapshot: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if k != "snapshot"}


def run_language_trace_demo(
    steps: int = 200,
    state_dir: str = ".solaris_ai_nn_state/language_demo",
    seed: int = 7,
    substrate: str = "esn",
    embodied: bool = False,
    enable_plasticity: bool = False,
    verbose: bool = False,
) -> LanguageTraceResult:
    """Run the bounded language-traced session and return its result."""
    if embodied:
        return _run_embodied(steps, state_dir, seed, substrate, verbose)

    stimulus_provider, reaction_provider = _make_providers()
    runner = ContinuousRunner(
        state_dir=state_dir, max_steps=steps, checkpoint_interval_steps=max(25, steps // 4),
        prune_interval_steps=max(50, steps // 3), seed=seed, action_labels=ACTIONS,
        vocabulary=list(WORLD.keys()) + ["I exist!"], substrate_name=substrate,
        stimulus_provider=stimulus_provider, reaction_provider=reaction_provider,
        silence_threshold=3, enable_language=True, report_interval_steps=50,
        enable_plasticity=enable_plasticity,
    )
    snapshot = runner.run()

    ctx = runner._language_context()
    engine = runner.bridge.explanation_engine
    explanations = {
        "last_event": engine.explain_last_event(ctx).text,
        "action_suggestion": engine.explain_action_suggestion(ctx).text,
        "strongest_habit": engine.explain_strongest_habit(ctx).text,
        "inner_map": engine.explain_inner_map(ctx).text,
        "continuity": engine.explain_continuity(ctx).text,
    }
    md_path = runner.pm.session_report_md_path
    preview = ""
    if md_path.exists():
        preview = "\n".join(md_path.read_text(encoding="utf-8").splitlines()[:18])

    result = LanguageTraceResult(
        steps=snapshot["session_steps"],
        meaning_atoms=snapshot["language"]["meaning_atoms"],
        explanations=explanations,
        report_json_path=str(runner.pm.session_report_json_path),
        report_md_path=str(md_path),
        report_preview=preview,
        snapshot=snapshot,
    )
    if verbose:
        _print(result, embodied=False)
    return result


def _run_embodied(steps: int, state_dir: str, seed: int, substrate: str,
                  verbose: bool) -> LanguageTraceResult:
    from ..embodiment.simulation_runner import SensorimotorSimulationRunner
    from ..language import serialization as LS
    from ..language.reporting import ExperimentReportBuilder
    from ..runtime.persistence import PersistenceManager

    runner = SensorimotorSimulationRunner(
        max_steps=steps, seed=seed, state_dir=state_dir, substrate=substrate,
        enable_language=True,
    )
    report = runner.run()
    pm = PersistenceManager(state_dir)
    session = (ExperimentReportBuilder(title="Solaris-AI-NN embodied language demo")
               .add_metadata(substrate=substrate, steps=steps, embodied=True)
               .add_section("runtime", {"steps": report["steps"]})
               .add_section("actions", report["action_counts"])
               .add_section("reactions", report["reactions"])
               .add_section("embodiment", report["embodiment"])
               .add_section("explanations", report["language"]["last_explanations"])
               .build())
    LS.save_report(session, pm.session_report_json_path, pm.session_report_md_path)
    LS.save_meaning_trace(runner.bridge.meaning_trace_builder.to_trace(),
                          pm.meaning_trace_path)

    result = LanguageTraceResult(
        steps=report["steps"],
        meaning_atoms=report["language"]["meaning_atoms"],
        explanations=dict(report["language"]["last_explanations"]),
        report_json_path=str(pm.session_report_json_path),
        report_md_path=str(pm.session_report_md_path),
        report_preview="\n".join(session.to_markdown().splitlines()[:18]),
        snapshot=report,
    )
    if verbose:
        _print(result, embodied=True)
    return result


def _print(result: LanguageTraceResult, embodied: bool) -> None:
    print("=" * 70)
    print(f"Solaris-AI-NN -- language trace demo "
          f"({result.steps} steps, embodied={embodied})")
    print("=" * 70)
    print(f"meaning atoms recorded: {result.meaning_atoms}")
    print("-" * 70)
    for name, text in result.explanations.items():
        print(f"[{name}]")
        print(f"  {text}")
    print("-" * 70)
    print(f"report (JSON): {result.report_json_path}")
    print(f"report (MD):   {result.report_md_path}")
    print("-" * 70)
    print("Markdown report preview:")
    print(result.report_preview)
    print("-" * 70)
    print("Every statement above is rendered from recorded state. No LLM was")
    print("used and no consciousness is claimed.")


def main() -> None:
    run_language_trace_demo(verbose=True)


if __name__ == "__main__":
    main()
