"""Bounded background agent loop with durable progress and a strict tool allowlist."""
import json
import threading
import time

from .memory import MemoryStore
from .model import generate
from .patterns import analyze_patterns
from .scanner import scan_path
from .web import search_web

MAX_STEPS = 24
MAX_SECONDS = 30 * 60
_STOP_EVENTS: dict[str, threading.Event] = {}
_LOCK = threading.Lock()
_WORKERS: dict[str, threading.Thread] = {}

def cancel_task(task_id: str) -> None:
    event = _STOP_EVENTS.get(task_id)
    if event:
        event.set()

def _json_action(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("Agent did not return a JSON action.")
    value = json.loads(text[start:end + 1])
    if not isinstance(value, dict):
        raise ValueError("Agent action must be a JSON object.")
    return value

def _record(store: MemoryStore, task_id: str, status: str, detail: str = ""):
    store.update_task(task_id, status=status, detail=detail)

def run_task(store: MemoryStore, task_id: str, goal: str, workspace: str = "") -> None:
    started = time.monotonic()
    prior = store.get_task(task_id) or {}
    prior_steps = prior.get("steps", [])
    observations: list[str] = [
        f"Checkpoint from step {item['step']} ({item['action']}): {item['detail'][:2500]}"
        for item in prior_steps[-12:]
    ]
    findings: list[dict] = []
    search_results: list[dict] = []
    scanned = False
    for item in prior_steps:
        detail = item.get("detail", "")
        try:
            if item.get("action") == "scan_workspace" and "\\n" in detail:
                findings = json.loads(detail.split("\\n", 1)[1])
                scanned = True
            elif item.get("action") == "search_web" and "\\n" in detail:
                search_results.extend(json.loads(detail.split("\\n", 1)[1]))
        except (ValueError, TypeError):
            observations.append("A previous result could not be restored from its checkpoint.")
    step_offset = max((int(item.get("step", 0)) for item in prior_steps), default=0)
    stop_event = _STOP_EVENTS.setdefault(task_id, threading.Event())
    _record(store, task_id, "running", "Starting task and preparing a plan.")
    system = (
        "You are HackerCoderAI, an autonomous but bounded coding and defensive-security agent. "
        "Choose exactly one next action as JSON. Allowed actions only: "
        '{"action":"search_web","query":"..."}; '
        '{"action":"scan_workspace"}; '
        '{"action":"analyze_patterns"}; '
        '{"action":"finish","summary":"..."}. '
        "Use search_web for public research. scan_workspace is read-only and only scans the user-supplied workspace. "
        "Use analyze_patterns after gathering evidence. Never invent tool results. "
        "Do not request credentials, attack systems, run commands, edit files, or make external changes. "
        "Work toward the user's goal, avoid repeating completed searches, and finish when evidence is sufficient. "
        "Return JSON only."
    )
    for iteration in range(1, MAX_STEPS + 1):
        step = step_offset + iteration
        if stop_event.is_set():
            _record(store, task_id, "cancelled", "Stopped by user.")
            return
        if time.monotonic() - started > MAX_SECONDS:
            _record(store, task_id, "paused", "Time budget reached; progress checkpoint saved.")
            return
        prompt = (
            f"USER GOAL:\n{goal[:3000]}\n"
            f"WORKSPACE: {workspace or 'not supplied'}\n"
            f"STEP: {step}/{MAX_STEPS}\n"
            f"WORKSPACE_ALREADY_SCANNED: {scanned}\n"
            f"OBSERVATIONS (latest first, bounded):\n" + "\n---\n".join(observations[-8:]) +
            "\nChoose the next allowed action. Do not repeat an action unless there is a reason."
        )
        try:
            action = _json_action(generate([
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ]))
            kind = action.get("action")
            if kind == "finish":
                summary = str(action.get("summary", "Task completed."))[:4000]
                report = summary
                if findings:
                    report += "\n\nPattern analysis:\n" + json.dumps(analyze_patterns(findings, search_results), indent=2)[:5000]
                if search_results:
                    report += "\n\nSources:\n" + "\n".join(f"- {x['title']}: {x['url']}" for x in search_results[:20])
                store.add_task_step(task_id, step, "finish", report)
                _record(store, task_id, "completed", report)
                return
            if kind == "search_web":
                query = " ".join(str(action.get("query", "")).split())[:300]
                if not query:
                    raise ValueError("Search action had no query.")
                results = search_web(query, max_results=6)
                search_results.extend(results)
                result_text = json.dumps(results, ensure_ascii=False)[:6500] if results else "No usable results."
                observations.append("WEB SEARCH: " + query + "\n" + result_text)
                store.add_task_step(task_id, step, "search_web", "Query: " + query + "\n" + result_text)
            elif kind == "scan_workspace":
                if not workspace:
                    observations.append("WORKSPACE SCAN: unavailable; user did not provide a workspace path.")
                    store.add_task_step(task_id, step, "scan_workspace", "Skipped: no workspace path.")
                elif scanned:
                    observations.append("WORKSPACE SCAN: already completed; use existing findings.")
                else:
                    findings = scan_path(workspace)
                    scanned = True
                    result_text = json.dumps(findings[:100], ensure_ascii=False)[:9000]
                    observations.append(f"WORKSPACE SCAN: {len(findings)} heuristic findings. " + result_text)
                    store.add_task_step(task_id, step, "scan_workspace", f"{len(findings)} heuristic findings.\n{result_text}")
            elif kind == "analyze_patterns":
                report = analyze_patterns(findings, search_results)
                observations.append("PATTERN ANALYSIS: " + json.dumps(report, ensure_ascii=False)[:5000])
                store.add_task_step(task_id, step, "analyze_patterns", json.dumps(report, indent=2))
            else:
                raise ValueError(f"Unsupported agent action: {kind!r}")
            _record(store, task_id, "running", f"Completed step {step}: {kind}")
        except Exception as exc:
            message = f"{type(exc).__name__}: {exc}"
            observations.append("TOOL/MODEL ERROR: " + message)
            store.add_task_step(task_id, step, "error", message)
            _record(store, task_id, "running", f"Step {step} had an error; continuing cautiously.")
    partial = "Step budget reached for this run. Checkpoint saved; resume to continue.\n" + "\n\n".join(observations[-8:])
    _record(store, task_id, "paused", partial)

def start_task(store: MemoryStore, task_id: str, goal: str, workspace: str = "") -> None:
    with _LOCK:
        thread = threading.Thread(target=run_task, args=(store, task_id, goal, workspace),
                                  daemon=True, name=f"agent-{task_id[:8]}")
        _WORKERS[task_id] = thread
        _STOP_EVENTS[task_id] = threading.Event()
        thread.start()
