from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from .config import settings
from .memory import MemoryStore
from .model import generate
from .scanner import scan_path

app = FastAPI(title=settings.app_name)
store = MemoryStore(settings.database_path)

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>HackerCoderAI</title><style>
:root{color-scheme:dark;--bg:#080b12;--panel:#101725;--line:#26344a;--cyan:#42e8d5;--red:#ff3158}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at top,#172337,var(--bg) 60%);color:#e7edf7;font:15px system-ui}
main{max-width:1000px;margin:40px auto;padding:20px}.brand{color:var(--cyan);letter-spacing:.18em;font-weight:800}
h1{font-size:clamp(28px,5vw,48px);margin:8px 0}.muted{color:#91a1b8}.panel{background:#101725dd;border:1px solid var(--line);border-radius:16px;padding:20px;margin:18px 0}
textarea,input{width:100%;background:#080e18;color:#e7edf7;border:1px solid var(--line);border-radius:10px;padding:12px;font:inherit}
textarea{min-height:110px}button{background:var(--cyan);color:#061116;border:0;border-radius:9px;padding:11px 18px;font-weight:800;cursor:pointer;margin-top:10px}
pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#080e18;padding:14px;border-radius:10px;border:1px solid var(--line)}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}@media(max-width:700px){.grid{grid-template-columns:1fr}}
</style></head><body><main><div class="brand">HACKERCODERAI // LOCAL MODE</div><h1>Code smarter. Audit defensively.</h1>
<p class="muted">Offline-first · CPU inference · Local SQLite memory · No telemetry</p>
<div class="panel"><h2>Assistant</h2><p class="muted">Use /remember followed by a note to save a local memory. Do not save secrets.</p>
<form method="post" action="/chat"><textarea name="message" placeholder="Ask about code, debugging, or defensive security..." required></textarea><button>Send prompt</button></form>
{%CHAT%}</div><div class="grid"><section class="panel"><h2>Source scanner</h2><p class="muted">Read-only heuristic review of a local directory. Findings require manual validation.</p>
<form method="post" action="/scan"><input name="path" placeholder="/path/to/your/project" required><button>Scan directory</button></form>{%SCAN%}</section>
<section class="panel"><h2>System profile</h2><p>Model profile: <b>PROFILE</b></p><p>Model configured: <b>MODEL</b></p><p class="muted">Q2_K = compact v2 · Q4_K_M = quality v4</p></section></div></main></body></html>"""

last_chat = ""
last_scan = ""

def render():
    page = PAGE.replace("PROFILE", settings.model_profile)
    page = page.replace("MODEL", "ready" if settings.model_file else "not configured")
    page = page.replace("{%CHAT%}", last_chat).replace("{%SCAN%}", last_scan)
    return page

@app.get("/", response_class=HTMLResponse)
def home():
    return render()

@app.post("/chat", response_class=HTMLResponse)
def chat(message: str = Form(...)):
    global last_chat
    prompt = message.strip()
    if prompt.startswith("/remember "):
        try:
            store.remember(prompt[len("/remember "):])
            answer = "Saved a local memory."
        except ValueError as exc:
            answer = str(exc)
    else:
        store.add_message("user", prompt)
        memories = store.memories()
        messages = [{"role":"system","content":
            "You are HackerCoderAI, an offline coding and defensive security assistant. "
            "Support authorized code review, safe testing, and remediation. Do not claim "
            "heuristic findings are confirmed vulnerabilities. Never request secrets. "
            + (" User-approved notes: " + " | ".join(memories) if memories else "")}]
        messages.extend(store.recent_messages())
        try:
            answer = generate(messages)
        except Exception as exc:
            answer = f"Model unavailable: {exc}"
        store.add_message("assistant", answer)
    last_chat = "<pre>" + answer.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;") + "</pre>"
    return render()

@app.post("/scan", response_class=HTMLResponse)
def scan(path: str = Form(...)):
    global last_scan
    try:
        findings = scan_path(path)
        if not findings:
            last_scan = "<pre>No heuristic matches. This is not proof that the code is secure.</pre>"
        else:
            lines = [f'{f["severity"].upper()} {f["rule"]} — {f["file"]}:{f["line"]}\n{f["explanation"]}\nEvidence: {f["evidence"]}' for f in findings[:100]]
            last_scan = "<pre>" + "\n\n".join(lines).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;") + "</pre>"
    except Exception as exc:
        last_scan = "<pre>Scan error: " + str(exc).replace("<","&lt;") + "</pre>"
    return render()
