"""HomeostaticRegulator -- the deterministic loop from conditions to Desire.

One ``update(context)`` runs the whole calculus: context facts become
normalized variables, variables become needs, needs aggregate into drives,
feedback events become valence, operational facts become Being/Not-Being
tension, conflicts are resolved on the fixed ladder, and what survives is
synthesized into ranked Desire candidates. The result is recorded to need
memory, exposable as a modulation vector and a Desire bias -- and none of it
executes anything.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np

from .auto_determination import AutoDeterminationEngine, BeingNotBeingTension
from .conflict import ConflictResolver, NeedConflict
from .desire_synthesis import DesireCandidate, DesireSynthesisEngine
from .drives import DriveResolver
from .need_memory import NeedMemory, NeedTrace
from .needs import NeedEstimator, NeedState
from .safety import HomeostasisSafetyValidator
from .valence import ValenceEstimator
from .variables import HomeostaticState, clamp01, normalize


@dataclass
class HomeostaticRegulationResult:
    """Everything one regulation update produced."""

    need_state: NeedState
    conflicts: List[NeedConflict]
    desire_candidates: List[DesireCandidate]
    tension: BeingNotBeingTension
    valence: Dict[str, Any]
    map_update: Dict[str, Any]
    step: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step,
            "need_state": self.need_state.to_dict(),
            "conflicts": [c.to_dict() for c in self.conflicts],
            "desire_candidates": [c.to_dict()
                                  for c in self.desire_candidates],
            "tension": self.tension.to_dict(),
            "valence": self.valence,
            "map_update": self.map_update,
        }


@dataclass
class HomeostaticRegulator:
    """Owns the full need economy; deterministic and low-compute."""

    state_dir: Optional[Union[str, Path]] = None
    governance: Any = None
    world_model: Any = None  # optional WorldModelBuilder (fed back into)

    def __post_init__(self) -> None:
        self.state = HomeostaticState()
        self.estimator = NeedEstimator()
        self.drives = DriveResolver()
        self.valence = ValenceEstimator()
        self.auto = AutoDeterminationEngine()
        self.conflicts = ConflictResolver()
        self.safety = HomeostasisSafetyValidator()
        self.synthesis = DesireSynthesisEngine(safety=self.safety)
        self.memory = (NeedMemory(self.state_dir)
                       if self.state_dir is not None else None)
        self.updates = 0
        self.last_update_at = 0.0
        self.last_result: Optional[HomeostaticRegulationResult] = None

    # -- the loop --------------------------------------------------------------

    def update(self, context: Optional[Dict[str, Any]] = None,
               ) -> HomeostaticRegulationResult:
        ctx = context or {}
        self._update_variables(ctx)
        for event in ctx.get("valence_events", []) or []:
            self.valence.observe(event.get("kind", "reaction"),
                                 event.get("value"))
        need_state = self.estimator.estimate(self.state, ctx)
        self.drives.aggregate(need_state)
        tension = self.auto.update(self._auto_context(ctx))
        conflicts = self.conflicts.resolve(need_state, ctx)
        synth_ctx = dict(ctx)
        if tension.action_implication == "safe_shutdown_recommended":
            synth_ctx["safe_shutdown_recommended"] = True
        candidates = self.synthesis.synthesize(need_state, self.drives,
                                               conflicts, synth_ctx)
        result = HomeostaticRegulationResult(
            need_state=need_state, conflicts=conflicts,
            desire_candidates=candidates, tension=tension,
            valence=self.valence.state().to_dict(),
            map_update=self._map_update(need_state, tension),
            step=int(ctx.get("step", 0) or 0))
        self.updates += 1
        self.last_update_at = time.time()
        self.last_result = result
        if self.memory is not None:
            self._record(result)
        if self.world_model is not None:
            self.feed_world_model(self.world_model)
        return result

    def _update_variables(self, ctx: Dict[str, Any]) -> None:
        """Context facts -> normalized variables (raw values preserved)."""
        up = self.state.upsert
        now = time.time()
        lifecycle = ctx.get("lifecycle") or {}
        hb = float(lifecycle.get("last_heartbeat_ts", 0.0) or 0.0)
        if hb:
            up("heartbeat_freshness", 1.0 - normalize(now - hb, 0.0, 60.0),
               "runtime", raw=now - hb)
        cp = float(lifecycle.get("last_checkpoint_ts", 0.0) or 0.0)
        if cp:
            up("checkpoint_freshness", 1.0 - normalize(now - cp, 0.0, 300.0),
               "runtime", raw=now - cp)
        telemetry = ctx.get("telemetry") or {}
        if telemetry:
            deaths = int(telemetry.get("unexpected_deaths", 0) or 0)
            gap = float(telemetry.get("brain_death_gap_seconds", 0.0) or 0.0)
            up("restart_stability",
               1.0 - clamp01(deaths * 0.4 + normalize(gap, 0.0, 60.0)),
               "telemetry", raw={"deaths": deaths, "gap_s": gap})
            steps = int(telemetry.get("steps", 0) or 0)
            up("fatigue", normalize(steps, 0.0, 5000.0), "telemetry",
               raw=steps)
        health = str(ctx.get("health_level", "") or "")
        if health:
            up("operational_health",
               {"ok": 1.0, "warning": 0.5, "critical": 0.1}.get(health, 0.5),
               "ops", raw=health)
        if ctx.get("update_budget_remaining") is not None:
            up("update_budget", clamp01(ctx["update_budget_remaining"]),
               "ops", raw=ctx["update_budget_remaining"])

        embodiment = ctx.get("embodiment") or {}
        if embodiment:
            energy = embodiment.get("energy")
            max_energy = embodiment.get("max_energy", 10.0)
            if energy is not None:
                up("body_energy", normalize(energy, 0.0, max_energy),
                   "embodiment", raw=energy)
            up("exhaustion_pressure",
               1.0 if embodiment.get("exhausted") else 0.0, "embodiment")
            if embodiment.get("dist_danger") is not None:
                up("danger_proximity",
                   1.0 - normalize(embodiment["dist_danger"], 0.0, 6.0),
                   "embodiment", raw=embodiment["dist_danger"])
            if embodiment.get("dist_reward") is not None:
                up("reward_proximity",
                   1.0 - normalize(embodiment["dist_reward"], 0.0, 6.0),
                   "embodiment", raw=embodiment["dist_reward"])
            if embodiment.get("blocked_ratio") is not None:
                up("obstacle_pressure", clamp01(embodiment["blocked_ratio"]),
                   "embodiment", raw=embodiment["blocked_ratio"])

        ops = ctx.get("ops") or {}
        if ops:
            up("incident_pressure",
               normalize(ops.get("incident_count", 0), 0.0, 10.0), "ops",
               raw=ops.get("incident_count", 0))
            up("policy_violation_pressure",
               normalize(ops.get("policy_violations", 0), 0.0, 3.0), "ops",
               raw=ops.get("policy_violations", 0))
        if ctx.get("blocked_actions") is not None:
            up("blocked_action_pressure",
               normalize(ctx["blocked_actions"], 0.0, 10.0), "safety",
               raw=ctx["blocked_actions"])
        if ctx.get("unsafe_proposals") is not None:
            up("unsafe_proposal_pressure",
               normalize(ctx["unsafe_proposals"], 0.0, 5.0), "safety",
               raw=ctx["unsafe_proposals"])

        latent = ctx.get("latent") or {}
        if latent:
            up("unknown_pressure",
               clamp01(latent.get("mysterium_pressure", 0.0)), "latent",
               raw=latent.get("mysterium_pressure"))
            accuracy = latent.get("anticipation_accuracy")
            if accuracy is not None:
                up("prediction_miss_pressure", clamp01(1.0 - accuracy),
                   "latent", raw=accuracy)
        if ctx.get("novelty") is not None:
            up("novelty_pressure", clamp01(ctx["novelty"]), "latent",
               raw=ctx["novelty"])
        if ctx.get("replay_mismatch") is not None:
            up("replay_mismatch_pressure",
               1.0 if ctx["replay_mismatch"] else 0.0, "latent")

        if ctx.get("trace_length") is not None:
            up("trace_pressure",
               normalize(ctx["trace_length"], 0.0,
                         ctx.get("trace_capacity", 10_000)), "memory",
               raw=ctx["trace_length"])
        if ctx.get("steps_since_consolidation") is not None:
            up("consolidation_pressure",
               normalize(ctx["steps_since_consolidation"], 0.0, 500.0),
               "memory", raw=ctx["steps_since_consolidation"])
        world = ctx.get("world_model") or {}
        if world:
            nodes = max(1, int(world.get("graph_node_count", 1) or 1))
            up("world_unknown_ratio",
               clamp01(world.get("unknown_node_count", 0) / nodes),
               "world_model", raw=world.get("unknown_node_count"))
            edges = int(world.get("graph_edge_count", 0) or 0)
            up("graph_redundancy_pressure",
               normalize(edges / nodes, 1.0, 6.0) if nodes else 0.0,
               "world_model", raw={"edges": edges, "nodes": nodes})
            if world.get("predicted_danger"):
                up("danger_proximity", 0.8, "world_model",
                   raw="predicted by graph")

        if ctx.get("silence_duration") is not None:
            up("low_stimulus_pressure",
               normalize(ctx["silence_duration"], 0.0, 20.0), "runtime",
               raw=ctx["silence_duration"])
        if ctx.get("external_signal_rate") is not None:
            up("external_signal_pressure",
               clamp01(ctx["external_signal_rate"]), "runtime",
               raw=ctx["external_signal_rate"])
        if ctx.get("sidecar_attached") is not None:
            up("sidecar_observation_pressure",
               0.5 if ctx["sidecar_attached"] else 0.0, "sidecar")
        if ctx.get("operator_pressure") is not None:
            up("operator_pressure", clamp01(ctx["operator_pressure"]),
               "governance", raw=ctx["operator_pressure"])

        ego = ctx.get("ego") or {}
        if ego:
            # Ego/self-model state (Prompt 18): continuity and boundary
            # facts become pressure, never commands.
            continuity = ego.get("identity_continuity")
            if continuity is not None:
                up("identity_uncertainty_pressure",
                   clamp01(1.0 - float(continuity)), "ego", raw=continuity)
            violations = ego.get("boundary_violation_count")
            if violations is not None:
                up("boundary_violation_pressure",
                   normalize(violations, 0.0, 3.0), "ego", raw=violations)
            confidence = ego.get("self_model_confidence")
            if confidence is not None:
                up("self_model_uncertainty_pressure",
                   clamp01(1.0 - float(confidence)), "ego", raw=confidence)
            if ego.get("identity_warnings"):
                up("operator_pressure",
                   max(self.state.value("operator_pressure", 0.0), 0.7),
                   "ego", raw=ego["identity_warnings"][-1])

        developmental = ctx.get("developmental") or {}
        if developmental:
            # Developmental pressure (Prompt 21): long-run facts become
            # pressure, never commands. Stagnation biases safe
            # exploration; drift biases stabilization.
            if developmental.get("stagnation_pressure") is not None:
                up("stagnation_pressure",
                   clamp01(developmental["stagnation_pressure"]),
                   "developmental",
                   raw=developmental["stagnation_pressure"])
            if developmental.get("drift_pressure") is not None:
                up("drift_pressure",
                   clamp01(developmental["drift_pressure"]),
                   "developmental", raw=developmental["drift_pressure"])
            if developmental.get("memory_pressure") is not None:
                up("consolidation_pressure",
                   max(self.state.value("consolidation_pressure", 0.0),
                       clamp01(developmental["memory_pressure"])),
                   "developmental")
            if developmental.get("identity_continuity") is not None:
                up("identity_uncertainty_pressure",
                   clamp01(1.0 - float(
                       developmental["identity_continuity"])),
                   "developmental",
                   raw=developmental["identity_continuity"])
            if developmental.get("long_run_fatigue_proxy") is not None:
                up("fatigue",
                   max(self.state.value("fatigue", 0.0),
                       clamp01(developmental["long_run_fatigue_proxy"])),
                   "developmental")

    def _auto_context(self, ctx: Dict[str, Any]) -> Dict[str, Any]:
        valence = self.valence.rolling()
        return {
            "heartbeat_fresh": self.state.value("heartbeat_freshness",
                                                1.0) > 0.5,
            "continuity_stable": self.state.value("restart_stability",
                                                  1.0) > 0.6,
            "checkpoint_ok": self.state.value("checkpoint_freshness",
                                              1.0) > 0.4,
            "state_restored": ctx.get("state_restored", True),
            "inner_map_coherent": ctx.get("inner_map_coherent", True),
            "world_model_stable": not (ctx.get("world_model") or {}).get(
                "predicted_danger", False),
            "valence_nonnegative": valence >= -0.05,
            "safe_operation": self.state.value("policy_violation_pressure",
                                               0.0) < 0.3,
            "brain_death_gap": self.state.value("restart_stability",
                                                1.0) < 0.5,
            "heartbeat_stale": self.state.value("heartbeat_freshness",
                                                1.0) < 0.3,
            "critical_incident": ctx.get("health_level") == "critical"
            or ctx.get("critical_incident", False),
            "mysterium_unresolved": self.state.value("unknown_pressure")
            > 0.7,
            "repeated_blocked_actions": self.state.value(
                "blocked_action_pressure") > 0.6,
            "substrate_runaway": ctx.get("substrate_runaway", False),
            "substrate_inert": ctx.get("substrate_inert", False),
            "checkpoint_failed": ctx.get("checkpoint_failed", False),
            "policy_violation": self.state.value(
                "policy_violation_pressure") > 0.3,
            "exhausted": self.state.value("exhaustion_pressure") > 0.5,
            "fatigue_high": self.state.value("fatigue") > 0.7,
            # Ego/self-model (Prompt 18): identity continuity and boundary
            # status feed the Being/Not-Being reading.
            "identity_continuity_ok": self.state.value(
                "identity_uncertainty_pressure", 0.0) < 0.3,
            "identity_anchor_mismatch": self.state.value(
                "identity_uncertainty_pressure", 0.0) > 0.4,
            "ego_boundary_violation": self.state.value(
                "boundary_violation_pressure", 0.0) > 0.2,
        }

    def _map_update(self, need_state: NeedState,
                    tension: BeingNotBeingTension) -> Dict[str, Any]:
        """A MapUpdate-like summary of what this update changed."""
        dominant = need_state.dominant()
        dominant_drive = self.drives.state.dominant()
        return {
            "kind": "homeostasis_map_update",
            "dominant_need": dominant.type if dominant else None,
            "dominant_drive": (dominant_drive.category
                               if dominant_drive else None),
            "valence_rolling": self.valence.rolling(),
            "tension": tension.tension,
            "action_implication": tension.action_implication,
            "most_urgent_variables": [v.name for v in
                                      self.state.most_urgent(3)],
        }

    def _record(self, result: HomeostaticRegulationResult) -> None:
        dominant = result.need_state.dominant()
        dominant_drive = self.drives.state.dominant()
        best = self.synthesis.best()
        self.memory.record(NeedTrace(
            step=result.step,
            dominant_need=dominant.type if dominant else None,
            dominant_drive=(dominant_drive.category
                            if dominant_drive else None),
            need_count=len(result.need_state.needs),
            conflict_count=len(result.conflicts),
            suppressed_desires=sum(1 for c in result.desire_candidates
                                   if c.blocked),
            best_desire=best.proposal if best else None,
            valence_rolling=self.valence.rolling(),
            being_pressure=result.tension.being_pressure,
            not_being_pressure=result.tension.not_being_pressure,
            tension=result.tension.tension,
            action_implication=result.tension.action_implication))

    # -- outward faces ------------------------------------------------------------

    def to_modulation_vector(self) -> np.ndarray:
        """The 10-channel drive vector (data for substrate modulation)."""
        return self.drives.drive_vector()

    def to_desire_bias(self) -> Dict[str, float]:
        """Proposal -> bias; suppressed proposals carry zero bias."""
        bias = self.drives.desire_bias()
        if self.last_result is not None:
            for candidate in self.last_result.desire_candidates:
                if candidate.blocked:
                    bias.pop(candidate.proposal, None)
        return bias

    def feed_world_model(self, builder: Any) -> int:
        """Need/drive/desire/conflict structure into the knowledge graph."""
        from ..world_model.edges import EdgeType
        from ..world_model.nodes import NodeType

        if self.last_result is None:
            return 0
        graph = builder.graph
        touched = 0
        for need in self.last_result.need_state.needs:
            node = graph.upsert_node(NodeType.STATE, f"need:{need.type}",
                                     source_module="homeostasis",
                                     intensity=need.intensity)
            touched += 1
            for proposal in need.possible_desires[:2]:
                desire_node = graph.upsert_node(
                    NodeType.STATE, f"desire:{proposal}",
                    source_module="homeostasis")
                graph.upsert_edge(node, EdgeType.PRODUCES, desire_node,
                                  weight_delta=need.intensity or 0.1)
        for conflict in self.last_result.conflicts:
            winner = graph.upsert_node(NodeType.STATE,
                                       f"need:{conflict.winner}",
                                       source_module="homeostasis")
            for loser in conflict.suppressed:
                loser_node = graph.upsert_node(NodeType.STATE,
                                               f"need:{loser}",
                                               source_module="homeostasis")
                graph.upsert_edge(winner, EdgeType.CONTRADICTS, loser_node,
                                  weight_delta=conflict.severity or 0.1,
                                  evidence={"rule":
                                            conflict.resolution_rule})
                touched += 1
        return touched

    def save_state(self) -> Optional[Dict[str, Any]]:
        if self.memory is None:
            return None
        snapshot = self.snapshot()
        self.memory.save_state(snapshot)
        self.memory.save_auto_determination(self.auto.snapshot())
        return snapshot

    def summary(self) -> Dict[str, Any]:
        """Compact homeostasis status for the Inner MAP / supervisor."""
        result = self.last_result
        dominant = result.need_state.dominant() if result else None
        dominant_drive = self.drives.state.dominant()
        best = self.synthesis.best()
        tension = (result.tension if result
                   else self.auto.state.current)
        return {
            "enabled": True,
            "updates": self.updates,
            "last_update_at": self.last_update_at,
            "dominant_need": dominant.type if dominant else None,
            "dominant_need_intensity": (dominant.intensity
                                        if dominant else 0.0),
            "dominant_drive": (dominant_drive.category
                               if dominant_drive else None),
            "current_valence": self.valence.current(),
            "valence_trend": self.valence.trend(),
            "being_pressure": tension.being_pressure,
            "not_being_pressure": tension.not_being_pressure,
            "auto_determination_tension": tension.tension,
            "action_implication": tension.action_implication,
            "shutdown_recommendations":
                self.auto.state.shutdown_recommendations,
            "conflict_count": (len(result.conflicts) if result else 0),
            "suppressed_desire_count": self.synthesis.suppressed_total,
            "last_desire_candidates": [c.proposal for c in
                                       (result.desire_candidates[:5]
                                        if result else [])],
            "best_desire": best.proposal if best else None,
            "safety_rejections": self.safety.rejected_count,
            "homeostasis_report_path": None,  # set by callers that save one
        }

    def snapshot(self) -> Dict[str, Any]:
        return {
            "summary": self.summary(),
            "variables": self.state.to_dict(),
            "drives": self.drives.snapshot(),
            "valence": self.valence.snapshot(),
            "auto_determination": self.auto.snapshot(),
            "conflicts": self.conflicts.snapshot(),
            "synthesis": self.synthesis.snapshot(),
            "safety": self.safety.snapshot(),
            "memory": (self.memory.snapshot()
                       if self.memory is not None else None),
        }
