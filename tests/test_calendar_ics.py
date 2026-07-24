"""Standalone .ics generation tests. This module is appointment-agnostic and
has no Slack or referral coupling — tests reflect that."""

from __future__ import annotations

from datetime import datetime

import pytest

from services.calendar import Appointment, appointment_from_slot, build_ics


def _appt(**overrides):
    kwargs = dict(
        uid="test-1@meridian.local",
        summary="Follow-up appointment",
        start=datetime(2026, 7, 28, 9, 0, 0),
        end=datetime(2026, 7, 28, 9, 45, 0),
        description="See worklist for details.",
    )
    kwargs.update(overrides)
    return Appointment(**kwargs)


def test_produces_valid_vcalendar_skeleton():
    ics = build_ics(_appt())
    assert ics.startswith("BEGIN:VCALENDAR")
    assert ics.rstrip().endswith("END:VCALENDAR")
    assert "BEGIN:VEVENT" in ics and "END:VEVENT" in ics
    assert "VERSION:2.0" in ics


def test_times_and_uid_render():
    ics = build_ics(_appt())
    assert "DTSTART:20260728T090000" in ics
    assert "DTEND:20260728T094500" in ics
    assert "UID:test-1@meridian.local" in ics


def test_crlf_line_endings():
    """RFC 5545 requires CRLF; calendar apps are strict about this."""
    ics = build_ics(_appt())
    assert "\r\n" in ics
    # No bare LF that isn't preceded by CR.
    assert "\n" not in ics.replace("\r\n", "")


def test_generic_not_hardcoded_to_colonoscopy():
    """The module books ANY appointment type."""
    ics = build_ics(
        _appt(summary="Dermatology consult", appointment_type="derm")
    )
    assert "SUMMARY:Dermatology consult" in ics
    assert "CATEGORIES:derm" in ics


def test_special_characters_are_escaped():
    ics = build_ics(_appt(summary="Consult; room 3, floor 2", description="line1\nline2"))
    assert "SUMMARY:Consult\\; room 3\\, floor 2" in ics
    assert "line1\\nline2" in ics


# --- invariant #2: output filter -------------------------------------------


def test_diagnostic_summary_is_replaced_with_safe_placeholder():
    """A summary containing a condition term must not reach the .ics."""
    ics = build_ics(_appt(summary="Suspected cancer follow-up"))
    assert "cancer" not in ics.lower()
    assert "SUMMARY:Appointment" in ics  # safe fallback


def test_diagnostic_description_is_replaced():
    ics = build_ics(_appt(description="Probable hemorrhoids, don't worry"))
    assert "hemorrhoid" not in ics.lower()
    assert "worry" not in ics.lower()


# --- slot parsing ----------------------------------------------------------


@pytest.mark.parametrize(
    "label,expected",
    [
        ("2026-07-28T09:00", datetime(2026, 7, 28, 9, 0)),
        ("2026-07-28T09:00 urgent clinic", datetime(2026, 7, 28, 9, 0)),
        ("2026-07-28 09:00", datetime(2026, 7, 28, 9, 0)),
        ("booked 2026-07-28T14:30:00 room 3", datetime(2026, 7, 28, 14, 30)),
    ],
)
def test_appointment_from_slot_parses_loose_labels(label, expected):
    appt = appointment_from_slot(uid="u", summary="s", slot_label=label)
    assert appt is not None
    assert appt.start == expected


@pytest.mark.parametrize("label", ["", "next week", "TBD", "urgent clinic"])
def test_appointment_from_slot_returns_none_when_no_time(label):
    assert appointment_from_slot(uid="u", summary="s", slot_label=label) is None


def test_duration_is_applied():
    appt = appointment_from_slot(
        uid="u", summary="s", slot_label="2026-07-28T09:00", duration_minutes=30
    )
    assert appt.end == datetime(2026, 7, 28, 9, 30)
