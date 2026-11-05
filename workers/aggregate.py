#!/usr/bin/env python3
"""Merge worker artifacts into a compact, durable Qill checkpoint."""
import argparse, json, os
from datetime import datetime, timezone
from pathlib import Path

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--input",default="qill-artifacts")
    parser.add_argument("--output",default="/tmp/qill-state")
    args=parser.parse_args()
    source,output=Path(args.input),Path(args.output)
    worker_dir=output/"workers"; worker_dir.mkdir(parents=True,exist_ok=True)
    workers=[]; findings=[]
    for path in sorted(source.glob("worker-*.json")):
        try:
            item=json.loads(path.read_text(encoding="utf-8")); workers.append(item)
            findings.extend(item.get("findings",[]))
        except Exception as exc:
            workers.append({"role":path.stem,"status":"failed","error":type(exc).__name__})
    for item in workers:
        role=item.get("role","unknown")
        (worker_dir/f"{role}.json").write_text(json.dumps(item,indent=2),encoding="utf-8")
    tests=next((w.get("tests") for w in workers if w.get("tests")),None)
    research=next((w.get("research") for w in workers if w.get("research")),None)
    summary={
        "workersTotal":8,
        "workersReported":len(workers),
        "workersCompleted":sum(1 for w in workers if w.get("status")=="completed"),
        "candidateFindings":len(findings),
        "testStatus":tests.get("status") if tests else "not-reported",
        "researchSources":len(research.get("sources",[])) if research else 0,
    }
    run_id=os.environ.get("GITHUB_RUN_ID","")
    latest={
        "schemaVersion":1,
        "updatedAt":datetime.now(timezone.utc).isoformat(),
        "goal":os.environ.get("QILL_GOAL","Scheduled repository research and quality cycle.")[:500],
        "run":{
            "id":run_id,"number":os.environ.get("GITHUB_RUN_NUMBER"),
            "attempt":os.environ.get("GITHUB_RUN_ATTEMPT"),
            "url":f"{os.environ.get('GITHUB_SERVER_URL','https://github.com')}/{os.environ.get('GITHUB_REPOSITORY','Screwyougucci/HackerCoderAI')}/actions/runs/{run_id}",
        },
        "summary":summary,"workers":workers,"findings":findings[:250],
        "research":research or {"sources":[],"note":"No research report was produced in this cycle."},
        "tests":tests or {"status":"not-reported"},
    }
    (output/"latest.json").write_text(json.dumps(latest,indent=2),encoding="utf-8")
    print(json.dumps(summary))
if __name__=="__main__": main()
