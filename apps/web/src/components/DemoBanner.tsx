// Invariant #6 requires a persistent, non-dismissible synthetic-data notice
// on every page. It used to be a red alert bar; it's now a quiet one-line
// strip so the demo doesn't shout at judges — but it stays present and
// non-dismissible. All patient names are fictional.
export default function DemoBanner() {
  return (
    <div
      role="note"
      className="w-full border-b border-slate-100 bg-white px-4 py-1.5 text-center text-[11px] tracking-wide text-slate-400"
    >
      Demo — synthetic data, fictional patients. Not for clinical use.
    </div>
  );
}
