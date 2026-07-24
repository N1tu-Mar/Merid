"use client";

// Role strip under the nav: makes the two-sided demo legible. Every app
// page belongs to either the patient's journey or the doctor's, and the
// strip shows which side you're on and where this page sits in that flow.
// Prior auth lives here as a doctor-side step rather than a top-level nav
// item — it's part of the clinic's journey, not a separate product.

import Link from "next/link";
import { usePathname } from "next/navigation";

const DOCTOR_STEPS = [
  { href: "/worklist", label: "Triage queue" },
  { href: "/pa-packets", label: "Prior auth & payer" },
  { href: "/dashboard", label: "Practice pulse" },
];

const PATIENT_STEPS = ["Call the line", "Answer the questions", "Pick a slot, see the cost"];

export default function FlowStrip() {
  const pathname = usePathname() ?? "";
  const isPatient = pathname.startsWith("/intake");
  const isDoctor =
    pathname.startsWith("/worklist") ||
    pathname.startsWith("/pa-packets") ||
    pathname.startsWith("/dashboard");

  if (!isPatient && !isDoctor) return null;

  return (
    <div className="w-full border-b border-slate-100 bg-white">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-3 gap-y-1 px-4 py-2 text-xs sm:px-6">
        <span
          className={`rounded-full px-2 py-0.5 font-bold uppercase tracking-wider ${
            isPatient ? "bg-amber-100 text-amber-700" : "bg-slate-900 text-white"
          }`}
        >
          {isPatient ? "Patient side" : "Doctor side"}
        </span>
        {isPatient
          ? PATIENT_STEPS.map((s, i) => (
              <span key={s} className="flex items-center gap-3 text-slate-500">
                {i > 0 && <span className="text-slate-300">→</span>}
                <span>
                  <span className="mr-1 font-bold text-amber-500">{i + 1}</span>
                  {s}
                </span>
              </span>
            ))
          : DOCTOR_STEPS.map((s, i) => {
              const active = pathname.startsWith(s.href);
              return (
                <span key={s.href} className="flex items-center gap-3">
                  {i > 0 && <span className="text-slate-300">→</span>}
                  <Link
                    href={s.href}
                    className={
                      active
                        ? "font-bold text-slate-900"
                        : "text-slate-500 hover:text-slate-900"
                    }
                  >
                    <span className={`mr-1 font-bold ${active ? "text-amber-500" : "text-slate-300"}`}>
                      {i + 1}
                    </span>
                    {s.label}
                  </Link>
                </span>
              );
            })}
        <span className="ml-auto hidden text-slate-400 sm:inline">
          {isPatient ? (
            <Link href="/worklist" className="hover:text-slate-600">
              switch to doctor side →
            </Link>
          ) : (
            <Link href="/intake" className="hover:text-slate-600">
              switch to patient side →
            </Link>
          )}
        </span>
      </div>
    </div>
  );
}
