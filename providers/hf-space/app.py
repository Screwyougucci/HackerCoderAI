"""Qill Gradio demo + authenticated HTTP worker API for Hugging Face Spaces."""
from __future__ import annotations

import asyncio
import hmac
import importlib.util
import os
import shutil
import tempfile
import time
import urllib.request
import zipfile
from pathlib import Path
from typing import Literal

import gradio as gr
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

REPO_DIR = Path("/tmp/HackerCoderAI")
ARCHIVE_URL = "https://github.com/Screwyougucci/HackerCoderAI/archive/refs/heads/main.zip"
MAX_CONCURRENCY = 3
TASK_TIMEOUT_SECONDS = 240
ALLOWED_ROLES = {
    "research-scout", "source-scanner", "test-runner", "pattern-miner",
    "validation-reviewer", "documentation-auditor", "regression-watcher",
    "intelligence-synthesizer",
}
ROLE_LABELS = {
    "research-scout": "Research Scout",
    "source-scanner": "Source Scanner",
    "test-runner": "Test Runner",
    "pattern-miner": "Pattern Miner",
    "validation-reviewer": "Validation Reviewer",
    "documentation-auditor": "Documentation Auditor",
    "regression-watcher": "Regression Watcher",
    "intelligence-synthesizer": "Intelligence Synthesizer",
}
slots = asyncio.Semaphore(MAX_CONCURRENCY)
repo_lock = asyncio.Lock()
app = FastAPI(title="Qill Worker API", version="1.1.0")


class WorkerRequest(BaseModel):
    role: Literal[
        "research-scout", "source-scanner", "test-runner", "pattern-miner",
        "validation-reviewer", "documentation-auditor", "regression-watcher",
        "intelligence-synthesizer",
    ]
    goal: str = Field(
        default="Review this repository for safe, authorized improvements.",
        max_length=1500,
    )


def authorized(supplied: str | None) -> bool:
    expected = os.environ.get("QILL_WORKER_KEY", "")
    return bool(expected and supplied and hmac.compare_digest(expected, supplied))


async def ensure_repository() -> None:
    async with repo_lock:
        if (REPO_DIR / "workers" / "run_worker.py").is_file():
            return
        if REPO_DIR.exists():
            shutil.rmtree(REPO_DIR)
        archive_response = await asyncio.to_thread(
            urllib.request.urlopen, ARCHIVE_URL, timeout=60
        )
        with archive_response:
            archive_bytes = archive_response.read(40_000_000)
        with tempfile.TemporaryDirectory(prefix="qill-source-") as temp_dir:
            archive_path = Path(temp_dir) / "source.zip"
            archive_path.write_bytes(archive_bytes)
            with zipfile.ZipFile(archive_path) as bundle:
                members = bundle.namelist()
                if not members:
                    raise RuntimeError("The repository archive was empty.")
                root_name = members[0].split("/", 1)[0]
                # Reject archive entries that could escape the temporary directory.
                for member in members:
                    if member.startswith("/") or ".." in Path(member).parts:
                        raise RuntimeError("Unsafe path in source archive.")
                bundle.extractall(temp_dir)
            extracted = Path(temp_dir) / root_name
            shutil.copytree(extracted, REPO_DIR)
        if not (REPO_DIR / "workers" / "run_worker.py").is_file():
            raise RuntimeError("Worker source checkout is incomplete.")


def execute_worker(role: str, goal: str) -> dict:
    module_path = REPO_DIR / "workers" / "run_worker.py"
    spec = importlib.util.spec_from_file_location("qill_worker_runtime", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load the fixed Qill worker module.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.run_role(role, goal)


async def run_task(role: str, goal: str) -> dict:
    if role not in ALLOWED_ROLES:
        raise ValueError("Role is not allowlisted.")
    async with slots:
        started = time.monotonic()
        await asyncio.wait_for(ensure_repository(), timeout=75)
        result = await asyncio.wait_for(
            asyncio.to_thread(execute_worker, role, goal[:1500]),
            timeout=TASK_TIMEOUT_SECONDS,
        )
        return {
            "ok": True,
            "provider": "huggingface-space",
            "durationSeconds": round(time.monotonic() - started, 2),
            "result": result,
        }


async def demo_run(role: str, goal: str):
    """Public, bounded demo. Goal is data only and is never executed as a command."""
    try:
        return await run_task(role, goal or "Review this repository for safe improvements.")
    except asyncio.TimeoutError:
        return {"ok": False, "error": "Worker deadline exceeded (4 minutes)."}
    except Exception as exc:
        return {"ok": False, "error": type(exc).__name__ + ": " + str(exc)[:500]}


@app.get("/health")
async def health():
    return {
        "ok": True,
        "provider": "huggingface-space",
        "maxConcurrency": MAX_CONCURRENCY,
        "availableSlots": slots._value,
    }


@app.post("/run")
async def run_worker(
    payload: WorkerRequest,
    x_qill_worker_key: str | None = Header(default=None),
):
    if not authorized(x_qill_worker_key):
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        return await run_task(payload.role, payload.goal)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Worker deadline exceeded")
    except Exception as exc:
        raise HTTPException(
            status_code=503 if isinstance(exc, (OSError, RuntimeError)) else 500,
            detail=type(exc).__name__ + ": " + str(exc)[:500],
        )


with gr.Blocks(title="Qill · HackerCoderAI", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        """
        # ◈ QILL / PROJECT INTELLIGENCE
        **HackerCoderAI · bounded multi-role repository demo**

        Explore the public HackerCoderAI project with one of eight fixed workers.
        This demo performs read-only analysis and bounded tests. Findings are
        heuristic leads, not confirmed vulnerabilities. It does not modify files,
        run user-supplied shell commands, or access private repositories.
        """
    )
    with gr.Row():
        role = gr.Dropdown(
            choices=[(label, key) for key, label in ROLE_LABELS.items()],
            value="source-scanner",
            label="Worker role",
        )
        run_button = gr.Button("▶ Run worker", variant="primary")
    goal = gr.Textbox(
        label="Objective",
        value="Review HackerCoderAI for safe, authorized improvements.",
        lines=3,
        max_lines=5,
        max_length=1500,
    )
    output = gr.JSON(label="Worker report")
    run_button.click(
        fn=demo_run,
        inputs=[role, goal],
        outputs=[output],
        concurrency_limit=MAX_CONCURRENCY,
        api_name="run_qill_worker",
    )
    gr.Markdown(
        """
        **Available roles:** Research Scout · Source Scanner · Test Runner ·
        Pattern Miner · Validation Reviewer · Documentation Auditor ·
        Regression Watcher · Intelligence Synthesizer

        **Limits:** maximum 3 concurrent tasks per Space; each task has a
        4-minute deadline. The public demo uses the checked-in public repository.
        """
    )

demo.queue(default_concurrency_limit=MAX_CONCURRENCY, max_size=12)
app = gr.mount_gradio_app(app, demo, path="/")
