#!/usr/bin/env python3
"""Bounded, non-LLM Qill worker tasks for public GitHub Actions runners."""
from __future__ import annotations
import argparse, json, re, subprocess, time, urllib.parse, urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", ".next", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", "qill-artifacts"}
TEXT_SUFFIXES = {".py", ".js", ".jsx", ".ts", ".tsx", ".json", ".yml", ".yaml", ".toml", ".md", ".txt"}
ROLES = {
    "research-scout": "Research Scout", "source-scanner": "Source Scanner",
    "test-runner": "Test Runner", "pattern-miner": "Pattern Miner",
    "validation-reviewer": "Validation Reviewer", "documentation-auditor": "Documentation Auditor",
    "regression-watcher": "Regression Watcher", "intelligence-synthesizer": "Intelligence Synthesizer",
}
RULES = [
    ("PY-SHELL-001", re.compile(r"subprocess\.(?:run|Popen|call|check_output)\([^\n]*shell\s*=\s*True"), "Review shell=True for command-injection risk."),
    ("PY-EVAL-001", re.compile(r"\b(?:eval|exec)\s*\("), "Review dynamic code execution and validate all inputs."),
    ("PY-PICKLE-001", re.compile(r"\bpickle\.(?:load|loads)\s*\("), "Never load pickle data from untrusted sources."),
    ("PY-YAML-001", re.compile(r"yaml\.load\s*\("), "Prefer yaml.safe_load for untrusted YAML."),
    ("TLS-VERIFY-001", re.compile(r"\bverify\s*=\s*False"), "TLS certificate verification is disabled."),
    ("JS-EVAL-001", re.compile(r"\beval\s*\("), "Review dynamic JavaScript evaluation."),
]
class ResultParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.items=[]; self.current=None; self.capture=None
    def handle_starttag(self, tag, attrs):
        attrs=dict(attrs); classes=attrs.get("class","")
        if tag=="a" and "result__a" in classes:
            self.current={"title":"","url":attrs.get("href","")}; self.capture="title"
        elif self.current is not None and tag in ("a","div") and "result__snippet" in classes:
            self.capture="snippet"
    def handle_data(self, data):
        if self.current is not None and self.capture:
            self.current[self.capture]=(self.current.get(self.capture,"")+data).strip()
    def handle_endtag(self, tag):
        if tag=="a" and self.current and self.capture=="title":
            self.items.append(self.current); self.current=None; self.capture=None
        elif tag=="div" and self.capture=="snippet": self.capture=None

def now(): return datetime.now(timezone.utc).isoformat()
def prior_state():
    url="https://raw.githubusercontent.com/Screwyougucci/HackerCoderAI/qill-state/state/latest.json"
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"Qill-Research-Agent/1.0"})
        with urllib.request.urlopen(req,timeout=8) as response: return json.loads(response.read(1_000_000).decode("utf-8"))
    except Exception: return {}
def research(goal):
    query=goal[:150] if goal and "Review this repository" not in goal else "secure software engineering testing Python JavaScript best practices"
    url="https://html.duckduckgo.com/html/?"+urllib.parse.urlencode({"q":query})
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 QillResearch/1.0"})
    try:
        with urllib.request.urlopen(req,timeout=12) as response:
            parser=ResultParser(); parser.feed(response.read(900_000).decode("utf-8","replace"))
        return {"query":query,"sources":parser.items[:6],"note":"Public search snippets only; open original sources to verify claims."}
    except Exception as exc: return {"query":query,"sources":[],"note":"Research endpoint unavailable: "+type(exc).__name__}
def iter_source_files():
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in SKIP_DIRS for part in path.parts): continue
        if path.suffix.lower() not in TEXT_SUFFIXES or path.name.startswith(".env"): continue
        if path.stat().st_size>1_000_000: continue
        yield path
def scan():
    findings=[]
    for path in iter_source_files():
        try: lines=path.read_text(encoding="utf-8",errors="ignore").splitlines()
        except OSError: continue
        for line_no,line in enumerate(lines,1):
            for rule_id,pattern,advice in RULES:
                if pattern.search(line):
                    findings.append({"rule":rule_id,"file":str(path.relative_to(ROOT)),"line":line_no,"evidence":line.strip()[:180],"advice":advice,"confidence":"heuristic"})
    return findings[:250]
def run_tests():
    if not (ROOT/"tests").exists(): return {"status":"not-configured","exitCode":None,"output":"No tests/ directory found."}
    try:
        proc=subprocess.run(["python","-m","unittest","discover","-s","tests","-v"],cwd=ROOT,capture_output=True,text=True,timeout=75,check=False)
        output=(proc.stdout+"\n"+proc.stderr)[-7000:]
        status="no-tests" if "Ran 0 tests" in output else ("passed" if proc.returncode==0 else "failed")
        return {"status":status,"exitCode":proc.returncode,"output":output}
    except subprocess.TimeoutExpired: return {"status":"timeout","exitCode":None,"output":"Test suite exceeded the 75-second safety budget."}
    except Exception as exc: return {"status":"error","exitCode":None,"output":type(exc).__name__+": "+str(exc)}
def docs_audit():
    readme=ROOT/"README.md"; docs=ROOT/"docs"; missing=[]
    if not readme.exists(): missing.append("README.md is missing")
    if not docs.exists(): missing.append("docs/ directory is missing")
    broken=[]
    if readme.exists():
        for line_no,line in enumerate(readme.read_text(encoding="utf-8",errors="ignore").splitlines(),1):
            for target in re.findall(r"\]\((?!https?://|#)([^)]+)\)",line):
                if not (ROOT/target.split("#",1)[0]).exists(): broken.append({"line":line_no,"target":target})
    return {"missing":missing,"broken_relative_links":broken[:40],"docs_files":sum(1 for p in docs.rglob("*") if p.is_file()) if docs.exists() else 0}
def pattern_report(findings):
    counts={}
    for item in findings:
        key=(item.get("rule","unknown"),item.get("file","unknown")); counts[key]=counts.get(key,0)+1
    return [{"rule":k[0],"file":k[1],"count":v} for k,v in sorted(counts.items(),key=lambda x:(-x[1],x[0]))[:30]]
def run_role(role,goal):
    started=time.monotonic()
    result={"role":role,"label":ROLES[role],"status":"completed","startedAt":now(),"goal":goal[:500]}
    if role=="research-scout": result["research"]=research(goal)
    elif role=="source-scanner": result["findings"]=scan()
    elif role=="test-runner": result["tests"]=run_tests()
    elif role=="pattern-miner":
        old=prior_state(); findings=old.get("findings",[])
        result["patterns"]=pattern_report(findings); result["historicalFindingCount"]=len(findings)
    elif role=="validation-reviewer":
        candidates=scan()
        result["review"]={"candidateCount":len(candidates),"reviewed":[{"rule":f["rule"],"file":f["file"],"line":f["line"],"disposition":"needs-human-verification"} for f in candidates[:50]],"note":"Static pattern matches are leads, not confirmed vulnerabilities. No exploit attempts are performed."}
    elif role=="documentation-auditor": result["documentation"]=docs_audit()
    elif role=="regression-watcher":
        current=scan(); old=prior_state()
        previous={(x.get("rule"),x.get("file"),x.get("line")) for x in old.get("findings",[])}
        current_keys={(x.get("rule"),x.get("file"),x.get("line")) for x in current}
        result["regression"]={"currentCandidates":len(current),"newCandidates":len(current_keys-previous) if previous else len(current),"previousCheckpointAvailable":bool(old)}
    elif role=="intelligence-synthesizer":
        result["inventory"]={"pythonFiles":sum(1 for p in ROOT.rglob("*.py") if not any(x in SKIP_DIRS for x in p.parts)),"typescriptFiles":sum(1 for p in ROOT.rglob("*.ts*") if not any(x in SKIP_DIRS for x in p.parts)),"documentationFiles":sum(1 for p in ROOT.rglob("*.md") if not any(x in SKIP_DIRS for x in p.parts))}
        result["recommendation"]="Review worker findings, run project-specific tests, and approve any code changes manually."
    result["durationSeconds"]=round(time.monotonic()-started,2); result["finishedAt"]=now()
    return result
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--role",required=True,choices=sorted(ROLES))
    parser.add_argument("--goal",default="Review this repository for safe, authorized improvements.")
    parser.add_argument("--output",default="worker.json")
    args=parser.parse_args(); report=run_role(args.role,args.goal)
    target=Path(args.output); target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps({"role":args.role,"status":report["status"],"durationSeconds":report["durationSeconds"]}))
if __name__=="__main__": main()
