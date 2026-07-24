"""Corroboration reconciler: two independent readings -> one feature set.

The system extracts clinical facts twice, by mechanisms that fail
differently:

  path A (deterministic)  services/intake/parser.py reads the call transcript
                          with closed-form keyword matching
  path B (model)          services/extract/multimodal.py reads the same
                          transcript *plus* any uploaded documents

This module merges them. It is pure: no I/O, no network, no database, no
model call. Given the same two inputs it always returns the same output,
which is what lets it sit on the triage path at all.

Why it exists
-------------
The deterministic parser scans for keywords without parsing negation scope,
so a hedged answer silently inverts:

    "nope, apart from the bleeding"  ->  rectal_bleeding = False, conf 0.9

Alone, that launders a 52-year-old from urgent to routine *and still books
them*, because SCREENING_AGE_NO_PRIOR fires and supplies a plausible audit
trail. The failure is invisible, not loud.

The fix is not to let a model decide the value. It is to have a second
reader, and to treat their disagreement as the finding.

Two things happen on a conflict, and both matter:

  1. The value resolves toward whichever reading the *rule engine* treats as
     more urgent — so the resulting urgency is correct, not merely flagged.
     "More urgent" is never hardcoded per field; it is measured by running
     app.rule_engine over the candidates. When the rules change, this
     follows automatically, and fields with no safe direction (age cuts both
     ways: BLEEDING_OVER_50 vs YOUNG_BLEEDING_PLUS_FEATURE) need no special
     case.

  2. The conflict is reported, so a human is told which fact was disputed
     and what each reader saw.

Confidence is *derived* here, never accepted from an extractor. A model's
self-reported confidence is not calibrated, and the parser's was a constant.
What carries information is whether two independent readers agreed.

Boundary
--------
This module does not produce a verdict and does not set a disposition.
Callers run app.rule_engine on `result.features` as usual, and should force
the disposition to ESCALATE when `result.has_conflict` — keeping the
computed urgency, which is the point of step 1 above.
"""

from __future__ import annotations

import itertools
import logging
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.rule_engine import _evaluate_unsafe, load_rules
from app.schemas import URGENCY_ORDER, ReferralFeatures

log = logging.getLogger("meridian.extract.reconcile")

CorroborationState = Literal["corroborated", "single_sourced", "conflict", "absent"]

# The clinical fields. Provenance fields are metadata about the extraction,
# not facts to reconcile.
_METADATA_FIELDS = {"source_refs", "extraction_confidence"}
CLINICAL_FIELDS: tuple[str, ...] = tuple(
    f for f in ReferralFeatures.model_fields if f not in _METADATA_FIELDS
)

# Confidence as a function of corroboration, not of anything a model claimed.
# `conflict` sits deliberately below the 0.5 threshold that existing callers
# (services/referral/pipeline.py, services/intake/call.py) already treat as
# escalate-worthy, so a disputed fact trips the machinery that is already
# there rather than needing a parallel one.
CONFIDENCE_BY_STATE: dict[str, float] = {
    "corroborated": 0.95,
    "single_sourced": 0.60,
    "conflict": 0.30,
    "absent": 0.0,
}


def _confidence_for(state: CorroborationState, reported: list[float]) -> float:
    """Corroboration sets a *ceiling*, never a floor.

    Two readers agreeing does not make an illegible checkbox legible. If a
    reader said it was only 0.3 sure of what it saw, agreement raises the
    odds both read the same mark — not the odds the mark was clear. So a
    field ends up at most as trustworthy as its shakiest reading, and at
    most what corroboration warrants.

    Without this, reconciliation would *overwrite* a low-confidence signal
    from an extractor with 0.95 and silently disarm the escalation gate that
    services/referral/pipeline.py and services/intake/call.py already run.
    """
    ceiling = CONFIDENCE_BY_STATE[state]
    return min([ceiling, *reported]) if reported else ceiling

# Above this many simultaneously disputed fields, resolving jointly costs
# 2^n rule-engine passes. Practically unreachable (there are 12 fields, and
# a case where 10 of them are disputed is not a triage problem, it is a
# broken pipeline), but bounded rather than left to blow up.
MAX_JOINT_CONFLICT_FIELDS = 10


class FieldReconciliation(BaseModel):
    """How one clinical field was settled, and on what evidence."""

    field: str
    value: Any = None
    state: CorroborationState
    deterministic_value: Any = None
    model_value: Any = None
    confidence: float = 0.0
    source_refs: list[str] = Field(default_factory=list)


class ReconciliationResult(BaseModel):
    """Merged features plus a per-field account of how they were settled.

    `features` is what goes to the rule engine. `fields` is what goes to the
    nurse — it is the difference between "urgent" and "urgent, and here is
    the fact the two readers disagreed about".
    """

    features: ReferralFeatures
    fields: list[FieldReconciliation]
    conflicts: list[str] = Field(default_factory=list)
    has_conflict: bool = False

    def by_field(self, name: str) -> FieldReconciliation:
        for f in self.fields:
            if f.field == name:
                return f
        raise KeyError(f"unknown clinical field: {name!r}")


def reconcile(
    deterministic: ReferralFeatures,
    model: ReferralFeatures,
) -> ReconciliationResult:
    """Merge two independent readings of the same case.

    `deterministic` is the keyword parser's reading (transcript only).
    `model` is the multimodal extractor's reading (transcript + documents).
    Neither is trusted over the other; where they disagree the rule engine
    decides which reading is more urgent.
    """
    det_values = deterministic.model_dump(exclude=_METADATA_FIELDS)
    mod_values = model.model_dump(exclude=_METADATA_FIELDS)

    settled: dict[str, Any] = {}
    states: dict[str, CorroborationState] = {}
    conflicts: dict[str, tuple[Any, Any]] = {}

    for name in CLINICAL_FIELDS:
        a, b = det_values.get(name), mod_values.get(name)

        if a is None and b is None:
            states[name] = "absent"
        elif a is None or b is None:
            states[name] = "single_sourced"
            settled[name] = a if b is None else b
        elif a == b:
            states[name] = "corroborated"
            settled[name] = a
        else:
            states[name] = "conflict"
            conflicts[name] = (a, b)

    if conflicts:
        settled.update(_resolve_conflicts(settled, conflicts))
        log.warning(
            "extraction_conflict",
            extra={"fields": sorted(conflicts), "n_conflicts": len(conflicts)},
        )

    features = _build_features(settled, states, deterministic, model)

    field_reports = [
        FieldReconciliation(
            field=name,
            value=settled.get(name),
            state=states[name],
            deterministic_value=det_values.get(name),
            model_value=mod_values.get(name),
            confidence=_confidence_for(
                states[name], _reported_confidence(name, deterministic, model)
            ),
            source_refs=_refs_for(name, states[name], deterministic, model),
        )
        for name in CLINICAL_FIELDS
    ]

    return ReconciliationResult(
        features=features,
        fields=field_reports,
        conflicts=sorted(conflicts),
        has_conflict=bool(conflicts),
    )


def _resolve_conflicts(
    base: dict[str, Any], conflicts: dict[str, tuple[Any, Any]]
) -> dict[str, Any]:
    """Pick the assignment of disputed fields that the rules treat as worst.

    Resolved *jointly*, not field by field: YOUNG_BLEEDING_PLUS_FEATURE needs
    bleeding AND a second feature, so choosing each field's "worse" value in
    isolation can miss a combination that fires a higher rule.

    Ranked by (urgency, number of rules fired). The rule count only breaks
    ties, and it favours the reading that surfaces more clinical reasoning
    for the reviewing nurse.
    """
    names = sorted(conflicts)

    if len(names) > MAX_JOINT_CONFLICT_FIELDS:
        # Degenerate input. Fall back to independent per-field resolution so
        # this stays bounded; every field involved is flagged as a conflict
        # regardless, so a human sees all of it either way.
        log.error("conflict_resolution_degraded", extra={"n_conflicts": len(names)})
        return {
            name: _resolve_conflicts(base, {name: conflicts[name]})[name] for name in names
        }

    cfg = load_rules()  # once, not once per candidate combination
    best_assignment: dict[str, Any] | None = None
    best_key: tuple[int, int] = (-1, -1)

    for combo in itertools.product(*(conflicts[n] for n in names)):
        assignment = dict(zip(names, combo))
        candidate = {**base, **assignment}
        try:
            # Deliberately the untraced internal, not the public evaluate():
            # these are search probes, not decisions, and app.rule_engine's
            # public entry point emits a Braintrust span per call. Tracing
            # 2^n probes would bury the one verdict that actually happened.
            verdict = _evaluate_unsafe(
                ReferralFeatures(**candidate), "reconcile-probe", cfg
            )
        except Exception:
            # A combination the schema rejects cannot be the answer; skip it
            # rather than letting one bad candidate abort resolution.
            log.exception("conflict_probe_failed", extra={"assignment": assignment})
            continue

        key = (URGENCY_ORDER.index(verdict.urgency), len(verdict.rules_fired))
        if key > best_key:
            best_key, best_assignment = key, assignment

    if best_assignment is None:
        # Nothing evaluated cleanly. Do not silently drop the disputed fields
        # — take the model's reading and let the conflict flag force review.
        return {name: conflicts[name][1] for name in names}

    return best_assignment


def _build_features(
    settled: dict[str, Any],
    states: dict[str, CorroborationState],
    deterministic: ReferralFeatures,
    model: ReferralFeatures,
) -> ReferralFeatures:
    """Assemble the merged ReferralFeatures the rule engine will see.

    Absent fields stay None and are given neither a source_ref nor a
    confidence entry — the same contract the extractors follow, so
    downstream code cannot tell a merged feature set from a single-source
    one except by looking at the report.
    """
    source_refs: dict[str, str] = {}
    confidence: dict[str, float] = {}

    for name, state in states.items():
        if state == "absent":
            continue
        refs = _refs_for(name, state, deterministic, model)
        if refs:
            source_refs[name] = " | ".join(refs)
        confidence[name] = _confidence_for(
            state, _reported_confidence(name, deterministic, model)
        )

    return ReferralFeatures(
        **{name: settled.get(name) for name in CLINICAL_FIELDS},
        source_refs=source_refs,
        extraction_confidence=confidence,
    )


def _reported_confidence(
    name: str, deterministic: ReferralFeatures, model: ReferralFeatures
) -> list[float]:
    """What each reader claimed for this field, where it claimed anything."""
    return [
        value
        for value in (
            deterministic.extraction_confidence.get(name),
            model.extraction_confidence.get(name),
        )
        if isinstance(value, (int, float))
    ]


def _refs_for(
    name: str,
    state: CorroborationState,
    deterministic: ReferralFeatures,
    model: ReferralFeatures,
) -> list[str]:
    """Both readers' citations, in path order.

    On a conflict this deliberately keeps *both* — the nurse needs to see the
    line each reader was looking at to adjudicate, not just the one that
    happened to win.
    """
    if state == "absent":
        return []
    return [
        ref
        for ref in (deterministic.source_refs.get(name), model.source_refs.get(name))
        if ref
    ]
