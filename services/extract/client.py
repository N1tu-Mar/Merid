"""One Fireworks client, shared by every model role in this package.

Exists so that adding a model class (vision, compact text, reranker) is a
call site and a registry entry, not another copy of HTTP plumbing with its
own subtly different timeout and error handling.

Two things it enforces everywhere:

**Schema-constrained decoding.** Requests use
``response_format: {"type": "json_schema", ...}``, so the model is
constrained at decode time to the shape we asked for. That is stronger than
parsing-and-retrying: a field outside the schema is not something the
decoder can emit. (Fireworks note: a json_schema response_format disables
reasoning output on reasoning models, which is fine — perception tasks here
want the answer, not a reasoning trace. Their docs also warn to *also* ask
for JSON in the prompt or a model can emit whitespace until it hits the
token cap, so callers must say so in their system prompt.)

**Telemetry per call.** Model id, latency, and token usage come back on
every result and are attached to the Braintrust span. That is what makes
"we route each task to a different model" checkable rather than asserted.

Failure is fail-closed: any timeout, transport error, truncation, or
malformed body raises FireworksError. Callers must convert that to
ESCALATE — never to a guess (CLAUDE.md invariant #3).
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any

import httpx

from app.tracing import log_span
from services.extract.models import model_for

log = logging.getLogger("meridian.extract.client")

FIREWORKS_URL = "https://api.fireworks.ai/inference/v1/chat/completions"

# Per-call default. Vision calls carry a page image and legitimately take
# longer than a transcript read, so callers override rather than us picking
# one number that is wrong for both.
DEFAULT_TIMEOUT_S = float(os.environ.get("FIREWORKS_TIMEOUT_S", "60"))
DEFAULT_MAX_TOKENS = int(os.environ.get("FIREWORKS_MAX_TOKENS", "8192"))


class FireworksError(Exception):
    """Any failure reaching or parsing a Fireworks response.
    Callers must treat this as ESCALATE, never fall back to a guess."""


@dataclass
class CallResult:
    """Parsed model output plus the provenance of the call that produced it."""

    data: dict[str, Any]
    task: str
    model: str
    latency_ms: int
    usage: dict[str, Any] | None = field(default=None)

    def provenance(self) -> dict[str, Any]:
        """Compact record of which model did this work, for storage and UI."""
        return {
            "task": self.task,
            "model": self.model,
            "latency_ms": self.latency_ms,
            "usage": self.usage,
        }


def api_key() -> str | None:
    """Read at call time, not import time — app.env loads .env during app
    package import, and module-level capture races that ordering."""
    return os.environ.get("FIREWORKS_API_KEY")


def call_json(
    task: str,
    messages: list[dict[str, Any]],
    schema: dict[str, Any],
    schema_name: str,
    timeout_s: float = DEFAULT_TIMEOUT_S,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> CallResult:
    """Call the model registered for `task`, constrained to `schema`.

    `messages` is OpenAI-shaped, so a vision call differs from a text call
    only in its content parts — the same reason the multi-model routing is
    cheap to maintain.
    """
    key = api_key()
    if not key:
        raise FireworksError(
            f"FIREWORKS_API_KEY not configured — {task} cannot run. "
            "Extraction fails closed to ESCALATE rather than guessing."
        )

    model = model_for(task)
    payload = {
        "model": model,
        "messages": messages,
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": schema_name, "schema": schema},
        },
        "temperature": 0,
        "max_tokens": max_tokens,
    }
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

    started = time.monotonic()
    try:
        resp = httpx.post(FIREWORKS_URL, json=payload, headers=headers, timeout=timeout_s)
        resp.raise_for_status()
    except httpx.TimeoutException as e:
        raise FireworksError(f"{task}: timed out after {timeout_s}s") from e
    except httpx.HTTPError as e:
        raise FireworksError(f"{task}: call failed: {e}") from e
    latency_ms = int((time.monotonic() - started) * 1000)

    try:
        body = resp.json()
        choice = body["choices"][0]
    except (ValueError, KeyError, IndexError) as e:
        raise FireworksError(f"{task}: malformed response: {e}") from e

    if choice.get("finish_reason") == "length":
        # Truncated mid-JSON. Parsing would either fail or silently drop
        # trailing fields — the second is worse, so refuse both.
        raise FireworksError(f"{task}: response truncated (finish_reason=length)")

    try:
        data = json.loads((choice["message"]["content"] or "").strip())
    except (KeyError, TypeError, json.JSONDecodeError) as e:
        raise FireworksError(f"{task}: response was not valid JSON: {e}") from e

    if not isinstance(data, dict):
        raise FireworksError(f"{task}: expected a JSON object, got {type(data).__name__}")

    result = CallResult(
        data=data, task=task, model=model, latency_ms=latency_ms, usage=body.get("usage")
    )
    log.info(
        "fireworks_call  task=%s  model=%s  latency_ms=%d",
        task,
        model,
        latency_ms,
        extra=result.provenance(),
    )
    log_span(metadata=result.provenance())
    return result


def image_part(image: bytes, mime: str = "image/png") -> dict[str, Any]:
    """An OpenAI-shaped image content part, base64 data-URI encoded.

    Fireworks' vision API takes the same shape as OpenAI's, which is why a
    page image slots into the same client as a transcript.
    """
    import base64

    b64 = base64.b64encode(image).decode("ascii")
    return {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}}
