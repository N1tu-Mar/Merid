"""Booking helper for an approved, booked referral — now decoupled from Slack.

History: this module used to POST at a Slack Workflow Builder trigger to have
Slack's Google Calendar connector create the event. That path is a dead end —
the connector refuses to run from a webhook trigger (it requires a human
button/link start), so it could never be fully automated. Calendar generation
now lives in the standalone, Slack-independent `services.calendar` module,
which produces a portable .ics for ANY appointment type.

What remains here is the thin triage-specific adapter: turn a verdict +
booking slot into a generic Appointment, and hand back the .ics. It still
enforces the urgency threshold (shared with Slack notification) and the
no-diagnosis output filter (inside the .ics builder).

Upgrade path unchanged: swap the .ics builder for a Google Calendar API call
(service account) and you get a real event ID back for the audit trail. The
Appointment abstraction makes that a one-call change.
"""

from __future__ import annotations

import logging
import os

from services.calendar import Appointment, appointment_from_slot, build_ics
from services.notify.slack import meets_threshold

log = logging.getLogger("meridian.notify.calendar")

WORKLIST_BASE_URL = os.environ.get("WORKLIST_BASE_URL", "http://localhost:3000")
DEFAULT_DURATION_MINUTES = int(os.environ.get("CALENDAR_DURATION_MINUTES", "45"))


def build_appointment(
    *,
    referral_id: str,
    urgency: str,
    booked_slot: str,
    approved_by: str,
) -> Appointment | None:
    """Turn a triage booking into a generic Appointment, or None if the slot
    has no parseable time.

    Title policy (invariant #2): the summary carries NO clinical content — a
    calendar entry syncs to phones and shared displays. Referral ID + urgency
    only; detail lives behind the worklist link.
    """
    return appointment_from_slot(
        uid=f"meridian-{referral_id}@meridian.local",
        summary=f"Colonoscopy consult — {referral_id} ({urgency})",
        slot_label=booked_slot,
        duration_minutes=DEFAULT_DURATION_MINUTES,
        description=(
            f"Triage approved by {approved_by}. "
            f"Details: {WORKLIST_BASE_URL}/worklist/{referral_id}\n"
            "DEMO — synthetic data. Not for clinical use."
        ),
        appointment_type="gi-consult",
    )


def create_calendar_event(
    *,
    referral_id: str,
    urgency: str,
    booked_slot: str | None,
    approved_by: str,
) -> dict:
    """Produce a calendar booking (.ics) for an approved verdict. Never raises.

    Returns a status dict. When an .ics is produced, it is included under
    "ics" so the caller can offer it for download; the event itself is created
    when a human opens that file in their calendar app.

    Status values: generated, skipped_below_threshold, skipped_no_slot,
    skipped_unparseable_slot, failed.
    """
    try:
        # Shares SLACK_NOTIFY_MIN_URGENCY with Slack notification so the two
        # can't drift: set it to "routine" to book every approval.
        if not meets_threshold(urgency):
            log.info(
                "calendar_skipped_below_threshold",
                extra={"referral_id": referral_id, "urgency": urgency},
            )
            return {"status": "skipped_below_threshold", "urgency": urgency}

        if not booked_slot:
            log.info("calendar_skipped_no_slot", extra={"referral_id": referral_id})
            return {"status": "skipped_no_slot"}

        appt = build_appointment(
            referral_id=referral_id,
            urgency=urgency,
            booked_slot=booked_slot,
            approved_by=approved_by,
        )
        if appt is None:
            # No parseable time — refuse rather than invent one.
            log.warning(
                "calendar_skipped_unparseable_slot",
                extra={"referral_id": referral_id, "slot": booked_slot},
            )
            return {"status": "skipped_unparseable_slot", "slot": booked_slot}

        ics = build_ics(appt)
        log.info(
            "calendar_ics_generated",
            extra={"referral_id": referral_id, "start": appt.start.isoformat()},
        )
        return {
            "status": "generated",
            "ics": ics,
            "start": appt.start.isoformat(),
            "end": appt.end.isoformat(),
            "summary": appt.summary,
        }

    except Exception as e:
        log.exception("calendar_event_failed", extra={"referral_id": referral_id})
        return {"status": "failed", "error": str(e)}
