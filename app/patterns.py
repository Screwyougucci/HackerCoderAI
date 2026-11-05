"""Group repeated source findings into useful, reviewable patterns."""
from collections import Counter, defaultdict
from pathlib import Path
import re

def analyze_patterns(findings: list[dict], search_results: list[dict] | None = None) -> dict:
    by_rule = defaultdict(list)
    by_file = defaultdict(list)
    for item in findings:
        by_rule[item.get("rule", "UNKNOWN")].append(item)
        by_file[item.get("file", "unknown")].append(item)

    repeated_rules = [
        {"pattern": rule, "count": len(items),
         "files": sorted({str(x.get("file", "")) for x in items})[:20],
         "severity": max((str(x.get("severity", "low")) for x in items),
                         key=lambda x: {"low": 0, "medium": 1, "high": 2, "critical": 3}.get(x, 0))}
        for rule, items in by_rule.items() if len(items) > 1
    ]
    repeated_files = [
        {"file": filename, "count": len(items),
         "rules": sorted({str(x.get("rule", "")) for x in items})}
        for filename, items in by_file.items() if len(items) > 1
    ]
    domains = Counter()
    for item in search_results or []:
        host = re.sub(r"^www\\.", "", __import__("urllib.parse", fromlist=["urlparse"]).urlparse(item.get("url", "")).hostname or "")
        if host:
            domains[host] += 1
    return {
        "finding_count": len(findings),
        "repeated_rule_patterns": sorted(repeated_rules, key=lambda x: (-x["count"], x["pattern"])),
        "files_with_multiple_findings": sorted(repeated_files, key=lambda x: (-x["count"], x["file"])),
        "source_domain_frequency": [{"domain": k, "count": v} for k, v in domains.most_common(10)],
        "caution": "Patterns are correlations and heuristic matches, not proof of exploitability or common root cause."
    }
