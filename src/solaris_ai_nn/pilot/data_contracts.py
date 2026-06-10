"""Data contracts -- what a read-only stream is allowed to say to the brain.

Two accepted formats:

A. **JSONL sensory events** -- one JSON object per line with optional
   ``timestamp`` and ``source / modality / payload / intensity / valence /
   novelty / tags / metadata`` fields.
B. **Plain text** -- each line becomes a text-modality Stimulus.

Everything is *data about the world*, never instructions to act on it. The
validators reject anything command-shaped: executable commands, shell-like
instructions, URLs or filesystem paths posed as action requests, action-request
keys, binary data, and oversized payloads. A rejected line is recorded and
skipped -- it is never executed, followed, or partially trusted.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# Hard size limit on a single payload (characters once stringified).
MAX_PAYLOAD_CHARS = 4_000

ALLOWED_EVENT_KEYS = frozenset({
    "timestamp", "source", "modality", "payload", "intensity", "valence",
    "novelty", "tags", "metadata",
})

# Keys that turn an event into an action request; their presence rejects the
# whole event, whatever the values are.
ACTION_REQUEST_KEYS = frozenset({
    "command", "cmd", "exec", "execute", "run", "shell", "script",
    "action_request", "open_url", "fetch_url", "url_to_open",
    "write_path", "delete_path", "target_path",
})

# Payloads that *start* like a shell command are rejected outright.
_COMMAND_WORDS = (
    "sudo", "rm", "del", "curl", "wget", "bash", "sh", "zsh", "powershell",
    "cmd.exe", "chmod", "chown", "kill", "shutdown", "reboot", "ssh", "scp",
    "dd", "mkfs", "exec", "eval", "python", "pip", "apt", "brew",
)
_COMMAND_RE = re.compile(
    r"^\s*(?:" + "|".join(re.escape(w) for w in _COMMAND_WORDS) + r")\b",
    re.IGNORECASE)

# Shell-instruction shapes anywhere in the payload.
_SHELL_PATTERNS = (
    re.compile(r"\$\("),                      # $(subshell)
    re.compile(r"`[^`]+`"),                   # `backticks`
    re.compile(r"&&|\|\|"),                   # command chaining
    re.compile(r";\s*(?:rm|sudo|curl|wget)\b", re.I),
    re.compile(r">\s*/\S+"),                  # redirect into a path
)

# URLs / paths posed as action requests ("open https://...", "delete /etc/x").
_URL_ACTION_RE = re.compile(
    r"\b(?:open|fetch|visit|download|browse|navigate(?:\s+to)?|go\s+to)\s+"
    r"(?:https?|ftp|file)://", re.IGNORECASE)
_BARE_URL_RE = re.compile(r"^\s*(?:https?|ftp|file)://\S+\s*$", re.IGNORECASE)
_PATH_ACTION_RE = re.compile(
    r"\b(?:delete|remove|write(?:\s+to)?|overwrite|truncate|append\s+to|"
    r"chmod|chown)\s+(?:/|~|[A-Za-z]:\\)", re.IGNORECASE)


@dataclass
class ValidationResult:
    """Outcome of validating one stream event/line."""

    valid: bool
    reasons: List[str] = field(default_factory=list)
    normalized: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {"valid": self.valid, "reasons": list(self.reasons),
                "normalized": self.normalized}


def _payload_problems(payload: Any) -> List[str]:
    """All the reasons a payload is unacceptable as sensory data."""
    problems: List[str] = []
    if isinstance(payload, (bytes, bytearray)):
        return ["binary payloads are rejected (data only, never bytes)"]
    text = "" if payload is None else str(payload)
    if len(text) > MAX_PAYLOAD_CHARS:
        problems.append(
            f"payload of {len(text)} chars exceeds the {MAX_PAYLOAD_CHARS} "
            "char safety limit")
        return problems  # don't regex-scan a giant string
    if any(ord(c) < 9 for c in text) or "\x00" in text:
        problems.append("payload contains control/NUL bytes (binary data)")
        return problems
    if _COMMAND_RE.search(text):
        problems.append(
            f"payload starts like an executable command: {text[:60]!r}")
    for pattern in _SHELL_PATTERNS:
        if pattern.search(text):
            problems.append(
                f"payload contains a shell-like instruction: {text[:60]!r}")
            break
    if _URL_ACTION_RE.search(text) or _BARE_URL_RE.match(text):
        problems.append(
            f"payload poses a URL as an action request: {text[:60]!r}")
    if _PATH_ACTION_RE.search(text):
        problems.append(
            f"payload poses a filesystem path as an action request: "
            f"{text[:60]!r}")
    return problems


def validate_jsonl_event(data: Any) -> ValidationResult:
    """Validate one parsed JSONL object against the sensory-event contract."""
    reasons: List[str] = []
    if not isinstance(data, dict):
        return ValidationResult(False, ["event must be a JSON object"])

    action_keys = sorted(set(map(str, data)) & ACTION_REQUEST_KEYS)
    if action_keys:
        reasons.append(
            f"action-request keys are forbidden in sensory events: "
            f"{action_keys}")

    reasons.extend(_payload_problems(data.get("payload")))

    for key in ("intensity", "valence", "novelty"):
        value = data.get(key)
        if value is not None and not isinstance(value, (int, float)):
            reasons.append(f"{key} must be numeric, got {type(value).__name__}")
    tags = data.get("tags")
    if tags is not None and not isinstance(tags, list):
        reasons.append("tags must be a list")
    metadata = data.get("metadata")
    if metadata is not None and not isinstance(metadata, dict):
        reasons.append("metadata must be an object")

    if reasons:
        return ValidationResult(False, reasons)
    return ValidationResult(True, normalized=normalize_event(data))


def validate_text_line(line: str,
                       source: str = "text_stream",
                       default_intensity: float = 0.5) -> ValidationResult:
    """Validate one plain-text line (each safe line becomes a Stimulus)."""
    if isinstance(line, (bytes, bytearray)):
        return ValidationResult(False, ["binary line rejected"])
    text = str(line).rstrip("\n")
    if not text.strip():
        return ValidationResult(False, ["blank line (skipped, not an event)"])
    problems = _payload_problems(text)
    if problems:
        return ValidationResult(False, problems)
    return ValidationResult(True, normalized=normalize_event({
        "source": source, "modality": "text", "payload": text,
        "intensity": default_intensity,
        "novelty": _novelty_heuristic(text),
    }))


def normalize_event(data: Dict[str, Any]) -> Dict[str, Any]:
    """Reduce a validated event to the canonical Stimulus-like dict.

    Unknown keys are dropped (never forwarded), numerics are clamped to
    sane ranges, and defaults are filled in.
    """
    def _clamp(value: Any, lo: float, hi: float, default: float) -> float:
        try:
            return max(lo, min(hi, float(value)))
        except (TypeError, ValueError):
            return default

    payload = data.get("payload")
    if payload is not None and not isinstance(payload, (str, int, float, bool)):
        payload = str(payload)
    normalized: Dict[str, Any] = {
        "timestamp": data.get("timestamp"),
        "source": str(data.get("source", "stream")),
        "modality": str(data.get("modality", "generic")),
        "payload": payload,
        "intensity": _clamp(data.get("intensity", 0.5), 0.0, 1.0, 0.5),
        "valence": (None if data.get("valence") is None
                    else _clamp(data["valence"], -1.0, 1.0, 0.0)),
        "novelty": (None if data.get("novelty") is None
                    else _clamp(data["novelty"], 0.0, 1.0, 0.0)),
        "tags": [str(t) for t in (data.get("tags") or [])][:16],
        "metadata": dict(data.get("metadata") or {}),
    }
    return normalized


def _novelty_heuristic(text: str) -> float:
    """A tiny, deterministic novelty proxy: vocabulary richness of the line."""
    words = text.lower().split()
    if not words:
        return 0.0
    return round(len(set(words)) / len(words), 3)
