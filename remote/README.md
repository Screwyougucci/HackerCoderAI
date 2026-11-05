# Qill Distributed Control Center

Vercel-hosted dashboard for eight bounded GitHub Actions worker roles, with an optional Hugging Face Gradio Space worker pool.

## Zero-cost design

- Dashboard/control plane: Next.js on the existing Vercel project.
- Main workers: standard GitHub-hosted Ubuntu runners, max-parallel 3, on a public repository.
- Schedule: bounded worker cycle every 30 minutes, plus manual dispatch.
- Memory: GitHub worker checkpoint JSON is committed to the dedicated `qill-state` branch.
- Optional Space workers: `providers/hf-space/` contains a Gradio demo and API endpoint for all eight fixed worker roles, with at most three concurrent tasks per Space.
- No paid model API or Hugging Face Jobs are called.

## GitHub controls

In Vercel project `hackercoderai-remote`, root directory `remote`, configure `HACKERCODERAI_ACCESS_KEY` and `GITHUB_TOKEN`. The GitHub token should be fine-grained and scoped only to `Screwyougucci/HackerCoderAI`, with Actions read/write permission.

## Optional Hugging Face Space

The Gradio Space files are in `providers/hf-space/`. Hugging Face currently requires PRO for ordinary CPU Basic Gradio/Docker Spaces, but eligible free personal accounts may host up to two Gradio ZeroGPU Spaces. Qill does not use a GPU function. Do not enable paid hardware or billing.

To deploy under the connected account `Smatt324`:
1. Install `huggingface_hub`: `python -m pip install -U huggingface_hub`.
2. Run `python providers/hf-space/deploy_space.py`.
3. Enter a Hugging Face write token at the hidden prompt. The script does not save it.
4. If Hugging Face returns HTTP 402, stop; do not upgrade or add payment details.

Expected demo: `https://huggingface.co/spaces/Smatt324/qill-project-intelligence`. Gradio automatically exposes `/agents.md` and `/gradio_api/info`.

## Connect to Vercel

Set `HF_WORKER_A_URL=https://smatt324-qill-project-intelligence.hf.space` in Vercel. Optionally set `HF_WORKER_B_URL` to a second Space. `HF_WORKER_TOKEN` is optional for private/token-aware calls. Redeploy Vercel.

- `GET /api/providers` checks Space API health.
- Authenticated `POST /api/providers` dispatches one of the fixed roles through Gradio's call/poll API.
- Failover occurs only after an explicit HTTP 429/503 response. Ambiguous network failures and tasks with a returned event ID are never replayed, avoiding duplicate work.

Space tasks return JSON to the caller and do not write durable checkpoints. The GitHub Actions workflow remains the recurring scheduler and checkpoint writer. Free ZeroGPU quotas and Space availability still apply.

## Workflow and checkpoints

Workflow: `.github/workflows/qill-workers.yml`

- Eight fixed roles: research scout, source scanner, test runner, pattern miner, validation reviewer, documentation auditor, regression watcher, intelligence synthesizer.
- Each job has a five-minute hard timeout; the test command itself has a 75-second timeout.
- Consolidation writes the latest checkpoint and per-worker JSON to `qill-state`.
- Scheduled cycles run every 30 minutes. This is recurring batch execution, not always-on compute.

Candidate findings are heuristic leads, not confirmed vulnerabilities. Validate them manually before making changes.
