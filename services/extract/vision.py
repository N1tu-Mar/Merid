"""A vision model reads the referral page itself, not an OCR transcription.

Why this is a different model class and not a prompt change: a faxed referral
is a page image. The clinically load-bearing content is often *not* flowing
text —

  - which symptom checkbox is ticked
  - handwriting in the margin ("probable hemorrhoids, reassured pt")
  - which value sits under which field label
  - an insurance card photocopied into a corner

OCR-to-text flattens all of that. A dropped checkbox is a dropped red flag,
which is the same silent-suppression failure as the intake parser's negation
bug — just in a different modality.

Boundary with Daytona: the sandbox still owns turning untrusted bytes into
page images. Decoding a hostile PDF is the RCE-prone step and stays isolated
(services/referral/sandbox.py). This module takes bytes that are already
images and never touches a parser. Handing the sandbox's output to a model
does not weaken that boundary — it means the sandbox no longer has to run an
OCR toolchain at all.

Documents may be multi-page and a case may carry several (a referral plus
whatever medical history a patient uploaded). All pages go in one request so
the model can resolve facts across them; they are numbered so source_refs
can say which page a quote came from.
"""

from __future__ import annotations

import logging

from app.schemas import ReferralFeatures
from services.extract.client import CallResult, FireworksError, call_json, image_part
from services.extract.schema import EXTRACTION_RULES, ExtractionError, features_schema, to_features

log = logging.getLogger("meridian.extract.vision")

TASK = "referral_vision"

# A page image costs more tokens and more time than a transcript; one number
# for both would be wrong for one of them.
VISION_TIMEOUT_S = 90.0

# Guard against a caller handing over a 200-page upload: the request would
# time out and fail closed, which is safe but wastes the attempt. Fail fast
# and let a human triage the document set instead.
MAX_PAGES = 12

SYSTEM_PROMPT = f"""You read scanned clinical documents — referral faxes,
discharge summaries, lab reports, and photographs of paperwork.

{EXTRACTION_RULES}

These are page images, so read the page as a page:
  - a ticked checkbox states the thing next to it; an empty one states its
    absence. Say which you saw.
  - read handwriting, including margin notes and annotations
  - keep values attached to the field label they sit under
  - if a page is illegible or cut off, leave the affected fields null rather
    than reconstructing what it probably said

In source_refs, prefix each quote with its page, e.g.
"page 2: 'bright red blood PR x3 weeks'" or
"page 1: checkbox ticked - Rectal bleeding"."""


def extract_from_images(
    images: list[bytes],
    mime: str = "image/png",
    context: str | None = None,
) -> tuple[ReferralFeatures, CallResult]:
    """Read page images into features, with the call's provenance.

    `context` is optional non-authoritative framing (e.g. "patient-uploaded
    medical history"). It is never treated as a source of facts — anything
    reported still has to be quotable from a page.

    Raises ExtractionError on empty/oversized input or unusable output, and
    FireworksError on transport failure. Both mean ESCALATE.
    """
    if not images:
        raise ExtractionError("no page images supplied")
    if len(images) > MAX_PAGES:
        raise ExtractionError(
            f"{len(images)} pages exceeds MAX_PAGES={MAX_PAGES}; route to human review"
        )
    if any(not page for page in images):
        raise ExtractionError("one or more page images are empty")

    parts: list[dict] = []
    if context:
        parts.append({"type": "text", "text": f"Document context: {context}"})
    parts.append(
        {
            "type": "text",
            "text": f"{len(images)} page image(s) follow, in order starting at page 1.",
        }
    )
    parts.extend(image_part(page, mime=mime) for page in images)

    result = call_json(
        task=TASK,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": parts},
        ],
        schema=features_schema(),
        schema_name="ReferralFeatures",
        timeout_s=VISION_TIMEOUT_S,
    )

    features = to_features(result.data)
    log.info(
        "vision_extraction_complete",
        extra={
            "model": result.model,
            "latency_ms": result.latency_ms,
            "pages": len(images),
            "fields_populated": len(features.source_refs),
        },
    )
    return features, result


__all__ = [
    "MAX_PAGES",
    "TASK",
    "ExtractionError",
    "FireworksError",
    "extract_from_images",
]
