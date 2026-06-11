"""Approval router -- operator decisions onto real pending requests only.

Approvals and rejections must name an existing pending request in the
ApprovalRegistry; unknown and expired requests come back as grounded
refusals that list what *is* pending. An approval grants exactly the
permission the request named -- it bypasses nothing prohibited.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .operator_commands import OperatorCommand
from .response_builder import CommunicationResponse, ResponseBuilder
from .templates import render


@dataclass
class ApprovalRouter:
    """Parses approve/reject commands against the ApprovalRegistry."""

    registry: Any = None
    audit: Any = None
    builder: ResponseBuilder = field(default_factory=ResponseBuilder)
    approvals_processed: int = field(default=0, init=False)
    rejections_processed: int = field(default=0, init=False)
    refused: int = field(default=0, init=False)

    def handle(self, command: OperatorCommand,
               context: Optional[Dict[str, Any]] = None,
               ) -> CommunicationResponse:
        if self.registry is None:
            return self.builder.missing_component_response(
                "approval registry")
        request_id = str(command.parsed_args.get("request_id", ""))
        operator = command.operator or "operator"
        approve = command.type == "approve_governance_request"
        try:
            if approve:
                request = self.registry.approve(
                    request_id, operator,
                    note=f"approved via communication gateway "
                         f"(command {command.command_id})")
                self.approvals_processed += 1
                text = render("governance_approved",
                              request_id=request.request_id,
                              permission=request.requested_permission,
                              operator=operator, status=request.status)
            else:
                request = self.registry.reject(
                    request_id, operator,
                    reason=f"rejected via communication gateway "
                           f"(command {command.command_id})")
                self.rejections_processed += 1
                text = render("governance_rejected",
                              request_id=request.request_id,
                              permission=request.requested_permission,
                              operator=operator)
            return self.builder.governance_response(
                text, [f"approval_request:{request.request_id}",
                       f"command:{command.command_id}"])
        except KeyError:
            self.refused += 1
            pending = ", ".join(
                r.request_id for r in self.registry.list_pending()[:5]) \
                or "none"
            return self.builder.governance_response(
                render("governance_unknown", request_id=request_id,
                       pending=pending),
                [f"approvals:pending=[{pending}]"], executed=False)
        except ValueError as exc:
            self.refused += 1
            return self.builder.governance_response(
                render("governance_expired", request_id=request_id,
                       reason=str(exc)),
                [f"approval_request:{request_id}"], executed=False)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "approvals_processed": self.approvals_processed,
            "rejections_processed": self.rejections_processed,
            "refused": self.refused,
            "pending": ([r.request_id for r in
                         self.registry.list_pending()]
                        if self.registry is not None else []),
        }
