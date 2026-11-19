import os
import re
import ast
import uuid
import tracemalloc
from typing import Dict, List, Tuple, Optional, Any

from schemas import (
    BugReport,
    OptimizationFinding,
    SecurityFinding,
    ArchitectureFinding,
    SandboxedValidation
)
from ast_detector import detect_ast_bugs
from ast_patcher import apply_single_ast_patch, compose_multi_ast_patches, generate_unified_diff

# Regex patterns for Security Analysis
SECURITY_PATTERNS = [
    {
        "type": "Hardcoded Secret / API Key",
        "pattern": r"(?i)(api[_-]?key|secret[_-]?key|auth[_-]?token|password|passwd|client[_-]?secret)\s*[:=]\s*['\"][A-Za-z0-9_\-\.]{12,}['\"]",
        "severity": "Critical",
        "confidence": "High",
        "desc": "Hardcoded secret or credential detected in source code.",
        "remediation": "Move credentials to secure environment variables (.env) or a secret manager."
    },
    {
        "type": "AWS Access Key Exposure",
        "pattern": r"(A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}",
        "severity": "Critical",
        "confidence": "High",
        "desc": "AWS Access Key ID pattern detected in source code.",
        "remediation": "Rotate this key immediately and load AWS credentials via IAM roles or environment variables."
    },
    {
        "type": "SQL Injection Risk",
        "pattern": r"(?i)(execute|cursor\.execute|query|sql|stmt)\s*(?:\(|=)\s*['\"].*?(SELECT|INSERT|UPDATE|DELETE).*?['\"]\s*(\+|\%|\.format\(|f['\"])",
        "severity": "High",
        "confidence": "High",
        "desc": "Unsanitized dynamic string concatenation detected in SQL query.",
        "remediation": "Use parameterized queries or prepared statements (e.g. cursor.execute(query, (params,))) to prevent SQL injection."
    },
    {
        "type": "Command Injection Risk",
        "pattern": r"(?i)(os\.system|subprocess\.call|subprocess\.Popen)\s*\(\s*(f['\"].*?['\"]|.*?(\+|\%))",
        "severity": "Critical",
        "confidence": "High",
        "desc": "Dynamic string construction passed to system shell execution.",
        "remediation": "Use subprocess.run with arguments passed as a list, and set shell=False."
    },
    {
        "type": "Unsafe Dynamic Code Execution (eval/exec)",
        "pattern": r"\b(eval|exec)\s*\(",
        "severity": "High",
        "confidence": "Medium",
        "desc": "Direct invocation of eval() or exec() executes arbitrary code.",
        "remediation": "Refactor logic to use safe parsers like ast.literal_eval() or explicit dispatch dictionaries."
    },
    {
        "type": "Unsafe Object Deserialization",
        "pattern": r"\b(pickle\.loads?|yaml\.load\s*\([^,)]+\))",
        "severity": "High",
        "confidence": "High",
        "desc": "Unsafe deserialization can execute arbitrary malicious bytecode.",
        "remediation": "Use yaml.safe_load() or JSON deserialization for untrusted data payloads."
    }
]

def analyze_security_vulnerabilities(files_dict: Dict[str, str]) -> List[SecurityFinding]:
    """Scans all source files for security flaws, credentials, and injection risks."""
    findings: List[SecurityFinding] = []

    for rel_path, content in files_dict.items():
        # Skip test files from secret scanning false positives
        is_test = "test" in rel_path.lower()
        lines = content.splitlines()

        for idx, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("/*"):
                continue

            for sp in SECURITY_PATTERNS:
                if is_test and "secret" in sp["type"].lower():
                    continue

                if re.search(sp["pattern"], line):
                    findings.append(SecurityFinding(
                        id=f"sec-{uuid.uuid4().hex[:8]}",
                        title=f"{sp['type']} in {os.path.basename(rel_path)}",
                        file_path=rel_path,
                        line_start=idx,
                        line_end=idx,
                        severity=sp["severity"],
                        confidence=sp["confidence"],
                        vulnerability_type=sp["type"],
                        description=f"{sp['desc']} Located at line {idx}.",
                        remediation=sp["remediation"]
                    ))

    return findings

def analyze_performance_and_ram(files_dict: Dict[str, str]) -> List[OptimizationFinding]:
    """
    Identifies RAM bottlenecks, CPU inefficiencies, memory leak risks,
    and unnecessary/redundant code structures.
    """
    optimizations: List[OptimizationFinding] = []

    for rel_path, content in files_dict.items():
        lines = content.splitlines()

        # 1. Python AST-based performance & memory analysis
        if rel_path.endswith(".py"):
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    # Inefficient Nested Loops
                    if isinstance(node, (ast.For, ast.While)):
                        for child in node.body:
                            if isinstance(child, (ast.For, ast.While)):
                                for grandchild in child.body:
                                    if isinstance(grandchild, (ast.For, ast.While)):
                                        optimizations.append(OptimizationFinding(
                                            id=f"perf-{uuid.uuid4().hex[:8]}",
                                            title=f"O(N³) Triple Nested Loop in {os.path.basename(rel_path)}",
                                            file_path=rel_path,
                                            line_start=getattr(node, 'lineno', 1),
                                            line_end=getattr(grandchild, 'lineno', getattr(node, 'lineno', 1)),
                                            category="CPU Optimisation",
                                            severity="High",
                                            problem="Three levels of nested loops detected. Time complexity scales cubically with collection size.",
                                            why_inefficient="Deep loop nesting causes dramatic CPU spikes on large datasets.",
                                            suggested_improvement="Refactor using hash maps (dictionaries), set lookups, or batch vectorized operations.",
                                            expected_benefit="Reduces time complexity from O(N³) to O(N) or O(N log N).",
                                            is_measured=False,
                                            risk_level="Medium"
                                        ))
                                        break

                    # Memory Bottleneck: Eager full list instantiation in range()
                    if isinstance(node, ast.ListComp):
                        # Detect [x for x in range(100000+)]
                        for gen in node.generators:
                            if isinstance(gen.iter, ast.Call) and getattr(gen.iter.func, 'id', '') == 'range':
                                if gen.iter.args and isinstance(gen.iter.args[0], ast.Constant):
                                    if isinstance(gen.iter.args[0].value, int) and gen.iter.args[0].value >= 50000:
                                        optimizations.append(OptimizationFinding(
                                            id=f"ram-{uuid.uuid4().hex[:8]}",
                                            title=f"Excessive Memory Allocation via List Comprehension",
                                            file_path=rel_path,
                                            line_start=getattr(node, 'lineno', 1),
                                            category="RAM Optimisation",
                                            severity="High",
                                            problem=f"List comprehension eagerly instantiates {gen.iter.args[0].value:,} elements in heap memory.",
                                            why_inefficient="Allocating entire arrays at once consumes substantial RAM and triggers garbage collector pauses.",
                                            suggested_improvement="Replace list comprehension brackets `[...]` with generator expression `(...)` to stream elements on demand.",
                                            expected_benefit="Reduces peak RAM allocation to O(1) constant memory.",
                                            is_measured=False,
                                            risk_level="Low"
                                        ))

                    # Resource Leak: Unclosed file handles (open without with)
                    if isinstance(node, ast.Assign):
                        if isinstance(node.value, ast.Call) and getattr(node.value.func, 'id', '') == 'open':
                            # Check if parent is With
                            optimizations.append(OptimizationFinding(
                                id=f"leak-{uuid.uuid4().hex[:8]}",
                                title=f"Potential Resource Leak: Unmanaged open() call",
                                file_path=rel_path,
                                line_start=getattr(node, 'lineno', 1),
                                category="Memory Leak Risk",
                                severity="Medium",
                                problem="File handle opened via direct assignment without context manager.",
                                why_inefficient="Unclosed OS file descriptors remain locked in process memory until garbage collected.",
                                suggested_improvement="Wrap with `with open(...) as f:` to guarantee deterministic descriptor release.",
                                expected_benefit="Prevents file descriptor leaks and frees OS buffer memory immediately.",
                                is_measured=False,
                                risk_level="Low"
                            ))

            except Exception:
                pass

        # 2. General regex patterns for JS/Java/Python
        for idx, line in enumerate(lines, 1):
            # Repeated regex compilation inside a function or loop
            if re.search(r"re\.(search|match|findall)\(['\"][^'\"]{10,}['\"]", line):
                optimizations.append(OptimizationFinding(
                    id=f"perf-{uuid.uuid4().hex[:8]}",
                    title=f"Inline Regex Recompilation in {os.path.basename(rel_path)}",
                    file_path=rel_path,
                    line_start=idx,
                    category="CPU Optimisation",
                    severity="Low",
                    problem="Regular expression string parsed on every call.",
                    why_inefficient="Compiling regex patterns repetitively wastes CPU cycles in hot code paths.",
                    suggested_improvement="Pre-compile pattern at module level: `PATTERN = re.compile(...)`.",
                    expected_benefit="Speeds up matching loop by 3-5x.",
                    is_measured=False,
                    risk_level="Low"
                ))

            # Unused / redundant debug console statements in JS/Python
            if re.search(r"console\.log\(|print\s*\(\s*['\"](?:debug|test|here|value:?)", line, re.I):
                optimizations.append(OptimizationFinding(
                    id=f"clean-{uuid.uuid4().hex[:8]}",
                    title=f"Redundant Debug Logging Statement",
                    file_path=rel_path,
                    line_start=idx,
                    category="Unused Code",
                    severity="Informational",
                    problem="Orphaned debug print/console.log statement left in source.",
                    why_inefficient="Synchronous console writes cause I/O blocking in production runtimes.",
                    suggested_improvement="Remove debug statements or route through a configurable logger at DEBUG level.",
                    expected_benefit="Eliminates unnecessary console I/O overhead and cleans production output.",
                    is_measured=False,
                    risk_level="Low"
                ))

    return optimizations

def analyze_architecture_and_quality(
    files_dict: Dict[str, str],
    dependencies: List[Any]
) -> List[ArchitectureFinding]:
    """Analyzes modularity, broken cross-file links, and architecture health."""
    findings: List[ArchitectureFinding] = []

    # Map all existing internal relative file paths and module stems
    existing_stems = set()
    for rel_path in files_dict.keys():
        clean = os.path.splitext(rel_path)[0].replace("/", ".")
        existing_stems.add(clean)
        existing_stems.add(os.path.basename(os.path.splitext(rel_path)[0]))

    # Check for broken internal imports in Python / JS
    for dep in dependencies:
        if not getattr(dep, 'is_external', True):
            target = getattr(dep, 'target', '')
            source = getattr(dep, 'source_file', '')
            clean_target = target.lstrip("./").replace("/", ".").replace(".py", "").replace(".js", "").replace(".ts", "")
            
            # If target looks like a relative module but doesn't exist
            if clean_target and clean_target not in existing_stems and not any(clean_target in stem for stem in existing_stems):
                findings.append(ArchitectureFinding(
                    id=f"arch-{uuid.uuid4().hex[:8]}",
                    title=f"Broken Module Reference: '{target}'",
                    category="API Inconsistency",
                    affected_files=[source],
                    description=f"File '{source}' attempts to import internal module '{target}', which does not exist in the project tree.",
                    recommendation=f"Update import statement in '{source}' to point to the correct relative path or install the missing module."
                ))

    # Check for frontend-backend API consistency
    frontend_api_calls = []
    backend_routes = []
    for rel_path, content in files_dict.items():
        if rel_path.endswith((".js", ".jsx", ".ts", ".tsx")):
            for m in re.finditer(r"fetch\s*\(\s*['\"](/api/[^'\"]+)['\"]", content):
                frontend_api_calls.append((rel_path, m.group(1)))
        elif rel_path.endswith(".py"):
            for m in re.finditer(r"@(?:app|router)\.(?:get|post|put|delete)\s*\(\s*['\"](/api/[^'\"]+)['\"]", content):
                backend_routes.append(m.group(1))

    # Verify if any frontend endpoint has no backend handler
    if backend_routes and frontend_api_calls:
        routes_set = set(backend_routes)
        for fe_file, endpoint in frontend_api_calls:
            # Clean route parameters for matching
            base_ep = re.sub(r"\?.*$", "", endpoint)
            if base_ep not in routes_set and not any(r.startswith(base_ep.split("{")[0]) for r in routes_set):
                findings.append(ArchitectureFinding(
                    id=f"arch-{uuid.uuid4().hex[:8]}",
                    title=f"Unmatched API Endpoint: {base_ep}",
                    category="API Inconsistency",
                    affected_files=[fe_file],
                    description=f"Frontend invokes '{base_ep}', but no matching backend route handler was discovered in backend source files.",
                    recommendation="Ensure the backend defines a route handler for this endpoint or verify URL consistency."
                ))

    return findings

def profile_python_execution_memory(code: str) -> Tuple[float, float, str]:
    """
    Executes Python snippet under tracemalloc to measure exact heap RAM and execution time.
    Returns (peak_ram_kb, duration_ms, stdout_output).
    """
    import io
    import sys
    import time

    tracemalloc.start()
    start_time = time.perf_counter()
    stdout_capture = io.StringIO()
    old_stdout = sys.stdout

    try:
        sys.stdout = stdout_capture
        exec_globals = {"__name__": "__main__"}
        exec(code, exec_globals)
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        current, peak = tracemalloc.get_traced_memory()
        peak_kb = round(peak / 1024.0, 2)
        out_str = stdout_capture.getvalue()
        return peak_kb, duration_ms, out_str
    except Exception as e:
        return 0.0, 0.0, f"Execution failed: {str(e)}"
    finally:
        sys.stdout = old_stdout
        tracemalloc.stop()
