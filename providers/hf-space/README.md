---
title: Qill Worker
emoji: 🛰️
colorFrom: gray
colorTo: red
sdk: docker
app_port: 7860
pinned: false
---

# Qill Hugging Face Space worker

A bounded, authenticated worker adapter for the Qill project. It accepts only the eight fixed worker roles from the public HackerCoderAI repository. It does not accept shell commands or arbitrary repository URLs.

## Space secrets

Set `QILL_WORKER_KEY` in **Settings → Variables and secrets**. Use a long random value. Put the exact same value in Vercel as `HF_WORKER_TOKEN`.

Keep the Space on free CPU Basic hardware. Do not select upgraded CPU/GPU hardware or enable billing. CPU Basic Spaces can sleep after inactivity, so the Vercel coordinator will treat a sleeping/unavailable Space as unavailable and try the next configured provider.

## API

- `GET /health` — provider readiness and current concurrency.
- `POST /run` — authenticated task execution.

Example request:

```http
POST /run
X-Qill-Worker-Key: <QILL_WORKER_KEY>
Content-Type: application/json

{"role":"source-scanner","goal":"Review the repository for safe, authorized improvements."}
```

The service permits at most three concurrent tasks, has a four-minute task deadline, and only invokes the checked-in `workers/run_worker.py` with a fixed role allowlist. Results are returned as JSON. The service is stateless; durable checkpoints remain the responsibility of the GitHub Actions consolidation workflow.

## Deploy

Create a new **Docker Space** in your Hugging Face account and upload the contents of this directory. Choose only CPU Basic if your account permits free compute Spaces. Current Hugging Face account/plan eligibility may restrict creating compute-backed Docker Spaces; if the UI requires a paid plan, stop and do not upgrade. The adapter is not active until the Space URL is configured in Vercel.
