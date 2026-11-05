# HackerCoderAI Remote

A Vercel-hosted remote control panel for HackerCoderAI.

## Architecture

- Next.js dashboard on Vercel.
- Vercel AI Gateway performs hosted model inference. Default model: `alibaba/qwen3-coder-30b-a3b`.
- `@vercel/sandbox` creates an isolated Firecracker Linux microVM for each smoke test.
- The initial sandbox has 1 vCPU, a 2 GB memory profile, a 2-minute timeout, no outbound network, and is discarded after the test.
- The local Windows EXE remains independent and continues using the local GGUF model.

## Deploy

Set the sensitive Vercel environment variable `HACKERCODERAI_ACCESS_KEY` for production. The dashboard requires this key before it will call the AI or create a sandbox. Do not commit the key or place it in client-side source. The page accepts it in a password field and sends it only as a request header.


Create a Vercel project linked to this repository with the project root set to `remote`. Use Node.js 22 or later. Enable AI Gateway for the project. The deployed Vercel runtime uses its OIDC identity for AI Gateway and Sandbox access; if your team requires an API key instead, configure it as a server-side environment variable in Vercel, never in browser code.

## Test

- `GET /api/health` checks the deployed API.
- The dashboard's **Run AI + sandbox test** button calls the hosted model and then runs a fixed Python smoke test inside a network-disabled Vercel Sandbox.
- The API reports the model response and sandbox exit code/output.

## Safety and current scope

The first release does not execute arbitrary model-generated shell commands, modify repositories, or scan third-party systems. The sandbox test is fixed and network-disabled. The task text is sent to the selected AI Gateway model. Longer durable workflows, authenticated user accounts, persistent task history, and explicit approval-gated repository operations are not implemented in this first smoke-test release.

## Local development

```bash
npm install
npm run dev
```

Local calls to Vercel Sandbox require Vercel credentials and project linkage as described in the Vercel Sandbox documentation.
