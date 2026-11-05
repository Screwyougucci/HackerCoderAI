"""Download the default abliterated GGUF model from Hugging Face."""
from pathlib import Path
from huggingface_hub import hf_hub_download

REPO_ID = "tensorblock/Qwen2.5-3B-Instruct-abliterated-GGUF"
FILENAME = "Qwen2.5-3B-Instruct-abliterated-Q4_K_M.gguf"
DEST = Path("data/models")
def main():
    DEST.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {FILENAME} (~1.93 GB) from {REPO_ID} ...")
    path = hf_hub_download(
        repo_id=REPO_ID,
        filename=FILENAME,
        local_dir=DEST,
    )
    print(f"Model ready: {path}")
    print("Set MODEL_PATH to this file if you use a custom location.")
if __name__ == "__main__":
    main()
