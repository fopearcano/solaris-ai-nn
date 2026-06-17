#!/usr/bin/env python3
"""Receptor field demo: chronos, machine body, operator pulse, unknown source.

    python examples/run_receptor_field_demo.py --state-dir .solaris_ai_nn_live/receptor_demo

Builds the membrane receptor field and matches a few sample events, showing which
receptor handles each source. The operator-pulse receptor is attenuated by default
and the unknown-source receptor is conservative.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.environmental_membrane import EnvironmentalReceptorField


def _ev(eid, sid, modality="scalar", absence=False):
    return {"event_id": eid, "source_id": sid, "modality": modality,
            "channel": "c", "payload": {"v": 1},
            "quality": {"is_absence": absence, "is_noisy": False}}


def main():
    parser = argparse.ArgumentParser(description="Receptor field demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_live/receptor_demo")
    args = parser.parse_args()

    field = EnvironmentalReceptorField()
    print("=== Receptor field demo ===")
    print(f"  receptors: {field.index()['membrane_receptor_count']}")
    samples = [
        ("chronos", _ev("e1", "chronos_absence", "chronos")),
        ("machine body", _ev("e2", "machine_body")),
        ("operator pulse", _ev("e3", "operator_pulse", "pulse")),
        ("unknown source", _ev("e4", "mystery_source")),
        ("absence", _ev("e5", "chronos_absence", "chronos", absence=True)),
    ]
    for label, ev in samples:
        m = field.match(ev)
        r = field.receptor(m.receptor_id)
        perm = getattr(r, "baseline_permeability", "?")
        print(f"  {label:<16} -> {m.receptor_id} (baseline permeability {perm})")
    print("note: the operator-pulse receptor is attenuated by default; the "
          "unknown-source receptor is conservative; debug gloss never defines "
          "internal truth.")


if __name__ == "__main__":
    main()
