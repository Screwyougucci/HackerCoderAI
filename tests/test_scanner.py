from app.scanner import scan_text

def test_detects_python_eval():
    findings = scan_text("value = eval(user_input)\n")
    assert any(item["rule"] == "PY-EVAL" and item["line"] == 1 for item in findings)

def test_detects_dom_sink():
    findings = scan_text("node.innerHTML = value")
    assert any(item["rule"] == "JS-INNERHTML" for item in findings)

def test_safe_code_has_no_matches():
    assert scan_text("print('hello')\n") == []
