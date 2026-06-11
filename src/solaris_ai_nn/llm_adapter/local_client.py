"""LocalHTTPLLMAdapter -- stdlib-only HTTP to a *local* model endpoint.

Supports Ollama-compatible (``/api/generate``), LM Studio compatible
(OpenAI-style ``/v1/chat/completions``), and generic local HTTP payloads,
using nothing but ``urllib``. Localhost only by default; every call has a
timeout; every failure becomes a refused response, never an exception.
No service needs to be installed or running for the rest of the system to
work -- this adapter simply refuses when nothing answers.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Dict, Optional

from .base import LLMAdapter, LLMRequest, LLMResponse
from .config import LLMAdapterConfig, is_localhost_url
from .prompt_contracts import build_prompt


class LocalHTTPLLMAdapter(LLMAdapter):
    """Talks to one configured local endpoint; refuses everything else."""

    name = "local_http"

    def __init__(self, config: Optional[LLMAdapterConfig] = None) -> None:
        super().__init__()
        self.config = config or LLMAdapterConfig(
            provider="generic_local_http")
        self.name = f"local_http:{self.config.provider}"

    # -- endpoint safety ---------------------------------------------------------------

    def endpoint_allowed(self) -> "tuple[bool, str]":
        url = self.config.endpoint_url
        if not url:
            return (False, "no endpoint_url configured")
        if is_localhost_url(url):
            return (True, "localhost endpoint")
        if self.config.allow_remote_network \
                and not self.config.allow_network_localhost_only:
            return (True, "remote endpoint explicitly enabled (requires "
                          "governance approval)")
        return (False, f"endpoint {url!r} is not localhost; remote "
                       "network access is disabled by default")

    # -- generation --------------------------------------------------------------------

    def _generate(self, request: LLMRequest) -> LLMResponse:
        allowed, reason = self.endpoint_allowed()
        if not allowed:
            return LLMResponse(request_id=request.request_id,
                               refused=True, refusal_reason=reason,
                               safety_status="refused")
        prompt = build_prompt(request)
        url, payload = self._build_call(prompt, request)
        try:
            body = json.dumps(payload).encode("utf-8")
            http_request = urllib.request.Request(
                url, data=body,
                headers={"Content-Type": "application/json"},
                method="POST")
            with urllib.request.urlopen(
                    http_request,
                    timeout=self.config.timeout_s) as response:
                data = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, OSError, ValueError,
                TimeoutError) as exc:
            return LLMResponse(
                request_id=request.request_id, refused=True,
                refusal_reason=f"local endpoint unavailable: {exc}",
                safety_status="refused")
        text = self._extract_text(data)
        if not text:
            return LLMResponse(
                request_id=request.request_id, refused=True,
                refusal_reason="endpoint returned no usable text",
                safety_status="refused")
        return LLMResponse(
            request_id=request.request_id, output_text=text,
            used_context_refs=[f"context:{key}" for key in
                               sorted(request.grounded_context)][:8],
            raw_model_name=self.config.model_name or "unknown-local")

    def _build_call(self, prompt: str, request: LLMRequest,
                    ) -> "tuple[str, Dict[str, Any]]":
        base = (self.config.endpoint_url or "").rstrip("/")
        model = self.config.model_name or "local-model"
        max_tokens = min(request.max_tokens, self.config.max_tokens)
        if self.config.provider == "ollama_compatible":
            return (f"{base}/api/generate", {
                "model": model, "prompt": prompt, "stream": False,
                "options": {"temperature": request.temperature,
                            "num_predict": max_tokens}})
        if self.config.provider == "lmstudio_compatible":
            return (f"{base}/v1/chat/completions", {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": request.temperature, "stream": False})
        return (base, {"prompt": prompt, "model": model,
                       "max_tokens": max_tokens,
                       "temperature": request.temperature})

    @staticmethod
    def _extract_text(data: Any) -> str:
        if not isinstance(data, dict):
            return ""
        # Ollama-style.
        if isinstance(data.get("response"), str):
            return data["response"].strip()
        # OpenAI-style.
        choices = data.get("choices")
        if isinstance(choices, list) and choices:
            message = choices[0].get("message") or {}
            if isinstance(message.get("content"), str):
                return message["content"].strip()
            if isinstance(choices[0].get("text"), str):
                return choices[0]["text"].strip()
        # Generic.
        for key in ("text", "output", "completion"):
            if isinstance(data.get(key), str):
                return data[key].strip()
        return ""
