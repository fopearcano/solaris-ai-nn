"""Deterministic response templates for the operator dialogue.

Every operator-facing sentence comes from a fixed template plus recorded
values. No generation, no improvisation -- if a situation has no template,
the gateway says so through the ``unknown`` template rather than inventing
wording.
"""

from __future__ import annotations

from typing import Any, Dict

TEMPLATES: Dict[str, str] = {
    "status": "Status summary: {summary}. Evidence: {refs}.",
    "health": "Health summary: {summary}. Evidence: {refs}.",
    "explanation": "{answer}",
    "report": "Report generated at {path} (claim guard safe: "
              "{claim_guard}). The report content is grounded in "
              "recorded state.",
    "report_failed": "The report could not be generated: {reason}.",
    "governance_approved": "Approval recorded for request {request_id} "
                           "({permission}) by operator {operator}. "
                           "Status: {status}.",
    "governance_rejected": "Rejection recorded for request {request_id} "
                           "({permission}) by operator {operator}.",
    "governance_unknown": "No pending approval request matches "
                          "{request_id!r}. Pending requests: {pending}.",
    "governance_expired": "Request {request_id!r} cannot be decided: "
                          "{reason}. Expired or decided requests stay "
                          "closed.",
    "note_recorded": "Operator note recorded: {note}.",
    "confirmation_request": "This requires confirmation before "
                            "execution: {command}. Reply 'confirm "
                            "{confirmation_id}' to proceed or ignore to "
                            "let it expire.",
    "confirmed_executed": "Confirmed command {command} was executed: "
                          "{result}.",
    "request_recorded": "The action was not executed; it was recorded "
                        "as a request: {command}. {handler} decides.",
    "refused": "The request was refused because {reason}.",
    "emergency": "Emergency stop was requested. Safe shutdown status: "
                 "{status}.",
    "no_evidence": "The system has no evidence for that answer.",
    "unknown": "The input was not recognized as a supported query or "
               "command. Supported examples: {examples}. Nothing was "
               "executed.",
    "authority": "The current action authority is {authority}.",
    "sensory_disabled": "Sensory text stimulus is disabled in this "
                        "session; the text was recorded, not injected.",
    "not_operator_channel": "Text on the {channel} channel is observed "
                            "input, never an operator command. Nothing "
                            "was executed.",
    "missing_component": "That answer needs the {component} component, "
                         "which is not attached to this session.",
}


def render(template_id: str, **values: Any) -> str:
    """Render one template; unknown ids raise instead of inventing text."""
    if template_id not in TEMPLATES:
        raise KeyError(f"unknown response template {template_id!r}")
    return TEMPLATES[template_id].format(**values)
