"use client";

import { useState } from "react";

type RunResult = {
  model?: string;
  answer?: string;
  sandbox?: { status: string; stdout: string; exitCode: number; region?: string };
  error?: string;
};

export default function Home() {
  const [goal, setGoal] = useState("Explain how this remote AI runner works and suggest a safe first coding task.");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<RunResult | null>(null);

  async function runTask() {
    setBusy(true);
    setResult(null);
    try {
      const response = await fetch("/api/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ goal }),
      });
      const data = await response.json();
      setResult(data);
    } catch (error) {
      setResult({ error: error instanceof Error ? error.message : "Request failed" });
    } finally {
      setBusy(false);
    }
  }

  return (
    <main>
      <div className="top">
        <div className="brand">HACKERCODERAI / REMOTE</div>
        <div className="status">VERCEL CLOUD COMPUTE</div>
      </div>
      <h1>Your agent.<br /><span>Cloud-powered.</span></h1>
      <p className="intro">A remote control room for HackerCoderAI. Vercel AI Gateway provides the model inference; Vercel Sandboxes provide isolated Linux computers for approved execution and tests.</p>
      <div className="layout">
        <section className="panel">
          <h2>Start a cloud AI run</h2>
          <p className="muted">Describe a task. The model will analyze it, then a fresh Vercel Sandbox will run a contained environment check.</p>
          <textarea value={goal} onChange={(event) => setGoal(event.target.value)} maxLength={2000} aria-label="Task description" />
          <button onClick={runTask} disabled={busy || !goal.trim()}>{busy ? "Starting cloud run…" : "Run AI + sandbox test"}</button>
          {result && <div className="result" aria-live="polite">
            {result.error ? "ERROR: " + result.error : ""}
            {result.model ? "MODEL: " + result.model + "\n\n" : ""}
            {result.answer ? result.answer + "\n\n" : ""}
            {result.sandbox ? "SANDBOX: " + result.sandbox.status + "\nEXIT CODE: " + result.sandbox.exitCode + "\nOUTPUT:\n" + result.sandbox.stdout : ""}
          </div>}
        </section>
        <aside className="panel">
          <h2>Compute architecture</h2>
          <div className="stat"><b>AI Gateway</b><span className="muted tiny">Hosted model inference, routed through Vercel</span></div>
          <div className="stat"><b>Sandbox VM</b><span className="muted tiny">Isolated Linux execution, created on demand</span></div>
          <div className="stat"><b>Local EXE</b><span className="muted tiny">Your Windows desktop build remains independent</span></div>
          <p className="foot">This first cloud test runs a fixed, network-disabled Python smoke test. It does not execute arbitrary shell commands or scan external targets. Longer durable workflows and saved task history are the next layer.</p>
        </aside>
      </div>
    </main>
  );
}
