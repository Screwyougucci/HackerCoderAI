"""Authenticated, bounded Qill worker API for a Hugging Face Docker Space."""
from __future__ import annotations
import asyncio, hmac, importlib.util, os, shutil, tempfile, time, urllib.request, zipfile
from pathlib import Path
from typing import Literal
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
slots = asyncio.Semaphore(MAX_CONCURRENCY)
repo_lock = asyncio.Lock()
app = FastAPI(title="Qill Worker", version="1.0.0")

class WorkerRequest(BaseModel):
    role: Literal[
        "research-scout", "source-scanner", "test-runner", "pattern-miner",
        "validation-reviewer", "documentation-auditor", "regression-watcher",
        "intelligence-synthesizer",
    ]
    goal: str = Field(default="Review this repository for safe, authorized improvements.", max_length=1500)

def authorized(supplied: str | None) -> bool:
    expected = os.environ.get("QILL_WORKER_KEY", "")
    return bool(expected and supplied and hmac.compare_digest(expected, supplied))

async def ensure_repository() -> None:
    async with repo_lock:
        if (REPO_DIR / "workers" / "run_worker.py").is_file():
            return
        if REPO_DIR.exists():
            shutil.rmtree(REPO_DIR)
        archive = await asyncio.to_thread(urllib.request.urlopen, ARCHIVE_URL, timeout=60)
        with archive:
            data = archive.read(40_000_000)
        with tempfile.TemporaryDirectory(prefix="qill-source-") as tmp:
            archive_path = Path(tmp) / "source.zip"
            archive_path.write_bytes(data)
            with zipfile.ZipFile(archive_path) as bundle:
                root = bundle.namelist()[0].split("/", 1)[0]
                bundle.extractall(tmp)
            extracted = Path(tmp) / root
            shutil.copytree(extracted, REPO_DIR)
        if not (REPO_DIR / "workers" / "run_worker.py").is_file():
            raise HTTPException(status_code=503, detail="Worker source checkout is incomplete.")

def execute_worker(role: str, goal: str) -> dict:
    module_path = REPO_DIR / "workers" / "run_worker.py"
    spec = importlib.util.spec_from_file_location("qill_worker_runtime", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load the fixed Qill worker module.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.run_role(role, goal)

@app.get("/health")
async def health():
    return {"ok": True, "provider": "huggingface-space", "maxConcurrency": MAX_CONCURRENCY,
            "availableSlots": slots._value}

@app.post("/run")
async def run_worker(payload: WorkerRequest, x_qill_worker_key: str | None = Header(default=None)):
    if not authorized(x_qill_worker_key):
        raise HTTPException(status_code=401, detail="Unauthorized")
    if payload.role not in ALLOWED_ROLES:
        raise HTTPException(status_code=400, detail="Role is not allowlisted")
    async with slots:
        started = time.monotonic()
        try:
            await asyncio.wait_for(ensure_repository(), timeout=75)
            result = await asyncio.wait_for(
                asyncio.to_thread(execute_worker, payload.role, payload.goal),
                timeout=TASK_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            raise HTTPException(status_code=504, detail="Worker deadline exceeded")
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=type(exc).__name__ + ": " + str(exc)[:500])
        return {"ok": True, "provider": "huggingface-space",
                "durationSeconds": round(time.monotonic() - started, 2), "result": result}
