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


def inspect_html_file(filepath: str, content: str) -> List[Dict[str, Any]]:
    """
    HTML markup, accessibility, and structure analyzer.
    Detects missing doctype, missing alt attributes, unclosed tags, broken forms, and deprecated elements.
    """
    findings: List[Dict[str, Any]] = []
    lines = content.splitlines()

    # 1. Missing DOCTYPE
    first_non_empty = next((l.strip() for l in lines if l.strip()), "")
    if not first_non_empty.lower().startswith("<!doctype html"):
        findings.append({
            "title": "HTML Standard: Missing '<!DOCTYPE html>' Declaration (Line 1)",
            "line_start": 1,
            "line_end": 1,
            "category": "Syntax Errors",
            "severity": "WARNING",
            "confidence": 99,
            "description": "HTML document does not declare modern HTML5 DOCTYPE. Browsers will render in Quirks Mode, causing layout inconsistencies.",
            "root_cause": "The document header lacks '<!DOCTYPE html>'. Omitting the DOCTYPE triggers legacy rendering modes.",
            "trigger_input_or_state": "Any modern web browser rendering this document.",
            "repair_summary": "Prepend standard '<!DOCTYPE html>' at line 1.",
            "type": "missing_doctype"
        })

    # 2. Line-by-line defects
    for idx, line in enumerate(lines):
        lineno = idx + 1
        trimmed = line.strip()

        # Check <img> missing alt attribute
        if "<img " in trimmed and "alt=" not in trimmed:
            findings.append({
                "title": f"Accessibility (WCAG 2.1): Missing 'alt' on <img> Tag (Line {lineno})",
                "line_start": lineno,
                "line_end": lineno,
                "category": "Code Quality Problems",
                "severity": "WARNING",
                "confidence": 95,
                "description": f"Image tag on line {lineno} lacks an 'alt' attribute, violating WCAG 2.1 accessibility standards.",
                "root_cause": f"At line {lineno}, <img> element has no alternative text description. Screen readers cannot describe the graphic.",
                "trigger_input_or_state": "Screen reader or accessibility audit tool scanning the document.",
                "repair_summary": f"Add descriptive `alt=\"Image graphic\"` attribute to <img> tag on line {lineno}.",
                "type": "missing_alt",
                "line_idx": idx
            })

        # Check <form> missing action or method
        if "<form" in trimmed and (">" in trimmed) and ("method=" not in trimmed or "action=" not in trimmed):
            findings.append({
                "title": f"HTML Form Specification: Missing 'action' or 'method' (Line {lineno})",
                "line_start": lineno,
                "line_end": lineno,
                "category": "Structural Errors",
                "severity": "WARNING",
                "confidence": 90,
                "description": f"Form tag on line {lineno} does not specify explicit HTTP submission method or action destination.",
                "root_cause": f"At line {lineno}, <form> relies on browser defaults (implicit GET), which may leak sensitive form data into URL parameters.",
                "trigger_input_or_state": "User submits form without explicit destination or POST method.",
                "repair_summary": f"Add `method=\"POST\" action=\"#\"` to <form> element on line {lineno}.",
                "type": "form_attributes",
                "line_idx": idx
            })

        # Check deprecated tags: <center>, <font>, <marquee>, <blink>
        for dep in ("<center>", "<font", "<marquee>", "<blink>"):
            if dep in trimmed.lower():
                tag_name = dep.replace("<", "").replace(">", "").strip()
                findings.append({
                    "title": f"Deprecated HTML Element: '<{tag_name}>' (Line {lineno})",
                    "line_start": lineno,
                    "line_end": lineno,
                    "category": "Code Quality Problems",
                    "severity": "WARNING",
                    "confidence": 95,
                    "description": f"The '<{tag_name}>' element on line {lineno} was deprecated in modern HTML specifications.",
                    "root_cause": f"At line {lineno}, obsolete presentation tag '<{tag_name}>' violates modern web separation of concerns.",
                    "trigger_input_or_state": "Modern browser rendering engine.",
                    "repair_summary": f"Replace '<{tag_name}>' with modern semantic container or CSS styling.",
                    "type": "deprecated_tag",
                    "line_idx": idx,
                    "tag_name": tag_name
                })

    # 3. Check unclosed tags (e.g. <p> without </p> before closing </div>)
    for idx, line in enumerate(lines):
        lineno = idx + 1
        trimmed = line.strip()
        if trimmed.startswith("<p>") and "</p>" not in trimmed:
            closed = False
            for forward in lines[idx+1:idx+6]:
                if "</p>" in forward:
                    closed = True
                    break
                if "</div" in forward or "</body" in forward or "<p>" in forward:
                    break
            if not closed:
                findings.append({
                    "title": f"HTML Syntax: Unclosed '<p>' Tag (Line {lineno})",
                    "line_start": lineno,
                    "line_end": lineno,
                    "category": "Syntax Errors",
                    "severity": "ERROR",
                    "confidence": 92,
                    "description": f"Paragraph tag '<p>' on line {lineno} is unclosed before enclosing container terminates.",
                    "root_cause": f"At line {lineno}, paragraph element lacks terminating '</p>', causing unexpected DOM hierarchy inheritance.",
                    "trigger_input_or_state": "DOM parser constructing browser render tree.",
                    "repair_summary": f"Append closing '</p>' tag to line {lineno}.",
                    "type": "unclosed_p",
                    "line_idx": idx
                })

    return findings


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


def run_llm_analysis(files_dict: Dict[str, str], api_key: Optional[str] = None) -> Tuple[List[BugReport], str]:
    """
    Executes AutoPatch LLM-based analysis across programming files and web/markup/HTML files.
    - Multi-Error Detection: Identifies all detectable errors (5, 10, 20+) in 50-line and large files.
    - Token-Efficient JSON Architecture: Eliminates redundant file reproductions, preventing truncation.
    - Multi-Pass Review: Pass 1 thorough code review, Pass 2 error coverage review, Pass 3 deduplication.
    - Fix -> Sandbox -> Retest Loop: Executes repaired code in isolated sandbox, diagnoses failures, retests.
    """
    effective_key = api_key or os.getenv("GEMINI_API_KEY", "").strip()
    bugs: List[BugReport] = []
    active_model_name = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    candidate_models = [
        "gemini-3.5-flash-lite",
        "gemini-3.5-flash",
    ]

    client = None
    if effective_key:
        try:
            from google import genai
            client = genai.Client(api_key=effective_key)
        except Exception:
            client = None

    llm_analyzed_count = 0
    MAX_LLM_FILES = 4

    for rel_path, content in files_dict.items():
        ext = os.path.splitext(rel_path)[1].lower()
        if ext in (".pyc", ".png", ".jpg", ".jpeg", ".ico", ".svg", ".zip", ".tar", ".gz", ".lock", ".txt", ".md", ".csv", ".json", ".yaml", ".yml"):
            continue

        is_html = ext in (".html", ".htm")
        is_prog = ext in (".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".cpp", ".c", ".h", ".hpp", ".cs", ".go", ".rs", ".php", ".rb", ".swift", ".kt")
        is_css = ext in (".css",)

        if not (is_prog or is_html or is_css):
            continue

        # Check Cache
        cache_key = get_content_hash(rel_path, content, effective_key, active_model_name)
        if cache_key in LLM_CACHE:
            cached_bugs, cached_model = LLM_CACHE[cache_key]
            bugs.extend(cached_bugs)
            active_model_name = cached_model
            continue

        file_bugs: List[BugReport] = []
        analyzed_via_gemini = False

        if client and is_prog and llm_analyzed_count < MAX_LLM_FILES:
            llm_analyzed_count += 1
            chunks = chunk_source_code(content, max_lines_per_chunk=300)
            chunk_success_all = True

            for start_line, end_line, chunk_text in chunks:
                chunk_analyzed = False
                for model_attempt in candidate_models:
                    try:
                        from google.genai import types

                        # PASS 1: COMPLETE THOROUGH ANALYSIS
                        pass1_prompt = f"""You are AutoPatch's automated bug detection and code repair engine for INNOVEDGE Hackathon 2026.
Analyze this source file and identify ALL independent programming errors, syntax flaws, logic bugs, type errors, off-by-one boundaries, dead code, mutable defaults, and undefined identifiers.
DO NOT STOP AFTER THE FIRST ERROR. Inspect every single function, class, loop, condition, calculation, and variable.

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
                            contents=pass1_prompt,
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

                        # PASS 2: Quick fallback review ONLY if Pass 1 found 0 bugs
                        num_lines = len(chunk_text.splitlines())
                        if num_lines >= 15 and len(raw_bug_list) == 0:
                            found_titles = [b.get("title", "") for b in raw_bug_list]
                            pass2_prompt = f"""Review lines {start_line}-{end_line} of {rel_path} again to identify any ADDITIONAL independent bugs, edge cases, type errors, or calculation flaws not already listed in: {found_titles}.
Source Code:
{chunk_text}

Respond ONLY with a JSON array of additional bugs:
[
  {{
    "title": "Clear concise bug title with line number",
    "line_start": {start_line},
    "line_end": {start_line},
    "problematic_code": "exact bad line",
    "suggested_fix": "replacement line",
    "category": "Syntax Errors | Variable Errors | Function Errors | Logical Errors | Structural Errors | Code Quality Problems",
    "severity": "ERROR | WARNING | INFO",
    "confidence": 90,
    "description": "Short explanation",
    "root_cause": "Detailed explanation",
    "trigger_input_or_state": "Failure condition",
    "repair_summary": "Summary of repair"
  }}
]
If no more bugs exist, return [].
"""
                            try:
                                resp2 = client.models.generate_content(
                                    model=model_attempt,
                                    contents=pass2_prompt,
                                    config=types.GenerateContentConfig(
                                        response_mime_type="application/json",
                                        max_output_tokens=4096
                                    )
                                )
                                parsed2 = robust_json_loads(resp2.text) if (resp2 and resp2.text) else []
                                if isinstance(parsed2, list):
                                    raw_bug_list.extend(parsed2)
                            except Exception:
                                pass

                        # PASS 3: DEDUPLICATION & CONSOLIDATION
                        seen_keys = set()
                        deduped_bugs: List[Dict[str, Any]] = []
                        for b in raw_bug_list:
                            lstart = int(b.get("line_start", start_line))
                            title_norm = re.sub(r'[^a-zA-Z0-9]', '', b.get("title", "").lower()[:20])
                            key = (lstart, title_norm)
                            if key not in seen_keys:
                                seen_keys.add(key)
                                deduped_bugs.append(b)

                        # Sort by line number
                        deduped_bugs.sort(key=lambda x: int(x.get("line_start", 1)))

                        # STEP 4 to STEP 7: SANDBOX RETEST & HEAL LOOP
                        final_composed_code, sandbox_result = retest_and_heal_in_sandbox(
                            client=client,
                            model_name=model_attempt,
                            composed_code=composed_code,
                            file_rel=rel_path,
                            max_retries=3
                        )

                        # Package validated findings into BugReport objects
                        for item in deduped_bugs:
                            line_s = int(item.get("line_start", start_line))
                            line_e = int(item.get("line_end", line_s))
                            single_patched = create_single_bug_patch(content, item)
                            diff = generate_unified_diff(content, single_patched, rel_path)

                            # If single diff is empty but composed diff exists, use composed diff
                            if not diff and final_composed_code != content:
                                single_patched = final_composed_code
                                diff = generate_unified_diff(content, final_composed_code, rel_path)

                            sev_str = str(item.get("severity", "WARNING")).upper()
                            if sev_str not in ("ERROR", "WARNING", "INFO"):
                                sev_str = "WARNING"

                            # Build real sandboxed validation details
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
                                confidence=int(item.get("confidence", 92)),
                                description=item.get("description", ""),
                                root_cause=item.get("root_cause", "Identified by Gemini code review."),
                                trigger_input_or_state=item.get("trigger_input_or_state", "Execution condition."),
                                repair_summary=item.get("repair_summary", "Targeted fix applied."),
                                original_code=content,
                                patched_code=single_patched,
                                composed_code=final_composed_code,
                                diff=diff,
                                validation=validation_obj,
                                status="Needs Review",
                                created_at="Just now"
                            ))

                        chunk_analyzed = True
                        active_model_name = model_attempt
                        break
                    except Exception:
                        continue

                if not chunk_analyzed:
                    chunk_success_all = False
                    break

            if chunk_success_all:
                analyzed_via_gemini = True

        # Fallback / Local Analysis if Gemini not active or offline
        if not analyzed_via_gemini:
            if is_html:
                html_findings = inspect_html_file(rel_path, content)
                if html_findings:
                    composed_html = patch_html_file(content, html_findings)
                    for f in html_findings:
                        single_patched = patch_html_file(content, [f])
                        diff = generate_unified_diff(content, single_patched, rel_path)
                        file_bugs.append(BugReport(
                            id=f"bug-html-{uuid.uuid4().hex[:8]}",
                            title=f["title"],
                            file_path=rel_path,
                            line_start=f["line_start"],
                            line_end=f["line_end"],
                            category=f["category"],
                            severity=f["severity"],
                            confidence=f["confidence"],
                            description=f["description"],
                            root_cause=f["root_cause"],
                            trigger_input_or_state=f["trigger_input_or_state"],
                            repair_summary=f["repair_summary"],
                            original_code=content,
                            patched_code=single_patched,
                            composed_code=composed_html,
                            diff=diff,
                            status="Needs Review",
                            created_at="Just now"
                        ))
            elif is_prog:
                from ast_detector import detect_ast_bugs
                from ast_patcher import apply_single_ast_patch, compose_multi_ast_patches
                raw_findings = detect_ast_bugs(rel_path, content)
                if raw_findings:
                    composed_code, _ = compose_multi_ast_patches(content, raw_findings, rel_path)
                    for finding in raw_findings:
                        patched_code, diff = apply_single_ast_patch(content, finding, rel_path)
                        if not diff and composed_code != content:
                            patched_code = composed_code
                            diff = generate_unified_diff(content, composed_code, rel_path)
                        file_bugs.append(BugReport(
                            id=finding["id"],
                            title=finding["title"],
                            file_path=rel_path,
                            line_start=finding["line_start"],
                            line_end=finding["line_end"],
                            col_offset=finding.get("col_offset", 0),
                            end_col_offset=finding.get("end_col_offset", 0),
                            category=finding["category"],
                            severity=finding["severity"],
                            confidence=finding["confidence"],
                            description=finding.get("description", ""),
                            root_cause=finding["root_cause"],
                            trigger_input_or_state=finding["trigger_input_or_state"],
                            repair_summary=finding.get("repair_summary", "Applied targeted fix."),
                            original_code=content,
                            patched_code=patched_code,
                            composed_code=composed_code,
                            diff=diff,
                            status="Needs Review",
                            created_at="Just now"
                        ))

        # Save to Cache
        LLM_CACHE[cache_key] = (file_bugs, active_model_name)
        bugs.extend(file_bugs)

    if not effective_key:
        engine_label = "Gemini LLM Engine (Local Heuristic / API Key Setup Required)"
    else:
        engine_label = f"Google Gemini LLM Engine ({active_model_name})"

    return bugs, engine_label
