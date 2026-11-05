"""Qill Gradio Space demo for the public HackerCoderAI project."""
from __future__ import annotations

import asyncio
import importlib.util
import shutil
import tempfile
import time
import urllib.request
import zipfile
from pathlib import Path

import gradio as gr

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


async def ensure_repository() -> None:
    async with repo_lock:
        if (REPO_DIR / "workers" / "run_worker.py").is_file():
            return
        if REPO_DIR.exists():
            shutil.rmtree(REPO_DIR)
        response = await asyncio.to_thread(urllib.request.urlopen, ARCHIVE_URL, timeout=60)
        with response:
            archive_bytes = response.read(40_000_000)
        with tempfile.TemporaryDirectory(prefix="qill-source-") as temp_dir:
            archive_path = Path(temp_dir) / "source.zip"
            archive_path.write_bytes(archive_bytes)
            with zipfile.ZipFile(archive_path) as bundle:
                members = bundle.namelist()
                if not members:
                    raise RuntimeError("The project archive was empty.")
                root_name = members[0].split("/", 1)[0]
                for member in members:
                    if member.startswith("/") or ".." in Path(member).parts:
                        raise RuntimeError("Unsafe path in project archive.")
                bundle.extractall(temp_dir)
            shutil.copytree(Path(temp_dir) / root_name, REPO_DIR)
        if not (REPO_DIR / "workers" / "run_worker.py").is_file():
            raise RuntimeError("Project checkout is incomplete.")


def execute_worker(role: str, goal: str) -> dict:
    module_path = REPO_DIR / "workers" / "run_worker.py"
    spec = importlib.util.spec_from_file_location("qill_worker_runtime", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load the fixed Qill worker module.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.run_role(role, goal)


async def run_qill_worker(role: str, goal: str) -> dict:
    """Run one fixed worker. Goal is data, never a shell command."""
    if role not in ALLOWED_ROLES:
        return {"ok": False, "error": "Worker role is not allowlisted."}
    goal = (goal or "Review this repository for safe, authorized improvements.")[:1500]
    async with slots:
        started = time.monotonic()
        try:
            await asyncio.wait_for(ensure_repository(), timeout=75)
            result = await asyncio.wait_for(
                asyncio.to_thread(execute_worker, role, goal),
                timeout=TASK_TIMEOUT_SECONDS,
            )
            return {
                "ok": True,
                "provider": "huggingface-space",
                "durationSeconds": round(time.monotonic() - started, 2),
                "result": result,
            }
        except asyncio.TimeoutError:
            return {"ok": False, "error": "Worker exceeded its time limit."}
        except Exception as exc:
            return {"ok": False, "error": type(exc).__name__ + ": " + str(exc)[:500]}


with gr.Blocks(title="Qill · HackerCoderAI", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        """
        # ◈ Q I L L
        **DISTRIBUTED PROJECT INTELLIGENCE**  
        HackerCoderAI · Eight bounded worker roles · Read-only demo

        Explore the public **Screwyougucci/HackerCoderAI** repository.
        Choose a worker, describe the objective, and inspect its JSON report.
        Your objective is plain text—not a command or code.
        """
    )
    with gr.Row():
        role = gr.Dropdown(
            choices=[(label, key) for key, label in ROLE_LABELS.items()],
            value="source-scanner",
            label="Worker role",
            scale=1,
        )
        run_button = gr.Button("▶ RUN WORKER", variant="primary", scale=0)
    goal = gr.Textbox(
        label="Objective",
        value="Review HackerCoderAI for safe, authorized improvements.",
        lines=3,
        max_lines=5,
        max_length=1500,
    )
    output = gr.JSON(label="Worker report")
    run_button.click(
        fn=run_qill_worker,
        inputs=[role, goal],
        outputs=output,
        concurrency_limit=MAX_CONCURRENCY,
        api_name="run_qill_worker",
    )
    gr.Markdown(
        """
        **Worker roster:** Research Scout · Source Scanner · Test Runner ·
        Pattern Miner · Validation Reviewer · Documentation Auditor ·
        Regression Watcher · Intelligence Synthesizer

        **Safety & limits:** up to 3 concurrent tasks; 4-minute task deadline;
        public repository only; no arbitrary shell commands or file modifications.
        Static matches are heuristic leads requiring human verification.
        """
    )
    gr.Examples(
        examples=[
            ["source-scanner", "Review the repository for common unsafe coding patterns."],
            ["test-runner", "Run the project's bounded unit-test suite."],
            ["documentation-auditor", "Check README links and documentation structure."],
            ["intelligence-synthesizer", "Summarize the repository's project inventory."],
        ],
        inputs=[role, goal],
    )

demo.queue(default_concurrency_limit=MAX_CONCURRENCY, max_size=12)
