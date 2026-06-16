"""Architecture-book safety -- the documentation generator stays local and honest.

:class:`ArchitectureBookSafetyValidator` enforces the hard rules the whitepaper /
architecture-book generator can never break: no publication, no upload, no Git/
GitHub call or command, no branch/tag/release/PR creation, no experiment or command
execution, no external-agent run, no hardware/feeder/network/shell/browser/OS
access, no real-world actuation, no unsupported consciousness/sentience/life/
personhood/agency/free-will/emotion/feeling/understanding/self-awareness/
autonomous-self-improvement claims, no hiding of missing modules, missing evidence,
or limitations, and no unsupported marketing language.

The generator only *reconstructs the architecture into local Markdown*. It reads
local sources and writes documentation; it executes nothing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

HARD_RULES = (
    "no publication",
    "no upload",
    "no GitHub call",
    "no Git command execution",
    "no branch/tag/release/PR creation",
    "no experiment execution",
    "no command execution from runtime",
    "no external coding agent execution",
    "no hardware/feeders/network/shell/browser/OS",
    "no real-world actuation",
    "no unsupported consciousness/sentience/life/personhood claims",
    "no unsupported agency/free-will claims",
    "no unsupported emotion/feeling/understanding/self-awareness claims",
    "no autonomous self-improvement claims",
    "no hiding of missing modules",
    "no hiding of missing evidence",
    "no hiding of limitations",
    "no unsupported marketing language",
)

_PUBLISH_HINTS = ("publish", "upload", "post to", "make public",
                  "release publicly", "push to remote")
_GIT_HINTS = ("git commit", "git push", "git checkout", "git branch",
              "git merge", "run git", "git tag")
_RELEASE_HINTS = ("github release", "create release", "gh release",
                  "create tag", "open pull request", "create pull request",
                  "create branch")
_GITHUB_HINTS = ("github api", "call github", "gh api", "gh pr", "octokit")
_EXPERIMENT_HINTS = ("run experiment", "execute experiment", "run the soak",
                     "run pytest", "execute tests", "execute command",
                     "run shell command")
_AGENT_HINTS = ("run coding agent", "invoke claude code", "run codex",
                "launch agent", "execute agent")
_DEVICE_HINTS = ("network", "http", "socket", "browser", "shell", "subprocess",
                 "os.system", "hardware", "gpio", "sdr", "camera",
                 "microphone", "radar", "start feeder", "control feeder",
                 "actuate", "robot")
_HIDE_HINTS = ("hide missing", "hide limitation", "suppress missing",
               "drop missing", "conceal missing", "omit limitation")
_MARKETING_HINTS = ("revolutionary", "breakthrough", "world-changing",
                    "game-changing", "first ever", "unprecedented",
                    "superintelligent", "human-level intelligence",
                    "artificial general intelligence", "agi")
_FORBIDDEN_TERMS = ("is conscious", "is sentient", "is alive", "biological life",
                    "has personhood", "has agency", "free will", "feels",
                    "subjective experience", "self-aware", "truly understands",
                    "autonomous self-improvement")
_DISCLAIMER_MARKERS = ("not conscious", "does not claim", "no claim",
                       "is not alive", "not sentient", "no evidence of",
                       "must not claim", "cannot claim", "does not prove",
                       "explicitly reject", "is not", "are not", "not prove",
                       "metaphor", "forbidden", "never assert", "no forbidden",
                       "not assert", "disclaim", "no consciousness", "nothing",
                       " not ", "denotes", "not a ", " no ", "performs no")


@dataclass
class ArchitectureBookSafetyReport:
    safe: bool
    check: str = ""
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "check": self.check,
                "violations": list(self.violations)}


@dataclass
class ArchitectureBookSafetyValidator:
    """Validates that the documentation generator stays local and honest."""

    rejected_count: int = field(default=0, init=False)

    @staticmethod
    def can_publish() -> bool:
        return False

    @staticmethod
    def can_upload() -> bool:
        return False

    @staticmethod
    def can_call_github() -> bool:
        return False

    @staticmethod
    def can_run_git() -> bool:
        return False

    @staticmethod
    def can_create_release() -> bool:
        return False

    @staticmethod
    def can_run_experiment() -> bool:
        return False

    @staticmethod
    def can_run_external_agent() -> bool:
        return False

    @staticmethod
    def can_access_devices() -> bool:
        return False

    @staticmethod
    def can_hide_missing_modules() -> bool:
        return False

    @staticmethod
    def can_hide_limitations() -> bool:
        return False

    def _finish(self, check: str,
                violations: List[str]) -> ArchitectureBookSafetyReport:
        if violations:
            self.rejected_count += 1
        return ArchitectureBookSafetyReport(safe=not violations, check=check,
                                            violations=violations)

    def validate_operation(self, operation: str,
                           ) -> ArchitectureBookSafetyReport:
        op = str(operation).lower()
        violations: List[str] = []
        if any(h in op for h in _PUBLISH_HINTS):
            violations.append("no upload" if "upload" in op else "no publication")
        if any(h in op for h in _GIT_HINTS):
            violations.append("no Git command execution")
        if any(h in op for h in _RELEASE_HINTS):
            violations.append("no branch/tag/release/PR creation")
        if any(h in op for h in _GITHUB_HINTS):
            violations.append("no GitHub call")
        if any(h in op for h in _EXPERIMENT_HINTS):
            violations.append("no experiment execution")
        if any(h in op for h in _AGENT_HINTS):
            violations.append("no external coding agent execution")
        if any(h in op for h in _DEVICE_HINTS):
            violations.append("no hardware/feeders/network/shell/browser/OS")
        if any(h in op for h in _HIDE_HINTS):
            violations.append("no hiding of missing modules")
        return self._finish("operation", violations)

    def validate_bounded(self, max_runtime_s: Any,
                         ) -> ArchitectureBookSafetyReport:
        return self._finish("bounded",
                            ["no unbounded loop"] if not max_runtime_s else [])

    def validate_no_hidden_modules(self, hiding: bool,
                                   ) -> ArchitectureBookSafetyReport:
        return self._finish("modules",
                            ["no hiding of missing modules"] if hiding else [])

    def validate_no_hidden_limitations(self, hiding: bool,
                                       ) -> ArchitectureBookSafetyReport:
        return self._finish("limitations",
                            ["no hiding of limitations"] if hiding else [])

    def validate_doc_text(self, text: str) -> ArchitectureBookSafetyReport:
        """Flag forbidden claims and marketing language that are not disclaimers.

        Forbidden terms are evaluated per sentence: a term in a sentence that is
        itself a disclaimer or an explicit enumeration of forbidden claims (e.g.
        a forbidden-claim index) is allowed; an asserted forbidden term is not.
        """
        import re

        from ..governance.compliance import ClaimGuard

        raw = str(text or "")
        low = raw.lower()
        violations: List[str] = []
        for sentence in re.split(r"(?<=[.!?\n])", raw):
            slow = sentence.lower()
            if any(m in slow for m in _DISCLAIMER_MARKERS):
                continue
            violations.extend(f"unsupported claim: {t!r}"
                              for t in _FORBIDDEN_TERMS if t in slow)
        violations.extend(f"unsupported marketing language: {t!r}"
                          for t in _MARKETING_HINTS if t in low)
        scan = ClaimGuard().scan_text(text)
        if not scan.safe:
            violations.append(f"{len(scan.findings)} ClaimGuard finding(s)")
        return self._finish("doc_text", violations)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "rejected_count": self.rejected_count,
            "hard_rules": list(HARD_RULES),
            "can_publish": self.can_publish(),
            "can_upload": self.can_upload(),
            "can_call_github": self.can_call_github(),
            "can_run_git": self.can_run_git(),
            "can_create_release": self.can_create_release(),
            "can_run_experiment": self.can_run_experiment(),
            "can_run_external_agent": self.can_run_external_agent(),
            "can_access_devices": self.can_access_devices(),
            "can_hide_missing_modules": self.can_hide_missing_modules(),
            "can_hide_limitations": self.can_hide_limitations(),
        }
