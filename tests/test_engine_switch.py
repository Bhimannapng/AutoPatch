import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

import pytest
from analyzer import run_analysis
from llm_engine import inspect_html_file, patch_html_file

def test_ast_mode_python_detection():
    py_code = """def calculate_avg(items):
    total = sum(items)
    return total / len(items)
"""
    bugs, engine = run_analysis({"test_div.py": py_code}, engine_mode="AST")
    assert "AST" in engine
    assert len(bugs) >= 1
    zero_div = next((b for b in bugs if "Zero" in b.title or "Zero Division" in b.category or "Logical" in b.category), None)
    assert zero_div is not None
    assert zero_div.line_start == 3


def test_ast_mode_multi_language_support():
    # Java AST support
    java_code = """public class Calc {
    public int div(int a) { return a / 0; }
}"""
    bugs, engine = run_analysis({"Calc.java": java_code}, engine_mode="AST")
    assert len(bugs) >= 1
    assert any("Division by Zero" in b.title for b in bugs)

    # JS AST support
    js_code = """function test(x) {
    if (x = 5) { return x; }
}"""
    bugs, engine = run_analysis({"test.js": js_code}, engine_mode="AST")
    assert len(bugs) >= 1
    assert any("Assignment" in b.title for b in bugs)


def test_llm_mode_html_inspection_and_repair():
    raw_html = """<html>
<head><title>Test App</title></head>
<body>
    <img src="pic.jpg">
    <p>Unclosed paragraph
    <form>
        <input type="submit">
    </form>
</body>
</html>"""
    findings = inspect_html_file("index.html", raw_html)
    assert len(findings) >= 3
    titles = [f["title"] for f in findings]
    assert any("DOCTYPE" in t for t in titles)
    assert any("alt" in t for t in titles)
    assert any("Unclosed" in t for t in titles)

    patched = patch_html_file(raw_html, findings)
    assert "<!DOCTYPE html>" in patched
    assert 'alt="Image graphic"' in patched
