---
title: Qill Project Intelligence
emoji: 🛰️
colorFrom: gray
colorTo: red
sdk: gradio
sdk_version: 5.33.0
app_file: app.py
pinned: false
license: mit
short_description: Read-only multi-role analysis demo for HackerCoderAI
---

# ◈ Qill · HackerCoderAI

An interactive Gradio demo for the public [Screwyougucci/HackerCoderAI](https://github.com/Screwyougucci/HackerCoderAI) project.

Choose one of eight fixed worker roles, enter a plain-language objective, and inspect a structured JSON report.

## Demo capabilities

- Research Scout — searches public technical references.
- Source Scanner — identifies selected risky coding patterns.
- Test Runner — runs the repository's bounded unit tests.
- Pattern Miner — summarizes historical checkpoint patterns.
- Validation Reviewer — marks heuristic findings for human review.
- Documentation Auditor — checks README links and documentation structure.
- Regression Watcher — compares current candidates with the saved checkpoint.
- Intelligence Synthesizer — builds a small project inventory.

## Runtime limits and safety

- Maximum three concurrent tasks per Space.
- Four-minute worker deadline.
- Public repository only; source is checked out from the project's public main branch.
- User objectives are treated as data, never as shell commands.
- No arbitrary shell execution, file writes, external target scans, or automatic code changes.
- Findings are heuristic leads, not confirmed vulnerabilities.

## Hugging Face setup

This is a **Gradio Space**, not a Docker Space. Copy the contents of this directory to the root of a new Space repository.

For a strict-$0 setup, use an eligible **ZeroGPU** Space on a free personal account, if the ZeroGPU option is available. Hugging Face currently permits eligible free personal accounts in good standing to host up to two ZeroGPU Spaces. Do not choose CPU Upgrade, paid GPU hardware, or enable billing. A regular Gradio Space on CPU Basic requires PRO for personal accounts.

After deployment, Gradio automatically exposes an `/agents.md` endpoint describing the API schema and call/poll procedure. The demo endpoint is named `run_qill_worker`.

## Connect to Vercel

Set `HF_WORKER_A_URL` in Vercel to the Space runtime URL, for example:

`https://<your-username>-qill-project-intelligence.hf.space`

Optionally set `HF_WORKER_B_URL` to a second Space. Redeploy Vercel after changing environment variables. The Vercel API uses the Gradio call/poll interface and tries the next Space only when a provider is unreachable or rejects a request with a quota/unavailable response.

The browser demo is public and operates only on this public repository. Do not add private source code or secrets to the demo.
