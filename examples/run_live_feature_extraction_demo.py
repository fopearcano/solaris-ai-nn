#!/usr/bin/env python3
"""Live feature extraction demo: scalar, absence, rhythm; gloss never truth.

    python examples/run_live_feature_extraction_demo.py --state-dir .solaris_ai_nn_live/feat_demo

Loads the bundled stable-pattern fixture and extracts feature vectors directly:
scalar payload buckets, absence markers, and (where available) rhythm markers. It
demonstrates that the debug gloss is kept only as a non-ground-truth annotation and
that the operator pulse is not treated as teaching. Read-only; nothing is learned.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.live_ontogenesis import LiveFeatureExtractor

_FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "live_ontogenesis")


def _load(fixture: str):
    path = os.path.join(_FIXTURES, fixture)
    rows = []
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
    return rows


def main():
    parser = argparse.ArgumentParser(description="Live feature extraction demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_live/feat_demo")
    parser.add_argument("--fixture", type=str,
                        default="sample_stable_patterns.jsonl")
    args = parser.parse_args()

    events = _load(args.fixture)
    result = LiveFeatureExtractor().extract(accepted_events=events,
                                            load_status="stable")
    d = result.to_dict()

    print("=== Live feature extraction demo ===")
    print(f"  feature vectors : {d['live_feature_vector_count']}")
    print(f"  by source       : {d['by_source']}")
    print(f"  by modality     : {d['by_modality']}")
    print(f"  skipped         : {d['skipped_count']} (private/secret)")
    scalar = next((v for v in result.vectors if v.scalar_values), None)
    absence = next((v for v in result.vectors if v.is_absence), None)
    gloss = next((v for v in result.vectors if v.debug_gloss_annotation), None)
    if scalar:
        print(f"  scalar feature  : {scalar.source_id} {scalar.scalar_values}")
    if absence:
        print(f"  absence feature : {absence.source_id} (is_absence=True)")
    if gloss:
        gd = gloss.to_dict()
        print(f"  debug gloss     : kept as annotation only; "
              f"human_label_is_ground_truth={gd['human_label_is_ground_truth']}, "
              f"debug_gloss_is_ground_truth={gd['debug_gloss_is_ground_truth']}")
    print("note            : debug gloss is a non-ground-truth annotation; the "
          "operator pulse is stimulus, not teaching; human text is represented "
          "structurally, not semantically.")


if __name__ == "__main__":
    main()
