"""StateGraph -- a dependency-free self-map of the substrate's parts.

A lightweight directed graph (plain dicts/lists, no networkx) describing the
components of Solaris-AI-NN and how they relate. It is the NN analogue of the
assembled topology in Solaris_Ai's ``conscience.py``: a visual self-map the Inner
MAP can export. ``to_dot`` / ``to_mermaid`` render it without any dependency.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class StateGraph:
    """A tiny directed graph of nodes and labelled edges."""

    nodes: Dict[str, Dict[str, str]] = field(default_factory=dict)
    edges: List[Tuple[str, str, str]] = field(default_factory=list)

    def add_node(self, name: str, role: str = "") -> None:
        """Add (or update) a node with an optional human role label."""
        self.nodes[name] = {"role": role}

    def add_edge(self, src: str, dst: str, label: str = "") -> None:
        """Add a directed edge ``src -> dst`` with a relationship label.

        Endpoints are auto-created as bare nodes if not already present.
        """
        self.nodes.setdefault(src, {"role": ""})
        self.nodes.setdefault(dst, {"role": ""})
        self.edges.append((src, dst, label))

    def to_dict(self) -> Dict[str, object]:
        return {
            "nodes": [{"name": n, **attrs} for n, attrs in self.nodes.items()],
            "edges": [{"src": s, "dst": d, "label": lbl} for s, d, lbl in self.edges],
        }

    def to_dot(self) -> str:
        """Render as Graphviz DOT."""
        lines = ["digraph solaris_ai_nn {", "  rankdir=LR;"]
        for name, attrs in self.nodes.items():
            role = attrs.get("role", "")
            label = f"{name}\\n({role})" if role else name
            lines.append(f'  "{name}" [label="{label}"];')
        for src, dst, lbl in self.edges:
            lines.append(f'  "{src}" -> "{dst}" [label="{lbl}"];')
        lines.append("}")
        return "\n".join(lines)

    def to_mermaid(self) -> str:
        """Render as a Mermaid flowchart."""
        lines = ["flowchart LR"]
        for name, attrs in self.nodes.items():
            role = attrs.get("role", "")
            text = f"{name}<br/>{role}" if role else name
            lines.append(f'  {name}["{text}"]')
        for src, dst, lbl in self.edges:
            arrow = f"-- {lbl} -->" if lbl else "-->"
            lines.append(f"  {src} {arrow} {dst}")
        return "\n".join(lines)


def build_default_state_graph() -> StateGraph:
    """Build the canonical Solaris-AI-NN self-map (nodes + relationships)."""
    g = StateGraph()
    for name, role in [
        ("runtime", "session loop"),
        ("bridge", "signal substrate"),
        ("reservoir", "ESN temporal state"),
        ("readout", "action tendencies"),
        ("memory", "trace + consolidation"),
        ("habit", "reinforced pathways"),
        ("synthesis", "subtractive pruning"),
        ("telemetry", "observable metrics"),
        ("continuity", "lifecycle + persistence"),
        ("boundaries", "operating limits"),
        ("tendencies", "suggested action/desire"),
        ("unknown", "drift / novelty"),
    ]:
        g.add_node(name, role)

    g.add_edge("bridge", "reservoir", "updates")
    g.add_edge("reservoir", "readout", "feeds")
    g.add_edge("readout", "tendencies", "produces")
    g.add_edge("habit", "tendencies", "biases")
    g.add_edge("synthesis", "readout", "prunes weak pathways")
    g.add_edge("synthesis", "habit", "prunes weak pathways")
    g.add_edge("bridge", "memory", "records")
    g.add_edge("reservoir", "memory", "snapshots")
    g.add_edge("telemetry", "runtime", "observes")
    g.add_edge("continuity", "runtime", "persists")
    g.add_edge("runtime", "boundaries", "respects")
    g.add_edge("reservoir", "unknown", "drift source")
    g.add_edge("inner_map", "runtime", "observes")
    g.add_edge("inner_map", "bridge", "observes")
    g.add_edge("inner_map", "memory", "observes")
    g.add_edge("inner_map", "habit", "observes")
    g.add_edge("inner_map", "synthesis", "observes")
    g.add_edge("inner_map", "boundaries", "checks")
    g.nodes["inner_map"]["role"] = "self-observation"

    # Controlled-plasticity subsystem (Prompt 5).
    for name, role in [
        ("plasticity_engine", "applies mutations"),
        ("policy", "proposes mutations"),
        ("safety_validator", "validates mutations"),
        ("rollback_manager", "undoes mutations"),
        ("audit_log", "records mutations"),
    ]:
        g.add_node(name, role)
    g.add_edge("telemetry", "policy", "informs")
    g.add_edge("inner_map", "policy", "informs")
    g.add_edge("policy", "plasticity_engine", "proposes mutation")
    g.add_edge("safety_validator", "plasticity_engine", "validates mutation")
    g.add_edge("plasticity_engine", "readout", "applies mutation")
    g.add_edge("plasticity_engine", "reservoir", "applies mutation")
    g.add_edge("plasticity_engine", "habit", "applies mutation")
    g.add_edge("plasticity_engine", "synthesis", "applies mutation")
    g.add_edge("rollback_manager", "plasticity_engine", "restores previous state")
    g.add_edge("audit_log", "plasticity_engine", "records every mutation")
    g.add_edge("boundaries", "safety_validator", "defines limits")

    # Substrate laboratory (Prompt 6).
    for name, role in [
        ("substrate_registry", "selectable substrates"),
        ("esn_substrate", "ESN baseline"),
        ("liquid_state_substrate", "liquid-state inspired"),
        ("spiking_recurrent_substrate", "binary spiking"),
        ("substrate_metrics", "shared activity metrics"),
        ("event_encoder", "signal -> vector"),
    ]:
        g.add_node(name, role)
    g.add_edge("substrate_registry", "esn_substrate", "registers")
    g.add_edge("substrate_registry", "liquid_state_substrate", "registers")
    g.add_edge("substrate_registry", "spiking_recurrent_substrate", "registers")
    # "reservoir" is the selected substrate node; it already feeds the readout.
    g.add_edge("event_encoder", "reservoir", "feeds selected substrate")
    g.add_edge("substrate_metrics", "inner_map", "feeds")
    g.add_edge("plasticity_engine", "substrate_registry",
               "may tune substrate parameters within safety bounds")

    # Solaris sidecar integration (Prompt 7). External nodes are Solaris_Ai's;
    # the sidecar only observes them and suggests -- action authority stays out.
    for name, role in [
        ("solaris_conscience_external", "Solaris_Ai organism (external)"),
        ("solaris_bus_external", "Solaris_Ai bus (external)"),
        ("solaris_nn_sidecar", "optional adaptive sidecar"),
        ("bus_connector", "observe-first subscription"),
        ("signal_mirror", "read-only signal mirror"),
        ("suggestion_channel", "suggestions only, never committed"),
    ]:
        g.add_node(name, role)
    g.add_edge("solaris_conscience_external", "solaris_bus_external", "owns")
    g.add_edge("solaris_bus_external", "bus_connector", "emits observed signals")
    g.add_edge("bus_connector", "bridge", "forwards to neural bridge")
    g.add_edge("bridge", "reservoir", "updates substrate")
    g.add_edge("bus_connector", "signal_mirror", "mirrors")
    g.add_edge("bus_connector", "suggestion_channel", "routes suggestions")
    g.add_edge("suggestion_channel", "solaris_bus_external",
               "publishes suggestions (never Actions)")
    g.add_edge("inner_map", "solaris_nn_sidecar", "observes sidecar state")
    g.add_edge("solaris_nn_sidecar", "bus_connector", "owns")
    g.add_edge("solaris_conscience_external", "solaris_conscience_external",
               "remains action authority")

    # Embodiment / sensorimotor sandbox (Prompt 8). Simulation-only.
    for name, role in [
        ("simulated_body", "body in simulation"),
        ("grid_world", "bounded 2D world"),
        ("sensors", "simulated senses"),
        ("effectors", "simulated actions"),
        ("energy_model", "simulated metabolism"),
        ("embodiment_safety", "simulation-only authority"),
        ("sensorimotor_runner", "perceive/act/learn loop"),
    ]:
        g.add_node(name, role)
    g.add_edge("grid_world", "sensors", "produces sensory data")
    g.add_edge("sensors", "bridge", "emit Stimulus")
    g.add_edge("bridge", "reservoir", "updates substrate")
    g.add_edge("bridge", "effectors", "suggests Action")
    g.add_edge("embodiment_safety", "effectors", "validates Action")
    g.add_edge("effectors", "grid_world", "act in simulation")
    g.add_edge("grid_world", "bridge", "feedback emits Reaction")
    g.add_edge("energy_model", "sensors", "internal need Stimulus")
    g.add_edge("sensorimotor_runner", "simulated_body", "drives")
    g.add_edge("inner_map", "simulated_body", "observes body/world state")
    g.add_edge("inner_map", "grid_world", "observes body/world state")

    # Internal language / explainability layer (Prompt 9).
    for name, role in [
        ("language_layer", "cross-module meaning"),
        ("meaning_trace_builder", "events -> atoms"),
        ("causal_trace_builder", "heuristic chains"),
        ("explanation_engine", "grounded explanations"),
        ("structural_summarizer", "counts, not prose"),
        ("query_interface", "deterministic queries"),
        ("report_builder", "JSON/Markdown reports"),
    ]:
        g.add_node(name, role)
    g.add_edge("bridge", "meaning_trace_builder", "signals feed")
    g.add_edge("telemetry", "structural_summarizer", "feeds")
    g.add_edge("inner_map", "explanation_engine", "feeds")
    g.add_edge("simulated_body", "explanation_engine", "embodiment feeds")
    g.add_edge("meaning_trace_builder", "causal_trace_builder", "feeds")
    g.add_edge("explanation_engine", "language_layer", "produces SystemUtterance")
    g.add_edge("query_interface", "explanation_engine", "routes queries")
    g.add_edge("structural_summarizer", "report_builder", "feeds")
    g.add_edge("report_builder", "continuity", "persists session reports")

    # Evaluation / benchmark layer (Prompt 10).
    for name, role in [
        ("benchmark_runner", "bounded benchmark execution"),
        ("experiment_registry", "protocol catalogue"),
        ("metric_collector", "objective domain metrics"),
        ("evaluation_score", "cautious scorecard"),
        ("failure_analyzer", "diagnosis, no auto-fix"),
        ("artifact_collector", "file evidence"),
    ]:
        g.add_node(name, role)
    g.add_edge("experiment_registry", "benchmark_runner", "provides protocols")
    g.add_edge("benchmark_runner", "artifact_collector", "experiments produce artifacts")
    g.add_edge("artifact_collector", "metric_collector", "artifacts feed metrics")
    g.add_edge("metric_collector", "evaluation_score", "metrics feed scorecard")
    g.add_edge("evaluation_score", "inner_map", "scorecard feeds Inner MAP")
    g.add_edge("failure_analyzer", "report_builder", "failure analysis feeds debugging")

    # Operations / long-running supervision (Prompt 11).
    for name, role in [
        ("operational_supervisor", "segmented supervision"),
        ("health_monitor", "domain health checks"),
        ("watchdog", "requests safe shutdown"),
        ("resource_budget", "soft limits"),
        ("safe_shutdown_manager", "dying well"),
        ("incident_log", "operational evidence"),
        ("run_registry", "run history"),
        ("artifact_rotation_policy", "bounded evidence"),
        ("local_status_server", "read-only localhost status"),
    ]:
        g.add_node(name, role)
    g.add_edge("runtime", "health_monitor", "runners feed")
    g.add_edge("health_monitor", "watchdog", "feeds")
    g.add_edge("watchdog", "safe_shutdown_manager", "can request safe shutdown")
    g.add_edge("resource_budget", "incident_log", "feeds")
    g.add_edge("incident_log", "inner_map", "feeds")
    g.add_edge("operational_supervisor", "run_registry", "updates")
    g.add_edge("artifact_rotation_policy", "incident_log", "preserves evidence")
    g.add_edge("operational_supervisor", "local_status_server", "owns (opt-in)")

    # Governance / operator control (Prompt 12). Control layer, not cognition.
    for name, role in [
        ("governance_policy", "what is allowed"),
        ("permission_set", "deny-by-default scopes"),
        ("approval_registry", "local human approval ledger"),
        ("risk_assessment", "named risks per run"),
        ("emergency_stop", "always-available stop"),
        ("claim_guard", "no unsupported claims"),
        ("runbook", "written operator procedure"),
        ("post_run_review", "human recommendation"),
    ]:
        g.add_node(name, role)
    g.add_edge("runtime", "risk_assessment", "manifest feeds")
    g.add_edge("risk_assessment", "approval_registry",
               "high risks require approval")
    g.add_edge("permission_set", "operational_supervisor",
               "permissions feed supervisor")
    g.add_edge("governance_policy", "operational_supervisor",
               "evaluates manifest before run")
    g.add_edge("approval_registry", "governance_policy",
               "approvals satisfy required scopes")
    g.add_edge("emergency_stop", "safe_shutdown_manager",
               "requests safe shutdown")
    g.add_edge("claim_guard", "report_builder", "scans reports before save")
    g.add_edge("governance_policy", "inner_map",
               "governance status feeds Inner MAP")
    g.add_edge("runbook", "operational_supervisor",
               "documents the procedure")
    g.add_edge("post_run_review", "governance_policy",
               "feeds the next run's evaluation")

    # Pilot-0 deployment (Prompt 13). Controlled deployment, not autonomy.
    for name, role in [
        ("pilot_profile", "sanctioned deployment shape"),
        ("pilot_manifest", "one pilot, fully pinned"),
        ("pilot_safety_validator", "refuses unsafe pilots"),
        ("pilot_deployment_runner", "governed bounded pilot"),
        ("pilot_readiness_report", "ready or not, and why"),
        ("pilot_report", "the written account"),
        ("read_only_stream_ingestor", "reads local streams, only"),
        ("stream_sensor", "events -> Stimuli"),
    ]:
        g.add_node(name, role)
    g.add_edge("pilot_profile", "pilot_manifest", "pins defaults")
    g.add_edge("pilot_manifest", "governance_policy",
               "pilot manifest feeds governance")
    g.add_edge("pilot_manifest", "risk_assessment", "feeds")
    g.add_edge("pilot_safety_validator", "pilot_deployment_runner",
               "safety gates deployment")
    g.add_edge("read_only_stream_ingestor", "stream_sensor",
               "validated events")
    g.add_edge("stream_sensor", "bridge", "stream sensors feed neural bridge")
    g.add_edge("operational_supervisor", "pilot_deployment_runner",
               "supervises the pilot")
    g.add_edge("pilot_readiness_report", "pilot_deployment_runner",
               "gates the launch")
    g.add_edge("evaluation_score", "pilot_report", "evaluation feeds report")
    g.add_edge("pilot_report", "inner_map", "pilot state feeds Inner MAP")

    # Latent cognition (Prompt 14). Bounded offline processing; never acts.
    for name, role in [
        ("sleep_wake_controller", "mode state machine"),
        ("latent_scheduler", "bounded cycle decisions"),
        ("sleep_cycle", "maintenance + consolidation"),
        ("dream_cycle", "sandboxed counterfactual replay"),
        ("offline_replay_engine", "windows into sandboxes"),
        ("counterfactual_generator", "labelled what-if variants"),
        ("anticipation_tracker", "one-step predictions"),
        ("mysterium_tracker", "numeric unknown pressure"),
        ("complexity_pressure_monitor", "inertia/chaos detection"),
        ("latent_safety_validator", "no actions while latent"),
    ]:
        g.add_node(name, role)
    g.add_edge("memory", "offline_replay_engine", "trace memory feeds replay")
    g.add_edge("offline_replay_engine", "dream_cycle",
               "replay feeds substrate sandbox")
    g.add_edge("counterfactual_generator", "dream_cycle",
               "labelled variants")
    g.add_edge("anticipation_tracker", "mysterium_tracker",
               "compares prediction to actual")
    g.add_edge("mysterium_tracker", "latent_scheduler",
               "unknown pressure informs scheduling")
    g.add_edge("complexity_pressure_monitor", "latent_scheduler",
               "suggests latent action")
    g.add_edge("latent_scheduler", "sleep_wake_controller", "drives modes")
    g.add_edge("latent_safety_validator", "sleep_wake_controller",
               "gates transitions")
    g.add_edge("sleep_cycle", "memory", "consolidates")
    g.add_edge("dream_cycle", "inner_map", "latent report feeds Inner MAP")

    # World model / neuro-symbolic memory (Prompt 15).
    for name, role in [
        ("knowledge_graph", "observed symbols + relations"),
        ("world_model_builder", "grows the graph from everything"),
        ("signal_graph_extractor", "signals -> structure"),
        ("embodiment_graph_extractor", "GridWorld -> structure"),
        ("language_graph_extractor", "meaning atoms -> structure"),
        ("latent_graph_extractor", "offline evidence -> structure"),
        ("association_learner", "counted pairwise associations"),
        ("causal_association_model", "candidates, never proven causes"),
        ("context_tracker", "which situation it was"),
        ("world_model_predictor", "predictions from graph counts"),
        ("graph_synthesis_pruner", "subtraction over graph memory"),
    ]:
        g.add_node(name, role)
    g.add_edge("memory", "world_model_builder", "trace memory feeds")
    g.add_edge("language_layer", "world_model_builder",
               "language trace feeds")
    g.add_edge("simulated_body", "world_model_builder", "embodiment feeds")
    g.add_edge("dream_cycle", "world_model_builder",
               "latent replay feeds (offline)")
    g.add_edge("signal_graph_extractor", "knowledge_graph", "upserts")
    g.add_edge("embodiment_graph_extractor", "knowledge_graph", "upserts")
    g.add_edge("language_graph_extractor", "knowledge_graph", "upserts")
    g.add_edge("latent_graph_extractor", "knowledge_graph",
               "upserts (offline-marked)")
    g.add_edge("association_learner", "knowledge_graph", "writes weights")
    g.add_edge("causal_association_model", "knowledge_graph",
               "causes_candidate edges")
    g.add_edge("context_tracker", "knowledge_graph", "context nodes")
    g.add_edge("world_model_predictor", "anticipation_tracker",
               "world model feeds anticipation")
    g.add_edge("world_model_builder", "inner_map",
               "world model feeds Inner MAP")
    g.add_edge("graph_synthesis_pruner", "knowledge_graph",
               "synthesis feeds pruning report")

    # Homeostasis / need economy (Prompt 16). Pressure, never authority.
    for name, role in [
        ("homeostatic_regulator", "the need-economy loop"),
        ("homeostatic_state", "normalized internal variables"),
        ("need_estimator", "variables -> need pressures"),
        ("drive_resolver", "needs -> drive channels"),
        ("valence_estimator", "feedback polarity, not emotion"),
        ("auto_determination_engine", "Being/Not-Being tension"),
        ("conflict_resolver", "safety-first priority ladder"),
        ("desire_synthesis_engine", "drives -> Desire suggestions"),
        ("need_memory", "the pressure trail on disk"),
    ]:
        g.add_node(name, role)
    g.add_edge("telemetry", "homeostatic_state", "telemetry feeds variables")
    g.add_edge("homeostatic_state", "need_estimator",
               "variables feed needs")
    g.add_edge("need_estimator", "drive_resolver", "needs feed drives")
    g.add_edge("drive_resolver", "desire_synthesis_engine",
               "drives feed desire synthesis")
    g.add_edge("conflict_resolver", "desire_synthesis_engine",
               "conflicts suppress unsafe desires")
    g.add_edge("desire_synthesis_engine", "bridge",
               "desire candidates bias suggestions")
    g.add_edge("valence_estimator", "auto_determination_engine", "feeds")
    g.add_edge("homeostatic_regulator", "need_memory", "records")
    g.add_edge("homeostatic_regulator", "inner_map",
               "homeostasis feeds Inner MAP")

    # Executive function (Prompt 17). Arbitration, never authority.
    for name, role in [
        ("desire_queue", "competing Desire candidates"),
        ("inhibition_controller", "explainable suppression"),
        ("action_arbitrator", "scores with penalties dominating"),
        ("prospection_engine", "bounded consequence estimates"),
        ("short_horizon_planner", "<=3-step suggestion plans"),
        ("executive_working_memory", "short-lived active context"),
        ("attention_selector", "prioritization, not awareness"),
        ("decision_trace_recorder", "every arbitration written down"),
        ("executive_policy", "mode control, ops first"),
        ("executive_safety_validator", "the walls around arbitration"),
    ]:
        g.add_node(name, role)
    g.add_edge("desire_synthesis_engine", "desire_queue",
               "homeostasis feeds desire queue")
    g.add_edge("world_model_predictor", "prospection_engine",
               "world model feeds prospection")
    g.add_edge("inhibition_controller", "action_arbitrator",
               "inhibition filters candidates")
    g.add_edge("action_arbitrator", "bridge",
               "arbitration selects the suggestion")
    g.add_edge("short_horizon_planner", "action_arbitrator",
               "planner sequences short plans")
    g.add_edge("decision_trace_recorder", "report_builder",
               "decision trace feeds language/reporting")
    g.add_edge("executive_policy", "inner_map",
               "executive state feeds Inner MAP")
    return g
