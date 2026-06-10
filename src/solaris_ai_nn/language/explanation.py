"""ExplanationEngine -- grounded, deterministic explanations of runtime state.

Every explanation references concrete fields from an :class:`ExplanationContext`
(and lists them in ``grounded_in``). When the context lacks the data, the
engine says so explicitly (``does_not_know`` template + ``unknowns``) rather
than inventing anything. Motivational language is avoided: the system
"suggested" and "produced a tendency"; it did not "want".
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from . import templates as T
from .schemas import CausalTrace, Explanation, ExplanationContext, QueryResult


def _unknown(topic: str, missing: str) -> Explanation:
    return Explanation(topic=topic, text=T.render("does_not_know", missing=missing),
                       unknowns=[missing], confidence=0.0)


@dataclass
class ExplanationEngine:
    """Renders grounded explanations from context snapshots."""

    # -- core explainers --------------------------------------------------------

    def explain_last_event(self, context: ExplanationContext) -> Explanation:
        sig = context.last_signal
        if not sig:
            return _unknown("last_event", "the last signal")
        if sig.get("is_absence"):
            text = T.render("signal_absence")
        else:
            text = T.render("signal_received",
                            signal_type=sig.get("kind"), origin=sig.get("origin"),
                            intensity=sig.get("intensity"))
        return Explanation(topic="last_event", text=text,
                           grounded_in=[f"last_signal.{k}" for k in
                                        ("kind", "origin", "intensity")
                                        if k in sig])

    def explain_action_suggestion(self, context: ExplanationContext) -> Explanation:
        bridge = context.bridge
        if not bridge or bridge.get("last_suggested_action") is None:
            return _unknown("action_suggestion", "a previous action suggestion")
        text = T.render("action_suggested",
                        action=bridge["last_suggested_action"],
                        confidence=bridge.get("last_confidence"))
        grounded = ["bridge.last_suggested_action", "bridge.last_confidence"]
        explanation = Explanation(topic="action_suggestion", text=text,
                                  grounded_in=grounded)
        explanation.text += " " + T.render(
            "substrate_state",
            substrate_type=bridge.get("substrate_type"),
            state_size=bridge.get("substrate_config", {}).get("state_size"),
            state_norm=round(bridge.get("substrate_state_norm", 0.0), 4),
            activity_rate=round(bridge.get("substrate_activity_rate", 0.0), 4),
            drift=round(bridge.get("substrate_metrics", {}).get("drift", 0.0), 4))
        explanation.grounded_in.append("bridge.substrate_metrics")
        return explanation

    def explain_blocked_action(self, context: ExplanationContext) -> Explanation:
        result = context.last_result
        if not result:
            return _unknown("blocked_action", "a previous action result")
        if result.get("executed"):
            return Explanation(
                topic="blocked_action",
                text=f"The last action ({result.get('action')}) was not "
                     "blocked; it executed with consequence: "
                     f"{result.get('consequence', 'unknown')}.",
                grounded_in=["last_result.executed", "last_result.consequence"])
        text = T.render("action_blocked", action=result.get("action"),
                        reason=result.get("blocked_reason"))
        return Explanation(topic="blocked_action", text=text,
                           grounded_in=["last_result.blocked_reason"])

    def explain_action_result(self, context: ExplanationContext) -> Explanation:
        result = context.last_result
        if not result:
            return _unknown("action_result", "a previous action result")
        if not result.get("executed"):
            return self.explain_blocked_action(context)
        text = T.render("action_executed", action=result.get("action"),
                        consequence=result.get("consequence"))
        return Explanation(topic="action_result", text=text,
                           grounded_in=["last_result.action",
                                        "last_result.consequence"])

    def explain_reaction(self, context: ExplanationContext) -> Explanation:
        sig = context.last_signal or {}
        valence = sig.get("valence")
        if sig.get("kind") != "Reaction" or valence is None:
            telemetry = context.telemetry or {}
            if telemetry.get("readout_updates", 0) == 0:
                return _unknown("reaction", "a previous Reaction")
            return Explanation(
                topic="reaction",
                text=f"The readout has received {telemetry['readout_updates']} "
                     "feedback updates this session; the most recent signal "
                     "was not a Reaction.",
                grounded_in=["telemetry.readout_updates"])
        text = T.render("reaction_feedback", valence=valence)
        return Explanation(topic="reaction", text=text,
                           grounded_in=["last_signal.valence"])

    def explain_strongest_habit(self, context: ExplanationContext) -> Explanation:
        if not context.habits:
            return _unknown("strongest_habit", "any learned habit pathway")
        top = max(context.habits, key=lambda h: abs(h.get("weight", 0.0)))
        text = T.render("habit_strongest", pattern=top.get("pattern"),
                        action=top.get("action"),
                        weight=round(top.get("weight", 0.0), 4))
        return Explanation(topic="strongest_habit", text=text,
                           grounded_in=["habits[0].pattern", "habits[0].action",
                                        "habits[0].weight"])

    def explain_pruning(self, context: ExplanationContext) -> Explanation:
        pruning = context.pruning
        if not pruning or not pruning.get("passes"):
            return _unknown("pruning", "a previous synthesis pruning pass")
        text = T.render("synthesis_pruned", count=pruning.get("removed", 0),
                        reason=pruning.get("reason",
                                           "their weights fell below the "
                                           "subtraction threshold"))
        return Explanation(topic="pruning", text=text,
                           grounded_in=["pruning.removed", "pruning.passes"])

    def explain_plasticity(self, context: ExplanationContext) -> Explanation:
        pl = context.plasticity
        if not pl:
            return _unknown("plasticity", "plasticity engine state")
        last_applied = pl.get("last_applied")
        last_rejected = pl.get("last_rejected")
        if last_applied:
            target = last_applied.get("target", {})
            change = last_applied.get("change", {})
            text = T.render("plasticity_applied",
                            target=f"{target.get('component')}."
                                   f"{target.get('parameter')}",
                            old_value=change.get("old_value"),
                            new_value=change.get("new_value"),
                            reason=last_applied.get("reason"))
            return Explanation(topic="plasticity", text=text,
                               grounded_in=["plasticity.last_applied"])
        if last_rejected:
            target = last_rejected.get("target", {})
            text = T.render("plasticity_rejected",
                            target=f"{target.get('component')}."
                                   f"{target.get('parameter')}",
                            reason="; ".join(
                                (last_rejected.get("safety_result") or {})
                                .get("violations", ["safety violation"])))
            return Explanation(topic="plasticity", text=text,
                               grounded_in=["plasticity.last_rejected"])
        return Explanation(
            topic="plasticity",
            text=f"Plasticity is active but has applied "
                 f"{pl.get('applied_count', 0)} and rejected "
                 f"{pl.get('rejected_count', 0)} steps so far; none recently.",
            grounded_in=["plasticity.applied_count", "plasticity.rejected_count"])

    def explain_inner_map(self, context: ExplanationContext) -> Explanation:
        im = context.inner_map
        if not im:
            return _unknown("inner_map", "an Inner MAP snapshot")
        neural = im.get("neural", {}) or {}
        plasticity = im.get("plasticity", {}) or {}
        continuity = im.get("continuity", {}) or {}
        text = T.render("inner_map_state",
                        substrate_type=neural.get("substrate_type"),
                        state_norm=round(neural.get("reservoir_state_norm", 0.0), 4),
                        habit_pathways=plasticity.get("habit_pathways"),
                        pruning_count=plasticity.get("pruning_count"),
                        lifetime_steps=continuity.get("lifetime_steps"),
                        restarts=continuity.get("restart_count"))
        return Explanation(topic="inner_map", text=text,
                           grounded_in=["inner_map.neural",
                                        "inner_map.plasticity",
                                        "inner_map.continuity"])

    def explain_continuity(self, context: ExplanationContext) -> Explanation:
        continuity = context.continuity or (context.inner_map or {}).get("continuity")
        if not continuity:
            return _unknown("continuity", "continuity state")
        gap = continuity.get("brain_death_gap_seconds", 0.0) or 0.0
        restarts = continuity.get("restart_count", 0)
        if gap > 0.0 and not continuity.get("graceful_previous_shutdown", True):
            text = T.render("continuity_gap", seconds=round(gap, 3))
        elif restarts > 0:
            text = T.render("continuity_clean", restarts=restarts)
        else:
            text = ("This is the first recorded session for this state "
                    "directory; no restart has occurred.")
        return Explanation(topic="continuity", text=text,
                           grounded_in=["continuity.restart_count",
                                        "continuity.brain_death_gap_seconds"])

    def explain_substrate(self, context: ExplanationContext) -> Explanation:
        bridge = context.bridge
        if not bridge:
            return _unknown("substrate", "a bridge snapshot")
        metrics = bridge.get("substrate_metrics", {}) or {}
        text = T.render("substrate_state",
                        substrate_type=bridge.get("substrate_type"),
                        state_size=bridge.get("substrate_config", {}).get("state_size"),
                        state_norm=round(metrics.get("state_norm", 0.0), 4),
                        activity_rate=round(metrics.get("activity_rate", 0.0), 4),
                        drift=round(metrics.get("drift", 0.0), 4))
        return Explanation(topic="substrate", text=text,
                           grounded_in=["bridge.substrate_type",
                                        "bridge.substrate_metrics"])

    def explain_embodiment(self, context: ExplanationContext) -> Explanation:
        emb = context.embodiment
        if not emb:
            return _unknown("embodiment", "an embodiment snapshot "
                                          "(no simulated body is attached)")
        text = T.render("embodiment_state", position=emb.get("position"),
                        energy=round(float(emb.get("energy", 0.0)), 2),
                        exhausted=emb.get("exhausted"),
                        last_action=emb.get("last_action"),
                        last_result=emb.get("last_action_result"),
                        authority=emb.get("action_authority"))
        return Explanation(topic="embodiment", text=text,
                           grounded_in=["embodiment.position", "embodiment.energy",
                                        "embodiment.action_authority"])

    def explain_silence(self, context: ExplanationContext) -> Explanation:
        summary = context.trace_summary or {}
        absence = summary.get("absence_count")
        telemetry = context.telemetry or {}
        if absence is None:
            return _unknown("silence", "an absence-stimulus count")
        text = T.render("silence_summary", absence_count=absence,
                        reservoir_updates=telemetry.get("reservoir_updates"))
        return Explanation(topic="silence", text=text,
                           grounded_in=["trace_summary.absence_count",
                                        "telemetry.reservoir_updates"])

    def explain_causal_trace(self, trace: CausalTrace) -> Explanation:
        from .causal_trace import CausalTraceBuilder

        builder = CausalTraceBuilder(traces={trace.chain_id: trace})
        return builder.explain_chain(trace.chain_id)

    # -- queries ------------------------------------------------------------------

    def explain_query(self, query: str, context: ExplanationContext) -> QueryResult:
        from .query import QueryInterface  # local: avoid module cycle

        return QueryInterface(engine=self).answer(query, context)
