import { timingSafeEqual } from "node:crypto";

export const runtime = "nodejs";
export const maxDuration = 300;

const ROLES = new Set([
  "research-scout", "source-scanner", "test-runner", "pattern-miner",
  "validation-reviewer", "documentation-auditor", "regression-watcher",
  "intelligence-synthesizer",
]);

function authorized(request: Request) {
  const expected = process.env.HACKERCODERAI_ACCESS_KEY || "";
  const supplied = request.headers.get("x-hackercoderai-key") || "";
  if (!expected || !supplied) return false;
  const a = Buffer.from(expected), b = Buffer.from(supplied);
  return a.length === b.length && timingSafeEqual(a, b);
}

function providers() {
  return [
    { name: "hf-space-a", url: process.env.HF_WORKER_A_URL || "" },
    { name: "hf-space-b", url: process.env.HF_WORKER_B_URL || "" },
  ].filter((p) => p.url.startsWith("https://"));
}

function hfHeaders(json = false) {
  const headers: Record<string, string> = {};
  if (json) headers["Content-Type"] = "application/json";
  const token = process.env.HF_WORKER_TOKEN || "";
  if (token) headers.Authorization = "Bearer " + token;
  return headers;
}

function extractGradioOutput(raw: string) {
  const events = raw.split(/\r?\n/).filter((line) => line.startsWith("data:"));
  for (const event of events.reverse()) {
    const value = event.slice(5).trim();
    if (!value || value === "[DONE]") continue;
    try {
      const parsed = JSON.parse(value);
      if (Array.isArray(parsed)) return parsed[0];
      if (parsed?.output?.data) return parsed.output.data[0];
      if (parsed?.data) return parsed.data[0] ?? parsed.data;
      return parsed;
    } catch { /* try the previous event */ }
  }
  return null;
}

export async function GET() {
  const configured = providers();
  const status = await Promise.all(configured.map(async (provider) => {
    try {
      const response = await fetch(provider.url.replace(/\/$/, "") + "/gradio_api/info", {
        headers: hfHeaders(), signal: AbortSignal.timeout(10000), cache: "no-store",
      });
      return { name: provider.name, status: response.ok ? "healthy" : "unavailable" };
    } catch {
      return { name: provider.name, status: "sleeping-or-unreachable" };
    }
  }));
  return Response.json({
    ok: true, providerCount: configured.length, configured: configured.length > 0,
    authConfigured: Boolean(process.env.HACKERCODERAI_ACCESS_KEY),
    providers: status,
    note: configured.length ? "Gradio API schema health checks are best-effort." : "No Hugging Face Space URLs configured.",
  });
}

export async function POST(request: Request) {
  if (!authorized(request)) return Response.json({ error: "Access denied." }, { status: 401 });

  let body: { role?: string; goal?: string };
  try { body = await request.json(); } catch { return Response.json({ error: "Send valid JSON." }, { status: 400 }); }
  const role = body.role || "";
  const goal = typeof body.goal === "string" ? body.goal : "Review this repository for safe, authorized improvements.";
  if (!ROLES.has(role)) return Response.json({ error: "Role must be one of the eight fixed Qill worker roles." }, { status: 400 });
  if (goal.length > 1500) return Response.json({ error: "Goal must be 1,500 characters or fewer." }, { status: 400 });

  const pool = providers();
  if (!pool.length) return Response.json({ error: "No Hugging Face Spaces configured. Set HF_WORKER_A_URL and optionally HF_WORKER_B_URL in Vercel." }, { status: 503 });

  const attempts: Array<{ provider: string; status: number | string }> = [];
  for (const provider of pool) {
    const base = provider.url.replace(/\/$/, "");
    let eventId = "";
    try {
      const submit = await fetch(base + "/gradio_api/call/run_qill_worker", {
        method: "POST", headers: hfHeaders(true),
        body: JSON.stringify({ data: [role, goal] }),
        signal: AbortSignal.timeout(20000), cache: "no-store",
      });
      if (!submit.ok) {
        attempts.push({ provider: provider.name, status: submit.status });
        if (submit.status === 429 || submit.status === 503) continue;
        const detail = await submit.text();
        return Response.json({ error: "Space rejected the task; no failover attempted.", provider: provider.name, detail: detail.slice(0, 800), attempts }, { status: 502 });
      }
      const accepted = await submit.json();
      eventId = typeof accepted.event_id === "string" ? accepted.event_id : "";
      if (!eventId) return Response.json({ error: "Space accepted an unexpected Gradio response. Task was not replayed.", provider: provider.name, attempts }, { status: 502 });

      // Once a Gradio event ID exists, the task may be running. Never replay it to another provider.
      const poll = await fetch(base + "/gradio_api/call/run_qill_worker/" + encodeURIComponent(eventId), {
        headers: hfHeaders(), signal: AbortSignal.timeout(270000), cache: "no-store",
      });
      if (!poll.ok) return Response.json({ error: "Task was accepted, but its result could not be retrieved. Do not resubmit until checking the Space.", provider: provider.name, status: poll.status, attempts }, { status: 502 });
      const output = extractGradioOutput(await poll.text());
      if (output === null) return Response.json({ error: "Gradio returned no completed result. Check the Space directly before retrying.", provider: provider.name, attempts }, { status: 502 });
      if (output?.ok === false) return Response.json({ error: output.error || "Worker reported an error.", provider: provider.name, result: output, attempts }, { status: 502 });
      return Response.json({ ok: true, dispatchedTo: provider.name, attempts, result: output });
    } catch (error) {
      if (eventId) return Response.json({ error: "Task was accepted but polling failed; it was not replayed to avoid duplicate execution.", provider: provider.name, attempts }, { status: 504 });
      if (error instanceof Error && error.name === "TimeoutError") {
        return Response.json({ error: "Space submission timed out; task acceptance is uncertain, so it was not replayed.", provider: provider.name, attempts }, { status: 504 });
      }
      attempts.push({ provider: provider.name, status: "unreachable-before-acceptance" });
    }
  }
  return Response.json({ error: "All configured free Spaces are unavailable or quota-limited. Retry after a Space wakes or its quota resets.", attempts }, { status: 503 });
}
