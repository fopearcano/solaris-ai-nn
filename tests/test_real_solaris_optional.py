"""The real-Solaris example must skip gracefully when Solaris_Ai is absent."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
EXAMPLE = REPO / "examples" / "run_real_solaris_integration_if_available.py"


def test_real_solaris_example_exits_gracefully():
    proc = subprocess.run(
        [sys.executable, str(EXAMPLE)],
        capture_output=True, text=True, timeout=60, cwd=str(REPO),
    )
    # Exit code 0 whether or not the real package is installed.
    assert proc.returncode == 0, proc.stderr
    out = proc.stdout
    assert "real Solaris_Ai integration" in out
    # Either it skipped gracefully or it attached/detached cleanly.
    assert ("exiting gracefully" in out) or ("Detached cleanly" in out)


def test_optional_layer_importable_without_solaris():
    # Importing the integration package itself never requires solaris.
    from solaris_ai_nn import integration

    assert hasattr(integration, "SolarisNNSidecar")
    assert integration.is_solaris_available() in (True, False)


def test_plasticity_cannot_touch_solaris_runtime():
    """Integration safety rules (section 17) hold in the validator."""
    from solaris_ai_nn.plasticity.mutation import (
        PlasticityChange,
        PlasticityStep,
        PlasticityTarget,
    )
    from solaris_ai_nn.plasticity.safety import PlasticitySafetyValidator

    v = PlasticitySafetyValidator()

    def step(component, parameter, new):
        return PlasticityStep(target=PlasticityTarget(component, parameter),
                              change=PlasticityChange(old_value=None, new_value=new))

    # Cannot mutate Solaris runtime objects / bus subscriptions / lifecycle.
    assert not v.is_safe(step("conscience", "anything", 1))
    assert not v.is_safe(step("solaris_bus", "handlers", []))
    assert not v.is_safe(step("bridge", "bus_subscriptions", []))
    assert not v.is_safe(step("bridge", "lifecycle_death", True))
    # Cannot publish committed actions or flip observe_only automatically.
    assert not v.is_safe(step("bridge", "publish_committed_action", True))
    assert not v.is_safe(step("bridge", "observe_only", False))
    # Cannot enable real integration below sidecar_ready...
    weak = step("inner_map", "integration_enabled", True)
    assert not v.is_safe(weak, {"compatibility_level": "bus_observable"})
    # ...but may at sidecar_ready or better.
    assert v.is_safe(step("inner_map", "integration_enabled", True),
                     {"compatibility_level": "sidecar_ready"})
