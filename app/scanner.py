"""Read-only heuristic scanner. Matches are leads, never proof of a vulnerability."""
from pathlib import Path
import re

RULES = [
    ("PY-EVAL", "high", re.compile(r"\beval\s*\("), "Dynamic evaluation can execute attacker-controlled input."),
    ("PY-EXEC", "high", re.compile(r"\bexec\s*\("), "Dynamic execution can execute attacker-controlled input."),
    ("PY-SHELL", "high", re.compile(r"subprocess\.(?:run|Popen|call)\s*\([^\n]*shell\s*=\s*True"), "Shell invocation increases command-injection risk; inspect input flow."),
    ("JS-INNERHTML", "medium", re.compile(r"\.innerHTML\s*="), "Untrusted HTML assigned to innerHTML can cause DOM XSS."),
    ("JS-EVAL", "high", re.compile(r"\beval\s*\("), "Dynamic evaluation can execute attacker-controlled JavaScript."),
    ("SQL-CONCAT", "medium", re.compile(r"(?:SELECT|INSERT|UPDATE|DELETE)[^\n]*\+\s*[A-Za-z_]"), "String-built SQL may be injectable; prefer parameterized queries."),
    ("C-STRCPY", "medium", re.compile(r"\b(?:strcpy|sprintf)\s*\("), "Unbounded string operation; verify buffer sizing and consider safer APIs."),
    ("SECRET-LITERAL", "medium", re.compile(r"(?i)(?:api[_-]?key|secret|password)\s*=\s*['\"][^'\"]{8,}['\"]"), "Possible hard-coded credential; rotate if real and move to secret storage."),
]
ALLOWED = {".py", ".js", ".jsx", ".ts", ".tsx", ".c", ".h", ".cpp", ".hpp", ".sh", ".ps1"}

def scan_text(text: str, filename: str = "source") -> list[dict]:
    findings = []
    for number, line in enumerate(text.splitlines(), 1):
        for rule_id, severity, pattern, explanation in RULES:
            if pattern.search(line):
                findings.append({"rule": rule_id, "severity": severity,
                                 "line": number, "file": filename,
                                 "evidence": line.strip()[:240],
                                 "explanation": explanation})
    return findings

def scan_path(root: str, max_files: int = 500, max_bytes: int = 1_000_000) -> list[dict]:
    base = Path(root).expanduser().resolve()
    if not base.is_dir():
        raise ValueError("Scan path must be an existing directory.")
    findings, count = [], 0
    for path in base.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in ALLOWED:
            continue
        if any(part in {".git", ".venv", "node_modules", "__pycache__"} for part in path.parts):
            continue
        count += 1
        if count > max_files:
            break
        try:
            if path.stat().st_size > max_bytes:
                continue
            findings.extend(scan_text(path.read_text(encoding="utf-8", errors="replace"),
                                      str(path.relative_to(base))))
        except OSError:
            continue
    return findings
