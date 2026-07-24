# 2-minute demo video script

Screen-record at merid-hacksprint.vercel.app (or localhost — faster, no
tunnel risk). Have two tabs pre-opened: `/` (landing) and `/intake`.
Dismiss the CopilotKit popup once before recording. Speak plainly; the
timestamps are targets, not handcuffs. Total ≈ 2:00.

---

**0:00–0:12 — The hook** *(on the landing page, slowly scroll the hero)*

> Raise your hand if you hate being on hold. Now imagine you're doubled
> over, gripping your stomach — and in cancer care, every four weeks of
> delay raises your risk of dying by up to thirteen percent. That's the
> BMJ, 1.2 million patients. This is Meridian: the end of "please hold."

**0:12–0:25 — The stakes** *(scroll to the three big numbers)*

> Three in four colorectal cancers under 50 are caught late. The average
> GI wait is 40 days — the longest of any specialty. And when a missed
> cancer becomes a malpractice claim, the average payment is $491,000.
> The failure isn't medicine. It's routing.

**0:25–0:55 — Patient side** *(switch to `/intake`, click **Place call**;
let two turns of audio play, then talk over it)*

> This is the patient's door. Maya Chen, 42, three weeks of bleeding —
> her doctor wrote "probable hemorrhoids." Watch: the voice agent asks
> eleven evidence-based questions plus her insurance…
>
> *(point at the outcome card as it appears)*
>
> …and before she hangs up: flagged urgent, booked for tomorrow, three
> clinics sorted by distance with her estimated cost, and a hold-the-date
> calendar link. Notice what it never said — a diagnosis. The voice
> physically can't. The filter runs inside the speech synthesizer.

**0:55–1:25 — Doctor side** *(click "switch to doctor side", open Maya's
case, scroll to the fired rules, then click Approve → type a name →
Confirm)*

> Same case, the clinic's door. No AI opinions here — a written rule
> fired: under 50, bleeding, plus a second red flag. The threshold comes
> from a study of 2,093 real patients — the citation is right there in
> the interface. Insurance matched *after* the clinical verdict — money
> can never change urgency. A nurse signs — that's a hash, that's an
> audit trail — the slot hits the calendar, and the care team gets a
> Slack draft that passed the same no-diagnosis filter.

**1:25–1:45 — Prior auth + payer call** *(flow strip → step 2, open the
seeded packet, click Approve → Submit → Call payer IVR; let one hold-music
line of audio play)*

> Prior auth writes itself — every sentence linked to its source — the
> physician signs, and then our agent does the thing everyone hates:
> it calls the payer, presses 3, enters the member ID, and sits through
> the hold music. Approved. A human never touched the phone.

**1:45–2:00 — Close** *(flow strip → Practice pulse; end on the tiles)*

> Sixteen referrals, triaged in under a second each, the write-off
> caught, hold time eaten. One hundred percent of urgent cases flagged,
> zero patients falsely reassured — tested, traced, and cited. We don't
> diagnose anyone. We make sure the right people get scoped. Meridian.

---

**Recording tips**
- Reseed first for clean state: `rm meridian.db && .venv/bin/python -m app.seed`
  (then restart the backend) — fictional names, one drafted PA packet ready.
- The IVR audio and intake audio play from the committed cache — no wifi needed.
- If a click lags, keep talking; dead air is worse than a spinner.
- Backup one-liner if anything breaks on camera: "This is live — and when
  anything fails in Meridian, it fails to a human. Including demos."
