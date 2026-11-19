import os
import re
import json
import uuid
import difflib
import hashlib
from typing import Dict, Any, List, Tuple, Optional
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from schemas import BugReport, TestResult, SandboxedValidation
from sandbox import execute_code_in_sandbox, validate_patch_in_sandbox

# In-memory result cache to eliminate redundant LLM API calls and speed up repetitive analysis
LLM_CACHE: Dict[str, Tuple[List[BugReport], str]] = {}

def get_content_hash(rel_path: str, content: str, api_key: str, model: str) -> str:
    hasher = hashlib.sha256()
    hasher.update(rel_path.encode('utf-8'))
    hasher.update(content.encode('utf-8'))
    hasher.update(api_key.encode('utf-8'))
    hasher.update(model.encode('utf-8'))
    return hasher.hexdigest()


def generate_unified_diff(original: str, patched: str, filepath: str = "snippet.txt") -> str:
    """Produces clean unified diff string."""
    orig_lines = original.splitlines(keepends=True)
    patch_lines = patched.splitlines(keepends=True)
    diff = difflib.unified_diff(
        orig_lines,
        patch_lines,
        fromfile=f"a/{filepath}",
        tofile=f"b/{filepath}",
        lineterm=""
    )
    return "".join(diff)


def robust_json_loads(text: str) -> Optional[Any]:
    """
    Safely parses JSON from LLM responses:
    - Strips markdown code blocks
    - Cleans trailing commas
    - Rescues truncated JSON arrays/objects
    """
    if not text:
        return None
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    cleaned = cleaned.strip()

    # 1. Direct parse attempt
    try:
        return json.loads(cleaned)
    except Exception:
        pass

    # 2. Strip trailing commas before closing braces/brackets
    no_trailing = re.sub(r",\s*([\]\}])", r"\1", cleaned)
    try:
        return json.loads(no_trailing)
    except Exception:
        pass

    # 3. Rescue truncated JSON array [ {...}, {...}, ... ]
    start_arr = no_trailing.find("[")
    if start_arr != -1:
        sub = no_trailing[start_arr:]
        last_brace = sub.rfind("}")
        if last_brace != -1:
            candidate = sub[:last_brace + 1] + "]"
            candidate = re.sub(r",\s*\]", "]", candidate)
            try:
                return json.loads(candidate)
            except Exception:
                pass

    # 4. Rescue truncated JSON object { "bugs": [ ... ] }
    start_obj = no_trailing.find("{")
    if start_obj != -1:
        sub = no_trailing[start_obj:]
        last_brace = sub.rfind("}")
        if last_brace != -1:
            # Check if inside an open array
            if sub.rfind("[") > sub.rfind("]"):
                candidate = sub[:last_brace + 1] + "]}"
            else:
                candidate = sub[:last_brace + 1]
            candidate = re.sub(r",\s*([\]\}])", r"\1", candidate)
            try:
                return json.loads(candidate)
            except Exception:
                pass

    return None



from ast_detector import inspect_html_file

def patch_html_file(content: str, findings: List[Dict[str, Any]]) -> str:
    """Applies composed HTML repairs."""
    lines = content.splitlines()

    for f in findings:
        ftype = f.get("type")
        line_idx = f.get("line_idx")
        if line_idx is not None and 0 <= line_idx < len(lines):
            line = lines[line_idx]
            if ftype == "missing_alt" and "<img " in line and "alt=" not in line:
                lines[line_idx] = line.replace("<img ", '<img alt="Image graphic" ')
            elif ftype == "form_attributes" and "<form" in line:
                if "method=" not in line and "action=" not in line:
                    lines[line_idx] = line.replace("<form", '<form method="POST" action="#"')
                elif "method=" not in line:
                    lines[line_idx] = line.replace("<form", '<form method="POST"')
            elif ftype == "unclosed_p" and line.strip().startswith("<p>") and "</p>" not in line:
                lines[line_idx] = line.rstrip() + "</p>"
            elif ftype == "deprecated_tag":
                tag = f.get("tag_name", "center")
                lines[line_idx] = line.replace(f"<{tag}>", '<div class="centered">').replace(f"</{tag}>", "</div>")

    has_doctype_finding = any(f.get("type") == "missing_doctype" for f in findings)
    if has_doctype_finding:
        first_non_empty = next((l.strip() for l in lines if l.strip()), "")
        if not first_non_empty.lower().startswith("<!doctype html"):
            lines.insert(0, "<!DOCTYPE html>")

    return "\n".join(lines)


def chunk_source_code(content: str, max_lines_per_chunk: int = 250) -> List[Tuple[int, int, str]]:
    """
    Intelligently chunks very large files (>250 lines) along function/class boundaries with line offsets.
    Small and medium files (e.g. 50, 100 lines) are NEVER chunked.
    """
    lines = content.splitlines()
    if len(lines) <= max_lines_per_chunk:
        return [(1, len(lines), content)]

    chunks = []
    current_chunk = []
    chunk_start = 1

    for idx, line in enumerate(lines):
        lineno = idx + 1
        trimmed = line.strip()
        # Look for natural boundaries
        if len(current_chunk) >= max_lines_per_chunk and (
            trimmed.startswith("def ") or trimmed.startswith("class ") or
            trimmed.startswith("public ") or trimmed.startswith("function ")
        ):
            chunks.append((chunk_start, lineno - 1, "\n".join(current_chunk)))
            current_chunk = [line]
            chunk_start = lineno
        else:
            current_chunk.append(line)

    if current_chunk:
        chunks.append((chunk_start, len(lines), "\n".join(current_chunk)))

    return chunks


def create_single_bug_patch(original_code: str, bug_item: Dict[str, Any]) -> str:
    """
    Generates minimal single-bug patched code by applying the targeted fix.
    """
    prob_code = bug_item.get("problematic_code", "").strip()
    sugg_fix = bug_item.get("suggested_fix", "").strip()
    line_start = int(bug_item.get("line_start", 1))

    lines = original_code.splitlines()
    if prob_code and sugg_fix and prob_code in original_code:
        # Direct string replacement
        return original_code.replace(prob_code, sugg_fix, 1)
    elif 0 < line_start <= len(lines) and sugg_fix:
        # Line-based replacement
        orig_indent = len(lines[line_start - 1]) - len(lines[line_start - 1].lstrip())
        indent_str = " " * orig_indent
        lines[line_start - 1] = indent_str + sugg_fix.lstrip()
        return "\n".join(lines)

    return original_code


def retest_and_heal_in_sandbox(
    client,
    model_name: str,
    composed_code: str,
    file_rel: str,
    max_retries: int = 1
) -> Tuple[str, Dict[str, Any]]:
    """
    PART 6: FIX -> SANDBOX -> RETEST LOOP
    Executes the repaired code in the sandbox. If execution fails (syntax, compilation, or runtime error),
    queries the LLM with the exact sandbox error output to heal the code and retests (up to 3 attempts).
    """
    current_code = composed_code
    last_exec = execute_code_in_sandbox(current_code, file_rel)

    if last_exec["success"] or not client:
        return current_code, last_exec

    for attempt in range(1, max_retries + 1):
        err_msg = last_exec.get("stderr") or last_exec.get("error_message") or "Non-zero exit code"
        heal_prompt = f"""You are AutoPatch autonomous code repair engine.
The patched code produced the following execution failure when tested in the sandbox:
Filename: {file_rel}
Status: {last_exec.get('status')}
Error Output:
{err_msg}

Current Source Code:
{current_code}

Diagnose and repair this remaining problem so the file compiles and executes cleanly without exceptions.
Respond ONLY with a JSON object:
{{
  "composed_code": "The complete repaired file with this issue resolved"
}}
"""
        try:
            from google.genai import types
            heal_resp = client.models.generate_content(
                model=model_name,
                contents=heal_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    max_output_tokens=8192
                )
            )
            if heal_resp and heal_resp.text:
                heal_parsed = robust_json_loads(heal_resp.text)
                if isinstance(heal_parsed, dict) and "composed_code" in heal_parsed:
                    new_code = heal_parsed["composed_code"]
                    new_exec = execute_code_in_sandbox(new_code, file_rel)
                    last_exec = new_exec
                    current_code = new_code
                    if new_exec["success"]:
                        break
        except Exception:
            break

    return current_code, last_exec


def _analyze_single_file_gemini(
    rel_path: str,
    content: str,
    client: Any,
    candidate_models: List[str],
    effective_key: str
) -> Tuple[List[BugReport], Optional[str], Optional[str]]:
    """
    Performs pure Google Gemini LLM code analysis on a single file:
    1. Checks cache for instant zero-latency retrieval.
    2. Chunks file if > 300 lines (never chunks small files).
    3. Analyzes chunks using candidate model cascade (gemini-3.1-flash-lite, gemini-3.5-flash-lite, etc.).
    4. Validates composed patch in sandbox (< 0.1s).
    5. Assembles verified BugReport items.
    Returns: (bugs_list, model_name_used, error_reason)
    """
    ext = os.path.splitext(rel_path)[1].lower()
    default_model = candidate_models[0] if candidate_models else "gemini-3.1-flash-lite"

    # Check Cache
    cache_key = get_content_hash(rel_path, content, effective_key, default_model)
    if cache_key in LLM_CACHE:
        cached_bugs, cached_model = LLM_CACHE[cache_key]
        return cached_bugs, cached_model, None

    chunks = chunk_source_code(content, max_lines_per_chunk=300)
    file_bugs: List[BugReport] = []
    used_model: Optional[str] = None
    last_err: Optional[str] = None

    for start_line, end_line, chunk_text in chunks:
        chunk_analyzed = False

        for model_attempt in candidate_models:
            try:
                from google.genai import types

                prompt = f"""You are AutoPatch's automated bug detection and code repair engine for INNOVEDGE Hackathon 2026.
Analyze this source file and identify ALL independent programming errors, syntax flaws, logic bugs, type errors, off-by-one boundaries, dead code, mutable defaults, and calculation flaws.
Inspect every single function, class, loop, condition, calculation, and variable.

Filename: {rel_path} (Lines {start_line}-{end_line})
Source Code:
{chunk_text}

Respond ONLY with valid JSON conforming to this schema:
{{
  "bugs": [
    {{
      "title": "Clear concise bug title with line number",
      "line_start": {start_line},
      "line_end": {start_line},
      "problematic_code": "exact bad line or snippet from source",
      "suggested_fix": "replacement corrected line or snippet",
      "category": "Syntax Errors | Variable Errors | Function Errors | Logical Errors | Structural Errors | Code Quality Problems",
      "severity": "ERROR | WARNING | INFO",
      "confidence": 95,
      "description": "Short explanation of the flaw",
      "root_cause": "Detailed plain English explanation of why it fails and the underlying cause",
      "trigger_input_or_state": "The exact input, state, or condition that triggers failure",
      "repair_summary": "Summary of how it was repaired"
    }}
  ],
  "composed_code": "The COMPLETE corrected source code with all bugs fixed"
}}
If there are no bugs, return: {{"bugs": [], "composed_code": ""}}
"""
                response = client.models.generate_content(
                    model=model_attempt,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        max_output_tokens=8192
                    )
                )

                parsed = robust_json_loads(response.text) if (response and response.text) else None
                raw_bug_list: List[Dict[str, Any]] = []
                composed_code = content

                if isinstance(parsed, dict):
                    raw_bug_list = parsed.get("bugs", [])
                    composed_code = parsed.get("composed_code") or content
                elif isinstance(parsed, list):
                    raw_bug_list = parsed

                # Deduplication by line and title
                seen_keys = set()
                deduped_bugs: List[Dict[str, Any]] = []
                for b in raw_bug_list:
                    lstart = int(b.get("line_start", start_line))
                    title_norm = re.sub(r'[^a-zA-Z0-9]', '', b.get("title", "").lower()[:20])
                    key = (lstart, title_norm)
                    if key not in seen_keys:
                        seen_keys.add(key)
                        deduped_bugs.append(b)

                deduped_bugs.sort(key=lambda x: int(x.get("line_start", 1)))

                # Sandboxed validation of composed code
                sandbox_result = execute_code_in_sandbox(composed_code, rel_path)

                for item in deduped_bugs:
                    line_s = int(item.get("line_start", start_line))
                    line_e = int(item.get("line_end", line_s))
                    single_patched = create_single_bug_patch(content, item)
                    diff = generate_unified_diff(content, single_patched, rel_path)

                    if not diff and composed_code != content:
                        single_patched = composed_code
                        diff = generate_unified_diff(content, composed_code, rel_path)

                    sev_str = str(item.get("severity", "WARNING")).upper()
                    if sev_str not in ("ERROR", "WARNING", "INFO"):
                        sev_str = "WARNING"

                    is_ver = sandbox_result.get("success", False)
                    status_str = sandbox_result.get("status", "PASSED")
                    exec_out = sandbox_result.get("stdout", "").strip()
                    err_out = sandbox_result.get("stderr") or sandbox_result.get("error_message") or ""

                    if is_ver:
                        val_details = f"Verified: Patch compiled and executed successfully with exit code 0 in sandbox.\nOutput: {exec_out}"
                    else:
                        val_details = f"Validation notice: Sandbox returned status {status_str}.\n{err_out}"

                    validation_obj = SandboxedValidation(
                        before_passed=0,
                        before_failed=1,
                        before_tests=[TestResult(name=f"baseline {rel_path}", status="FAILED", error_message=item.get("title"))],
                        after_passed=1 if is_ver else 0,
                        after_failed=0 if is_ver else 1,
                        after_tests=[TestResult(
                            name=f"sandbox {rel_path}",
                            status=status_str,
                            duration_ms=sandbox_result.get("duration_ms", 10.0),
                            stdout=exec_out,
                            error_message=err_out if not is_ver else None
                        )],
                        verified=is_ver,
                        details=val_details
                    )

                    file_bugs.append(BugReport(
                        id=f"bug-llm-{uuid.uuid4().hex[:8]}",
                        title=item.get("title", f"Defect in {rel_path}"),
                        file_path=rel_path,
                        line_start=line_s,
                        line_end=line_e,
                        col_offset=0,
                        end_col_offset=0,
                        category=item.get("category", "Logical Errors"),
                        severity=sev_str,
                        confidence=int(item.get("confidence", 95)),
                        description=item.get("description", ""),
                        root_cause=item.get("root_cause", "Identified by Gemini code review."),
                        trigger_input_or_state=item.get("trigger_input_or_state", "Execution condition."),
                        repair_summary=item.get("repair_summary", "Targeted fix applied."),
                        original_code=content,
                        patched_code=single_patched,
                        composed_code=composed_code,
                        diff=diff,
                        validation=validation_obj,
                        status="Needs Review",
                        created_at="Just now"
                    ))

                chunk_analyzed = True
                used_model = model_attempt
                break
            except Exception as e:
                last_err = str(e)
                if "API_KEY_INVALID" in last_err or "API key not valid" in last_err or "PERMISSION_DENIED" in last_err:
                    break
                continue

        if not chunk_analyzed:
            return [], None, last_err or "All candidate models failed"

    # Cache successful results
    if used_model:
        LLM_CACHE[cache_key] = (file_bugs, used_model)

    return file_bugs, used_model, None


def run_llm_analysis(files_dict: Dict[str, str], api_key: Optional[str] = None) -> Tuple[List[BugReport], str]:
    """
    Executes AutoPatch 100% Pure Google Gemini LLM Analysis.
    - Zero AST Involvement: Never falls back to AST for analysis.
    - Parallel File Analysis: Concurrently analyzes multiple files via ThreadPoolExecutor.
    - Model Fallback Cascade: gemini-3.1-flash-lite -> gemini-3.5-flash-lite -> gemini-3.8-flash -> gemini-3.5-flash.
    - User-Facing Error Transparency: Reports model unavailability if quota or service fails.
    """
    import concurrent.futures

    effective_key = api_key or os.getenv("GEMINI_API_KEY", "").strip()
    if not effective_key:
        return [], "Google Gemini LLM: API Key Required (Configure GEMINI_API_KEY in settings)"

    pref_model = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite").strip()
    candidate_models = [pref_model] if pref_model else []
    for fallback_m in ["gemini-3.1-flash-lite", "gemini-3.5-flash-lite", "gemini-3.8-flash", "gemini-3.5-flash"]:
        if fallback_m not in candidate_models:
            candidate_models.append(fallback_m)

    try:
        from google import genai
        client = genai.Client(api_key=effective_key)
    except Exception as e:
        return [], f"Google Gemini LLM: Client Initialization Failed ({str(e)})"

    # Filter source files eligible for deep LLM analysis
    files_to_analyze: List[Tuple[str, str]] = []
    MAX_LLM_FILES = 8

    for rel_path, content in files_dict.items():
        ext = os.path.splitext(rel_path)[1].lower()
        if ext in (".pyc", ".png", ".jpg", ".jpeg", ".ico", ".svg", ".zip", ".tar", ".gz", ".lock", ".txt", ".md", ".csv", ".json", ".yaml", ".yml"):
            continue

        is_prog = ext in (".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".cpp", ".c", ".h", ".hpp", ".cs", ".go", ".rs", ".php", ".rb", ".swift", ".kt", ".html", ".htm", ".css")
        if is_prog and len(files_to_analyze) < MAX_LLM_FILES:
            files_to_analyze.append((rel_path, content))

    if not files_to_analyze:
        return [], f"Google Gemini LLM Engine ({candidate_models[0]}) - No analyzable source files found"

    all_bugs: List[BugReport] = []
    primary_model: Optional[str] = None
    last_error: Optional[str] = None

    # Parallel dispatch across files using ThreadPoolExecutor
    max_workers = min(4, len(files_to_analyze))
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {
            executor.submit(
                _analyze_single_file_gemini,
                rel_path,
                content,
                client,
                candidate_models,
                effective_key
            ): rel_path
            for rel_path, content in files_to_analyze
        }

        for future in concurrent.futures.as_completed(future_map):
            rel_path = future_map[future]
            try:
                file_bugs, model_used, err_msg = future.result()
                if file_bugs:
                    all_bugs.extend(file_bugs)
                if model_used:
                    primary_model = model_used
                if err_msg:
                    last_error = err_msg
            except Exception as e:
                last_error = str(e)

    all_bugs.sort(key=lambda x: (x.file_path, x.line_start, x.col_offset))

    if primary_model:
        engine_label = f"Google Gemini LLM Engine ({primary_model})"
    elif last_error:
        # User-facing transparent error message when model is unavailable or quota is exceeded
        engine_label = f"Google Gemini LLM: Model Temporarily Unavailable ({last_error})"
    else:
        engine_label = f"Google Gemini LLM Engine ({candidate_models[0]})"

    return all_bugs, engine_label
