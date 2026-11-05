# Qill Distributed Control Center

Vercel-hosted dashboard for eight independent, short-lived GitHub Actions worker VMs.

## Zero-cost design

- Dashboard: Next.js on the existing Vercel Hobby project.
- Workers: eight separate standard GitHub-hosted Ubuntu runners, launched in parallel from a public repository.
- Schedule: one bounded worker cycle every 30 minutes, plus manual dispatch.
- Memory: checkpoint JSON committed to the dedicated qill-state branch.
- Inference: no paid model API is called. The first release uses deterministic research, source heuristics, tests, and pattern analysis. Hugging Face and Cloudflare adapters are listed as optional future providers, not active compute.
- Safety: source scanning is read-only; tests run in isolated ephemeral runners; no arbitrary generated shell commands, deployment, external target scanning, or automatic code changes.

GitHub documents standard hosted runners as free and unlimited for public repositories. This repository must remain public for the strict $0 compute assumption. See https://docs.github.com/en/actions/reference/runners/github-hosted-runners.

## Configure the dashboard controls

In Vercel project hackercoderai-remote, root directory remote, add these Production environment variables:

- HACKERCODERAI_ACCESS_KEY: a long random dashboard password you generate.
- GITHUB_TOKEN: a fine-grained GitHub token scoped only to Screwyougucci/HackerCoderAI, with Actions: read and write permission. The token is used server-side to dispatch, pause, resume, and cancel workflow runs. Never put it in browser code or commit it.

Redeploy after adding the variables. The dashboard status view reads public workflow/checkpoint metadata; control actions require the access key and token.

## Worker schedule and checkpoints

Workflow: .github/workflows/qill-workers.yml

- Eight roles run in parallel: research scout, source scanner, test runner, pattern miner, validation reviewer, documentation auditor, regression watcher, intelligence synthesizer.
- Each job has a five-minute hard timeout; the test command itself has a 75-second timeout.
- The consolidation job writes the latest checkpoint and per-worker JSON to the qill-state branch.
- Scheduled cycles run every 30 minutes. GitHub schedule events can be delayed during high load; this is recurring batch execution, not eight always-on servers.
- Dashboard actions: start a cycle, pause/resume the schedule, and cancel active runs.

## Optional providers

The dashboard reserves slots for Hugging Face Spaces and Cloudflare Workers. They are standby only in this release. Activating them requires deploying those provider-specific workers in the user's own free-tier accounts and configuring authenticated endpoints. Hugging Face free Spaces can sleep and ZeroGPU has quotas; Cloudflare Workers Free is suitable for coordination/API tasks, not sustained AI inference. No provider is allowed to upgrade to paid billing automatically.

## Local checks

    python -m py_compile workers/run_worker.py workers/aggregate.py
    python workers/run_worker.py --role source-scanner --goal "Review this repository" --output /tmp/qill-worker.json
    python workers/aggregate.py --input /tmp/qill-empty --output /tmp/qill-state

Candidate findings are heuristic leads, not confirmed vulnerabilities. Validate them manually before making changes.
