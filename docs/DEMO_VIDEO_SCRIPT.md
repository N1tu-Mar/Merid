# 2-minute demo video script

Conversational, and it follows the frontend exactly — sponsors come up
where their tech actually fires in the flow, not as a separate section.
Record at merid-hacksprint.vercel.app or localhost. Reseed first, dismiss
the CopilotKit popup once, pre-open `/` and `/intake`. Timestamps are
targets; if a click lags, keep talking. Total ≈ 2:00.

---

**0:00–0:15 — Landing page** *(hero on screen; scroll slowly as you talk)*

> Raise your hand if you hate being on hold. Yeah — everyone. Now imagine
> you're doubled over gripping your stomach, and the best healthcare can
> offer you is elevator music. Here's the part that isn't funny: in
> cancer care, every four weeks of delay raises your risk of dying by up
> to thirteen percent. Three in four colorectal cancers in people under
> fifty get caught late. The average wait just to *see* a GI doctor is
> forty days. So we built Meridian — the end of "please hold."

**0:15–0:55 — Patient side** *(go to `/intake`; point at the insurance
dropdown, then click **Place call** and let the first two audio turns play
underneath you)*

> This is what a patient gets. Maya Chen, 42, three weeks of bleeding —
> her doctor already wrote her off as "probable hemorrhoids." She calls,
> and an ElevenLabs voice agent picks up — no hold music, and it asks
> eleven clinically-grounded questions plus her insurance. Two things are
> happening under the hood: a deterministic parser is doing the labeling —
> auditable, no AI vibes — and Fireworks runs a corroborating pass, small
> fast open models giving us a confidence score on every single field.
> The calls are stateless, so no patient text ever sits in some model
> provider's logs. If the parser and the model disagree, or confidence
> drops? It goes to a human. It never guesses.
>
> *(outcome card appears — point as you go)*
>
> And look what she gets before she hangs up: flagged urgent, booked
> tomorrow, three clinics sorted by distance with what it'll roughly cost
> her on her plan, and a hold-the-date for her calendar. Notice what the
> voice never said — a diagnosis. It physically can't. Our no-diagnosis
> filter runs *inside* the speech synthesizer.

**0:55–1:35 — Doctor side** *(click "switch to doctor side"; hover the 🔒
badge on the worklist, open Maya's case, scroll the fired rule, then
Approve → type a name → Confirm)*

> Same case, the clinic's view. See this lock badge? Faxes are
> attacker-controlled input, so every document gets opened inside a
> Daytona sandbox — internet blocked, and it self-destructs seconds
> later. Sensitive files never touch our servers, and the sandbox ID is
> right here as proof.
>
> Now the decision. No model decided this — a written rule fired: under
> fifty, bleeding, plus a second red flag. That threshold was measured on
> two thousand and ninety-three real patients, and the citation is right
> there in the interface. Insurance got matched too — but only *after*
> the clinical verdict. Money can never change urgency in this system.
>
> *(click Confirm approval)*
>
> A nurse signs — that's a cryptographic hash, that's an audit trail —
> and the moment she does, the slot hits the calendar and CopilotKit's
> care-team loop drafts the Slack note, which passes the same
> no-diagnosis filter. Agents prepare. Humans commit.

**1:35–1:50 — Prior auth & payer** *(flow strip → step 2; open the packet,
Approve → Submit → Call payer IVR; let one line of hold music play)*

> Prior auth writes itself — every sentence linked to its source — the
> physician signs, and then our agent does the job everyone hates: it
> calls the insurance company. Real phone tree, real touch-tones, real
> hold music — ElevenLabs on both ends. Approved. No human sat on hold.

**1:50–2:00 — Practice pulse** *(flow strip → step 3; end on the tiles)*

> And it's all measured. Every decision streams a trace to Braintrust,
> which grades us on every change: one hundred percent of urgent cases
> caught, zero patients falsely reassured — even our extraction model was
> picked by a head-to-head eval, not a vibe. We don't diagnose anyone.
> We make sure the right people get scoped. Meridian.

---

**Recording prep**
- Clean state: `rm meridian.db && .venv/bin/python -m app.seed`, restart
  the backend — fictional names, one PA packet pre-drafted at step 2.
- Intake + IVR audio play from the committed cache — wifi can't hurt you.
- Dismiss the CopilotKit popup once in the recording browser.
- Do one silent click-through before rolling; the approve form needs a
  typed name ("Dana Brooks, RN" reads well on camera).
- If something breaks on camera: "This is live — and when anything fails
  in Meridian, it fails to a human. Including demos." Then keep going.
