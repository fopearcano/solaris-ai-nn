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

        result = (self._unsafe(lowered)
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
