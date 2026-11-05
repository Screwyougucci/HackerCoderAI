# Qill Distributed Control Center

Vercel-hosted dashboard for eight bounded GitHub Actions worker roles, with an optional authenticated Hugging Face Space worker adapter.

## Zero-cost design

- Dashboard: Next.js on the existing Vercel Hobby project.
- Main workers: standard GitHub-hosted Ubuntu runners, max-parallel 3, on a public repository.
- Schedule: one bounded worker cycle every 30 minutes, plus manual dispatch.
- Memory: GitHub worker checkpoint JSON is committed to the dedicated `qill-state` branch.
- Optional Space workers: `providers/hf-space/` contains a Docker Space adapter with a three-request concurrency cap and fixed role allowlist.
- No paid model API or Hugging Face Jobs are called.
- Workers run bounded repository scans and tests; no arbitrary shell input or automatic code changes.

## GitHub controls

In Vercel project `hackercoderai-remote`, root directory `remote`, configure `HACKERCODERAI_ACCESS_KEY` and `GITHUB_TOKEN`. The GitHub token should be fine-grained and scoped only to `Screwyougucci/HackerCoderAI`, with Actions read/write permission.

## Optional Hugging Face Space workers

The adapter code is in `providers/hf-space/`. Create a Docker Space only if your account permits compute-backed Spaces on free CPU Basic. CPU Basic has 2 vCPU and 16 GB RAM, but free Spaces can sleep. Account eligibility for compute-backed Docker/Gradio Spaces can vary. If the UI asks for a subscription, payment method, or upgraded hardware, stop and do not enable billing.

Set `QILL_WORKER_KEY` as a Space secret. In Vercel, set `HF_WORKER_TOKEN` to the same secret, `HF_WORKER_A_URL` to the first Space base URL, and optionally `HF_WORKER_B_URL` to a second Space URL. Redeploy Vercel.

`GET /api/providers` reports Space health. Authenticated `POST /api/providers` accepts one of the eight fixed roles and tries the next Space when the previous one is unreachable or returns HTTP 429/503. It does not retry timeouts or application/authentication errors because those could duplicate work. Include `x-hackercoderai-key` with the dashboard access key.

Space tasks return JSON to the caller and do not write durable checkpoints. The existing GitHub Actions workflow remains the scheduled runner and checkpoint writer. This is not an always-on queue; free CPU Basic Spaces may sleep.

## Workflow and checkpoints

Workflow: `.github/workflows/qill-workers.yml`

- Eight fixed roles: research scout, source scanner, test runner, pattern miner, validation reviewer, documentation auditor, regression watcher, intelligence synthesizer.
- Each job has a five-minute hard timeout; the test command itself has a 75-second timeout.
- Consolidation writes the latest checkpoint and per-worker JSON to `qill-state`.
- Scheduled cycles run every 30 minutes. GitHub may delay scheduled events during high load; this is recurring batch execution, not always-on compute.

## Local checks

    python -m py_compile workers/run_worker.py workers/aggregate.py
    python workers/run_worker.py --role source-scanner --goal "Review this repository" --output /tmp/qill-worker.json
    python workers/aggregate.py --input /tmp/qill-empty --output /tmp/qill-state

Candidate findings are heuristic leads, not confirmed vulnerabilities. Validate them manually before making changes.
