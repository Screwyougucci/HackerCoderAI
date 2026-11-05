# HackerCoderAI

**Offline-first coding and defensive security assistant** for Windows, Linux, and WSL2.

HackerCoderAI is a local project, separate from DarthLinux. It is designed to run on CPU-only systems and keeps chat history and user-approved memories in a local SQLite database. It includes two model profiles:

| Profile | GGUF quantization | Purpose |
|---|---|---|
| **v2** | Q2_K | Smallest footprint; use when memory is tight. Lower answer quality. |
| **v4** | Q4_K_M | Better coding and analysis quality; recommended default. |

Both profiles use the same base model: **Qwen2.5-Coder-3B-Instruct**. Quantized model files are not included in Git; download them separately from a trusted model publisher and verify their checksums.

## Current status

This repository starts with a runnable local foundation: a FastAPI chat UI, llama.cpp-compatible model loading, SQLite conversation memory, and a read-only source scanner for common risky code patterns. Advanced features listed below are roadmap items, not claims that they are already implemented.

## Features

- Local browser UI; binds to 127.0.0.1 by default.
- GGUF model selection via configuration (Q2_K or Q4_K_M).
- Persistent local conversations and explicit `/remember` notes in SQLite.
- Defensive source review for common risky patterns in Python, JavaScript/TypeScript, C/C++, shell, and PowerShell.
- No telemetry, no mandatory cloud API, no automatic network scanning.
- Clear separation between findings and confirmed vulnerabilities: static matches are leads requiring manual review.

## Requirements

- Python 3.10+
- 8 GB RAM minimum recommended; 16 GB preferred.
- CPU inference supported. No NVIDIA GPU is required.
- A GGUF model file compatible with llama.cpp.
- Internet is needed only to install dependencies/download a model; runtime can be offline.

## Quick start

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux / WSL: source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and set `MODEL_PATH` to your local GGUF file. Then:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8001
```

Open http://127.0.0.1:8001. The app remains usable for source scanning without a model; chat requires a configured model.

## Model setup

Use Qwen2.5-Coder-3B-Instruct GGUF from a publisher you trust. Place files under `models/` (the directory is git-ignored), then set:

```dotenv
MODEL_PATH=models/qwen2.5-coder-3b-instruct-q4_k_m.gguf
MODEL_PROFILE=v4
```

For the smaller profile, use a genuine Q2_K GGUF file and set `MODEL_PROFILE=v2`. Quantization filenames vary by publisher; confirm the actual quantization in the model card rather than renaming a file.

## Safety and privacy

- Treat model output as suggestions, not proof.
- Only scan source code you own or are authorized to assess.
- The scanner reads files; it does not execute code, exploit targets, or make network requests.
- Memory is local. Do not store passwords, API keys, tokens, or other secrets.
- The web server binds to localhost by default. Do not expose it to a LAN or the public internet without adding authentication and transport security.

## Roadmap

1. Model download/checksum helper and profile validation.
2. Improved scanner rules with tests and severity confidence.
3. Local CVE-feed import (offline data; no implied live feed).
4. Code workspace/editor and hardware/RAM dashboard.
5. Exportable reports and configurable retention.

## License

MIT. See [LICENSE](LICENSE).
