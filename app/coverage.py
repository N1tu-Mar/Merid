"""Insurance matching for the demo: which (synthetic) plan covers this
patient, does the procedure need prior auth, and what will the patient
roughly owe.

This is deliberately NOT part of the clinical rule engine — coverage can
never change urgency (a rule engine that triages differently by payer would
violate the whole design). It runs after the clinical verdict, purely to
answer the two questions patients actually ask on the phone: "do I need
approval?" and "what will it cost me?"

Plans are synthetic and assigned deterministically per referral (same
pattern as the mock payer IVR): reproducible in a live demo, varied across
the worklist, and impossible to confuse with real insurance data.
"""

from __future__ import annotations

import hashlib

# Synthetic plan table. Cost bands are illustrative demo figures in the
# range of published colonoscopy episode costs (Medicare ~$950 all-in 2015,
# commercial ~$2,033 in 2016 — see docs/FACTS.md #10); they are not quotes.
PLANS: list[dict] = [
    {
        "plan": "Aurora PPO (synthetic)",
        "pa_required": True,
        "est_patient_share": "$150–$400",
        "note": "Prior auth required for diagnostic colonoscopy; screening covered in full.",
    },
    {
        "plan": "Granite HMO (synthetic)",
        "pa_required": True,
        "est_patient_share": "$250–$600",
        "note": "Prior auth + in-network facility required.",
    },
    {
        "plan": "Harbor Medicare Advantage (synthetic)",
        "pa_required": False,
        "est_patient_share": "$0–$150",
        "note": "No prior auth for colonoscopy following a positive screen or red-flag referral.",
    },
]


def coverage_for(referral_id: str) -> dict:
    """Deterministic synthetic plan match for a referral."""
    digest = hashlib.sha256(f"coverage:{referral_id}".encode()).hexdigest()
    plan = PLANS[int(digest[:8], 16) % len(PLANS)]
    return {
        **plan,
        "synthetic": True,
        # What the pipeline does with the answer — never a clinical decision:
        "next_step": (
            "Agent drafts the prior-auth packet for physician sign-off"
            if plan["pa_required"]
            else "No prior auth needed — booking stands as approved"
        ),
    }
