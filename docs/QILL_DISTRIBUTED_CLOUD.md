# Qill distributed cloud architecture

## Design goal

A strict-$0 compute fleet with provider-aware failover, bounded parallelism, and durable checkpoints. Vercel is the control plane. GitHub Actions remains the scheduled worker pool; optional Hugging Face Spaces can receive individual worker tasks.

## Provider pool

| Provider | Function | Cap | State |
|---|---|---:|---|
| GitHub Actions standard runners | Main CPU workers | 3 concurrent jobs | Active |
| Hugging Face Spaces CPU Basic | HTTP worker tasks | 3 concurrent requests per Space | Adapter committed; Space setup required |
| Cloudflare Workers Free | Lightweight coordination | 100k requests/day; 10ms CPU/request | Standby |

Hugging Face Jobs are excluded because they are billed. Qill must not invoke paid hardware or paid jobs.

## Hugging Face adapter

Deployable source is in `providers/hf-space/`. It exposes `GET /health` and authenticated `POST /run`, accepts only the eight fixed Qill roles, checks out the public project, and runs the existing fixed worker module. Each Space allows at most three concurrent tasks.

Create a Docker Space only if the Hugging Face account allows compute-backed Spaces on free CPU Basic hardware. The default CPU Basic tier has 2 vCPU and 16 GB RAM, and free Spaces can sleep after inactivity. Account/plan eligibility can vary. If the UI asks for a subscription, payment method, or hardware upgrade, stop and do not enable billing.

Set the Space secret `QILL_WORKER_KEY`. In Vercel project `hackercoderai-remote` (root directory `remote`), set:
- `HF_WORKER_TOKEN`: same random secret as `QILL_WORKER_KEY`.
- `HF_WORKER_A_URL`: first Space base URL, such as `https://<namespace>-qill-worker.hf.space`.
- `HF_WORKER_B_URL`: optional second Space base URL.

Redeploy Vercel after setting the variables. Server-side endpoints:
- `GET /api/providers` checks configured Space health.
- `POST /api/providers` dispatches one allowlisted role. Include `x-hackercoderai-key` and a JSON body with `role` and optional `goal`.

The dispatcher tries Space B after Space A only when A is unreachable or returns HTTP 429/503. It does not retry authentication, validation, application errors, or ambiguous timeouts. This is task-level failover, not a durable queue. The existing GitHub Actions workflow remains the recurring scheduler and checkpoint writer.

## Scheduling and failover

1. Run no more than three active jobs per provider.
2. Use only configured providers; unconfigured Spaces are not considered healthy.
3. On HTTP 429/503 or a connection failure before a response, try the next configured Space.
4. Do not replay a timed-out request because the remote worker may still be executing.
5. If all Spaces are unavailable, return an explicit unavailable response. Retry later; this adapter does not claim to persist a queue.
6. Never purchase credits, upgrade hardware, or bypass provider limits.

The GitHub Actions workflow has `max-parallel: 3` and writes checkpoints to `qill-state`. Cross-provider dispatch becomes usable only after at least one eligible Space is deployed and its Vercel variables are configured.

## State and safety

- GitHub worker output is checkpointed to `qill-state`.
- Space tasks return JSON to the caller; they do not write the checkpoint branch.
- Workers perform bounded repository analysis and tests. Findings are heuristic leads, not confirmed vulnerabilities.
- No arbitrary shell command is accepted, and no code is automatically changed.
- Credentials belong only in server-side Vercel/Hugging Face secrets, never in Git.
