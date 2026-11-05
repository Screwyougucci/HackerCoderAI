# HackerCoderAI

**Local-first coding and defensive security assistant** for Windows, Linux, and WSL2.

## Model

The default model is **Qwen2.5-3B-Instruct-abliterated**, using the Q4_K_M GGUF quantization. It is an abliterated model variant; that changes its refusal behavior, not its factual accuracy or safety. Treat generated code and security findings as untrusted until reviewed. The model is downloaded separately (about 1.93 GB) and is never bundled into the executable.

Model source: [tensorblock GGUF model card](https://huggingface.co/tensorblock/Qwen2.5-3B-Instruct-abliterated-GGUF). Review the model card and licensing before use.

## Windows executable

A GitHub Actions workflow builds `HackerCoderAI.exe` on Windows. After the workflow completes:

1. Open the repository's **Actions** tab.
2. Select **Build Windows EXE** and open the successful run.
3. Under **Artifacts**, download `HackerCoderAI-Windows` and extract it.
4. Run `HackerCoderAI.exe`. It starts the local interface at `http://127.0.0.1:8001` and opens your browser.

The executable does not contain the model weights. On first setup, open a terminal in the extracted project/source directory and run:

```powershell
python -m pip install -r requirements.txt huggingface_hub
python -m app.download_model
```

The downloaded model is stored in `data/models/`. The app uses it automatically when that file exists. Keep the model file beside the app's working data directory. A standalone distribution package with a bundled model would be roughly 2 GB larger.

## Internet access

Internet is used for the explicit Hugging Face model download and GitHub Actions build. The local app itself binds only to `127.0.0.1`; it does not expose its UI to the network. Live web search and fetching external pages from inside chat are not yet implemented. This avoids silently sending prompts or source code to third-party services.

## Features

- Local browser-based chat UI, launched by the Windows executable.
- CPU-only GGUF inference through llama.cpp.
- Persistent local conversations and explicit `/remember` notes in SQLite.
- Read-only heuristic source scanner for Python, JavaScript/TypeScript, C/C++, shell, and PowerShell.
- No telemetry and no mandatory cloud API.
- Findings are investigation leads, not confirmed vulnerabilities.

## Requirements

- Windows 10/11, Linux, or WSL2.
- 16 GB RAM recommended for the 3B Q4_K_M model; CPU inference is supported.
- Python 3.10+ for source/manual setup.
- About 2 GB free storage for the model, plus app/runtime space.

## Manual setup

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux / WSL: source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install huggingface_hub
python -m app.download_model
python -m app.desktop
```

Open `http://127.0.0.1:8001` if it does not open automatically.

## Defensive-use boundaries

Only scan source code you own or are authorized to assess. The scanner reads local files; it does not execute code, exploit targets, or perform network scans. Do not store passwords, API keys, tokens, or other secrets in chat memory. Do not expose the local UI to a LAN or public internet without authentication and transport security.

## Current status

The Windows build workflow and model downloader have been added. The executable has **not yet been built or tested**; use the Actions artifact only after a successful run. Live internet search from inside the assistant is a separate feature and is not included yet.

## License

MIT. See [LICENSE](LICENSE).
