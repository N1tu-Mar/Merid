"""Tests for the corroboration reconciler.

Written before the implementation (repo norm: the test for a decision
component comes first). These pin the behaviour that matters clinically:

  - agreement raises confidence, it does not change values
  - a field only one path could see is usable but marked single-sourced
  - a *conflict* resolves to whichever reading the rule engine treats as
    more urgent, and is always surfaced

The headline case is the last one: the intake parser reads "nope, apart from
the bleeding" as rectal_bleeding=False, which silently launders a 52-year-old
from urgent to routine. Reconciliation has to undo that.
"""

from __future__ import annotations

import pytest

from app.rule_engine import evaluate
from app.schemas import ReferralFeatures
from services.extract.reconcile import (
    CONFIDENCE_BY_STATE,
    ReconciliationResult,
    reconcile,
)


def feats(**kwargs) -> ReferralFeatures:
    """Build a feature set, auto-populating source_refs for every set field
    so the fixtures look like real extractor output."""
    refs = {k: f"test:{k}" for k, v in kwargs.items() if v is not None}
    return ReferralFeatures(**kwargs, source_refs=refs)


# ---------------------------------------------------------------------------
# agreement
# ---------------------------------------------------------------------------


def test_agreement_is_corroborated_and_keeps_the_value():
    result = reconcile(
        deterministic=feats(age=42, rectal_bleeding=True),
        model=feats(age=42, rectal_bleeding=True),
    )
    assert result.features.rectal_bleeding is True
    assert result.features.age == 42
    assert result.by_field("rectal_bleeding").state == "corroborated"
    assert not result.has_conflict


def test_corroborated_fields_carry_both_source_refs():
    result = reconcile(
        deterministic=ReferralFeatures(
            rectal_bleeding=True, source_refs={"rectal_bleeding": "transcript:turn_4"}
        ),
        model=ReferralFeatures(
            rectal_bleeding=True, source_refs={"rectal_bleeding": "evidence:2:'blood PR'"}
        ),
    )
    ref = result.features.source_refs["rectal_bleeding"]
    assert "transcript:turn_4" in ref
    assert "evidence:2:'blood PR'" in ref


def test_agreement_on_false_is_still_corroboration():
    """Both paths agreeing a red flag is absent is a real signal, not a gap."""
    result = reconcile(
        deterministic=feats(rectal_bleeding=False),
        model=feats(rectal_bleeding=False),
    )
    assert result.features.rectal_bleeding is False
    assert result.by_field("rectal_bleeding").state == "corroborated"


# ---------------------------------------------------------------------------
# single-sourced: only one path could see the field
# ---------------------------------------------------------------------------


def test_field_only_the_model_saw_is_single_sourced():
    """The deterministic parser reads transcripts only. A fact that exists
    solely in an uploaded document has no second voter — usable, but the
    nurse must be able to see it was uncorroborated."""
    result = reconcile(
        deterministic=feats(age=61),
        model=feats(age=61, iron_deficiency_anemia=True),
    )
    assert result.features.iron_deficiency_anemia is True
    assert result.by_field("iron_deficiency_anemia").state == "single_sourced"
    assert not result.has_conflict


def test_field_only_the_parser_saw_is_single_sourced():
    result = reconcile(
        deterministic=feats(abdominal_pain=True),
        model=feats(),
    )
    assert result.features.abdominal_pain is True
    assert result.by_field("abdominal_pain").state == "single_sourced"


def test_field_neither_path_saw_is_absent_and_stays_none():
    result = reconcile(deterministic=feats(age=42), model=feats(age=42))
    assert result.features.fit_result is None
    assert result.by_field("fit_result").state == "absent"
    # absent fields must not fabricate a source_ref
    assert "fit_result" not in result.features.source_refs


# ---------------------------------------------------------------------------
# confidence is derived from corroboration, never asserted by a model
# ---------------------------------------------------------------------------


def test_confidence_comes_from_state_not_from_the_inputs():
    """Inputs claim wildly different confidence; output ignores both and
    derives it from whether the paths agreed."""
    result = reconcile(
        deterministic=ReferralFeatures(
            rectal_bleeding=False,
            source_refs={"rectal_bleeding": "a"},
            extraction_confidence={"rectal_bleeding": 0.9},
        ),
        model=ReferralFeatures(
            rectal_bleeding=False,
            source_refs={"rectal_bleeding": "b"},
            extraction_confidence={"rectal_bleeding": 0.11},
        ),
    )
    assert result.features.extraction_confidence["rectal_bleeding"] == (
        CONFIDENCE_BY_STATE["corroborated"]
    )


def test_conflict_confidence_is_below_the_escalation_threshold():
    """Existing callers escalate under 0.5 — a conflict must land there."""
    assert CONFIDENCE_BY_STATE["conflict"] < 0.5
    assert CONFIDENCE_BY_STATE["corroborated"] >= 0.5


# ---------------------------------------------------------------------------
# conflict: the reason this module exists
# ---------------------------------------------------------------------------


def test_conflict_resolves_toward_the_more_urgent_reading():
    result = reconcile(
        deterministic=feats(age=42, rectal_bleeding=False, abdominal_pain=True),
        model=feats(age=42, rectal_bleeding=True, abdominal_pain=True),
    )
    assert result.features.rectal_bleeding is True
    assert result.by_field("rectal_bleeding").state == "conflict"
    assert result.has_conflict
    assert "rectal_bleeding" in result.conflicts


def test_conflict_records_both_candidate_values_for_the_nurse():
    result = reconcile(
        deterministic=feats(rectal_bleeding=False),
        model=feats(rectal_bleeding=True),
    )
    field = result.by_field("rectal_bleeding")
    assert field.deterministic_value is False
    assert field.model_value is True


def test_conflicting_age_is_resolved_by_urgency_not_by_magnitude():
    """Age has no safe direction: 52 fires BLEEDING_OVER_50 (urgent) while 42
    fires YOUNG_BLEEDING_PLUS_FEATURE (also urgent) only when a second feature
    is present. With bleeding alone, the *older* reading is the urgent one, so
    a naive 'pick the younger age' rule would under-triage."""
    result = reconcile(
        deterministic=feats(age=42, rectal_bleeding=True),
        model=feats(age=52, rectal_bleeding=True),
    )
    assert result.features.age == 52
    verdict = evaluate(result.features, referral_id="t")
    assert verdict.urgency == "urgent"


def test_conflicts_are_resolved_jointly_not_field_by_field():
    """Two conflicting fields must be resolved as a combination — the most
    urgent joint assignment, not the most urgent choice for each field in
    isolation."""
    result = reconcile(
        deterministic=feats(age=42, rectal_bleeding=True, abdominal_pain=False),
        model=feats(age=42, rectal_bleeding=False, abdominal_pain=True),
    )
    # YOUNG_BLEEDING_PLUS_FEATURE needs bleeding AND a second feature; only
    # the (True, True) combination reaches urgent.
    assert result.features.rectal_bleeding is True
    assert result.features.abdominal_pain is True
    assert evaluate(result.features, referral_id="t").urgency == "urgent"


def test_resolution_never_lowers_urgency_below_either_input():
    """Whatever it picks must be at least as urgent as either path alone."""
    det = feats(age=52, rectal_bleeding=False, prior_colonoscopy_date=None)
    mod = feats(age=52, rectal_bleeding=True, prior_colonoscopy_date=None)
    result = reconcile(deterministic=det, model=mod)

    from app.schemas import URGENCY_ORDER

    rank = URGENCY_ORDER.index
    merged = rank(evaluate(result.features, referral_id="t").urgency)
    assert merged >= rank(evaluate(det, referral_id="t").urgency)
    assert merged >= rank(evaluate(mod, referral_id="t").urgency)


# ---------------------------------------------------------------------------
# the headline regression: the parser's silent laundering
# ---------------------------------------------------------------------------


def test_hedged_bleeding_no_longer_launders_a_52_year_old_to_routine():
    """"nope, apart from the bleeding" parses to rectal_bleeding=False at
    confidence 0.9. Alone that produces routine/BOOK via SCREENING_AGE_NO_PRIOR
    — a confident-looking wrong answer. The model path reads it correctly and
    reconciliation must restore urgent."""
    parser_reading = feats(
        age=52,
        rectal_bleeding=False,
        prior_colonoscopy_date=None,
        change_in_bowel_habit=False,
        unintentional_weight_loss=False,
        abdominal_pain=False,
        iron_deficiency_anemia=False,
        fit_result="negative",
        abdominal_or_rectal_mass=False,
    )
    assert evaluate(parser_reading, referral_id="t").urgency == "routine"  # the bug

    model_reading = parser_reading.model_copy(update={"rectal_bleeding": True})
    result = reconcile(deterministic=parser_reading, model=model_reading)

    assert result.features.rectal_bleeding is True
    assert result.has_conflict
    assert evaluate(result.features, referral_id="t").urgency == "urgent"


# ---------------------------------------------------------------------------
# structural guarantees
# ---------------------------------------------------------------------------


def test_every_clinical_field_is_reported_exactly_once():
    result = reconcile(deterministic=feats(age=42), model=feats(age=42))
    clinical = set(ReferralFeatures.model_fields) - {"source_refs", "extraction_confidence"}
    reported = [f.field for f in result.fields]
    assert sorted(reported) == sorted(clinical)
    assert len(reported) == len(set(reported))


def test_result_is_serialisable_for_the_api():
    result = reconcile(
        deterministic=feats(rectal_bleeding=False),
        model=feats(rectal_bleeding=True),
    )
    dumped = result.model_dump(mode="json")
    assert dumped["has_conflict"] is True
    assert isinstance(dumped["fields"], list)


def test_reconciling_two_empty_paths_is_safe():
    result = reconcile(deterministic=ReferralFeatures(), model=ReferralFeatures())
    assert not result.has_conflict
    assert all(f.state == "absent" for f in result.fields)
    assert evaluate(result.features, referral_id="t").disposition == "ESCALATE"


def test_by_field_rejects_unknown_field():
    result = reconcile(deterministic=ReferralFeatures(), model=ReferralFeatures())
    with pytest.raises(KeyError):
        result.by_field("not_a_field")


def test_reconciliation_result_type():
    assert isinstance(
        reconcile(deterministic=ReferralFeatures(), model=ReferralFeatures()),
        ReconciliationResult,
    )
