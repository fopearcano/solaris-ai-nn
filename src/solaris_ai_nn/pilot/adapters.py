"""Pilot adapters -- thin glue between pilot profiles and existing runners.

Each adapter knows how to build (per supervised segment) the runner that the
profile calls for, and how to summarize what its inputs did. No runner logic
is duplicated here; the existing runners stay the single source of truth.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .pilot_manifest import PilotManifest
from .stream_sensors import SilenceWindowSensor, build_stream_sensor


@dataclass
class SimulatedPilotAdapter:
    """Profile ``simulated`` -> SensorimotorSimulationRunner segments."""

    manifest: PilotManifest

    def build_runner(self, segment_steps: int) -> Any:
        from ..embodiment.simulation_runner import SensorimotorSimulationRunner

        m = self.manifest
        return SensorimotorSimulationRunner(
            max_steps=segment_steps, seed=m.seed, state_dir=m.state_dir,
            substrate=m.substrate,
            enable_language=m.enabled_features.get("language", False),
            enable_plasticity=m.enabled_features.get("plasticity", False))

    def input_summary(self) -> Dict[str, Any]:
        return {"kind": "simulated", "inputs": ["grid_world_sensors"],
                "external_data": False}


@dataclass
class ReadOnlyStreamPilotAdapter:
    """Profile ``read_only_stream`` -> ContinuousRunner + stream sensors.

    One sensor chain is shared across all supervised segments so the stream
    position survives segment boundaries.
    """

    manifest: PilotManifest
    silence_window: int = 5
    default_intensity: float = 0.5

    sensors: List[SilenceWindowSensor] = field(default_factory=list,
                                               init=False)
    _provider: Optional[Callable] = field(default=None, init=False)

    def __post_init__(self) -> None:
        for source in self.manifest.input_sources:
            self.sensors.append(build_stream_sensor(
                source, silence_window=self.silence_window,
                default_intensity=self.default_intensity))

    def stimulus_provider(self) -> Callable:
        """Round-robin over the configured sensors (built once, shared)."""
        if self._provider is None:
            sensors = self.sensors

            def provider(step: int):
                for sensor in sensors:
                    stimulus = sensor(step)
                    if stimulus is not None:
                        return stimulus
                return None

            self._provider = provider
        return self._provider

    def build_runner(self, segment_steps: int) -> Any:
        from ..runtime.continuous_runner import ContinuousRunner

        m = self.manifest
        return ContinuousRunner(
            state_dir=m.state_dir, max_steps=segment_steps, seed=m.seed,
            substrate_name=m.substrate,
            stimulus_provider=self.stimulus_provider(),
            enable_language=m.enabled_features.get("language", False),
            enable_plasticity=m.enabled_features.get("plasticity", False),
            plasticity_dry_run=m.enabled_features.get("plasticity_dry_run",
                                                      False),
            enable_latent=m.enabled_features.get("latent", False),
            enable_world_model=m.enabled_features.get("world_model", False))

    def input_summary(self) -> Dict[str, Any]:
        return {
            "kind": "read_only_stream",
            "inputs": list(self.manifest.input_sources),
            "external_data": True,
            "read_only": True,
            "sensors": [s.snapshot() for s in self.sensors],
        }


@dataclass
class SolarisSidecarPilotAdapter:
    """Profile ``solaris_sidecar_observe`` -> observe-only SolarisNNSidecar.

    The adapter exposes a runner-shaped object (``run()`` / ``stop()`` /
    ``bridge``) so the OperationalSupervisor can drive it in segments. The
    conscience is injected (fake or real); an optional ``driver`` callable
    pumps signals per step in demos -- with a real runtime, signals simply
    arrive while we observe.
    """

    manifest: PilotManifest
    conscience: Any = None
    driver: Optional[Callable[[Any, int], None]] = None
    publish_suggestions: bool = False  # off by default; approval-gated
    governance: Any = None

    sidecar: Any = field(default=None, init=False)
    steps_observed: int = field(default=0, init=False)

    def _ensure_sidecar(self) -> Any:
        from ..integration.conscience_sidecar import SolarisNNSidecar

        if self.conscience is None:
            raise ValueError("the sidecar pilot needs a conscience to "
                             "observe (inject a fake one for demos)")
        if self.sidecar is None:
            self.sidecar = SolarisNNSidecar(
                observe_only=not self.publish_suggestions,
                publish_suggestions=self.publish_suggestions,
                governance=self.governance,
                seed=self.manifest.seed,
                substrate_name=self.manifest.substrate)
            self.sidecar.attach(self.conscience)
        return self.sidecar

    def build_runner(self, segment_steps: int) -> Any:
        adapter = self

        class _SidecarSegment:
            """One bounded observation window, runner-shaped."""

            def __init__(self) -> None:
                self.bridge = adapter._ensure_sidecar().bridge
                self._stopped = False

            def run(self) -> Dict[str, Any]:
                sidecar = adapter._ensure_sidecar()
                sidecar.start()
                for step in range(segment_steps):
                    if self._stopped:
                        break
                    adapter.steps_observed += 1
                    if adapter.driver is not None:
                        adapter.driver(adapter.conscience,
                                       adapter.steps_observed)
                sidecar.stop()
                return sidecar.snapshot()

            def stop(self, reason: str = "") -> None:
                self._stopped = True

        return _SidecarSegment()

    def input_summary(self) -> Dict[str, Any]:
        summary: Dict[str, Any] = {
            "kind": "solaris_sidecar_observe",
            "inputs": ["solaris_bus_signals"],
            "external_data": True,
            "observe_only": not self.publish_suggestions,
            "steps_observed": self.steps_observed,
        }
        if self.sidecar is not None:
            summary["sidecar"] = self.sidecar.integration_summary()
        return summary
