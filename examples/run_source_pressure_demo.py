#!/usr/bin/env python3
"""Source pressure demo: balanced diet, dominant operator, silent, noisy.

    python examples/run_source_pressure_demo.py --state-dir .solaris_ai_nn_live/pressure_demo

Computes membrane source pressure for several synthetic batches: a balanced diet, an
operator-dominated batch, a batch with a silent expected source, and a noisy batch.
Source pressure informs permeability but never modifies feeders.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.environmental_membrane import MembraneSourcePressure


def _ev(sid, noisy=False):
    return {"event_id": f"e_{sid}_{noisy}", "source_id": sid, "modality": "scalar",
            "channel": "c", "payload": {"v": 1},
            "quality": {"is_absence": False, "is_noisy": noisy}, "debug_gloss": ""}


def main():
    parser = argparse.ArgumentParser(description="Source pressure demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_live/pressure_demo")
    args = parser.parse_args()

    sp = MembraneSourcePressure()
    balanced = [_ev(s) for s in ("chronos_absence", "machine_body",
                                 "local_weather_readonly_external",
                                 "project_artifact_field")]
    operator = [_ev("operator_pulse") for _ in range(6)] + [_ev("machine_body")]
    silent = [_ev("machine_body") for _ in range(4)]
    noisy = [_ev("machine_body", noisy=True) for _ in range(4)]

    print("=== Source pressure demo ===")
    for label, events, expected in [
            ("balanced diet", balanced, []),
            ("operator dominant", operator, []),
            ("silent expected source", silent,
             ["chronos_absence", "operator_pulse"]),
            ("noisy source", noisy, [])]:
        a = sp.assess(events=events, expected_sources=expected).to_dict()
        print(f"  {label:<24} status={a['status']} "
              f"(operator {a['membrane_operator_dominance_score']}, "
              f"dominance {a['membrane_source_pressure_dominance_score']})")
    print("note: source pressure informs permeability but never modifies "
          "feeders; recommendations are report-only; dominance is always "
          "visible.")


if __name__ == "__main__":
    main()
