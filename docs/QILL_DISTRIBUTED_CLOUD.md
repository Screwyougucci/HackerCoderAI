# Qill distributed cloud architecture

## Design goal

A $0 compute fleet with provider-aware failover, bounded parallelism, and durable checkpoints. Vercel is the control plane. The worker pool is composed of independently limited providers.

## Provider pool

| Provider | Function | Cap | State |
|---|---|---:|---|
| GitHub Actions standard runners | Main CPU workers | 3 concurrent jobs | Active |
| Hugging Face Spaces CPU Basic | Lightweight HTTP workers | 2–3 concurrent requests per Space | Requires Space deployment |
| Hugging Face ZeroGPU | Short GPU inference bursts | At most 2 free Spaces per eligible personal account; 5 GPU minutes/day | Optional, quota-limited |
| Cloudflare Workers Free | Queue routing, status, lightweight coordination | 100k requests/day; 10ms CPU/request | Standby |

**Hugging Face Jobs are excluded:** CPU Basic Jobs cost $0.01/hour. Qill must not invoke Jobs or any paid flavor under the strict-$0 requirement.

## Scheduling and failover

1. Divide the eight worker roles into bounded jobs.
2. Run no more than three active jobs on each provider at a time.
3. Select only providers marked healthy and with remaining documented free quota.
4. When a provider reports quota exhaustion, stop dispatching new work to it and route the next queued task to the next eligible provider.
5. If a Space sleeps or is temporarily unavailable, defer it and use another healthy provider.
6. Do not treat authentication errors, malformed payloads, or code failures as quota exhaustion.
7. If all providers are unavailable, retain the queue and resume after a legitimate reset/wake event. Never purchase credits, upgrade hardware, create extra accounts, or bypass provider limits.

The current GitHub Actions workflow has max-parallel: 3. This is the live concurrency cap for the only active compute provider. Space endpoints are not connected yet, so cross-provider failover is not active.

## Free-tier facts

- GitHub standard hosted runners are free and unlimited for public repositories. The project must remain public and use standard runners.
- Hugging Face CPU Basic Spaces have 2 vCPU and 16 GB RAM, but free Spaces can sleep when unused.
- Free personal Hugging Face accounts in good standing can host up to two ZeroGPU Spaces. Free account ZeroGPU usage quota is five GPU minutes per day.
- Hugging Face Jobs are billed per minute; CPU Basic is $0.01/hour.
- Cloudflare Workers Free provides 100,000 requests/day and 10 ms CPU per request, making it suitable for routing/health APIs rather than sustained model inference.

## State and safety

- Worker output is checkpointed to the dedicated qill-state branch.
- Workers run bounded, read-only repository scans and tests.
- Findings are heuristic leads, not confirmed vulnerabilities.
- No model-generated shell commands are executed and no code is automatically changed.
- Provider credentials must be stored as server-side secrets in Vercel, never committed to Git.
