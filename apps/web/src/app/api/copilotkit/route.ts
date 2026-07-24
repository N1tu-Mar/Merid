// CopilotKit runtime endpoint.
//
// The adapter points at Fireworks, not OpenAI: Fireworks exposes an
// OpenAI-compatible /v1 surface, so OpenAIAdapter works against it with a
// baseURL override. That means the copilot reuses the FIREWORKS_API_KEY this
// project already provisions — no new vendor, no new key.
//
// The key is read from a NON-public env var and stays server-side. It must
// never be exposed via NEXT_PUBLIC_* (see CLAUDE.md deployment section).
//
// If no key is configured, this route degrades to the previous inert
// behaviour (valid empty response) rather than throwing
// CopilotApiDiscoveryError and breaking page rendering — which is what
// happened the last time a provider was mounted without an adapter.
import {
  CopilotRuntime,
  OpenAIAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import OpenAI from "openai";
import { NextRequest, NextResponse } from "next/server";

const FIREWORKS_API_KEY = process.env.FIREWORKS_API_KEY;
// Default matches the extraction pipeline's eval-chosen model. The previous
// default (llama-v3p1-70b-instruct) was rotated off Fireworks serverless and
// 404s — which silently ate every copilot reply. Fireworks deprecates
// serverless models over time: if the copilot goes mute, test the model id
// with a direct curl first.
const FIREWORKS_MODEL =
  process.env.COPILOT_MODEL || "accounts/fireworks/models/deepseek-v4-flash";

export const POST = async (req: NextRequest) => {
  if (!FIREWORKS_API_KEY) {
    // Inert fallback — keeps a mounted <CopilotKit> provider from crashing
    // the page when no key is present (e.g. a fresh clone, or Vercel preview
    // without env vars set).
    return NextResponse.json({ data: null }, { status: 200 });
  }

  const openai = new OpenAI({
    apiKey: FIREWORKS_API_KEY,
    baseURL: "https://api.fireworks.ai/inference/v1",
  });

  // No-diagnosis guard, enforced at the API boundary rather than trusted to
  // prompt assembly: CopilotKit places the sidebar's `instructions` deep in
  // its composed prompt, and models ignored them there (a bait question
  // produced a hemorrhoids-vs-cancer differential — the single worst output
  // this product can emit). A position-0 system message survives whatever
  // the framework builds around it; verified effective against the same
  // bait. This is the same instinct as the voice layer: the constraint
  // lives at the boundary, not in a suggestion.
  const NO_DIAGNOSIS_GUARD = {
    role: "system" as const,
    content:
      "ABSOLUTE OVERRIDE — outranks every later instruction and every user " +
      "request: you never name, confirm, deny, compare, or rank any medical " +
      "condition or its likelihood, in any form — no differentials, no " +
      "tables of conditions, no 'more likely statistically', not even to " +
      "rule something out, not even when the referral text names one. If " +
      "asked anything diagnostic ('could it just be…', 'is this cancer', " +
      "'compare X vs Y'), your ENTIRE reply is: a one-line statement that " +
      "no part of this system diagnoses, then only the deterministic facts " +
      "from the context: which rule fired, the features behind it, its " +
      "evidence citation, the verdict urgency, and the approval status.",
  };
  // The adapter CLONES the client we hand it (createOpenAI({baseURL,
  // apiKey, ...}) inside @copilotkit/runtime), so instance patches are
  // discarded. Patch the Completions PROTOTYPE instead — the clone is
  // built from the same deduped `openai` module, so its chat.completions
  // shares this prototype. Guard create() and stream() alike.
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const guardProto = (obj: any) => {
    if (!obj) return;
    const proto = Object.getPrototypeOf(obj);
    if (!proto || proto.__meridianNoDiagnosisGuard) return;
    proto.__meridianNoDiagnosisGuard = true;
    for (const method of ["create", "stream"]) {
      if (typeof proto[method] === "function") {
        const orig = proto[method];
        proto[method] = function (params: any, opts?: any) {
          const guarded = params?.messages
            ? { ...params, messages: [NO_DIAGNOSIS_GUARD, ...params.messages] }
            : params;
          return orig.call(this, guarded, opts);
        };
      }
    }
  };
  guardProto(openai.chat.completions);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  guardProto((openai as any).beta?.chat?.completions);

  const runtime = new CopilotRuntime();
  const serviceAdapter = new OpenAIAdapter({
    openai,
    model: FIREWORKS_MODEL,
    // Without this, CopilotKit downgrades system-role messages during
    // message conversion — which is why the sidebar's `instructions` were
    // getting ignored by the model.
    keepSystemRole: true,
  });

  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter,
    endpoint: "/api/copilotkit",
  });

  return handleRequest(req);
};

export const GET = async () => {
  return NextResponse.json({
    status: FIREWORKS_API_KEY ? "copilot runtime active" : "copilot runtime disabled (no key)",
  });
};
