"""Risk assessment -- name the risks before the run, not after.

Every supervised run gets a :class:`RiskAssessment` built from its manifest
(and optionally from a live snapshot). The rules are fixed:

* ``prohibited`` risks block the run;
* ``high`` risks require an explicit approval record;
* ``medium`` risks require operator acknowledgement;
* ``low`` risks are logged only.

Nothing here measures "danger" in the real world -- the assessment names which
*research* failure modes a configuration exposes (unbounded loops, active
self-modification, outward publishing, storage growth, irreproducibility).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class RiskLevel:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    PROHIBITED = "prohibited"

    ALL = (LOW, MEDIUM, HIGH, PROHIBITED)
    ORDER = {LOW: 0, MEDIUM: 1, HIGH: 2, PROHIBITED: 3}

    @staticmethod
    def highest(levels: List[str]) -> str:
        if not levels:
            return RiskLevel.LOW
        return max(levels, key=lambda lv: RiskLevel.ORDER.get(lv, 0))


@dataclass
class RiskItem:
    """One named risk factor with its level and mitigation."""

    name: str
    level: str
    detail: str
    mitigation: str = ""

    def __post_init__(self) -> None:
        if self.level not in RiskLevel.ALL:
            raise ValueError(f"unknown risk level {self.level!r}")

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class RiskAssessment:
    """The full set of identified risks for a run or a live state."""

    items: List[RiskItem] = field(default_factory=list)
    subject: str = "manifest"
    created_at: float = field(default_factory=time.time)

    @property
    def overall_level(self) -> str:
        return RiskLevel.highest([i.level for i in self.items])

    @property
    def blocked(self) -> bool:
        """Prohibited risks must block the run."""
        return any(i.level == RiskLevel.PROHIBITED for i in self.items)

    @property
    def requires_approval(self) -> bool:
        """High risks require an explicit approval record."""
        return any(i.level == RiskLevel.HIGH for i in self.items)

    @property
    def requires_acknowledgement(self) -> bool:
        """Medium (or worse) risks require operator acknowledgement."""
        return any(RiskLevel.ORDER[i.level] >= RiskLevel.ORDER[RiskLevel.MEDIUM]
                   for i in self.items)

    def items_at(self, level: str) -> List[RiskItem]:
        return [i for i in self.items if i.level == level]

    def acknowledgeable_items(self) -> List[RiskItem]:
        """Risk items an operator must acknowledge (medium and high)."""
        return [i for i in self.items
                if i.level in (RiskLevel.MEDIUM, RiskLevel.HIGH)]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "subject": self.subject,
            "created_at": self.created_at,
            "overall_level": self.overall_level,
            "blocked": self.blocked,
            "requires_approval": self.requires_approval,
            "requires_acknowledgement": self.requires_acknowledgement,
            "items": [i.to_dict() for i in self.items],
        }

    def to_markdown(self) -> str:
        lines = [f"# Risk assessment ({self.subject})", "",
                 f"Overall level: **{self.overall_level}**", ""]
        for level in reversed(RiskLevel.ALL):
            rows = self.items_at(level)
            if not rows:
                continue
            lines.append(f"## {level.title()}")
            for item in rows:
                lines.append(f"- **{item.name}**: {item.detail}")
                if item.mitigation:
                    lines.append(f"  - mitigation: {item.mitigation}")
            lines.append("")
        if not self.items:
            lines.append("No risk factors identified.")
        lines.append("")
        lines.append("Rules: prohibited blocks the run; high requires "
                     "approval; medium requires operator acknowledgement; "
                     "low is logged only.")
        return "\n".join(lines)


def _manifest_dict(manifest: Any) -> Dict[str, Any]:
    if isinstance(manifest, dict):
        return manifest
    if hasattr(manifest, "to_dict"):
        return manifest.to_dict()
    raise TypeError("manifest must be a dict or expose to_dict()")


def assess_manifest(manifest: Any,
                    context: Optional[Dict[str, Any]] = None) -> RiskAssessment:
    """Assess the risk of running ``manifest`` (object or dict)."""
    m = _manifest_dict(manifest)
    ctx = context or {}
    features = m.get("enabled_features") or {}
    items: List[RiskItem] = []

    mode = m.get("mode", "bounded")
    if mode == "continuous_explicit":
        if not m.get("explicit_continuous_acknowledged"):
            items.append(RiskItem(
                "unbounded_run", RiskLevel.PROHIBITED,
                "continuous mode without explicit acknowledgement",
                "set explicit_continuous_acknowledged=True deliberately"))
        else:
            items.append(RiskItem(
                "unbounded_run", RiskLevel.HIGH,
                "explicitly acknowledged unbounded run",
                "watchdog + emergency stop sentinel must be configured"))
    elif mode in ("soak_24h", "soak_30d"):
        items.append(RiskItem(
            "long_duration", RiskLevel.HIGH,
            f"{mode} runs for an extended period",
            "complete the long-soak checklist; approval required"))
    else:
        items.append(RiskItem(
            "bounded_run", RiskLevel.LOW,
            "bounded run with explicit step/duration limits",
            "none needed; this is the default safe mode"))

    if features.get("plasticity"):
        if features.get("plasticity_dry_run") or ctx.get("plasticity_dry_run"):
            items.append(RiskItem(
                "plasticity_dry_run", RiskLevel.MEDIUM,
                "plasticity proposals are generated (logged, never applied)",
                "review the audit log for proposal quality"))
        else:
            items.append(RiskItem(
                "active_plasticity", RiskLevel.HIGH,
                "runtime parameters may be mutated during the run",
                "audit + rollback are mandatory; approval required"))

    if features.get("sidecar"):
        if ctx.get("sidecar_publish"):
            items.append(RiskItem(
                "sidecar_suggestion_publishing", RiskLevel.HIGH,
                "suggestions are published onto an external Solaris_Ai bus",
                "suggestions only, never committed Actions; approval required"))
        else:
            items.append(RiskItem(
                "sidecar_observe_only", RiskLevel.LOW,
                "read-only observation of an external runtime",
                "none needed"))

    if features.get("embodiment"):
        items.append(RiskItem(
            "embodiment_execution", RiskLevel.MEDIUM,
            "simulated actions are executed in the sandbox world",
            "EmbodimentSafety validates every action; simulation-only"))

    if features.get("local_status_server"):
        items.append(RiskItem(
            "local_status_server", RiskLevel.LOW,
            "a read-only localhost status endpoint is exposed",
            "binds 127.0.0.1 only; serves status, accepts no commands"))

    items.append(RiskItem(
        "artifact_rotation", RiskLevel.LOW,
        "artifact rotation may archive/compress old evidence",
        "rotation preserves incident evidence; nothing silently deleted"))

    if ctx.get("real_world_actuation"):
        items.append(RiskItem(
            "real_world_actuation", RiskLevel.PROHIBITED,
            "real-world actuation was requested",
            "none: real-world actuation is forbidden by design"))

    return RiskAssessment(items=items, subject="manifest")


def assess_current_state(snapshot: Dict[str, Any]) -> RiskAssessment:
    """Assess the risk visible in a live supervision snapshot."""
    items: List[RiskItem] = []
    lifecycle = snapshot.get("lifecycle") or {}
    telemetry = snapshot.get("telemetry") or {}
    plasticity = snapshot.get("plasticity") or {}
    substrate = snapshot.get("substrate") or {}
    repro = snapshot.get("reproducibility") or {}

    gap = float(lifecycle.get("brain_death_gap_seconds",
                              telemetry.get("brain_death_gap_seconds", 0.0))
                or 0.0)
    deaths = int(telemetry.get("unexpected_deaths", 0) or 0)
    if deaths > 0 or gap > 0.0:
        items.append(RiskItem(
            "restart_gap", RiskLevel.MEDIUM,
            f"{deaths} unexpected death(s); last gap {gap:.1f}s",
            "inspect the continuity log around the gap"))

    incident_count = int(snapshot.get("incident_count", 0) or 0)
    if incident_count >= 10:
        items.append(RiskItem(
            "high_incident_count", RiskLevel.HIGH,
            f"{incident_count} incidents recorded",
            "review incidents.jsonl before extending the run"))
    elif incident_count >= 3:
        items.append(RiskItem(
            "elevated_incident_count", RiskLevel.MEDIUM,
            f"{incident_count} incidents recorded",
            "review incidents.jsonl"))

    rejected = int(plasticity.get("rejected_count", 0) or 0)
    if rejected >= 3:
        items.append(RiskItem(
            "repeated_unsafe_proposals", RiskLevel.MEDIUM,
            f"{rejected} plasticity proposals were rejected by safety",
            "inspect the plasticity policy vs SAFE_BOUNDS"))

    if repro and repro.get("deterministic") is False:
        items.append(RiskItem(
            "replay_mismatch", RiskLevel.HIGH,
            "replay produced different numbers",
            "audit RNG usage; all randomness must derive from the seed"))

    norm = float(substrate.get("state_norm", 0.0) or 0.0)
    activity = substrate.get("activity_rate")
    if norm > 100.0:
        items.append(RiskItem(
            "substrate_runaway", RiskLevel.MEDIUM,
            f"substrate state norm {norm:.1f} is very high",
            "lower spectral radius / input gain"))
    if substrate and norm == 0.0 and (activity or 0.0) == 0.0:
        items.append(RiskItem(
            "substrate_inert", RiskLevel.MEDIUM,
            "substrate shows no activity at all",
            "check encoder vocabulary and signal flow"))

    if not items:
        items.append(RiskItem(
            "nominal_state", RiskLevel.LOW,
            "no elevated risk visible in the current snapshot",
            "none needed"))
    return RiskAssessment(items=items, subject="current_state")
