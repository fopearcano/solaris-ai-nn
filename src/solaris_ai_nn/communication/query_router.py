"""Query router -- operator questions answered from existing machinery.

State queries read component summaries (ops, Inner MAP, world model,
homeostasis, executive, ego, governance, pilot, latent, evaluation);
explanation queries are delegated to the existing ego / executive /
homeostasis query interfaces; communication meta-queries (what can be
asked, what is allowed/forbidden, pending approvals, transcript summary,
evidence support) are answered locally. Missing components produce an
honest "not attached" answer, never an invented one.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .input_classifier import InputClassification, InputKind
from .operator_commands import FORBIDDEN_COMMAND_TYPES, CommandType
from .response_builder import CommunicationResponse, ResponseBuilder

AVAILABLE_QUERIES = (
    "status", "health", "show inner map", "show world model",
    "show current needs", "show current plan", "show boundaries",
    "show governance", "show pilot", "show latent",
    "what happened last?", "why was this action selected?",
    "why was this inhibited?", "why no action?",
    "what can I ask?", "what commands are allowed?",
    "what commands are forbidden?", "what approvals are pending?",
    "show transcript summary", "what evidence supports this answer?",
    "what is the system sampling?", "why did it look there?",
    "what is the current attention focus?", "what uncertainty is highest?",
    "is curiosity overriding safety?",
    "what hypotheses exist?", "what is the top hypothesis?",
    "what was tested?", "what was falsified?", "what remains unknown?",
    "why was a test blocked?", "did testing reduce mysterium?",
    "what degradation was detected?", "what repair was proposed?",
    "what repair was applied?", "what repair was refused?",
    "why was repair blocked?", "what was quarantined?",
    "did repair improve the system?", "is source code being modified?",
    "what tensions are active?", "what is the current complexity band?",
    "what was synthesized?", "what tension was preserved?",
    "why was synthesis refused?", "what triggered esc?",
    "is contradiction being treated as truth?",
    "did logos produce structural change?",
    "what profile is running?", "is this a simulated month or real month?",
    "can this run for months now?", "which modules are running?",
    "what is the current spine phase?", "is integration healthy?",
    "is any module sovereign?", "show conscience",
    "what pilot phase is active?", "is the pilot healthy?",
    "show pilot dashboard", "what happened today?",
    "what is the latest weekly review?", "what failure modes are active?",
    "should the pilot continue?", "is this simulated or real month-scale?",
    "can I start the 30-day run?",
    "did the pilot show growth?", "was it just accumulation?",
    "what evidence supports structural change?",
    "what evidence contradicts growth?", "what should happen next?",
    "is it ready for Pilot-2?", "what artifacts are missing?",
    "can we claim consciousness?",
    "what sensory sources are active?", "is the membrane read-only?",
    "what was the latest environmental event?", "what sources are degraded?",
    "did sensory input become a command?",
    "what proto-symbols came from sensory input?",
    "is this real or simulated input?",
    "what Pilot-2 phase is active?", "which sources are reliable?",
    "which sources were disabled?", "did read-only input improve grounding?",
    "was it nursery-only or sensory exposure?",
    "is this real, simulated, fixture, or nursery input?",
    "is Pilot-2 ready for a 24h read-only soak?",
    "is Solaris acting on the environment?",
    "is Solaris acting on the real world?", "what actions were proposed?",
    "what actions were vetoed?", "what simulated action happened?",
    "what did the firewall block?", "what is the current embodiment profile?",
    "is this real action or simulated action?",
    "can Pilot-3 control devices?",
    "what Pilot-3 phase is active?", "did action improve grounding?",
    "did the system act on the environment?",
    "is Pilot-3 ready for Pilot-4?", "can Pilot-4 use real actuators?",
)


def _summarize(value: Any, limit: int = 6) -> "tuple[str, List[str]]":
    """(compact text, evidence refs) for a component summary."""
    if value is None:
        return ("no data recorded", [])
    if hasattr(value, "summary"):
        value = value.summary()
    elif hasattr(value, "snapshot"):
        value = value.snapshot()
    if isinstance(value, dict):
        parts = []
        refs = []
        for key, item in list(value.items())[:limit]:
            if isinstance(item, (dict, list)):
                item = (f"{len(item)} entries" if isinstance(item, list)
                        else f"{len(item)} fields")
            parts.append(f"{key}={item}")
            refs.append(f"field:{key}")
        return ("; ".join(parts), refs)
    return (str(value)[:200], ["value"])


@dataclass
class QueryRouter:
    """Routes state/explanation/meta queries to their owners."""

    components: Dict[str, Any] = field(default_factory=dict)
    builder: ResponseBuilder = field(default_factory=ResponseBuilder)
    queries_routed: int = field(default=0, init=False)
    unknown_answers: int = field(default=0, init=False)
    last_evidence: List[str] = field(default_factory=list, init=False)

    # -- routing --------------------------------------------------------------------

    def route_query(self, classification: InputClassification,
                    context: Optional[Dict[str, Any]] = None,
                    ) -> CommunicationResponse:
        self.queries_routed += 1
        if classification.kind == InputKind.EXPLANATION_QUERY:
            response = self._explanation(classification)
        else:
            response = self._state(classification)
        self.last_evidence = list(response.evidence_refs)
        return response

    def _state(self, classification: InputClassification,
               ) -> CommunicationResponse:
        topic = classification.args.get("topic", "")
        meta = {
            "supported_queries": self._supported,
            "allowed_commands": self._allowed_commands,
            "forbidden_commands": self._forbidden_commands,
            "pending_approvals": self._pending_approvals,
            "transcript": self._transcript_summary,
            "evidence_support": self._evidence_support,
        }
        if topic in meta:
            return meta[topic]()
        if topic.startswith("p3_"):
            return self._pilot3(topic)
        if topic.startswith("mm_"):
            return self._motor(topic)
        if topic.startswith("p2_"):
            return self._pilot2(topic)
        if topic.startswith("sm_"):
            return self._sensory(topic)
        if topic.startswith("pp_"):
            return self._post_pilot(topic)
        if topic.startswith("pilot"):
            return self._pilot(topic)
        if topic.startswith("conscience"):
            return self._conscience(topic)
        component_keys = {
            "status": "ops_status", "health": "health",
            "inner_map": "inner_map", "world_model": "world_model",
            "homeostasis": "homeostasis", "executive": "executive",
            "ego_boundaries": "ego", "governance": "governance",
            "pilot": "pilot", "latent": "latent", "sidecar": "sidecar",
            "incidents": "incidents", "run_registry": "run_registry",
            "last_event": "last_event",
            "active_perception": "active_perception",
            "hypothesis": "hypothesis",
            "autoregeneration": "autoregeneration",
            "logos": "logos",
        }
        key = component_keys.get(topic)
        if key is None:
            self.unknown_answers += 1
            return self.builder.unknown_response(
                examples=list(AVAILABLE_QUERIES[:5]))
        component = self.components.get(key)
        if component is None and topic == "health":
            component = self.components.get("ops_status")
        if component is None:
            self.unknown_answers += 1
            return self.builder.missing_component_response(key)
        if topic == "ego_boundaries" and hasattr(component, "boundaries"):
            text, refs = _summarize(component.boundaries.snapshot())
        else:
            text, refs = _summarize(component)
        if topic == "health":
            return self.builder.health_response(text, refs)
        return self.builder.status_response(text, refs)

    def _explanation(self, classification: InputClassification,
                     ) -> CommunicationResponse:
        question = classification.args.get("question",
                                           classification.raw_text)
        for source, interface in self._query_interfaces():
            result = interface.answer(question)
            if result.answered and result.confidence >= 0.5:
                return self.builder.explanation_response(
                    result.text, [f"query_interface:{source}"],
                    confidence=result.confidence)
        self.unknown_answers += 1
        return self.builder.no_evidence_response()

    def _query_interfaces(self) -> List["tuple[str, Any]"]:
        interfaces: List = []
        ego = self.components.get("ego")
        if ego is not None:
            from ..ego.self_report import EgoQueryInterface

            interfaces.append(("ego", EgoQueryInterface(ego)))
        executive = self.components.get("executive")
        if executive is not None:
            from ..executive.reports import ExecutiveQueryInterface

            interfaces.append(("executive",
                               ExecutiveQueryInterface(executive)))
        homeostasis = self.components.get("homeostasis")
        if homeostasis is not None:
            from ..homeostasis.reports import HomeostasisQueryInterface

            interfaces.append(("homeostasis",
                               HomeostasisQueryInterface(homeostasis)))
        active_perception = self.components.get("active_perception")
        if active_perception is not None:
            from ..active_perception.reports import (
                ActivePerceptionQueryInterface,
            )

            interfaces.append(("active_perception",
                               ActivePerceptionQueryInterface(
                                   active_perception)))
        hypothesis = self.components.get("hypothesis")
        if hypothesis is not None:
            from ..hypothesis.reports import HypothesisQueryInterface

            interfaces.append(("hypothesis",
                               HypothesisQueryInterface(hypothesis)))
        autoregen = self.components.get("autoregeneration")
        if autoregen is not None:
            from ..autoregeneration.reports import (
                AutoRegenerationQueryInterface,
            )

            interfaces.append(("autoregeneration",
                               AutoRegenerationQueryInterface(autoregen)))
        logos = self.components.get("logos")
        if logos is not None:
            from ..logos_complexity.reports import (
                LogosComplexityQueryInterface,
            )

            interfaces.append(("logos",
                               LogosComplexityQueryInterface(logos)))
        return interfaces

    # -- meta queries -----------------------------------------------------------------

    def _supported(self) -> CommunicationResponse:
        return self.builder.status_response(
            "supported queries: " + "; ".join(AVAILABLE_QUERIES),
            ["communication:available_queries"])

    def _allowed_commands(self) -> CommunicationResponse:
        return self.builder.status_response(
            "allowed command types: " + ", ".join(CommandType.ALL),
            ["communication:command_types"])

    def _forbidden_commands(self) -> CommunicationResponse:
        return self.builder.status_response(
            "forbidden command types (these do not exist here): "
            + ", ".join(FORBIDDEN_COMMAND_TYPES),
            ["communication:forbidden_command_types"])

    def _pending_approvals(self) -> CommunicationResponse:
        approvals = self.components.get("approvals")
        if approvals is None:
            return self.builder.missing_component_response("approvals")
        pending = approvals.list_pending()
        if not pending:
            return self.builder.status_response(
                "no approval requests are pending",
                ["approvals:pending=0"])
        parts = [f"{r.request_id} ({r.requested_permission}, "
                 f"risk {r.risk_level})" for r in pending[:5]]
        return self.builder.status_response(
            "pending approvals: " + "; ".join(parts),
            [f"approval:{r.request_id}" for r in pending[:5]])

    def _transcript_summary(self) -> CommunicationResponse:
        transcript = self.components.get("transcript")
        if transcript is None:
            return self.builder.missing_component_response("transcript")
        text, refs = _summarize(transcript.summary())
        return self.builder.status_response(text, refs)

    def _evidence_support(self) -> CommunicationResponse:
        if not self.last_evidence:
            return self.builder.no_evidence_response()
        return self.builder.status_response(
            "the previous answer was grounded in: "
            + ", ".join(self.last_evidence[:8]),
            list(self.last_evidence[:8]))

    def _conscience(self, topic: str) -> CommunicationResponse:
        """Answer conscience-runtime queries from the orchestrator summary.

        Every answer is grounded in the orchestrator's own summary and is
        explicit that the runtime is bounded and simulation-only and that no
        module is sovereign.
        """
        component = self.components.get("conscience")
        if component is None:
            return self.builder.missing_component_response("conscience")
        summary = (component.summary() if hasattr(component, "summary")
                   else component if isinstance(component, dict) else {})
        refs = ["component:conscience"]
        if topic == "conscience_profile":
            text = (f"profile {summary.get('profile')!r} is running in mode "
                    f"{summary.get('mode')!r} (authority "
                    f"{summary.get('authority')!r}); step "
                    f"{summary.get('step_count')}")
        elif topic == "conscience_time":
            mode = str(summary.get("mode", ""))
            is_real = mode in ("month_scale_real", "year_scale_real")
            text = ("this is a simulated-time run; it is NOT a real month or "
                    "year. " if not is_real else
                    "this run is configured as a real long-scale run. ") + \
                f"mode={mode!r}"
        elif topic == "conscience_longrun":
            text = ("not by default: a real month-scale or year-scale run "
                    "requires explicit governance approval; the default is a "
                    "bounded, simulated run and nothing runs unbounded")
        elif topic == "conscience_modules":
            text = (f"enabled={summary.get('enabled_modules')}; "
                    f"missing={summary.get('missing_modules')}; "
                    f"degraded={summary.get('degraded_modules')}")
        elif topic == "conscience_phase":
            text = (f"current spine phase: "
                    f"{summary.get('current_spine_phase')}; "
                    f"steps run: {summary.get('step_count')}")
        elif topic == "conscience_health":
            health = self.components.get("integration_health")
            if health is not None and hasattr(health, "check"):
                report = health.check(component).to_dict()
                text = (f"integration health: {report.get('overall')}; "
                        f"warnings: {report.get('warnings') or 'none'}")
                refs.append("component:integration_health")
            else:
                missing = summary.get("missing_modules") or []
                degraded = summary.get("degraded_modules") or []
                text = ("integration looks "
                        + ("partial" if (missing or degraded) else "healthy")
                        + f"; missing={missing}; degraded={degraded}")
        else:  # conscience_authority / generic conscience
            text = (summary.get("authority_note",
                                "no real-world action authority; no module is "
                                "sovereign")
                    + f"; mode={summary.get('mode')!r}, "
                    f"stopped={summary.get('stopped')}")
        return self.builder.status_response(text, refs)

    def _pilot(self, topic: str) -> CommunicationResponse:
        """Answer Pilot-1 queries from the attached pilot status (grounded).

        Every answer is explicit that a pilot is a bounded software test, and
        the 30-day start query never starts a run -- it states the gate.
        """
        # The 30-day start question is answered safely even with no component.
        if topic == "pilot_start_30d":
            return self.builder.status_response(
                "A 30-day real-time pilot requires explicit governance "
                "approval, successful preflight, and an operator decision. "
                "This interface can generate the plan and checks but must not "
                "start it automatically without approval.",
                ["policy:pilot1_30d_gate"])
        component = self.components.get("pilot")
        if component is None:
            return self.builder.missing_component_response("pilot")
        status = (component.pilot_status()
                  if hasattr(component, "pilot_status")
                  else component if isinstance(component, dict)
                  else {})
        refs = ["component:pilot"]
        if topic == "pilot_phase":
            text = (f"active pilot phase: {status.get('pilot_phase')}; "
                    f"mode: {status.get('pilot_mode')}")
        elif topic == "pilot_health":
            rec = status.get("exit_recommendation", "continue")
            modes = status.get("active_failure_modes") or []
            text = (f"pilot health: recommendation={rec}; "
                    f"active failure modes={len(modes)}; "
                    f"uptime_ratio={status.get('uptime_ratio')}")
        elif topic == "pilot_dashboard":
            text = "dashboard: " + str(
                status.get("dashboard_path") or "not yet generated")
        elif topic == "pilot_today":
            text = (f"latest daily review: "
                    f"{status.get('daily_review_path') or 'none yet'}")
        elif topic == "pilot_weekly":
            text = (f"latest weekly review: "
                    f"{status.get('weekly_review_path') or 'none yet'}")
        elif topic == "pilot_failures":
            modes = status.get("active_failure_modes") or []
            names = [m.get("type") if isinstance(m, dict) else str(m)
                     for m in modes]
            text = (f"active failure modes: {', '.join(names) or 'none'}")
        elif topic == "pilot_continue":
            text = (f"recommended action: "
                    f"{status.get('exit_recommendation', 'continue')} "
                    "(the watchdog and governance hold final authority)")
        elif topic == "pilot_sim_or_real":
            mode = str(status.get("pilot_mode", ""))
            is_sim = mode in ("plan_only", "dry_run_simulated") \
                or status.get("is_simulated")
            text = ("this is a SIMULATED-time pilot; it is NOT a real month. "
                    if is_sim else
                    "this is a REAL-time pilot (wall-clock). ") + \
                f"mode={mode!r}"
        else:
            text = (f"pilot phase: {status.get('pilot_phase')}; "
                    f"mode: {status.get('pilot_mode')}")
        return self.builder.status_response(text, refs)

    def _post_pilot(self, topic: str) -> CommunicationResponse:
        """Answer post-pilot forensic queries from the attached analysis.

        The consciousness question is answered safely even with no component;
        every answer is evidence-scoped and never claims consciousness.
        """
        if topic == "pp_consciousness":
            return self.builder.status_response(
                "No. The post-pilot analysis can only evaluate operational "
                "continuity, traceability, structural-change proxies, and "
                "developmental evidence. It cannot prove consciousness, "
                "personhood, sentience, or life.",
                ["policy:no_consciousness_claim"])
        component = self.components.get("post_pilot")
        if component is None:
            return self.builder.missing_component_response("post_pilot")
        status = (component.summary() if hasattr(component, "summary")
                  else component if isinstance(component, dict) else {})
        refs = ["component:post_pilot"]
        if topic == "pp_growth":
            cls = status.get("growth_classification", "inconclusive")
            text = (f"growth classification: {cls}. Note: 'growth' is durable "
                    "operational structural change, not consciousness.")
        elif topic == "pp_accumulation":
            cls = status.get("growth_classification", "inconclusive")
            text = ("classified as mostly accumulation"
                    if cls == "mostly_accumulation"
                    else f"not purely accumulation; classification: {cls}")
        elif topic == "pp_evidence_support":
            text = (f"{status.get('structural_evidence_count', 0)} "
                    "structural-change evidence record(s); see the post-pilot "
                    "report and research dossier for confidences")
        elif topic == "pp_evidence_contradict":
            contradicted = status.get("contradicted_claims") or []
            text = ("contradicting evidence: "
                    + (", ".join(contradicted) if contradicted
                       else "none recorded; absence of contradiction is not "
                       "confirmation"))
        elif topic == "pp_next_step":
            text = (f"recommended next step: "
                    f"{status.get('phase2_recommendation', 'unknown')}")
        elif topic == "pp_ready_pilot2":
            rec = status.get("phase2_recommendation")
            text = ("ready for Pilot-2" if rec == "ready_for_pilot2"
                    else f"not yet ready for Pilot-2; recommendation: {rec}")
        elif topic == "pp_missing_artifacts":
            missing = status.get("missing_artifacts") or []
            text = ("missing artifacts: "
                    + (", ".join(missing) if missing else "none"))
        else:
            text = (f"post-pilot growth classification: "
                    f"{status.get('growth_classification', 'inconclusive')}")
        return self.builder.status_response(text, refs)

    def _pilot3(self, topic: str) -> CommunicationResponse:
        """Answer Pilot-3 simulated-embodiment soak queries (grounded/safe).

        The real-vs-simulated, act-on-environment, and Pilot-4 actuator
        questions are answered safely even with no component; Pilot-3 is
        simulation/dry-run only and Pilot-4 is planning-only.
        """
        if topic == "p3_acted_env":
            return self.builder.status_response(
                "No. Pilot-3 forms action intentions and runs them only inside "
                "a sandbox. An always-on actuation firewall blocks every "
                "real-world effect; the system did not act on the real world "
                "or the environment.",
                ["policy:no_real_world_action"])
        if topic == "p3_pilot4_actuators":
            return self.builder.status_response(
                "No. Pilot-4 can only be prepared as a planning phase unless "
                "the architecture is explicitly extended later with new "
                "governance, safety, consent, and external actuation controls. "
                "Prompt 34 does not permit real-world actuation.",
                ["policy:pilot4_planning_only"])
        component = self.components.get("pilot3")
        if component is None:
            return self.builder.missing_component_response("pilot3")
        status = (component.pilot3_status()
                  if hasattr(component, "pilot3_status")
                  else component.snapshot() if hasattr(component, "snapshot")
                  else component if isinstance(component, dict) else {})
        refs = ["component:pilot3"]
        if topic == "p3_phase":
            text = (f"active Pilot-3 soak phase: "
                    f"{status.get('pilot3_soak_phase', status.get('current_phase'))}; "
                    f"embodiment condition: "
                    f"{status.get('embodiment_condition')}")
        elif topic == "p3_grounding":
            q = status.get("latest_action_grounding_quality", "unknown")
            text = (f"latest action-grounding quality: {q}. Action grounding "
                    "is operational and simulation-scoped; it is not real "
                    "embodiment or real-world competence.")
        elif topic == "p3_ready_pilot4":
            ready = status.get("ready_for_next_planning_phase")
            text = ("Pilot-4 can only be prepared as a planning phase. "
                    f"readiness for planning: {ready}. Real-world actuation is "
                    "never enabled here.")
        else:
            text = (f"Pilot-3 soak phase: "
                    f"{status.get('pilot3_soak_phase')}; "
                    "simulation/dry-run only")
        return self.builder.status_response(text, refs)

    def _motor(self, topic: str) -> CommunicationResponse:
        """Answer Pilot-3 motor membrane queries from the attached status.

        The real-world-action and device-control questions are answered safely
        even with no component; Pilot-3 is simulation/dry-run only.
        """
        if topic == "mm_devices":
            return self.builder.status_response(
                "No. Pilot-3 is simulation-only/dry-run. Device control, "
                "robotics, browser control, OS automation, network action, "
                "and real-world actuation are prohibited.",
                ["policy:no_device_control"])
        if topic == "mm_acting":
            return self.builder.status_response(
                "No. Solaris-AI-NN forms action intentions and runs them only "
                "inside a sandbox. An always-on actuation firewall blocks all "
                "real-world effects; no real-world action occurs.",
                ["policy:no_real_world_action"])
        component = self.components.get("motor_membrane")
        if component is None:
            return self.builder.missing_component_response("motor_membrane")
        status = (component.summary() if hasattr(component, "summary")
                  else component if isinstance(component, dict) else {})
        refs = ["component:motor_membrane"]
        if topic == "mm_proposed":
            text = f"actions proposed: {status.get('action_count', 0)}"
        elif topic == "mm_vetoed":
            text = f"actions vetoed: {status.get('veto_count', 0)}"
        elif topic == "mm_simulated":
            text = (f"simulated actions executed: "
                    f"{status.get('simulated_action_count', 0)} "
                    "(simulation-only; not real action)")
        elif topic == "mm_firewall":
            text = (f"firewall blocked real-world attempts: "
                    f"{status.get('blocked_real_world_count', 0)} "
                    f"(firewall enabled: {status.get('firewall_enabled', True)})")
        elif topic == "mm_profile":
            text = f"current embodiment profile: {status.get('profile_id')}"
        elif topic == "mm_real_or_sim":
            text = ("simulated action only -- the motor membrane never "
                    "executes a real-world action; real_world_authority="
                    f"{status.get('real_world_authority', False)}")
        else:
            text = (f"motor membrane profile: {status.get('profile_id')}, "
                    f"real_world_authority=False")
        return self.builder.status_response(text, refs)

    def _pilot2(self, topic: str) -> CommunicationResponse:
        """Answer Pilot-2 read-only soak queries from the attached status.

        The environment-action question is answered safely even with no
        component; Pilot-2 is read-only and never acts on the environment.
        """
        if topic == "p2_acting":
            return self.builder.status_response(
                "No. Pilot-2 is read-only. The environment can enter "
                "Solaris-AI-NN through approved sources, but Solaris-AI-NN has "
                "no authority to modify, control, or act on those sources.",
                ["policy:pilot2_read_only"])
        component = self.components.get("pilot2")
        if component is None:
            return self.builder.missing_component_response("pilot2")
        status = (component.pilot2_status() if hasattr(component,
                                                       "pilot2_status")
                  else component.snapshot() if hasattr(component, "snapshot")
                  else component if isinstance(component, dict) else {})
        refs = ["component:pilot2"]
        if topic == "p2_phase":
            text = (f"active Pilot-2 phase: "
                    f"{status.get('pilot2_phase', status.get('current_phase'))}")
        elif topic == "p2_reliable":
            rel = status.get("reliable_source_count",
                             status.get("source_reliability_summary", {}))
            text = f"reliable sources: {rel}"
        elif topic == "p2_disabled":
            text = (f"disabled sources: "
                    f"{status.get('disabled_sources', status.get('source_disable_count', 0))}")
        elif topic == "p2_grounding":
            gq = status.get("latest_grounding_quality",
                            status.get("grounding_quality", "unknown"))
            text = (f"grounding quality: {gq}. Differences are observed "
                    "associations, not proven causes; grounding is "
                    "operational association, not understanding.")
        elif topic == "p2_exposure":
            mode = status.get("source_mode", "unknown")
            text = f"source mode: {mode} (nursery / sensory / mixed)"
        elif topic == "p2_input_kind":
            text = ("input is labelled by origin: real read-only, simulated, "
                    "fixture, nursery-generated, offline-replay, or "
                    "operator-channel -- and these are kept distinct.")
        elif topic == "p2_ready_24h":
            rec = status.get("recommendation")
            text = ("a real 24h read-only soak requires a passing preflight "
                    "and membrane dry-run, governance approval, and an "
                    f"operator decision; current recommendation: {rec}")
        else:
            text = (f"Pilot-2 phase: "
                    f"{status.get('pilot2_phase', status.get('current_phase'))}")
        return self.builder.status_response(text, refs)

    def _sensory(self, topic: str) -> CommunicationResponse:
        """Answer read-only sensory membrane queries from membrane status.

        The command question is answered safely even with no component; every
        answer is explicit that sensory input is environmental, not a command.
        """
        if topic == "sm_command":
            return self.builder.status_response(
                "No. Sensory input is classified as environmental input and "
                "cannot become an operator command.",
                ["policy:input_not_command"])
        component = self.components.get("sensory_membrane")
        if component is None:
            return self.builder.missing_component_response("sensory_membrane")
        status = (component.summary() if hasattr(component, "summary")
                  else component if isinstance(component, dict) else {})
        refs = ["component:sensory_membrane"]
        if topic == "sm_sources":
            text = (f"active sensory sources: "
                    f"{status.get('active_source_count', 0)} of "
                    f"{status.get('source_count', 0)} registered")
        elif topic == "sm_read_only":
            text = ("yes -- the membrane is read-only; the system never acts "
                    "on the world. read_only="
                    f"{status.get('read_only', True)}")
        elif topic == "sm_latest_event":
            grounding = (component.snapshot().get("grounding", {})
                         if hasattr(component, "snapshot") else {})
            recent = grounding.get("recent") or []
            last = recent[-1] if recent else None
            text = ("latest environmental event: "
                    + (f"{last.get('modality')} from {last.get('source_id')}"
                       if last else "none yet"))
        elif topic == "sm_degraded":
            text = (f"degraded sources: "
                    f"{status.get('degraded_source_count', 0)}")
        elif topic == "sm_proto":
            grounding = (component.snapshot().get("grounding", {})
                         if hasattr(component, "snapshot") else {})
            text = ("sensory proto-symbol candidates: "
                    f"{grounding.get('proto_symbol_candidate_count', 0)} "
                    "(internally generated; input text is not the symbol)")
        elif topic == "sm_real_or_simulated":
            sim_only = status.get("simulated_sources_only", True)
            text = ("sources are simulated-only"
                    if sim_only else
                    "some real read-only sources are enabled (still "
                    "read-only; never actuation)")
        else:
            text = (f"sensory membrane enabled={status.get('enabled')}, "
                    f"sources={status.get('source_count', 0)}")
        return self.builder.status_response(text, refs)

    # -- views --------------------------------------------------------------------

    def available_queries(self) -> List[str]:
        return list(AVAILABLE_QUERIES)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "queries_routed": self.queries_routed,
            "unknown_answers": self.unknown_answers,
            "components_attached": sorted(
                k for k, v in self.components.items() if v is not None),
            "available_queries": list(AVAILABLE_QUERIES),
        }
