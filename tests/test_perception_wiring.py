"""The referral pipeline running two readers end to end.

tests/test_referral_pipeline.py already covers the failure envelope, but it
runs with no FIREWORKS_API_KEY, so both readers fail and every case lands on
the same ESCALATE. These tests stub the readers instead, so the paths that
only exist when perception actually succeeds are exercised:

  - two readers agreeing -> corroborated, books normally
  - two readers disagreeing -> correct urgency, but never booked
  - one reader -> single-sourced, still usable
  - an image-only PDF -> readable at all, which it was not before
"""

from __future__ import annotations

import json

import pytest

from app.db import ReferralRecord, get_session
from app.schemas import ReferralFeatures
from services.extract import perception as perc
from services.referral import pipeline


@pytest.fixture
def readers(monkeypatch):
    """Stub both readers. Set .text / .vision to features or an Exception."""
    box: dict = {"text": None, "vision": None, "vision_pages": None}

    def fake_text(raw_text, model=None):
        outcome = box["text"]
        if isinstance(outcome, Exception):
            raise outcome
        if outcome is None:
            raise RuntimeError("text reader not configured for this test")
        return outcome

    def fake_vision(images, mime="image/png", context=None):
        box["vision_pages"] = len(images)
        outcome = box["vision"]
        if isinstance(outcome, Exception):
            raise outcome
        if outcome is None:
            raise RuntimeError("vision reader not configured for this test")

        class _Call:
            model = "accounts/fireworks/models/test-vlm"
            latency_ms = 42

        return outcome, _Call()

    monkeypatch.setattr("services.referral.extract.extract_features", fake_text)
    monkeypatch.setattr("services.extract.vision.extract_from_images", fake_vision)
    return box


@pytest.fixture
def sandbox(monkeypatch):
    """Stub the sandbox: control the text and page images a document yields."""
    box: dict = {"text": "REFERRAL: see attached", "images": [b"\x89PNG-page-1"]}

    def fake_parse(content, filename):
        from services.referral.sandbox import SandboxParseResult

        return SandboxParseResult(
            text=box["text"],
            sandbox_id="ds-test",
            duration_ms=12,
            sandboxed=True,
            sandbox_source="snapshot:meridian-parse:2",
            page_images=box["images"],
        )

    monkeypatch.setattr(pipeline, "parse_document_in_sandbox", fake_parse)
    return box


def feats(confidence: float = 0.9, **kwargs) -> ReferralFeatures:
    return ReferralFeatures(
        **kwargs,
        source_refs={k: f"ref:{k}" for k, v in kwargs.items() if v is not None},
        extraction_confidence={k: confidence for k, v in kwargs.items() if v is not None},
    )


def stored(referral_id: str) -> ReferralRecord:
    session = get_session()
    try:
        return session.get(ReferralRecord, referral_id)
    finally:
        session.close()


# ---------------------------------------------------------------------------


def test_agreeing_readers_produce_a_normal_bookable_verdict(readers, sandbox):
    agreed = dict(age=52, rectal_bleeding=True, prior_colonoscopy_date=None)
    readers["text"] = feats(**agreed)
    readers["vision"] = feats(**agreed)

    _, verdict = pipeline.process_referral(b"x", "referral.pdf")

    assert verdict.urgency == "urgent"
    assert verdict.disposition == "BOOK"
    report = json.loads(stored(verdict.referral_id).perception_json)
    assert report["corroborated"] is True
    assert report["has_conflict"] is False


def test_disagreeing_readers_keep_the_urgency_but_are_never_booked(readers, sandbox):
    """The whole point: OCR text missed the bleeding, the page image caught
    it. Urgency must be right AND a human must look."""
    readers["text"] = feats(age=52, rectal_bleeding=False, prior_colonoscopy_date=None)
    readers["vision"] = feats(age=52, rectal_bleeding=True, prior_colonoscopy_date=None)

    _, verdict = pipeline.process_referral(b"x", "referral.pdf")

    assert verdict.urgency == "urgent", "resolved toward the more urgent reading"
    assert verdict.disposition == "ESCALATE", "a disputed fact is never booked"
    assert "BLEEDING_OVER_50" in verdict.rules_fired

    report = json.loads(stored(verdict.referral_id).perception_json)
    assert report["has_conflict"] is True
    assert report["conflicts"] == ["rectal_bleeding"]


def test_conflict_escalates_without_discarding_the_rules_fired(readers, sandbox):
    """A bare ESCALATE would have thrown away why it was urgent."""
    readers["text"] = feats(age=42, rectal_bleeding=False, abdominal_pain=True)
    readers["vision"] = feats(age=42, rectal_bleeding=True, abdominal_pain=True)

    _, verdict = pipeline.process_referral(b"x", "referral.pdf")

    assert verdict.disposition == "ESCALATE"
    assert "YOUNG_BLEEDING_PLUS_FEATURE" in verdict.rules_fired


def test_text_only_document_runs_one_reader_and_still_works(readers, sandbox):
    sandbox["images"] = []
    readers["text"] = feats(age=52, rectal_bleeding=True, prior_colonoscopy_date=None)

    _, verdict = pipeline.process_referral(b"x", "referral.txt")

    assert verdict.urgency == "urgent"
    report = json.loads(stored(verdict.referral_id).perception_json)
    assert report["corroborated"] is False, "one reader is not corroboration"
    field = next(f for f in report["fields"] if f["field"] == "rectal_bleeding")
    assert field["state"] == "single_sourced"


def test_image_only_pdf_is_now_readable_at_all(readers, sandbox):
    """A scanned fax with no extractable text used to be unparseable. The
    vision reader can read the page, so it reaches triage instead."""
    sandbox["text"] = ""
    readers["vision"] = feats(age=52, rectal_bleeding=True, prior_colonoscopy_date=None)
    readers["text"] = RuntimeError("should not be consulted for empty text")

    _, verdict = pipeline.process_referral(b"x", "scan.pdf")

    assert verdict.urgency == "urgent"
    assert verdict.disposition == "BOOK"
    assert readers["vision_pages"] == 1


def test_document_with_neither_text_nor_pages_still_escalates(readers, sandbox):
    sandbox["text"] = ""
    sandbox["images"] = []

    _, verdict = pipeline.process_referral(b"x", "empty.pdf")

    assert verdict.disposition == "ESCALATE"
    assert verdict.rules_fired == []
    assert stored(verdict.referral_id).perception_json is None


def test_both_readers_failing_escalates_rather_than_guessing(readers, sandbox):
    readers["text"] = RuntimeError("fireworks down")
    readers["vision"] = RuntimeError("fireworks down")

    _, verdict = pipeline.process_referral(b"x", "referral.pdf")

    assert verdict.disposition == "ESCALATE"
    assert verdict.rules_fired == []


def test_one_reader_failing_does_not_lose_the_other(readers, sandbox):
    readers["text"] = RuntimeError("model timeout")
    readers["vision"] = feats(age=52, rectal_bleeding=True, prior_colonoscopy_date=None)

    _, verdict = pipeline.process_referral(b"x", "referral.pdf")

    assert verdict.urgency == "urgent"
    report = json.loads(stored(verdict.referral_id).perception_json)
    outcomes = {r["name"]: r for r in report["readers"]}
    assert outcomes["text_extract"]["ok"] is False
    assert "model timeout" in outcomes["text_extract"]["error"]
    assert outcomes["referral_vision"]["ok"] is True
    assert outcomes["referral_vision"]["latency_ms"] == 42


def test_a_readers_own_low_confidence_still_escalates(readers, sandbox):
    """Corroboration is a ceiling, not a floor — two readers agreeing on an
    illegible field must not manufacture confidence in it."""
    agreed = dict(age=52, rectal_bleeding=True, prior_colonoscopy_date=None)
    readers["text"] = feats(confidence=0.2, **agreed)
    readers["vision"] = feats(confidence=0.95, **agreed)

    _, verdict = pipeline.process_referral(b"x", "referral.pdf")

    assert verdict.disposition == "ESCALATE"


def test_perception_report_reaches_the_api(readers, sandbox):
    from app.main import _worklist_item

    readers["text"] = feats(age=52, rectal_bleeding=False, prior_colonoscopy_date=None)
    readers["vision"] = feats(age=52, rectal_bleeding=True, prior_colonoscopy_date=None)
    _, verdict = pipeline.process_referral(b"x", "referral.pdf")

    session = get_session()
    try:
        item = _worklist_item(session, session.get(ReferralRecord, verdict.referral_id))
    finally:
        session.close()

    json.dumps(item)  # must be serialisable
    assert item["perception"]["has_conflict"] is True
    assert item["perception"]["conflicts"] == ["rectal_bleeding"]


def test_absent_perception_is_null_not_an_empty_report(readers, sandbox):
    """"Not assessed" and "assessed, no conflict" must stay distinguishable."""
    from app.main import _worklist_item

    sandbox["text"] = ""
    sandbox["images"] = []
    _, verdict = pipeline.process_referral(b"x", "empty.pdf")

    session = get_session()
    try:
        item = _worklist_item(session, session.get(ReferralRecord, verdict.referral_id))
    finally:
        session.close()

    assert item["perception"] is None
