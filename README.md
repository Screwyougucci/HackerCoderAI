# HackerCoderAI

A local-first coding and defensive-security assistant powered by an abliterated Qwen2.5-3B-Instruct GGUF model.

## What it can do

- Local chat and persistent SQLite memory.
- Optional live public-web research from the chat UI, with source URLs included in the answer.
- Automatically trigger web research for clearly time-sensitive or research-oriented prompts, or tick **Use live web research**.
- Read-only source-code heuristic scanner.
- Background agent tasks with multi-step planning, progress checkpoints, cancellation, and resume after app restart.
- Pattern analysis that groups repeated findings by rule and file, and tracks source-domain frequency.
- CPU-only inference through llama.cpp.
- Windows executable build through GitHub Actions.

## Model

Default: **Qwen2.5-3B-Instruct-abliterated Q4_K_M**. The model weights are separate from the EXE and downloaded with `python -m app.download_model`. Abliteration changes refusal behavior; it does not improve factual accuracy or make outputs inherently safe.

## Run

```powershell
python -m pip install -r requirements.txt huggingface_hub
python -m app.download_model
python -m app.desktop
```

Open `http://127.0.0.1:8001`. The Windows EXE is published as an artifact by the **Build Windows EXE** workflow after a successful run.

## Agent behavior and current limits

The background agent runs in a worker thread for up to 30 minutes per run and up to 24 model/tool steps per run. It records each step in SQLite, pauses at its budget, and can be resumed from the saved step history. It can search public sources, perform a read-only scan of a user-supplied local workspace, and group repeated heuristic findings into patterns. It is not yet a full Grok/Operator equivalent: it does not deeply browse arbitrary pages, edit files, execute shell commands, install software, send messages, or make purchases. Those capabilities need separate sandboxed tools and explicit approval gates.

The app binds to `127.0.0.1` only. Search queries are sent to DuckDuckGo; your chat transcript and local source files are not sent as search queries. Web snippets are untrusted input and may be incomplete or malicious. Verify important claims against original sources.

## Security

Only analyze code and systems you own or are authorized to assess. The scanner is read-only and heuristic; findings are leads, not proof. Do not expose the local web UI publicly without authentication and TLS. Never store passwords, tokens, or API keys in memory.

## Build status

The repository contains a Windows build workflow. A build is not considered complete until GitHub Actions succeeds and the EXE is downloaded and tested on Windows.

## License

MIT.
