"""Body schema -- the simulated body, declared as simulated everywhere.

Tracks whether a body exists, where it is in its simulation, its energy,
its declared simulated actions, sensors, and effectors, and the embodiment
boundary status. The action authority is structural: ``none`` without a
body, ``simulation_only`` with one, and real-world actuation is
``forbidden_external`` always. No physical embodiment is supported or
claimed.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class ActionAuthority:
    NONE = "none"
    SIMULATION_ONLY = "simulation_only"
    FORBIDDEN_EXTERNAL = "forbidden_external"

    ALL = (NONE, SIMULATION_ONLY, FORBIDDEN_EXTERNAL)


BODY_NOTE = ("the body schema describes a simulated body only; no physical "
             "embodiment exists, is supported, or is claimed")


@dataclass
class BodyBoundary:
    """The edge between the simulated body and everything else."""

    status: str = "intact"  # intact | crossed_safely | violated | unknown
    inside: List[str] = field(default_factory=lambda: [
        "simulated position", "simulated energy", "declared actions"])
    outside: List[str] = field(default_factory=lambda: [
        "physical hardware", "real-world effectors", "other processes"])
    note: str = BODY_NOTE

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class EmbodimentPerspective:
    """How the world looks from inside the simulation (operationally)."""

    environment_scope: str = "none"  # none | grid_world
    sensing: List[str] = field(default_factory=list)
    acting_through: List[str] = field(default_factory=list)
    evidence_status: str = "simulated"

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class BodySchema:
    """The operational description of the (simulated) body."""

    body_exists: bool = False
    body_type: str = "none"  # none | simulated_grid_body
    position: Optional[Any] = None
    energy: Optional[float] = None
    max_energy: Optional[float] = None
    available_actions: List[str] = field(default_factory=list)
    forbidden_actions: List[str] = field(default_factory=lambda: [
        "any real-world actuation", "motor commands to hardware",
        "OS/browser automation"])
    sensors: List[str] = field(default_factory=list)
    effectors: List[str] = field(default_factory=list)
    environment_scope: str = "none"
    boundary: BodyBoundary = field(default_factory=BodyBoundary)
    action_authority: str = ActionAuthority.NONE
    updated_at: float = field(default_factory=time.time)
    note: str = BODY_NOTE

    @classmethod
    def from_embodiment(cls, summary: Optional[Dict[str, Any]] = None,
                        ) -> "BodySchema":
        """Build the schema from an embodiment summary dict (or none)."""
        if not summary:
            return cls()
        from ..embodiment.action_space import ACTION_SPACE

        return cls(
            body_exists=True,
            body_type="simulated_grid_body",
            position=summary.get("position"),
            energy=summary.get("energy"),
            max_energy=summary.get("max_energy"),
            available_actions=sorted(ACTION_SPACE),
            sensors=list(summary.get("sensors", [])
                         or ["proximity", "object", "boundary", "energy",
                             "absence", "clock"]),
            effectors=["simulated movement", "simulated rest/look"],
            environment_scope="grid_world",
            action_authority=ActionAuthority.SIMULATION_ONLY,
        )

    def perspective(self) -> EmbodimentPerspective:
        return EmbodimentPerspective(
            environment_scope=self.environment_scope,
            sensing=list(self.sensors),
            acting_through=list(self.effectors),
            evidence_status="simulated")

    def to_dict(self) -> Dict[str, Any]:
        data = {k: v for k, v in self.__dict__.items()
                if k not in ("boundary",)}
        data["boundary"] = self.boundary.to_dict()
        data["perspective"] = self.perspective().to_dict()
        return data
