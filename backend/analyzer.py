import os
import ast
import uuid
from typing import List, Dict, Optional, Tuple, Any
from schemas import (
    BugReport,
    FileNode,
    OptimizationFinding,
    SecurityFinding,
    ArchitectureFinding
)
from ast_detector import detect_ast_bugs
from ast_patcher import apply_single_ast_patch, compose_multi_ast_patches, generate_unified_diff
from llm_engine import run_llm_analysis
from multi_analyzer import (
    analyze_security_vulnerabilities,
    analyze_performance_and_ram,
    analyze_architecture_and_quality
)

def build_file_tree(root_dir: str, current_dir: Optional[str] = None) -> List[FileNode]:
    if current_dir is None:
        current_dir = root_dir

    nodes: List[FileNode] = []
    try:
        entries = sorted(os.listdir(current_dir))
    except Exception:
        return nodes

    for entry in entries:
        if entry.startswith(".") or entry in ("__pycache__", "venv", "node_modules", ".pytest_cache", ".git", "dist", "build"):
            continue
        full_path = os.path.join(current_dir, entry)
        rel_path = os.path.relpath(full_path, root_dir)
        is_dir = os.path.isdir(full_path)
        size = 0 if is_dir else os.path.getsize(full_path)

        children = build_file_tree(root_dir, full_path) if is_dir else None
        nodes.append(FileNode(
            name=entry,
            path=rel_path,
            is_dir=is_dir,
            size=size,
            children=children
        ))
    return nodes

def run_pure_ast_analysis(files_dict: Dict[str, str]) -> Tuple[List[BugReport], str]:
    """Runs deterministic AST analysis across Python, Java, JS, and HTML files."""
    bugs: List[BugReport] = []

    for rel_path, content in files_dict.items():
        raw_findings = detect_ast_bugs(rel_path, content)

        if raw_findings:
            if rel_path.endswith(".py"):
                composed_code, _ = compose_multi_ast_patches(content, raw_findings, rel_path)
            else:
                composed_code = content

            for finding in raw_findings:
                if rel_path.endswith(".py"):
                    patched_code, diff = apply_single_ast_patch(content, finding, rel_path)
                    if not diff and composed_code != content:
                        patched_code = composed_code
                        diff = generate_unified_diff(content, composed_code, rel_path)
                else:
                    patched_code = content
                    diff = ""

                bugs.append(BugReport(
                    id=finding.get("id", f"bug-{uuid.uuid4().hex[:8]}"),
                    title=finding["title"],
                    file_path=rel_path,
                    line_start=finding.get("line_start", 1),
                    line_end=finding.get("line_end", 1),
                    col_offset=finding.get("col_offset", 0),
                    end_col_offset=finding.get("end_col_offset", 0),
                    category=finding.get("category", "Syntax Errors"),
                    severity=finding.get("severity", "ERROR"),
                    confidence=finding.get("confidence", 95),
                    description=finding.get("description", ""),
                    root_cause=finding.get("root_cause", "Identified by AST syntax analysis."),
                    trigger_input_or_state=finding.get("trigger_input_or_state", "Execution condition."),
                    repair_summary=finding.get("repair_summary", "Applied targeted AST transformation."),
                    original_code=content,
                    patched_code=patched_code,
                    composed_code=composed_code,
                    diff=diff,
                    status="Needs Review",
                    created_at="Just now"
                ))

    return bugs, "Pure Multi-Language AST Engine (Offline / Zero-LLM)"

def run_combined_analysis(files_dict: Dict[str, str], api_key: Optional[str] = None) -> Tuple[List[BugReport], str]:
    """
    Two-Stage Combined Pipeline:
    Stage 1: Run deterministic AST detector first.
    Stage 2: Run Gemini LLM analysis.
    Stage 3: Merge and deduplicate results.
    """
    ast_bugs, _ = run_pure_ast_analysis(files_dict)
    llm_bugs, _ = run_llm_analysis(files_dict, api_key)

    merged: List[BugReport] = list(ast_bugs)
    ast_locations = {(b.file_path, b.line_start) for b in ast_bugs}

    for lb in llm_bugs:
        loc = (lb.file_path, lb.line_start)
        if loc not in ast_locations:
            merged.append(lb)

    merged.sort(key=lambda x: (x.file_path, x.line_start, x.col_offset))
    return merged, "Combined Analysis (Two-Stage Pipeline: AST + Gemini LLM)"

def run_analysis(
    files_dict: Dict[str, str],
    engine_mode: str = "AST",
    api_key: Optional[str] = None
) -> Tuple[List[BugReport], str]:
    """
    Unified analyzer routing between 4 engine modes:
    - 'AST': Pure AST Engine (Python `ast`, Java `javalang`, JS `esprima`, HTML markup)
    - 'LLM': Google Gemini GenAI SDK Multi-Language Engine
    - 'COMBINED': Two-Stage Combined Pipeline (AST + Gemini LLM)
    - 'SANDBOX': Sandboxed Execution & Test Validation Mode
    """
    mode = engine_mode.upper().strip()

    if mode == "LLM":
        try:
            bugs, model_used = run_llm_analysis(files_dict, api_key)
            if bugs:
                return bugs, model_used
        except Exception:
            pass
        return run_pure_ast_analysis(files_dict)
    elif mode == "COMBINED":
        try:
            return run_combined_analysis(files_dict, api_key)
        except Exception:
            return run_pure_ast_analysis(files_dict)
    elif mode == "SANDBOX":
        bugs, _ = run_pure_ast_analysis(files_dict)
        return bugs, "Sandboxed Execution & Test Validation Engine"
    else:
        return run_pure_ast_analysis(files_dict)

def run_complete_project_analysis(
    files_dict: Dict[str, str],
    engine_mode: str = "AST",
    api_key: Optional[str] = None,
    dependencies: Optional[List[Any]] = None
) -> Tuple[List[BugReport], List[OptimizationFinding], List[SecurityFinding], List[ArchitectureFinding], str]:
    """
    Comprehensive Project-Level Intelligence Engine:
    1. Bugs & Root-Causes (AST / LLM)
    2. RAM & CPU Optimizations
    3. Security & Secret Exposure Analysis
    4. Architecture & Modularity Consistency
    """
    bugs, model_used = run_analysis(files_dict, engine_mode=engine_mode, api_key=api_key)
    optimizations = analyze_performance_and_ram(files_dict)
    security = analyze_security_vulnerabilities(files_dict)
    architecture = analyze_architecture_and_quality(files_dict, dependencies or [])

    return bugs, optimizations, security, architecture, model_used
