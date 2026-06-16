"""Birth certificate -- the operational record of a live read-only birth.

:class:`BirthCertificateBuilder` writes the birth certificate (Markdown + JSON).
The certificate is operational, not biological: it states explicitly that it does
not imply consciousness, sentience, biological life, personhood, agency, free will,
emotion, feeling, understanding, self-awareness, autonomous self-improvement, or
subjective experience.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

_DISCLAIMER = (
    "This is an operational live-read-only birth event. It does not imply "
    "consciousness, sentience, biological life, personhood, agency, free will, "
    "emotion, feeling, understanding, self-awareness, autonomous "
    "self-improvement, or subjective experience.")


@dataclass
class BirthCertificate:
    """The structured birth certificate."""

    run_id: str
    fields: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = {"birth_run_id": self.run_id}
        d.update(self.fields)
        d["disclaimer"] = _DISCLAIMER
        return d

    def render_md(self) -> str:
        f = self.fields
        lines = [f"# Live Read-Only Birth Certificate ({self.run_id})", "",
                 f"> {_DISCLAIMER}", "",
                 f"- created_at_utc: {f.get('created_at_utc')}",
                 f"- profile id: {f.get('profile_id')}",
                 f"- governance file: {f.get('governance_file_path')}",
                 f"- feeder registry: {f.get('feeder_registry_path')}",
                 f"- allowed sources: {', '.join(f.get('allowed_sources', []))}",
                 f"- forbidden sources: "
                 f"{len(f.get('forbidden_sources', []))} listed",
                 f"- inbox files read: {f.get('inbox_files_read', 0)}",
                 f"- accepted events: {f.get('accepted_event_count', 0)}",
                 f"- quarantined events: {f.get('quarantined_event_count', 0)}",
                 f"- first accepted event id: "
                 f"{f.get('first_accepted_event_id') or 'none'}",
                 f"- first accepted event timestamp: "
                 f"{f.get('first_accepted_event_timestamp') or 'none'}",
                 f"- first absence event id: "
                 f"{f.get('first_absence_event_id') or 'none'}",
                 f"- first noise/overload event id: "
                 f"{f.get('first_noise_event_id') or 'none'}",
                 f"- first operator pulse id: "
                 f"{f.get('first_operator_pulse_id') or 'none'}",
                 f"- first safety block: "
                 f"{f.get('first_safety_block') or 'none'}",
                 f"- membrane activation: {f.get('membrane_activation_status')}",
                 f"- metabolism status: "
                 f"{f.get('metabolism_status') or 'not run'}",
                 f"- safety status: {f.get('safety_status')}",
                 ""]
        if f.get("operator_note"):
            lines += [f"- operator note: {f.get('operator_note')}", ""]
        lines += ["## Limitations", ""]
        lines += [f"- {l}" for l in f.get("limitations", [])]
        lines += ["", "_No feeder was started or controlled; no hardware, "
                  "network, Git/GitHub, shell, browser, or OS access occurred; "
                  "no command was executed; and no sensory text was treated as a "
                  "command._"]
        return "\n".join(lines) + "\n"


@dataclass
class BirthCertificateBuilder:
    """Builds and writes the birth certificate for a run."""

    state_dir: str = ".solaris_ai_nn_live"

    def build(self, *, run_id: str, profile: Any, governance_path: str,
              feeder_registry_path: str, allowed_sources: List[str],
              forbidden_sources: List[str], inbox_result: Dict[str, Any],
              membrane: Dict[str, Any], metabolism_status: str = "",
              first_safety_block: str = "", safety_status: str = "pass",
              operator_note: str = "") -> BirthCertificate:
        fields = {
            "created_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                            time.gmtime()),
            "profile_id": getattr(profile, "profile_id", ""),
            "governance_file_path": governance_path,
            "feeder_registry_path": feeder_registry_path,
            "allowed_sources": list(allowed_sources),
            "forbidden_sources": list(forbidden_sources),
            "inbox_files_read": inbox_result.get("live_inbox_file_count", 0),
            "accepted_event_count": inbox_result.get(
                "live_event_accepted_count", 0),
            "quarantined_event_count": inbox_result.get(
                "live_event_quarantined_count", 0),
            "first_accepted_event_id": membrane.get("first_event_id", ""),
            "first_accepted_event_timestamp": membrane.get(
                "first_event_timestamp", ""),
            "first_absence_event_id": membrane.get("first_absence_event_id", ""),
            "first_noise_event_id": membrane.get("first_noise_event_id", ""),
            "first_operator_pulse_id": membrane.get(
                "first_operator_pulse_id", ""),
            "first_safety_block": first_safety_block,
            "membrane_activation_status": (
                "activated" if membrane.get("membrane_activated") else "not "
                "activated"),
            "metabolism_status": metabolism_status,
            "safety_status": safety_status,
            "operator_note": operator_note,
            "limitations": list(getattr(profile, "limitations", [])),
        }
        return BirthCertificate(run_id=run_id, fields=fields)

    def write(self, certificate: BirthCertificate) -> Dict[str, str]:
        base = os.path.join(self.state_dir, "certificates")
        os.makedirs(base, exist_ok=True)
        md_path = os.path.join(base,
                               f"BIRTH_CERTIFICATE_{certificate.run_id}.md")
        json_path = os.path.join(base,
                                 f"BIRTH_CERTIFICATE_{certificate.run_id}.json")
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(certificate.render_md())
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(certificate.to_dict(), fh, indent=2, default=str)
        return {"markdown": md_path, "json": json_path}
