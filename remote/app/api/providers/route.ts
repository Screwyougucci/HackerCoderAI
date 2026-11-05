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
  const token = process.env.HF_WORKER_TOKEN || "";
  return [
    { name: "hf-space-a", url: process.env.HF_WORKER_A_URL || "" },
    { name: "hf-space-b", url: process.env.HF_WORKER_B_URL || "" },
  ].filter((p) => p.url.startsWith("https://") && token);
}

export async function GET() {
  const configured = providers();
  const status = await Promise.all(configured.map(async (provider) => {
    try {
      const response = await fetch(provider.url.replace(/\/$/, "") + "/health", {
        signal: AbortSignal.timeout(8000), cache: "no-store",
      });
      const details = response.ok ? await response.json() : null;
      return { name: provider.name, status: response.ok ? "healthy" : "unavailable", details };
    } catch {
      return { name: provider.name, status: "sleeping-or-unreachable" };
    }
  }));
  return Response.json({
    ok: true, providerCount: configured.length, configured: configured.length > 0,
    authConfigured: Boolean(process.env.HF_WORKER_TOKEN), providers: status,
    note: configured.length ? "Health checks are best-effort." : "No Hugging Face worker URLs and token configured.",
  });
}

export async function POST(request: Request) {
  if (!authorized(request)) return Response.json({ error: "Access denied." }, { status: 401 });
  const token = process.env.HF_WORKER_TOKEN || "";
  if (!token) return Response.json({ error: "HF_WORKER_TOKEN is not configured in Vercel." }, { status: 503 });

  let body: { role?: string; goal?: string };
  try { body = await request.json(); } catch { return Response.json({ error: "Send valid JSON." }, { status: 400 }); }
  const role = body.role || "";
  const goal = typeof body.goal === "string" ? body.goal : "Review this repository for safe, authorized improvements.";
  if (!ROLES.has(role)) return Response.json({ error: "Role must be one of the eight fixed Qill worker roles." }, { status: 400 });
  if (goal.length > 1500) return Response.json({ error: "Goal must be 1,500 characters or fewer." }, { status: 400 });

  const pool = providers();
  if (!pool.length) return Response.json({ error: "No Hugging Face workers configured. Set HF_WORKER_A_URL, optionally HF_WORKER_B_URL, and HF_WORKER_TOKEN." }, { status: 503 });

  const attempts: Array<{ provider: string; status: number | string }> = [];
  for (const provider of pool) {
    try {
      const response = await fetch(provider.url.replace(/\/$/, "") + "/run", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Qill-Worker-Key": token },
        body: JSON.stringify({ role, goal }),
        signal: AbortSignal.timeout(270000), cache: "no-store",
      });
      if (response.ok) return Response.json({ ok: true, dispatchedTo: provider.name, attempts, ...(await response.json()) });
      attempts.push({ provider: provider.name, status: response.status });
      if (response.status !== 429 && response.status !== 503) {
        const detail = await response.text();
        return Response.json({ error: "Worker rejected the task; no failover attempted.", provider: provider.name, status: response.status, detail: detail.slice(0, 800), attempts }, { status: 502 });
      }
    } catch (error) {
      if (error instanceof Error && error.name === "TimeoutError") {
        attempts.push({ provider: provider.name, status: "timeout-not-retried" });
        return Response.json({ error: "Worker timed out; task was not replayed to avoid duplicate execution.", attempts }, { status: 504 });
      }
      attempts.push({ provider: provider.name, status: "unreachable" });
    }
  }
  return Response.json({ error: "All configured free Spaces are unavailable or quota-limited. Retry after a Space wakes or quota resets.", attempts }, { status: 503 });
}
