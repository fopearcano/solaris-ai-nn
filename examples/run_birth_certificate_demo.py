#!/usr/bin/env python3
"""Birth certificate demo: certificate from a synthetic accepted batch, disclaimer.

    python examples/run_birth_certificate_demo.py --state-dir .solaris_ai_nn_live/test_certificate

Builds a birth certificate from a synthetic accepted-event batch and shows the
required non-claim disclaimer. The certificate is operational, not biological: it
does not imply consciousness, life, or agency.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.live_birth import (
    BirthCertificateBuilder,
    default_live_birth_profile,
)


def main():
    parser = argparse.ArgumentParser(description="Birth certificate demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_live/test_certificate")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    profile = default_live_birth_profile()
    builder = BirthCertificateBuilder(state_dir=args.state_dir)
    certificate = builder.build(
        run_id="demo_birth",
        profile=profile,
        governance_path=".solaris_ai_nn_live/governance/LIVE_READONLY_GOVERNANCE.json",
        feeder_registry_path=".solaris_ai_nn_live/feeders/FEEDER_REGISTRY.json",
        allowed_sources=profile.allowed_sources,
        forbidden_sources=profile.forbidden_sources,
        inbox_result={"live_inbox_file_count": 1,
                      "live_event_accepted_count": 6,
                      "live_event_quarantined_count": 5},
        membrane={"membrane_activated": True, "first_event_id": "ev_chronos_1",
                  "first_event_timestamp": "2026-06-16T18:00:00Z",
                  "first_absence_event_id": "ev_chronos_2",
                  "first_operator_pulse_id": "ev_pulse_1"},
        metabolism_status="report-only handoff of 6 accepted event(s)",
        operator_note="synthetic accepted batch (demo)")
    paths = builder.write(certificate)

    print("=== Birth certificate demo ===")
    print(f"  certificate (md)  : {paths['markdown']}")
    print(f"  certificate (json): {paths['json']}")
    d = certificate.to_dict()
    print(f"  first accepted id : {d['first_accepted_event_id']}")
    print(f"  first absence id  : {d['first_absence_event_id']}")
    print(f"  first pulse id    : {d['first_operator_pulse_id']}")
    print(f"  accepted / quarantined: {d['accepted_event_count']} / "
          f"{d['quarantined_event_count']}")
    print("  required disclaimer:")
    print(f"    {d['disclaimer']}")


if __name__ == "__main__":
    main()
