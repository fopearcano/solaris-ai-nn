#!/usr/bin/env python3
"""Attach the NN sidecar to the REAL Solaris_Ai runtime -- if it is installed.

This example never fails when ``fopearcano/solaris-ai`` is absent: it checks
importability first and exits gracefully with instructions. When the real
package is available it instantiates a Conscience (without starting its async
loops), probes compatibility, attaches the sidecar in observe-only mode,
optionally lets the runtime emit a few signals, prints the report, and detaches.

    python examples/run_real_solaris_integration_if_available.py
"""

from __future__ import annotations

import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.integration import (
    SolarisNNSidecar,
    SolarisRuntimeProbe,
    get_solaris_import_error,
    import_solaris_conscience,
    is_solaris_available,
)


def main() -> int:
    print("=" * 70)
    print("Solaris-AI-NN -- real Solaris_Ai integration (optional)")
    print("=" * 70)

    if not is_solaris_available():
        print("Solaris_Ai is NOT importable in this environment -- exiting gracefully.")
        print(f"  recorded import error: {get_solaris_import_error()}")
        print()
        print("To run this example against the real runtime:")
        print("  1. clone https://github.com/fopearcano/solaris-ai")
        print("  2. make its `src/` importable, e.g.:")
        print("       pip install -e /path/to/solaris-ai")
        print("     or PYTHONPATH=/path/to/solaris-ai/src python examples/"
              "run_real_solaris_integration_if_available.py")
        print("  3. re-run this example.")
        print()
        print("Nothing failed: the integration layer is optional by design.")
        return 0

    conscience_cls = import_solaris_conscience()
    if conscience_cls is None:
        print("`solaris` imports but no Conscience class was found "
              f"({get_solaris_import_error()}).")
        print("Probing the module surface only; exiting gracefully.")
        return 0

    # Instantiate WITHOUT starting it: we only probe + observe-attach.
    try:
        conscience = conscience_cls()
    except Exception as exc:
        print(f"Conscience() could not be instantiated safely: {exc}")
        print("Probing the class surface instead (no instance, no side effects).")
        report = SolarisRuntimeProbe().probe(conscience_cls)
        print(json.dumps(report.to_dict(), indent=2, default=str))
        return 0

    sidecar = SolarisNNSidecar(observe_only=True)
    report = sidecar.attach(conscience)
    print(f"compatibility: {report.summary()}")

    try:
        sidecar.start()
        print("sidecar attached + observing (observe-only; the real Bus is async --")
        print("signals will flow once the Solaris event loop runs).")
        # We do NOT start Solaris_Ai's async lifecycle here and we inject no
        # stimuli: this smoke test proves safe attach/probe/detach only.
        print("-" * 70)
        print("sidecar snapshot:")
        print(json.dumps(sidecar.snapshot()["integration"], indent=2, default=str))
    finally:
        sidecar.detach()
        print("-" * 70)
        print("Detached cleanly. No stimulate/react/death was called; no Action committed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
