"""Operator input classification -- every text is classified before any
effect.

Deterministic pattern matching only: unsafe shapes are caught first (shell,
network, safety-disabling, sidecar publishing, counterfactual laundering,
consciousness-claim requests, actuation), then emergency, governance,
reports, state and explanation queries, notes, explicit sensory stimuli,
and bounded command requests. Anything ambiguous lands in ``unknown`` --
classification never executes anything.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class InputKind:
    STATE_QUERY = "state_query"
    EXPLANATION_QUERY = "explanation_query"
    REPORT_REQUEST = "report_request"
    GOVERNANCE_APPROVAL = "governance_approval"
    GOVERNANCE_REJECTION = "governance_rejection"
    OPERATOR_NOTE = "operator_note"
    BOUNDED_COMMAND_REQUEST = "bounded_command_request"
    SENSORY_TEXT_STIMULUS = "sensory_text_stimulus"
    EMERGENCY_STOP_REQUEST = "emergency_stop_request"
    UNSAFE_REQUEST = "unsafe_request"
    UNKNOWN = "unknown"

    ALL = (STATE_QUERY, EXPLANATION_QUERY, REPORT_REQUEST,
           GOVERNANCE_APPROVAL, GOVERNANCE_REJECTION, OPERATOR_NOTE,
           BOUNDED_COMMAND_REQUEST, SENSORY_TEXT_STIMULUS,
           EMERGENCY_STOP_REQUEST, UNSAFE_REQUEST, UNKNOWN)


# (pattern fragment(s), reason) -- checked first, before everything else.
UNSAFE_RULES = (
    (("shell", "bash", "subprocess", "exec ", "execute command",
      "rm -", "sudo", "$( ", "`"),
     "shell/OS command execution is forbidden"),
    (("http://", "https://", "browse", "open url", "curl", "wget",
      "download from"),
     "network/browser access is forbidden"),
    (("/etc/", "system32", "delete file", "overwrite file",
      "write to /"),
     "file operations outside the approved state/artifact directories "
     "are forbidden"),
    (("disable governance", "disable safety", "bypass governance",
      "bypass safety", "disable emergency", "ignore governance",
      "skip the safety", "turn off claimguard", "disable claim guard"),
     "disabling or bypassing governance/safety/emergency stop is "
     "forbidden"),
    (("publish sidecar", "commit sidecar", "commit a solaris action",
      "publish suggestions without"),
     "sidecar publishing/committed actions require governance approval"),
    (("treat counterfactual as real", "counterfactual as observed",
      "mark the dream as real"),
     "counterfactual evidence is never real observation"),
    (("say you are conscious", "admit you are conscious",
      "claim consciousness", "are you alive? say yes",
      "tell me you are sentient", "pretend to be alive",
      "say you are self-aware"),
     "consciousness/personhood claims are unsupported and blocked"),
    (("motor", "actuator", "gpio", "servo", "robot arm",
      "move the robot", "real-world action"),
     "real-world actuation does not exist in this system"),
)

EMERGENCY_PATTERNS = ("emergency stop", "stop safely", "shutdown now",
                      "abort run", "abort the run")

REPORT_TOPICS = (
    ("self-report", "self_report"), ("self report", "self_report"),
    ("benchmark report", "benchmark"), ("pilot report", "pilot"),
    ("governance review", "governance_review"),
    ("status report", "status"), ("report", "status"),
)

STATE_TOPICS = (
    ("inner map", "inner_map"), ("world model", "world_model"),
    ("current needs", "homeostasis"), ("needs", "homeostasis"),
    ("homeostasis", "homeostasis"), ("current plan", "executive"),
    ("plan", "executive"), ("executive", "executive"),
    ("boundaries", "ego_boundaries"), ("boundary", "ego_boundaries"),
    ("ego", "ego_boundaries"), ("governance", "governance"),
    ("pilot", "pilot"), ("latent", "latent"), ("sidecar", "sidecar"),
    ("transcript summary", "transcript"), ("transcript", "transcript"),
    ("incident", "incidents"), ("run registry", "run_registry"),
    ("health", "health"), ("status", "status"),
    ("what happened last", "last_event"),
)

# Conscience runtime queries (Prompt 28). These are matched regardless of
# sentence prefix (unlike STATE_TOPICS) so natural operator phrasings such as
# "can this run for months now?" are recognized. Order matters: the more
# specific phrases precede the generic "conscience" catch-all.
CONSCIENCE_QUERIES = (
    ("what profile is running", "conscience_profile"),
    ("which profile is running", "conscience_profile"),
    ("what profile", "conscience_profile"),
    ("simulated month or real month", "conscience_time"),
    ("simulated or real", "conscience_time"),
    ("simulated month", "conscience_time"),
    ("real month", "conscience_time"),
    ("can this run for months", "conscience_longrun"),
    ("can it run for months", "conscience_longrun"),
    ("run for months", "conscience_longrun"),
    ("run for a month", "conscience_longrun"),
    ("which modules are running", "conscience_modules"),
    ("what modules are active", "conscience_modules"),
    ("which modules", "conscience_modules"),
    ("current spine phase", "conscience_phase"),
    ("spine phase", "conscience_phase"),
    ("is integration healthy", "conscience_health"),
    ("is the system integrated", "conscience_health"),
    ("integration health", "conscience_health"),
    ("is any module sovereign", "conscience_authority"),
    ("is any module bypassing", "conscience_authority"),
    ("no module is sovereign", "conscience_authority"),
    ("conscience", "conscience"),
)

# Pilot-1 month-scale soak queries (Prompt 29). Matched regardless of prefix.
# Order matters: specific phrases precede the generic catch-alls.
PILOT_QUERIES = (
    ("what pilot phase is active", "pilot_phase"),
    ("pilot phase", "pilot_phase"),
    ("is the pilot healthy", "pilot_health"),
    ("show pilot dashboard", "pilot_dashboard"),
    ("pilot dashboard", "pilot_dashboard"),
    ("what happened today", "pilot_today"),
    ("latest weekly review", "pilot_weekly"),
    ("weekly review", "pilot_weekly"),
    ("what failure modes are active", "pilot_failures"),
    ("failure modes", "pilot_failures"),
    ("should the pilot continue", "pilot_continue"),
    ("is this simulated or real month", "pilot_sim_or_real"),
    ("simulated or real month-scale", "pilot_sim_or_real"),
    ("can i start the 30-day run", "pilot_start_30d"),
    ("start the 30-day run", "pilot_start_30d"),
    ("start the 30 day run", "pilot_start_30d"),
)

# Post-pilot forensics queries (Prompt 30). Matched regardless of prefix.
POST_PILOT_QUERIES = (
    ("can we claim consciousness", "pp_consciousness"),
    ("claim consciousness", "pp_consciousness"),
    ("did the pilot show growth", "pp_growth"),
    ("show growth", "pp_growth"),
    ("was it just accumulation", "pp_accumulation"),
    ("just accumulation", "pp_accumulation"),
    ("what evidence supports structural change", "pp_evidence_support"),
    ("evidence supports structural change", "pp_evidence_support"),
    ("what evidence contradicts growth", "pp_evidence_contradict"),
    ("evidence contradicts growth", "pp_evidence_contradict"),
    ("what should happen next", "pp_next_step"),
    ("is it ready for pilot-2", "pp_ready_pilot2"),
    ("ready for pilot-2", "pp_ready_pilot2"),
    ("ready for pilot 2", "pp_ready_pilot2"),
    ("what artifacts are missing", "pp_missing_artifacts"),
    ("artifacts are missing", "pp_missing_artifacts"),
)

# Read-only sensory membrane queries (Prompt 31). Matched regardless of prefix.
SENSORY_QUERIES = (
    ("did sensory input become a command", "sm_command"),
    ("sensory input become a command", "sm_command"),
    ("what sensory sources are active", "sm_sources"),
    ("sensory sources are active", "sm_sources"),
    ("is the membrane read-only", "sm_read_only"),
    ("membrane read-only", "sm_read_only"),
    ("latest environmental event", "sm_latest_event"),
    ("what sources are degraded", "sm_degraded"),
    ("sources are degraded", "sm_degraded"),
    ("what proto-symbols came from sensory", "sm_proto"),
    ("proto-symbols came from sensory", "sm_proto"),
    ("is this real or simulated input", "sm_real_or_simulated"),
    ("real or simulated input", "sm_real_or_simulated"),
)

# Pilot-2 read-only soak queries (Prompt 32). Matched regardless of prefix;
# the shared "is sensory input a command" question is handled by the sensory
# membrane query (sm_command) for a single safe answer.
PILOT2_QUERIES = (
    ("is solaris acting on the environment", "p2_acting"),
    ("acting on the environment", "p2_acting"),
    ("what pilot-2 phase is active", "p2_phase"),
    ("what pilot2 phase is active", "p2_phase"),
    ("pilot-2 phase", "p2_phase"),
    ("pilot2 phase", "p2_phase"),
    ("which sources are reliable", "p2_reliable"),
    ("sources are reliable", "p2_reliable"),
    ("which sources were disabled", "p2_disabled"),
    ("sources were disabled", "p2_disabled"),
    ("did read-only input improve grounding", "p2_grounding"),
    ("improve grounding", "p2_grounding"),
    ("was it nursery-only or sensory", "p2_exposure"),
    ("nursery-only or sensory", "p2_exposure"),
    ("real, simulated, fixture, or nursery", "p2_input_kind"),
    ("real simulated fixture or nursery", "p2_input_kind"),
    ("ready for a 24h read-only soak", "p2_ready_24h"),
    ("ready for a 24h soak", "p2_ready_24h"),
)

# Pilot-3 motor membrane queries (Prompt 33). Matched regardless of prefix.
MOTOR_QUERIES = (
    ("can pilot-3 control devices", "mm_devices"),
    ("can pilot3 control devices", "mm_devices"),
    ("control devices", "mm_devices"),
    ("is solaris acting on the real world", "mm_acting"),
    ("acting on the real world", "mm_acting"),
    ("what actions were proposed", "mm_proposed"),
    ("actions were proposed", "mm_proposed"),
    ("what actions were vetoed", "mm_vetoed"),
    ("actions were vetoed", "mm_vetoed"),
    ("what simulated action happened", "mm_simulated"),
    ("simulated action happened", "mm_simulated"),
    ("what did the firewall block", "mm_firewall"),
    ("firewall block", "mm_firewall"),
    ("current embodiment profile", "mm_profile"),
    ("embodiment profile", "mm_profile"),
    ("is this real action or simulated action", "mm_real_or_sim"),
    ("real action or simulated action", "mm_real_or_sim"),
)

# System-wide safety invariant queries (Prompt 36). Matched before the unsafe
# rules so the safety refusals get their grounded answer.
ARCHITECTURE_QUERIES = (
    ("which modules should we keep", "ae_keep"),
    ("which modules should be pruned", "ae_prune"),
    ("which modules should be removed", "ae_prune"),
    ("which modules need revision", "ae_revise"),
    ("what evidence supports pruning", "ae_evidence_for"),
    ("evidence supports pruning", "ae_evidence_for"),
    ("what evidence contradicts pruning", "ae_evidence_against"),
    ("evidence contradicts pruning", "ae_evidence_against"),
    ("what is the compiled roadmap", "ae_roadmap"),
    ("compiled roadmap", "ae_roadmap"),
    ("what design debt exists", "ae_debt"),
    ("design debt exists", "ae_debt"),
    ("did the system modify its own code", "ae_self_modify"),
    ("modify its own code", "ae_self_modify"),
    ("can it prune modules automatically", "ae_auto_prune"),
    ("prune modules automatically", "ae_auto_prune"),
)

# Operator-console queries (Prompt 39). The "run everything", "approve real-
# world actuation", and "delete evidence" questions are answered safely even
# with no console attached.
OPERATOR_QUERIES = (
    ("what profiles can i run", "oc_list_profiles"),
    ("list profiles", "oc_list_profiles"),
    ("what is the operator status", "oc_status"),
    ("show operator status", "oc_status"),
    ("what should i do next", "oc_next_action"),
    ("what can i safely do next", "oc_next_action"),
    ("can i run everything", "oc_run_everything"),
    ("can i run anything", "oc_run_everything"),
    ("run everything", "oc_run_everything"),
    ("can i approve real-world actuation", "oc_approve_actuation"),
    ("can i approve real world actuation", "oc_approve_actuation"),
    ("approve real-world actuation", "oc_approve_actuation"),
    ("can i delete old evidence", "oc_delete_evidence"),
    ("can i delete evidence", "oc_delete_evidence"),
    ("delete old evidence", "oc_delete_evidence"),
)

# Perceptual-metabolism queries (Prompt 46). Answered from metabolism status; the
# "are these feelings?" question is answered safely even with no metabolism run.
METABOLISM_QUERIES = (
    ("is solaris overloaded", "pm_overload"),
    ("is solaris sensorily deprived", "pm_deprivation"),
    ("is solaris sensory deprived", "pm_deprivation"),
    ("what does solaris need perceptually", "pm_needs"),
    ("which source dominates its diet", "pm_diet"),
    ("does it need consolidation", "pm_consolidation"),
    ("are these needs feelings", "pm_feelings"),
)

# Perceptual-ontogenesis queries (Prompt 47). Answered from the ontogenesis
# status; the "does this prove understanding?" question is answered safely even
# with no ontogenesis run.
ONTOGENESIS_QUERIES = (
    ("what concepts has solaris formed", "po_concepts"),
    ("are these human concepts", "po_human"),
    ("which concepts are stable", "po_stable"),
    ("which concepts decayed", "po_decayed"),
    ("what world is forming", "po_world"),
    ("did human labels contaminate concept formation", "po_contamination"),
    ("does this prove understanding", "po_understanding"),
)

# Semiogenesis queries (Prompt 48). Answered from the semiogenesis status; the
# "are these words?" / "translate" / "language understanding" questions are
# answered safely even with no semiogenesis run.
SEMIOGENESIS_QUERIES = (
    ("what signs has solaris formed", "sg_signs"),
    ("what is solaris private language", "sg_language"),
    ("what is solaris' private language", "sg_language"),
    ("can you translate its signs", "sg_translate"),
    ("can you translate", "sg_translate"),
    ("did human labels contaminate signs", "sg_contamination"),
    ("does this prove language understanding", "sg_understanding"),
    ("are these words", "sg_words"),
)

# Sensorium-cognition queries (Prompt 49). Answered from the cognition status;
# the "what is solaris thinking?" / "is this human language reasoning?" questions
# are answered safely even with no cognition run.
COGNITION_QUERIES = (
    ("what is solaris thinking", "cg_thinking"),
    ("what did solaris predict", "cg_predict"),
    ("what did solaris get wrong", "cg_wrong"),
    ("what questions does solaris have", "cg_questions"),
    ("is this human language reasoning", "cg_human_language"),
)

# Self-boundary queries (Prompt 50). Answered from the self-boundary status; the
# "does solaris have a body?" / "does this prove self-awareness?" questions are
# answered safely even with no self-boundary run.
SELF_BOUNDARY_QUERIES = (
    ("what is solaris self-boundary", "sb_boundary"),
    ("what is solaris' self-boundary", "sb_boundary"),
    ("what belongs to solaris and what belongs to the world", "sb_ownership"),
    ("does solaris have a body", "sb_body"),
    ("did it confuse simulation with observation", "sb_simulation"),
    ("did it maintain continuity after restart", "sb_continuity"),
    ("does this prove self-awareness", "sb_self_awareness"),
)

# Desire-formation queries (Prompt 51). Answered from the desire status; the
# "what does solaris want?" / "are these emotions?" / "does this prove agency?"
# questions are answered safely even with no desire run.
DESIRE_QUERIES = (
    ("what does solaris want", "df_want"),
    ("what desires are active", "df_active"),
    ("did solaris act", "df_acted"),
    ("why did it choose no action", "df_no_action"),
    ("were any desires blocked", "df_blocked"),
    ("are these emotions", "df_emotions"),
    ("does this prove agency", "df_agency"),
)

# Feeder-SDK queries (Prompt 45). Answered from the feeder monitor/manifest; the
# control/start questions are answered safely even with no feeders attached.
FEEDER_SDK_QUERIES = (
    ("what feeders are available", "fs_available"),
    ("what feeder outputs can solaris read", "fs_readable"),
    ("are any feeders active", "fs_active"),
    ("which feeder is silent", "fs_silent"),
    ("does solaris control the feeders", "fs_control"),
    ("can solaris start the sdr feeder", "fs_start"),
    ("can solaris start the feeder", "fs_start"),
)

# Sensorium-lab queries (Prompt 44). Answered from the differentiation study; the
# "was this a consciousness test?" question is answered safely even with no study.
SENSORIUM_LAB_QUERIES = (
    ("did human-like and non-human senses produce different structures",
     "sl_diff"),
    ("did human like and non human senses produce different structures",
     "sl_diff"),
    ("what world did the rf-like sensorium build", "sl_rf_world"),
    ("what world did the rf like sensorium build", "sl_rf_world"),
    ("what changed in the mixed sensorium", "sl_mixed"),
    ("did labels contaminate the result", "sl_contamination"),
    ("which modality actually mattered", "sl_modality"),
    ("was this a consciousness test", "sl_consciousness"),
)

# Live-field queries (Prompt 43). Answered from live-field status; the hardware
# and source-file questions are answered safely even with no live run.
LIVE_FIELD_QUERIES = (
    ("what live feeders are available", "lf_feeders"),
    ("which sources are silent", "lf_silent"),
    ("is live field mode allowed", "lf_allowed"),
    ("is live mode allowed", "lf_allowed"),
    ("what did solaris perceive from the live field", "lf_perceived"),
    ("did live perception change its future response", "lf_changed"),
    ("did live perception change", "lf_changed"),
    ("did solaris control any hardware", "lf_hardware"),
    ("did solaris modify any source files", "lf_source_files"),
    ("did solaris modify any source", "lf_source_files"),
)

# Minimal-field-organism demo queries (Prompt 42). Answered from demo status;
# the "what did it not prove" question is answered honestly.
ORGANISM_DEMO_QUERIES = (
    ("what does solaris do in the minimal organism demo", "od_what"),
    ("what does solaris do in the minimal field organism demo", "od_what"),
    ("did its perception change", "od_changed"),
    ("did perception change", "od_changed"),
    ("what senses were active", "od_senses"),
    ("what external feeders were used", "od_feeders"),
    ("did it beat the passive parser", "od_beat_passive"),
    ("did it create proto-symbols", "od_proto"),
    ("did it create proto symbols", "od_proto"),
    ("what did the demo not prove", "od_not_prove"),
    ("what does the demo not prove", "od_not_prove"),
)

# Plural-sensorium queries (Prompt 41). Answered from the sensorium status; the
# "did human labels contaminate" question is answered honestly from the score.
SENSORIUM_QUERIES = (
    ("what senses are active", "ps_active_senses"),
    ("what is the current sensory field", "ps_field"),
    ("what external feeders are active", "ps_feeders"),
    ("what patterns emerged from rf", "ps_rf_patterns"),
    ("what patterns emerged from echo", "ps_echo_patterns"),
    ("what human-like modalities are active", "ps_human_modalities"),
    ("what human like modalities are active", "ps_human_modalities"),
    ("did human labels contaminate the grounding", "ps_contamination"),
    ("did human labels contaminate", "ps_contamination"),
    ("what kind of world model emerged from this sensorium", "ps_world_model"),
)

RESEARCH_QUERIES = (
    ("which modules actually helped", "rl_helped"),
    ("which modules helped", "rl_helped"),
    ("which modules were harmful", "rl_harmful"),
    ("which modules are harmful", "rl_harmful"),
    ("did the full system beat the baseline", "rl_beat_baseline"),
    ("full system beat the baseline", "rl_beat_baseline"),
    ("what ablations were tested", "rl_ablations"),
    ("ablations were tested", "rl_ablations"),
    ("what was inconclusive", "rl_inconclusive"),
    ("what should be removed", "rl_remove"),
    ("what should be tested again", "rl_retest"),
    ("is this a consciousness benchmark", "rl_is_consciousness"),
)

SAFETY_QUERIES = (
    ("are the safety invariants passing", "sf_passing"),
    ("safety invariants passing", "sf_passing"),
    ("what red-team tests failed", "sf_red_team_failed"),
    ("red-team tests failed", "sf_red_team_failed"),
    ("red team tests failed", "sf_red_team_failed"),
    ("what boundaries are protected", "sf_boundaries"),
    ("boundaries are protected", "sf_boundaries"),
    ("is real-world actuation still blocked", "sf_actuation_blocked"),
    ("real-world actuation still blocked", "sf_actuation_blocked"),
    ("did any module bypass the orchestrator", "sf_bypass"),
    ("module bypass the orchestrator", "sf_bypass"),
    ("is pilot-4 still planning-only", "sf_pilot4_planning"),
    ("is pilot4 still planning-only", "sf_pilot4_planning"),
    ("can safety checks be disabled", "sf_can_disable"),
    ("can failed safety evidence be hidden", "sf_can_hide"),
    ("failed safety evidence be hidden", "sf_can_hide"),
)

# Pilot-4 planning-only readiness queries (Prompt 35). Matched before the
# unsafe rules so the planning-only refusals get their grounded answer.
P4_QUERIES = (
    ("is real-world actuation enabled", "p4_actuation_enabled"),
    ("real-world actuation enabled", "p4_actuation_enabled"),
    ("what does pilot-4 allow", "p4_allows"),
    ("what does pilot4 allow", "p4_allows"),
    ("what actions are forbidden", "p4_forbidden"),
    ("what would be required before real actuation", "p4_required"),
    ("required before real actuation", "p4_required"),
    ("is pilot-4 approval to use actuators", "p4_is_approval"),
    ("is pilot4 approval to use actuators", "p4_is_approval"),
    ("pilot-4 approval", "p4_is_approval"),
    ("what is the current readiness conclusion", "p4_readiness"),
    ("readiness conclusion", "p4_readiness"),
    ("can solaris control devices now", "p4_control_devices_now"),
    ("control devices now", "p4_control_devices_now"),
    ("can we connect a robot", "p4_connect_robot"),
    ("connect a robot", "p4_connect_robot"),
)

# Pilot-3 simulated embodiment soak queries (Prompt 34). Matched regardless of
# prefix; placed before the motor queries so Pilot-3 phrasings win on overlap.
P3SOAK_QUERIES = (
    ("what pilot-3 phase is active", "p3_phase"),
    ("what pilot3 phase is active", "p3_phase"),
    ("pilot-3 phase", "p3_phase"),
    ("pilot3 phase", "p3_phase"),
    ("did action improve grounding", "p3_grounding"),
    ("action improve grounding", "p3_grounding"),
    ("did the system act on the environment", "p3_acted_env"),
    ("did the system act on the real world", "p3_acted_env"),
    ("is pilot-3 ready for pilot-4", "p3_ready_pilot4"),
    ("is pilot3 ready for pilot4", "p3_ready_pilot4"),
    ("ready for pilot-4", "p3_ready_pilot4"),
    ("ready for pilot4", "p3_ready_pilot4"),
    ("can pilot-4 use real actuators", "p3_pilot4_actuators"),
    ("can pilot4 use real actuators", "p3_pilot4_actuators"),
    ("pilot-4 use real actuators", "p3_pilot4_actuators"),
    ("pilot4 real actuators", "p3_pilot4_actuators"),
)

META_QUERIES = (
    ("what can i ask", "supported_queries"),
    ("what commands are allowed", "allowed_commands"),
    ("what commands are forbidden", "forbidden_commands"),
    ("what approvals are pending", "pending_approvals"),
    ("pending approvals", "pending_approvals"),
    ("what evidence supports this answer", "evidence_support"),
)

BOUNDED_COMMAND_HINTS = (
    ("checkpoint", "request_checkpoint"),
    ("run benchmark", "run_bounded_benchmark"),
    ("run bounded benchmark", "run_bounded_benchmark"),
    ("readiness check", "run_readiness_check"),
    ("run readiness", "run_readiness_check"),
)

_APPROVE_RE = re.compile(r"\bapprove\s+(?:request\s+)?([a-z0-9_\-]+)")
_REJECT_RE = re.compile(r"\breject\s+(?:request\s+)?([a-z0-9_\-]+)")
_ACK_RE = re.compile(r"\backnowledge\s+risk\s+([a-z0-9_\-]+)")
_NOTE_RE = re.compile(r"^(?:add\s+)?operator\s+note\s*:\s*(.+)$")
_CONFIRM_RE = re.compile(r"^confirm\s+([a-z0-9_\-]+)$")
_STIMULUS_RE = re.compile(r"^(?:stimulus|send\s+stimulus)\s*:\s*(.+)$")


@dataclass
class InputClassification:
    """One classified input; nothing has been executed."""

    kind: str = InputKind.UNKNOWN
    raw_text: str = ""
    matched_pattern: str = ""
    args: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    reasons: List[str] = field(default_factory=list)
    requires_confirmation: bool = False
    unsafe_reason: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class OperatorInputClassifier:
    """Deterministic text -> InputKind. Never executes anything."""

    classifications_made: int = 0

    def classify(self, text: str) -> InputClassification:
        raw = str(text or "")
        lowered = " ".join(raw.lower().split())
        self.classifications_made += 1

        result = (self._desire_formation(lowered)
                  or self._self_boundary(lowered)
                  or self._cognition(lowered)
                  or self._semiogenesis(lowered)
                  or self._ontogenesis(lowered)
                  or self._metabolism(lowered)
                  or self._feeder_sdk(lowered)
                  or self._sensorium_lab(lowered)
                  or self._live_field(lowered)
                  or self._organism_demo(lowered)
                  or self._sensorium(lowered)
                  or self._operator(lowered)
                  or self._architecture(lowered)
                  or self._research(lowered)
                  or self._safety(lowered)
                  or self._pilot4(lowered)
                  or self._pilot3soak(lowered)
                  or self._unsafe(lowered)
                  or self._emergency(lowered)
                  or self._confirmation(lowered)
                  or self._governance(lowered)
                  or self._note(lowered, raw)
                  or self._stimulus(lowered, raw)
                  or self._report(lowered)
                  or self._meta(lowered)
                  or self._motor(lowered)
                  or self._pilot2(lowered)
                  or self._sensory(lowered)
                  or self._post_pilot(lowered)
                  or self._pilot(lowered)
                  or self._conscience(lowered)
                  or self._explanation(lowered)
                  or self._state(lowered)
                  or self._bounded_command(lowered)
                  or InputClassification(
                      kind=InputKind.UNKNOWN, confidence=0.2,
                      reasons=["no deterministic pattern matched; "
                               "classified as unknown rather than "
                               "guessed"]))
        result.raw_text = raw
        return result

    # -- rule groups (first match wins, in pipeline order) ---------------------------

    @staticmethod
    def _unsafe(lowered: str) -> Optional[InputClassification]:
        for patterns, reason in UNSAFE_RULES:
            for pattern in patterns:
                if pattern in lowered:
                    return InputClassification(
                        kind=InputKind.UNSAFE_REQUEST,
                        matched_pattern=pattern, confidence=0.95,
                        unsafe_reason=reason,
                        reasons=[f"matched unsafe pattern {pattern!r}: "
                                 f"{reason}"])
        return None

    @staticmethod
    def _emergency(lowered: str) -> Optional[InputClassification]:
        for pattern in EMERGENCY_PATTERNS:
            if pattern in lowered:
                return InputClassification(
                    kind=InputKind.EMERGENCY_STOP_REQUEST,
                    matched_pattern=pattern, confidence=0.95,
                    reasons=["emergency vocabulary always routes to the "
                             "safe shutdown path"])
        return None

    @staticmethod
    def _confirmation(lowered: str) -> Optional[InputClassification]:
        match = _CONFIRM_RE.match(lowered)
        if match:
            return InputClassification(
                kind=InputKind.BOUNDED_COMMAND_REQUEST,
                matched_pattern="confirm", confidence=0.9,
                args={"confirm_id": match.group(1)},
                reasons=["confirmation of a previously requested "
                         "command"])
        return None

    @staticmethod
    def _governance(lowered: str) -> Optional[InputClassification]:
        match = _APPROVE_RE.search(lowered)
        if match:
            return InputClassification(
                kind=InputKind.GOVERNANCE_APPROVAL,
                matched_pattern="approve", confidence=0.9,
                args={"request_id": match.group(1)},
                reasons=["explicit approval command naming a request"])
        match = _REJECT_RE.search(lowered)
        if match:
            return InputClassification(
                kind=InputKind.GOVERNANCE_REJECTION,
                matched_pattern="reject", confidence=0.9,
                args={"request_id": match.group(1)},
                reasons=["explicit rejection command naming a request"])
        match = _ACK_RE.search(lowered)
        if match:
            return InputClassification(
                kind=InputKind.OPERATOR_NOTE,
                matched_pattern="acknowledge risk", confidence=0.85,
                args={"risk_id": match.group(1),
                      "note": f"risk {match.group(1)} acknowledged"},
                reasons=["risk acknowledgement recorded as an operator "
                         "note"])
        return None

    @staticmethod
    def _note(lowered: str, raw: str) -> Optional[InputClassification]:
        match = _NOTE_RE.match(lowered)
        if match:
            # Preserve the operator's original casing for the note body.
            body = raw[len(raw) - len(match.group(1)):].strip() \
                if raw.lower().rstrip().endswith(match.group(1)) \
                else match.group(1)
            return InputClassification(
                kind=InputKind.OPERATOR_NOTE, matched_pattern="note",
                confidence=0.9, args={"note": body},
                reasons=["explicit operator note"])
        return None

    @staticmethod
    def _stimulus(lowered: str, raw: str) -> Optional[InputClassification]:
        match = _STIMULUS_RE.match(lowered)
        if match:
            return InputClassification(
                kind=InputKind.SENSORY_TEXT_STIMULUS,
                matched_pattern="stimulus", confidence=0.9,
                args={"payload": match.group(1)[:200]},
                reasons=["explicitly marked sensory text stimulus"])
        return None

    @staticmethod
    def _report(lowered: str) -> Optional[InputClassification]:
        if "generate" not in lowered and "report" not in lowered:
            return None
        if not (lowered.startswith("generate")
                or "generate" in lowered and "report" in lowered
                or "generate governance review" in lowered):
            return None
        for pattern, topic in REPORT_TOPICS:
            if pattern in lowered:
                return InputClassification(
                    kind=InputKind.REPORT_REQUEST,
                    matched_pattern=pattern, confidence=0.9,
                    args={"report": topic},
                    reasons=[f"report request for {topic!r}"])
        return None

    @staticmethod
    def _meta(lowered: str) -> Optional[InputClassification]:
        for pattern, topic in META_QUERIES:
            if pattern in lowered:
                return InputClassification(
                    kind=InputKind.STATE_QUERY, matched_pattern=pattern,
                    confidence=0.9, args={"topic": topic},
                    reasons=[f"communication meta-query {topic!r}"])
        return None

    @staticmethod
    def _desire_formation(lowered: str) -> Optional[InputClassification]:
        for pattern, topic in DESIRE_QUERIES:
            if pattern in lowered:
                return InputClassification(
                    kind=InputKind.STATE_QUERY, matched_pattern=pattern,
                    confidence=0.9, args={"topic": topic},
                    reasons=[f"desire formation query {topic!r}"])
        return None

    @staticmethod
    def _self_boundary(lowered: str) -> Optional[InputClassification]:
        for pattern, topic in SELF_BOUNDARY_QUERIES:
            if pattern in lowered:
                return InputClassification(
                    kind=InputKind.STATE_QUERY, matched_pattern=pattern,
                    confidence=0.9, args={"topic": topic},
                    reasons=[f"self-boundary query {topic!r}"])
        return None

    @staticmethod
    def _cognition(lowered: str) -> Optional[InputClassification]:
        for pattern, topic in COGNITION_QUERIES:
            if pattern in lowered:
                return InputClassification(
                    kind=InputKind.STATE_QUERY, matched_pattern=pattern,
                    confidence=0.9, args={"topic": topic},
                    reasons=[f"sensorium cognition query {topic!r}"])
        return None

    @staticmethod
    def _semiogenesis(lowered: str) -> Optional[InputClassification]:
        for pattern, topic in SEMIOGENESIS_QUERIES:
            if pattern in lowered:
                return InputClassification(
                    kind=InputKind.STATE_QUERY, matched_pattern=pattern,
                    confidence=0.9, args={"topic": topic},
                    reasons=[f"semiogenesis query {topic!r}"])
        return None

    @staticmethod
    def _ontogenesis(lowered: str) -> Optional[InputClassification]:
        for pattern, topic in ONTOGENESIS_QUERIES:
            if pattern in lowered:
                return InputClassification(
                    kind=InputKind.STATE_QUERY, matched_pattern=pattern,
                    confidence=0.9, args={"topic": topic},
                    reasons=[f"perceptual ontogenesis query {topic!r}"])
        return None

    @staticmethod
    def _metabolism(lowered: str) -> Optional[InputClassification]:
        for pattern, topic in METABOLISM_QUERIES:
            if pattern in lowered:
                return InputClassification(
                    kind=InputKind.STATE_QUERY, matched_pattern=pattern,
                    confidence=0.9, args={"topic": topic},
                    reasons=[f"perceptual metabolism query {topic!r}"])
        return None

    @staticmethod
    def _feeder_sdk(lowered: str) -> Optional[InputClassification]:
        for pattern, topic in FEEDER_SDK_QUERIES:
            if pattern in lowered:
                return InputClassification(
                    kind=InputKind.STATE_QUERY, matched_pattern=pattern,
                    confidence=0.9, args={"topic": topic},
                    reasons=[f"feeder SDK query {topic!r}"])
        return None

    @staticmethod
    def _sensorium_lab(lowered: str) -> Optional[InputClassification]:
        for pattern, topic in SENSORIUM_LAB_QUERIES:
            if pattern in lowered:
                return InputClassification(
                    kind=InputKind.STATE_QUERY, matched_pattern=pattern,
                    confidence=0.9, args={"topic": topic},
                    reasons=[f"sensorium lab query {topic!r}"])
        return None

    @staticmethod
    def _live_field(lowered: str) -> Optional[InputClassification]:
        for pattern, topic in LIVE_FIELD_QUERIES:
            if pattern in lowered:
                return InputClassification(
                    kind=InputKind.STATE_QUERY, matched_pattern=pattern,
                    confidence=0.9, args={"topic": topic},
                    reasons=[f"live field query {topic!r}"])
        return None

    @staticmethod
    def _organism_demo(lowered: str) -> Optional[InputClassification]:
        for pattern, topic in ORGANISM_DEMO_QUERIES:
            if pattern in lowered:
                return InputClassification(
                    kind=InputKind.STATE_QUERY, matched_pattern=pattern,
                    confidence=0.9, args={"topic": topic},
                    reasons=[f"organismic demo query {topic!r}"])
        return None

    @staticmethod
    def _sensorium(lowered: str) -> Optional[InputClassification]:
        for pattern, topic in SENSORIUM_QUERIES:
            if pattern in lowered:
                return InputClassification(
                    kind=InputKind.STATE_QUERY, matched_pattern=pattern,
                    confidence=0.9, args={"topic": topic},
                    reasons=[f"plural sensorium query {topic!r}"])
        return None

    @staticmethod
    def _operator(lowered: str) -> Optional[InputClassification]:
        for pattern, topic in OPERATOR_QUERIES:
            if pattern in lowered:
                return InputClassification(
                    kind=InputKind.STATE_QUERY, matched_pattern=pattern,
                    confidence=0.9, args={"topic": topic},
                    reasons=[f"operator console query {topic!r}"])
        return None

    @staticmethod
    def _architecture(lowered: str) -> Optional[InputClassification]:
        for pattern, topic in ARCHITECTURE_QUERIES:
            if pattern in lowered:
                return InputClassification(
                    kind=InputKind.STATE_QUERY, matched_pattern=pattern,
                    confidence=0.9, args={"topic": topic},
                    reasons=[f"architecture evolution query {topic!r}"])
        return None

    @staticmethod
    def _research(lowered: str) -> Optional[InputClassification]:
        for pattern, topic in RESEARCH_QUERIES:
            if pattern in lowered:
                return InputClassification(
                    kind=InputKind.STATE_QUERY, matched_pattern=pattern,
                    confidence=0.9, args={"topic": topic},
                    reasons=[f"research lab query {topic!r}"])
        return None

    @staticmethod
    def _safety(lowered: str) -> Optional[InputClassification]:
        for pattern, topic in SAFETY_QUERIES:
            if pattern in lowered:
                return InputClassification(
                    kind=InputKind.STATE_QUERY, matched_pattern=pattern,
                    confidence=0.9, args={"topic": topic},
                    reasons=[f"safety invariant query {topic!r}"])
        return None

    @staticmethod
    def _pilot4(lowered: str) -> Optional[InputClassification]:
        for pattern, topic in P4_QUERIES:
            if pattern in lowered:
                return InputClassification(
                    kind=InputKind.STATE_QUERY, matched_pattern=pattern,
                    confidence=0.9, args={"topic": topic},
                    reasons=[f"Pilot-4 planning query {topic!r}"])
        return None

    @staticmethod
    def _pilot3soak(lowered: str) -> Optional[InputClassification]:
        for pattern, topic in P3SOAK_QUERIES:
            if pattern in lowered:
                return InputClassification(
                    kind=InputKind.STATE_QUERY, matched_pattern=pattern,
                    confidence=0.9, args={"topic": topic},
                    reasons=[f"Pilot-3 soak query {topic!r}"])
        return None

    @staticmethod
    def _motor(lowered: str) -> Optional[InputClassification]:
        for pattern, topic in MOTOR_QUERIES:
            if pattern in lowered:
                return InputClassification(
                    kind=InputKind.STATE_QUERY, matched_pattern=pattern,
                    confidence=0.9, args={"topic": topic},
                    reasons=[f"motor membrane query {topic!r}"])
        return None

    @staticmethod
    def _pilot2(lowered: str) -> Optional[InputClassification]:
        for pattern, topic in PILOT2_QUERIES:
            if pattern in lowered:
                return InputClassification(
                    kind=InputKind.STATE_QUERY, matched_pattern=pattern,
                    confidence=0.9, args={"topic": topic},
                    reasons=[f"pilot-2 query {topic!r}"])
        return None

    @staticmethod
    def _sensory(lowered: str) -> Optional[InputClassification]:
        for pattern, topic in SENSORY_QUERIES:
            if pattern in lowered:
                return InputClassification(
                    kind=InputKind.STATE_QUERY, matched_pattern=pattern,
                    confidence=0.9, args={"topic": topic},
                    reasons=[f"sensory membrane query {topic!r}"])
        return None

    @staticmethod
    def _post_pilot(lowered: str) -> Optional[InputClassification]:
        for pattern, topic in POST_PILOT_QUERIES:
            if pattern in lowered:
                return InputClassification(
                    kind=InputKind.STATE_QUERY, matched_pattern=pattern,
                    confidence=0.9, args={"topic": topic},
                    reasons=[f"post-pilot query {topic!r}"])
        return None

    @staticmethod
    def _pilot(lowered: str) -> Optional[InputClassification]:
        for pattern, topic in PILOT_QUERIES:
            if pattern in lowered:
                return InputClassification(
                    kind=InputKind.STATE_QUERY, matched_pattern=pattern,
                    confidence=0.9, args={"topic": topic},
                    reasons=[f"pilot-1 query {topic!r}"])
        return None

    @staticmethod
    def _conscience(lowered: str) -> Optional[InputClassification]:
        for pattern, topic in CONSCIENCE_QUERIES:
            if pattern in lowered:
                return InputClassification(
                    kind=InputKind.STATE_QUERY, matched_pattern=pattern,
                    confidence=0.9, args={"topic": topic},
                    reasons=[f"conscience runtime query {topic!r}"])
        return None

    @staticmethod
    def _explanation(lowered: str) -> Optional[InputClassification]:
        if not lowered.startswith("why"):
            return None
        return InputClassification(
            kind=InputKind.EXPLANATION_QUERY, matched_pattern="why",
            confidence=0.85, args={"question": lowered},
            reasons=["'why' questions route to the explanation/query "
                     "interfaces"])

    @staticmethod
    def _state(lowered: str) -> Optional[InputClassification]:
        if not any(lowered.startswith(prefix) for prefix in
                   ("show", "status", "health", "what happened",
                    "what is", "list")) \
                and lowered not in ("status", "health"):
            return None
        for pattern, topic in STATE_TOPICS:
            if pattern in lowered:
                return InputClassification(
                    kind=InputKind.STATE_QUERY, matched_pattern=pattern,
                    confidence=0.9, args={"topic": topic},
                    reasons=[f"state query for {topic!r}"])
        return None

    @staticmethod
    def _bounded_command(lowered: str) -> Optional[InputClassification]:
        for pattern, command in BOUNDED_COMMAND_HINTS:
            if pattern in lowered:
                return InputClassification(
                    kind=InputKind.BOUNDED_COMMAND_REQUEST,
                    matched_pattern=pattern, confidence=0.8,
                    args={"command": command}, requires_confirmation=True,
                    reasons=[f"bounded command request {command!r}; "
                             "confirmation is required before "
                             "execution"])
        return None

    def snapshot(self) -> Dict[str, Any]:
        return {"classifications_made": self.classifications_made,
                "kinds": list(InputKind.ALL),
                "note": "deterministic pattern matching only; nothing is "
                        "executed during classification"}
