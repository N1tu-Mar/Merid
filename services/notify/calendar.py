"""Provider-side calendar event for an approved, booked referral.

Why this shape: there is no GCP project for this demo, so we do not call the
Google Calendar API directly. Instead Slack creates the event for us, via a
Workflow Builder workflow using the `google.calendar/create_event` connector
step. That keeps setup entirely inside the Slack UI — no GCP project, no
service account, no domain-wide delegation. Google auth is the workflow
author's, granted once when the connector step is added.

Two transports, in preference order:

1. **Workflow webhook trigger** (`SLACK_WORKFLOW_WEBHOOK_URL`) — we POST
   structured JSON straight at the workflow. This is the real integration:
   fields arrive as typed workflow variables and map onto the connector's
   inputs directly. Preferred whenever it is configured.
2. **Marker message** (`SLACK_WEBHOOK_URL`) — we post a human-readable line
   tagged with EVENT_MARKER to the channel. Useful as a visible fallback when
   no workflow exists yet: the demo still shows the intent to schedule, and a
   channel-message-triggered workflow can pick it up.

Known tradeoff, unchanged by either transport: the event is created by Slack,
so no Google event ID comes back and we cannot record it against the verdict.
The booking is therefore *not* in our audit trail — only the intent to book
is. If that gap matters (it plausibly does for a signed clinical approval),
the upgrade path is a service account calling the Calendar API from here,
which would return an ID we can persist. `build_event()` is deliberately
transport-agnostic so that swap stays a one-file change.

Title policy (invariant #2): event titles carry NO clinical content. A
calendar entry syncs to phones, shows on shared office displays, and appears
in notification previews outside the building. Title is referral ID plus
urgency; everything else lives behind the worklist link.
"""

from __future__ import annotations

import logging
import os

import httpx

from app.output_filter import check_output
from services.notify.slack import meets_threshold

log = logging.getLogger("meridian.notify.calendar")

# Preferred transport: a Workflow Builder webhook trigger that runs the
# Google Calendar connector step.
WORKFLOW_WEBHOOK_URL = os.environ.get("SLACK_WORKFLOW_WEBHOOK_URL")
# Fallback transport: a plain incoming webhook posting a marker message.
WEBHOOK_URL = os.environ.get("SLACK_CALENDAR_WEBHOOK_URL") or os.environ.get(
    "SLACK_WEBHOOK_URL"
)
TIMEOUT_SECONDS = float(os.environ.get("SLACK_TIMEOUT_S", "5"))
WORKLIST_BASE_URL = os.environ.get("WORKLIST_BASE_URL", "http://localhost:3000")
# Default appointment length; the connector needs an end time, not a duration.
DEFAULT_DURATION_MINUTES = int(os.environ.get("CALENDAR_DURATION_MINUTES", "45"))

# Marker the fallback channel-message workflow trigger matches on. Keep it
# stable — changing it means reconfiguring the workflow in the Slack UI.
EVENT_MARKER = "[MERIDIAN-CALENDAR]"


def parse_slot(booked_slot: str) -> tuple[str | None, str | None]:
    """Pull ISO start/end times out of a free-text slot label.

    `booked_slot` is nurse-entered and deliberately loose — e.g.
    "2026-07-28T09:00 urgent clinic". The calendar connector needs real
    timestamps, so we extract the leading ISO datetime and derive an end.

    Returns (start_iso, end_iso), or (None, None) if no datetime is present.
    Callers must treat (None, None) as "not schedulable" rather than guessing
    a time — inventing an appointment slot is exactly the kind of silent
    fabrication this codebase avoids everywhere else.
    """
    import re
    from datetime import datetime, timedelta

    m = re.search(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(:\d{2})?", booked_slot or "")
    if not m:
        return None, None
    try:
        start = datetime.fromisoformat(m.group(0).replace(" ", "T"))
    except ValueError:
        return None, None
    end = start + timedelta(minutes=DEFAULT_DURATION_MINUTES)
    return start.isoformat(), end.isoformat()


def build_event(
    *,
    referral_id: str,
    urgency: str,
    booked_slot: str,
    approved_by: str,
) -> dict:
    """Build the calendar event payload.

    Transport-agnostic on purpose: these are the fields the Google Calendar
    connector (and the Calendar API itself) needs, so swapping the Slack
    transport for a direct API call means changing only how this dict is
    delivered, not how it is built.
    """
    start_iso, end_iso = parse_slot(booked_slot)
    return {
        "title": f"Colonoscopy consult — {referral_id} ({urgency})",
        # Raw nurse-entered label, kept for the human-readable fallback path.
        "slot_label": booked_slot,
        # Machine-usable times for the connector. None when the slot label
        # carried no parseable datetime.
        "start": start_iso,
        "end": end_iso,
        "description": (
            f"Triage approved by {approved_by}. "
            f"Details: {WORKLIST_BASE_URL}/worklist/{referral_id}\n"
            "DEMO — synthetic data. Not for clinical use."
        ),
        "referral_id": referral_id,
        "urgency": urgency,
    }


def create_calendar_event(
    *,
    referral_id: str,
    urgency: str,
    booked_slot: str | None,
    approved_by: str,
) -> dict:
    """Request creation of a provider-side calendar event. Never raises.

    Status values: requested_via_workflow, requested_via_message,
    skipped_below_threshold, skipped_no_slot, skipped_unparseable_slot,
    skipped_no_webhook, blocked_by_output_filter, failed.
    """
    try:
        # Same urgency gate as Slack notification, and for the same reason: a
        # routine screening booking landing on the provider calendar via this
        # path is noise. Shares SLACK_NOTIFY_MIN_URGENCY so the two channels
        # can't drift apart — set it to "routine" to schedule every approval.
        if not meets_threshold(urgency):
            log.info(
                "calendar_skipped_below_threshold",
                extra={"referral_id": referral_id, "urgency": urgency},
            )
            return {"status": "skipped_below_threshold", "urgency": urgency}

        if not booked_slot:
            # No slot means nothing to schedule. Not an error — plenty of
            # approvals record the verdict before a time is chosen.
            log.info("calendar_skipped_no_slot", extra={"referral_id": referral_id})
            return {"status": "skipped_no_slot"}

        if not WORKFLOW_WEBHOOK_URL and not WEBHOOK_URL:
            log.info("calendar_skipped_no_webhook", extra={"referral_id": referral_id})
            return {"status": "skipped_no_webhook"}

        event = build_event(
            referral_id=referral_id,
            urgency=urgency,
            booked_slot=booked_slot,
            approved_by=approved_by,
        )

        # Filter the title and description — these are the strings that leave
        # our access-controlled surface and land on calendars/phones.
        for field in ("title", "description"):
            try:
                result = check_output(event[field])
            except Exception:
                log.exception("calendar_filter_error_fail_closed")
                return {
                    "status": "blocked_by_output_filter",
                    "reasons": [f"filter_error:{field}"],
                }
            if not result.allowed:
                log.warning(
                    "calendar_blocked_by_output_filter",
                    extra={"referral_id": referral_id, "field": field, "reasons": result.reasons},
                )
                return {"status": "blocked_by_output_filter", "reasons": result.reasons}

        # Preferred transport: structured JSON straight at a Workflow Builder
        # webhook trigger, whose variables feed the Google Calendar connector.
        if WORKFLOW_WEBHOOK_URL:
            if not event["start"]:
                # The connector needs a real timestamp. Refuse rather than
                # invent one — a fabricated appointment time is worse than
                # no event, and the Slack notification still went out.
                log.warning(
                    "calendar_skipped_unparseable_slot",
                    extra={"referral_id": referral_id, "slot": booked_slot},
                )
                return {"status": "skipped_unparseable_slot", "slot": booked_slot}

            # Workflow webhook triggers take a flat, string-valued payload.
            payload = {
                "title": event["title"],
                "start": event["start"],
                "end": event["end"],
                "description": event["description"],
                "referral_id": event["referral_id"],
                "urgency": event["urgency"],
            }
            resp = httpx.post(
                WORKFLOW_WEBHOOK_URL, json=payload, timeout=TIMEOUT_SECONDS
            )
            resp.raise_for_status()
            log.info(
                "calendar_event_requested_via_workflow",
                extra={"referral_id": referral_id, "start": event["start"]},
            )
            return {"status": "requested_via_workflow", "event": event}

        # Fallback transport: visible marker message in the channel.
        text = (
            f"{EVENT_MARKER}\n"
            f"*{event['title']}*\n"
            f"• When: {event['start'] or event['slot_label']}\n"
            f"• {event['description'].splitlines()[0]}"
        )
        resp = httpx.post(WEBHOOK_URL, json={"text": text}, timeout=TIMEOUT_SECONDS)
        resp.raise_for_status()
        log.info(
            "calendar_event_requested",
            extra={"referral_id": referral_id, "slot": booked_slot},
        )
        # "requested", never "created": the event is created by the Slack
        # workflow downstream, and we get no confirmation back.
        return {"status": "requested_via_message", "event": event}

    except Exception as e:
        log.exception("calendar_event_failed", extra={"referral_id": referral_id})
        return {"status": "failed", "error": str(e)}
