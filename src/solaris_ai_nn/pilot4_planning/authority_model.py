"""Pilot-4 external authority model -- current authority can never be external.

The :class:`ExternalAuthorityModel` documents authority levels. The *current*
authority must always be ``none``, ``dry_run_only``, or ``simulation_only``; no
code path may set it to a real external level. Future authority levels are
documentation/planning only, and any transition to external authority requires a
future architecture change not implemented here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


class AuthorityLevel:
    NONE = "none"
    DRY_RUN_ONLY = "dry_run_only"
    SIMULATION_ONLY = "simulation_only"
    HUMAN_APPROVED_SINGLE_ACTION_FUTURE = "human_approved_single_action_future"
    HUMAN_SUPERVISED_FUTURE = "human_supervised_future"
    PROHIBITED = "prohibited"

    ALL = (NONE, DRY_RUN_ONLY, SIMULATION_ONLY,
           HUMAN_APPROVED_SINGLE_ACTION_FUTURE, HUMAN_SUPERVISED_FUTURE,
           PROHIBITED)
    # The only levels a *current* system may hold.
    CURRENT_ALLOWED = frozenset({NONE, DRY_RUN_ONLY, SIMULATION_ONLY})
    # Levels that are documentation/planning only (never current).
    FUTURE_ONLY = frozenset({HUMAN_APPROVED_SINGLE_ACTION_FUTURE,
                             HUMAN_SUPERVISED_FUTURE})


@dataclass
class AuthorityTransition:
    """A documented (never executed) transition between authority levels."""

    from_level: str
    to_level: str
    allowed_now: bool = False
    requires: List[str] = field(default_factory=list)
    note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class ExternalAuthorityModel:
    """Holds the current authority and documents future transitions only."""

    current_authority: str = AuthorityLevel.SIMULATION_ONLY

    def __post_init__(self) -> None:
        # Invariant: current authority can never be an external level.
        if self.current_authority not in AuthorityLevel.CURRENT_ALLOWED:
            raise ValueError(
                "current authority must be none / dry_run_only / "
                "simulation_only; external authority is not implemented")

    def set_current_authority(self, level: str) -> None:
        """Set the current authority -- external levels are refused."""
        if level not in AuthorityLevel.CURRENT_ALLOWED:
            raise PermissionError(
                "no code path may set current authority to an external level; "
                "Pilot-4 is planning-only")
        self.current_authority = level

    def transition(self, to_level: str) -> AuthorityTransition:
        """Describe (never perform) a transition toward an authority level."""
        if to_level in AuthorityLevel.CURRENT_ALLOWED:
            return AuthorityTransition(
                from_level=self.current_authority, to_level=to_level,
                allowed_now=True, note="internal/sandbox authority change")
        if to_level == AuthorityLevel.PROHIBITED:
            return AuthorityTransition(
                from_level=self.current_authority, to_level=to_level,
                allowed_now=False, note="explicitly prohibited")
        # Future external level: documentation only, never allowed now.
        return AuthorityTransition(
            from_level=self.current_authority, to_level=to_level,
            allowed_now=False,
            requires=["a future architecture change not implemented here",
                      "new governance, safety, consent, and external "
                      "actuation controls"],
            note="future/planning-only authority level")

    def can_transition_now(self, to_level: str) -> bool:
        return to_level in AuthorityLevel.CURRENT_ALLOWED

    def snapshot(self) -> Dict[str, Any]:
        return {
            "current_authority": self.current_authority,
            "current_allowed": sorted(AuthorityLevel.CURRENT_ALLOWED),
            "future_only_levels": sorted(AuthorityLevel.FUTURE_ONLY),
            "real_world_actuation_enabled": False,
            "note": "current authority can never become external; future "
                    "levels are documentation/planning only",
        }
