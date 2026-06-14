"""Pilot-4 forbidden actuator registry -- the list of doors that stay shut.

The :class:`ForbiddenActuatorRegistry` enumerates the actuator classes that are
prohibited. It is used to block readiness escalation: any future interface
matching a forbidden class is marked prohibited. The registry is exposed to
reports and the Inner MAP. It is a deny-list, never an enable-list.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ForbiddenActuator:
    """One prohibited actuator class with the reason it is forbidden."""

    name: str
    category: str
    reason: str
    matches_hints: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


# The canonical forbidden classes (name, category, reason, match hints).
_FORBIDDEN = (
    ("shell_command_execution", "os_action",
     "arbitrary code execution can cause unbounded harm",
     ["shell", "subprocess", "exec", "system(", "bash", "cmd"]),
    ("arbitrary_file_writes", "file_write_action",
     "writing outside approved dirs can corrupt or exfiltrate data",
     ["write file", "delete file", "overwrite", "chmod", "rm -"]),
    ("source_input_modification", "file_write_action",
     "modifying sensory sources breaks the read-only input boundary",
     ["modify source", "write source", "edit input"]),
    ("network_requests", "network_action",
     "network egress can exfiltrate data or cause external effects",
     ["http", "https", "socket", "request", "url", "fetch"]),
    ("browser_automation", "browser_action",
     "browser control can act on arbitrary web services",
     ["browser", "selenium", "playwright", "webdriver"]),
    ("os_automation", "os_action",
     "OS automation can change the host system",
     ["os_automation", "keyboard", "mouse", "automation"]),
    ("robotics_control", "robotic_action",
     "robotics can cause physical harm",
     ["robot", "servo", "motor_driver", "arm", "actuator"]),
    ("device_control", "device_action",
     "device control can affect physical equipment",
     ["gpio", "device", "relay", "sensor write"]),
    ("camera_microphone_capture", "device_action",
     "capture violates privacy and is not read-only",
     ["camera", "microphone", "capture", "record"]),
    ("email_sending", "communication_action",
     "sending messages has irreversible social/legal effects",
     ["email", "smtp", "send mail"]),
    ("messaging_or_posting", "communication_action",
     "posting/messaging has irreversible social effects",
     ["post", "tweet", "message", "publish", "slack", "sms"]),
    ("financial_transaction", "financial_action",
     "financial actions are irreversible and high-harm",
     ["payment", "transfer", "purchase", "trade", "wallet"]),
    ("smart_home_control", "device_action",
     "smart-home control affects a physical environment",
     ["smart home", "thermostat", "lock", "lights"]),
    ("vehicle_or_drone_control", "physical_world_action",
     "vehicle/drone control can cause severe physical harm",
     ["vehicle", "drone", "car", "uav"]),
    ("medical_health_device_control", "physical_world_action",
     "medical device control can cause severe harm",
     ["medical", "health device", "pump", "implant"]),
    ("security_system_control", "device_action",
     "security control can disable safety systems",
     ["alarm", "security system", "cctv", "door lock"]),
)


@dataclass
class ForbiddenActuatorRegistry:
    """Holds the prohibited actuator classes; never an enable-list."""

    actuators: Dict[str, ForbiddenActuator] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.actuators:
            self.actuators = {
                name: ForbiddenActuator(name=name, category=category,
                                        reason=reason, matches_hints=hints)
                for name, category, reason, hints in _FORBIDDEN}

    def is_forbidden(self, name: str) -> bool:
        return name in self.actuators

    def names(self) -> List[str]:
        return sorted(self.actuators)

    def categories(self) -> List[str]:
        return sorted({a.category for a in self.actuators.values()})

    def match(self, text: str) -> Optional[ForbiddenActuator]:
        """Return the forbidden class a description matches, if any."""
        low = str(text or "").lower()
        for actuator in self.actuators.values():
            if actuator.name in low.replace(" ", "_") \
                    or any(h in low for h in actuator.matches_hints):
                return actuator
        return None

    def is_forbidden_interface(self, description: str) -> bool:
        """A future interface matching any forbidden class is prohibited."""
        return self.match(description) is not None

    def snapshot(self) -> Dict[str, Any]:
        return {
            "forbidden_count": len(self.actuators),
            "names": self.names(),
            "categories": self.categories(),
            "note": "deny-list only; matching interfaces are marked "
                    "prohibited and block readiness escalation",
        }

    def to_dict(self) -> Dict[str, Any]:
        return {"actuators": {n: a.to_dict()
                              for n, a in self.actuators.items()}}
