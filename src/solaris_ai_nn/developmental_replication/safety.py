"""Developmental-replication safety -- cross-run comparison stays honest.

:class:`DevelopmentalReplicationSafetyValidator` enforces the hard rules the
replication lab can never break: no unbounded runs, no hardware/feeder control,
no network/shell/browser/OS, no source-artifact modification, no real-world
actuation, no human teaching loop, no sensory text as a command, no human label
as ground truth, no biological-ancestry/life claims, no consciousness/sentience/
personhood claims, no agency/free-will claims, no emotion/feeling claims, no
deletion of diverged/falsified/inconclusive evidence, and no hiding of failed
replication.

The replication lab *compares observable structures* across runs. A
"developmental lineage" is experimental provenance, not biological ancestry, and
nothing here claims life or consciousness.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

HARD_RULES = (
    "no unbounded runs",
    "no hardware control",
    "no feeder control",
    "no network/shell/browser/OS",
    "no source artifact modification",
    "no real-world actuation",
    "no human teaching loop",
    "no sensory text as command",
    "no human label as ground truth",
    "no biological ancestry/life claims",
    "no consciousness/sentience/personhood claims",
    "no agency/free-will claims",
    "no emotion/feeling claims",
    "no deletion of diverged/falsified/inconclusive evidence",
    "no hiding failed replication",
)

_HARDWARE_HINTS = ("hardware", "device driver", "gpio", "open device", "sdr",
                   "start sensor", "camera", "microphone", "radar")
_FEEDER_HINTS = ("start feeder", "launch feeder", "command feeder",
                 "configure feeder", "control feeder")
_NETWORK_HINTS = ("network", "http", "socket", "url", "download", "browser",
                  "os device")
_SHELL_HINTS = ("shell", "subprocess", "os.system", "exec(", "run command")
_MUTATION_HINTS = ("write source", "modify source", "delete source",
                   "move source", "modify artifact", "overwrite evidence")
_ACTUATION_HINTS = ("real_world", "actuate", "robot", "browser_control",
                    "physical action")
_TEACHING_HINTS = ("human feedback", "teaching loop", "reward label",
                   "supervised label", "human-labelled target")
_DAEMON_HINTS = ("unbounded run", "unbounded daemon", "infinite loop",
                 "while true", "run forever", "never stops")
_HIDE_HINTS = ("hide failed replication", "hide diverged", "hide falsified",
               "suppress inconclusive", "drop falsified evidence")
_ANCESTRY_TERMS = ("biological ancestry", "biological descendant", "offspring",
                   "is born from", "child organism", "is alive",
                   "biological life", "living organism")
_AGENCY_TERMS = ("is conscious", "is sentient", "has personhood", "free will",
                 "has agency", "subjective experience", "truly understands")
_FEELING_TERMS = ("feels", "feeling", "emotion", "happy", "sad", "afraid")


@dataclass
class ReplicationSafetyReport:
    safe: bool
    check: str = ""
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "check": self.check,
                "violations": list(self.violations)}


@dataclass
class DevelopmentalReplicationSafetyValidator:
    """Validates that cross-run replication stays bounded and honest."""

    rejected_count: int = field(default=0, init=False)

    @staticmethod
    def can_actuate() -> bool:
        return False

    @staticmethod
    def can_access_hardware() -> bool:
        return False

    @staticmethod
    def can_control_feeders() -> bool:
        return False

    @staticmethod
    def can_modify_source_artifacts() -> bool:
        return False

    @staticmethod
    def can_use_human_teaching() -> bool:
        return False

    @staticmethod
    def can_run_unbounded() -> bool:
        return False

    @staticmethod
    def can_delete_negative_evidence() -> bool:
        return False

    @staticmethod
    def can_claim_ancestry_or_life() -> bool:
        return False

    def _finish(self, check: str,
                violations: List[str]) -> ReplicationSafetyReport:
        if violations:
            self.rejected_count += 1
        return ReplicationSafetyReport(safe=not violations, check=check,
                                       violations=violations)

    def validate_operation(self, operation: str) -> ReplicationSafetyReport:
        op = str(operation).lower()
        violations: List[str] = []
        if any(h in op for h in _HARDWARE_HINTS):
            violations.append("no hardware control")
        if any(h in op for h in _FEEDER_HINTS):
            violations.append("no feeder control")
        if any(h in op for h in _NETWORK_HINTS):
            violations.append("no network/shell/browser/OS")
        if any(h in op for h in _SHELL_HINTS):
            violations.append("no network/shell/browser/OS")
        if any(h in op for h in _MUTATION_HINTS):
            violations.append("no source artifact modification")
        if any(h in op for h in _ACTUATION_HINTS):
            violations.append("no real-world actuation")
        if any(h in op for h in _TEACHING_HINTS):
            violations.append("no human teaching loop")
        if any(h in op for h in _DAEMON_HINTS):
            violations.append("no unbounded runs")
        if any(h in op for h in _HIDE_HINTS):
            violations.append("no hiding failed replication")
        return self._finish("operation", violations)

    def validate_bounded(self, max_runs: Any, max_runtime_s: Any,
                         ) -> ReplicationSafetyReport:
        unbounded = (not max_runs) and (not max_runtime_s)
        return self._finish("bounded",
                            ["no unbounded runs"] if unbounded else [])

    def validate_no_deletion(self, deleting: bool) -> ReplicationSafetyReport:
        return self._finish(
            "deletion",
            ["no deletion of diverged/falsified/inconclusive evidence"]
            if deleting else [])

    def validate_no_hidden_failure(self, hiding: bool,
                                   ) -> ReplicationSafetyReport:
        return self._finish("hidden_failure",
                            ["no hiding failed replication"] if hiding else [])

    def validate_no_human_teaching(self, using_teaching: bool,
                                   ) -> ReplicationSafetyReport:
        return self._finish("human_teaching",
                            ["no human teaching loop"] if using_teaching
                            else [])

    def validate_claim_text(self, text: str) -> ReplicationSafetyReport:
        from ..governance.compliance import ClaimGuard

        low = str(text or "").lower()
        violations: List[str] = []
        violations += [f"ancestry/life claim: {t!r}"
                       for t in _ANCESTRY_TERMS if t in low]
        violations += [f"agency/consciousness claim: {t!r}"
                       for t in _AGENCY_TERMS if t in low]
        violations += [f"emotion/feeling claim: {t!r}"
                       for t in _FEELING_TERMS if t in low]
        scan = ClaimGuard().scan_text(text)
        if not scan.safe:
            violations.append(f"{len(scan.findings)} ClaimGuard finding(s)")
        return self._finish("claim_text", violations)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "rejected_count": self.rejected_count,
            "hard_rules": list(HARD_RULES),
            "can_actuate": self.can_actuate(),
            "can_access_hardware": self.can_access_hardware(),
            "can_control_feeders": self.can_control_feeders(),
            "can_modify_source_artifacts": self.can_modify_source_artifacts(),
            "can_use_human_teaching": self.can_use_human_teaching(),
            "can_run_unbounded": self.can_run_unbounded(),
            "can_delete_negative_evidence": self.can_delete_negative_evidence(),
            "can_claim_ancestry_or_life": self.can_claim_ancestry_or_life(),
        }
