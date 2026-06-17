"""Impression loader: impressions load, missing warns/blocks, fields exposed."""

from __future__ import annotations

import os
import sys

from solaris_ai_nn.membrane_integration import SensoryImpressionLoader

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _membrane_integration_helpers import stage_pipeline  # noqa: E402


def test_impressions_load(tmp_path):
    state = stage_pipeline(str(tmp_path))
    result = SensoryImpressionLoader().load(state)
    assert result.membrane_present is True
    assert result.impressions_present is True
    assert len(result.impressions) == 4


def test_missing_impressions_warn_or_block(tmp_path):
    # No membrane staged.
    warn = SensoryImpressionLoader().load(str(tmp_path))
    assert warn.warnings
    assert not warn.blockers
    block = SensoryImpressionLoader().load(
        str(tmp_path), require_membrane=True, require_impressions=True)
    assert block.blockers


def test_contamination_and_source_pressure_fields_exposed(tmp_path):
    state = stage_pipeline(str(tmp_path))
    result = SensoryImpressionLoader().load(state)
    imp = result.impressions[0]
    d = imp.to_dict()
    for field in ("contamination", "source_pressure", "receptor_id",
                  "permeability_status", "salience"):
        assert field in d


def test_clean_impressions_filter(tmp_path):
    state = stage_pipeline(str(tmp_path))
    result = SensoryImpressionLoader().load(state)
    # The operator-pulse impression has contamination 0.4 (< 0.5) so is clean;
    # all fixture impressions are non-blocked.
    assert len(result.clean_impressions) == len(result.impressions)
