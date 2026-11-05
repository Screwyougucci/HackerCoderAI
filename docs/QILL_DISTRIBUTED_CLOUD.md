# Qill distributed cloud architecture

## Design goal

A strict-$0 compute fleet with bounded parallelism, provider-aware failover, and durable GitHub checkpoints. Vercel is the control plane. GitHub Actions is the scheduled worker pool; Hugging Face Gradio Spaces can receive individual worker tasks.

## Provider pool

| Provider | Function | Cap | State |
|---|---|---:|---|
| GitHub Actions standard runners | Main CPU workers | 3 concurrent jobs | Active |
| Hugging Face Gradio ZeroGPU Spaces | Interactive demo and task workers | 3 concurrent tasks per Space | Code ready; deployment requires a write token |
| Cloudflare Workers Free | Lightweight coordination | 100k requests/day; 10ms CPU/request | Standby |

## Hugging Face Space

The deployable Gradio app is in `providers/hf-space/`. It checks out the public HackerCoderAI repository and exposes the eight fixed worker roles through a Gradio interface. Gradio automatically exposes an `/agents.md` endpoint and a machine-readable `/gradio_api/info` schema.

The app accepts only the fixed roles, limits concurrency to three tasks per Space, and applies a four-minute task deadline. The objective is plain text; no arbitrary shell command is accepted. Reports are read-only heuristic results.

### Strict-$0 deployment

Hugging Face currently states that ordinary Gradio/Docker Spaces on CPU Basic require PRO for personal accounts. Eligible free personal accounts in good standing may host up to two Gradio Spaces on ZeroGPU. Qill does not call a GPU function; ZeroGPU is selected as the free-eligible Gradio hosting option. Do not choose paid CPU/GPU hardware, enable billing, or buy credits. If the account is ineligible, stop and leave the Space undeployed.

The connected Hugging Face account may not have repository write permission. The helper `providers/hf-space/deploy_space.py` creates the Space under `Smatt324/qill-project-intelligence`, requests `zero-a10g`, and uploads this folder. Run:

```bash
python -m pip install -U huggingface_hub
python providers/hf-space/deploy_space.py
```

The script prompts for a write token with hidden input. It does not save the token. If Hugging Face returns HTTP 402, stop; do not upgrade or add payment details. If it returns 401/403, create a write-scoped token and retry.

After deployment:
- Demo: `https://huggingface.co/spaces/Smatt324/qill-project-intelligence`
- Agent guide: `https://huggingface.co/spaces/Smatt324/qill-project-intelligence/agents.md`
- Runtime: `https://smatt324-qill-project-intelligence.hf.space`

### Connect to Vercel

In Vercel project `hackercoderai-remote` (root directory `remote`), set:
- `HF_WORKER_A_URL=https://smatt324-qill-project-intelligence.hf.space`
- Optional `HF_WORKER_B_URL` for a second independently created Space.

`HF_WORKER_TOKEN` is optional and only needed if you want authenticated Hub access to a private Space or a token-aware Gradio call. Redeploy Vercel after changing variables.

Vercel endpoints:
- `GET /api/providers` checks the Gradio API schema.
- `POST /api/providers` dispatches one fixed role through `/gradio_api/call/run_qill_worker`, then polls the returned event ID.

Failover is safe: Vercel tries the next Space only if the initial submission is rejected with 429/503 or cannot connect before acceptance. Once Gradio returns an event ID, Vercel never replays that task elsewhere, avoiding duplicate work. If polling fails, inspect the Space before retrying.

## Scheduling and checkpoints

The GitHub Actions workflow has `max-parallel: 3` and runs every 30 minutes (plus manual dispatch). The consolidation job writes worker reports to the `qill-state` branch. This is recurring batch execution, not always-on compute. Hugging Face Space tasks return their reports to the caller and do not write the checkpoint branch.

## Safety and cost controls

- No paid model APIs or Hugging Face Jobs are called.
- No automatic account rotation, quota bypass, or paid fallback.
- Workers inspect only the public HackerCoderAI repository.
- No arbitrary shell commands, automatic code edits, or exploit attempts.
- Static findings are heuristic leads and require human verification.
