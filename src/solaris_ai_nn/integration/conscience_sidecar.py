"""SolarisNNSidecar -- mount Solaris-AI-NN beside a Solaris_Ai Conscience.

The sidecar is the one-stop attachment point: it probes a Conscience-like
runtime, builds (or accepts) a :class:`SolarisNeuralBridge`, wires a
:class:`SolarisBusConnector`, a :class:`SignalMirror`, and a
:class:`SuggestionChannel`, and exposes status/persistence.

What the sidecar will NEVER do (these are design invariants, not options):

* call ``conscience.stimulate()`` or ``conscience.react()`` on its own
  (an experiment may drive the conscience directly -- the sidecar won't);
* call any lifecycle/death method on the conscience;
* alter Solaris_Ai module wiring or source files;
* commit Actions -- everything outbound is a clearly-marked suggestion.

Solaris_Ai remains the organism and the action authority; the sidecar observes,
learns, and proposes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..bridges.neural_bridge import SolarisNeuralBridge
from ..signals.encoding import EventEncoder
from .bus_connector import SolarisBusConnector
from .compatibility import BUS_OBSERVABLE, SolarisCompatibilityReport
from .integration_state import IntegrationState
from .signal_mirror import SignalMirror
from .solaris_probe import SolarisRuntimeProbe
from .suggestion_channel import SuggestionChannel

DEFAULT_ACTIONS = ["approach", "withdraw", "consume", "observe"]


@dataclass
class SolarisNNSidecar:
    """Optional adaptive substrate attached beside a Solaris_Ai runtime.

    Args:
        bridge: An existing bridge to use (one is built if omitted).
        observe_only: Never publish anything (suggestions are stored locally).
        publish_suggestions: Allow publishing when not observe-only.
        action_labels / vocabulary / substrate_name / seed: bridge defaults.
        suggestion_threshold: Minimum confidence to publish a suggestion.
        mirror_capacity: Bound on the in-memory signal mirror.
    """

    bridge: Optional[SolarisNeuralBridge] = None
    observe_only: bool = False
    publish_suggestions: bool = True
    action_labels: List[str] = field(default_factory=lambda: list(DEFAULT_ACTIONS))
    vocabulary: Optional[List[str]] = None
    substrate_name: str = "esn"
    seed: int = 0
    suggestion_threshold: float = 0.5
    mirror_capacity: int = 5_000

    probe: SolarisRuntimeProbe = field(default_factory=SolarisRuntimeProbe)
    report: Optional[SolarisCompatibilityReport] = field(default=None, init=False)
    connector: Optional[SolarisBusConnector] = field(default=None, init=False)
    mirror: Optional[SignalMirror] = field(default=None, init=False)
    channel: Optional[SuggestionChannel] = field(default=None, init=False)
    _conscience: Any = field(default=None, init=False, repr=False)
    _started: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if self.bridge is None:
            self.bridge = SolarisNeuralBridge(
                action_labels=list(self.action_labels),
                encoder=EventEncoder(vocabulary=self.vocabulary),
                substrate_name=self.substrate_name,
                seed=self.seed,
            )

    # -- lifecycle ---------------------------------------------------------------

    def attach(self, conscience: Any) -> SolarisCompatibilityReport:
        """Probe ``conscience`` and wire the sidecar to it (does not start).

        Raises ``ValueError`` if the runtime is below ``bus_observable``.
        """
        if self._conscience is not None:
            raise RuntimeError("sidecar is already attached; detach first")
        self.report = self.probe.probe(conscience)
        if not self.report.is_compatible(BUS_OBSERVABLE):
            raise ValueError(
                "runtime is not observable: " + self.report.summary())
        self._conscience = conscience
        self.mirror = SignalMirror(capacity=self.mirror_capacity)
        self.channel = SuggestionChannel(
            publish_enabled=self.publish_suggestions and not self.observe_only)
        self.connector = SolarisBusConnector(
            bridge=self.bridge,
            publish_suggestions=self.publish_suggestions,
            observe_only=self.observe_only,
            suggestion_threshold=self.suggestion_threshold,
            mirror=self.mirror,
            channel=self.channel,
        )
        state = self.connector.state
        state.compatibility_level = self.report.level
        state.observe_only = self.observe_only
        state.conscience_summary = self._safe_conscience_summary(conscience)
        return self.report

    def start(self) -> None:
        """Begin observing: subscribe the connector to the conscience's bus."""
        if self._conscience is None or self.connector is None:
            raise RuntimeError("attach(conscience) before start()")
        if self._started:
            return
        self.connector.attach(self._conscience.bus)
        self._started = True

    def stop(self) -> None:
        """Stop observing (unsubscribe / go inactive). Attachment remains."""
        if self.connector is not None and self._started:
            self.connector.detach()
        self._started = False

    def detach(self) -> None:
        """Stop and release the conscience reference. Fully reversible."""
        self.stop()
        self._conscience = None

    # -- status -------------------------------------------------------------------

    @property
    def state(self) -> IntegrationState:
        if self.connector is not None:
            return self.connector.state
        return IntegrationState(observe_only=self.observe_only)

    def integration_summary(self) -> Dict[str, Any]:
        """Compact integration status for the Inner MAP."""
        st = self.state.to_dict()
        return {
            "attached": st["attached"],
            "observing": st["observing"],
            "observe_only": st["observe_only"],
            "compatibility_level": (self.report.level if self.report
                                    else "unavailable"),
            "mirrored_signals": len(self.mirror) if self.mirror else 0,
            "suggestions_produced": st["suggestions_produced"],
            "suggestions_published": st["suggestions_published"],
            "last_suggestion_confidence": self.bridge.suggestion_confidence(),
            "action_authority": False,
            "substrate_type": self.bridge.substrate.name,
            "sidecar_health": self.healthcheck()["healthy"],
        }

    def snapshot(self) -> Dict[str, Any]:
        return {
            "started": self._started,
            "observe_only": self.observe_only,
            "compatibility": self.report.to_dict() if self.report else None,
            "connector": self.connector.snapshot() if self.connector else None,
            "bridge": self.bridge.substrate_summary(),
            "integration": self.integration_summary() if self.connector else None,
        }

    def healthcheck(self) -> Dict[str, Any]:
        errors = self.state.errors if self.connector is not None else []
        healthy = (
            self.bridge is not None
            and (self.connector is None or len(errors) == 0)
        )
        return {
            "healthy": healthy,
            "attached": self._conscience is not None,
            "started": self._started,
            "error_count": len(errors),
            "last_errors": errors[-3:],
            "compatibility_level": self.report.level if self.report else "unavailable",
        }

    # -- persistence ---------------------------------------------------------------

    def persist(self, state_dir: Union[str, Path]) -> Dict[str, str]:
        """Save integration state + suggestions + mirrored-signal summaries.

        Writes ``integration_state.json``, ``suggestions.jsonl``, and
        ``mirrored_signals.jsonl`` under ``state_dir`` (summaries only, unless
        the mirror was built with ``full_payloads=True``).
        """
        from ..runtime.persistence import PersistenceManager  # local: avoid cycle

        pm = PersistenceManager(state_dir)
        pm.save_integration_state(self.state.to_dict())
        paths = {"integration_state": str(pm.integration_state_path)}
        if self.channel is not None:
            self.channel.to_jsonl(pm.suggestions_path)
            paths["suggestions"] = str(pm.suggestions_path)
        if self.mirror is not None:
            self.mirror.to_jsonl(pm.mirrored_signals_path)
            paths["mirrored_signals"] = str(pm.mirrored_signals_path)
        return paths

    # -- helpers --------------------------------------------------------------------

    @staticmethod
    def _safe_conscience_summary(conscience: Any) -> Dict[str, Any]:
        """A tiny, read-only description of the attached runtime."""
        summary: Dict[str, Any] = {"type": type(conscience).__name__}
        snap = getattr(conscience, "snapshot", None)
        if callable(snap):
            try:
                raw = snap()
                if isinstance(raw, dict):
                    summary["snapshot_keys"] = sorted(raw)[:10]
            except Exception as exc:  # read-only: never fail attach over this
                summary["snapshot_error"] = str(exc)
        return summary
