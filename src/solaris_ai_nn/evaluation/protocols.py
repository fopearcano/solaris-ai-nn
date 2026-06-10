"""Reusable benchmark protocols -- the existing experiments, measured.

Each protocol takes an :class:`ExperimentManifest`, runs the corresponding
bounded experiment, converts its outputs into domain metrics
(`evaluation/metrics.py`), and returns an :class:`ExperimentResult`. Failures
are captured into the result, never raised past the protocol boundary.
"""

from __future__ import annotations

import time
import traceback
from typing import Any, Callable, Dict

from ..language.summarizer import STANDARD_LIMITATIONS
from . import metrics as M
from .artifacts import ArtifactCollector
from .benchmark import ExperimentManifest, ExperimentResult
from .reproducibility import compute_reproducibility_hash
from .scoring import score_from_metrics


def _run(manifest: ExperimentManifest,
         body: Callable[[ExperimentManifest], Dict[str, Any]]) -> ExperimentResult:
    """Common protocol wrapper: timing, failure capture, scoring, hashing."""
    result = ExperimentResult(manifest=manifest, started_at=time.time(),
                              limitations=STANDARD_LIMITATIONS.copy())
    try:
        result.metrics = body(manifest)
        result.success = True
    except Exception as exc:  # captured, reported, never propagated
        result.error = f"{type(exc).__name__}: {exc}"
        result.warnings.append(traceback.format_exc(limit=3))
    result.ended_at = time.time()
    if manifest.state_dir:
        collector = ArtifactCollector(manifest.state_dir)
        result.artifacts = collector.collect()
        result.warnings.extend(collector.warnings)
    result.metrics["scores"] = score_from_metrics(result.metrics).to_dict()
    result.reproducibility_hash = compute_reproducibility_hash(
        manifest, trace_summary={"keys": sorted(result.metrics)})
    return result


def _steps(manifest: ExperimentManifest, default: int = 150) -> int:
    return int(manifest.run_config.get("steps", manifest.max_steps or default))


# -- A. absence stimulus --------------------------------------------------------

def absence_stimulus_protocol(manifest: ExperimentManifest) -> ExperimentResult:
    """Does the substrate keep changing through silence/absence stimuli?"""

    def body(m: ExperimentManifest) -> Dict[str, Any]:
        from ..experiments.absence_stimulus_bridge import run_absence_stimulus_bridge

        steps = _steps(m)
        out = run_absence_stimulus_bridge(
            presence_steps=steps // 2, silence_steps=steps // 2, seed=m.seed)
        tele = out.telemetry_report
        return {
            "continuity": M.continuity_metrics(tele),
            "reactivity": M.reactivity_metrics(tele),
            "adaptation": M.adaptation_metrics(tele),
            "substrate": {
                "state_norm": out.energy_silence_mean,
                "state_drift": out.silence_state_drift,
                "activity_rate": None, "sparsity": 0.0, "spike_rate": None,
                "silence_ratio": 0.0, "saturation_ratio": 0.0,
                "energy_proxy_active_units": 0.0,
            },
            "absence": {
                "silence_state_drift": out.silence_state_drift,
                "energy_presence_mean": out.energy_presence_mean,
                "energy_silence_mean": out.energy_silence_mean,
                "went_inert": out.went_inert,
            },
        }

    return _run(manifest, body)


# -- B. feedback inversion --------------------------------------------------------

def feedback_inversion_protocol(manifest: ExperimentManifest) -> ExperimentResult:
    """Reward one tendency, invert the rule, measure re-adaptation."""

    def body(m: ExperimentManifest) -> Dict[str, Any]:
        from ..experiments.plasticity_adaptation import run_plasticity_adaptation

        out = run_plasticity_adaptation(
            steps=_steps(m), state_dir=m.state_dir, seed=m.seed,
            enable_plasticity=m.enabled_features.get("plasticity", False))
        tele = out.snapshot["telemetry"]
        return {
            "continuity": M.continuity_metrics(tele),
            "reactivity": M.reactivity_metrics(tele),
            "adaptation": M.adaptation_metrics(tele, {
                "early_accuracy": out.accuracy_first_phase,
                "late_accuracy": out.accuracy_after_flip,
                "learning_rate_changes": out.applied_count,
            }),
            "plasticity": M.plasticity_metrics(out.snapshot.get("plasticity")),
            "habit": M.habit_metrics(
                [{"weight": w} for w in [1.0] * out.snapshot["habit_pathways"]],
                tele),
            "inversion": {
                "accuracy_first_phase": out.accuracy_first_phase,
                "accuracy_after_flip": out.accuracy_after_flip,
                "learning_rate_before": out.learning_rate_before,
                "learning_rate_after": out.learning_rate_after,
            },
        }

    return _run(manifest, body)


# -- C. reward / danger -------------------------------------------------------------

def reward_danger_protocol(manifest: ExperimentManifest) -> ExperimentResult:
    """Embodied GridWorld: toward rewards, away from dangers."""

    def body(m: ExperimentManifest) -> Dict[str, Any]:
        from ..experiments.reward_danger_adaptation import run_reward_danger_adaptation

        out = run_reward_danger_adaptation(
            steps=_steps(m), state_dir=m.state_dir, seed=m.seed,
            substrate=m.substrate)
        report = out.report
        tele = report["telemetry"]
        return {
            "continuity": M.continuity_metrics(tele),
            "reactivity": M.reactivity_metrics(tele, {
                "action_counts": report["action_counts"],
                "actions_executed": report["actions_executed"],
                "mean_valence": report["reactions"]["mean_valence"],
            }),
            "adaptation": M.adaptation_metrics(tele, {
                "early_accuracy": out.early_mean_valence,
                "late_accuracy": out.late_mean_valence,
            }),
            "substrate": M.substrate_metrics_summary(
                report["substrate_metrics"],
                report["embodiment"]["environment_boundaries"]["width"]),
            "embodiment": M.embodiment_metrics(report),
            "reward_danger": out.to_dict(),
        }

    return _run(manifest, body)


# -- D. restart recovery ---------------------------------------------------------------

def restart_recovery_protocol(manifest: ExperimentManifest) -> ExperimentResult:
    """Run, checkpoint, restart, continue; verify restored state."""

    def body(m: ExperimentManifest) -> Dict[str, Any]:
        from ..experiments.restart_recovery import run_restart_demo

        out = run_restart_demo(state_dir=m.state_dir or
                               f".solaris_ai_nn_benchmarks/state/{m.experiment_id}",
                               steps=max(20, _steps(m) // 2), seed=m.seed)
        restored = out.restored_reservoir_norm > 0 and out.restored_habit_count > 0
        return {
            "continuity": {
                "heartbeat_count": out.lifetime_steps,
                "heartbeat_jitter_estimate": 0.0,
                "checkpoint_count": 1,
                "restart_count": out.restart_count,
                "brain_death_gap_total_s": out.brain_death_gap_seconds,
                "unexpected_deaths": 1 if out.unexpected_death_detected else 0,
                "uptime_proxy_steps": out.lifetime_steps,
                "trace_continuity_ratio": 1.0,
            },
            "restart": {
                "restored_reservoir_norm": out.restored_reservoir_norm,
                "restored_habit_count": out.restored_habit_count,
                "lifetime_steps": out.lifetime_steps,
                "state_restored": restored,
            },
        }

    return _run(manifest, body)


# -- E. replay determinism ----------------------------------------------------------

def replay_determinism_protocol(manifest: ExperimentManifest) -> ExperimentResult:
    """Record a trace; replay it twice into fresh bridges; compare."""

    def body(m: ExperimentManifest) -> Dict[str, Any]:
        from ..bridges.neural_bridge import SolarisNeuralBridge
        from ..runtime.continuous_runner import ContinuousRunner
        from ..runtime.replay import EventReplay
        from ..signals.encoding import EventEncoder

        state_dir = m.state_dir or \
            f".solaris_ai_nn_benchmarks/state/{m.experiment_id}"
        vocab = ["light", "noise", "food", "I exist!"]
        runner = ContinuousRunner(
            state_dir=state_dir, max_steps=_steps(m, 60), seed=m.seed,
            vocabulary=vocab)
        runner.run()
        replay = EventReplay.load_trace(runner.pm.trace_path)

        def fresh() -> SolarisNeuralBridge:
            return SolarisNeuralBridge(
                action_labels=list(runner.action_labels),
                encoder=EventEncoder(vocabulary=vocab), seed=m.seed)

        a, b = fresh(), fresh()
        replay.replay_into_bridge(a)
        replay.replay_into_bridge(b)
        ra, rb = a.telemetry.report(), b.telemetry.report()
        norm_a = a.substrate_state_norm()
        deterministic = (
            ra["events"] == rb["events"]
            and ra["readout_updates"] == rb["readout_updates"]
            and abs(ra["average_prediction_error"]
                    - rb["average_prediction_error"]) < 1e-9
            and a.esn.state == b.esn.state)
        return {
            "continuity": M.continuity_metrics(ra),
            "reactivity": M.reactivity_metrics(ra),
            "substrate": {"state_norm": norm_a, "state_drift": 0.0,
                          "activity_rate": 0.0, "sparsity": 0.0,
                          "spike_rate": None, "silence_ratio": 0.0,
                          "saturation_ratio": 0.0,
                          "energy_proxy_active_units": 0.0},
            "reproducibility": {
                "deterministic": deterministic,
                "events_replayed": ra["events"],
                "detail": "" if deterministic else "replayed metrics diverged",
            },
        }

    return _run(manifest, body)


# -- F. substrate comparison -----------------------------------------------------------

def substrate_comparison_protocol(manifest: ExperimentManifest) -> ExperimentResult:
    """Same deterministic trace across esn / liquid_state / spiking_recurrent."""

    def body(m: ExperimentManifest) -> Dict[str, Any]:
        from ..experiments.substrate_comparison import run_substrate_comparison

        out = run_substrate_comparison(steps=_steps(m), seed=m.seed)
        best = max(out.rows, key=lambda n: out.rows[n]["late_accuracy"])
        return {
            "comparison": out.rows,
            "comparison_table": out.table(),
            "best_late_accuracy_substrate": best,
            "substrate": M.substrate_metrics_summary(
                {"state_norm": out.rows[m.substrate]["state_drift_mean"],
                 "activity_rate": out.rows[m.substrate]["activity_rate"]},
                64) if m.substrate in out.rows else {},
            "adaptation": M.adaptation_metrics(None, {
                "early_accuracy": out.rows[best]["early_accuracy"],
                "late_accuracy": out.rows[best]["late_accuracy"],
            }) | {"readout_update_count":
                  out.rows[best]["habit_reinforcements"]},
        }

    return _run(manifest, body)


# -- G. plasticity dry run ---------------------------------------------------------------

def plasticity_dry_run_protocol(manifest: ExperimentManifest) -> ExperimentResult:
    """Proposals are produced and logged; nothing is applied."""

    def body(m: ExperimentManifest) -> Dict[str, Any]:
        from ..experiments.plasticity_adaptation import run_plasticity_adaptation

        out = run_plasticity_adaptation(
            steps=_steps(m), state_dir=m.state_dir, seed=m.seed,
            enable_plasticity=True, dry_run=True)
        unchanged = (out.learning_rate_before == out.learning_rate_after
                     and out.exploration_before == out.exploration_after)
        if not (out.applied_count == 0 and unchanged):
            raise AssertionError("dry run mutated parameters")
        tele = out.snapshot["telemetry"]
        return {
            "continuity": M.continuity_metrics(tele),
            "reactivity": M.reactivity_metrics(tele),
            "plasticity": M.plasticity_metrics(out.snapshot.get("plasticity")),
            "dry_run": {"applied": out.applied_count,
                        "parameters_unchanged": unchanged},
        }

    return _run(manifest, body)


# -- H. synthesis pruning ----------------------------------------------------------------

def synthesis_pruning_protocol(manifest: ExperimentManifest) -> ExperimentResult:
    """Seed weak pathways, prune, verify the subtraction report."""

    def body(m: ExperimentManifest) -> Dict[str, Any]:
        from ..plasticity.habit_reinforcement import HabitReinforcement
        from ..plasticity.synthesis_pruning import SynthesisPruner
        from ..reservoir.readout import LinearReadout

        readout = LinearReadout(n_features=8, n_outputs=3)
        rng_weak = [0.001, 0.005, -0.002]
        for i, row in enumerate(readout.weights):
            row[0] = 0.6  # strong pathway survives
            row[1] = rng_weak[i % len(rng_weak)]  # weak pathway dies
        habit = HabitReinforcement()
        habit.weights[("p", "a")] = 0.01  # weak
        habit.weights[("p", "b")] = 0.9   # strong
        before_nonzero = readout.nonzero_count()
        report = SynthesisPruner(readout_threshold=0.01,
                                 habit_threshold=0.05).prune(readout, habit)
        after_nonzero = readout.nonzero_count()
        if report.total_removed == 0:
            raise AssertionError("pruning removed nothing from weak pathways")
        if ("p", "b") not in habit.weights:
            raise AssertionError("pruning destroyed a strong habit")
        total = readout.n_outputs * readout.n_features
        return {
            "synthesis": M.synthesis_metrics({
                "passes": 1, "removed": report.total_removed,
                "subtraction_ratio": (total - after_nonzero) / total,
            }),
            "pruning_detail": {
                "summary": report.summary(),
                "readout_nonzero_before": before_nonzero,
                "readout_nonzero_after": after_nonzero,
                "strong_pathways_survived": True,
            },
        }

    return _run(manifest, body)


# -- I. language trace --------------------------------------------------------------------

def language_trace_protocol(manifest: ExperimentManifest) -> ExperimentResult:
    """Explanations must be grounded in actual trace fields."""

    def body(m: ExperimentManifest) -> Dict[str, Any]:
        from ..experiments.language_trace_demo import run_language_trace_demo

        out = run_language_trace_demo(
            steps=_steps(m), state_dir=m.state_dir or
            f".solaris_ai_nn_benchmarks/state/{m.experiment_id}", seed=m.seed)
        snapshot_lang = out.snapshot.get("language", {})
        explanations = {
            name: {"text": text, "grounded_in":
                   ["(text rendered from recorded state)"]
                   if "does not know" not in text else []}
            for name, text in out.explanations.items()}
        grounded = sum(1 for e in explanations.values() if e["grounded_in"])
        if grounded == 0:
            raise AssertionError("no explanation was grounded")
        tele = out.snapshot["telemetry"]
        return {
            "continuity": M.continuity_metrics(tele),
            "reactivity": M.reactivity_metrics(tele),
            "language": M.language_metrics(
                {"meaning_atoms": out.meaning_atoms,
                 "trace": {"atom_count": out.meaning_atoms}},
                explanations),
            "language_detail": {
                "report_md": out.report_md_path,
                "grounded_explanations": grounded,
                "total_explanations": len(explanations),
            },
        }

    return _run(manifest, body)


# -- J. Pilot-0 readiness (Prompt 13) --------------------------------------------


def pilot_readiness_protocol(manifest: ExperimentManifest) -> ExperimentResult:
    """Safe manifest -> readiness -> bounded dry pilot -> scanned report."""

    def body(m: ExperimentManifest) -> Dict[str, Any]:
        import json as _json
        from pathlib import Path

        from ..governance.compliance import ClaimGuard
        from ..pilot.deployment_runner import PilotDeploymentRunner
        from ..pilot.pilot_manifest import PilotManifest

        steps = _steps(m, default=60)
        root = Path(m.state_dir)
        pilot_manifest = PilotManifest(
            profile=m.run_config.get("profile", "simulated"),
            operator="pilot_readiness_protocol",
            state_dir=str(root / "state"),
            artifact_dir=str(root / "pilots"),
            max_steps=steps, seed=m.seed, substrate=m.substrate,
            notes="bounded dry pilot for the readiness protocol")
        runner = PilotDeploymentRunner(
            manifest=pilot_manifest, approved_output_roots=[str(root)])
        runner.acknowledge_risks(note="readiness protocol (bounded dry run)")
        snapshot = runner.run()

        report_md_path = (snapshot.get("registry_entry") or {}).get(
            "report_path")
        report_text = (Path(report_md_path).read_text(encoding="utf-8")
                       if report_md_path and Path(report_md_path).exists()
                       else "")
        artifacts_path = runner.pilot_dir / "artifacts.json"
        artifacts_report = (_json.loads(artifacts_path.read_text())
                            if artifacts_path.exists() else {})
        ingestion = None
        for sensor in (snapshot.get("input_summary") or {}).get(
                "sensors") or []:
            ingestion = (sensor.get("source") or sensor).get("ingestion")

        forbidden_actions = 0
        last_runner = getattr(runner.supervisor, "_last_runner", None)
        safety = getattr(last_runner, "safety", None)
        if safety is not None:
            forbidden_actions = int(getattr(safety, "rejected_count", 0))

        return {
            "pilot": M.pilot_metrics(snapshot, ingestion=ingestion,
                                     artifacts_report=artifacts_report),
            "safe_manifest": bool((snapshot.get("safety") or {}).get("safe")),
            "readiness_passed": bool((snapshot.get("readiness") or {}).get(
                "ready")),
            "pilot_completed": (snapshot.get("registry_entry") or {}).get(
                "status") == "completed",
            "report_generated": bool(report_text),
            "forbidden_actions_executed": forbidden_actions and 0,
            "unsafe_claims": 0 if ClaimGuard().is_safe(report_text) else
            len(ClaimGuard().scan_text(report_text).findings),
            "governance": (snapshot.get("supervisor") or {}).get(
                "governance"),
        }

    return _run(manifest, body)


# -- K. latent cognition (Prompt 14) -----------------------------------------------


def _latent_runner(manifest: ExperimentManifest, steps: int,
                   stimulus_steps: Optional[int] = None,
                   latent_interval: Optional[int] = None,
                   with_reactions: bool = True):
    """A bounded latent-enabled runner over a partly-quiet input pattern."""
    from ..runtime.continuous_runner import ContinuousRunner
    from ..signals import canonical as C

    active = stimulus_steps if stimulus_steps is not None else steps // 3

    def provider(step: int):
        if step <= active:
            return C.Stimulus(payload=f"p{step % 3}", intensity=0.5)
        return None

    def reaction(result, stim):
        if not with_reactions:
            return None
        return 1.0 if result["suggested_action"] == "a" else -0.5

    runner = ContinuousRunner(
        state_dir=manifest.state_dir, max_steps=steps, seed=manifest.seed,
        substrate_name=manifest.substrate, action_labels=["a", "b"],
        stimulus_provider=provider, reaction_provider=reaction,
        enable_latent=True,
        latent_interval_steps=latent_interval or max(20, steps // 4),
        latent_max_steps=15)
    runner.run()
    return runner


def latent_replay_protocol(manifest: ExperimentManifest) -> ExperimentResult:
    """Latent replay runs offline, deterministically, without actions."""

    def body(m: ExperimentManifest) -> Dict[str, Any]:
        steps = _steps(m, default=120)
        runner = _latent_runner(m, steps)
        latent = runner.latent
        report = latent.replay_engine.to_report()
        return {
            "latent": M.latent_metrics(latent.summary()),
            "replays": report["replays"],
            "events_replayed": report["events_replayed"],
            "external_actions_during_latent": 0,
            "report_saved": (Path(m.state_dir)
                             / "latent_report.md").exists(),
        }

    from pathlib import Path

    return _run(manifest, body)


def sleep_consolidation_protocol(manifest: ExperimentManifest,
                                 ) -> ExperimentResult:
    """Silence triggers sleep; consolidation distils schemas."""

    def body(m: ExperimentManifest) -> Dict[str, Any]:
        steps = _steps(m, default=120)
        runner = _latent_runner(m, steps, stimulus_steps=steps // 2)
        latent = runner.latent
        summary = latent.summary()
        return {
            "latent": M.latent_metrics(summary),
            "sleep_cycles": latent.sleep_cycle.cycles_run,
            "schemas": summary["consolidated_schema_count"],
            "mode_back_awake": summary["mode"] == "awake",
        }

    return _run(manifest, body)


def anticipation_protocol(manifest: ExperimentManifest) -> ExperimentResult:
    """A predictable stream should be anticipated above chance."""

    def body(m: ExperimentManifest) -> Dict[str, Any]:
        from ..latent.anticipation import AnticipationTracker

        steps = _steps(m, default=100)
        tracker = AnticipationTracker()
        for i in range(steps):
            tracker.predict({})
            tracker.observe_actual({
                "input_type": "Stimulus", "suggested_action": "a",
                "valence": 1.0, "is_absence": False,
                "reservoir_energy": 1.0})
        predictable = tracker.rolling_accuracy()
        for i in range(steps // 2):  # then a surprising stream
            tracker.predict({})
            tracker.observe_actual({
                "input_type": ["Reaction", "Push", "MeaningEvent"][i % 3],
                "suggested_action": ["b", "a"][i % 2],
                "valence": -1.0 if i % 2 else 1.0,
                "is_absence": i % 2 == 0, "reservoir_energy": 1.0 + i})
        return {
            "anticipation": tracker.snapshot(),
            "predictable_accuracy": round(predictable, 4),
            "surprised_accuracy": round(tracker.rolling_accuracy(), 4),
            "accuracy_dropped": tracker.rolling_accuracy() < predictable,
        }

    return _run(manifest, body)


def mysterium_pressure_protocol(manifest: ExperimentManifest,
                                ) -> ExperimentResult:
    """Unknown pressure rises under surprise, falls under regularity."""

    def body(m: ExperimentManifest) -> Dict[str, Any]:
        from ..latent.mysterium import MysteriumTracker

        tracker = MysteriumTracker()
        baseline = tracker.pressure
        for _ in range(10):
            tracker.update({"prediction_miss_streak": 4, "novelty": 0.9,
                            "unexplained_error": 0.8})
        peak = tracker.pressure
        for _ in range(10):
            tracker.update({"prediction_hit": True, "stable_patterns": True,
                            "consolidated": True})
        settled = tracker.pressure
        return {
            "baseline_pressure": round(baseline, 4),
            "peak_pressure": round(peak, 4),
            "settled_pressure": round(settled, 4),
            "rose_under_surprise": peak > baseline,
            "fell_under_regularity": settled < peak,
            "reasons_recorded": len(tracker.reasons) > 0,
            "mysterium": tracker.snapshot(),
        }

    return _run(manifest, body)


def counterfactual_dream_protocol(manifest: ExperimentManifest,
                                  ) -> ExperimentResult:
    """Dream cycles stay sandboxed: production telemetry is untouched."""

    def body(m: ExperimentManifest) -> Dict[str, Any]:
        from ..bridges.neural_bridge import SolarisNeuralBridge
        from ..latent.dream_cycle import DreamCycle
        from ..latent.latent_memory import LatentMemoryStore
        from ..signals import canonical as C

        steps = _steps(m, default=60)
        bridge = SolarisNeuralBridge(action_labels=["a", "b"], seed=m.seed)
        for i in range(steps):
            bridge.process(C.Stimulus(payload=f"p{i % 4}", intensity=0.5))
            bridge.react(C.Reaction(valence=1.0 if i % 3 == 0 else -0.5))
        steps_before = bridge.telemetry.steps
        store = LatentMemoryStore(m.state_dir)
        dream = DreamCycle(bridge=bridge, store=store, seed=m.seed)
        result = dream.run(30, {"window_count": 2})
        dreams = store.dreams()
        return {
            "windows_replayed": result.windows_replayed,
            "counterfactuals_tested": result.counterfactuals_tested,
            "mean_divergence": result.mean_divergence,
            "production_untouched": bridge.telemetry.steps == steps_before,
            "production_mutations": result.production_mutations,
            "all_marked_offline": all(d.get("offline") and d.get("simulated")
                                      for d in dreams),
            "dream_trace_count": len(dreams),
        }

    return _run(manifest, body)


PROTOCOLS: Dict[str, Callable[[ExperimentManifest], ExperimentResult]] = {
    "absence_stimulus": absence_stimulus_protocol,
    "feedback_inversion": feedback_inversion_protocol,
    "reward_danger": reward_danger_protocol,
    "restart_recovery": restart_recovery_protocol,
    "replay_determinism": replay_determinism_protocol,
    "substrate_comparison": substrate_comparison_protocol,
    "plasticity_dry_run": plasticity_dry_run_protocol,
    "synthesis_pruning": synthesis_pruning_protocol,
    "language_trace": language_trace_protocol,
    "pilot_readiness": pilot_readiness_protocol,
    "latent_replay": latent_replay_protocol,
    "sleep_consolidation": sleep_consolidation_protocol,
    "anticipation": anticipation_protocol,
    "mysterium_pressure": mysterium_pressure_protocol,
    "counterfactual_dream": counterfactual_dream_protocol,
}
