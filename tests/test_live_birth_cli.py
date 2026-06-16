"""Live birth CLI: init, doctor, birth (safe sample), quarantine, certificate."""

from __future__ import annotations

import json
import os
import shutil

from solaris_ai_nn.cli import main
from solaris_ai_nn.live_birth import approved_governance, feeder_registry_template

_SAMPLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "examples", "live_birth", "sample_inbox")


def _approve(state_dir):
    with open(os.path.join(state_dir, "governance",
                           "LIVE_READONLY_GOVERNANCE.json"), "w") as fh:
        json.dump(approved_governance(), fh)
    with open(os.path.join(state_dir, "feeders", "FEEDER_REGISTRY.json"),
              "w") as fh:
        json.dump(feeder_registry_template(), fh)
    inbox = os.path.join(state_dir, "inbox")
    for fn in ("birth_events.jsonl", "unsafe_events.jsonl"):
        src = os.path.join(_SAMPLE, fn)
        if os.path.isfile(src):
            shutil.copy(src, os.path.join(inbox, fn))


def test_live_init_command(tmp_path):
    rc = main(["live-init", "--state-dir", str(tmp_path)])
    assert rc == 0
    assert os.path.isfile(os.path.join(str(tmp_path), "governance",
                                       "LIVE_READONLY_GOVERNANCE.json"))


def test_live_doctor_command(tmp_path):
    main(["live-init", "--state-dir", str(tmp_path)])
    rc = main(["live-doctor", "--state-dir", str(tmp_path)])
    assert rc == 0  # SAFE-OFF blockers, but non-strict returns 0


def test_live_birth_command_with_safe_sample(tmp_path):
    main(["live-init", "--state-dir", str(tmp_path)])
    _approve(str(tmp_path))
    rc = main(["live-birth", "--state-dir", str(tmp_path), "--max-events", "100",
               "--require-governance"])
    assert rc == 0
    cert_dir = os.path.join(str(tmp_path), "certificates")
    assert any(f.endswith(".md") for f in os.listdir(cert_dir))


def test_live_quarantine_command(tmp_path):
    main(["live-init", "--state-dir", str(tmp_path)])
    _approve(str(tmp_path))
    main(["live-birth", "--state-dir", str(tmp_path), "--require-governance"])
    rc = main(["live-quarantine", "--state-dir", str(tmp_path)])
    assert rc == 0


def test_birth_certificate_command(tmp_path):
    main(["live-init", "--state-dir", str(tmp_path)])
    _approve(str(tmp_path))
    main(["live-birth", "--state-dir", str(tmp_path), "--require-governance"])
    rc = main(["birth-certificate", "--state-dir", str(tmp_path)])
    assert rc == 0


def test_strict_mode_nonzero_on_blocker(tmp_path):
    main(["live-init", "--state-dir", str(tmp_path)])  # SAFE-OFF governance
    rc = main(["live-birth", "--state-dir", str(tmp_path), "--require-governance",
               "--strict"])
    assert rc == 2


def test_alpha_group_live_init(tmp_path):
    rc = main(["alpha", "live-init", "--state-dir", str(tmp_path)])
    assert rc == 0
