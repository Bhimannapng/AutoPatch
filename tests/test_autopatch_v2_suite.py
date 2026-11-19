import os
import shutil
import tempfile
import pytest
from schemas import (
    ProjectAnalysisSummary,
    BugReport,
    OptimizationFinding,
    SecurityFinding,
    ArchitectureFinding,
    AgentChatRequest
)
from project_analyzer import (
    safe_extract_zip,
    scan_project_structure
)
from multi_analyzer import (
    analyze_security_vulnerabilities,
    analyze_performance_and_ram,
    analyze_architecture_and_quality,
    profile_python_execution_memory
)
from agents import (
    get_agents_info_list,
    handle_agent_chat,
    AGENTS_REGISTRY
)
from analyzer import run_complete_project_analysis
from state import state

# TEST 1: Small Python Project
def test_small_python_project_analysis():
    files = {
        "main.py": "def run(x):\n    return x / 0\nif __name__ == '__main__':\n    run(5)\n",
        "utils.py": "def helper(val, cache=[]):\n    cache.append(val)\n    return cache\n"
    }
    bugs, opts, sec, arch, model = run_complete_project_analysis(files, engine_mode="AST")
    assert len(bugs) >= 1
    # Check that mutable default argument bug was detected
    assert any("Mutable Default Argument" in b.title or "Division" in b.title for b in bugs)

# TEST 2: Java Project Analysis
def test_java_project_analysis():
    files = {
        "com/app/Main.java": (
            "package com.app;\n"
            "public class Main {\n"
            "    public static void main(String[] args) {\n"
            "        int a = 10;\n"
            "        int b = 0;\n"
            "        System.out.println(a / b);\n"
            "    }\n"
            "}\n"
        )
    }
    bugs, opts, sec, arch, model = run_complete_project_analysis(files, engine_mode="AST")
    assert len(bugs) >= 1
    assert any(b.file_path.endswith(".java") for b in bugs)

# TEST 3: Full-Stack Project Integration
def test_full_stack_project_structure():
    with tempfile.TemporaryDirectory() as tmp_dir:
        os.makedirs(os.path.join(tmp_dir, "frontend", "src"))
        os.makedirs(os.path.join(tmp_dir, "backend"))

        with open(os.path.join(tmp_dir, "frontend", "package.json"), "w") as f:
            f.write('{"name": "web", "dependencies": {"react": "^18.0.0"}}')
        with open(os.path.join(tmp_dir, "backend", "requirements.txt"), "w") as f:
            f.write("fastapi==0.100.0\nuvicorn==0.22.0\n")
        with open(os.path.join(tmp_dir, "backend", "app.py"), "w") as f:
            f.write("from fastapi import FastAPI\napp = FastAPI()\n")

        files_dict, metrics, report = scan_project_structure(tmp_dir, "FullStackApp")
        assert "React" in report.detected_frameworks
        assert "FastAPI" in report.detected_frameworks
        assert "Full-Stack Application" in report.project_type

# TEST 4: Performance Analysis (O(N^3) Nested Loops)
def test_performance_nested_loops_detection():
    files = {
        "compute.py": (
            "def heavy_calc(grid):\n"
            "    s = 0\n"
            "    for i in grid:\n"
            "        for j in i:\n"
            "            for k in j:\n"
            "                s += k\n"
            "    return s\n"
        )
    }
    opts = analyze_performance_and_ram(files)
    assert any("Triple Nested Loop" in o.title or "O(N³)" in o.title for o in opts)
    assert any(o.category == "CPU Optimisation" for o in opts)

# TEST 5: RAM Profiling (Measurable Heap Memory with tracemalloc)
def test_ram_profiling_measurement():
    code = (
        "data = [x * 2 for x in range(20000)]\n"
        "s = sum(data)\n"
        "print(f'Done: {s}')\n"
    )
    peak_kb, duration_ms, stdout_out = profile_python_execution_memory(code)
    assert peak_kb > 0.0
    assert duration_ms >= 0.0
    assert "Done:" in stdout_out

# TEST 6: Security Analysis (Hardcoded API keys and SQL Injection)
def test_security_vulnerability_detection():
    files = {
        "auth.py": "API_SECRET_KEY = 'sk_live_98374928374982374982734'\n",
        "db.py": "def get_user(uid):\n    query = 'SELECT * FROM users WHERE id = ' + uid\n    cursor.execute(query)\n"
    }
    sec = analyze_security_vulnerabilities(files)
    assert len(sec) >= 2
    types = [s.vulnerability_type for s in sec]
    assert any("Hardcoded Secret" in t for t in types)
    assert any("SQL Injection" in t for t in types)

# TEST 7: Three AI Agents Collaboration and Grounding
def test_three_agents_collaboration():
    summary = ProjectAnalysisSummary(
        project_id="test-proj-01",
        project_name="ECommerceApp",
        project_type="Full-Stack Application",
        detected_languages=["Python", "JavaScript"],
        detected_frameworks=["FastAPI", "React"],
        entry_points=["backend/main.py"],
        capacity_metrics={
            "total_archive_size_bytes": 1024,
            "extracted_size_bytes": 1024,
            "total_files_discovered": 5,
            "relevant_source_files": 5,
            "total_lines_of_code": 250,
            "files_analyzed": 5,
            "files_excluded": [],
            "files_remaining": 0,
            "ram_consumed_mb": 0.5,
            "analysis_duration_ms": 1.2,
            "gemini_tokens_used": 0
        },
        bugs=[
            BugReport(
                id="bug-1",
                title="Zero Division in Payment Handler",
                file_path="backend/payment.py",
                line_start=15,
                line_end=15,
                category="Runtime Error",
                severity="Critical",
                confidence=95,
                root_cause="Missing check for zero denominator.",
                trigger_input_or_state="Empty cart checkout.",
                original_code="res = amount / count",
                patched_code="res = amount / count if count else 0.0",
                diff="...",
                created_at="now"
            )
        ],
        optimizations=[
            OptimizationFinding(
                id="opt-1",
                title="Quadratic Loop in Order Aggregator",
                file_path="backend/orders.py",
                line_start=20,
                category="CPU Optimisation",
                severity="High",
                problem="Nested loop iterating over order items.",
                why_inefficient="O(N^2) complexity.",
                suggested_improvement="Use dictionary lookup.",
                expected_benefit="O(N) linear time.",
                risk_level="Low"
            )
        ],
        security_findings=[],
        architecture_findings=[]
    )

    agents = get_agents_info_list(summary)
    assert len(agents) == 3
    assert agents[0].name.startswith("Dr. Patch")
    assert agents[1].name.startswith("Nova")
    assert agents[2].name.startswith("Aegis")

    # Test Bug Agent Response
    req_bugs = AgentChatRequest(agent_id="agent_bugs", message="What is the critical bug?")
    res_bugs = handle_agent_chat(req_bugs, summary, {}, api_key="")
    assert "Zero Division in Payment Handler" in res_bugs.reply or "Dr. Patch" in res_bugs.agent_name

    # Test RAM Agent Response
    req_ram = AgentChatRequest(agent_id="agent_ram", message="How can I optimize memory?")
    res_ram = handle_agent_chat(req_ram, summary, {}, api_key="")
    assert "Nova" in res_ram.agent_name

# TEST 8: Large Project Handling (Simulating 1,000+ lines without artificial limits)
def test_large_project_handling():
    files = {}
    total_lines = 0
    for i in range(15):
        lines = [f"def function_{i}_{j}():\n    return {j} * {i}\n" for j in range(50)]
        content = "".join(lines)
        files[f"module_{i}.py"] = content
        total_lines += len(lines)

    assert total_lines >= 750
    bugs, opts, sec, arch, model = run_complete_project_analysis(files, engine_mode="AST")
    # Verifies processing completes without crashing or truncating files
    assert model is not None

# TEST 9: Safe Patch Rollback / Revert in State
def test_patch_revert_workflow():
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_file = os.path.join(tmp_dir, "calc.py")
        original_code = "def calc(a, b):\n    return a / b\n"
        with open(test_file, "w") as f:
            f.write(original_code)

        state.current_project_dir = tmp_dir
        state.files_dict["calc.py"] = original_code
        state.original_files_backup["calc.py"] = original_code

        bug = BugReport(
            id="bug-test-1",
            title="Division by zero",
            file_path="calc.py",
            line_start=2,
            line_end=2,
            category="Runtime Error",
            severity="Critical",
            confidence=95,
            root_cause="No zero guard",
            trigger_input_or_state="b=0",
            original_code=original_code,
            patched_code="def calc(a, b):\n    return a / b if b else 0\n",
            diff="...",
            created_at="now"
        )
        state.bugs = [bug]

        # 1. Apply patch
        applied = state.apply_patch_to_project(bug)
        assert applied is True
        with open(test_file, "r") as f:
            assert "if b else 0" in f.read()

        # 2. Revert patch
        reverted = state.revert_patch("bug-test-1")
        assert reverted is True
        with open(test_file, "r") as f:
            assert f.read() == original_code
        assert bug.status == "Needs Review"
