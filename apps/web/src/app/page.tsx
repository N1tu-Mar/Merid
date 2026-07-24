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

const STEPS = [
  {
    n: "1",
    title: "A fax or a phone call arrives",
    body: "The two ways every GI referral shows up today. No new software for the referring doctor, no portal for the patient.",
  },
  {
    n: "2",
    title: "AI reads it — facts only",
    body: "Inside a locked, throwaway sandbox. It pulls out age, symptoms, duration. It has no opinions and no authority.",
  },
  {
    n: "3",
    title: "Rules set how fast",
    body: "Ten auditable rules, thresholds measured on 2,093 real patients. Every verdict shows exactly which rule fired and the study behind it.",
  },
  {
    n: "4",
    title: "A nurse clicks approve",
    body: "The appointment books, lands on the calendar, and the patient hears back — same day, not week six.",
  },
  {
    n: "5",
    title: "The paperwork fights itself",
    body: "Prior auth drafts with every sentence sourced. The doctor signs. The agent dials the payer's phone tree and sits through the hold music.",
  },
];

export default function Home() {
  return (
    <div className="min-h-screen bg-white text-slate-900 selection:bg-amber-100">
      <DemoBanner />

      <header>
        <nav className="mx-auto flex max-w-4xl items-center justify-between px-6 py-6">
          <span className="text-lg font-bold tracking-tight">
            Meridian
            <span className="ml-3 hidden text-xs font-normal normal-case tracking-normal text-slate-400 sm:inline">
              books the scope · never plays doctor
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
            <span className="text-slate-400">&ldquo;Please hold.&rdquo;</span>
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
          <div className="mt-12 space-y-0">
            {STEPS.map((s) => (
              <div
                key={s.n}
                className="grid gap-2 border-t border-slate-100 py-7 first:border-t-0 sm:grid-cols-[4rem_16rem_1fr] sm:gap-6"
              >
                <span className="text-2xl font-bold text-amber-500">{s.n}</span>
                <h3 className="font-bold">{s.title}</h3>
                <p className="text-sm leading-relaxed text-slate-500">{s.body}</p>
              </div>
            ))}
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
              <p className="text-6xl font-bold tracking-tight">0</p>
              <p className="mt-2 text-sm text-slate-500">
                models trained on patient data — that&apos;s the point. The
                medicine lives in rules you can read, not weights you can&apos;t.
              </p>
            </div>
          </div>
        </section>

        {/* Slide 6b — the stack, each doing a real job */}
        <section className="border-t border-slate-100 py-24">
          <Kicker>Built on</Kicker>
          <h2 className="mt-6 max-w-2xl text-3xl font-bold leading-tight tracking-tight sm:text-4xl">
            Five tools. Each one load-bearing.
          </h2>
          <div className="mt-10">
            {[
              {
                name: "Daytona",
                job: "Every fax is opened inside a throwaway, internet-blocked sandbox that's destroyed seconds later — hostile documents never touch our system. The worklist shows each sandbox ID as proof.",
              },
              {
                name: "Fireworks AI",
                job: "Reads messy referral text into structured facts in about a second. We raced two of their models on the same gold referrals and kept the winner — the choice ships with its scorecard.",
              },
              {
                name: "ElevenLabs",
                job: "Both phone legs: the patient intake line (talk to it live on the demo) and the payer hold-music call. Every spoken word passes the no-diagnosis filter before it reaches the voice.",
              },
              {
                name: "Braintrust",
                job: "Every live decision streams a replayable trace, and our test suite grades the system on every change: 100% of urgent cases caught, zero patients falsely reassured.",
              },
              {
                name: "CopilotKit",
                job: "The clinic-side copilot in the worklist — drafts the calendar event and the Slack note to the care team; a human still clicks send.",
              },
            ].map((s) => (
              <div
                key={s.name}
                className="grid gap-1 border-t border-slate-100 py-6 first:border-t-0 sm:grid-cols-[12rem_1fr] sm:gap-6"
              >
                <p className="font-bold">{s.name}</p>
                <p className="text-sm leading-relaxed text-slate-500">{s.job}</p>
              </div>
            ))}
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
          <span>Meridian — demo · synthetic data · not for clinical use</span>
          <span>AI reads · rules decide · people sign</span>
        </div>
      </footer>
    </div>
  );
}
