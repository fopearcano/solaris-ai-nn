"""Console summary cards: generated, blocker card, skipped optional, membrane metrics."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _tester_console_helpers import (  # noqa: E402
    build_console,
    stage_membrane_bypass,
)
from solaris_ai_nn.tester_console import SummaryCardKind, SummarySeverity  # noqa: E402


def test_cards_generated(tmp_path):
    rt = build_console(tmp_path, fixture=True)
    kinds = {c.kind for c in rt.cards}
    assert SummaryCardKind.FIXTURE_DEMO in kinds
    assert SummaryCardKind.SAFETY in kinds
    assert SummaryCardKind.MEMBRANE in kinds


def test_blocker_card_appears(tmp_path):
    stage_membrane_bypass(os.path.join(str(tmp_path), "live"))
    rt = build_console(tmp_path)
    integ = next(c for c in rt.cards
                 if c.kind == SummaryCardKind.MEMBRANE_INTEGRATION)
    assert integ.status == SummarySeverity.BLOCKER
    assert integ.blockers


def test_skipped_optional_card_appears(tmp_path):
    rt = build_console(tmp_path, fixture=True)
    onto = next(c for c in rt.cards
                if c.kind == SummaryCardKind.ONTOGENESIS)
    assert onto.status == SummarySeverity.OPTIONAL_SKIPPED


def test_membrane_card_includes_impression_metrics(tmp_path):
    live = os.path.join(str(tmp_path), "live")
    os.makedirs(os.path.join(live, "membrane", "index"), exist_ok=True)
    import json
    json.dump({"membrane_impression_count": 7},
              open(os.path.join(live, "membrane", "index", "i.json"), "w"))
    rt = build_console(tmp_path)
    impr = next(c for c in rt.cards
                if c.kind == SummaryCardKind.SENSORY_IMPRESSIONS)
    assert impr.metrics.get("impression_count") == 7
