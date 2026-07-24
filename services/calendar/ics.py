"""iCalendar (.ics) generation for any appointment the system books.

Why .ics rather than the Google Calendar API: it needs no GCP project, no
service account, no OAuth — it is a plain text file that every calendar app
(Google, Apple, Outlook) imports. That makes it the right zero-setup default,
and the Google Calendar API stays a clean drop-in upgrade later (same
Appointment in, an event ID back).

Scope: this module is appointment-type-agnostic. A colonoscopy consult is just
one caller. It knows nothing about referrals, triage, or Slack — callers pass a
plain Appointment.

Invariant #2 still applies: an appointment summary/description lands on a
provider's phone and shared displays, so both fields are run through the
no-diagnosis output filter, fail-closed. A field that fails the filter is
dropped to a safe placeholder rather than leaked.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from app.output_filter import check_output

log = logging.getLogger("meridian.calendar.ics")

# RFC 5545 line-folding limit is 75 octets; kept simple for ASCII demo data.
_SAFE_SUMMARY_FALLBACK = "Appointment"
_SAFE_DESCRIPTION_FALLBACK = "Details available in the Meridian worklist."


@dataclass
class Appointment:
    """A generic booking. No clinical or referral coupling.

    `uid` must be stable for a given logical appointment so re-importing the
    .ics updates the same calendar entry instead of creating a duplicate.
    """

    uid: str
    summary: str
    start: datetime
    end: datetime
    description: str = ""
    location: str = ""
    # Free-form; lets a caller label what kind of appointment this is without
    # this module needing to know the taxonomy.
    appointment_type: str = "appointment"
    attendees: list[str] = field(default_factory=list)


def appointment_from_slot(
    *,
    uid: str,
    summary: str,
    slot_label: str,
    duration_minutes: int = 45,
    description: str = "",
    location: str = "",
    appointment_type: str = "appointment",
) -> Appointment | None:
    """Build an Appointment from a loose, human-entered slot label.

    `slot_label` is deliberately loose — e.g. "2026-07-28T09:00 urgent clinic".
    Returns None if no datetime can be parsed: callers must treat that as "not
    schedulable" rather than invent a time (no silent fabrication).
    """
    import re

    m = re.search(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(:\d{2})?", slot_label or "")
    if not m:
        return None
    try:
        start = datetime.fromisoformat(m.group(0).replace(" ", "T"))
    except ValueError:
        return None
    return Appointment(
        uid=uid,
        summary=summary,
        start=start,
        end=start + timedelta(minutes=duration_minutes),
        description=description,
        location=location,
        appointment_type=appointment_type,
    )


def _safe(text: str, fallback: str) -> str:
    """Run text through the no-diagnosis filter, fail-closed to a placeholder."""
    try:
        if check_output(text).allowed:
            return text
    except Exception:
        log.exception("ics_filter_error_fail_closed")
    log.warning("ics_field_replaced_by_safe_fallback")
    return fallback


def _escape(text: str) -> str:
    """RFC 5545 text escaping: backslash, comma, semicolon, newline."""
    return (
        text.replace("\\", "\\\\")
        .replace(",", "\\,")
        .replace(";", "\\;")
        .replace("\n", "\\n")
    )


def _fmt(dt: datetime) -> str:
    """Floating local time per RFC 5545 (no trailing Z, no TZID) — matches the
    naive datetimes we parse from slot labels."""
    return dt.strftime("%Y%m%dT%H%M%S")


def build_ics(appt: Appointment, *, prodid: str = "-//Meridian//Booking//EN") -> str:
    """Render an Appointment as a single-event VCALENDAR string.

    Summary and description are output-filtered (invariant #2). Times are
    written as floating local time to match parsed slot labels.
    """
    summary = _safe(appt.summary, _SAFE_SUMMARY_FALLBACK)
    description = _safe(appt.description, _SAFE_DESCRIPTION_FALLBACK) if appt.description else ""

    # DTSTAMP must be deterministic (no Date.now-style call) so the same
    # appointment renders byte-identical and re-imports cleanly. Anchor it to
    # the event start rather than "now".
    dtstamp = _fmt(appt.start)

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:{prodid}",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "BEGIN:VEVENT",
        f"UID:{_escape(appt.uid)}",
        f"DTSTAMP:{dtstamp}",
        f"DTSTART:{_fmt(appt.start)}",
        f"DTEND:{_fmt(appt.end)}",
        f"SUMMARY:{_escape(summary)}",
    ]
    if description:
        lines.append(f"DESCRIPTION:{_escape(description)}")
    if appt.location:
        lines.append(f"LOCATION:{_escape(_safe(appt.location, ''))}")
    if appt.appointment_type:
        lines.append(f"CATEGORIES:{_escape(appt.appointment_type)}")
    for email in appt.attendees:
        lines.append(f"ATTENDEE:mailto:{_escape(email)}")
    lines += ["END:VEVENT", "END:VCALENDAR"]

    # RFC 5545 requires CRLF line endings.
    return "\r\n".join(lines) + "\r\n"
