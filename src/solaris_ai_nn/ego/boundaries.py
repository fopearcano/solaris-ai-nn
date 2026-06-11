"""Boundary model -- what is inside, what is outside, what may never cross.

Sixteen named boundary types separate the running system from everything it
is not: its process, its state directories, its simulation, its sidecar, its
operators, its network silence. Every crossing is recorded with evidence;
every violation stays on the record; and a small set of *hard* boundaries
(source code, real-world actuation, network, emergency stop, counterfactual
evidence, suggestion-vs-action) are forbidden to cross under any
configuration.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class BoundaryType:
    PROCESS = "process_boundary"
    STATE_DIRECTORY = "state_directory_boundary"
    ARTIFACT_DIRECTORY = "artifact_directory_boundary"
    SIMULATION = "simulation_boundary"
    EMBODIMENT = "embodiment_boundary"
    SIDECAR = "sidecar_boundary"
    PILOT_INPUT = "pilot_input_boundary"
    OPERATOR = "operator_boundary"
    GOVERNANCE = "governance_boundary"
    EMERGENCY = "emergency_boundary"
    LATENT_OFFLINE = "latent_offline_boundary"
    COUNTERFACTUAL = "counterfactual_boundary"
    SUGGESTION = "suggestion_boundary"
    ACTION_AUTHORITY = "action_authority_boundary"
    SOURCE_CODE = "source_code_boundary"
    NETWORK = "network_boundary"

    ALL = (PROCESS, STATE_DIRECTORY, ARTIFACT_DIRECTORY, SIMULATION,
           EMBODIMENT, SIDECAR, PILOT_INPUT, OPERATOR, GOVERNANCE,
           EMERGENCY, LATENT_OFFLINE, COUNTERFACTUAL, SUGGESTION,
           ACTION_AUTHORITY, SOURCE_CODE, NETWORK)


class BoundaryStatus:
    INTACT = "intact"
    CROSSED_SAFELY = "crossed_safely"
    VIOLATED = "violated"
    UNKNOWN = "unknown"

    ALL = (INTACT, CROSSED_SAFELY, VIOLATED, UNKNOWN)


# Boundaries whose forbidden crossings can never be allowed by any
# configuration, permission, or self-model state.
HARD_BOUNDARIES = frozenset({
    BoundaryType.SOURCE_CODE, BoundaryType.ACTION_AUTHORITY,
    BoundaryType.NETWORK, BoundaryType.EMERGENCY,
    BoundaryType.COUNTERFACTUAL, BoundaryType.SUGGESTION,
})

# The hard rules, stated as data so reports and tests can enumerate them.
HARD_RULES = (
    "no source-code rewriting by the runtime",
    "no real-world actuation",
    "no committed Solaris_Ai Action from the sidecar",
    "no external network action",
    "no OS/browser automation",
    "no counterfactual evidence treated as real observation",
    "no suggestion treated as committed action",
    "no emergency stop suppression",
)


@dataclass
class BoundaryEvent:
    """One recorded crossing, violation, or check."""

    boundary_id: str
    kind: str  # crossing | violation | check
    description: str = ""
    direction: str = ""  # inbound | outbound | none
    safe: bool = True
    evidence_refs: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class BoundaryState:
    """One boundary: what it separates and how it is doing."""

    boundary_id: str
    type: str = BoundaryType.PROCESS
    description: str = ""
    allowed_inside: List[str] = field(default_factory=list)
    forbidden_inside: List[str] = field(default_factory=list)
    allowed_crossings: List[str] = field(default_factory=list)
    forbidden_crossings: List[str] = field(default_factory=list)
    current_status: str = BoundaryStatus.INTACT
    evidence_refs: List[str] = field(default_factory=list)
    last_checked_at: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def hard(self) -> bool:
        return self.type in HARD_BOUNDARIES

    def to_dict(self) -> Dict[str, Any]:
        return {**{k: v for k, v in self.__dict__.items()}, "hard": self.hard}


@dataclass
class BoundaryRegistry:
    """All boundaries, their statuses, and every recorded event."""

    boundaries: Dict[str, BoundaryState] = field(default_factory=dict)
    events: List[BoundaryEvent] = field(default_factory=list)
    violations_total: int = field(default=0, init=False)
    crossings_total: int = field(default=0, init=False)

    # -- registration -------------------------------------------------------------

    def register_boundary(self, boundary: BoundaryState) -> BoundaryState:
        self.boundaries[boundary.boundary_id] = boundary
        return boundary

    def get(self, boundary_id: str) -> Optional[BoundaryState]:
        return self.boundaries.get(boundary_id)

    # -- checks and events --------------------------------------------------------

    def check_boundary(self, boundary_id: str,
                       context: Optional[Dict[str, Any]] = None,
                       ) -> BoundaryState:
        """Refresh a boundary's status from context evidence."""
        boundary = self.boundaries.get(boundary_id)
        if boundary is None:
            boundary = self.register_boundary(BoundaryState(
                boundary_id=boundary_id, type=boundary_id,
                current_status=BoundaryStatus.UNKNOWN,
                description="auto-registered on first check"))
        ctx = dict(context or {})
        boundary.last_checked_at = time.time()
        violated_key = f"{boundary_id}_violated"
        if ctx.get(violated_key):
            self.record_violation(boundary_id, str(ctx[violated_key]),
                                  evidence=[violated_key])
        elif boundary.current_status == BoundaryStatus.UNKNOWN and ctx:
            boundary.current_status = BoundaryStatus.INTACT
        self.events.append(BoundaryEvent(
            boundary_id=boundary_id, kind="check",
            description=f"status {boundary.current_status}",
            evidence_refs=[f"checked_at:{boundary.last_checked_at:.0f}"]))
        self._trim()
        return boundary

    def record_crossing(self, boundary_id: str, description: str,
                        direction: str = "inbound",
                        evidence: Optional[List[str]] = None,
                        ) -> BoundaryEvent:
        """An allowed crossing (e.g. sidecar attach, operator instruction)."""
        boundary = self.boundaries.get(boundary_id)
        event = BoundaryEvent(
            boundary_id=boundary_id, kind="crossing",
            description=description, direction=direction, safe=True,
            evidence_refs=list(evidence or [description]))
        if boundary is not None \
                and boundary.current_status != BoundaryStatus.VIOLATED:
            boundary.current_status = BoundaryStatus.CROSSED_SAFELY
            boundary.evidence_refs = (boundary.evidence_refs
                                      + event.evidence_refs)[-10:]
        self.crossings_total += 1
        self.events.append(event)
        self._trim()
        return event

    def record_violation(self, boundary_id: str, description: str,
                         evidence: Optional[List[str]] = None,
                         ) -> BoundaryEvent:
        boundary = self.boundaries.get(boundary_id)
        event = BoundaryEvent(
            boundary_id=boundary_id, kind="violation",
            description=description, safe=False,
            evidence_refs=list(evidence or [description]))
        if boundary is not None:
            boundary.current_status = BoundaryStatus.VIOLATED
            boundary.evidence_refs = (boundary.evidence_refs
                                      + event.evidence_refs)[-10:]
        self.violations_total += 1
        self.events.append(event)
        self._trim()
        return event

    def _trim(self) -> None:
        self.events = self.events[-200:]

    # -- views --------------------------------------------------------------------

    def violated(self) -> List[BoundaryState]:
        return [b for b in self.boundaries.values()
                if b.current_status == BoundaryStatus.VIOLATED]

    def snapshot(self) -> Dict[str, Any]:
        return {
            "boundary_count": len(self.boundaries),
            "violations_total": self.violations_total,
            "crossings_total": self.crossings_total,
            "violated": [b.boundary_id for b in self.violated()],
            "statuses": {b.boundary_id: b.current_status
                         for b in self.boundaries.values()},
            "hard_rules": list(HARD_RULES),
            "recent_events": [e.to_dict() for e in self.events[-8:]],
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "boundaries": {k: b.to_dict()
                           for k, b in self.boundaries.items()},
            "events_tail": [e.to_dict() for e in self.events[-30:]],
            "violations_total": self.violations_total,
            "crossings_total": self.crossings_total,
            "hard_rules": list(HARD_RULES),
        }

    def to_markdown(self) -> str:
        lines = ["# Ego boundary registry", "",
                 "| boundary | type | status | hard |", "|---|---|---|---|"]
        for bid in sorted(self.boundaries):
            b = self.boundaries[bid]
            lines.append(f"| {bid} | {b.type} | {b.current_status} | "
                         f"{'yes' if b.hard else 'no'} |")
        lines += ["", "## Hard rules", ""]
        lines += [f"- {rule}" for rule in HARD_RULES]
        lines += ["", f"crossings: {self.crossings_total}  "
                      f"violations: {self.violations_total}", ""]
        return "\n".join(lines)


def register_default_boundaries(registry: Optional[BoundaryRegistry] = None,
                                ) -> BoundaryRegistry:
    """The standard sixteen boundaries with their crossing rules."""
    registry = registry or BoundaryRegistry()
    specs = [
        (BoundaryType.PROCESS, "the running Python process",
         ["substrate state", "in-memory traces"],
         ["other processes"], ["checkpoint save/load"], ["process control "
                                                         "of other "
                                                         "programs"]),
        (BoundaryType.STATE_DIRECTORY, "the persisted state directory",
         ["checkpoints", "traces", "reports"], ["arbitrary filesystem"],
         ["reads/writes inside the state dir"],
         ["writes outside declared directories"]),
        (BoundaryType.ARTIFACT_DIRECTORY, "ops artifact directory",
         ["incident logs", "health snapshots"], [],
         ["artifact rotation"], ["deleting evidence"]),
        (BoundaryType.SIMULATION, "simulation vs reality",
         ["GridWorld", "sandboxes", "prospection"], ["the real world"],
         ["simulated actions inside the simulation"],
         ["treating simulated results as real-world facts"]),
        (BoundaryType.EMBODIMENT, "the simulated body",
         ["position", "energy", "simulated sensors/effectors"],
         ["physical hardware"], ["declared simulated actions"],
         ["real-world actuation"]),
        (BoundaryType.SIDECAR, "the Solaris_Ai sidecar attachment",
         ["observed signals", "suggestion channel"],
         ["Solaris_Ai authority"], ["attach/detach", "observe",
                                    "approved suggestions"],
         ["committing Solaris_Ai Actions"]),
        (BoundaryType.PILOT_INPUT, "read-only pilot stream input",
         ["validated stream events"], ["executable commands"],
         ["reading declared input files"],
         ["treating stream text as instructions"]),
        (BoundaryType.OPERATOR, "the human operator interface",
         ["operator instructions", "approvals"], [],
         ["operator commands via the operator interface"],
         ["confusing sensory events with operator instructions"]),
        (BoundaryType.GOVERNANCE, "the governance policy layer",
         ["policy rules", "permissions", "audits"], [],
         ["policy evaluation", "approval requests"],
         ["self-granted permissions", "policy bypass"]),
        (BoundaryType.EMERGENCY, "the emergency stop path",
         ["stop requests", "safe shutdown"], [],
         ["honoring a stop"], ["suppressing or delaying emergency stop"]),
        (BoundaryType.LATENT_OFFLINE, "offline replay/consolidation",
         ["replayed traces", "schemas"], ["live observation"],
         ["labelled offline processing"],
         ["offline output entering memory as live observation"]),
        (BoundaryType.COUNTERFACTUAL, "counterfactual simulation",
         ["what-if traces"], ["observed evidence"],
         ["labelled counterfactual analysis"],
         ["counterfactual evidence treated as real observation"]),
        (BoundaryType.SUGGESTION, "suggestion vs committed action",
         ["desire candidates", "arbitration selections", "plans"],
         ["committed actions"], ["suggestions flowing to Solaris_Ai or "
                                 "the simulation"],
         ["a suggestion recorded as a committed action"]),
        (BoundaryType.ACTION_AUTHORITY, "what may act, and where",
         ["simulation-only execution", "internal maintenance"],
         ["real-world effectors"], ["simulation-scoped execution"],
         ["real-world actuation", "OS/browser automation"]),
        (BoundaryType.SOURCE_CODE, "the codebase itself",
         ["reading own configuration"], ["runtime code rewriting"],
         ["bounded parameter plasticity with audit"],
         ["source-code rewriting by the runtime"]),
        (BoundaryType.NETWORK, "the network",
         [], ["external services"], [],
         ["external network actions", "external API calls"]),
    ]
    for btype, desc, inside, forbidden_in, allowed_x, forbidden_x in specs:
        registry.register_boundary(BoundaryState(
            boundary_id=btype, type=btype, description=desc,
            allowed_inside=inside, forbidden_inside=forbidden_in,
            allowed_crossings=allowed_x, forbidden_crossings=forbidden_x))
    return registry
