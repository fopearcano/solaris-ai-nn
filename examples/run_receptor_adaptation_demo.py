#!/usr/bin/env python3
"""Receptor adaptation demo: baseline learning -> sensitivity shift -> fatigue.

    python examples/run_receptor_adaptation_demo.py --state-dir .solaris_ai_nn_state/test_receptor_adaptation

Drives one receptor with a calm baseline, then a sustained burst, then silence,
and shows that the receptor learns a baseline, sensitises to novelty, fatigues /
saturates under sustained intensity, and recovers -- i.e. long exposure changes
future perception.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.plural_sensorium import Receptor
from solaris_ai_nn.plural_sensorium.event_envelope import SensoryEventEnvelope


def _event(power, ts):
    return SensoryEventEnvelope(source_id="vib_feed", source_kind="fixture_replay",
                                modality="vibration", features={"amp": power},
                                timestamp=ts)


def main():
    parser = argparse.ArgumentParser(description="Receptor adaptation demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/test_receptor_adaptation")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    r = Receptor(receptor_id="vib", modality="vibration", source_id="vib_feed")
    print("=== Receptor adaptation demo ===")
    # Calm baseline.
    for i in range(5):
        r.observe(_event(0.3, float(i)))
    print(f"after calm: baseline={r.baseline:.3f} sensitivity="
          f"{r.sensitivity.value:.2f} state={r.adaptation_state}")
    sens_before = r.sensitivity.value
    # Sudden burst -> novelty -> sensitise.
    r.observe(_event(1.5, 5.0))
    print(f"after burst: novelty={r.recent_novelty:.2f} sensitivity="
          f"{r.sensitivity.value:.2f} state={r.adaptation_state}")
    # Sustained high intensity -> fatigue / saturation.
    for i in range(6):
        r.observe(_event(1.6, 6.0 + i))
    print(f"after sustained: fatigue={r.fatigue:.2f} saturation="
          f"{r.saturation:.2f} state={r.adaptation_state}")
    # Silence -> recovery.
    for _ in range(4):
        r.observe_silence()
    print(f"after silence: fatigue={r.fatigue:.2f} silence="
          f"{r.silence_duration:.1f} state={r.adaptation_state}")
    print(f"adaptation events     : {r.adaptation_count}")
    print(f"sensitivity changed   : {r.sensitivity.value != sens_before}")
    print("note                  : long exposure changes future perception; "
          "internal attention only, no hardware.")


if __name__ == "__main__":
    main()
