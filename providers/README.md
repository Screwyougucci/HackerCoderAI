# Qill provider pool and zero-cost rules

Qill uses bounded concurrency per provider. A provider is eligible only while its own free-tier quota and service status permit the work. On quota exhaustion, the scheduler stops sending new work there and tries the next configured provider. If every provider is exhausted or asleep, work waits for a legitimate quota reset or wake-up.

## Current provider pool

| Provider | Workload | Free capacity and limits | Qill status |
|---|---|---|---|
| GitHub Actions | Real worker VMs | Standard runners are free and unlimited for public repositories | Active; max 3 concurrent jobs |
| Hugging Face Spaces CPU Basic | Lightweight worker HTTP service | 2 vCPU / 16 GB RAM; free Spaces can sleep when unused | Not connected yet |
| Hugging Face ZeroGPU Spaces | Short GPU inference bursts | Free personal accounts in good standing can host up to 2 Spaces; free account quota is 5 GPU minutes/day | Not connected; burst-only |
| Cloudflare Workers Free | Queue/control API, health checks, routing | 100,000 requests/day; 10 ms CPU per request | Standby; coordinator only |

## Hugging Face Jobs are not free

Do not use the Hugging Face Jobs API for this strict-$0 project. Its default CPU Basic flavor is billed at $0.01/hour. Qill must not start Jobs or paid hardware automatically.

## Concurrency and failover policy

- Target: 2–3 active tasks per configured provider.
- Current GitHub Actions pool: 3 active jobs at a time; the eight worker roles queue in the same workflow.
- Each additional Space endpoint gets its own cap of at most 2–3 active requests.
- Use bounded task payloads, idempotency keys, and checkpoint writes. Retry only transient failures.
- A quota response (for example HTTP 429 or a provider-specific daily-quota response) opens that provider's circuit until its documented reset time. Sleeping/unavailable Space responses are temporarily unavailable.
- Authentication failures, malformed requests, and application bugs are not quota exhaustion; surface them for repair.
- If no provider is eligible, pause/queue. Never fall back to paid hardware.

## Hugging Face Space setup still required

The connected Hugging Face account is a free personal account. This repository does not yet contain a deployed Space endpoint, and the available Hugging Face connector cannot create a Space repository. To activate Spaces, create one or two Gradio Spaces under the account using CPU Basic (or ZeroGPU for short inference bursts), deploy the Qill worker service, and add each endpoint and its access secret to Vercel as server-only environment variables. Do not use HF Jobs.

## Capacity is not always-on

Free Spaces can sleep. ZeroGPU quota is small and resets 24 hours after first GPU use. Cloudflare Workers are suitable for lightweight coordination, not long-running model inference. GitHub Actions provides the dependable CPU worker pool while the public repository and standard runner policy remain eligible. A recurring schedule is not a continuously running server.
