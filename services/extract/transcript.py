"""Path B for a voice call: a compact text model reads the transcript.

The deterministic parser (services/intake/parser.py) is path A. It matches
keywords without parsing negation scope, so it inverts on hedged answers:

    "nope, apart from the bleeding"  ->  rectal_bleeding = False, conf 0.9

This module is the second reader. It is NOT a replacement for the parser and
must not become one — services/extract/reconcile.py compares the two, and a
single reader has nothing to be corroborated against.

Model choice: a compact model, deliberately. The hard part of this task is
negation scope over a short closed-form transcript, not reasoning depth, and
the bigger model measured *worse* on verdict preservation in
evals/extraction_ab.py. See services/extract/models.py for the routing table.
"""

from __future__ import annotations

import logging

from app.schemas import ReferralFeatures
from services.extract.client import CallResult, FireworksError, call_json
from services.extract.schema import EXTRACTION_RULES, ExtractionError, features_schema, to_features

log = logging.getLogger("meridian.extract.transcript")

TASK = "transcript_extract"

SYSTEM_PROMPT = f"""You extract structured intake facts from a transcript of a
phone call between a clinic intake line and a patient.

{EXTRACTION_RULES}

Quotes in source_refs must come from what the PATIENT said, not from the
agent's questions. The agent asking "have you noticed any rectal bleeding?"
is not evidence of bleeding."""


def extract_from_transcript(transcript: str) -> tuple[ReferralFeatures, CallResult]:
    """Read a call transcript into features, with the call's provenance.

    Raises ExtractionError on empty input or unusable output, and
    FireworksError on transport failure. Both must be treated as ESCALATE by
    the caller — never as an absence of red flags.
    """
    if not transcript or not transcript.strip():
        raise ExtractionError("empty transcript")

    result = call_json(
        task=TASK,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": transcript},
        ],
        schema=features_schema(),
        schema_name="ReferralFeatures",
    )

    features = to_features(result.data)
    log.info(
        "transcript_extraction_complete",
        extra={
            "model": result.model,
            "latency_ms": result.latency_ms,
            "fields_populated": len(features.source_refs),
        },
    )
    return features, result


def format_transcript(turns: list[tuple[str, str]]) -> str:
    """Render (speaker, text) turns into the flat form the model reads.

    services/intake/call.py already produces turns in this shape, so a live
    call and a replayed one present identically to the extractor.
    """
    return "\n".join(f"{speaker}: {text}" for speaker, text in turns)


__all__ = [
    "TASK",
    "ExtractionError",
    "FireworksError",
    "extract_from_transcript",
    "format_transcript",
]
