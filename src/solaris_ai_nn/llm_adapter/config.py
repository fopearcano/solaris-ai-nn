"""LLM adapter configuration -- off by default, localhost by default.

The adapter is disabled unless explicitly enabled; remote networks are
prohibited unless governance approves them on top of an explicit config
flag; and every safety lever (grounding validation, ClaimGuard,
deterministic fallback) defaults to on and is expected to stay on.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

PROVIDERS = ("mock", "ollama_compatible", "lmstudio_compatible",
             "generic_local_http")

LOCALHOST_NAMES = ("localhost", "127.0.0.1", "::1", "[::1]")


def is_localhost_url(url: Optional[str]) -> bool:
    if not url:
        return False
    try:
        hostname = urlparse(url).hostname or ""
    except ValueError:
        return False
    return hostname in LOCALHOST_NAMES


@dataclass
class LLMAdapterConfig:
    """All the levers, defaulted to the safe position."""

    enabled: bool = False
    provider: str = "mock"
    endpoint_url: Optional[str] = None
    model_name: Optional[str] = None
    timeout_s: float = 10.0
    max_tokens: int = 512
    temperature: float = 0.1
    allow_network_localhost_only: bool = True
    allow_remote_network: bool = False
    fallback_to_deterministic: bool = True
    require_grounding_validation: bool = True
    require_claim_guard: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.provider not in PROVIDERS:
            raise ValueError(f"unknown LLM provider {self.provider!r}")

    # -- validation ---------------------------------------------------------------

    def validate(self) -> List[str]:
        """Issues that make this config unusable (empty list == usable)."""
        issues: List[str] = []
        if not self.enabled:
            return issues  # disabled is always a valid (and safe) state
        if self.provider != "mock":
            if not self.endpoint_url:
                issues.append("a non-mock provider needs an endpoint_url")
            elif not is_localhost_url(self.endpoint_url):
                if not self.allow_remote_network:
                    issues.append(
                        f"endpoint {self.endpoint_url!r} is not localhost "
                        "and remote network access is disabled (default)")
                elif self.allow_network_localhost_only:
                    issues.append(
                        "allow_remote_network requires "
                        "allow_network_localhost_only=False AND explicit "
                        "governance approval")
        if self.timeout_s <= 0:
            issues.append("timeout_s must be positive")
        if not self.fallback_to_deterministic:
            issues.append("fallback_to_deterministic must stay enabled; "
                          "the deterministic response is the source of "
                          "truth")
        if not self.require_claim_guard:
            issues.append("require_claim_guard must stay enabled")
        if not self.require_grounding_validation:
            issues.append("require_grounding_validation must stay "
                          "enabled")
        return issues

    def endpoint_is_localhost(self) -> bool:
        return is_localhost_url(self.endpoint_url)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)
