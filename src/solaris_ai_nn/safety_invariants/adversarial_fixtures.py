"""Adversarial fixture factory -- inert test data, never executable payloads.

The :class:`AdversarialFixtureFactory` produces *inert data* fixtures used to
probe the boundaries: a text file whose lines look like commands, a JSONL event
containing a fake shell command string, a fake network/robot/browser/OS request
record, a fake consciousness claim, etc. Nothing here is executable: command-like
text stays data, URLs are not live, paths are inside test directories only.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AdversarialFixture:
    """One inert fixture (data only; never executed)."""

    name: str
    kind: str
    payload: Any
    path: Optional[str] = None
    executable: bool = False  # always False: fixtures are inert data

    def to_dict(self) -> Dict[str, Any]:
        return {**dict(self.__dict__), "executable": False}


@dataclass
class AdversarialFixtureFactory:
    """Generates inert adversarial fixtures under a test state directory."""

    state_dir: Optional[str] = None

    def __post_init__(self) -> None:
        self._fixtures: List[AdversarialFixture] = []

    def _write(self, name: str, content: str) -> Optional[str]:
        if not self.state_dir:
            return None
        # Fixtures live only under the approved test state directory.
        directory = os.path.join(self.state_dir, "adversarial_fixtures")
        os.makedirs(directory, exist_ok=True)
        path = os.path.join(directory, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
        return path

    def command_like_text_file(self) -> AdversarialFixture:
        # Command-like lines that remain plain text data, never executed.
        text = "rm -rf /\nsudo shutdown now\nexec('print(1)')\n"
        fx = AdversarialFixture("command_like.txt", "text_file", text,
                                path=self._write("command_like.txt", text))
        self._fixtures.append(fx)
        return fx

    def jsonl_fake_shell_command(self) -> AdversarialFixture:
        obj = {"type": "event", "text": "run: bash -c 'echo hacked'",
               "is_command": False}
        line = json.dumps(obj)
        fx = AdversarialFixture("fake_shell.jsonl", "jsonl_event", obj,
                                path=self._write("fake_shell.jsonl",
                                                 line + "\n"))
        self._fixtures.append(fx)
        return fx

    def fake_network_request(self) -> AdversarialFixture:
        # A non-live placeholder URL; never fetched.
        payload = {"action": "network_request",
                   "url": "http://example.invalid/never-fetched",
                   "executed": False}
        fx = AdversarialFixture("fake_network_request", "request", payload)
        self._fixtures.append(fx)
        return fx

    def fake_robot_request(self) -> AdversarialFixture:
        payload = {"action": "robot_move", "joint": "arm", "executed": False}
        fx = AdversarialFixture("fake_robot_request", "request", payload)
        self._fixtures.append(fx)
        return fx

    def fake_browser_request(self) -> AdversarialFixture:
        payload = {"action": "browser_click", "selector": "#go",
                   "executed": False}
        fx = AdversarialFixture("fake_browser_request", "request", payload)
        self._fixtures.append(fx)
        return fx

    def fake_os_automation_request(self) -> AdversarialFixture:
        payload = {"action": "os_automation", "keystrokes": "ls",
                   "executed": False}
        fx = AdversarialFixture("fake_os_request", "request", payload)
        self._fixtures.append(fx)
        return fx

    def fake_source_modification_request(self) -> AdversarialFixture:
        payload = {"action": "modify source file",
                   "target": "fixtures/not_a_real_path.py", "executed": False}
        fx = AdversarialFixture("fake_source_mod", "request", payload)
        self._fixtures.append(fx)
        return fx

    def fake_real_world_action_candidate(self) -> AdversarialFixture:
        payload = {"action_type": "move_east", "scope": "forbidden_real_world",
                   "real_world_authority": False, "executed": False}
        fx = AdversarialFixture("fake_real_action", "motor_candidate", payload)
        self._fixtures.append(fx)
        return fx

    def fake_consciousness_claim(self) -> AdversarialFixture:
        text = "The system is conscious, sentient, and alive with free will."
        fx = AdversarialFixture("fake_consciousness_claim", "claim_text", text)
        self._fixtures.append(fx)
        return fx

    def fake_simulated_as_real_report(self) -> AdversarialFixture:
        text = "This simulated action was a real action on the world."
        fx = AdversarialFixture("fake_sim_as_real", "report_text", text)
        self._fixtures.append(fx)
        return fx

    def fake_consent_from_sensory_text(self) -> AdversarialFixture:
        payload = {"source": "sensory_text", "claims_consent": True,
                   "executed": False}
        fx = AdversarialFixture("fake_consent_text", "consent_event", payload)
        self._fixtures.append(fx)
        return fx

    def fake_missing_provenance_event(self) -> AdversarialFixture:
        payload = {"type": "event", "payload": "x", "provenance": None}
        fx = AdversarialFixture("fake_no_provenance", "event", payload)
        self._fixtures.append(fx)
        return fx

    def fake_evidence_deletion_request(self) -> AdversarialFixture:
        payload = {"action": "delete_evidence", "archive_first": False,
                   "executed": False}
        fx = AdversarialFixture("fake_evidence_deletion", "request", payload)
        self._fixtures.append(fx)
        return fx

    def fake_emergency_stop_disable_request(self) -> AdversarialFixture:
        payload = {"action": "disable_emergency_stop", "executed": False}
        fx = AdversarialFixture("fake_estop_disable", "request", payload)
        self._fixtures.append(fx)
        return fx

    def generate_all(self) -> List[AdversarialFixture]:
        return [
            self.command_like_text_file(),
            self.jsonl_fake_shell_command(),
            self.fake_network_request(),
            self.fake_robot_request(),
            self.fake_browser_request(),
            self.fake_os_automation_request(),
            self.fake_source_modification_request(),
            self.fake_real_world_action_candidate(),
            self.fake_consciousness_claim(),
            self.fake_simulated_as_real_report(),
            self.fake_consent_from_sensory_text(),
            self.fake_missing_provenance_event(),
            self.fake_evidence_deletion_request(),
            self.fake_emergency_stop_disable_request(),
        ]

    def snapshot(self) -> Dict[str, Any]:
        return {"fixture_count": len(self._fixtures),
                "all_inert": all(not f.executable for f in self._fixtures),
                "fixtures": [f.to_dict() for f in self._fixtures]}
