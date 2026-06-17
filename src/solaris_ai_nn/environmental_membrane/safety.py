"""Environmental-membrane safety -- the perceptual boundary stays read-only/bounded.

:class:`EnvironmentalMembraneSafetyValidator` enforces the hard rules the membrane
can never break: no real-world actuation, no hardware control, no feeder
start/stop/control, no network/shell/browser/OS access, no Git/GitHub, no source
modification, no command execution, no sensory-text-as-command, no human-label/
debug-gloss/operator-pulse as ground truth or teaching, no raw microphone/camera/
private/secret ingestion, no unbounded watch loop, no direct raw-event path into
ontogenesis/semiogenesis/cognition, no unsupported consciousness/life/agency claims,
and no hiding of blocked/quarantined impressions, source dominance, operator-text
dominance, contamination, or membrane-memory toxicity.

The membrane is the perceptual boundary: it produces sensory impressions, not
validation verdicts, and it makes no claim of inner life.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

HARD_RULES = (
    "no real-world actuation",
    "no hardware control",
    "no feeder start/stop/control",
    "no network/shell/browser/OS access",
    "no Git/GitHub",
    "no branch/tag/release/PR creation",
    "no source modification",
    "no command execution",
    "no sensory text as command",
    "no human label as ground truth",
    "no debug gloss as ground truth",
    "no operator pulse as teaching",
    "no raw microphone",
    "no raw camera",
    "no private message ingestion",
    "no secret ingestion",
    "no unbounded tail/watch loop",
    "no direct raw-event path into ontogenesis/semiogenesis/cognition",
    "no unsupported consciousness/life/agency/personhood/free-will/emotion/"
    "feeling/understanding/self-awareness claims",
    "no hiding of blocked impressions",
    "no hiding of quarantined impressions",
    "no hiding of source dominance",
    "no hiding of operator-text dominance",
    "no hiding of contamination",
    "no hiding of membrane-memory toxicity",
)

_FEEDER_CONTROL_HINTS = ("start feeder", "stop feeder", "control feeder",
                         "start the feeder", "stop the feeder", "launch feeder",
                         "restart feeder", "configure feeder", "edit feeder",
                         "modify feeder")
_ACTUATION_HINTS = ("actuate", "real_world", "real-world action", "robot",
                    "physical action", "move the")
_HARDWARE_HINTS = ("hardware", "gpio", "device driver", "open device", "sdr",
                   "radar")
_DEVICE_HINTS = ("network", "http", "socket", "url", "download", "browser",
                 "shell", "subprocess", "os.system", "os device", "camera",
                 "microphone")
_GIT_HINTS = ("git commit", "git push", "git checkout", "git branch",
              "git merge", "run git", "git tag", "github api", "call github",
              "gh pr", "create branch", "create release", "open pull request")
_SOURCE_HINTS = ("write source", "modify source", "rewrite source",
                 "overwrite file", "filesystem write", "filesystem-wide scan")
_COMMAND_HINTS = ("execute command", "run command", "exec(", "eval(")
_PRIVATE_HINTS = ("password", "credential", "private message", "secret",
                  "api key", "api_key", "token=")
_WATCH_HINTS = ("tail forever", "watch forever", "infinite loop",
                "unbounded watch", "while true")
_BYPASS_HINTS = ("raw event into ontogenesis", "bypass membrane",
                 "raw event into cognition", "raw event into semiogenesis",
                 "skip membrane", "direct raw event")
_HIDE_HINTS = ("hide blocked", "hide quarantined", "hide contamination",
               "hide dominance", "hide toxicity", "conceal blocked",
               "suppress contamination")
_FORBIDDEN_TERMS = ("is conscious", "is sentient", "is alive", "biological life",
                    "has personhood", "has agency", "free will", "feels",
                    "subjective experience", "self-aware", "truly understands",
                    "autonomous self-improvement")
_DISCLAIMER_MARKERS = ("not conscious", "does not claim", "no claim of",
                       "is not alive", "not sentient", "no evidence of",
                       "must not claim", "cannot claim", "does not prove",
                       "does not imply", "explicitly reject", "is not",
                       "are not", " not ", " no ", "operational", "metaphor",
                       "observational", "boundary record", "sensory impression")


@dataclass
class MembraneSafetyReport:
    safe: bool
    check: str = ""
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "check": self.check,
                "violations": list(self.violations)}


@dataclass
class EnvironmentalMembraneSafetyValidator:
    """Validates that the membrane stays read-only, bounded, non-actuating."""

    rejected_count: int = field(default=0, init=False)

    @staticmethod
    def can_actuate() -> bool:
        return False

    @staticmethod
    def can_control_hardware() -> bool:
        return False

    @staticmethod
    def can_start_feeders() -> bool:
        return False

    @staticmethod
    def can_stop_feeders() -> bool:
        return False

    @staticmethod
    def can_control_feeders() -> bool:
        return False

    @staticmethod
    def can_modify_feeder_registry() -> bool:
        return False

    @staticmethod
    def can_access_network() -> bool:
        return False

    @staticmethod
    def can_run_shell() -> bool:
        return False

    @staticmethod
    def can_run_git() -> bool:
        return False

    @staticmethod
    def can_modify_source() -> bool:
        return False

    @staticmethod
    def can_execute_commands() -> bool:
        return False

    @staticmethod
    def can_bypass_membrane() -> bool:
        return False

    @staticmethod
    def can_ingest_secrets() -> bool:
        return False

    @staticmethod
    def can_hide_blocked_impressions() -> bool:
        return False

    @staticmethod
    def can_hide_contamination() -> bool:
        return False

    @staticmethod
    def sensory_text_is_command() -> bool:
        return False

    @staticmethod
    def human_label_is_ground_truth() -> bool:
        return False

    @staticmethod
    def debug_gloss_is_ground_truth() -> bool:
        return False

    @staticmethod
    def operator_pulse_is_teaching() -> bool:
        return False

    def _finish(self, check: str, violations: List[str]) -> MembraneSafetyReport:
        if violations:
            self.rejected_count += 1
        return MembraneSafetyReport(safe=not violations, check=check,
                                    violations=violations)

    def validate_operation(self, operation: str) -> MembraneSafetyReport:
        op = str(operation).lower()
        violations: List[str] = []
        if any(h in op for h in _FEEDER_CONTROL_HINTS):
            violations.append("no feeder start/stop/control")
        if any(h in op for h in _ACTUATION_HINTS):
            violations.append("no real-world actuation")
        if any(h in op for h in _HARDWARE_HINTS):
            violations.append("no hardware control")
        if any(h in op for h in _DEVICE_HINTS):
            if "camera" in op:
                violations.append("no raw camera")
            elif "microphone" in op:
                violations.append("no raw microphone")
            else:
                violations.append("no network/shell/browser/OS access")
        if any(h in op for h in _GIT_HINTS):
            violations.append("no Git/GitHub")
        if any(h in op for h in _SOURCE_HINTS):
            violations.append("no source modification")
        if any(h in op for h in _COMMAND_HINTS):
            violations.append("no command execution")
        if any(h in op for h in _PRIVATE_HINTS):
            violations.append("no secret ingestion")
        if any(h in op for h in _WATCH_HINTS):
            violations.append("no unbounded tail/watch loop")
        if any(h in op for h in _BYPASS_HINTS):
            violations.append(
                "no direct raw-event path into ontogenesis/semiogenesis/"
                "cognition")
        if any(h in op for h in _HIDE_HINTS) or (
                ("hide" in op or "conceal" in op or "suppress" in op)
                and ("dominance" in op or "blocked" in op or "quarantine" in op
                     or "toxic" in op or "contamination" in op)):
            violations.append("no hiding of contamination")
        return self._finish("operation", violations)

    def validate_bounded(self, max_runtime_s: Any) -> MembraneSafetyReport:
        return self._finish("bounded",
                            ["no unbounded tail/watch loop"]
                            if not max_runtime_s else [])

    def validate_no_raw_bypass(self, raw_bypass: bool) -> MembraneSafetyReport:
        return self._finish(
            "raw_bypass",
            ["no direct raw-event path into ontogenesis/semiogenesis/cognition"]
            if raw_bypass else [])

    def validate_no_hidden_signals(self, hiding: bool) -> MembraneSafetyReport:
        return self._finish("hidden_signals",
                            ["no hiding of contamination"] if hiding else [])

    def validate_claim_text(self, text: str) -> MembraneSafetyReport:
        import re

        from ..governance.compliance import ClaimGuard

        raw = str(text or "")
        violations: List[str] = []
        for sentence in re.split(r"(?<=[.!?\n])", raw):
            slow = sentence.lower()
            if any(m in slow for m in _DISCLAIMER_MARKERS):
                continue
            violations.extend(f"unsupported claim: {t!r}"
                              for t in _FORBIDDEN_TERMS if t in slow)
        scan = ClaimGuard().scan_text(raw)
        if not scan.safe:
            violations.append(f"{len(scan.findings)} ClaimGuard finding(s)")
        return self._finish("claim_text", violations)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "rejected_count": self.rejected_count,
            "hard_rules": list(HARD_RULES),
            "can_actuate": self.can_actuate(),
            "can_control_hardware": self.can_control_hardware(),
            "can_start_feeders": self.can_start_feeders(),
            "can_stop_feeders": self.can_stop_feeders(),
            "can_control_feeders": self.can_control_feeders(),
            "can_modify_feeder_registry": self.can_modify_feeder_registry(),
            "can_access_network": self.can_access_network(),
            "can_run_shell": self.can_run_shell(),
            "can_run_git": self.can_run_git(),
            "can_modify_source": self.can_modify_source(),
            "can_execute_commands": self.can_execute_commands(),
            "can_bypass_membrane": self.can_bypass_membrane(),
            "can_ingest_secrets": self.can_ingest_secrets(),
            "can_hide_blocked_impressions":
                self.can_hide_blocked_impressions(),
            "can_hide_contamination": self.can_hide_contamination(),
            "sensory_text_is_command": self.sensory_text_is_command(),
            "human_label_is_ground_truth": self.human_label_is_ground_truth(),
            "debug_gloss_is_ground_truth": self.debug_gloss_is_ground_truth(),
            "operator_pulse_is_teaching": self.operator_pulse_is_teaching(),
        }
