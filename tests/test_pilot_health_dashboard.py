"""Pilot-1 health dashboard: Markdown + JSON output, degraded modules shown."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.pilot1 import (
    PilotConfig,
    PilotHealthDashboard,
    PilotObservabilityCollector,
)


def _dash(tmp_path):
    cfg = PilotConfig(base_dir=str(tmp_path))
    obs = PilotObservabilityCollector(base_dir=str(tmp_path))
    obs.observe(snapshot={"structural_change_score": 0.1,
                          "proto_symbol_count": 3})
    return PilotHealthDashboard(base_dir=str(tmp_path)), obs, cfg


def test_dashboard_files_generated(tmp_path):
    dash, obs, cfg = _dash(tmp_path)
    state = dash.build_state(observability=obs, config=cfg)
    paths = dash.write(state)
    assert os.path.exists(paths["markdown"]) and os.path.exists(paths["json"])


def test_dashboard_json_valid(tmp_path):
    dash, obs, cfg = _dash(tmp_path)
    state = dash.build_state(observability=obs, config=cfg)
    paths = dash.write(state)
    data = json.loads(open(paths["json"]).read())
    assert "pilot_phase" in data and "exit_recommendation" in data


def test_degraded_module_shown(tmp_path):
    dash, obs, cfg = _dash(tmp_path)
    state = dash.build_state(observability=obs, config=cfg,
                             extra={"degraded_modules": ["world_model"]})
    md = dash.render_markdown(state)
    assert "world_model" in md


def test_dashboard_disclaims_personhood(tmp_path):
    dash, obs, cfg = _dash(tmp_path)
    state = dash.build_state(observability=obs, config=cfg)
    assert "Not a person" in dash.render_markdown(state)
