#!/usr/bin/env python3
"""Live sign generator demo: opaque, deterministic; labels/gloss not identity.

    python examples/run_live_sign_generator_demo.py --state-dir .solaris_ai_nn_live/siggen_demo

Loads the bundled safe live-concept fixture and generates private sign tokens
directly. It shows that tokens are opaque (``sig_live_<hash>`` + ``LSigma-<n>``),
deterministic for a given feature signature, and that a requested label/gloss-derived
token is refused as identity (the opaque token is kept and the candidate is marked
label-dependent / contaminated). Read-only; nothing is learned.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.live_semiogenesis import (
    ConceptInputLoader,
    LivePrivateSignGenerator,
)

_FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "live_semiogenesis")


def main():
    parser = argparse.ArgumentParser(description="Live sign generator demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_live/siggen_demo")
    args = parser.parse_args()

    recs = json.load(open(os.path.join(_FIXTURES, "sample_live_concepts.json")))
    concepts = ConceptInputLoader().from_records(recs["records"],
                                                 synthetic=True).eligible
    gen = LivePrivateSignGenerator()

    print("=== Live sign generator demo ===")
    a = gen.generate_token("machine_body:scalar:aa11")
    b = gen.generate_token("machine_body:scalar:aa11")
    c = gen.generate_token("chronos_absence:chronos:cc33")
    print(f"  deterministic    : {a.private_token} == {b.private_token} -> "
          f"{a.private_token == b.private_token}")
    print(f"  opaque token A   : {a.private_token} ({a.short_code})")
    print(f"  opaque token C   : {c.private_token} ({c.short_code})")

    result = gen.generate_for_concepts(
        concepts, requested_tokens={recs["records"][0]["concept_id"]:
                                    "the calm machine state"})
    print("  generated signs  :")
    for cand in result.candidates:
        print(f"    - {cand.private_token} linked={cand.linked_concept_ids} "
              f"contam={cand.contamination_findings or 'none'}")
    print("note             : sign tokens are deterministic, opaque, and "
          "private; human labels/gloss are never used as sign identity; a "
          "label-derived request is refused and marked label-dependent.")


if __name__ == "__main__":
    main()
