import Image from "next/image";
import Link from "next/link";
import { Newsreader } from "next/font/google";
import DemoBanner from "@/components/DemoBanner";

// Landing page as a pitch, not a website: white, one idea per screen,
// numbers over paragraphs. Every stat is verified against a primary source
// in docs/FACTS.md — nothing renders here that isn't on that sheet.

const newsreader = Newsreader({
  subsets: ["latin"],
  style: ["normal", "italic"],
  weight: ["400", "500"],
  variable: "--font-newsreader",
});

const serif = "font-[family-name:var(--font-newsreader)]";

function Kicker({ children }: { children: React.ReactNode }) {
  return (
    <p className="font-mono text-[11px] font-medium uppercase tracking-[0.3em] text-slate-400">
      {children}
    </p>
  );
}

export default function Home() {
  return (
    <div className={`${newsreader.variable} min-h-screen bg-white text-slate-900 selection:bg-amber-100`}>
      <DemoBanner />

      <header>
        <nav className="mx-auto flex max-w-4xl items-center justify-between px-6 py-6">
          <span className={`${serif} text-xl`}>Meridian</span>
          <div className="flex items-center gap-6 text-sm text-slate-500">
            <Link href="/intake" className="hover:text-slate-900">Intake Line</Link>
            <Link href="/worklist" className="hover:text-slate-900">Worklist</Link>
            <Link href="/dashboard" className="hover:text-slate-900">Dashboard</Link>
          </div>
        </nav>
      </header>

      <main className="mx-auto max-w-4xl px-6">
        {/* Slide 1 — the story */}
        <section className="flex min-h-[85vh] flex-col justify-center">
          <Kicker>Referral triage, not diagnosis</Kicker>
          <h1 className={`${serif} mt-8 text-5xl leading-[1.1] tracking-tight sm:text-7xl`}>
            A 42-year-old with rectal bleeding is told it&apos;s{" "}
            <em>probably hemorrhoids.</em>
          </h1>
          <p className="mt-8 max-w-xl text-lg text-slate-500">
            Meridian makes that miss impossible — and books the colonoscopy
            before the call ends.
          </p>
          <div className="mt-10 flex items-center gap-6">
            <Link
              href="/intake"
              className="rounded-full bg-slate-900 px-6 py-3 text-sm font-medium text-white hover:bg-slate-700"
            >
              Hear the call
            </Link>
            <span className="text-sm text-slate-400">3-minute live demo</span>
          </div>
        </section>

        {/* Slide 2 — the problem, one number at a time */}
        <section className="border-t border-slate-100 py-28">
          <Kicker>The problem</Kicker>
          <h2 className={`${serif} mt-6 text-4xl tracking-tight sm:text-5xl`}>
            The failure isn&apos;t medicine. <em>It&apos;s routing.</em>
          </h2>
          <div className="mt-16 space-y-14">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-baseline sm:gap-10">
              <span className={`${serif} min-w-[14rem] text-6xl tracking-tight`}>3 in 4</span>
              <p className="max-w-md text-slate-500">
                colorectal cancers in adults under 50 are caught at an advanced
                stage — incidence is rising 3% a year.
              </p>
            </div>
            <div className="flex flex-col gap-2 sm:flex-row sm:items-baseline sm:gap-10">
              <span className={`${serif} min-w-[14rem] text-6xl tracking-tight`}>91% → 17%</span>
              <p className="max-w-md text-slate-500">
                five-year survival, caught early versus late. Timing is the
                outcome.
              </p>
            </div>
            <div className="flex flex-col gap-2 sm:flex-row sm:items-baseline sm:gap-10">
              <span className={`${serif} min-w-[14rem] text-6xl tracking-tight`}>40 days</span>
              <p className="max-w-md text-slate-500">
                average wait for a GI appointment — the longest of any
                specialty. The fax queue, phone tag, and prior auth are the
                delay.
              </p>
            </div>
          </div>
        </section>

        {/* Slide 3 — the market */}
        <section className="border-t border-slate-100 py-28">
          <Kicker>The market</Kicker>
          <h2 className={`${serif} mt-6 max-w-2xl text-4xl leading-tight tracking-tight sm:text-5xl`}>
            Two-thirds of referrals never become <em>completed visits.</em>
          </h2>
          <p className="mt-8 max-w-xl text-lg text-slate-500">
            Every one a GI practice recovers is a four-figure procedure it
            already owns. Meridian converts the queue: referral to booked in
            minutes, prior auth drafted, payer chased — while staff time on
            hold goes to zero.
          </p>
        </section>

        {/* Slide 4 — how */}
        <section className="border-t border-slate-100 py-28">
          <Kicker>How</Kicker>
          <h2 className={`${serif} mt-6 text-4xl tracking-tight sm:text-5xl`}>
            Models read. Rules decide. <em>People sign.</em>
          </h2>
          <div className="mt-14 grid gap-10 sm:grid-cols-3">
            <div>
              <p className="font-mono text-xs text-amber-600">01</p>
              <p className="mt-3 text-slate-600">
                AI reads the fax and the phone call — inside a destroyed-on-exit
                sandbox. It extracts facts. It has no opinions.
              </p>
            </div>
            <div>
              <p className="font-mono text-xs text-amber-600">02</p>
              <p className="mt-3 text-slate-600">
                Ten auditable rules set the urgency — thresholds measured on
                2,093 real patients, cited line by line.
              </p>
            </div>
            <div>
              <p className="font-mono text-xs text-amber-600">03</p>
              <p className="mt-3 text-slate-600">
                A nurse signs every booking. A physician signs every prior
                auth. The agent does the waiting, not the deciding.
              </p>
            </div>
          </div>
        </section>

        {/* Slide 5 — one product shot */}
        <section className="border-t border-slate-100 py-28">
          <Kicker>The demo</Kicker>
          <h2 className={`${serif} mt-6 text-4xl tracking-tight sm:text-5xl`}>
            The call ends with an <em>appointment.</em>
          </h2>
          <figure className="mt-12">
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
              Live: the 42-year-old&apos;s call, audible, booked urgent — and the
              voice physically cannot say a diagnosis.
            </figcaption>
          </figure>
        </section>

        {/* Slide 6 — proof */}
        <section className="border-t border-slate-100 py-28">
          <Kicker>Proof, not promises</Kicker>
          <div className="mt-10 grid gap-12 sm:grid-cols-3">
            <div>
              <p className={`${serif} text-6xl tracking-tight`}>100%</p>
              <p className="mt-2 text-sm text-slate-500">
                escalation recall — every should-be-urgent case flagged
              </p>
            </div>
            <div>
              <p className={`${serif} text-6xl tracking-tight`}>0</p>
              <p className="mt-2 text-sm text-slate-500">
                patients falsely reassured — no code path auto-clears anyone
              </p>
            </div>
            <div>
              <p className={`${serif} text-6xl tracking-tight`}>2,093</p>
              <p className="mt-2 text-sm text-slate-500">
                real patients behind the rule thresholds — every rule cites its
                study in the UI
              </p>
            </div>
          </div>
          <p className="mt-14 max-w-xl text-slate-500">
            Every decision streams a replayable trace. The extraction model was
            chosen by a measured A/B, not a vibe. Every number on this page has
            a primary source.
          </p>
        </section>

        {/* Slide 7 — close */}
        <section className="flex min-h-[60vh] flex-col items-center justify-center border-t border-slate-100 text-center">
          <p className={`${serif} max-w-3xl text-4xl leading-snug tracking-tight sm:text-5xl`}>
            We don&apos;t diagnose. We make sure the right people{" "}
            <em>get scoped.</em>
          </p>
          <div className="mt-10 flex gap-4">
            <Link
              href="/intake"
              className="rounded-full bg-slate-900 px-6 py-3 text-sm font-medium text-white hover:bg-slate-700"
            >
              Try the demo
            </Link>
            <Link
              href="/dashboard"
              className="rounded-full border border-slate-300 px-6 py-3 text-sm font-medium text-slate-600 hover:border-slate-500"
            >
              See the evals
            </Link>
          </div>
        </section>
      </main>

      <footer className="border-t border-slate-100">
        <div className="mx-auto flex max-w-4xl flex-col items-center justify-between gap-2 px-6 py-8 font-mono text-[11px] tracking-wide text-slate-400 sm:flex-row">
          <span>MERIDIAN — DEMO. SYNTHETIC DATA. NOT FOR CLINICAL USE.</span>
          <span>MODELS READ · RULES DECIDE · PEOPLE SIGN</span>
        </div>
      </footer>
    </div>
  );
}
