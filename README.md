# HackerCoderAI

A local-first coding and defensive-security assistant powered by an abliterated Qwen2.5-3B-Instruct GGUF model.

## What it can do

- Local chat and persistent SQLite memory.
- Optional live public-web research from the chat UI, with source URLs included in the answer.
- Automatically trigger web research for clearly time-sensitive or research-oriented prompts, or tick **Use live web research**.
- Read-only source-code heuristic scanner.
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

HackerCoderAI can take a research or analysis request, gather web search results, reason over them locally, and return a sourced result. It is a bounded first-stage agent, not a full Grok/Operator equivalent yet. It does not currently browse arbitrary pages deeply, execute shell commands, edit project files, install software, send messages, or make purchases. Those capabilities need separate tools, sandboxing, and explicit approval gates before implementation.

The app binds to `127.0.0.1` only. Search queries are sent to DuckDuckGo; your chat transcript and local source files are not sent as search queries. Web snippets are untrusted input and may be incomplete or malicious. Verify important claims against original sources.

## Security

Only analyze code and systems you own or are authorized to assess. The scanner is read-only and heuristic; findings are leads, not proof. Do not expose the local web UI publicly without authentication and TLS. Never store passwords, tokens, or API keys in memory.

## Build status

The repository contains a Windows build workflow. A build is not considered complete until GitHub Actions succeeds and the EXE is downloaded and tested on Windows.

## License

MIT.
