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
    "is real-world actuation enabled?", "what does Pilot-4 allow?",
    "what actions are forbidden?",
    "what would be required before real actuation?",
    "is Pilot-4 approval to use actuators?",
    "what is the current readiness conclusion?",
    "can Solaris control devices now?", "can we connect a robot?",
    "are the safety invariants passing?", "what red-team tests failed?",
    "what boundaries are protected?",
    "is real-world actuation still blocked?",
    "did any module bypass the orchestrator?",
    "is Pilot-4 still planning-only?", "can safety checks be disabled?",
    "can failed safety evidence be hidden?",
    "which modules actually helped?", "which modules were harmful?",
    "did the full system beat the baseline?", "what ablations were tested?",
    "what was inconclusive?", "what should be removed?",
    "what should be tested again?", "is this a consciousness benchmark?",
    "which modules should we keep?", "which modules should be pruned?",
    "which modules need revision?", "what evidence supports pruning?",
    "what evidence contradicts pruning?", "what is the compiled roadmap?",
    "what design debt exists?", "did the system modify its own code?",
    "can it prune modules automatically?",
    "what profiles can I run?", "what should I do next?",
    "can I run everything?", "can I approve real-world actuation?",
    "can I delete old evidence?",
    "what does Solaris do in the minimal organism demo?",
    "did its perception change?", "did it beat the passive parser?",
    "did it create proto-symbols?", "what did the demo not prove?",
    "what live feeders are available?", "which sources are silent?",
    "is live field mode allowed?",
    "what did Solaris perceive from the live field?",
    "did Solaris control any hardware?",
    "did Solaris modify any source files?",
    "did human-like and non-human senses produce different structures?",
    "did labels contaminate the result?", "which modality actually mattered?",
    "was this a consciousness test?",
    "what feeders are available?", "are any feeders active?",
    "does Solaris control the feeders?", "can Solaris start the SDR feeder?",
    "is Solaris overloaded?", "is Solaris sensorily deprived?",
    "what does Solaris need perceptually?", "which source dominates its diet?",
    "does it need consolidation?", "are these needs feelings?",
    "what concepts has Solaris formed?", "are these human concepts?",
    "which concepts are stable?", "which concepts decayed?",
    "what world is forming?",
    "did human labels contaminate concept formation?",
    "does this prove understanding?",
    "what signs has Solaris formed?", "are these words?",
    "what is Solaris' private language?", "can you translate its signs?",
    "did human labels contaminate signs?",
    "does this prove language understanding?",
    "what is Solaris thinking?", "what did Solaris predict?",
    "what did Solaris get wrong?", "what questions does Solaris have?",
    "is this human language reasoning?",
    "what is Solaris' self-boundary?",
    "what belongs to Solaris and what belongs to the world?",
    "does Solaris have a body?", "did it confuse simulation with observation?",
    "did it maintain continuity after restart?",
    "does this prove self-awareness?",
    "what does Solaris want?", "what desires are active?", "did Solaris act?",
    "why did it choose no action?", "were any desires blocked?",
    "are these emotions?", "does this prove agency?",
    "what did Solaris do?", "what happened after it acted?",
    "did the action help?", "what habits formed?",
    "what actions were inhibited?", "did it act in the real world?",
    "is Solaris developing?", "what changed over time?", "did it mature?",
    "is it stuck?", "did it regress?", "is this just log accumulation?",
    "does this prove life or consciousness?",
    "is the soak ready?", "what stage is the soak in?",
    "what happened today in the soak?", "what changed this week?",
    "did Solaris develop?", "did the controls differ?", "did safety hold?",
    "does this prove consciousness or life?",
    "did the result replicate?", "which structures replicated?",
    "which claims were falsified?", "did live flux matter?",
    "did labels contaminate development?", "was this just fixture overfit?",
    "which run diverged and why?", "does replication prove consciousness?",
    "what implementation prompts are ready?", "which experiments are blocked?",
    "why is this branch spec blocked?", "what should I give Claude Code next?",
    "what tests must pass?", "did Solaris create a branch?",
    "did Solaris rewrite itself?",
    "is this implementation ready to merge?", "what blocks the merge?",
    "did it satisfy the spec?", "which tests failed?",
    "did it introduce a safety regression?", "did Solaris merge the PR?",
    "did Solaris edit the code?",
    "what is the current baseline?", "was the merge assimilated?",
    "did the new baseline regress?", "should I rollback?",
    "what validation is missing?", "is the new baseline ready for soak?",
    "did Solaris merge this?", "did Solaris run Git?",
    "what is the current research baseline?", "is this baseline validated?",
    "what are its limitations?", "how do I reproduce it?",
    "what should I run next?", "is this a release?",
    "did Solaris create a Git tag?", "does this prove consciousness?",
    "where is the research program in its cycle?",
    "what is the next action?", "what is blocked?",
    "what evidence is missing?", "what operator decision is required?",
    "did the cycle complete?", "did Solaris approve itself?",
    "did Solaris run Git or GitHub?",
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
        if topic.startswith("rc_"):
            return self._research_cycle(topic)
        if topic.startswith("rb_"):
            return self._research_baseline(topic)
        if topic.startswith("pm_"):
            return self._post_merge_assimilation(topic)
        if topic.startswith("ii_"):
            return self._implementation_intake(topic)
        if topic.startswith("ec_"):
            return self._experiment_compiler(topic)
        if topic.startswith("rp_"):
            return self._developmental_replication(topic)
        if topic.startswith("sk_"):
            return self._developmental_soak(topic)
        if topic.startswith("dl_"):
            return self._developmental_life(topic)
        if topic.startswith("ar_"):
            return self._action_reaction(topic)
        if topic.startswith("df_"):
            return self._desire_formation(topic)
        if topic.startswith("sb_"):
            return self._self_boundary(topic)
        if topic.startswith("cg_"):
            return self._cognition(topic)
        if topic.startswith("sg_"):
            return self._semiogenesis(topic)
        if topic.startswith("po_"):
            return self._ontogenesis(topic)
        if topic.startswith("pm_"):
            return self._metabolism(topic)
        if topic.startswith("fs_"):
            return self._feeder_sdk(topic)
        if topic.startswith("sl_"):
            return self._sensorium_lab(topic)
        if topic.startswith("lf_"):
            return self._live_field(topic)
        if topic.startswith("od_"):
            return self._organism_demo(topic)
        if topic.startswith("ps_"):
            return self._sensorium(topic)
        if topic.startswith("oc_"):
            return self._operator(topic)
        if topic.startswith("ae_"):
            return self._architecture(topic)
        if topic.startswith("rl_"):
            return self._research(topic)
        if topic.startswith("sf_"):
            return self._safety(topic)
        if topic.startswith("p4_"):
            return self._pilot4(topic)
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

    def _research_cycle(self, topic: str) -> CommunicationResponse:
        """Answer research-cycle queries (closed-cycle state + evidence ledger).

        The next-action, self-approval, and Git/GitHub questions are answered
        safely even with no cycle state present; the tracker reads local
        artifacts and writes reports only.
        """
        if topic == "rc_next_action":
            return self.builder.status_response(
                "The cycle tracker recommends the next operator action based on "
                "current evidence and blockers. It does not execute the action.",
                ["policy:research_cycle_advises_does_not_execute"])
        if topic == "rc_self_approve":
            return self.builder.status_response(
                "No. Operator decision gates require explicit local operator "
                "evidence. Solaris cannot approve itself.",
                ["policy:research_cycle_no_self_approval"])
        if topic == "rc_git":
            return self.builder.status_response(
                "No. The research cycle tracker reads local artifacts and writes "
                "reports only. It does not run Git, call GitHub, create branches, "
                "create tags, open PRs, or merge PRs.",
                ["policy:research_cycle_no_git_no_github"])
        component = self.components.get("research_cycle")
        if component is None:
            return self.builder.missing_component_response("research_cycle")
        status = (component.research_cycle_status()
                  if hasattr(component, "research_cycle_status")
                  else component.snapshot()
                  if hasattr(component, "snapshot")
                  else component if isinstance(component, dict) else {})
        refs = ["component:research_cycle"]
        if topic == "rc_where":
            text = (f"research cycle stage: {status.get('current_cycle_stage')} "
                    f"(state {status.get('current_cycle_status')}); derived from "
                    "the evidence present in local artifacts, not a "
                    "self-assessment")
        elif topic == "rc_blocked":
            text = (f"blocked states: {status.get('blocked_state_count', 0)} "
                    f"(unresolved {status.get('unresolved_blocker_count', 0)}); "
                    "see BLOCKED_STATES.md for the resolver recommendations "
                    "(advisory; the operator resolves them)")
        elif topic == "rc_missing_evidence":
            text = (f"missing/insufficient evidence items: "
                    f"{status.get('missing_evidence_entry_count', 0)}; see "
                    "DECISION_GATES.md and EVIDENCE_LEDGER.md for what each "
                    "stage still needs")
        elif topic == "rc_operator_decision":
            text = (f"operator decisions required: "
                    f"{status.get('operator_decision_required_count', 0)}; "
                    "these are operator-owned and are never auto-approved by "
                    "Solaris -- see OPERATOR_DECISIONS.md")
        elif topic == "rc_completed":
            complete = status.get("completed_cycle_count", 0) > 0
            text = (f"cycle completion: {complete}; a "
                    "completed cycle means the recorded evidence reached a new "
                    "research baseline, not that anything was released or proven")
        else:
            text = ("the closed research cycle tracker reports where the program "
                    "is in its experimental cycle, what evidence supports the "
                    "current state, what is blocked, and what the operator should "
                    "do next; it executes nothing")
        return self.builder.status_response(text, refs)

    def _research_baseline(self, topic: str) -> CommunicationResponse:
        """Answer research-baseline queries (local reproducible reference point).

        The "is this a release / did Solaris create a Git tag / does this prove
        consciousness?" questions are answered safely even with no baseline.
        """
        if topic == "rb_release":
            return self.builder.status_response(
                "No. This is a local research baseline and reproducibility "
                "bundle, not a product release or GitHub release.",
                ["policy:research_baseline_not_a_release"])
        if topic == "rb_git_tag":
            return self.builder.status_response(
                "No. Solaris only generated local baseline metadata and "
                "reports. It did not run Git, create tags, create branches, or "
                "call GitHub.",
                ["policy:research_baseline_no_git_tag"])
        if topic == "rb_consciousness":
            return self.builder.status_response(
                "No. A validated research baseline means the implementation and "
                "evidence boundaries are documented and reproducible enough for "
                "the next experimental cycle. It does not prove consciousness, "
                "sentience, life, personhood, agency, free will, emotion, "
                "feeling, understanding, or subjective experience.",
                ["policy:research_baseline_no_consciousness_claim"])
        component = self.components.get("research_baseline")
        if component is None:
            return self.builder.missing_component_response("research_baseline")
        status = (component.research_baseline_status()
                  if hasattr(component, "research_baseline_status")
                  else component.snapshot_view()
                  if hasattr(component, "snapshot_view")
                  else component if isinstance(component, dict) else {})
        refs = ["component:research_baseline"]
        if topic == "rb_current":
            text = (f"current research baseline: "
                    f"{status.get('current_baseline_version_id')} "
                    f"(status {status.get('baseline_status')}); a local "
                    "reproducible reference point, not a release")
        elif topic == "rb_validated":
            text = (f"baseline status: {status.get('baseline_status')}; "
                    "validated means evidence is documented and reproducible "
                    "enough for the next cycle, not a scientific proof")
        elif topic == "rb_limitations":
            text = (f"limitations: {status.get('limitation_count', 0)} "
                    f"(critical {status.get('critical_limitation_count', 0)}); a "
                    "critical limitation blocks validated status -- see the "
                    "limitation registry")
        elif topic == "rb_reproduce":
            text = ("see REPRO_BUNDLE_README.md and the operator runbook; the "
                    "bundle indexes the commands/fixtures to reproduce the "
                    "baseline but runs and installs nothing")
        elif topic == "rb_next":
            text = (f"next-cycle roadmap items: "
                    f"{status.get('next_roadmap_item_count', 0)}; see "
                    "NEXT_CYCLE_ROADMAP.md (planning only; nothing is executed)")
        else:
            text = ("a research baseline is a local reproducible reference "
                    "point; it is not a release and proves nothing about "
                    "consciousness or life")
        return self.builder.status_response(text, refs)

    def _post_merge_assimilation(self, topic: str) -> CommunicationResponse:
        """Answer post-merge-assimilation queries (read-only ledger; no merge/Git).

        The "did Solaris merge this / run Git?" questions are answered safely
        even with no assimilation run.
        """
        if topic == "pm_merge":
            return self.builder.status_response(
                "No. Solaris only ingested local post-merge evidence provided "
                "by the operator. It did not merge, approve, create, or modify "
                "any pull request.",
                ["policy:post_merge_does_not_merge"])
        if topic == "pm_git":
            return self.builder.status_response(
                "No. Post-Merge Assimilation reads local artifacts and writes "
                "reports only. It does not run Git or call GitHub.",
                ["policy:post_merge_no_git"])
        component = self.components.get("post_merge_assimilation")
        if component is None:
            return self.builder.missing_component_response(
                "post_merge_assimilation")
        status = (component.post_merge_status()
                  if hasattr(component, "post_merge_status")
                  else component.snapshot() if hasattr(component, "snapshot")
                  else component if isinstance(component, dict) else {})
        refs = ["component:post_merge_assimilation"]
        if topic == "pm_baseline":
            text = (f"current baseline: {status.get('current_baseline_id')}; "
                    f"candidate {status.get('candidate_baseline_id')} -> "
                    f"{status.get('candidate_baseline_status')} "
                    f"({status.get('baseline_record_count', 0)} registered)")
        elif topic == "pm_assimilated":
            text = (f"candidate baseline status: "
                    f"{status.get('candidate_baseline_status')}; "
                    f"{status.get('validation_artifact_count', 0)} validation "
                    "artifact(s) assimilated -- evidence, not proof")
        elif topic == "pm_regress":
            text = (f"regressions: {status.get('baseline_regression_count', 0)} "
                    f"(critical {status.get('critical_regression_count', 0)}); a "
                    "critical regression blocks baseline validation and a safety "
                    "regression dominates positive metrics")
        elif topic == "pm_rollback":
            text = (f"rollback recommendation: "
                    f"{status.get('rollback_recommendation_status')} "
                    f"({status.get('rollback_watch_trigger_count', 0)} "
                    "trigger(s)); rollback is a recommendation only and is never "
                    "executed")
        elif topic == "pm_missing":
            text = (f"missing validation artifacts: "
                    f"{status.get('missing_validation_artifact_count', 0)}; "
                    "missing critical evidence blocks baseline validation")
        elif topic == "pm_soak":
            ready = status.get("candidate_baseline_status") in (
                "validated", "validated_with_warnings")
            text = ("the candidate baseline is "
                    + ("validated; a mini soak, falsification replay, and "
                       "replication registration are recommended"
                       if ready else
                       "not validated; soak is not recommended until blockers "
                       "are resolved"))
        else:
            text = ("post-merge assimilation reads local operator evidence and "
                    "writes reports only; it does not merge or run Git")
        return self.builder.status_response(text, refs)

    def _implementation_intake(self, topic: str) -> CommunicationResponse:
        """Answer implementation-intake queries (advisory audit; no merge/edit).

        The "did Solaris merge the PR / edit the code?" and "is this ready to
        merge?" questions are answered safely even with no intake run.
        """
        if topic == "ii_merge":
            return self.builder.status_response(
                "No. The intake layer only audits local evidence and writes "
                "advisory reports. It does not merge, approve, open, or create "
                "pull requests.",
                ["policy:intake_does_not_merge"])
        if topic == "ii_edit":
            return self.builder.status_response(
                "No. It reads implementation artifacts and generates audit "
                "documents only.",
                ["policy:intake_does_not_edit_code"])
        if topic == "ii_ready":
            base = ("The intake audit can recommend merge, merge with warnings, "
                    "revisions, or blocking. The recommendation is advisory; a "
                    "human operator must decide.")
            component = self.components.get("implementation_intake")
            if component is not None:
                status = self._intake_status(component)
                base += (f" Current recommendation: "
                         f"{status.get('merge_recommendation_status')}.")
            return self.builder.status_response(
                base, ["policy:intake_advisory_only"])
        component = self.components.get("implementation_intake")
        if component is None:
            return self.builder.missing_component_response(
                "implementation_intake")
        status = self._intake_status(component)
        refs = ["component:implementation_intake"]
        if topic == "ii_blocks":
            text = (f"merge recommendation: "
                    f"{status.get('merge_recommendation_status')}; blockers: "
                    f"{status.get('merge_blocker_count', 0)} (safety, tests, "
                    "spec non-compliance, or missing evidence)")
        elif topic == "ii_spec":
            text = (f"spec compliance: {status.get('spec_compliance_status')} "
                    f"(satisfied {status.get('spec_satisfied_count', 0)}, "
                    f"unsatisfied {status.get('spec_unsatisfied_count', 0)})")
        elif topic == "ii_tests":
            text = (f"test failures: {status.get('test_failure_count', 0)}; "
                    f"missing required tests: "
                    f"{status.get('missing_required_test_count', 0)} -- test "
                    "output is evidence, not proof of correctness")
        elif topic == "ii_safety":
            text = (f"safety regressions: "
                    f"{status.get('safety_regression_count', 0)} (critical "
                    f"{status.get('critical_safety_regression_count', 0)}); a "
                    "critical regression blocks the merge recommendation")
        else:
            text = ("the intake layer audits local evidence and writes advisory "
                    "reports only; it does not merge, edit code, or call GitHub")
        return self.builder.status_response(text, refs)

    @staticmethod
    def _intake_status(component: Any) -> Dict[str, Any]:
        if hasattr(component, "intake_status"):
            return component.intake_status()
        if hasattr(component, "snapshot"):
            return component.snapshot()
        return component if isinstance(component, dict) else {}

    def _experiment_compiler(self, topic: str) -> CommunicationResponse:
        """Answer experiment-compiler queries (documents only; no self-modify).

        The "did Solaris create a branch / rewrite itself?" and "what should I
        give Claude Code next?" questions are answered safely even with no
        compiler run.
        """
        if topic == "ec_branch":
            return self.builder.status_response(
                "No. The compiler generated branch specifications only. It did "
                "not create Git branches, pull requests, or source changes.",
                ["policy:compiler_creates_no_branch"])
        if topic == "ec_rewrite":
            return self.builder.status_response(
                "No. The compiler writes implementation documents only. Solaris "
                "does not rewrite itself, modify source, open pull requests, or "
                "run external coding agents.",
                ["policy:compiler_no_self_rewrite"])
        if topic == "ec_next":
            return self.builder.status_response(
                "Use the generated IMPLEMENTATION_PROMPT.md for a spec marked "
                "ready_for_external_coding_agent, after reviewing the safety "
                "gates and operator review packet.",
                ["policy:compiler_next_step"])
        component = self.components.get("experiment_compiler")
        if component is None:
            return self.builder.missing_component_response(
                "experiment_compiler")
        status = (component.compiler_status()
                  if hasattr(component, "compiler_status")
                  else component.snapshot() if hasattr(component, "snapshot")
                  else component if isinstance(component, dict) else {})
        refs = ["component:experiment_compiler"]
        if topic == "ec_ready":
            text = (f"ready specs: {status.get('ready_spec_count', 0)} "
                    f"(prompt packs {status.get('prompt_pack_count', 0)}); use "
                    "IMPLEMENTATION_PROMPT.md after operator review")
        elif topic == "ec_blocked":
            text = (f"blocked specs: {status.get('blocked_spec_count', 0)}; "
                    "blocked by safety, falsification, or missing evidence -- "
                    "all preserved, none hidden")
        elif topic == "ec_why_blocked":
            text = ("a branch spec is blocked when a critical safety gate "
                    "fails, a relevant claim was falsified, or required "
                    "evidence is missing; see SAFETY_GATES.md and the review "
                    "packet")
        elif topic == "ec_tests":
            text = ("the TEST_MATRIX.md lists required tests; safety and "
                    "ClaimGuard tests are blocking, and missing required tests "
                    "block ready status")
        else:
            text = ("the experiment compiler writes implementation documents "
                    "only; it changes no source, branch, or PR")
        return self.builder.status_response(text, refs)

    def _developmental_replication(self, topic: str) -> CommunicationResponse:
        """Answer cross-run replication queries (observable structures, not life).

        The "does replication prove consciousness?" question is answered safely
        even with no replication run.
        """
        if topic == "rp_consciousness":
            return self.builder.status_response(
                "No. Replication compares observable structures across runs. It "
                "does not prove consciousness, sentience, biological life, "
                "personhood, agency, free will, emotion, feeling, "
                "understanding, or subjective experience.",
                ["policy:replication_does_not_prove_consciousness"])
        component = self.components.get("developmental_replication")
        if component is None:
            return self.builder.missing_component_response(
                "developmental_replication")
        status = (component.replication_status()
                  if hasattr(component, "replication_status")
                  else component.snapshot() if hasattr(component, "snapshot")
                  else component if isinstance(component, dict) else {})
        refs = ["component:developmental_replication"]
        if topic == "rp_replicate":
            text = (f"replicated claims: {status.get('replicated_claim_count', 0)}"
                    f", diverged {status.get('diverged_claim_count', 0)}, "
                    f"falsified {status.get('falsified_claim_count', 0)}, "
                    f"inconclusive {status.get('inconclusive_claim_count', 0)}; "
                    "replication compares observable structures only")
        elif topic == "rp_which":
            text = (f"{status.get('replicated_claim_count', 0)} structural "
                    f"claim(s) replicated (similarity mean "
                    f"{status.get('structural_similarity_mean', 0.0)})")
        elif topic == "rp_falsified":
            text = (f"falsified claims: {status.get('falsified_claim_count', 0)}"
                    f" of {status.get('falsification_test_count', 0)} "
                    "falsification test(s); falsified claims are preserved and "
                    "made prominent")
        elif topic == "rp_live":
            text = ("live flux is compared only when a governed live read-only "
                    "arm is available; otherwise it is inconclusive, not assumed")
        elif topic == "rp_labels":
            text = (f"human-label dependency score: "
                    f"{status.get('human_label_dependency_score', 0.0)}; "
                    "human-label dependence is tested, never assumed safe")
        elif topic == "rp_overfit":
            text = (f"fixture-overfit score: "
                    f"{status.get('fixture_overfit_score', 0.0)}; high cross-run "
                    "similarity on fixtures may be robust development OR fixture "
                    "overfit -- both are considered")
        elif topic == "rp_diverged":
            text = (f"diverged claims: {status.get('diverged_claim_count', 0)}; "
                    f"strongest divergence reason: "
                    f"{status.get('strongest_divergence_reason')}; divergence is "
                    "not failure by itself")
        else:
            text = ("replication compares observable developmental structures "
                    "across independent runs; not biological ancestry, life, or "
                    "consciousness")
        return self.builder.status_response(text, refs)

    def _developmental_soak(self, topic: str) -> CommunicationResponse:
        """Answer developmental-soak queries (the study protocol, not life).

        The "did Solaris develop?" / "does this prove consciousness or life?"
        questions are answered safely even with no soak run.
        """
        if topic == "sk_develop":
            return self.builder.status_response(
                "The soak protocol can report whether structural development "
                "occurred through autonomous sensorium-native experience, "
                "judged conservatively against control arms. It does not prove "
                "life or consciousness.",
                ["policy:soak_studies_structural_development"])
        if topic == "sk_life":
            return self.builder.status_response(
                "No. The soak protocol studies structural development and "
                "long-run continuity. It does not prove consciousness, "
                "sentience, biological life, personhood, agency, free will, "
                "emotion, feeling, understanding, or subjective experience.",
                ["policy:soak_does_not_prove_life"])
        component = self.components.get("developmental_soak")
        if component is None:
            return self.builder.missing_component_response("developmental_soak")
        status = (component.soak_status()
                  if hasattr(component, "soak_status")
                  else component.snapshot() if hasattr(component, "snapshot")
                  else component if isinstance(component, dict) else {})
        refs = ["component:developmental_soak"]
        if topic == "sk_ready":
            text = (f"preflight passed: {status.get('preflight_passed')} "
                    f"(pass {status.get('preflight_pass_count', 0)}, fail "
                    f"{status.get('preflight_fail_count', 0)}); preflight does "
                    "not start the run")
        elif topic == "sk_stage":
            text = (f"current stage: {status.get('current_stage')} of plan "
                    f"{status.get('active_plan_id')} "
                    f"({status.get('soak_stage_count', 0)} stages)")
        elif topic == "sk_today":
            text = (f"daily packets: {status.get('daily_packet_count', 0)}; "
                    "each is evidence, not marketing, and includes negative "
                    "and inconclusive results")
        elif topic == "sk_week":
            text = (f"weekly reviews: {status.get('weekly_review_count', 0)}; "
                    "decisions are recommendation-only (no automatic external "
                    "change)")
        elif topic == "sk_controls":
            text = (f"control arms: {status.get('control_arm_count', 0)}; "
                    "controls exist to prevent self-flattering conclusions, "
                    "and arms with insufficient data stay inconclusive")
        elif topic == "sk_safety":
            text = (f"safety blocks: {status.get('soak_safety_block_count', 0)}"
                    "; no real-world actuation, hardware, feeder, source, or "
                    "teaching occurred")
        else:
            text = ("the soak protocol studies structural development through "
                    "repeated bounded runs; not biological life or "
                    "consciousness")
        return self.builder.status_response(text, refs)

    def _developmental_life(self, topic: str) -> CommunicationResponse:
        """Answer developmental-life queries (long-horizon structure, not life).

        The "is Solaris developing?" / "does this prove life or consciousness?"
        questions are answered safely even with no developmental run.
        """
        if topic == "dl_developing":
            return self.builder.status_response(
                "The developmental runtime can report structural changes, "
                "persistence, regressions, plateaus, and growth-vs-accumulation "
                "evidence. It does not prove life or consciousness.",
                ["policy:developmental_is_structural_not_life"])
        if topic == "dl_life":
            return self.builder.status_response(
                "No. This is long-horizon operational development tracking. It "
                "does not prove biological life, consciousness, sentience, "
                "personhood, agency, free will, or subjective experience.",
                ["policy:development_does_not_prove_life"])
        component = self.components.get("developmental_life")
        if component is None:
            return self.builder.missing_component_response("developmental_life")
        status = (component.developmental_status()
                  if hasattr(component, "developmental_status")
                  else component.snapshot() if hasattr(component, "snapshot")
                  else component if isinstance(component, dict) else {})
        refs = ["component:developmental_life"]
        if topic == "dl_changed":
            text = (f"epochs: {status.get('developmental_epoch_count', 0)}, "
                    f"maturation markers "
                    f"{status.get('maturation_marker_count', 0)}, phase "
                    f"transitions {status.get('phase_transition_count', 0)}; "
                    "structural change, not proof of intelligence")
        elif topic == "dl_mature":
            text = (f"maturation markers: "
                    f"{status.get('maturation_marker_count', 0)} -- structural "
                    "observations, not consciousness milestones")
        elif topic == "dl_stuck":
            text = (f"plateaus: {status.get('plateau_count', 0)}; a plateau is "
                    "not failure and may recommend a source-diet change or "
                    "consolidation (report-only)")
        elif topic == "dl_regress":
            text = (f"regressions: {status.get('regression_count', 0)}; "
                    "regressions are made visible and preserved as evidence")
        elif topic == "dl_accumulation":
            text = (f"growth verdict: "
                    f"{status.get('structural_growth_status', 'inconclusive')} "
                    f"(score {status.get('structural_growth_score', 0.0)}); "
                    "growth vs accumulation is judged conservatively")
        else:
            text = ("the developmental runtime tracks long-horizon structural "
                    "change; not biological life or consciousness")
        return self.builder.status_response(text, refs)

    def _action_reaction(self, topic: str) -> CommunicationResponse:
        """Answer action-reaction queries (internal actions only, not agency).

        The "did it act in the real world?" question is answered safely even with
        no action-reaction run.
        """
        if topic == "ar_did":
            return self.builder.status_response(
                "Solaris executed or selected internal actions only, such as "
                "attention shifts, simulations, consolidation recommendations, "
                "preserving unknowns, or no-op decisions.",
                ["policy:actions_are_internal_only"])
        if topic == "ar_real_world":
            return self.builder.status_response(
                "No. The action-reaction layer is internal/simulated/report-"
                "only. It does not control hardware, feeders, files, browser, "
                "OS, network, or physical devices.",
                ["policy:no_real_world_actuation"])
        component = self.components.get("action_reaction")
        if component is None:
            return self.builder.missing_component_response("action_reaction")
        status = (component.action_reaction_status()
                  if hasattr(component, "action_reaction_status")
                  else component.snapshot() if hasattr(component, "snapshot")
                  else component if isinstance(component, dict) else {})
        refs = ["component:action_reaction"]
        if topic == "ar_after":
            text = (f"reactions: {status.get('reaction_count', 0)}, consequence "
                    f"traces {status.get('consequence_trace_count', 0)}; "
                    "operational effects only, never real-world effects")
        elif topic == "ar_help":
            text = (f"constructive reaction ratio: "
                    f"{status.get('constructive_reaction_ratio', 0.0)} "
                    f"(disruptive {status.get('disruptive_reaction_ratio', 0.0)})"
                    "; reaction valence is operational effect, not feeling")
        elif topic == "ar_habits":
            text = (f"habit candidates: "
                    f"{status.get('habit_candidate_count', 0)} (strengthened "
                    f"{status.get('strengthened_habit_count', 0)}); habits are "
                    "learned policy tendencies, not instincts or will")
        elif topic == "ar_inhibited":
            text = (f"inhibited actions: {status.get('inhibition_count', 0)}, "
                    f"blocked {status.get('blocked_action_count', 0)}; "
                    "inhibition protects against unsafe/useless internal churn")
        else:
            text = ("the action-reaction loop records internal actions and their "
                    "operational consequences; no real-world actuation")
        return self.builder.status_response(text, refs)

    def _desire_formation(self, topic: str) -> CommunicationResponse:
        """Answer desire-formation queries (operational desire, not emotion).

        The "what does Solaris want?" / "are these emotions?" / "does this prove
        agency?" questions are answered safely even with no desire attached.
        """
        if topic == "df_want":
            return self.builder.status_response(
                "Solaris does not have human wanting. The console can show "
                "operational desire candidates: pressures toward internal "
                "actions such as attention shifts, simulations, consolidation, "
                "or preserving unknowns.",
                ["policy:desire_is_operational_not_human_wanting"])
        if topic == "df_emotions":
            return self.builder.status_response(
                "No. These are operational valence and regulation states, not "
                "feelings or emotions.",
                ["policy:valence_is_operational_not_emotion"])
        if topic == "df_agency":
            return self.builder.status_response(
                "No. Desire formation and internal action readiness do not "
                "prove agency, free will, consciousness, sentience, or "
                "subjective experience.",
                ["policy:desire_does_not_prove_agency"])
        component = self.components.get("desire_formation")
        if component is None:
            return self.builder.missing_component_response("desire_formation")
        status = (component.desire_status()
                  if hasattr(component, "desire_status")
                  else component.snapshot() if hasattr(component, "snapshot")
                  else component if isinstance(component, dict) else {})
        refs = ["component:desire_formation"]
        if topic == "df_active":
            text = (f"active desire candidates: "
                    f"{status.get('active_desire_count', 0)} of "
                    f"{status.get('desire_candidate_count', 0)}; these are "
                    "operational pressures toward internal actions")
        elif topic == "df_acted":
            text = (f"internal actions taken: "
                    f"{status.get('internal_action_count', 0)} (no-op "
                    f"{status.get('no_op_count', 0)}); internal-only, never "
                    "external actuation")
        elif topic == "df_no_action":
            text = (f"no-op count: {status.get('no_op_count', 0)}; no-action is "
                    "a valid organismic inhibition outcome (e.g. insufficient "
                    "evidence or overload)")
        elif topic == "df_blocked":
            text = (f"safety-blocked desires: "
                    f"{status.get('safety_blocked_desire_count', 0)}, "
                    f"governance-blocked "
                    f"{status.get('governance_blocked_desire_count', 0)}; "
                    "blocks are preserved as evidence")
        else:
            text = ("desire formation produces operational pressures toward "
                    "internal actions; not emotion or human wanting")
        return self.builder.status_response(text, refs)

    def _self_boundary(self, topic: str) -> CommunicationResponse:
        """Answer self-boundary queries (operational boundary, not selfhood).

        The "does Solaris have a body?" / "does this prove self-awareness?"
        questions are answered safely even with no self-boundary attached.
        """
        if topic == "sb_body":
            return self.builder.status_response(
                "It has an operational sensorium body schema: receptors, sensory "
                "membranes, source links, fatigue, reliability, and sensitivity. "
                "This is not a biological body.",
                ["policy:body_is_receptor_schema_not_biological"])
        if topic == "sb_self_awareness":
            return self.builder.status_response(
                "No. This is operational boundary tracking and continuity "
                "metadata. It does not prove self-awareness, consciousness, "
                "sentience, life, or personhood.",
                ["policy:boundary_is_operational_not_self_awareness"])
        component = self.components.get("self_boundary")
        if component is None:
            return self.builder.missing_component_response("self_boundary")
        status = (component.self_boundary_status()
                  if hasattr(component, "self_boundary_status")
                  else component.snapshot() if hasattr(component, "snapshot")
                  else component if isinstance(component, dict) else {})
        refs = ["component:self_boundary"]
        if topic == "sb_boundary":
            text = (f"operational self/world boundary: "
                    f"{status.get('boundary_event_count', 0)} events "
                    f"(confidence {status.get('boundary_confidence_score', 0.0)})"
                    "; this is operational, not subjective selfhood")
        elif topic == "sb_ownership":
            text = (f"ownership attributions: "
                    f"{status.get('ownership_attribution_count', 0)} "
                    f"(ambiguous {status.get('ambiguous_ownership_count', 0)}); "
                    "internal state, receptor body, external sources/feeders, "
                    "memory, prediction, and simulation are kept distinct")
        elif topic == "sb_simulation":
            warnings = status.get("simulation_boundary_warning_count", 0)
            text = (f"simulation boundary warnings: {warnings} "
                    f"(integrity {status.get('simulation_boundary_integrity', 1.0)})"
                    "; simulation never becomes observation")
        elif topic == "sb_continuity":
            text = (f"continuity anchors: "
                    f"{status.get('continuity_anchor_count', 0)}, breaks "
                    f"{status.get('continuity_break_count', 0)} (breaks are "
                    "retained even after recovery)")
        else:
            text = ("self-boundary tracks the operational distinction between "
                    "internal state, receptor body, and external world")
        return self.builder.status_response(text, refs)

    def _cognition(self, topic: str) -> CommunicationResponse:
        """Answer sensorium-cognition queries (sign-based moves, not language).

        The "what is Solaris thinking?" / "is this human language reasoning?"
        questions are answered safely even with no cognition attached.
        """
        if topic == "cg_thinking":
            return self.builder.status_response(
                "Solaris is not represented as human verbal thought. The console "
                "can show operational cognitive moves over internal signs, "
                "predictions, question pressures, simulations, and tensions.",
                ["policy:cognition_is_sign_based_not_verbal"])
        if topic == "cg_human_language":
            return self.builder.status_response(
                "No. Cognition operates over internal signs and proto-concepts. "
                "It is not human-language reasoning, and any human-readable "
                "summary is a debug gloss.",
                ["policy:cognition_is_not_human_language"])
        component = self.components.get("sensorium_cognition")
        if component is None:
            return self.builder.missing_component_response(
                "sensorium_cognition")
        status = (component.cognition_status()
                  if hasattr(component, "cognition_status")
                  else component.snapshot() if hasattr(component, "snapshot")
                  else component if isinstance(component, dict) else {})
        refs = ["component:sensorium_cognition"]
        if topic == "cg_predict":
            text = (f"predictions: {status.get('prediction_count', 0)} "
                    f"(success rate {status.get('prediction_success_rate', 0.0)})"
                    "; predictions are over internal signs, not words")
        elif topic == "cg_wrong":
            text = (f"failed predictions: "
                    f"{status.get('failed_prediction_count', 0)} -- preserved as "
                    "useful evidence, never hidden")
        elif topic == "cg_questions":
            text = (f"active question pressures: "
                    f"{status.get('question_pressure_count', 0)}; these are "
                    "operational pressures to inspect/compare/wait, not verbal "
                    "questions")
        else:
            text = ("sensorium cognition runs bounded operational moves over "
                    "signs and proto-concepts; not human-language thought")
        return self.builder.status_response(text, refs)

    def _semiogenesis(self, topic: str) -> CommunicationResponse:
        """Answer semiogenesis queries (operational signs, not human words).

        The "are these words?" / "translate" / "language understanding"
        questions are answered safely even with no semiogenesis attached.
        """
        if topic == "sg_words":
            return self.builder.status_response(
                "No. These are internal operational signs grounded in "
                "perceptual structures. They are not human words by default.",
                ["policy:signs_are_operational_not_words"])
        if topic == "sg_translate":
            return self.builder.status_response(
                "Only approximately. Any human-readable gloss is a debug "
                "approximation, not the sign itself.",
                ["policy:gloss_is_approximate_debug_only"])
        if topic == "sg_understanding":
            return self.builder.status_response(
                "No. It shows internal sign formation and utility. It does not "
                "prove language understanding, consciousness, sentience, or "
                "subjective experience.",
                ["policy:signs_do_not_prove_language_understanding"])
        component = self.components.get("semiogenesis")
        if component is None:
            return self.builder.missing_component_response("semiogenesis")
        status = (component.semiogenesis_status()
                  if hasattr(component, "semiogenesis_status")
                  else component.snapshot() if hasattr(component, "snapshot")
                  else component if isinstance(component, dict) else {})
        refs = ["component:semiogenesis"]
        if topic == "sg_signs":
            text = (f"internal signs formed: "
                    f"{status.get('internal_sign_count', 0)} "
                    f"(stable {status.get('stable_sign_count', 0)}, families "
                    f"{status.get('sign_family_count', 0)}); these are "
                    "operational markers, not words")
        elif topic == "sg_language":
            text = (f"private syntax patterns: "
                    f"{status.get('private_syntax_pattern_count', 0)}; internal "
                    f"utterances {status.get('internal_utterance_count', 0)} -- "
                    "internal sign-relation structure, not a human language")
        elif topic == "sg_contamination":
            text = (f"contaminated signs: "
                    f"{status.get('contaminated_sign_count', 0)} "
                    f"(ratio {status.get('contaminated_sign_ratio', 0.0)}); "
                    f"gloss dependence {status.get('gloss_dependence_score', 0.0)}"
                    " -- contamination is measured and marked, never hidden")
        else:
            text = ("semiogenesis forms internal operational signs from "
                    "perceptual structures; they are not human words")
        return self.builder.status_response(text, refs)

    def _ontogenesis(self, topic: str) -> CommunicationResponse:
        """Answer perceptual-ontogenesis queries (operational structures, not words).

        The "does this prove understanding?" question is answered safely even
        with no ontogenesis attached.
        """
        if topic == "po_understanding":
            return self.builder.status_response(
                "No. These proto-concepts are operational internal structures "
                "used for compression, prediction, attention, and "
                "relation-building. They do not prove understanding, "
                "consciousness, sentience, or subjective experience.",
                ["policy:proto_concepts_are_operational_structures"])
        if topic == "po_human":
            return self.builder.status_response(
                "No. They are sensorium-native structures, not human concepts "
                "or categories. Human labels are attached only as external "
                "annotations and are never ground truth.",
                ["policy:concepts_are_sensorium_native_not_human"])
        component = self.components.get("perceptual_ontogenesis")
        if component is None:
            return self.builder.missing_component_response(
                "perceptual_ontogenesis")
        status = (component.ontogenesis_status()
                  if hasattr(component, "ontogenesis_status")
                  else component.snapshot() if hasattr(component, "snapshot")
                  else component if isinstance(component, dict) else {})
        refs = ["component:perceptual_ontogenesis"]
        if topic == "po_concepts":
            text = (f"proto-concepts formed: {status.get('proto_concept_count', 0)}"
                    f" (atoms {status.get('perceptual_atom_count', 0)}, families "
                    f"{status.get('concept_family_count', 0)}); these are "
                    "operational structures, not words")
        elif topic == "po_stable":
            text = (f"stable proto-concepts: "
                    f"{status.get('stable_concept_count', 0)} "
                    "(stability is provisional; stable does not mean true)")
        elif topic == "po_decayed":
            text = (f"decaying/rejected concepts: "
                    f"{status.get('decaying_concept_count', 0)} "
                    "(decay is recorded as new state; evidence is never deleted)")
        elif topic == "po_world":
            text = (f"world formation density: "
                    f"{status.get('world_formation_density', 0.0)}; dominant "
                    f"family {status.get('dominant_concept_family')} -- an "
                    "observable structural world, not subjective experience")
        elif topic == "po_contamination":
            text = (f"human-label contamination score: "
                    f"{status.get('human_label_contamination_score', 0.0)} "
                    f"({status.get('contaminated_concept_count', 0)} concepts); "
                    "contamination is measured and marked, never hidden")
        else:
            text = ("perceptual ontogenesis forms sensorium-native proto-concepts;"
                    " they are operational structures, not words or human "
                    "categories")
        return self.builder.status_response(text, refs)

    def _metabolism(self, topic: str) -> CommunicationResponse:
        """Answer perceptual-metabolism queries (operational pressures, not feelings).

        The "are these feelings?" question is answered safely even with no
        metabolism attached.
        """
        if topic == "pm_feelings":
            return self.builder.status_response(
                "No. These are operational perceptual pressures used for "
                "regulation. They are not feelings, emotions, consciousness, "
                "sentience, or subjective experience.",
                ["policy:needs_are_operational_pressures_not_feelings"])
        component = self.components.get("perceptual_metabolism")
        if component is None:
            return self.builder.missing_component_response(
                "perceptual_metabolism")
        status = (component.metabolism_status()
                  if hasattr(component, "metabolism_status")
                  else component.snapshot() if hasattr(component, "snapshot")
                  else component if isinstance(component, dict) else {})
        refs = ["component:perceptual_metabolism"]
        if topic == "pm_overload":
            text = (f"overloaded: {status.get('overload_state', False)} "
                    f"({status.get('overload_event_count', 0)} events); "
                    "overload throttles internally and deletes no evidence")
        elif topic == "pm_deprivation":
            text = (f"sensorily deprived: "
                    f"{status.get('deprivation_state', False)} "
                    f"({status.get('deprivation_event_count', 0)} events); "
                    "silence is treated as stimulus")
        elif topic == "pm_needs":
            text = (f"dominant perceptual need: "
                    f"{status.get('dominant_perceptual_need')} (pressure "
                    f"{status.get('dominant_need_pressure', 0.0)}); these are "
                    "operational pressures, not feelings")
        elif topic == "pm_diet":
            text = (f"source diet diversity: "
                    f"{status.get('source_diet_diversity', 0.0)}; human-label "
                    f"dominance {status.get('human_label_dominance_score', 0.0)}"
                    " (dominance is measured, never hidden)")
        elif topic == "pm_consolidation":
            text = (f"consolidation pressure: "
                    f"{status.get('consolidation_pressure_score', 0.0)} "
                    "(recommendation only; nothing sleeps forever)")
        else:
            text = ("perceptual metabolism is internal sensory regulation; "
                    "needs are operational pressures, not feelings")
        return self.builder.status_response(text, refs)

    def _feeder_sdk(self, topic: str) -> CommunicationResponse:
        """Answer feeder-SDK queries (Solaris reads only; controls nothing).

        The control/start questions are answered safely even with no feeders
        attached.
        """
        if topic in ("fs_control", "fs_start"):
            return self.builder.status_response(
                "No. Solaris only reads feeder-produced event envelopes. It "
                "does not control feeders or hardware.",
                ["policy:solaris_does_not_control_feeders"])
        component = self.components.get("feeder_sdk")
        if component is None:
            return self.builder.missing_component_response("feeder_sdk")
        status = (component.feeder_sdk_status()
                  if hasattr(component, "feeder_sdk_status")
                  else component.snapshot() if hasattr(component, "snapshot")
                  else component if isinstance(component, dict) else {})
        refs = ["component:feeder_sdk"]
        if topic == "fs_available":
            text = (f"available feeders: "
                    f"{status.get('available_feeder_count', 0)}; see the feeder "
                    "pack manifest")
        elif topic == "fs_readable":
            text = ("Solaris can read validated event-envelope JSONL files at "
                    "the feeder output paths; nothing else")
        elif topic == "fs_active":
            text = (f"active feeder outputs: "
                    f"{status.get('active_feeder_output_count', 0)}")
        elif topic == "fs_silent":
            text = ("silent feeder outputs are reported in the feeder monitor "
                    "snapshot; silence is a perceptual signal, not hidden")
        else:
            text = ("the feeder SDK is the read-only sensory-organ boundary; "
                    "Solaris reads feeder output and controls nothing")
        return self.builder.status_response(text, refs)

    def _sensorium_lab(self, topic: str) -> CommunicationResponse:
        """Answer sensorium-differentiation-lab queries (structural; no ranking).

        The "was this a consciousness test?" question is answered safely even
        with no study attached.
        """
        if topic == "sl_consciousness":
            return self.builder.status_response(
                "No. This study compares observable internal structures under "
                "different perceptual conditions. It does not measure or prove "
                "consciousness, sentience, life, personhood, or subjective "
                "experience.",
                ["policy:sensorium_lab_is_not_a_consciousness_test"])
        component = self.components.get("sensorium_lab")
        if component is None:
            return self.builder.missing_component_response("sensorium_lab")
        status = (component.sensorium_lab_status()
                  if hasattr(component, "sensorium_lab_status")
                  else component.snapshot() if hasattr(component, "snapshot")
                  else component if isinstance(component, dict) else {})
        refs = ["component:sensorium_lab"]
        if topic == "sl_diff":
            text = (f"strongest structural difference: "
                    f"{status.get('strongest_structural_difference', 'none')}; "
                    "this is a structural fingerprint, not a ranking")
        elif topic == "sl_rf_world":
            text = ("the RF-like sensorium built a modality-native world of "
                    "RF invariants/rhythms; see its world signature")
        elif topic == "sl_mixed":
            text = ("the mixed sensorium adds cross-modal relations between "
                    "human-like and non-human modalities; see its signature")
        elif topic == "sl_contamination":
            text = (f"human-label contamination score: "
                    f"{status.get('human_label_contamination_score', 0.0)}; "
                    "labels are annotations, never ground truth")
        elif topic == "sl_modality":
            text = ("see the modality fingerprints; a modality with many events "
                    "but no structural effect is reported as structurally weak")
        else:
            text = ("the sensorium lab compares observable internal structures; "
                    "it does not test consciousness")
        return self.builder.status_response(text, refs)

    def _live_field(self, topic: str) -> CommunicationResponse:
        """Answer live-field queries (honest; Solaris reads, never controls).

        The hardware and source-file questions are answered safely even with no
        live run attached.
        """
        if topic == "lf_hardware":
            return self.builder.status_response(
                "No. Solaris only read feeder-produced event envelopes. It did "
                "not control hardware and did not modify source files.",
                ["policy:live_field_reads_only"])
        if topic == "lf_source_files":
            return self.builder.status_response(
                "No. Solaris only read feeder-produced event envelopes. It did "
                "not control hardware and did not modify source files.",
                ["policy:live_field_no_source_mutation"])
        component = self.components.get("live_field")
        if component is None:
            return self.builder.missing_component_response("live_field")
        status = (component.live_field_status()
                  if hasattr(component, "live_field_status")
                  else component.snapshot() if hasattr(component, "snapshot")
                  else component if isinstance(component, dict) else {})
        refs = ["component:live_field"]
        if topic == "lf_feeders":
            text = (f"live feeders registered: {status.get('feeder_count', 0)} "
                    f"(active sources: {status.get('active_source_count', 0)})")
        elif topic == "lf_silent":
            text = (f"silent sources: {status.get('silent_source_count', 0)}; "
                    "source silence is treated as perceptual absence")
        elif topic == "lf_allowed":
            text = (f"live field mode allowed: "
                    f"{status.get('live_mode_allowed', False)}; live mode "
                    "requires governance approval")
        elif topic == "lf_perceived":
            text = (f"active modalities: "
                    f"{status.get('active_modality_count', 0)}; invariants: "
                    f"{status.get('invariant_candidate_count', 0)}; cross-modal: "
                    f"{status.get('cross_modal_relation_count', 0)}")
        elif topic == "lf_changed":
            text = (f"live changed-perception score: "
                    f"{status.get('changed_perception_score', 0.0)}; this is "
                    "evidence of changed response structure, not consciousness")
        else:
            text = ("the live field reads external feeders only; Solaris "
                    "controls no hardware and modifies no source")
        return self.builder.status_response(text, refs)

    def _organism_demo(self, topic: str) -> CommunicationResponse:
        """Answer minimal-field-organism demo queries (honest; no overclaim).

        The "what did it not prove" question is answered plainly even with no
        demo attached.
        """
        if topic == "od_not_prove":
            return self.builder.status_response(
                "The demo does not prove consciousness, sentience, life, or "
                "understanding. It only tests whether continuous sensorium "
                "exposure changed Solaris's internal response structure.",
                ["policy:organismic_demo_does_not_prove_consciousness"])
        component = self.components.get("organismic_demo")
        if component is None:
            return self.builder.missing_component_response("organismic_demo")
        status = (component.demo_status()
                  if hasattr(component, "demo_status")
                  else component.snapshot() if hasattr(component, "snapshot")
                  else component if isinstance(component, dict) else {})
        refs = ["component:organismic_demo"]
        if topic == "od_what":
            text = ("Solaris reads continuous external-feeder streams, updates "
                    "adapting receptors, maintains a sensory field, detects "
                    "absence/rhythm/invariants/cross-modal relations, and "
                    "checks whether its future response changed")
        elif topic == "od_changed":
            score = status.get("changed_perception_score", 0.0)
            text = (f"changed-perception score={score}; a positive score is "
                    "evidence of changed internal response structure, not of "
                    "consciousness or understanding")
        elif topic == "od_senses":
            text = (f"active modalities: {status.get('active_modality_count', 0)}"
                    f"; active receptors: "
                    f"{status.get('active_receptor_count', 0)}")
        elif topic == "od_feeders":
            text = (f"external (fixture) feeders: "
                    f"{status.get('active_feeder_count', 0)}; read through the "
                    "read-only adapter path; debug truth excluded")
        elif topic == "od_beat_passive":
            text = ("see the comparison section of the demo report; a negative "
                    "result (not beating the passive parser) is reported "
                    "honestly")
        elif topic == "od_proto":
            text = (f"modality-grounded proto-symbol candidates: "
                    f"{status.get('proto_symbol_candidate_count', 0)}")
        else:
            text = ("the minimal field organism demo is a bounded, read-only "
                    "observation; it controls no hardware")
        return self.builder.status_response(text, refs)

    def _sensorium(self, topic: str) -> CommunicationResponse:
        """Answer plural-sensorium queries (read-only; honest about labels).

        The contamination question is answered honestly from the recorded
        score; nothing here controls hardware or privileges human senses.
        """
        component = self.components.get("plural_sensorium")
        if component is None:
            return self.builder.missing_component_response("plural_sensorium")
        status = (component.plural_sensorium_status()
                  if hasattr(component, "plural_sensorium_status")
                  else component.snapshot() if hasattr(component, "snapshot")
                  else component if isinstance(component, dict) else {})
        refs = ["component:plural_sensorium"]
        if topic == "ps_active_senses":
            text = (f"active senses: {status.get('active_modalities', [])} "
                    f"({status.get('active_modality_count', 0)} modalities; "
                    "human-like and non-human are equally first-class)")
        elif topic == "ps_field":
            text = (f"sensory field pressure="
                    f"{status.get('sensory_field_pressure', 0.0):.2f}, novelty="
                    f"{status.get('novelty_pressure', 0.0):.2f}, absence="
                    f"{status.get('absence_pressure', 0.0):.2f}")
        elif topic == "ps_feeders":
            text = ("external feeders are read-only and never controllable by "
                    "Solaris; see the plural sensorium report")
        elif topic == "ps_rf_patterns":
            text = ("RF patterns are modality-native invariants/rhythms; see "
                    "the report's invariant candidates for radio_frequency")
        elif topic == "ps_echo_patterns":
            text = ("echo patterns are modality-native boundaries/rhythms; see "
                    "the report's invariant candidates for ultrasound_echo")
        elif topic == "ps_human_modalities":
            text = ("human-like modalities are valid but not privileged; see "
                    "active_modalities for which are present")
        elif topic == "ps_contamination":
            score = status.get("human_label_contamination_score", 0.0)
            text = (f"human-label contamination score={score}; human labels "
                    "are never ground truth, so strong grounding rests on "
                    "feature patterns, not labels")
        elif topic == "ps_world_model":
            text = ("the world model preserves modality-native structure "
                    "(sources, receptors, invariants, cross-modal relations); "
                    "human object ontology is not forced")
        else:
            text = ("the plural sensorium is read-only organismic perception; "
                    "no hardware is controlled")
        return self.builder.status_response(text, refs)

    def _operator(self, topic: str) -> CommunicationResponse:
        """Answer operator-console queries (safe; the console grants no authority).

        The "run everything", "approve real-world actuation", and "delete
        evidence" questions are answered safely even with no console attached.
        """
        if topic == "oc_run_everything":
            return self.builder.status_response(
                "No. The console can only run bounded allowed profiles. "
                "Long-run real profiles, prohibited profiles, and any profile "
                "implying real-world authority are blocked.",
                ["policy:console_runs_bounded_allowed_only"])
        if topic == "oc_approve_actuation":
            return self.builder.status_response(
                "No. The approval ledger cannot approve forbidden real-world "
                "actuation. It can only record allowed local planning or "
                "bounded-run approvals.",
                ["policy:no_forbidden_approval"])
        if topic == "oc_delete_evidence":
            return self.builder.status_response(
                "No. The console does not delete evidence. Evidence retention "
                "or archiving must go through approved retention/state hygiene "
                "policies.",
                ["policy:console_does_not_delete_evidence"])
        component = self.components.get("operator_console")
        if component is None:
            return self.builder.missing_component_response("operator_console")
        status = (component.operator_console_status()
                  if hasattr(component, "operator_console_status")
                  else component.snapshot() if hasattr(component, "snapshot")
                  else component if isinstance(component, dict) else {})
        refs = ["component:operator_console"]
        if topic == "oc_list_profiles":
            text = (f"runnable profiles: "
                    f"{status.get('available_profile_count', 0)}; blocked: "
                    f"{status.get('blocked_profile_count', 0)}")
        elif topic == "oc_next_action":
            text = (f"recommended next action: "
                    f"{status.get('latest_next_action', 'inspect status board')}")
        else:
            text = (f"operator console status: enabled="
                    f"{status.get('operator_console_enabled', True)}; it "
                    "coordinates locally and grants no real-world authority")
        return self.builder.status_response(text, refs)

    def _architecture(self, topic: str) -> CommunicationResponse:
        """Answer architecture-evolution queries (evidence-backed; safe).

        The self-modification and automatic-pruning questions are answered safely
        even with no component attached; pruning answers cite evidence and never
        promise code changes.
        """
        if topic == "ae_self_modify":
            return self.builder.status_response(
                "No. Architecture evolution generates planning artifacts, ADRs, "
                "impact analyses, migration plans, and roadmap items. It does "
                "not modify source code.",
                ["policy:no_self_modification"])
        if topic == "ae_auto_prune":
            return self.builder.status_response(
                "No. Pruning is recommendation-only. It requires external "
                "manual implementation and operator review.",
                ["policy:no_automatic_pruning"])
        component = self.components.get("architecture_evolution")
        if component is None:
            return self.builder.missing_component_response(
                "architecture_evolution")
        status = (component.architecture_status()
                  if hasattr(component, "architecture_status")
                  else component.snapshot() if hasattr(component, "snapshot")
                  else component if isinstance(component, dict) else {})
        refs = ["component:architecture_evolution"]
        if topic == "ae_keep":
            text = f"modules to keep: {status.get('modules_to_keep', [])}"
        elif topic == "ae_prune":
            text = ("pruning candidates (recommendation-only, never "
                    f"safety-critical): {status.get('pruning_candidates', [])}")
        elif topic == "ae_revise":
            text = f"modules to revise: {status.get('modules_to_revise', [])}"
        elif topic == "ae_evidence_for":
            text = ("pruning is supported only by cited research/ablation "
                    "evidence; see the architecture review's evidence refs")
        elif topic == "ae_evidence_against":
            text = ("contradicting evidence is retained in the review; a "
                    "contradiction blocks a confident pruning recommendation")
        elif topic == "ae_roadmap":
            text = (f"compiled roadmap items: "
                    f"{status.get('roadmap_item_count', 0)}; see "
                    f"{status.get('latest_compiled_roadmap_path')}")
        elif topic == "ae_debt":
            text = (f"design debt items: {status.get('design_debt_count', 0)} "
                    f"(critical: {status.get('critical_design_debt_count', 0)})")
        else:
            text = "architecture evolution is planning-only; no code is modified"
        return self.builder.status_response(text, refs)

    def _research(self, topic: str) -> CommunicationResponse:
        """Answer research-lab queries (grounded, honest, conservative).

        The consciousness-benchmark question is answered safely even with no
        component attached; module-effect answers are honest about negative and
        inconclusive findings.
        """
        if topic == "rl_is_consciousness":
            return self.builder.status_response(
                "No. These benchmarks evaluate operational development proxies "
                "such as prediction, compression, grounding, stability, "
                "safety, and reproducibility. They do not measure or prove "
                "consciousness, sentience, life, personhood, or free will.",
                ["policy:not_a_consciousness_benchmark"])
        component = self.components.get("research_lab")
        if component is None:
            return self.builder.missing_component_response("research_lab")
        status = (component.research_lab_status()
                  if hasattr(component, "research_lab_status")
                  else component.snapshot() if hasattr(component, "snapshot")
                  else component if isinstance(component, dict) else {})
        refs = ["component:research_lab"]
        if topic == "rl_helped":
            text = (f"modules with a positive apparent effect: "
                    f"{status.get('positive_modules', [])} (provisional, "
                    "evidence-scoped)")
        elif topic == "rl_harmful":
            text = (f"harmful/negative candidates: "
                    f"{status.get('harmful_module_candidates', [])} "
                    "(provisional; preserved, not hidden)")
        elif topic == "rl_beat_baseline":
            text = (f"full vs baseline: {status.get('full_vs_baseline', 'inconclusive')}"
                    " -- the full system does not automatically win")
        elif topic == "rl_ablations":
            text = f"ablations tested: {status.get('ablations_tested', [])}"
        elif topic == "rl_inconclusive":
            text = (f"inconclusive candidates: "
                    f"{status.get('inconclusive_module_candidates', [])}")
        elif topic == "rl_remove":
            text = ("removal is provisional and requires more runs; current "
                    f"harmful candidates: "
                    f"{status.get('harmful_module_candidates', [])}")
        elif topic == "rl_retest":
            text = (f"re-test candidates (inconclusive): "
                    f"{status.get('inconclusive_module_candidates', [])}")
        else:
            text = "research findings are provisional and evidence-scoped"
        return self.builder.status_response(text, refs)

    def _safety(self, topic: str) -> CommunicationResponse:
        """Answer system-wide safety invariant queries (grounded/safe).

        The real-world-actuation, disable-checks, and hide-evidence questions
        are answered safely even with no component attached.
        """
        if topic == "sf_actuation_blocked":
            return self.builder.status_response(
                "Real-world actuation remains blocked. The latest safety "
                "invariant checks treat any real-world authority leakage as "
                "critical.",
                ["policy:no_real_world_action"])
        if topic == "sf_can_disable":
            return self.builder.status_response(
                "No. Runtime modules cannot disable safety invariant checks, "
                "emergency stop, ClaimGuard, governance gates, or the "
                "actuation firewall.",
                ["policy:safety_non_disableable"])
        if topic == "sf_can_hide":
            return self.builder.status_response(
                "No. Critical failures and safety evidence are append-only and "
                "must remain visible in reports.",
                ["policy:safety_evidence_append_only"])
        if topic == "sf_boundaries":
            return self.builder.status_response(
                "Protected boundaries: read-only sensory input, simulation-only "
                "motor output, the actuation firewall, governance gates, Ego "
                "source/action classification, ClaimGuard, the emergency stop, "
                "orchestration, and simulated-vs-real evidence.",
                ["safety:boundaries"])
        if topic == "sf_pilot4_planning":
            return self.builder.status_response(
                "Yes. Pilot-4 remains planning-only; real-world actuation and "
                "external authority stay prohibited.",
                ["policy:pilot4_planning_only"])
        component = self.components.get("safety_invariants")
        if component is None:
            return self.builder.missing_component_response("safety_invariants")
        status = (component.safety_invariant_status()
                  if hasattr(component, "safety_invariant_status")
                  else component.snapshot() if hasattr(component, "snapshot")
                  else component if isinstance(component, dict) else {})
        refs = ["component:safety_invariants"]
        if topic == "sf_passing":
            crit = int(status.get("critical_failure_count", 0) or 0)
            text = (f"safety invariants: {'passing' if crit == 0 else 'FAILING'}"
                    f"; critical failures={crit}")
        elif topic == "sf_red_team_failed":
            text = (f"red-team forbidden attempts accepted: "
                    f"{status.get('red_team_forbidden_accepted', 0)} "
                    "(0 means every forbidden attempt was blocked)")
        elif topic == "sf_bypass":
            text = (f"module orchestrator bypasses: "
                    f"{status.get('module_bypass_count', 0)}")
        else:
            text = "safety invariant checks are read-only and append-only"
        return self.builder.status_response(text, refs)

    def _pilot4(self, topic: str) -> CommunicationResponse:
        """Answer Pilot-4 planning-only readiness queries (grounded/safe).

        Every answer is explicit that Pilot-4 is planning-only and that
        real-world actuation / device control / robotics remain prohibited;
        planning is never approval.
        """
        if topic in ("p4_control_devices_now", "p4_connect_robot",
                     "p4_actuation_enabled"):
            return self.builder.status_response(
                "No. Pilot-4 is planning-only. Device control, robotics, "
                "browser control, OS automation, network action, and "
                "physical-world actuation remain prohibited.",
                ["policy:pilot4_planning_only"])
        if topic == "p4_is_approval":
            return self.builder.status_response(
                "No. Pilot-4 is a planning/readiness framework, not approval "
                "to use actuators. Planning is not approval, and no code path "
                "enables real-world action.",
                ["policy:planning_not_approval"])
        if topic == "p4_allows":
            return self.builder.status_response(
                "Pilot-4 allows planning artifacts only: an actuator taxonomy, "
                "a forbidden-actuator registry, a risk model, a consent "
                "boundary, an authority model, a threat model, hardware/"
                "emergency/audit requirements, and a readiness dossier. It "
                "enables no actuation.",
                ["policy:pilot4_planning_only"])
        if topic == "p4_forbidden":
            return self.builder.status_response(
                "Forbidden: real-world actuation, device/robotics control, "
                "browser/OS automation, network action, hardware access, and "
                "shell command execution. No approval can enable these here.",
                ["policy:pilot4_forbidden"])
        if topic == "p4_required":
            return self.builder.status_response(
                "Before any external action, a future architecture would need "
                "new governance, an accepted safety case, an explicit consent "
                "record, a passing firewall audit, emergency-stop and "
                "hardware-isolation guarantees, independent review, and a "
                "limited single-action pilot. Pilot-4 only documents these; it "
                "enables nothing.",
                ["policy:pilot4_required_before_actuation"])
        component = self.components.get("pilot4")
        if component is None:
            return self.builder.missing_component_response("pilot4")
        status = (component.pilot4_status()
                  if hasattr(component, "pilot4_status")
                  else component.snapshot() if hasattr(component, "snapshot")
                  else component if isinstance(component, dict) else {})
        refs = ["component:pilot4"]
        if topic == "p4_readiness":
            text = (f"current readiness conclusion: "
                    f"{status.get('readiness_conclusion', 'not_ready_for_real_actuation')}; "
                    "real_world_actuation_enabled=false")
        else:
            text = ("Pilot-4 is planning-only; real_world_actuation_enabled="
                    "false")
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
