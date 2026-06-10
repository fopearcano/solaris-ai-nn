"""SolarisRuntimeProbe -- duck-typed inspection of a Solaris_Ai-like runtime.

The probe never imports ``solaris`` directly and never calls methods that act
(no ``stimulate``, no ``react``, no lifecycle calls). It only checks which
attributes/methods *exist* on an object that looks like Solaris_Ai's
``Conscience``, inspects its bus capabilities, and grades the result into a
:class:`SolarisCompatibilityReport`.
"""

from __future__ import annotations

from typing import Any, List, Optional

from .compatibility import (
    BUS_OBSERVABLE,
    FULL_TEST_READY,
    MINIMAL,
    SIDECAR_READY,
    UNAVAILABLE,
    FeatureStatus,
    SolarisCompatibilityReport,
)
from .optional_imports import import_solaris_signals

# Conscience-level features we look for (duck typing, no direct imports).
CONSCIENCE_FEATURES = ("bus", "lifecycle", "stimulate", "react", "snapshot",
                       "topology", "inner_map")
# Bus-level features.
BUS_FEATURES = ("subscribe", "subscribe_all", "publish", "subscriptions",
                "unsubscribe")


class SolarisRuntimeProbe:
    """Probe a Conscience-like object and grade its sidecar compatibility."""

    def __init__(self) -> None:
        self._report: Optional[SolarisCompatibilityReport] = None

    def probe(self, conscience_or_module: Any) -> SolarisCompatibilityReport:
        """Inspect ``conscience_or_module`` and produce a compatibility report."""
        report = SolarisCompatibilityReport()
        target = conscience_or_module

        if target is None:
            report.level = UNAVAILABLE
            report.notes.append("no runtime object supplied")
            self._report = report
            return report

        # If given a module, probe its Conscience class (never instantiate).
        if not hasattr(target, "bus") and hasattr(target, "Conscience"):
            target = getattr(target, "Conscience")
            report.notes.append("probed module's Conscience class (not an instance)")

        # Conscience-level features.
        for name in CONSCIENCE_FEATURES:
            present = hasattr(target, name) and getattr(target, name) is not None
            report.features.append(FeatureStatus(
                name=name, present=present,
                detail="" if present else f"object has no usable {name!r}"))

        # Bus-level features + subscriptions, if a bus exists.
        bus = getattr(target, "bus", None)
        if bus is not None:
            for name in BUS_FEATURES:
                present = callable(getattr(bus, name, None))
                report.features.append(FeatureStatus(
                    name=f"bus.{name}", present=present,
                    detail="" if present else f"bus has no callable {name!r}"))
            subs = getattr(bus, "subscriptions", None)
            if callable(subs):
                try:
                    raw = subs()
                    if isinstance(raw, dict):
                        report.bus_subscriptions = {
                            str(k): v for k, v in list(raw.items())[:50]}
                except Exception as exc:  # inspection only; never fail the probe
                    report.notes.append(f"bus.subscriptions() raised: {exc}")

        # Canonical Solaris signal classes (from the real package, if present).
        report.signal_classes = sorted(import_solaris_signals().keys())
        if not report.signal_classes:
            report.notes.append(
                "real Solaris signal classes not importable; duck-typed "
                "signals will be adapted by name/fields instead")

        report.level = self._grade(report)
        self._report = report
        return report

    @staticmethod
    def _grade(report: SolarisCompatibilityReport) -> str:
        bus_ok = (report.has("bus") and report.has("bus.publish")
                  and (report.has("bus.subscribe") or report.has("bus.subscribe_all")))
        if not bus_ok:
            # Something exists but cannot be observed through a bus.
            any_feature = any(f.present for f in report.features)
            return MINIMAL if any_feature else UNAVAILABLE
        sidecar = bus_ok and report.has("stimulate") and report.has("react") \
            and report.has("snapshot")
        if not sidecar:
            return BUS_OBSERVABLE
        full = sidecar and report.has("lifecycle") and report.has("inner_map") \
            and bool(report.signal_classes)
        return FULL_TEST_READY if full else SIDECAR_READY

    # -- conveniences over the last probe ------------------------------------

    def is_compatible(self, minimum: str = BUS_OBSERVABLE) -> bool:
        return self._report is not None and self._report.is_compatible(minimum)

    def missing_features(self) -> List[str]:
        return [] if self._report is None else self._report.missing_features()

    def to_dict(self) -> dict:
        return {} if self._report is None else self._report.to_dict()
