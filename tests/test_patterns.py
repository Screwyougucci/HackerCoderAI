from app.patterns import analyze_patterns

def test_groups_repeated_rules_and_files():
    findings = [
        {"rule": "JS-INNERHTML", "severity": "medium", "file": "a.js"},
        {"rule": "JS-INNERHTML", "severity": "medium", "file": "b.js"},
        {"rule": "PY-EVAL", "severity": "high", "file": "a.js"},
    ]
    result = analyze_patterns(findings)
    assert result["finding_count"] == 3
    assert result["repeated_rule_patterns"][0]["pattern"] == "JS-INNERHTML"
    assert result["files_with_multiple_findings"][0]["file"] == "a.js"
