"""Runs both readers for a case and hands back one reconciled feature set.

Lives in its own module so the call sites (services/referral/pipeline.py,
services/intake/call.py) stay a few lines each — those are files other
workstreams touch, and a small diff there is worth an extra file here.

Two entry points, one shape. Each pairs two readers that fail differently:

    perceive_document()   OCR text  ->  compact text model
                          page image -> vision model
    perceive_call()       transcript -> keyword parser (deterministic)
                          transcript -> compact text model

The pairing is the point. For a document, the two readers see genuinely
different artefacts: one reads OCR's flattening of the page, the other reads
the page. A ticked checkbox that OCR dropped is exactly the kind of thing
only one of them can see — which shows up as a conflict rather than as
silence.

Degradation is explicit, never silent:

  both readers ran      -> fields corroborated where they agree
  one reader ran        -> everything single-sourced (0.60), still usable
  neither reader ran    -> PerceptionError, which callers turn into ESCALATE

A single reader is not treated as agreement. That distinction is the whole
value of this layer, so it is visible in the output rather than folded away.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from app.schemas import ReferralFeatures
from services.extract.reconcile import ReconciliationResult, reconcile

log = logging.getLogger("meridian.extract.perception")


class PerceptionError(Exception):
    """No reader produced usable features. Callers must ESCALATE."""


@dataclass
class ReaderOutcome:
    """What one reader did, whether or not it worked."""

    name: str
    ok: bool
    model: str | None = None
    latency_ms: int | None = None
    error: str | None = None
    fields_populated: int = 0


@dataclass
class PerceptionResult:
    features: ReferralFeatures
    reconciliation: ReconciliationResult
    readers: list[ReaderOutcome] = field(default_factory=list)

    @property
    def has_conflict(self) -> bool:
        return self.reconciliation.has_conflict

    @property
    def conflicts(self) -> list[str]:
        return self.reconciliation.conflicts

    @property
    def readers_ok(self) -> int:
        return sum(1 for r in self.readers if r.ok)

    @property
    def corroborated(self) -> bool:
        """True only when two readers actually ran. A single reader that
        happened to succeed is not corroboration."""
        return self.readers_ok >= 2

    def report(self) -> dict:
        """Serialisable account of the perception step, for storage and UI.

        This is what lets a nurse see *which models read this case and
        whether they agreed*, rather than being handed a feature table with
        no indication of how contested it was.
        """
        return {
            "corroborated": self.corroborated,
            "has_conflict": self.has_conflict,
            "conflicts": self.conflicts,
            "readers": [
                {
                    "name": r.name,
                    "ok": r.ok,
                    "model": r.model,
                    "latency_ms": r.latency_ms,
                    "error": r.error,
                    "fields_populated": r.fields_populated,
                }
                for r in self.readers
            ],
            "fields": [f.model_dump(mode="json") for f in self.reconciliation.fields],
        }


def perceive_document(
    raw_text: str,
    page_images: list[bytes] | None = None,
) -> PerceptionResult:
    """Read a document with the text model and the vision model.

    `page_images` comes from the Daytona sandbox (SandboxParseResult). When
    it is empty — plain-text document, render failure, no Daytona key — the
    text reader runs alone and every field is single-sourced.
    """
    text_features, text_outcome = _run_text_reader(raw_text)
    vision_features, vision_outcome = _run_vision_reader(page_images or [])

    return _assemble(
        # Ordering matters only for how conflicts are labelled in the report:
        # `deterministic` is the more conservative reader of the pair.
        first=text_features,
        second=vision_features,
        outcomes=[text_outcome, vision_outcome],
    )


def perceive_call(
    parser_features: ReferralFeatures,
    transcript: str,
) -> PerceptionResult:
    """Read a call with the keyword parser and the transcript model.

    `parser_features` is what services/intake/parser.py already produced, so
    the deterministic path is unchanged and still runs first — this adds a
    second reader, it does not replace the first.
    """
    parser_outcome = ReaderOutcome(
        name="keyword_parser",
        ok=True,
        model="deterministic",
        fields_populated=len(parser_features.source_refs),
    )
    model_features, model_outcome = _run_transcript_reader(transcript)

    return _assemble(
        first=parser_features,
        second=model_features,
        outcomes=[parser_outcome, model_outcome],
    )


# ---------------------------------------------------------------------------
# readers
# ---------------------------------------------------------------------------


def _run_text_reader(raw_text: str) -> tuple[ReferralFeatures, ReaderOutcome]:
    """The existing extractor, unchanged — same model choice, same tracing.

    Imported lazily so this module can be used (and tested) without pulling
    in the referral package's dependencies.
    """
    from services.referral.extract import FIREWORKS_MODEL, extract_features

    if not raw_text or not raw_text.strip():
        return ReferralFeatures(), ReaderOutcome(
            name="text_extract", ok=False, error="no document text"
        )
    try:
        features = extract_features(raw_text)
    except Exception as e:
        log.warning("text_reader_failed", extra={"error": str(e)})
        return ReferralFeatures(), ReaderOutcome(
            name="text_extract", ok=False, model=FIREWORKS_MODEL, error=str(e)
        )
    return features, ReaderOutcome(
        name="text_extract",
        ok=True,
        model=FIREWORKS_MODEL,
        fields_populated=len(features.source_refs),
    )


def _run_vision_reader(page_images: list[bytes]) -> tuple[ReferralFeatures, ReaderOutcome]:
    from services.extract.vision import TASK, extract_from_images

    if not page_images:
        return ReferralFeatures(), ReaderOutcome(
            name="referral_vision", ok=False, error="no page images"
        )
    try:
        features, call = extract_from_images(page_images)
    except Exception as e:
        log.warning("vision_reader_failed", extra={"error": str(e)})
        return ReferralFeatures(), ReaderOutcome(
            name=TASK, ok=False, error=str(e)
        )
    return features, ReaderOutcome(
        name=TASK,
        ok=True,
        model=call.model,
        latency_ms=call.latency_ms,
        fields_populated=len(features.source_refs),
    )


def _run_transcript_reader(transcript: str) -> tuple[ReferralFeatures, ReaderOutcome]:
    from services.extract.transcript import TASK, extract_from_transcript

    if not transcript or not transcript.strip():
        return ReferralFeatures(), ReaderOutcome(
            name=TASK, ok=False, error="no transcript"
        )
    try:
        features, call = extract_from_transcript(transcript)
    except Exception as e:
        log.warning("transcript_reader_failed", extra={"error": str(e)})
        return ReferralFeatures(), ReaderOutcome(name=TASK, ok=False, error=str(e))
    return features, ReaderOutcome(
        name=TASK,
        ok=True,
        model=call.model,
        latency_ms=call.latency_ms,
        fields_populated=len(features.source_refs),
    )


# ---------------------------------------------------------------------------


def _assemble(
    first: ReferralFeatures,
    second: ReferralFeatures,
    outcomes: list[ReaderOutcome],
) -> PerceptionResult:
    if not any(o.ok for o in outcomes):
        reasons = "; ".join(f"{o.name}: {o.error}" for o in outcomes)
        raise PerceptionError(f"no reader produced features ({reasons})")

    result = reconcile(deterministic=first, model=second)

    log.info(
        "perception_complete",
        extra={
            "readers_ok": sum(1 for o in outcomes if o.ok),
            "conflicts": result.conflicts,
            "models": [o.model for o in outcomes if o.ok],
        },
    )
    return PerceptionResult(
        features=result.features, reconciliation=result, readers=outcomes
    )
