"""Tests for the multi-model perception layer.

Covers the routing table, the shared Fireworks client, and the two readers
built on it. No network: httpx.post is stubbed everywhere, so these run
without a FIREWORKS_API_KEY and without spending tokens.
"""

from __future__ import annotations

import json

import httpx
import pytest

from services.extract import client as client_mod
from services.extract import models, transcript, vision
from services.extract.client import CallResult, FireworksError, call_json, image_part
from services.extract.schema import ExtractionError, features_schema, to_features

PNG = b"\x89PNG\r\n\x1a\nfake-page-bytes"


# ---------------------------------------------------------------------------
# fakes
# ---------------------------------------------------------------------------


class FakeResponse:
    def __init__(self, body: dict, status: int = 200):
        self._body = body
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("boom", request=None, response=None)

    def json(self):
        return self._body


def completion(content: dict | str, finish_reason: str = "stop", usage: dict | None = None):
    text = content if isinstance(content, str) else json.dumps(content)
    return {
        "choices": [{"message": {"content": text}, "finish_reason": finish_reason}],
        "usage": usage or {"prompt_tokens": 10, "completion_tokens": 20},
    }


@pytest.fixture
def capture(monkeypatch):
    """Stub httpx.post, record the payload, return a configurable body."""
    box: dict = {"payload": None, "timeout": None, "body": completion({"age": 42})}

    def fake_post(url, json=None, headers=None, timeout=None):
        box["payload"] = json
        box["timeout"] = timeout
        body = box["body"]
        if isinstance(body, Exception):
            raise body
        return FakeResponse(body)

    monkeypatch.setattr(client_mod.httpx, "post", fake_post)
    monkeypatch.setenv("FIREWORKS_API_KEY", "test-key")
    return box


# ---------------------------------------------------------------------------
# registry
# ---------------------------------------------------------------------------


def test_every_task_has_a_distinct_model_and_a_rationale():
    for task, spec in models.REGISTRY.items():
        assert spec.task == task
        assert spec.default.startswith("accounts/fireworks/models/")
        assert spec.why.strip(), f"{task} has no rationale"
        assert spec.modality in {"vision", "text", "embedding", "rerank"}


def test_registry_spans_more_than_one_model_class():
    """The argument is multi-model, not one model called several times."""
    assert len({s.modality for s in models.REGISTRY.values()}) >= 4
    assert len({s.default for s in models.REGISTRY.values()}) >= 4


def test_env_var_overrides_the_default(monkeypatch):
    monkeypatch.setenv("FIREWORKS_VISION_MODEL", "accounts/fireworks/models/other-vlm")
    assert models.model_for("referral_vision") == "accounts/fireworks/models/other-vlm"


def test_unknown_task_raises_rather_than_defaulting():
    with pytest.raises(models.UnknownTask):
        models.model_for("not_a_task")


def test_registry_report_is_serialisable_and_flags_overrides(monkeypatch):
    monkeypatch.setenv("FIREWORKS_TRANSCRIPT_MODEL", "accounts/fireworks/models/pinned")
    report = {r["task"]: r for r in models.registry_report()}
    json.dumps(report)  # must not raise
    assert report["transcript_extract"]["overridden"] is True
    assert report["transcript_extract"]["model"] == "accounts/fireworks/models/pinned"
    assert report["referral_vision"]["overridden"] is False


# ---------------------------------------------------------------------------
# client: schema-constrained decoding + telemetry
# ---------------------------------------------------------------------------


def test_request_constrains_decoding_to_the_schema(capture):
    call_json(
        task="transcript_extract",
        messages=[{"role": "user", "content": "hi"}],
        schema={"type": "object"},
        schema_name="Thing",
    )
    fmt = capture["payload"]["response_format"]
    assert fmt["type"] == "json_schema"
    assert fmt["json_schema"]["name"] == "Thing"
    assert capture["payload"]["temperature"] == 0


def test_result_carries_model_and_latency_provenance(capture):
    result = call_json(
        task="transcript_extract",
        messages=[{"role": "user", "content": "hi"}],
        schema={"type": "object"},
        schema_name="Thing",
    )
    assert isinstance(result, CallResult)
    assert result.model == models.model_for("transcript_extract")
    assert result.latency_ms >= 0
    prov = result.provenance()
    assert prov["task"] == "transcript_extract"
    assert prov["usage"]["completion_tokens"] == 20


def test_missing_api_key_fails_closed(capture, monkeypatch):
    monkeypatch.delenv("FIREWORKS_API_KEY", raising=False)
    with pytest.raises(FireworksError, match="not configured"):
        call_json("transcript_extract", [], {"type": "object"}, "T")


@pytest.mark.parametrize(
    "body, match",
    [
        (completion({"age": 1}, finish_reason="length"), "truncated"),
        (completion("not json at all"), "not valid JSON"),
        (completion("[1, 2, 3]"), "expected a JSON object"),
        ({"choices": []}, "malformed response"),
    ],
)
def test_unusable_responses_fail_closed(capture, body, match):
    capture["body"] = body
    with pytest.raises(FireworksError, match=match):
        call_json("transcript_extract", [], {"type": "object"}, "T")


def test_timeout_fails_closed(capture):
    capture["body"] = httpx.TimeoutException("slow")
    with pytest.raises(FireworksError, match="timed out"):
        call_json("transcript_extract", [], {"type": "object"}, "T")


def test_transport_error_fails_closed(capture):
    capture["body"] = httpx.ConnectError("no route")
    with pytest.raises(FireworksError, match="call failed"):
        call_json("transcript_extract", [], {"type": "object"}, "T")


def test_image_part_is_a_base64_data_uri():
    part = image_part(PNG, mime="image/png")
    assert part["type"] == "image_url"
    assert part["image_url"]["url"].startswith("data:image/png;base64,")


# ---------------------------------------------------------------------------
# shared extraction contract
# ---------------------------------------------------------------------------


def test_schema_is_generated_from_the_pydantic_model():
    schema = features_schema()
    assert "rectal_bleeding" in schema["properties"]
    assert "source_refs" in schema["properties"]


def test_unsourced_metadata_for_null_fields_is_dropped():
    """A model citing a field it then reported as null must not leave the
    field looking populated to anything counting source_refs."""
    features = to_features(
        {
            "age": 42,
            "rectal_bleeding": None,
            "source_refs": {"age": "p1: '42 y/o'", "rectal_bleeding": "p1: nothing"},
            "extraction_confidence": {"age": 0.9, "rectal_bleeding": 0.4},
        }
    )
    assert "rectal_bleeding" not in features.source_refs
    assert "rectal_bleeding" not in features.extraction_confidence
    assert features.source_refs["age"] == "p1: '42 y/o'"


def test_invalid_output_raises_extraction_error():
    with pytest.raises(ExtractionError, match="schema validation"):
        to_features({"fit_result": "maybe-positive"})


# ---------------------------------------------------------------------------
# transcript reader (path B for voice)
# ---------------------------------------------------------------------------


def test_transcript_reader_uses_the_transcript_model(capture):
    capture["body"] = completion(
        {
            "age": 52,
            "rectal_bleeding": True,
            "source_refs": {"rectal_bleeding": "patient: 'apart from the bleeding'"},
            "extraction_confidence": {"rectal_bleeding": 0.8},
        }
    )
    features, result = transcript.extract_from_transcript("agent: ...\npatient: nope, apart from the bleeding")
    assert features.rectal_bleeding is True
    assert result.model == models.model_for("transcript_extract")
    assert capture["payload"]["model"] == models.model_for("transcript_extract")


def test_transcript_reader_rejects_empty_input(capture):
    with pytest.raises(ExtractionError, match="empty transcript"):
        transcript.extract_from_transcript("   ")


def test_format_transcript_matches_the_call_turn_shape():
    text = transcript.format_transcript([("agent", "Any bleeding?"), ("patient", "nope, apart from the bleeding")])
    assert text == "agent: Any bleeding?\npatient: nope, apart from the bleeding"


# ---------------------------------------------------------------------------
# vision reader (documents)
# ---------------------------------------------------------------------------


def test_vision_reader_sends_every_page_and_uses_the_vision_model(capture):
    capture["body"] = completion({"age": 42, "source_refs": {"age": "page 1: '42 y/o'"}})
    features, result = vision.extract_from_images([PNG, PNG, PNG])

    assert features.age == 42
    assert result.model == models.model_for("referral_vision")
    parts = capture["payload"]["messages"][1]["content"]
    assert sum(1 for p in parts if p["type"] == "image_url") == 3


def test_vision_reader_gets_a_longer_timeout_than_text(capture):
    capture["body"] = completion({"age": 42})
    vision.extract_from_images([PNG])
    assert capture["timeout"] == vision.VISION_TIMEOUT_S
    assert vision.VISION_TIMEOUT_S > 60.0


def test_vision_context_is_passed_but_pages_still_carry_the_facts(capture):
    capture["body"] = completion({"age": 42})
    vision.extract_from_images([PNG], context="patient-uploaded medical history")
    parts = capture["payload"]["messages"][1]["content"]
    assert any("patient-uploaded medical history" in p.get("text", "") for p in parts)


def test_vision_reader_rejects_empty_and_oversized_page_sets(capture):
    with pytest.raises(ExtractionError, match="no page images"):
        vision.extract_from_images([])
    with pytest.raises(ExtractionError, match="MAX_PAGES"):
        vision.extract_from_images([PNG] * (vision.MAX_PAGES + 1))
    with pytest.raises(ExtractionError, match="empty"):
        vision.extract_from_images([PNG, b""])


# ---------------------------------------------------------------------------
# the two readers feed reconciliation
# ---------------------------------------------------------------------------


def test_both_readers_produce_reconcilable_output(capture):
    """Same schema from both paths is what makes disagreement meaningful
    rather than an artefact of differing prompts."""
    from services.extract.reconcile import reconcile

    capture["body"] = completion(
        {"age": 52, "rectal_bleeding": False, "source_refs": {"rectal_bleeding": "patient: 'nope'"}}
    )
    from_transcript, _ = transcript.extract_from_transcript("patient: nope")

    capture["body"] = completion(
        {"age": 52, "rectal_bleeding": True, "source_refs": {"rectal_bleeding": "page 1: 'blood PR'"}}
    )
    from_pages, _ = vision.extract_from_images([PNG])

    result = reconcile(deterministic=from_transcript, model=from_pages)
    assert result.has_conflict
    assert result.features.rectal_bleeding is True
