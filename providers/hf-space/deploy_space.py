"""Create/update the Qill Gradio Space using a user-supplied write token.

Run from any machine with Python 3.10+:
    pip install -U huggingface_hub
    python deploy_space.py

The token is requested with hidden input and is never written to disk.
"""
from __future__ import annotations

import getpass
import os
from pathlib import Path

from huggingface_hub import HfApi, HfHubHTTPError

REPO_ID = "Smatt324/qill-project-intelligence"
SPACE_DIR = Path(__file__).resolve().parent


def main() -> None:
    token = os.environ.get("HF_TOKEN") or getpass.getpass(
        "Hugging Face write token (input hidden): "
    ).strip()
    if not token:
        raise SystemExit("No token supplied; nothing was changed.")

    api = HfApi(token=token)
    try:
        identity = api.whoami()
        print("Authenticated as:", identity.get("name", "Hugging Face user"))
        api.create_repo(
            repo_id=REPO_ID,
            repo_type="space",
            space_sdk="gradio",
            space_hardware="zero-a10g",
            private=False,
            exist_ok=True,
        )
        api.upload_folder(
            repo_id=REPO_ID,
            repo_type="space",
            folder_path=str(SPACE_DIR),
            ignore_patterns=["__pycache__", "*.pyc", ".DS_Store"],
            commit_message="Deploy Qill project intelligence demo",
        )
    except HfHubHTTPError as exc:
        status = getattr(exc.response, "status_code", None)
        if status == 402:
            raise SystemExit(
                "Hugging Face refused free Space creation for this account. "
                "No paid hardware was requested. Do not upgrade or add billing."
            ) from exc
        if status in (401, 403):
            raise SystemExit(
                "The token needs write access to repositories. Create a Hugging Face "
                "write token and run this script again; do not paste it into chat."
            ) from exc
        raise

    print("Space files uploaded.")
    print("Demo: https://huggingface.co/spaces/" + REPO_ID)
    print("Agent API guide: https://huggingface.co/spaces/" + REPO_ID + "/agents.md")
    print("Runtime URL: https://smatt324-qill-project-intelligence.hf.space")


if __name__ == "__main__":
    main()
