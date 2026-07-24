# 2-minute demo video script (v3)

Conversational, follows the frontend, and **every sponsor is named at the
exact moment their tech fires in the flow** — no separate sponsor section.

## The flow at a glance (this is the spine of the video)

| # | Flow step | Sponsor | What the viewer sees |
|---|---|---|---|
| 1 | Patient calls the intake line | **ElevenLabs** | Voice agent answers, asks 11 evidence-based questions + insurance |
| 2 | The transcript gets read | **Fireworks AI** | Deterministic parser labels; Fireworks corroborates with per-field confidence, stateless calls |
| 3 | (Fax path) documents get opened | **Daytona** | 🔒 badge — internet-blocked sandbox, self-destructs, ID shown as proof |
| 4 | Rules decide, evidence cited | — (our core) | Rule fired + the 2,093-patient study, linked in the UI |
| 5 | Nurse signs → care team looped in | **CopilotKit** | Signature hash, calendar event + filtered Slack draft to #gi-triage |
| 6 | Prior auth → agent phones the payer | **ElevenLabs** | Real phone tree, DTMF tones, hold music; status comes back |
| 7 | Everything measured | **Braintrust** | Practice pulse + traces; 100% urgent caught, 0 falsely reassured; model A/B receipt |

Patient demo covers steps 1–2 (+ booking payoff). Doctor demo covers 3–7.

---

## ACT 0 — Hook (0:00–0:15) · landing page, scroll slowly

> Raise your hand if you hate being on hold. Yeah — everyone. Now imagine
> you're doubled over gripping your stomach, and the best healthcare can
> offer you is elevator music. Here's the part that isn't funny: in cancer
> care, every four weeks of delay raises your risk of dying by up to
> thirteen percent. Three in four colorectal cancers in people under fifty
> get caught late. The average wait just to *see* a GI doctor is forty
> days. So we built Meridian — the end of "please hold."

## ACT 1 — The PATIENT demo (0:15–0:55) · go to `/intake`

*Point at the insurance dropdown, click **Place call**, let two audio
turns play under your voice.*

> Here's the patient's side. Maya Chen, forty-two, three weeks of
> bleeding — her doctor already wrote her off as "probable hemorrhoids."
> She calls, and an **ElevenLabs** voice agent picks up — no hold music —
> and walks her through eleven clinically-grounded questions, plus her
> insurance. **[ELEVENLABS — step 1 of the flow]**
>
> Under the hood, two readers check each other: our deterministic parser
> does the labeling — auditable, no AI vibes — and **Fireworks** runs the
> corroborating pass: small, fast, open models scoring confidence on
> every single field, called statelessly so no patient text ever sits in
> a model provider's logs. If they disagree, or confidence drops, it goes
> to a human. It never guesses. **[FIREWORKS — step 2]**

*The outcome card appears — point at each element.*

> Before she hangs up: flagged urgent, booked tomorrow, three clinics
> sorted by distance with what it'll roughly cost on her plan, and a
> hold-the-date for her calendar. And notice what the voice never said —
> a diagnosis. It physically can't; our no-diagnosis filter runs *inside*
> the speech synthesizer.

## ACT 2 — The DOCTOR demo (0:55–2:00) · click "switch to doctor side"

*The handoff line as the worklist loads:*

> That call Maya just made? It's already here, on the clinic's side —
> in the triage queue with an urgency, a disposition, and her insurance
> already matched.

*Hover the 🔒 badge on a fax-scan row.*

> Faxes come in this door too — and a fax is attacker-controlled input.
> So every document gets opened inside a **Daytona** sandbox: internet
> blocked, self-destructs seconds later, and the sandbox ID is badged
> right here as proof. Sensitive files never touch our servers.
> **[DAYTONA — step 3]**

*Open Maya's case; scroll to the fired rule.*

> Now the decision — and no model made it. A written rule fired: under
> fifty, bleeding, plus a second red flag. That threshold was measured on
> two thousand ninety-three real patients, and the citation is linked
> right in the interface. Insurance matched too — but only *after* the
> clinical verdict. Money can never change urgency here.

*Click Approve → type "Dana Brooks, RN" → Confirm. Point at the hash,
then the care-team card.*

> A nurse signs — that's a cryptographic hash, that's an audit trail —
> and the instant she does, **CopilotKit**'s care-team loop kicks in: the
> slot hits the calendar and a Slack draft for #gi-triage appears, having
> passed the same no-diagnosis filter. Agents prepare; humans commit.
> **[COPILOTKIT — step 5]**

*Flow strip → step 2 "Prior auth & payer". Open the packet, Approve →
Submit → Call payer IVR. Let one line of hold music play.*

> Prior auth writes itself — every sentence linked to its source — the
> physician signs, and then our agent does the job everyone hates: it
> calls the insurance company. Real phone tree, real touch-tones, real
> hold music — **ElevenLabs** on both ends of this product's phone calls.
> Approved. No human sat on hold. **[ELEVENLABS again — step 6]**

*Flow strip → step 3 "Practice pulse". End on the tiles.*

> And it's all measured. Every live decision streams a trace into
> **Braintrust**, which grades the system on every change: one hundred
> percent of urgent cases caught, zero patients falsely reassured — we
> even picked our extraction model with a head-to-head Braintrust eval,
> not a vibe. **[BRAINTRUST — step 7]**
>
> We don't diagnose anyone. We make sure the right people get scoped.
> Meridian.

---

## Recording prep

- Clean state: `rm meridian.db && .venv/bin/python -m app.seed`, restart
  the backend — fictional names, one PA packet pre-drafted at step 2.
- Intake + IVR audio play from the committed cache — wifi can't hurt you.
- Dismiss the CopilotKit popup once in the recording browser.
- One silent click-through before rolling.
- Running hot? Cut "called statelessly…" (it comes back at the Daytona
  beat). Never cut the last two sentences.
- If something breaks on camera: "This is live — and when anything fails
  in Meridian, it fails to a human. Including demos." Keep going.

## Honesty guardrails (if asked after)

- WorkOS and CodeRabbit are not integrated — don't claim them. If asked:
  WorkOS hosted us; CodeRabbit reviewed PRs is only claimable if it's
  actually installed on the repo.
- The CopilotKit LLM sidebar is feature-flagged off (it leaked a
  differential under red-teaming; fail-closed applies to us too). The
  Slack/calendar loop shown IS the CopilotKit lane's deterministic half.
- Documents are read as text after sandbox decode — don't claim live
  image-model inference; it's the designed next step.
