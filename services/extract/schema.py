"""The extraction contract shared by every perception model.

One schema and one set of rules, used identically by the transcript reader
and the vision reader. That is what makes their outputs comparable enough
for services/extract/reconcile.py to corroborate one against the other — if
each model were asked for a slightly different shape, disagreement would be
ambiguous between "the readers disagree" and "the prompts differed".

The schema handed to Fireworks is generated from ReferralFeatures itself, so
the decoder is constrained to the same model the rule engine consumes. There
is no hand-maintained copy to drift.
"""

from __future__ import annotations

import functools
from typing import Any

from app.schemas import ReferralFeatures


class ExtractionError(Exception):
    """Model output that does not satisfy the contract.
    Callers must treat this as ESCALATE (CLAUDE.md invariant #3)."""


@functools.lru_cache(maxsize=1)
def features_schema() -> dict[str, Any]:
    """JSON Schema for ReferralFeatures, for decode-time constraint.

    Generated, never written by hand: adding a field to the Pydantic model
    automatically extends what the decoder will accept.
    """
    return ReferralFeatures.model_json_schema()


# Shared across readers. Two non-obvious requirements are load-bearing:
#
#   - "not stated" must come back as null, not as a guess. A guessed False on
#     a red flag is the exact failure that launders a patient to routine.
#   - every non-null field must carry a verbatim quote. The PA packet drops
#     any sentence without a source_ref, so an unsourced fact is dead weight
#     downstream anyway.
EXTRACTION_RULES = """Return ONLY a JSON object. Do not write prose.

You report what the source states. You do not diagnose, estimate likelihood,
assess urgency, or infer anything not explicitly present.

For every field you populate:
  - put a verbatim quote of the text it came from in source_refs
  - put your confidence 0.0-1.0 in extraction_confidence

If a fact is not stated, its value is null and it must NOT appear in
source_refs or extraction_confidence. Never guess. "Not mentioned" and
"stated as absent" are different answers: the first is null, the second is
false.

Report negation carefully. A sentence can deny a symptom and then report it
("no, apart from the bleeding") — the reported symptom is present, and the
leading denial does not cancel it.

Never include a diagnosis, condition name, or clinical judgement anywhere in
your output, including inside quotes you copy."""


def to_features(data: dict[str, Any]) -> ReferralFeatures:
    """Validate raw model output into ReferralFeatures.

    Schema-constrained decoding makes malformed output unlikely, not
    impossible — a model can still emit a well-formed object with a value
    the Pydantic model rejects. Validate anyway rather than trust the
    decoder.
    """
    try:
        features = ReferralFeatures.model_validate(data)
    except Exception as e:
        raise ExtractionError(f"output failed schema validation: {e}") from e

    _drop_unsourced_metadata(features)
    return features


def _drop_unsourced_metadata(features: ReferralFeatures) -> None:
    """Strip source_refs/confidence entries for fields that came back null.

    Models sometimes cite a field they then reported as null. Left in place
    those entries make a null field look populated to anything counting
    `len(source_refs)`, and would let an absent fact carry confidence.
    """
    populated = {
        name
        for name, value in features.model_dump(
            exclude={"source_refs", "extraction_confidence"}
        ).items()
        if value is not None
    }
    for mapping in (features.source_refs, features.extraction_confidence):
        for name in [k for k in mapping if k not in populated]:
            del mapping[name]
