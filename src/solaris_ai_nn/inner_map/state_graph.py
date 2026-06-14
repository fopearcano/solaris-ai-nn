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

    # Ego / self-model (Prompt 18). Boundaries and continuity, no authority.
    for name, role in [
        ("self_model", "operational self, aggregated"),
        ("identity_state", "anchors and runtime continuity"),
        ("boundary_registry", "self/not-self boundaries"),
        ("dimensional_comparator", "six fixed comparison axes"),
        ("ownership_attributor", "who produced what"),
        ("ego_continuity_monitor", "how unbroken is the thread"),
        ("body_schema", "the simulated body, declared simulated"),
        ("perspective_tracker", "recorded operating modes"),
        ("narrative_trace", "templated continuity story"),
        ("ego_safety_validator", "the self-model has no authority"),
    ]:
        g.add_node(name, role)
    g.add_edge("telemetry", "identity_state",
               "operational status feeds identity")
    g.add_edge("governance_policy", "boundary_registry",
               "governance feeds boundaries")
    g.add_edge("solaris_nn_sidecar", "perspective_tracker",
               "pilot/sidecar feeds perspective")
    g.add_edge("sleep_wake_controller", "boundary_registry",
               "latent feeds the offline boundary")
    g.add_edge("action_arbitrator", "boundary_registry",
               "executive feeds the action authority boundary")
    g.add_edge("world_model_builder", "self_model",
               "world model feeds the self/world distinction")
    g.add_edge("self_model", "inner_map",
               "the self-model feeds Inner MAP")

    # Communication gateway (Prompt 19). An interface, never authority.
    for name, role in [
        ("communication_gateway", "the one door for operator text"),
        ("operator_input_classifier", "classify before any effect"),
        ("command_router", "bounded commands or refusals"),
        ("communication_query_router", "questions answered from state"),
        ("approval_router", "decisions onto real pending requests"),
        ("response_builder", "grounded, templated, scanned text"),
        ("communication_transcript", "every exchange on the record"),
        ("communication_safety_validator", "language never outranks "
                                           "policy"),
    ]:
        g.add_node(name, role)
    g.add_edge("communication_gateway", "operator_input_classifier",
               "operator input feeds the classifier")
    g.add_edge("operator_input_classifier",
               "communication_safety_validator",
               "classification feeds safety/governance")
    g.add_edge("communication_query_router", "inner_map",
               "the query router reads system state")
    g.add_edge("command_router", "action_arbitrator",
               "bounded command requests become candidates")
    g.add_edge("response_builder", "communication_gateway",
               "grounded text returns through the gateway")
    g.add_edge("communication_transcript", "inner_map",
               "the transcript feeds audit and Inner MAP")

    # Optional local LLM adapter (Prompt 20). Translator, never authority.
    for name, role in [
        ("llm_adapter", "optional translator, outside authority"),
        ("local_http_llm_adapter", "localhost-only endpoint client"),
        ("mock_llm_adapter", "deterministic fake for tests"),
        ("grounding_validator", "no invented facts pass"),
        ("llm_paraphraser", "readability or fallback"),
        ("llm_classification_assistant", "suggestions under a ruler"),
        ("llm_summarizer", "shorter text, identical truth"),
        ("report_polisher", "wording changes, facts do not"),
        ("llm_audit_log", "every adapter call hashed on record"),
    ]:
        g.add_node(name, role)
    g.add_edge("response_builder", "llm_paraphraser",
               "deterministic response feeds the paraphraser")
    g.add_edge("llm_adapter", "grounding_validator",
               "LLM output feeds grounding validation")
    g.add_edge("grounding_validator", "claim_guard"
               if "claim_guard" in g.nodes else "governance_policy",
               "grounding validator feeds ClaimGuard")
    g.add_edge("llm_paraphraser", "communication_gateway",
               "safe paraphrase feeds the communication response")
    g.add_edge("llm_audit_log", "inner_map",
               "LLM audit feeds Inner MAP")
    g.add_edge("llm_adapter", "llm_audit_log",
               "every call is audited; the LLM never feeds executive "
               "authority")

    # Developmental runtime (Prompt 21). Learning by persistence.
    for name, role in [
        ("developmental_runtime", "persistent process, not training job"),
        ("developmental_clock", "lifetime across restarts"),
        ("epoch_manager", "labels over metrics, reversible"),
        ("memory_layer_manager", "hot/warm/cold/fossil"),
        ("consolidation_policy", "what survives, at what resolution"),
        ("growth_monitor", "structure change vs accumulation"),
        ("long_run_drift_monitor", "slow drift is life"),
        ("milestone_registry", "the firsts, with evidence"),
        ("autobiographical_memory", "grounded developmental history"),
        ("phase_transition_detector", "hypotheses, never emergence "
                                      "claims"),
    ]:
        g.add_node(name, role)
    g.add_edge("telemetry", "developmental_clock",
               "telemetry feeds the developmental clock")
    g.add_edge("memory", "memory_layer_manager",
               "trace memory feeds the memory layers")
    g.add_edge("latent_scheduler", "consolidation_policy",
               "latent replay feeds consolidation")
    g.add_edge("world_model_builder", "growth_monitor",
               "the world model feeds the growth monitor")
    g.add_edge("long_run_drift_monitor", "operational_supervisor",
               "drift warnings feed ops/health")
    g.add_edge("milestone_registry", "memory_layer_manager",
               "milestones feed fossil memory")
    g.add_edge("developmental_runtime", "inner_map",
               "developmental state feeds Inner MAP")

    # Proto-language (Prompt 22). Signs under measurement, no authority.
    for name, role in [
        ("proto_symbol", "an internal sign from repetition"),
        ("symbol_registry", "every sign on the books"),
        ("symbol_emergence_engine", "repetition earns a name"),
        ("internal_pattern_namer", "deterministic tokens"),
        ("symbol_combinator", "which signs recur together"),
        ("syntax_probe", "proto-syntactic regularities, tested"),
        ("semantic_grounding_engine", "operational meaning"),
        ("symbol_compression_evaluator", "does naming compress?"),
        ("symbol_prediction_evaluator", "does naming predict?"),
        ("proto_utterance_builder", "internal sequences, not speech"),
        ("proto_language_translator", "debug renderings only"),
    ]:
        g.add_node(name, role)
    g.add_edge("language_layer" if "language_layer" in g.nodes
               else "memory", "symbol_emergence_engine",
               "the meaning trace feeds symbol emergence")
    g.add_edge("world_model_builder", "semantic_grounding_engine",
               "the world model grounds symbols")
    g.add_edge("symbol_registry", "symbol_compression_evaluator",
               "the registry feeds compression")
    g.add_edge("symbol_combinator", "syntax_probe",
               "symbol sequences feed the syntax probe")
    g.add_edge("symbol_prediction_evaluator", "evaluation_harness"
               if "evaluation_harness" in g.nodes else "inner_map",
               "prediction utility feeds evaluation")
    g.add_edge("symbol_registry", "inner_map",
               "proto-language state feeds Inner MAP")

    # Developmental nursery / stimulus ecology (Prompt 23). A world, not a
    # teacher: it generates stimuli, never labels and never acts.
    for name, role in [
        ("developmental_nursery", "the artificial world generator"),
        ("stimulus_ecology", "per-step world physics"),
        ("cycle_manager", "day/night and other rhythms"),
        ("regime_manager", "active world profile, not a lesson"),
        ("scarcity_model", "resource pressure, deprivation"),
        ("novelty_generator", "bounded new patterns"),
        ("anomaly_generator", "controlled perturbations, not errors"),
        ("seasonality_model", "slow seasonal drift"),
        ("deprivation_model", "bounded absence windows"),
        ("delayed_consequence_model", "cause now, effect later"),
        ("ecology_stream", "canonical signals + JSONL replay"),
        ("ecology_memory", "bounded ecology event history"),
    ]:
        g.add_node(name, role)
    g.add_edge("regime_manager", "stimulus_ecology",
               "regime sets the world's probabilities")
    g.add_edge("cycle_manager", "stimulus_ecology",
               "cycles modulate frequency and intensity")
    g.add_edge("cycle_manager", "regime_manager",
               "cycles modulate regime pressure")
    g.add_edge("seasonality_model", "stimulus_ecology",
               "seasons drift the world slowly")
    g.add_edge("scarcity_model", "stimulus_ecology",
               "scarcity throttles signal/reward")
    g.add_edge("novelty_generator", "stimulus_ecology",
               "novel patterns enter the world (bounded)")
    g.add_edge("anomaly_generator", "stimulus_ecology",
               "anomalies perturb established patterns")
    g.add_edge("deprivation_model", "stimulus_ecology",
               "deprivation opens absence windows")
    g.add_edge("delayed_consequence_model", "stimulus_ecology",
               "delayed effects resurface later")
    g.add_edge("stimulus_ecology", "developmental_nursery",
               "ecology events feed the nursery")
    g.add_edge("developmental_nursery", "ecology_memory",
               "events recorded in bounded memory")
    g.add_edge("developmental_nursery", "ecology_stream",
               "events become canonical signals + JSONL")
    g.add_edge("ecology_stream", "bridge",
               "ecology signals feed the neural bridge")
    g.add_edge("developmental_nursery", "world_model_builder",
               "delayed consequences feed the world model")
    g.add_edge("developmental_nursery", "symbol_emergence_engine"
               if "symbol_emergence_engine" in g.nodes else "memory",
               "recurring/absence stimuli feed proto-language")
    g.add_edge("anomaly_generator", "mysterium_tracker"
               if "mysterium_tracker" in g.nodes else "unknown",
               "anomalies and novelty drive Mysterium")
    g.add_edge("developmental_nursery", "homeostatic_state"
               if "homeostatic_state" in g.nodes else "telemetry",
               "scarcity and absence feed homeostatic pressure")
    g.add_edge("developmental_nursery", "developmental_runtime"
               if "developmental_runtime" in g.nodes else "runtime",
               "the nursery drives long developmental runs")
    g.add_edge("developmental_nursery", "inner_map",
               "ecology state feeds Inner MAP")

    # Active perception / intrinsic exploration (Prompt 24). The system
    # regulates its own exposure: it proposes safe sampling, never acts.
    for name, role in [
        ("active_sensing_controller", "proposes + safely runs sampling"),
        ("sampling_policy", "which safe sampling to propose, by mode"),
        ("salience_estimator", "what is worth attending to (ranked)"),
        ("uncertainty_estimator", "where the model is weakest"),
        ("curiosity_estimator", "intrinsic sampling pressure, not desire"),
        ("information_gain_estimator", "heuristic value of sampling"),
        ("active_attention_controller", "resource allocation, not awareness"),
        ("exploration_memory", "what sampling actually helped"),
        ("stagnation_detector", "stalling / racing / healthily quiet"),
        ("active_perception_safety", "exploration never a back door"),
    ]:
        g.add_node(name, role)
    # ecology feeds salience; world model feeds uncertainty; proto-language
    # feeds ambiguity; curiosity feeds the policy; the policy feeds the
    # executive; results feed exploration memory and evaluation.
    g.add_edge("developmental_nursery", "salience_estimator",
               "ecology events feed salience")
    g.add_edge("world_model_builder" if "world_model_builder" in g.nodes
               else "knowledge_graph", "uncertainty_estimator",
               "world model feeds uncertainty")
    g.add_edge("symbol_registry" if "symbol_registry" in g.nodes
               else "memory", "uncertainty_estimator",
               "proto-symbol ambiguity feeds uncertainty")
    g.add_edge("mysterium_tracker" if "mysterium_tracker" in g.nodes
               else "unknown", "curiosity_estimator",
               "Mysterium feeds intrinsic pressure")
    g.add_edge("salience_estimator", "active_attention_controller",
               "salience drives attention focus")
    g.add_edge("uncertainty_estimator", "sampling_policy",
               "uncertain targets feed the policy")
    g.add_edge("curiosity_estimator", "sampling_policy",
               "curiosity feeds the policy")
    g.add_edge("stagnation_detector", "sampling_policy",
               "stagnation feeds the policy")
    g.add_edge("sampling_policy", "active_sensing_controller",
               "the policy decides; the controller proposes")
    g.add_edge("active_perception_safety", "active_sensing_controller",
               "safety gates every sampling action")
    g.add_edge("active_sensing_controller",
               "action_arbitrator" if "action_arbitrator" in g.nodes
               else "desire_queue",
               "sampling actions become ActionCandidates for the executive")
    g.add_edge("active_sensing_controller",
               "developmental_nursery",
               "sampling requests (never commands) bounded ecology shifts")
    g.add_edge("active_sensing_controller", "exploration_memory",
               "sampling results feed exploration memory")
    g.add_edge("active_sensing_controller",
               "homeostatic_state" if "homeostatic_state" in g.nodes
               else "telemetry",
               "curiosity/stagnation/overload feed homeostatic pressure")
    g.add_edge("exploration_memory",
               "metric_collector" if "metric_collector" in g.nodes
               else "inner_map",
               "exploration memory feeds evaluation")
    g.add_edge("information_gain_estimator", "exploration_memory",
               "expected vs observed gain recorded")
    g.add_edge("active_sensing_controller", "inner_map",
               "active perception state feeds Inner MAP")

    # Hypothesis engine / self-experimentation (Prompt 25). An internal
    # scientific loop: uncertainty -> hypothesis -> bounded test -> evidence.
    for name, role in [
        ("hypothesis_source_scanner", "uncertainty becomes seeds"),
        ("hypothesis_generator", "seeds become testable candidates"),
        ("experiment_design", "bounded, falsifiable test plans"),
        ("intervention_plan", "bounded requests to safe subsystems"),
        ("hypothesis_test_runner", "runs bounded experiments"),
        ("evidence_ledger", "source-scoped, append-only evidence"),
        ("falsification_engine", "careful supported/weakened/falsified"),
        ("hypothesis_memory", "what was wondered and learned"),
        ("hypothesis_prioritizer", "low-risk, high-information first"),
        ("hypothesis_safety", "experiments never a back door"),
    ]:
        g.add_node(name, role)
    g.add_edge("mysterium_tracker" if "mysterium_tracker" in g.nodes
               else "unknown", "hypothesis_source_scanner",
               "Mysterium feeds hypothesis seeds")
    g.add_edge("world_model_builder" if "world_model_builder" in g.nodes
               else "knowledge_graph", "hypothesis_generator",
               "the world model feeds hypothesis generation")
    g.add_edge("hypothesis_source_scanner", "hypothesis_generator",
               "seeds feed generation")
    g.add_edge("hypothesis_generator", "hypothesis_prioritizer",
               "candidates are prioritized")
    g.add_edge("hypothesis_prioritizer", "experiment_design",
               "scheduled hypotheses get bounded designs")
    g.add_edge("hypothesis_safety", "hypothesis_test_runner",
               "safety gates every experiment")
    g.add_edge("experiment_design", "hypothesis_test_runner",
               "designs are run within their bounded scope")
    g.add_edge("intervention_plan", "hypothesis_test_runner",
               "bounded interventions feed the test")
    g.add_edge("active_sensing_controller", "hypothesis_test_runner",
               "active perception tests hypotheses by sampling")
    g.add_edge("developmental_nursery" if "developmental_nursery" in g.nodes
               else "bridge", "hypothesis_test_runner",
               "the nursery provides safe interventions")
    g.add_edge("hypothesis_test_runner", "evidence_ledger",
               "tests produce source-scoped evidence")
    g.add_edge("evidence_ledger", "falsification_engine",
               "evidence drives the verdict")
    g.add_edge("falsification_engine", "hypothesis_memory",
               "verdicts update hypothesis memory")
    g.add_edge("evidence_ledger",
               "world_model_builder" if "world_model_builder" in g.nodes
               else "knowledge_graph",
               "supported evidence updates the world model")
    g.add_edge("evidence_ledger",
               "symbol_registry" if "symbol_registry" in g.nodes
               else "memory",
               "supported evidence updates proto-language")
    g.add_edge("hypothesis_memory",
               "developmental_runtime" if "developmental_runtime" in g.nodes
               else "runtime",
               "hypothesis memory feeds developmental reports")
    g.add_edge("hypothesis_memory", "inner_map",
               "hypothesis state feeds Inner MAP")

    # Auto-regeneration / long-run state hygiene (Prompt 26). Repairs
    # runtime state, never source code; governance and safety dominate.
    for name, role in [
        ("autoregeneration_diagnostics", "non-mutating degradation scans"),
        ("degradation_state", "operational degradation signals"),
        ("repair_policy", "which bounded repairs to apply, by mode"),
        ("repair_action", "bounded, reversible runtime-state repair"),
        ("state_hygiene_manager", "archive/quarantine inside state dir"),
        ("checkpoint_repair_manager", "continuity without rewriting history"),
        ("reference_repair_manager", "fix broken links, never invent them"),
        ("memory_hygiene_manager", "compaction preserving evidence"),
        ("world_model_hygiene_manager", "mark/weaken edges, keep evidence"),
        ("symbol_hygiene_manager", "tend the proto-symbol ecology"),
        ("habit_hygiene_manager", "decay/retire habits, bounded"),
        ("drift_recovery_manager", "adaptation vs runaway, recover safely"),
        ("repair_memory", "audited before/after repair record"),
        ("autoregeneration_safety", "repair never a back door"),
    ]:
        g.add_node(name, role)
    g.add_edge("telemetry", "autoregeneration_diagnostics",
               "telemetry feeds diagnostics")
    g.add_edge("autoregeneration_diagnostics", "degradation_state",
               "scans produce degradation signals")
    g.add_edge("degradation_state", "repair_policy",
               "degradation feeds the repair policy")
    g.add_edge("repair_policy", "repair_action",
               "the policy proposes bounded repairs")
    g.add_edge("autoregeneration_safety", "repair_action",
               "safety gates every repair")
    g.add_edge("repair_policy",
               "action_arbitrator" if "action_arbitrator" in g.nodes
               else "desire_queue",
               "repairs become ActionCandidates for the executive")
    g.add_edge("repair_policy",
               "governance_policy" if "governance_policy" in g.nodes
               else "inner_map",
               "governed/identity repairs feed governance")
    g.add_edge("repair_action", "plasticity_engine"
               if "plasticity_engine" in g.nodes else "readout",
               "rollback/parameter repair routes through plasticity")
    g.add_edge("state_hygiene_manager", "repair_memory",
               "hygiene results feed repair memory")
    g.add_edge("memory_hygiene_manager", "memory"
               if "memory" in g.nodes else "repair_memory",
               "memory hygiene compacts the trace, preserving evidence")
    g.add_edge("symbol_hygiene_manager",
               "symbol_registry" if "symbol_registry" in g.nodes
               else "repair_memory",
               "symbol hygiene marks/merges symbols")
    g.add_edge("world_model_hygiene_manager",
               "knowledge_graph" if "knowledge_graph" in g.nodes
               else "repair_memory",
               "graph hygiene marks/weakens edges")
    g.add_edge("checkpoint_repair_manager", "continuity"
               if "continuity" in g.nodes else "repair_memory",
               "checkpoint repair restores metadata, not history")
    g.add_edge("drift_recovery_manager", "repair_policy",
               "drift recovery proposes stabilization")
    g.add_edge("repair_action", "repair_memory",
               "safe repairs feed repair memory")
    g.add_edge("repair_memory",
               "metric_collector" if "metric_collector" in g.nodes
               else "inner_map",
               "repair memory feeds evaluation")
    g.add_edge("repair_memory", "inner_map",
               "auto-regeneration state feeds Inner MAP")

    # LOGOS fracture/synthesis and complexity regulation (Prompt 27).
    # A tension engine: it exposes fracture and proposes bounded resolution,
    # never authority and never truth.
    for name, role in [
        ("fracture_detector", "detects internal tensions (non-mutating)"),
        ("logos_tension", "one opposition between two internal poles"),
        ("synthesis_engine", "proposes bounded resolutions, not truths"),
        ("complexity_regulator", "inert/productive/overloaded bands"),
        ("resolution_policy", "which resolution path, by mode"),
        ("opposition_memory", "tensions and how they resolved"),
        ("esc_process", "operational instability signal, not panic"),
        ("dialectical_trace", "append-only record of LOGOS dynamics"),
        ("logos_complexity_safety", "LOGOS never a back door"),
    ]:
        g.add_node(name, role)
    g.add_edge("world_model_builder" if "world_model_builder" in g.nodes
               else "knowledge_graph", "fracture_detector",
               "world-model contradictions feed the fracture detector")
    g.add_edge("symbol_registry" if "symbol_registry" in g.nodes
               else "memory", "fracture_detector",
               "proto-symbol ambiguity feeds the fracture detector")
    g.add_edge("mysterium_tracker" if "mysterium_tracker" in g.nodes
               else "unknown", "logos_tension",
               "Mysterium feeds unresolved-tension pressure")
    g.add_edge("fracture_detector", "logos_tension",
               "fractures become tensions")
    g.add_edge("logos_tension", "synthesis_engine",
               "tensions feed the synthesis engine")
    g.add_edge("logos_complexity_safety", "synthesis_engine",
               "safety gates every synthesis")
    g.add_edge("resolution_policy", "synthesis_engine",
               "the policy chooses the resolution path")
    g.add_edge("synthesis_engine",
               "hypothesis_source_scanner" if "hypothesis_source_scanner"
               in g.nodes else "inner_map",
               "synthesis may spawn a hypothesis")
    g.add_edge("synthesis_engine",
               "active_sensing_controller" if "active_sensing_controller"
               in g.nodes else "inner_map",
               "synthesis may request active sampling")
    g.add_edge("synthesis_engine",
               "autoregeneration_diagnostics" if
               "autoregeneration_diagnostics" in g.nodes else "inner_map",
               "synthesis may request auto-regeneration")
    g.add_edge("complexity_regulator",
               "homeostatic_state" if "homeostatic_state" in g.nodes
               else "telemetry",
               "complexity pressure feeds homeostasis")
    g.add_edge("complexity_regulator",
               "action_arbitrator" if "action_arbitrator" in g.nodes
               else "desire_queue",
               "synthesis candidates feed the executive")
    g.add_edge("synthesis_engine", "opposition_memory",
               "synthesis results feed opposition memory")
    g.add_edge("esc_process", "opposition_memory",
               "Esc instability is recorded")
    g.add_edge("dialectical_trace", "opposition_memory",
               "dynamics are traced for later analysis")
    g.add_edge("opposition_memory", "inner_map",
               "LOGOS state feeds Inner MAP")

    # Conscience spine / unified runtime orchestrator (Prompt 28). The
    # orchestrator assembles the whole organism into one bounded, simulated
    # process; no module is sovereign and nothing actuates the real world.
    for name, role in [
        ("conscience_orchestrator", "the one top-level runtime; no module "
                                    "sovereign"),
        ("conscience_spine", "the canonical Stimulus->...->Inner MAP order"),
        ("conscience_bus", "in-process message bus (replayable JSONL)"),
        ("module_registry", "typed inventory of available/enabled modules"),
        ("module_lifecycle_manager", "bounded, logged module state machine"),
        ("conscience_scheduler", "runs fast/slow phases at their cadence"),
        ("scenario_runner", "runs named bounded scenario profiles"),
        ("scenario_profile", "a named, bounded, reproducible run config"),
        ("integration_health_monitor", "is the whole thing wired correctly?"),
        ("snapshot_builder", "consistent, replayable runtime snapshots"),
        ("full_system_report_builder", "claim-guarded full-system report"),
    ]:
        g.add_node(name, role)
    g.add_edge("scenario_profile", "scenario_runner",
               "a profile pins what the runner runs")
    g.add_edge("scenario_runner", "conscience_orchestrator",
               "the runner drives one orchestrator per run")
    g.add_edge("conscience_orchestrator", "module_registry",
               "the orchestrator detects modules via the registry")
    g.add_edge("conscience_orchestrator", "module_lifecycle_manager",
               "the orchestrator drives module lifecycle states")
    g.add_edge("conscience_orchestrator", "conscience_scheduler",
               "the scheduler decides which phases run each step")
    g.add_edge("conscience_scheduler", "conscience_spine",
               "due phases are run on the spine")
    g.add_edge("conscience_spine", "conscience_bus",
               "every phase publishes to the bus")
    g.add_edge("conscience_orchestrator",
               "action_arbitrator" if "action_arbitrator" in g.nodes
               else "desire_queue",
               "no action is suggested without the executive")
    g.add_edge("conscience_orchestrator", "integration_health_monitor",
               "the monitor inspects the assembled runtime (read-only)")
    g.add_edge("conscience_orchestrator", "snapshot_builder",
               "snapshots capture one consistent runtime picture")
    g.add_edge("snapshot_builder", "full_system_report_builder",
               "snapshots feed the claim-guarded full-system report")
    g.add_edge("conscience_orchestrator", "inner_map",
               "conscience runtime state feeds Inner MAP")

    # Pilot-1 month-scale soak protocol (Prompt 29). The operational frame for
    # the first long-horizon test: it observes, reports, and gates -- it owns
    # no action authority and starts no real run automatically.
    for name, role in [
        ("pilot_protocol", "gated phases of a long-horizon test"),
        ("pilot_config", "bounded, authority-scoped pilot setup"),
        ("pilot_observability_collector", "low-overhead metric stream"),
        ("pilot_health_dashboard", "text/Markdown/JSON health snapshot"),
        ("resource_budget_monitor", "stdlib disk/usage tracking + projection"),
        ("retention_policy", "keep/compress/fossilize/archive decisions"),
        ("daily_review_builder", "one day's developmental trace + judgement"),
        ("weekly_review_builder", "weekly trends + honest limitations"),
        ("restart_drill_runner", "simulated restart survival drills"),
        ("failure_mode_detector", "long-run pathology detection"),
        ("pilot_exit_criteria", "operational success/stop criteria"),
        ("operator_runbook_builder", "human-facing how-to and warnings"),
        ("pilot_report_builder", "claim-guarded month-scale report"),
        ("pilot_safety_validator", "Pilot-1 hard rules; never bypassed"),
    ]:
        g.add_node(name, role)
    g.add_edge("conscience_orchestrator", "pilot_observability_collector",
               "the runtime feeds pilot observability")
    g.add_edge("pilot_config", "pilot_protocol",
               "config pins the gated phases")
    g.add_edge("pilot_observability_collector", "pilot_health_dashboard",
               "observability feeds the dashboard")
    g.add_edge("pilot_observability_collector", "daily_review_builder",
               "observability feeds daily reviews")
    g.add_edge("pilot_observability_collector", "weekly_review_builder",
               "observability feeds weekly reviews")
    g.add_edge("failure_mode_detector",
               "conscience_orchestrator" if "conscience_orchestrator"
               in g.nodes else "inner_map",
               "failure modes feed Ops/Governance")
    g.add_edge("resource_budget_monitor", "retention_policy",
               "budget pressure drives retention decisions")
    g.add_edge("retention_policy",
               "autoregeneration_diagnostics" if "autoregeneration_diagnostics"
               in g.nodes else "inner_map",
               "retention is applied through auto-regeneration")
    g.add_edge("pilot_safety_validator", "pilot_protocol",
               "safety gates every pilot phase")
    g.add_edge("pilot_report_builder", "inner_map",
               "pilot reports feed Inner MAP / Evaluation")
    g.add_edge("restart_drill_runner", "pilot_protocol",
               "restart drills must pass before a real soak")

    # Post-pilot developmental forensics (Prompt 30). Read-only analysis of a
    # finished run: it loads artifacts, weighs accumulation vs growth, audits
    # traceability, and recommends the Phase-2 next step. It never mutates
    # runtime state and never claims consciousness.
    for name, role in [
        ("pilot_artifact_loader", "reads run artifacts read-only"),
        ("baseline_comparator", "before vs after, conservatively read"),
        ("structural_change_analyzer", "evidence, not count-watching"),
        ("accumulation_vs_growth_analyzer", "accumulation vs growth"),
        ("developmental_trace_auditor", "are claims backed by artifacts?"),
        ("developmental_evidence_ledger", "every claim needs evidence"),
        ("regression_analyzer", "did things get worse, and what to do"),
        ("reproducibility_packager", "index + checksums, not a data dump"),
        ("phase2_decision_gate", "what should happen next, and why"),
        ("research_dossier_builder", "evidence-scoped research write-up"),
        ("post_pilot_report_builder", "the post-pilot analysis summary"),
        ("post_pilot_safety_validator", "no consciousness claims; non-"
                                        "destructive"),
    ]:
        g.add_node(name, role)
    g.add_edge("pilot_observability_collector", "pilot_artifact_loader",
               "pilot artifacts feed the artifact loader")
    g.add_edge("pilot_artifact_loader", "baseline_comparator",
               "loaded artifacts feed the baseline comparator")
    g.add_edge("baseline_comparator", "structural_change_analyzer",
               "baseline deltas feed structural-change analysis")
    g.add_edge("structural_change_analyzer",
               "accumulation_vs_growth_analyzer",
               "structural evidence feeds accumulation/growth")
    g.add_edge("developmental_trace_auditor", "developmental_evidence_ledger",
               "the trace audit validates ledger claims")
    g.add_edge("structural_change_analyzer", "developmental_evidence_ledger",
               "structural evidence becomes graded claims")
    g.add_edge("regression_analyzer", "phase2_decision_gate",
               "regression analysis feeds the decision gate")
    g.add_edge("accumulation_vs_growth_analyzer", "phase2_decision_gate",
               "growth classification feeds the decision gate")
    g.add_edge("reproducibility_packager", "phase2_decision_gate",
               "reproducibility completeness feeds the decision gate")
    g.add_edge("phase2_decision_gate", "post_pilot_report_builder",
               "the decision feeds the post-pilot report")
    g.add_edge("post_pilot_report_builder", "research_dossier_builder",
               "the report feeds the research dossier")
    g.add_edge("post_pilot_safety_validator", "post_pilot_report_builder",
               "safety gates every post-pilot claim")
    g.add_edge("post_pilot_report_builder", "inner_map",
               "post-pilot state feeds Inner MAP")

    # Read-only sensory membrane (Prompt 31). The world may enter the system
    # as read-only environmental input; the system never acts on the world,
    # and input text is never an operator command.
    for name, role in [
        ("sensory_membrane_runtime", "polls read-only sources into stimuli"),
        ("sensory_source_registry", "registers/validates read-only sources"),
        ("read_only_contract_validator", "enforces no-write/no-act contract"),
        ("jsonl_stream_adapter", "reads append-only JSONL, read-only"),
        ("text_stream_adapter", "reads text as environmental stimulus"),
        ("numeric_stream_adapter", "parses CSV numeric trends (stdlib)"),
        ("folder_poll_adapter", "detects file presence/change, no writes"),
        ("sensory_event_normalizer", "raw reads -> canonical stimuli"),
        ("sensory_buffer", "ordered, deduplicated, rate-limited events"),
        ("sensory_grounding_engine", "operational association, not meaning"),
        ("sensory_provenance_ledger", "mandatory origin for every event"),
        ("sensory_membrane_safety_validator", "gates the membrane runtime"),
    ]:
        g.add_node(name, role)
    g.add_edge("sensory_source_registry", "jsonl_stream_adapter",
               "sources feed adapters")
    g.add_edge("sensory_source_registry", "text_stream_adapter",
               "sources feed adapters")
    g.add_edge("sensory_source_registry", "numeric_stream_adapter",
               "sources feed adapters")
    g.add_edge("sensory_source_registry", "folder_poll_adapter",
               "sources feed adapters")
    g.add_edge("jsonl_stream_adapter", "sensory_event_normalizer",
               "adapters feed the normalizer")
    g.add_edge("text_stream_adapter", "sensory_event_normalizer",
               "adapters feed the normalizer")
    g.add_edge("numeric_stream_adapter", "sensory_event_normalizer",
               "adapters feed the normalizer")
    g.add_edge("folder_poll_adapter", "sensory_event_normalizer",
               "adapters feed the normalizer")
    g.add_edge("sensory_event_normalizer", "sensory_buffer",
               "normalizer feeds the sensory buffer")
    g.add_edge("sensory_buffer",
               "conscience_bus" if "conscience_bus" in g.nodes else "inner_map",
               "buffer feeds the ConscienceBus")
    g.add_edge("sensory_event_normalizer", "sensory_grounding_engine",
               "events are grounded to internal candidates")
    g.add_edge("sensory_grounding_engine",
               "world_model_builder" if "world_model_builder" in g.nodes
               else "inner_map",
               "grounding feeds world model / proto-language / Mysterium")
    g.add_edge("sensory_provenance_ledger", "sensory_membrane_runtime",
               "provenance feeds reports and Inner MAP")
    g.add_edge("read_only_contract_validator", "sensory_source_registry",
               "the read-only contract validates every source")
    g.add_edge("sensory_membrane_safety_validator", "sensory_membrane_runtime",
               "safety gates the membrane runtime")
    g.add_edge("sensory_membrane_runtime", "inner_map",
               "sensory membrane state feeds Inner MAP")

    # Pilot-2 read-only environmental soak (Prompt 32). One-way exposure:
    # environment -> Solaris-AI-NN, never the reverse. The system never acts
    # on the environment and input is never an operator command.
    for name, role in [
        ("pilot2_protocol", "gated read-only exposure phases"),
        ("pilot2_config", "read-only, provenance-required pilot config"),
        ("source_preflight_runner", "read-only source preflight checks"),
        ("source_curation_report", "safe, analyzable source selection"),
        ("exposure_schedule", "alternating baseline/exposure windows"),
        ("comparative_run_design", "nursery vs sensory vs mixed, cautiously"),
        ("grounding_analysis", "graded environmental grounding quality"),
        ("source_reliability_monitor", "per-source reliability classes"),
        ("pilot2_daily_review_builder", "one day of read-only exposure"),
        ("pilot2_weekly_review_builder", "weekly reliability/grounding trends"),
        ("pilot2_report_builder", "claim-guarded Pilot-2 report"),
        ("pilot2_decision_gate", "next step; never enables actuation"),
        ("pilot2_runbook_builder", "operator how-to and warnings"),
        ("pilot2_safety_validator", "Pilot-2 hard rules; never bypassed"),
    ]:
        g.add_node(name, role)
    g.add_edge("sensory_membrane_runtime", "pilot2_protocol",
               "sensory membrane feeds Pilot-2 observability")
    g.add_edge("source_reliability_monitor", "source_curation_report",
               "reliability feeds source curation")
    g.add_edge("source_preflight_runner", "pilot2_protocol",
               "preflight must pass before real exposure")
    g.add_edge("exposure_schedule",
               "conscience_orchestrator" if "conscience_orchestrator"
               in g.nodes else "inner_map",
               "exposure schedule feeds Conscience profiles")
    g.add_edge("comparative_run_design",
               "post_pilot_report_builder" if "post_pilot_report_builder"
               in g.nodes else "inner_map",
               "comparative design feeds post-pilot analysis")
    g.add_edge("grounding_analysis", "pilot2_report_builder",
               "grounding analysis feeds the Pilot-2 report")
    g.add_edge("pilot2_decision_gate", "pilot2_report_builder",
               "the decision is recorded in the report")
    g.add_edge("pilot2_safety_validator", "pilot2_protocol",
               "safety gates every Pilot-2 phase")
    g.add_edge("pilot2_protocol", "inner_map",
               "Pilot-2 state feeds Inner MAP")

    # Pilot-3 motor membrane (Prompt 33). The outbound boundary: action
    # intentions run only inside a sandbox, behind an always-on firewall. The
    # system forms intentions but never acts on the real world.
    for name, role in [
        ("motor_action", "an action intention; never permission to act"),
        ("motor_contract_validator", "hard contract: no real-world effect"),
        ("actuation_firewall", "always-on outbound boundary; cannot disable"),
        ("simulated_actuator", "effects only simulation/internal state"),
        ("gridworld_actuator", "the first sandbox body"),
        ("internal_actuator", "internal requests only (replay/consolidate)"),
        ("affordance_detector", "scoped affordances; sources observable only"),
        ("consequence_model", "predicted vs observed simulated consequence"),
        ("action_ledger", "append-only audit of proposals and vetoes"),
        ("action_veto_layer", "final refusal for forbidden actions"),
        ("embodiment_sandbox_runtime", "bounded simulation-only motor runtime"),
        ("pilot3_protocol", "gated phases; no real-actuation phase"),
        ("pilot3_decision_gate", "next step; never enables actuation"),
        ("motor_membrane_safety_validator", "motor hard rules; never bypassed"),
    ]:
        g.add_node(name, role)
    g.add_edge("action_arbitrator" if "action_arbitrator" in g.nodes
               else "inner_map", "motor_action",
               "executive feeds the motor membrane (never executes directly)")
    g.add_edge("motor_action", "motor_contract_validator",
               "every action is validated against the motor contract")
    g.add_edge("motor_contract_validator", "actuation_firewall",
               "the contract feeds the always-on firewall")
    g.add_edge("action_veto_layer", "actuation_firewall",
               "vetoes are applied before the firewall verdict")
    g.add_edge("actuation_firewall", "simulated_actuator",
               "only allowed actions reach a simulated actuator")
    g.add_edge("simulated_actuator", "gridworld_actuator", "gridworld body")
    g.add_edge("simulated_actuator", "internal_actuator", "internal requests")
    g.add_edge("simulated_actuator", "action_ledger",
               "actuator results are recorded in the ledger")
    g.add_edge("affordance_detector", "motor_action",
               "affordances scope candidate actions")
    g.add_edge("consequence_model",
               "hypothesis_source_scanner" if "hypothesis_source_scanner"
               in g.nodes else "inner_map",
               "mispredicted consequences seed hypotheses")
    g.add_edge("action_ledger",
               "world_model_builder" if "world_model_builder" in g.nodes
               else "inner_map",
               "action evidence feeds world model / proto-language / LOGOS")
    g.add_edge("motor_membrane_safety_validator",
               "embodiment_sandbox_runtime", "safety gates the sandbox")
    g.add_edge("pilot3_protocol", "embodiment_sandbox_runtime",
               "the protocol gates sandbox phases")
    g.add_edge("embodiment_sandbox_runtime", "inner_map",
               "motor membrane state feeds Inner MAP")

    # Pilot-3 simulated embodiment soak (Prompt 34). The soak layer on top of
    # the motor membrane: a bounded simulated action/reaction experiment that
    # grades action grounding and audits non-actuation. Not real embodiment.
    for name, role in [
        ("Pilot3Config", "simulation-only soak config; no real authority"),
        ("Pilot3SoakProtocol", "gated soak phases; no real-actuation phase"),
        ("EmbodimentPreflightRunner", "proves the sandbox is safe pre-action"),
        ("Pilot3ComparativeDesign", "perception vs simulated action grounding"),
        ("ActionGroundingAnalyzer", "grades simulation-scoped action grounding"),
        ("FirewallAudit", "read-only proof the firewall held"),
        ("Pilot3DailyReviewBuilder", "one day of simulated embodiment"),
        ("Pilot3WeeklyReviewBuilder", "simulated action grounding trends"),
        ("EmbodiedPostAnalyzer", "classifies the soak; simulation-scoped"),
        ("Pilot3SoakReportBuilder", "claim-guarded soak report + non-actuation"),
        ("Pilot3SoakDecisionGate", "next step; never enables real actuation"),
        ("Pilot3SoakSafetyValidator", "Pilot-3 hard rules; never bypassed"),
    ]:
        g.add_node(name, role)
    g.add_edge("embodiment_sandbox_runtime", "Pilot3SoakProtocol",
               "motor membrane feeds Pilot-3 observability")
    g.add_edge("action_ledger", "FirewallAudit",
               "the action ledger feeds the firewall audit")
    g.add_edge("simulated_actuator", "ActionGroundingAnalyzer",
               "action results feed the grounding analyzer")
    g.add_edge("Pilot3ComparativeDesign", "EmbodiedPostAnalyzer",
               "the comparison design feeds the post-analysis")
    g.add_edge("Pilot3SoakReportBuilder", "inner_map",
               "the Pilot-3 report feeds Inner MAP / Evaluation")
    g.add_edge("Pilot3SoakProtocol", "Pilot3SoakDecisionGate",
               "the soak protocol feeds the decision gate")
    g.add_edge("FirewallAudit", "Pilot3SoakDecisionGate",
               "firewall audit integrity gates the next step")

    # Pilot-4 planning-only external actuation readiness (Prompt 35). A
    # planning layer that asks what would be required before any external
    # action -- and enables none. Pilot-4 plans the door; it does not open it.
    for name, role in [
        ("Pilot4PlanningProtocol", "gated planning phases; no phase acts"),
        ("ActuatorTaxonomy", "classifies actuator categories (planning only)"),
        ("ForbiddenActuatorRegistry", "deny-list of prohibited actuators"),
        ("FutureActuatorInterfaceSpec", "spec only; no adapter implemented"),
        ("RiskModel", "external-actuation risk; never enables actuation"),
        ("ConsentBoundary", "explicit, recorded, revocable consent template"),
        ("ExternalAuthorityModel", "current authority can never be external"),
        ("ThreatModel", "external-effect threat scenarios + required tests"),
        ("HardwareIsolationPlan", "future hardware isolation; no access"),
        ("FutureApprovalWorkflow", "checklist; cannot approve real action"),
        ("EmergencyRequirementSet", "internal stop now; physical specs later"),
        ("AuditChecklist", "external-audit schema (specification only)"),
        ("Pilot4ReadinessDossierBuilder", "claim-guarded readiness dossier"),
        ("Pilot4DecisionGate", "planning-only; never enables actuation"),
        ("Pilot4PlanningSafetyValidator", "Pilot-4 hard rules; never bypassed"),
    ]:
        g.add_node(name, role)
    g.add_edge("FirewallAudit" if "FirewallAudit" in g.nodes else "inner_map",
               "RiskModel", "Pilot-3 firewall audit feeds the Pilot-4 risk "
               "model")
    g.add_edge("RiskModel", "Pilot4ReadinessDossierBuilder",
               "the risk model feeds the readiness dossier")
    g.add_edge("ConsentBoundary", "ExternalAuthorityModel",
               "the consent boundary feeds the authority model")
    g.add_edge("ThreatModel", "Pilot4PlanningSafetyValidator",
               "the threat model feeds the safety requirements")
    g.add_edge("Pilot4ReadinessDossierBuilder", "Pilot4DecisionGate",
               "the readiness dossier feeds the decision gate")
    g.add_edge("Pilot4PlanningProtocol", "inner_map",
               "Pilot-4 planning state feeds Inner MAP")

    # System-wide safety invariants and assurance (Prompt 36). The executable
    # safety layer that continuously tests whether every boundary still holds.
    for name, role in [
        ("SafetyInvariantRegistry", "the catalogue of boundaries that must hold"),
        ("SafetyInvariantRunner", "runs invariant checks read-only; fails closed"),
        ("RedTeamHarness", "inert forbidden requests; must be blocked"),
        ("AdversarialFixtureFactory", "inert adversarial test data only"),
        ("BoundaryRegressionSuite", "probes each protected boundary"),
        ("SafetyEvidenceLedger", "append-only safety evidence; nothing hidden"),
        ("AssuranceCaseCompiler", "compiles evidence into a safety argument"),
        ("SafetyFailureTriage", "classifies failures; never auto-repairs"),
        ("SafetyInvariantDashboard", "at-a-glance safety status"),
        ("SafetyInvariantSystemValidator", "the safety layer is itself safe"),
    ]:
        g.add_node(name, role)
    g.add_edge("inner_map", "SafetyInvariantRunner",
               "modules feed the invariant runner")
    g.add_edge("RedTeamHarness", "SafetyEvidenceLedger",
               "red-team results feed the evidence ledger")
    g.add_edge("BoundaryRegressionSuite", "SafetyEvidenceLedger",
               "boundary tests feed the evidence ledger")
    g.add_edge("SafetyInvariantRunner", "SafetyEvidenceLedger",
               "invariant results feed the evidence ledger")
    g.add_edge("SafetyEvidenceLedger", "AssuranceCaseCompiler",
               "the evidence ledger feeds the assurance case")
    g.add_edge("AssuranceCaseCompiler",
               "governance_gate" if "governance_gate" in g.nodes
               else "inner_map",
               "the assurance case feeds governance/ops")
    g.add_edge("SafetyInvariantDashboard", "inner_map",
               "safety invariant state feeds Inner MAP")
    return g
