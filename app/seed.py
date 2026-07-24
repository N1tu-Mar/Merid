"""Seed synthetic referrals (build order step 2) into the DB and produce verdicts.

Run: python -m app.seed
"""

from __future__ import annotations

import json
from pathlib import Path

from app.db import ReferralRecord, TriageVerdictRecord, get_session, init_db
from app.rule_engine import evaluate
from app.schemas import ReferralFeatures

SEED_PATH = Path(__file__).parent.parent / "data" / "synthetic" / "referrals.json"


def _synthetic_source_refs(features: dict) -> dict[str, str]:
    """Every populated feature must carry a source_ref. For seed data this
    points at the synthetic referral line rather than a real chart."""
    return {k: f"synthetic_referral:{k}" for k, v in features.items() if v is not None}


def _synthetic_confidence(features: dict) -> dict[str, float]:
    return {k: 0.95 for k, v in features.items() if v is not None}


def seed() -> None:
    init_db()
    session = get_session()
    try:
        cases = json.loads(SEED_PATH.read_text())
        for case in cases:
            existing = session.get(ReferralRecord, case["id"])
            if existing:
                continue

            raw_features = case["features"]
            features = ReferralFeatures(
                **raw_features,
                source_refs=_synthetic_source_refs(raw_features),
                extraction_confidence=_synthetic_confidence(raw_features),
            )

            record = ReferralRecord(
                id=case["id"],
                source=case["source"],
                raw_text=case["raw_text"],
                patient_name=case["patient_name"],
                features_json=features.model_dump_json(),
            )
            session.add(record)

            verdict = evaluate(features, referral_id=case["id"])
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
            print(
                f"seeded {case['id']}: urgency={verdict.urgency} "
                f"disposition={verdict.disposition} rules={verdict.rules_fired}"
            )
        session.commit()

        _seed_pa_packet(session)
    finally:
        session.close()


def _seed_pa_packet(session) -> None:
    """Seed one drafted PA packet (for the elderly-IDA case) so the PA page
    demos mid-flow: physician approval is the next click, not three steps of
    setup. The nurse approval it rests on is seeded synthetic data, clearly
    attributed — the live demo path still walks the full chain by hand."""
    import json as _json

    from app.approval import sign
    from app.db import PAPacketRecord
    from app.schemas import ReferralFeatures, TriageVerdict
    from services.priorauth.draft import draft_packet

    packet_id = "seed-packet-elderly-ida-b"  # id chosen so the mock payer status is "approved" — happy demo ending
    if session.get(PAPacketRecord, packet_id):
        return

    ref = session.get(ReferralRecord, "elderly-ida")
    if not ref:
        return
    verdict = (
        session.query(TriageVerdictRecord)
        .filter(TriageVerdictRecord.referral_id == ref.id)
        .first()
    )
    if not verdict or verdict.approved_by:
        return

    actor, approved_at, approval_hash = sign(
        "Nina Alvarez, RN (pre-seeded demo)",
        {"verdict_id": verdict.id, "referral_id": ref.id, "urgency": verdict.urgency},
    )
    verdict.approved_by = actor
    verdict.approved_at = approved_at
    verdict.approval_hash = approval_hash
    verdict.booked_slot = "Urgent GI clinic — tomorrow at 10:00 AM"

    features = ReferralFeatures.model_validate_json(ref.features_json)
    tv = TriageVerdict(
        referral_id=verdict.referral_id,
        urgency=verdict.urgency,
        disposition=verdict.disposition,
        rules_fired=verdict.rules_fired,
        rule_version=verdict.rule_version,
        missing_features=verdict.missing_features,
        created_at=verdict.created_at,
    )
    sentences, _dropped = draft_packet(features, tv)
    session.add(
        PAPacketRecord(
            id=packet_id,
            referral_id=ref.id,
            verdict_id=verdict.id,
            sentences_json=_json.dumps([s.model_dump() for s in sentences]),
            status="drafted",
        )
    )
    session.commit()
    print(f"seeded PA packet {packet_id} (drafted, awaiting physician approval)")


if __name__ == "__main__":
    seed()
