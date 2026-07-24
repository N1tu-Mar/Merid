"""End-to-end referral pipeline (build order step 3):

  bytes -> [Daytona sandbox: decode/OCR] -> plain text
        -> [Fireworks LLM: structured extraction] -> ReferralFeatures
        -> [app.rule_engine: deterministic rules] -> TriageVerdict
        -> persisted, ready for the nurse worklist

Every failure mode here (sandbox error, extraction error, unhandled
exception) is caught and converted into an ESCALATE verdict rather than
propagating — this is the fail-safe-defaults invariant applied at the
service boundary, on top of what app.rule_engine already guarantees for
rule evaluation itself.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from uuid import uuid4

from app.db import ReferralRecord, TriageVerdictRecord, get_session
from app.rule_engine import evaluate, load_rules
from app.schemas import ReferralFeatures, TriageVerdict
from app.tracing import log_span, traced
from services.extract.perception import PerceptionError, perceive_document
from services.referral.extract import ExtractionError
from services.referral.sandbox import SandboxError, parse_document_in_sandbox

log = logging.getLogger("meridian.referral.pipeline")


def _escalate_verdict(referral_id: str, reason: str) -> TriageVerdict:
    log.warning("referral_pipeline_escalated", extra={"referral_id": referral_id, "reason": reason})
    log_span(metadata={"escalate_reason": reason})
    return TriageVerdict(
        referral_id=referral_id,
        urgency="routine",
        disposition="ESCALATE",
        rules_fired=[],
        rule_version=load_rules().get("version", "unknown"),
        missing_features=[],
        created_at=datetime.now(timezone.utc),
    )


@traced
def process_referral(
    content: bytes,
    filename: str,
    patient_name: str = "",
    source: str = "fax_scan",
) -> tuple[ReferralRecord, TriageVerdict]:
    """Runs the full pipeline and persists the referral + verdict.

    Never raises: any failure anywhere in the pipeline results in a
    persisted ESCALATE verdict, because a human must always be able to find
    this referral on the worklist even when automation broke.

    Traced end-to-end in Braintrust when configured: the root span carries
    the verdict, with nested spans for sandbox parse, extraction, and rule
    evaluation — every production decision is replayable.
    """
    referral_id = str(uuid4())
    log_span(input={"doc_filename": filename, "bytes": len(content), "source": source})

    # No sandbox provenance yet: if parsing fails before a box runs, these stay
    # empty and no sandbox badge shows for the resulting ESCALATE item.
    sb: dict = {"sandbox_id": None, "sandbox_ms": None, "sandboxed": False, "sandbox_source": None}

    try:
        parse = parse_document_in_sandbox(content, filename)
    except SandboxError as e:
        return _persist(referral_id, source, "", patient_name, ReferralFeatures(), _escalate_verdict(referral_id, f"sandbox_error: {e}"), **sb)
    except Exception as e:
        log.exception("unexpected_sandbox_failure")
        return _persist(referral_id, source, "", patient_name, ReferralFeatures(), _escalate_verdict(referral_id, f"unexpected_sandbox_failure: {e}"), **sb)

    raw_text = parse.text
    sb = {
        "sandbox_id": parse.sandbox_id,
        "sandbox_ms": parse.duration_ms,
        "sandboxed": parse.sandboxed,
        "sandbox_source": parse.sandbox_source,
    }

    # A scanned fax can be a pure page image with no extractable text at all.
    # That used to be unparseable; the vision reader can read it, so only a
    # document with neither text nor pages is genuinely nothing to work with.
    if not raw_text.strip() and not parse.page_images:
        return _persist(referral_id, source, raw_text, patient_name, ReferralFeatures(), _escalate_verdict(referral_id, "document_unparseable_empty_text"), **sb)

    try:
        perception = perceive_document(raw_text, parse.page_images, source=source)
    except (PerceptionError, ExtractionError) as e:
        return _persist(referral_id, source, raw_text, patient_name, ReferralFeatures(), _escalate_verdict(referral_id, f"extraction_error: {e}"), **sb)
    except Exception as e:
        log.exception("unexpected_extraction_failure")
        return _persist(referral_id, source, raw_text, patient_name, ReferralFeatures(), _escalate_verdict(referral_id, f"unexpected_extraction_failure: {e}"), **sb)

    features = perception.features
    sb["perception"] = perception.report()

    # A conflicted field is deliberately scored below the threshold, but it
    # is handled after rule evaluation so the verdict keeps its urgency and
    # rules_fired. Excluded here so this gate — which produces a bare
    # ESCALATE with neither — cannot pre-empt the better answer.
    if any(
        value < LOW_CONFIDENCE_THRESHOLD
        for name, value in features.extraction_confidence.items()
        if name not in perception.conflicts
    ):
        return _persist(referral_id, source, raw_text, patient_name, features, _escalate_verdict(referral_id, "low_extraction_confidence"), **sb)

    try:
        verdict = evaluate(features, referral_id=referral_id)
    except Exception as e:
        log.exception("unexpected_rule_engine_failure")
        return _persist(referral_id, source, raw_text, patient_name, features, _escalate_verdict(referral_id, f"unexpected_rule_engine_failure: {e}"), **sb)

    if perception.has_conflict:
        # Keep the computed urgency — it was resolved toward the more urgent
        # reading, so it is correct — but never book on a disputed fact. The
        # nurse gets the right priority AND is told what the readers disagreed
        # about, which a bare ESCALATE would have thrown away.
        log.warning(
            "perception_conflict_forcing_escalate",
            extra={"referral_id": referral_id, "conflicts": perception.conflicts},
        )
        verdict = verdict.model_copy(update={"disposition": "ESCALATE"})

    log_span(
        output={"urgency": verdict.urgency, "disposition": verdict.disposition},
        metadata={
            "rules_fired": verdict.rules_fired,
            "rule_version": verdict.rule_version,
            "readers_ok": perception.readers_ok,
            "corroborated": perception.corroborated,
            "conflicts": perception.conflicts,
            **{k: v for k, v in sb.items() if k != "perception"},
        },
    )
    return _persist(referral_id, source, raw_text, patient_name, features, verdict, **sb)


LOW_CONFIDENCE_THRESHOLD = 0.5


def _persist(
    referral_id: str,
    source: str,
    raw_text: str,
    patient_name: str,
    features: ReferralFeatures,
    verdict: TriageVerdict,
    sandbox_id: str | None = None,
    sandbox_ms: int | None = None,
    sandboxed: bool = False,
    sandbox_source: str | None = None,
    perception: dict | None = None,
) -> tuple[ReferralRecord, TriageVerdict]:
    session = get_session()
    try:
        record = ReferralRecord(
            id=referral_id,
            source=source,
            raw_text=raw_text,
            patient_name=patient_name,
            features_json=features.model_dump_json(),
            sandbox_id=sandbox_id,
            sandbox_ms=sandbox_ms,
            sandboxed=sandboxed,
            sandbox_source=sandbox_source,
            # Which models read this case and whether they agreed. Null on
            # the failure paths that escalate before perception runs.
            perception_json=json.dumps(perception) if perception else None,
        )
        session.add(record)
        session.add(
            TriageVerdictRecord(
                id=verdict.id,
                referral_id=verdict.referral_id,
                urgency=verdict.urgency,
                disposition=verdict.disposition,
                rules_fired=verdict.rules_fired,
                rule_version=verdict.rule_version,
                missing_features=verdict.missing_features,
                created_at=verdict.created_at,
            )
        )
        session.commit()
        return record, verdict
    finally:
        session.close()
