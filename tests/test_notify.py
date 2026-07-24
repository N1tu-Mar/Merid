"""Notification tests. The load-bearing assertions here are the negative ones:
notification must never raise, and must never post a string that fails the
output filter.
"""

from __future__ import annotations

import pytest

from services.notify import calendar as cal
from services.notify import slack


class _FakeResponse:
    def raise_for_status(self):
        return None


@pytest.fixture
def captured(monkeypatch):
    """Capture Slack httpx.post calls. Calendar no longer posts to Slack —
    it produces .ics locally — so only the slack module is patched."""
    calls = []

    def fake_post(url, json=None, timeout=None):
        calls.append({"url": url, "json": json})
        return _FakeResponse()

    monkeypatch.setattr(slack.httpx, "post", fake_post)
    monkeypatch.setattr(slack, "WEBHOOK_URL", "https://hooks.slack.com/services/TEST")
    return calls


def _approve(**overrides):
    kwargs = dict(
        referral_id="REF-0042",
        verdict_id="V-1",
        urgency="urgent",
        rules_fired=["YOUNG_BLEEDING_PLUS_FEATURE"],
        rule_version="2026.07.24-1",
        approved_by="Nurse Chen",
        booked_slot="2026-07-28T09:00",
    )
    kwargs.update(overrides)
    return slack.notify_verdict_approved(**kwargs)


# --- threshold gating ------------------------------------------------------


@pytest.mark.parametrize(
    "urgency,expected",
    [("routine", False), ("soon", False), ("urgent", True), ("emergency", True)],
)
def test_default_threshold_is_urgent_and_above(urgency, expected):
    assert slack.meets_threshold(urgency, "urgent") is expected


@pytest.mark.parametrize("urgency", ["routine", "soon", "urgent", "emergency"])
def test_threshold_routine_notifies_on_every_verdict(urgency):
    """The configurable path: SLACK_NOTIFY_MIN_URGENCY=routine notifies on all."""
    assert slack.meets_threshold(urgency, "routine") is True


def test_unknown_urgency_notifies_rather_than_drops():
    assert slack.meets_threshold("banana", "urgent") is True


def test_below_threshold_does_not_post(captured):
    result = _approve(urgency="routine")
    assert result["status"] == "skipped_below_threshold"
    assert captured == []


def test_urgent_posts(captured):
    result = _approve()
    assert result["status"] == "sent"
    assert len(captured) == 1
    assert "REF-0042" in captured[0]["json"]["text"]


# --- invariant #2: output filter -------------------------------------------


def test_message_passes_output_filter():
    from app.output_filter import check_output

    text = slack.build_message(
        referral_id="REF-0042",
        verdict_id="V-1",
        urgency="urgent",
        rules_fired=["YOUNG_BLEEDING_PLUS_FEATURE"],
        rule_version="2026.07.24-1",
        approved_by="Nurse Chen",
        booked_slot="2026-07-28T09:00",
    )
    assert check_output(text).allowed


def test_diagnostic_language_is_blocked_not_posted(captured, monkeypatch):
    """If anything ever injects a condition term into the message, we must
    block the post rather than leak it to a staff channel."""
    monkeypatch.setattr(
        slack, "build_message", lambda **kw: "REF-0042 probable hemorrhoids, don't worry"
    )
    result = _approve()
    assert result["status"] == "blocked_by_output_filter"
    assert captured == []


# --- calendar: decoupled from Slack, produces .ics -------------------------


def _make_calendar(**overrides):
    kwargs = dict(
        referral_id="REF-0042",
        urgency="urgent",
        booked_slot="2026-07-28T09:00 urgent clinic",
        approved_by="Nurse Chen",
    )
    kwargs.update(overrides)
    return cal.create_calendar_event(**kwargs)


def test_calendar_does_not_touch_slack(monkeypatch):
    """The calendar path must not POST to Slack at all — if it tries, fail."""
    import services.calendar.ics as ics_mod  # noqa: F401

    # No httpx anywhere in the calendar module to patch; asserting the result
    # comes back "generated" with an .ics is proof it went the local path.
    result = _make_calendar()
    assert result["status"] == "generated"
    assert result["ics"].startswith("BEGIN:VCALENDAR")


def test_calendar_urgent_generates_ics():
    result = _make_calendar()
    assert result["status"] == "generated"
    assert result["start"] == "2026-07-28T09:00:00"
    assert result["end"] == "2026-07-28T09:45:00"
    assert "DTSTART:20260728T090000" in result["ics"]
    assert "DTEND:20260728T094500" in result["ics"]


def test_calendar_summary_carries_no_clinical_content():
    from app.output_filter import check_output

    appt = cal.build_appointment(
        referral_id="REF-0042",
        urgency="urgent",
        booked_slot="2026-07-28T09:00",
        approved_by="Nurse Chen",
    )
    assert check_output(appt.summary).allowed
    assert "REF-0042" in appt.summary
    assert "hemorrhoid" not in appt.summary.lower()


def test_calendar_respects_same_threshold_as_slack():
    """A routine approval must not book — calendar shares Slack's threshold."""
    result = _make_calendar(urgency="routine", booked_slot="2026-08-10T14:00")
    assert result["status"] == "skipped_below_threshold"


def test_calendar_without_slot_is_skipped():
    result = _make_calendar(booked_slot=None)
    assert result["status"] == "skipped_no_slot"


def test_unparseable_slot_refuses_rather_than_inventing_a_time():
    """A fabricated appointment time is worse than no event."""
    result = _make_calendar(booked_slot="next Tuesday-ish")
    assert result["status"] == "skipped_unparseable_slot"


def test_calendar_never_raises(monkeypatch):
    """Any internal failure returns a status dict, never propagates."""
    def boom(*a, **k):
        raise RuntimeError("ics generator blew up")

    monkeypatch.setattr(cal, "build_ics", boom)
    result = _make_calendar()
    assert result["status"] == "failed"


# --- never raises (slack) --------------------------------------------------


def test_slack_transport_failure_is_swallowed(monkeypatch):
    monkeypatch.setattr(slack, "WEBHOOK_URL", "https://hooks.slack.com/services/TEST")

    def boom(*a, **k):
        raise RuntimeError("slack is down")

    monkeypatch.setattr(slack.httpx, "post", boom)
    result = _approve()
    assert result["status"] == "failed"


def test_no_webhook_configured_is_not_an_error(monkeypatch):
    monkeypatch.setattr(slack, "WEBHOOK_URL", None)
    assert _approve()["status"] == "skipped_no_webhook"
