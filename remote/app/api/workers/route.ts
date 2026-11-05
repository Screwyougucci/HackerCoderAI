import { timingSafeEqual } from "node:crypto";

export const runtime = "nodejs";
export const maxDuration = 30;

const OWNER = "Screwyougucci";
const REPO = "HackerCoderAI";
const WORKFLOW = "qill-workers.yml";
const API = "https://api.github.com/repos/" + OWNER + "/" + REPO;

function githubHeaders(): Record<string, string> {
  const headers: Record<string, string> = {
    Accept: "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "Qill-Distributed-Dashboard",
  };
  if (process.env.GITHUB_TOKEN) headers.Authorization = "Bearer " + process.env.GITHUB_TOKEN;
  return headers;
}
function authorized(request: Request) {
  const expectedKey = process.env.HACKERCODERAI_ACCESS_KEY || "";
  const suppliedKey = request.headers.get("x-hackercoderai-key") || "";
  if (!expectedKey || !suppliedKey) return false;
  const a = Buffer.from(expectedKey);
  const b = Buffer.from(suppliedKey);
  return a.length === b.length && timingSafeEqual(a, b);
}
async function gh(url: string, init?: RequestInit) {
  return fetch(url, { ...init, headers: { ...githubHeaders(), ...(init?.headers || {}) }, cache: "no-store" });
}

export async function GET() {
  try {
    const responses = await Promise.all([
      gh(API + "/actions/workflows/" + WORKFLOW + "/runs?per_page=8"),
      gh(API + "/actions/workflows/" + WORKFLOW),
      gh(API + "/contents/state/latest.json?ref=qill-state"),
    ]);
    const runsResponse = responses[0], workflowResponse = responses[1], stateResponse = responses[2];
    const runsData = runsResponse.ok ? await runsResponse.json() : { workflow_runs: [] };
    const workflowData = workflowResponse.ok ? await workflowResponse.json() : null;
    let checkpoint = null;
    if (stateResponse.ok) {
      const file = await stateResponse.json();
      if (typeof file.content === "string") {
        try { checkpoint = JSON.parse(Buffer.from(file.content, "base64").toString("utf8")); } catch { checkpoint = null; }
      }
    }
    return Response.json({
      ok: true,
      provider: "GitHub Actions",
      workflowState: workflowData?.state || "unknown",
      latestRun: (runsData.workflow_runs || []).slice(0, 8).map((run: any) => ({
        id: run.id, runNumber: run.run_number, status: run.status, conclusion: run.conclusion,
        event: run.event, createdAt: run.created_at, updatedAt: run.updated_at, url: run.html_url,
      })),
      checkpoint,
      freeCompute: "Public-repository standard GitHub-hosted runners",
    });
  } catch (error) {
    console.error("qill_status_failed", error);
    return Response.json({ ok: false, error: "Unable to read GitHub worker status." }, { status: 502 });
  }
}

export async function POST(request: Request) {
  if (!authorized(request)) return Response.json({ error: "Access denied. Configure the dashboard access key in Vercel." }, { status: 401 });
  if (!process.env.GITHUB_TOKEN) return Response.json({
    error: "Missing GITHUB_TOKEN. Add a fine-grained GitHub token scoped to this repository with Actions: read and write permission in Vercel.",
  }, { status: 503 });
  let body: { action?: string; goal?: string };
  try { body = await request.json(); } catch { return Response.json({ error: "Send a valid JSON request." }, { status: 400 }); }
  const action = body.action || "start";
  const workflowUrl = API + "/actions/workflows/" + WORKFLOW;
  try {
    if (action === "start") {
      const goal = typeof body.goal === "string" ? body.goal.trim() : "";
      if (goal.length > 1500) return Response.json({ error: "Goal must be 1,500 characters or fewer." }, { status: 400 });
      const response = await gh(workflowUrl + "/dispatches", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ref: "main", inputs: { goal: goal || "Review this repository for safe, authorized improvements." } }),
      });
      if (!response.ok) return Response.json({ error: "GitHub rejected the run request (" + response.status + "). Check token permissions and Actions settings." }, { status: 502 });
      return Response.json({ ok: true, message: "Qill worker cycle dispatched.", action });
    }
    if (action === "pause" || action === "resume") {
      const response = await gh(workflowUrl + "/" + (action === "pause" ? "disable" : "enable"), { method: "PUT" });
      if (!response.ok) return Response.json({ error: "GitHub could not " + action + " the workflow (" + response.status + ")." }, { status: 502 });
      return Response.json({ ok: true, message: action === "pause" ? "Scheduled cycles paused." : "Scheduled cycles resumed.", action });
    }
    if (action === "stop") {
      const runsResponse = await gh(workflowUrl + "/runs?status=in_progress&per_page=20");
      if (!runsResponse.ok) return Response.json({ error: "Could not list active runs." }, { status: 502 });
      const data = await runsResponse.json();
      const active = data.workflow_runs || [];
      const results = await Promise.all(active.map((run: any) => gh(API + "/actions/runs/" + run.id + "/cancel", { method: "POST" })));
      return Response.json({ ok: true, action, cancelled: results.filter((r: Response) => r.ok).length, message: "Cancellation requested for active cycles." });
    }
    return Response.json({ error: "Action must be start, pause, resume, or stop." }, { status: 400 });
  } catch (error) {
    console.error("qill_control_failed", error);
    return Response.json({ error: "GitHub control request failed." }, { status: 502 });
  }
}
