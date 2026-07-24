"""Standalone calendar service — generates .ics for any appointment.

Deliberately decoupled from Slack and from the referral pipeline: it takes a
generic appointment and returns a calendar file. Any caller (triage approval,
voice intake booking, a future scheduling UI) can use it.
"""

from services.calendar.ics import Appointment, build_ics, appointment_from_slot

__all__ = ["Appointment", "build_ics", "appointment_from_slot"]
