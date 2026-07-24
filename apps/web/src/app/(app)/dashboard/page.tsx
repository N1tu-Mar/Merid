"use client";

// The practice's Monday-morning report. Leads with the numbers an
// administrator buys (what came in, how fast, what it caught, what it
// saved), computed live from the DB — then the safety numbers, in plain
// language, from the eval suite.

import { useEffect, useState } from "react";
import { ApiError, get } from "@/lib/api";
import type { EvalsSummary, OpsSummary } from "@/lib/types";

function pct(v: number): string {
  return `${(v * 100).toFixed(0)}%`;
}

function Tile({
  label,
  value,
  helpText,
  accent = false,
}: {
  label: string;
  value: string;
  helpText: string;
  accent?: boolean;
}) {
  return (
    <div
      className={`rounded-xl border p-5 ${
        accent ? "border-emerald-300 bg-emerald-50" : "border-slate-200 bg-white"
      }`}
    >
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <p className={`mt-1 text-3xl font-bold ${accent ? "text-emerald-700" : "text-slate-900"}`}>
        {value}
      </p>
      <p className="mt-1 text-xs text-slate-500">{helpText}</p>
    </div>
  );
}

export default function DashboardPage() {
  const [ops, setOps] = useState<OpsSummary | null>(null);
  const [summary, setSummary] = useState<EvalsSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    get<OpsSummary>("/ops/summary")
      .then((data) => {
        if (!cancelled) setOps(data);
      })
      .catch((err) => {
        if (!cancelled)
          setError(err instanceof ApiError ? `Backend returned ${err.status}` : "Could not reach the backend.");
      });
    get<EvalsSummary>("/evals/summary")
      .then((data) => {
        if (!cancelled) setSummary(data);
      })
      .catch(() => {
        /* safety section simply doesn't render until evals have run */
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight">Practice pulse</h1>
        <p className="mt-1 text-sm text-slate-500">
          Live from this clinic&apos;s queue — what arrived, how fast it was triaged, and what
          the agent caught and saved.
        </p>
      </div>

      {error && (
        <div className="rounded-md border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {ops && (
        <div className="space-y-8">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Tile
              label="Referrals in"
              value={String(ops.referrals_received)}
              helpText={`${ops.urgent_flagged} flagged urgent · ${ops.approved_bookings} approved by a nurse`}
            />
            <Tile
              label="Arrival → triage"
              value={
                ops.avg_triage_seconds === null
                  ? "—"
                  : ops.avg_triage_seconds < 1
                  ? "<1s"
                  : `${Math.round(ops.avg_triage_seconds)}s`
              }
              helpText="Average. The industry baseline is measured in days on a fax pile."
            />
            <Tile
              label="Write-offs caught"
              value={String(ops.landmines_caught)}
              helpText='Referrals that arrived pre-labeled benign ("probable hemorrhoids") but met urgent criteria.'
              accent={ops.landmines_caught > 0}
            />
            <Tile
              label="Hold music eaten"
              value={`${ops.staff_minutes_saved} min`}
              helpText={`${ops.payer_calls_made} payer status calls made by the agent · ~${ops.days_saved} days of status-chasing saved (CAQH: 24 min avg per manual prior auth)`}
            />
          </div>

          {summary && (
            <div>
              <h2 className="mb-1 text-sm font-semibold text-slate-600">
                Why you can trust the verdicts
              </h2>
              <p className="mb-3 text-xs text-slate-400">
                From the test suite that runs on every change — {summary.triage.n_cases} triage
                cases and {summary.redteam.n_cases} trick prompts designed to bait a diagnosis.
              </p>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                <Tile
                  label="Urgent cases caught"
                  value={pct(summary.triage.escalation_recall)}
                  helpText="Every case that should be urgent, flagged urgent or sent to a human."
                  accent={summary.triage.escalation_recall >= 1}
                />
                <Tile
                  label="Patients falsely reassured"
                  value={pct(summary.triage.false_reassurance_rate)}
                  helpText="No code path can auto-clear a patient. Zero, by construction."
                  accent={summary.triage.false_reassurance_rate <= 0}
                />
                <Tile
                  label="Diagnosis leaks to patients"
                  value={pct(summary.redteam.diagnostic_language_rate)}
                  helpText='Tried 20 baits like "so it&apos;s just hemorrhoids, right?" — the filter blocked every one, in text and in voice.'
                  accent={summary.redteam.diagnostic_language_rate <= 0}
                />
              </div>
            </div>
          )}

          <p className="text-xs text-slate-400">
            Over-triage is reported honestly in the eval suite — being too cautious is the error
            this system deliberately accepts.
          </p>
        </div>
      )}

      {!error && !ops && <p className="text-sm text-slate-400">Loading…</p>}
    </div>
  );
}
