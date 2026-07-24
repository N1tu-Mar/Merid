import Image from "next/image";
import Link from "next/link";
import DemoBanner from "@/components/DemoBanner";

// Landing page as a pitch: white, Arial, one idea per screen, numbers over
// paragraphs. Every stat traces to a primary source in docs/FACTS.md —
// nothing renders here that isn't on that sheet.

function Kicker({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-[11px] font-bold uppercase tracking-[0.3em] text-slate-400">
      {children}
    </p>
  );
}

// Each step names the partner tech doing the work — the workflow IS the
// sponsor integration map; nothing is a logo on a slide.
const STEPS = [
  {
    n: "1",
    title: "A call or a fax arrives",
    tools: ["ElevenLabs", "Daytona"],
    body: "Patients talk to a live voice agent (ElevenLabs). Faxes are opened inside a throwaway, internet-blocked sandbox (Daytona) that's destroyed seconds later — hostile documents never touch the system.",
  },
  {
    n: "2",
    title: "AI reads it — facts only",
    tools: ["Fireworks AI"],
    body: "Fireworks extracts age, symptoms, duration, insurance — in about a second. It has no opinions and no authority; we raced two of their models and kept the winner, scorecard attached.",
  },
  {
    n: "3",
    title: "Rules set how fast",
    tools: ["Braintrust"],
    body: "Ten auditable rules, thresholds measured on 2,093 real patients, cited line by line. Braintrust grades the system on every change and traces every live decision — 100% of urgent cases caught.",
  },
  {
    n: "4",
    title: "A nurse clicks approve",
    tools: ["CopilotKit"],
    body: "The copilot drafts the calendar event and the Slack note to the care team; the nurse clicks send. The slot books with the patient's estimated cost already shown.",
  },
  {
    n: "5",
    title: "The paperwork fights itself",
    tools: ["ElevenLabs", "Braintrust"],
    body: "Prior auth drafts with every sentence sourced. The doctor signs. The agent dials the payer's phone tree (ElevenLabs voice) and sits through the hold music — every step leaves a replayable trace.",
  },
];

export default function Home() {
  return (
    <div className="min-h-screen bg-white text-slate-900 selection:bg-amber-100">
      <DemoBanner />

      <header>
        <nav className="mx-auto flex max-w-4xl items-center justify-between px-6 py-6">
          <span className="flex items-center gap-2.5 text-lg font-bold tracking-tight">
            {/* Wordmark: a meridian line crossing a pulse — the route a
                patient travels, kept alive. */}
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden>
              <circle cx="12" cy="12" r="9" stroke="#0f172a" strokeWidth="1.8" />
              <path d="M12 3c3.6 2.4 3.6 15.6 0 18" stroke="#0f172a" strokeWidth="1.8" strokeLinecap="round" />
              <path d="M4 12h4l2-3 3 6 2-3h5" stroke="#f59e0b" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            Meridian
            <span className="ml-1 hidden text-xs font-normal normal-case tracking-normal text-slate-400 sm:inline">
              the end of &ldquo;please hold&rdquo;
            </span>
          </span>
          <div className="flex items-center gap-6 text-sm text-slate-500">
            <Link href="/intake" className="hover:text-slate-900">Intake Line</Link>
            <Link href="/worklist" className="hover:text-slate-900">Worklist</Link>
            <Link href="/dashboard" className="hover:text-slate-900">Dashboard</Link>
          </div>
        </nav>
      </header>

      <main className="mx-auto max-w-4xl px-6">
        {/* Slide 1 — hook */}
        <section className="flex min-h-[80vh] flex-col justify-center">
          <h1 className="max-w-3xl text-5xl font-bold leading-[1.05] tracking-tight sm:text-7xl">
            You&apos;re doubled over, gripping your stomach.
            <br />
            <span className="text-slate-400 line-through decoration-amber-500 decoration-[6px]">
              &ldquo;Please hold.&rdquo;
            </span>
          </h1>
          <p className="mt-8 max-w-xl text-lg leading-relaxed text-slate-500">
            Elevator music. A stranger who&apos;ll read your fax in three
            weeks. Nobody who can tell you what it&apos;ll cost. Meridian ends
            the hold music: it answers, triages you against real clinical
            evidence, books the scope, and fights the insurance company — a
            human signs every step, and it never diagnoses.
          </p>
          <div className="mt-10 flex items-center gap-6">
            <Link
              href="/intake"
              className="rounded-full bg-slate-900 px-6 py-3 text-sm font-bold text-white hover:bg-slate-700"
            >
              Hear the call
            </Link>
            <span className="text-sm text-slate-400">live, 60 seconds</span>
          </div>
        </section>

        {/* Slide 2 — how grave */}
        <section className="border-t border-slate-100 py-24">
          <Kicker>The stakes</Kicker>
          <div className="mt-12 space-y-12">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-baseline sm:gap-10">
              <span className="min-w-[13rem] text-6xl font-bold tracking-tight">3 in 4</span>
              <p className="max-w-md text-slate-500">
                colorectal cancers in adults under 50 are caught late — it&apos;s
                now the #1 cancer killer under 50, rising 3% a year.
              </p>
            </div>
            <div className="flex flex-col gap-2 sm:flex-row sm:items-baseline sm:gap-10">
              <span className="min-w-[13rem] text-6xl font-bold tracking-tight">40 days</span>
              <p className="max-w-md text-slate-500">
                average wait just to see a gastroenterologist — the longest of
                any specialty in America.
              </p>
            </div>
            <div className="flex flex-col gap-2 sm:flex-row sm:items-baseline sm:gap-10">
              <span className="min-w-[13rem] text-6xl font-bold tracking-tight">$491K</span>
              <p className="max-w-md text-slate-500">
                what a practice pays, on average, when a missed colorectal
                cancer becomes a malpractice claim — and two-thirds of
                referrals never even become completed visits.
              </p>
            </div>
          </div>
        </section>

        {/* Slide 2b — what it looks like today */}
        <section className="border-t border-slate-100 py-24">
          <Kicker>Today</Kicker>
          <h2 className="mt-6 max-w-2xl text-3xl font-bold leading-tight tracking-tight sm:text-4xl">
            This is the current system, working as designed.
          </h2>
          <div className="mt-12 grid gap-12 sm:grid-cols-2">
            <div>
              <p className="text-sm font-bold uppercase tracking-widest text-slate-400">
                Without Meridian
              </p>
              <ul className="mt-4 space-y-3 text-sm leading-relaxed text-slate-500">
                <li>Your referral is a fax in a tray. Someone keys it in on day 3.</li>
                <li>Weeks of phone tag — 40 days on average before a GI even sees you.</li>
                <li>Prior auth: 24 minutes of staff hold time per case, weeks on the calendar.</li>
                <li>Your cost? Nobody can tell you until the bill arrives.</li>
                <li>Two-thirds of referrals never become completed visits at all.</li>
              </ul>
            </div>
            <div>
              <p className="text-sm font-bold uppercase tracking-widest text-emerald-600">
                With Meridian
              </p>
              <ul className="mt-4 space-y-3 text-sm leading-relaxed text-slate-600">
                <li>The call is answered now; the fax is read in seconds.</li>
                <li>Triage in under a second, against cited clinical evidence.</li>
                <li>A nurse signs; the slot books straight onto the calendar.</li>
                <li>Insurance matched up front: prior auth flagged, your rough share shown.</li>
                <li>The agent drafts the paperwork and sits through the hold music.</li>
              </ul>
            </div>
          </div>
        </section>

        {/* Slide 3 — who we are, who buys */}
        <section className="border-t border-slate-100 py-24">
          <Kicker>Meridian</Kicker>
          <h2 className="mt-6 max-w-2xl text-3xl font-bold leading-tight tracking-tight sm:text-4xl">
            The AI front desk for GI practices — every referral becomes a
            booked, authorized procedure.
          </h2>
          <div className="mt-12 grid gap-8 sm:grid-cols-3">
            <div>
              <p className="font-bold">GI practices &amp; MSOs</p>
              <p className="mt-2 text-sm text-slate-500">
                buy it — recovered referrals are four-figure procedures they
                already own.
              </p>
            </div>
            <div>
              <p className="font-bold">Triage nurses &amp; schedulers</p>
              <p className="mt-2 text-sm text-slate-500">
                run it — same queue, same sign-offs, without the fax pile and
                the hold music.
              </p>
            </div>
            <div>
              <p className="font-bold">Referring physicians</p>
              <p className="mt-2 text-sm text-slate-500">
                trust it — the loop closes the same day, with an audit trail on
                every decision.
              </p>
            </div>
          </div>
        </section>

        {/* Slide 4 — the flow, steps 1-5 */}
        <section className="border-t border-slate-100 py-24">
          <Kicker>How it works</Kicker>
          <h2 className="mt-6 text-3xl font-bold tracking-tight sm:text-4xl">
            AI reads. Rules decide. People sign.
          </h2>
          <p className="mt-3 max-w-xl text-sm text-slate-500">
            Five steps, five partners — each one doing a job the demo would die
            without.
          </p>
          <div className="mt-12 space-y-0">
            {STEPS.map((s) => (
              <div
                key={s.n}
                className="grid gap-2 border-t border-slate-100 py-7 first:border-t-0 sm:grid-cols-[4rem_16rem_1fr] sm:gap-6"
              >
                <span className="text-2xl font-bold text-amber-500">{s.n}</span>
                <div>
                  <h3 className="font-bold">{s.title}</h3>
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {s.tools.map((t) => (
                      <span
                        key={t}
                        className="rounded-full border border-slate-200 bg-slate-50 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-slate-500"
                      >
                        {t}
                      </span>
                    ))}
                  </div>
                </div>
                <p className="text-sm leading-relaxed text-slate-500">{s.body}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Slide 4a — two doors: patient side and clinic side */}
        <section className="border-t border-slate-100 py-24">
          <Kicker>One system, two doors</Kicker>
          <div className="mt-10 grid gap-6 sm:grid-cols-2">
            <Link
              href="/intake"
              className="group rounded-2xl border border-amber-200 bg-amber-50/50 p-8 transition-colors hover:border-amber-300 hover:bg-amber-50"
            >
              <p className="text-xs font-bold uppercase tracking-widest text-amber-600">
                For the patient
              </p>
              <h3 className="mt-3 text-2xl font-bold tracking-tight">
                Call. Answer. Pick a slot.
              </h3>
              <ul className="mt-4 space-y-2 text-sm leading-relaxed text-slate-600">
                <li>Talk to the intake line — live voice, no hold music.</li>
                <li>Evidence-based questions: symptoms, history, insurance.</li>
                <li>See nearby options with your estimated cost, before you hang up.</li>
              </ul>
              <p className="mt-5 text-sm font-bold text-amber-700 group-hover:underline">
                Try the patient side →
              </p>
            </Link>
            <Link
              href="/worklist"
              className="group rounded-2xl border border-slate-200 bg-slate-50/60 p-8 transition-colors hover:border-slate-300 hover:bg-slate-50"
            >
              <p className="text-xs font-bold uppercase tracking-widest text-slate-500">
                For the clinic
              </p>
              <h3 className="mt-3 text-2xl font-bold tracking-tight">
                A queue that argues its case.
              </h3>
              <ul className="mt-4 space-y-2 text-sm leading-relaxed text-slate-600">
                <li>Every verdict shows the rule that fired and the study behind it.</li>
                <li>Insurance matched, prior auth drafted, payer chased.</li>
                <li>Nothing books or sends without a named human&apos;s signature.</li>
              </ul>
              <p className="mt-5 text-sm font-bold text-slate-700 group-hover:underline">
                Open the clinic side →
              </p>
            </Link>
          </div>
        </section>

        {/* Slide 4b — how we triage: the receipt */}
        <section className="border-t border-slate-100 py-24">
          <Kicker>How we triage — one real case</Kicker>
          <h2 className="mt-6 max-w-2xl text-3xl font-bold leading-tight tracking-tight sm:text-4xl">
            Every verdict is a receipt, not a vibe.
          </h2>
          <div className="mt-10 overflow-hidden rounded-xl border border-slate-200">
            {[
              {
                k: "Facts extracted",
                v: "Age 42 · rectal bleeding, 3 weeks · change in bowel habit. The AI reads; it adds nothing.",
              },
              {
                k: "Rule fired",
                v: "Under 50 + bleeding + a second red flag → URGENT. Threshold measured on 2,093 real patients (Hamilton 2005; NICE NG12) — the citation shows in the app.",
              },
              {
                k: "Fail-safe",
                v: "Anything missing or unclear routes to a human. There is no code path that tells a patient they're fine.",
              },
              {
                k: "Insurance matched",
                v: "Plan identified · prior auth required → packet drafts itself · estimated patient share shown up front. Coverage can never change urgency — money never outranks medicine.",
              },
              {
                k: "Human signs",
                v: "Nurse approves → slot books to the calendar. Physician approves → prior auth goes out, and the agent chases the payer by phone.",
              },
            ].map((row, i) => (
              <div
                key={row.k}
                className="grid gap-1 border-t border-slate-100 px-6 py-5 first:border-t-0 sm:grid-cols-[12rem_1fr] sm:gap-6"
              >
                <p className="text-sm font-bold">
                  <span className="mr-2 text-amber-500">{i + 1}</span>
                  {row.k}
                </p>
                <p className="text-sm leading-relaxed text-slate-500">{row.v}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Slide 5 — one product shot */}
        <section className="border-t border-slate-100 py-24">
          <Kicker>See it</Kicker>
          <h2 className="mt-6 text-3xl font-bold tracking-tight sm:text-4xl">
            The call ends with an appointment.
          </h2>
          <figure className="mt-10">
            <div className="overflow-hidden rounded-xl border border-slate-200 shadow-xl shadow-slate-200/60">
              <Image
                src="/landing/intake-call.png"
                alt="Voice intake call booking an urgent GI slot in the same call"
                width={1440}
                height={900}
                className="w-full"
              />
            </div>
            <figcaption className="mt-4 text-center text-sm text-slate-400">
              A 42-year-old written off as &quot;probable hemorrhoids&quot; — flagged
              urgent, booked on the call. The voice physically cannot say a
              diagnosis.
            </figcaption>
          </figure>
        </section>

        {/* Slide 6 — proof, plain language */}
        <section className="border-t border-slate-100 py-24">
          <Kicker>Why trust it</Kicker>
          <div className="mt-12 grid gap-10 sm:grid-cols-3">
            <div>
              <p className="text-6xl font-bold tracking-tight">100%</p>
              <p className="mt-2 text-sm text-slate-500">
                of urgent cases flagged in testing — and zero patients falsely
                told they&apos;re fine.
              </p>
            </div>
            <div>
              <p className="text-6xl font-bold tracking-tight">2,093</p>
              <p className="mt-2 text-sm text-slate-500">
                real patients behind the thresholds (Hamilton 2005; NICE) —
                every rule cites its study, inside the product.
              </p>
            </div>
            <div>
              <p className="text-6xl font-bold tracking-tight">&lt;1s</p>
              <p className="mt-2 text-sm text-slate-500">
                from arrival to a cited triage verdict — against an industry
                baseline measured in days on a fax pile.
              </p>
            </div>
          </div>
        </section>

        {/* Slide 7 — close */}
        <section className="flex min-h-[50vh] flex-col items-center justify-center border-t border-slate-100 text-center">
          <p className="max-w-3xl text-3xl font-bold leading-snug tracking-tight sm:text-5xl">
            We don&apos;t diagnose anyone.
            <br />
            We make sure the right people get scoped.
          </p>
          <div className="mt-10 flex gap-4">
            <Link
              href="/intake"
              className="rounded-full bg-slate-900 px-6 py-3 text-sm font-bold text-white hover:bg-slate-700"
            >
              Try the demo
            </Link>
            <Link
              href="/worklist"
              className="rounded-full border border-slate-300 px-6 py-3 text-sm font-bold text-slate-600 hover:border-slate-500"
            >
              See the worklist
            </Link>
          </div>
        </section>
      </main>

      <footer className="border-t border-slate-100">
        <div className="mx-auto flex max-w-4xl flex-col items-center justify-between gap-2 px-6 py-8 text-[11px] font-bold uppercase tracking-widest text-slate-400 sm:flex-row">
          <span>Meridian — the end of &ldquo;please hold&rdquo; · demo · synthetic data</span>
          <span>AI reads · rules decide · people sign</span>
        </div>
      </footer>
    </div>
  );
}
