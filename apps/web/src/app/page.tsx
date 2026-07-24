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
            Cancer still travels
            <br />
            <span className="text-slate-400">by fax.</span>
          </h1>
          <p className="mt-8 max-w-xl text-lg leading-relaxed text-slate-500">
            Referrals sit in fax queues and phone tag while early-stage becomes
            late-stage. Meridian answers the phone, reads the fax, and books
            the colonoscopy in minutes — a human signs every step, and it
            never, ever diagnoses.
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
