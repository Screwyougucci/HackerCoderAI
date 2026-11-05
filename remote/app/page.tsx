"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

type Worker = {
  role: string; label?: string; status: string; durationSeconds?: number;
  findings?: unknown[];
  tests?: { status?: string; exitCode?: number; output?: string };
  research?: { query?: string; sources?: { title?: string; url?: string }[]; note?: string };
  review?: { candidateCount?: number };
  regression?: { currentCandidates?: number; newCandidates?: number };
  recommendation?: string;
};
type ProviderData = { providers?: { name: string; status: string }[]; configured?: boolean };
type DashboardData = {
  ok?: boolean; workflowState?: string; error?: string;
  latestRun?: { id: number; runNumber: number; status: string; conclusion: string | null; event: string; createdAt: string; url: string }[];
  checkpoint?: {
    updatedAt?: string; goal?: string; summary?: Record<string, number | string>; workers?: Worker[];
    findings?: { rule: string; file: string; line: number; evidence: string; advice: string }[];
    research?: { sources?: { title?: string; url?: string }[] }; tests?: { status?: string; output?: string };
  } | null;
};
const workerCatalog = [
  ["research-scout", "Research Scout", "Finds public technical references"],
  ["source-scanner", "Source Scanner", "Read-only source heuristics"],
  ["test-runner", "Test Runner", "Runs repository unit tests"],
  ["pattern-miner", "Pattern Miner", "Groups recurring findings"],
  ["validation-reviewer", "Validation Reviewer", "Flags leads for human verification"],
  ["documentation-auditor", "Documentation Auditor", "Checks docs and local links"],
  ["regression-watcher", "Regression Watcher", "Compares with saved checkpoints"],
  ["intelligence-synthesizer", "Intelligence Synthesizer", "Builds project inventory and recommendations"],
] as const;

export default function Home() {
  const [accessKey, setAccessKey] = useState("");
  const [goal, setGoal] = useState("Review this repository for safe, authorized improvements.");
  const [data, setData] = useState<DashboardData | null>(null);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [providerData, setProviderData] = useState<ProviderData | null>(null);
  const [spaceBusy, setSpaceBusy] = useState(false);
  const [spaceResults, setSpaceResults] = useState<string[]>([]);

  const refresh = useCallback(async () => {
    try {
      const response = await fetch("/api/workers", { cache: "no-store" });
      const json = await response.json();
      setData(json);
      if (!response.ok) setError(json.error || "Status request failed.");
      try {
        const providerResponse = await fetch("/api/providers", { cache: "no-store" });
        setProviderData(await providerResponse.json());
      } catch { setProviderData(null); }
    } catch {
      setError("Dashboard could not reach the worker registry.");
    }
  }, []);

  useEffect(() => {
    void refresh();
    const timer = window.setInterval(() => void refresh(), 30000);
    return () => window.clearInterval(timer);
  }, [refresh]);

  const workers = useMemo(() => {
    const byRole = new Map((data?.checkpoint?.workers || []).map((worker) => [worker.role, worker]));
    return workerCatalog.map(([role, label, description], index) => ({
      role, label, description, index, report: byRole.get(role),
    }));
  }, [data]);
  const summary = data?.checkpoint?.summary;
  const latest = data?.latestRun?.[0];
  const workflowEnabled = data?.workflowState === "active";

  async function control(action: "start" | "pause" | "resume" | "stop") {
    setBusy(true); setError(""); setNotice("");
    try {
      const response = await fetch("/api/workers", {
        method: "POST",
        headers: { "Content-Type": "application/json", "x-hackercoderai-key": accessKey },
        body: JSON.stringify({ action, goal }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || "Control request failed.");
      setNotice(result.message || "Control request accepted.");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Control request failed.");
    } finally { setBusy(false); }
  }

  async function dispatchSpaceBatch() {
    setSpaceBusy(true); setSpaceResults([]); setError("");
    const roles = ["research-scout", "source-scanner", "test-runner"];
    try {
      const results = await Promise.all(roles.map(async (role) => {
        const response = await fetch("/api/providers", {
          method: "POST",
          headers: { "Content-Type": "application/json", "x-hackercoderai-key": accessKey },
          body: JSON.stringify({ role, goal }),
        });
        const result = await response.json();
        if (!response.ok) throw new Error(role + ": " + (result.error || "Dispatch failed"));
        return role + " → " + (result.dispatchedTo || "Space") + " (" + (result.result?.status || "completed") + ")";
      }));
      setSpaceResults(results);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Space dispatch failed.");
    } finally { setSpaceBusy(false); }
  }

  const hfStatus = providerData?.providers?.length
    ? providerData.providers.map((p) => p.status).join(" / ").toUpperCase()
    : "NOT CONFIGURED";

  return (
    <main className="shell">
      <header className="topbar">
        <div className="brandmark"><span className="brand-orb">Q</span><div><b>QILL</b><small>DISTRIBUTED INTELLIGENCE</small></div></div>
        <div className="top-meta"><span className="live-dot" /> CONTROL PLANE <span className="version">ZERO-COST MODE</span></div>
      </header>

      <section className="hero">
        <div className="eyebrow">AUTONOMOUS RESEARCH FLEET / BUILD 01</div>
        <h1>One brain.<br /><em>Eight workers.</em></h1>
        <p>Coordinate independent cloud runners, inspect their findings, and preserve every cycle as a resumable checkpoint. No paid model API or paid compute is called.</p>
      </section>

      <section className="metrics">
        <div className="metric"><span>WORKER TARGET</span><strong>08</strong><small>Independent job runners</small></div>
        <div className="metric"><span>LAST CYCLE</span><strong>{latest ? "#" + latest.runNumber : "—"}</strong><small>{latest ? latest.status.replace("_", " ") : "Waiting for first run"}</small></div>
        <div className="metric"><span>FINDING LEADS</span><strong>{summary?.candidateFindings ?? "—"}</strong><small>Heuristic, not confirmed</small></div>
        <div className="metric"><span>TEST SUITE</span><strong className="metric-small">{String(summary?.testStatus || "NOT RUN").toUpperCase()}</strong><small>Repository tests</small></div>
      </section>

      <div className="main-grid">
        <section className="panel fleet-panel">
          <div className="section-head"><div><span className="eyebrow">01 / COMPUTE FLEET</span><h2>Worker network</h2></div><button className="quiet-button" onClick={() => void refresh()}>↻ Refresh</button></div>
          <div className="worker-grid">
            {workers.map((worker) => (
              <article className="worker-card" key={worker.role}>
                <div className="worker-top"><span className="worker-index">0{worker.index + 1}</span><span className={worker.report?.status === "completed" ? "status-pill good" : worker.report?.status === "failed" ? "status-pill bad" : "status-pill idle"}>{worker.report?.status || "AWAITING RUN"}</span></div>
                <div className="worker-glyph">{["⌕","⌘","✓","⌗","◈","▤","↗","✳"][worker.index]}</div>
                <h3>{worker.label}</h3><p>{worker.description}</p>
                <div className="worker-foot"><span>{worker.report?.durationSeconds != null ? worker.report.durationSeconds + "s cycle" : "No checkpoint yet"}</span><span>GITHUB RUNNER</span></div>
              </article>
            ))}
          </div>
        </section>

        <aside className="side-stack">
          <section className="panel control-panel">
            <span className="eyebrow">02 / COMMAND</span><h2>Mission control</h2>
            <label htmlFor="goal">Research / engineering objective</label>
            <textarea id="goal" value={goal} onChange={(e) => setGoal(e.target.value)} maxLength={1500} />
            <label htmlFor="access">Dashboard control key</label>
            <input id="access" type="password" value={accessKey} onChange={(e) => setAccessKey(e.target.value)} placeholder="Vercel access key" autoComplete="off" />
            <button className="primary-button" disabled={busy || !accessKey.trim()} onClick={() => void control("start")}>{busy ? "SENDING…" : "▶  START WORKER CYCLE"}</button>
            <div className="button-row">
              {workflowEnabled
                ? <button className="secondary-button" disabled={busy || !accessKey.trim()} onClick={() => void control("pause")}>Ⅱ Pause schedule</button>
                : <button className="secondary-button" disabled={busy || !accessKey.trim()} onClick={() => void control("resume")}>▶ Resume schedule</button>}
              <button className="danger-button" disabled={busy || !accessKey.trim()} onClick={() => void control("stop")}>■ Stop active</button>
            </div>
            {notice && <div className="notice">{notice}</div>}
            {error && <div className="error">{error}</div>}
            <p className="hint">The key authorizes control only. It is sent to the server in a request header and is never saved in browser storage.</p>
          </section>

          <section className="panel provider-panel">
            <span className="eyebrow">03 / PROVIDERS</span><h2>Compute sources</h2>
            <div className="provider-row"><span className="provider-icon">GH</span><div><b>GitHub Actions</b><small>8 parallel public-repo runners</small></div><span className="provider-state active">ACTIVE</span></div>
            <div className="provider-row"><span className="provider-icon">HF</span><div><b>Hugging Face Spaces</b><small>Up to 3 tasks per Space · A/B failover</small></div><span className="provider-state">{hfStatus}</span></div>
            <div className="provider-row"><span className="provider-icon">CF</span><div><b>Cloudflare Workers</b><small>Coordinator integration not connected</small></div><span className="provider-state standby">STANDBY</span></div>
            <button className="secondary-button" disabled={spaceBusy || !accessKey.trim() || !providerData?.configured} onClick={() => void dispatchSpaceBatch()}>{spaceBusy ? "DISPATCHING 3 TASKS…" : "▶ RUN 3 SPACE TASKS"}</button>
            {spaceResults.map((item) => <p className="hint" key={item}>{item}</p>)}
            <p className="hint">The button sends three independent roles concurrently. Spaces must be deployed and configured in Vercel first. Free Spaces may sleep.</p>
          </section>
        </aside>
      </div>

      <section className="panel activity-panel">
        <div className="section-head"><div><span className="eyebrow">04 / PERSISTENT MEMORY</span><h2>Latest checkpoint</h2></div><span className="checkpoint-time">{data?.checkpoint?.updatedAt ? new Date(data.checkpoint.updatedAt).toLocaleString() : "NO CHECKPOINT"}</span></div>
        <div className="checkpoint-grid">
          <div><small>LAST OBJECTIVE</small><p>{data?.checkpoint?.goal || "The first worker cycle will create the initial shared checkpoint."}</p></div>
          <div><small>WORKFLOW</small><p>{latest ? <a href={latest.url} target="_blank" rel="noreferrer">Run #{latest.runNumber} · {latest.conclusion || latest.status} ↗</a> : "No workflow runs recorded yet."}</p></div>
          <div><small>RESEARCH SOURCES</small><p>{data?.checkpoint?.research?.sources?.length ?? 0} public search results captured</p></div>
        </div>
        <div className="findings">
          <div className="findings-head"><b>Candidate findings</b><span>READ-ONLY / HEURISTIC</span></div>
          {(data?.checkpoint?.findings || []).slice(0, 8).map((finding, i) => <div className="finding-row" key={finding.rule + "-" + finding.file + "-" + finding.line + "-" + i}><code>{finding.rule}</code><span>{finding.file}:{finding.line}</span><small>{finding.advice}</small></div>)}
          {!data?.checkpoint?.findings?.length && <p className="empty-state">No candidate findings in the saved checkpoint.</p>}
        </div>
      </section>

      <footer><span>QILL / HACKERCODERAI</span><span>BOUNDED JOBS · CHECKPOINTED STATE · HUMAN APPROVAL FOR CHANGES</span></footer>
    </main>
  );
}
