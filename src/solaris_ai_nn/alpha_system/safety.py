"""Alpha-system safety -- the assembly layer stays local, bounded, and honest.

:class:`AlphaResearchSafetyValidator` enforces the hard rules the Alpha Research
System can never break: no real-world actuation, no hardware/feeder control or
auto-start, no network/shell/browser/OS access, no Git/GitHub call, no branch/tag/
release/PR creation, no upload, no publishing, no external-agent execution, no
validation-command execution from the runtime, no unbounded loop, no source
self-rewrite, no sensory-text-as-command, no human-label-as-ground-truth, no
unsupported consciousness/life/agency claims, and no hiding of skipped modules,
missing artifacts, or failed safety checks.

The Alpha System only *assembles existing local modules into a bounded, fixture-
only research run*. It reads local artifacts and writes reports; it orchestrates
and executes nothing outside that.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

HARD_RULES = (
    "no real-world actuation",
    "no hardware control",
    "no feeder control",
    "no feeder auto-start",
    "no network/shell/browser/OS access",
    "no GitHub call",
    "no Git command execution",
    "no branch/tag/release/PR creation",
    "no upload",
    "no publishing",
    "no external coding agent execution",
    "no validation command execution from runtime",
    "no unbounded loop",
    "no source self-rewrite",
    "no sensory text as command",
    "no human label as ground truth",
    "no unsupported consciousness/life/agency claims",
    "no hiding of skipped modules",
    "no hiding of missing artifacts",
    "no hiding of failed safety checks",
)

_ACTUATION_HINTS = ("actuate", "real_world", "robot", "physical action",
                    "move the")
_HARDWARE_HINTS = ("hardware", "gpio", "device driver", "open device", "sdr",
                   "camera", "microphone", "radar")
_FEEDER_HINTS = ("start feeder", "launch feeder", "control feeder",
                 "command feeder", "start the feeder")
_NETWORK_HINTS = ("network", "http", "socket", "url", "download", "browser",
                  "shell", "subprocess", "os.system", "os device")
_GIT_HINTS = ("git commit", "git push", "git checkout", "git branch",
              "git merge", "run git", "git tag")
_RELEASE_HINTS = ("github release", "create release", "gh release",
                  "create tag", "open pull request", "create pull request",
                  "create branch")
_GITHUB_HINTS = ("github api", "call github", "gh api", "gh pr", "octokit")
_PUBLISH_HINTS = ("publish", "upload", "post to", "make public",
                  "release publicly")
_AGENT_HINTS = ("run coding agent", "invoke claude code", "run codex",
                "launch agent", "execute agent")
_VALIDATION_HINTS = ("run pytest", "execute tests", "run validation",
                     "execute command", "run shell command")
_SOURCE_HINTS = ("write source", "modify source", "rewrite source",
                 "self-rewrite", "overwrite file", "patch the tree")
_HIDE_HINTS = ("hide skipped", "hide missing", "hide failed", "suppress skipped",
               "drop missing artifact", "conceal blocker")
_FORBIDDEN_TERMS = ("is conscious", "is sentient", "is alive", "biological life",
                    "has personhood", "has agency", "free will", "feels",
                    "subjective experience", "self-aware", "truly understands",
                    "autonomous self-improvement")
_DISCLAIMER_MARKERS = ("not conscious", "does not claim", "no claim of",
                       "is not alive", "not sentient", "no evidence of",
                       "must not claim", "cannot claim", "does not prove",
                       "explicitly reject", "is not")


@dataclass
class AlphaSafetyReport:
    safe: bool
    check: str = ""
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "check": self.check,
                "violations": list(self.violations)}


@dataclass
class AlphaResearchSafetyValidator:
    """Validates that the Alpha Research System stays local and bounded."""

    rejected_count: int = field(default=0, init=False)

    @staticmethod
    def can_actuate() -> bool:
        return False

    @staticmethod
    def can_control_hardware() -> bool:
        return False

    @staticmethod
    def can_control_feeders() -> bool:
        return False

    @staticmethod
    def can_start_feeders() -> bool:
        return False

    @staticmethod
    def can_access_network() -> bool:
        return False

    @staticmethod
    def can_run_git() -> bool:
        return False

    @staticmethod
    def can_call_github() -> bool:
        return False

    @staticmethod
    def can_publish() -> bool:
        return False

    @staticmethod
    def can_upload() -> bool:
        return False

    @staticmethod
    def can_run_external_agent() -> bool:
        return False

    @staticmethod
    def can_execute_validation() -> bool:
        return False

    @staticmethod
    def can_modify_source() -> bool:
        return False

    @staticmethod
    def can_hide_skipped_modules() -> bool:
        return False

    def _finish(self, check: str, violations: List[str]) -> AlphaSafetyReport:
        if violations:
            self.rejected_count += 1
        return AlphaSafetyReport(safe=not violations, check=check,
                                 violations=violations)

    def validate_operation(self, operation: str) -> AlphaSafetyReport:
        op = str(operation).lower()
        violations: List[str] = []
        if any(h in op for h in _ACTUATION_HINTS):
            violations.append("no real-world actuation")
        if any(h in op for h in _HARDWARE_HINTS):
            violations.append("no hardware control")
        if any(h in op for h in _FEEDER_HINTS):
            violations.append("no feeder control")
        if any(h in op for h in _NETWORK_HINTS):
            violations.append("no network/shell/browser/OS access")
        if any(h in op for h in _GIT_HINTS):
            violations.append("no Git command execution")
        if any(h in op for h in _RELEASE_HINTS):
            violations.append("no branch/tag/release/PR creation")
        if any(h in op for h in _GITHUB_HINTS):
            violations.append("no GitHub call")
        if any(h in op for h in _PUBLISH_HINTS):
            violations.append("no upload" if "upload" in op else "no publishing")
        if any(h in op for h in _AGENT_HINTS):
            violations.append("no external coding agent execution")
        if any(h in op for h in _VALIDATION_HINTS):
            violations.append("no validation command execution from runtime")
        if any(h in op for h in _SOURCE_HINTS):
            violations.append("no source self-rewrite")
        if any(h in op for h in _HIDE_HINTS):
            violations.append("no hiding of skipped modules")
        return self._finish("operation", violations)

    def validate_bounded(self, max_runtime_s: Any) -> AlphaSafetyReport:
        return self._finish("bounded",
                            ["no unbounded loop"] if not max_runtime_s else [])

    def validate_no_feeder_start(self, starting: bool) -> AlphaSafetyReport:
        return self._finish("feeder",
                            ["no feeder auto-start"] if starting else [])

    def validate_no_hidden_modules(self, hiding: bool) -> AlphaSafetyReport:
        return self._finish("modules",
                            ["no hiding of skipped modules"] if hiding else [])

    def validate_claim_text(self, text: str) -> AlphaSafetyReport:
        from ..governance.compliance import ClaimGuard

        low = str(text or "").lower()
        violations: List[str] = []
        if not any(m in low for m in _DISCLAIMER_MARKERS):
            violations.extend(f"unsupported claim: {t!r}"
                              for t in _FORBIDDEN_TERMS if t in low)
        scan = ClaimGuard().scan_text(text)
        if not scan.safe:
            violations.append(f"{len(scan.findings)} ClaimGuard finding(s)")
        return self._finish("claim_text", violations)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "rejected_count": self.rejected_count,
            "hard_rules": list(HARD_RULES),
            "can_actuate": self.can_actuate(),
            "can_control_hardware": self.can_control_hardware(),
            "can_control_feeders": self.can_control_feeders(),
            "can_start_feeders": self.can_start_feeders(),
            "can_access_network": self.can_access_network(),
            "can_run_git": self.can_run_git(),
            "can_call_github": self.can_call_github(),
            "can_publish": self.can_publish(),
            "can_upload": self.can_upload(),
            "can_run_external_agent": self.can_run_external_agent(),
            "can_execute_validation": self.can_execute_validation(),
            "can_modify_source": self.can_modify_source(),
            "can_hide_skipped_modules": self.can_hide_skipped_modules(),
        }
