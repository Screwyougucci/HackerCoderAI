# Qill distributed cloud architecture

## Current deployment slice

Qill uses Vercel as the control plane and GitHub Actions as the first real compute provider. Eight independent standard Ubuntu runner VMs execute bounded worker jobs in parallel. The workflow is scheduled every 30 minutes and can also be dispatched manually.

| Provider | Role | State |
|---|---|---|
| Vercel Hobby | Dashboard and control API | Existing project, auto-deploys from remote/ |
| GitHub Actions | Eight ephemeral worker VMs | Active when workflow is enabled |
| Hugging Face Spaces | Optional model/inference adapter | Standby; requires a free eligible Space and quota |
| Cloudflare Workers | Optional lightweight coordination adapter | Standby; requires user deployment |

GitHub's public-repository standard runners are documented as free and unlimited. This depends on keeping the repository public and using standard runners, not larger paid runners. The worker VMs are temporary: they are created for a job and discarded after it completes.

## Eight worker roles

1. Research Scout — queries public search for a supplied objective and records source links/snippets.
2. Source Scanner — read-only heuristic scan of the checked-out repository.
3. Test Runner — runs the repository's unittest suite with a strict timeout.
4. Pattern Miner — groups findings from the previous checkpoint.
5. Validation Reviewer — labels scanner candidates as requiring human verification.
6. Documentation Auditor — checks README/docs presence and relative links.
7. Regression Watcher — compares current candidates with the prior checkpoint.
8. Intelligence Synthesizer — records project inventory and next-step recommendation.

A ninth, lightweight consolidation job merges artifacts and writes a checkpoint. It is orchestration, not an extra research worker.

## Persistence

Worker artifacts are merged into state/latest.json and state/workers/*.json on the dedicated qill-state branch. The dashboard reads this public checkpoint. A new worker cycle can use the last checkpoint as context.

## Limits and guardrails

- No paid Vercel Sandbox or AI Gateway calls are made by this design.
- No payment method or paid fallback is configured.
- No model-generated shell commands are executed.
- Source scanning is heuristic and read-only.
- Tests run only against this repository in ephemeral GitHub-hosted runners.
- The research worker stores links and snippets; it does not treat web content as instructions.
- External provider adapters remain inactive until their free resources are explicitly deployed.
- GitHub schedules are best-effort and may start late. The system is continuous in recurring cycles, not an always-on process.
