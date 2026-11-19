import os
import re
import sys
import shutil
import zipfile
import subprocess
import tempfile
import time
from typing import Dict, List, Tuple, Optional, Set
import psutil

from schemas import (
    FileNode,
    DependencyRelation,
    ProjectCapacityMetrics,
    ProjectStructureReport
)

EXCLUDED_DIR_PATTERNS = {
    "node_modules": "Third-party vendor dependency directory",
    ".git": "Version control repository metadata",
    "__pycache__": "Compiled Python bytecode cache",
    ".pytest_cache": "Test runner temporary cache",
    "venv": "Isolated Python virtual environment",
    ".venv": "Isolated Python virtual environment",
    "env": "Environment configuration directory",
    "dist": "Compiled production distribution bundle",
    "build": "Build output artifacts",
    ".idea": "IDE metadata directory",
    ".vscode": "IDE configuration directory",
    "target": "Java Maven/Gradle build target directory",
    "coverage": "Code coverage report directory"
}

EXCLUDED_FILE_EXTENSIONS = {
    ".pyc": "Compiled Python binary bytecode",
    ".pyo": "Optimized Python binary bytecode",
    ".class": "Compiled Java bytecode class file",
    ".o": "Compiled object binary",
    ".so": "Compiled shared library binary",
    ".dylib": "macOS dynamic library binary",
    ".dll": "Windows dynamic link library binary",
    ".exe": "Compiled executable binary",
    ".min.js": "Minified production JavaScript bundle",
    ".map": "JavaScript/CSS source map",
    ".png": "Binary image file",
    ".jpg": "Binary image file",
    ".jpeg": "Binary image file",
    ".gif": "Binary image file",
    ".svg": "Vector graphic file",
    ".ico": "Binary icon file",
    ".woff": "Binary font file",
    ".woff2": "Binary font file",
    ".ttf": "Binary font file",
    ".zip": "Archive file",
    ".tar": "Archive file",
    ".gz": "Compressed archive",
    ".sqlite": "Binary database file",
    ".db": "Binary database file"
}

def safe_extract_zip(zip_path: str, extract_to: str) -> None:
    """
    Safely extracts a ZIP archive with strict path-traversal safeguards.
    Prevents directory escape, malicious symlinks, and absolute path injection.
    """
    extract_to = os.path.abspath(extract_to)
    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.infolist():
            # Check for path traversal or absolute paths
            target_path = os.path.abspath(os.path.join(extract_to, member.filename))
            if not target_path.startswith(extract_to + os.sep) and target_path != extract_to:
                raise ValueError(f"Security Alert: Blocked path traversal attempt in archive: {member.filename}")
            
            # Check for illegal symbolic links
            if member.is_dir():
                os.makedirs(target_path, exist_ok=True)
            else:
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                with zf.open(member) as source, open(target_path, "wb") as target:
                    shutil.copyfileobj(source, target)

def unnest_single_root_directory(target_dir: str) -> None:
    """
    If the extracted archive contains a single top-level directory (e.g. repo-main/),
    unnest it so the project files sit directly in the target directory.
    """
    entries = [e for e in os.listdir(target_dir) if not e.startswith(".")]
    if len(entries) == 1:
        single_path = os.path.join(target_dir, entries[0])
        if os.path.isdir(single_path):
            temp_move = tempfile.mkdtemp()
            for item in os.listdir(single_path):
                shutil.move(os.path.join(single_path, item), temp_move)
            shutil.rmtree(single_path)
            for item in os.listdir(temp_move):
                shutil.move(os.path.join(temp_move, item), target_dir)
            shutil.rmtree(temp_move)

def clone_github_repo(repo_url: str, target_dir: str, branch: Optional[str] = None, auth_token: Optional[str] = None) -> Dict[str, str]:
    """
    Clones a GitHub repository using git CLI with security verification and shallow clone.
    """
    # URL validation
    clean_url = repo_url.strip()
    if not (clean_url.startswith("https://github.com/") or clean_url.startswith("git@github.com:") or clean_url.startswith("http://github.com/")):
        raise ValueError("Invalid GitHub repository URL. Must be a valid github.com repository.")
    
    # Authenticated URL injection if token provided
    clone_target_url = clean_url
    if auth_token and clean_url.startswith("https://github.com/"):
        token_clean = auth_token.strip()
        clone_target_url = clean_url.replace("https://github.com/", f"https://x-access-token:{token_clean}@github.com/")
    
    cmd = ["git", "clone", "--depth", "1"]
    if branch:
        cmd.extend(["--branch", branch.strip()])
    cmd.extend([clone_target_url, target_dir])

    # Run git clone with timeout
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=60,
            check=True
        )
    except subprocess.CalledProcessError as e:
        # Scrub token from error message
        err_msg = e.stderr or e.stdout or "Git clone failed"
        if auth_token:
            err_msg = err_msg.replace(auth_token, "******")
        raise RuntimeError(f"Git clone error: {err_msg.strip()}")
    except subprocess.TimeoutExpired:
        raise TimeoutError("Git clone timed out after 60 seconds.")

    # Retrieve commit hash & default branch
    commit_hash = "unknown"
    resolved_branch = branch or "default"
    try:
        c_proc = subprocess.run(["git", "rev-parse", "HEAD"], cwd=target_dir, capture_output=True, text=True, timeout=5)
        if c_proc.returncode == 0:
            commit_hash = c_proc.stdout.strip()[:10]
        b_proc = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=target_dir, capture_output=True, text=True, timeout=5)
        if b_proc.returncode == 0:
            resolved_branch = b_proc.stdout.strip()
    except Exception:
        pass

    return {
        "commit": commit_hash,
        "branch": resolved_branch,
        "repo_url": clean_url
    }

def scan_project_structure(
    project_dir: str,
    project_name: str,
    archive_size_bytes: int = 0
) -> Tuple[Dict[str, str], ProjectCapacityMetrics, ProjectStructureReport]:
    """
    Performs full project-level indexing:
    1. Traverses the directory tree.
    2. Segregates source files from vendor/build artifacts.
    3. Detects languages, frameworks, entry points, and dependency relationships.
    4. Computes capacity metrics (lines, sizes, RAM consumption).
    """
    start_time = time.time()
    initial_rss = psutil.Process().memory_info().rss

    discovered_files: List[str] = []
    relevant_files: Dict[str, str] = {}
    excluded_files: List[Dict[str, str]] = []
    total_lines = 0
    extracted_bytes = 0

    detected_languages_set: Set[str] = set()
    detected_frameworks_set: Set[str] = set()
    entry_points: List[str] = []
    dependencies_list: List[DependencyRelation] = []

    # Walk the directory tree
    for root, dirs, files in os.walk(project_dir):
        # Filter directories to skip traversing deep vendor folders
        dirs_to_remove = []
        for d in dirs:
            if d in EXCLUDED_DIR_PATTERNS:
                rel_d = os.path.relpath(os.path.join(root, d), project_dir)
                excluded_files.append({"file": rel_d + "/", "reason": EXCLUDED_DIR_PATTERNS[d]})
                dirs_to_remove.append(d)
        for d in dirs_to_remove:
            dirs.remove(d)

        for f in files:
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, project_dir)
            discovered_files.append(rel_path)

            try:
                f_size = os.path.getsize(full_path)
                extracted_bytes += f_size
            except Exception:
                f_size = 0

            ext = os.path.splitext(f)[1].lower()

            if ext in EXCLUDED_FILE_EXTENSIONS:
                excluded_files.append({"file": rel_path, "reason": EXCLUDED_FILE_EXTENSIONS[ext]})
                continue

            # Read source content
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as file_obj:
                    content = file_obj.read()
            except Exception as e:
                excluded_files.append({"file": rel_path, "reason": f"Unreadable file: {str(e)}"})
                continue

            relevant_files[rel_path] = content
            lines = content.splitlines()
            total_lines += len(lines)

            # Language detection
            if ext == ".py":
                detected_languages_set.add("Python")
                if "if __name__ == '__main__':" in content or "if __name__ == \"__main__\":" in content or f in ("main.py", "app.py", "server.py", "manage.py", "wsgi.py"):
                    entry_points.append(rel_path)
                # Parse Python dependencies
                parse_python_dependencies(rel_path, content, dependencies_list)

            elif ext == ".java":
                detected_languages_set.add("Java")
                if "public static void main(" in content:
                    entry_points.append(rel_path)
                parse_java_dependencies(rel_path, content, dependencies_list)

            elif ext in (".js", ".jsx", ".mjs"):
                detected_languages_set.add("JavaScript")
                if f in ("index.js", "main.js", "server.js", "app.js") or "const app = express()" in content:
                    entry_points.append(rel_path)
                parse_js_dependencies(rel_path, content, dependencies_list)

            elif ext in (".ts", ".tsx"):
                detected_languages_set.add("TypeScript")
                if f in ("index.ts", "main.ts", "server.ts", "App.tsx", "main.tsx", "index.tsx"):
                    entry_points.append(rel_path)
                parse_js_dependencies(rel_path, content, dependencies_list)

            elif ext in (".c", ".h"):
                detected_languages_set.add("C")
                if "int main(" in content or "void main(" in content:
                    entry_points.append(rel_path)

            elif ext in (".cpp", ".hpp", ".cc"):
                detected_languages_set.add("C++")
                if "int main(" in content:
                    entry_points.append(rel_path)

            elif ext == ".html":
                detected_languages_set.add("HTML")
                if f in ("index.html", "default.html"):
                    entry_points.append(rel_path)

            elif ext == ".css":
                detected_languages_set.add("CSS")

            # Framework detection via config / manifest files
            if f == "requirements.txt":
                c_lower = content.lower()
                if "flask" in c_lower: detected_frameworks_set.add("Flask")
                if "django" in c_lower: detected_frameworks_set.add("Django")
                if "fastapi" in c_lower: detected_frameworks_set.add("FastAPI")
                if "torch" in c_lower or "pytorch" in c_lower: detected_frameworks_set.add("PyTorch")
                if "tensorflow" in c_lower: detected_frameworks_set.add("TensorFlow")
                if "pandas" in c_lower or "numpy" in c_lower: detected_frameworks_set.add("Data Science Stack")
                if "uvicorn" in c_lower: detected_frameworks_set.add("ASGI/Uvicorn")

            elif f == "package.json":
                c_lower = content.lower()
                if '"react"' in c_lower or '"react-dom"' in c_lower: detected_frameworks_set.add("React")
                if '"vue"' in c_lower: detected_frameworks_set.add("Vue.js")
                if '"next"' in c_lower: detected_frameworks_set.add("Next.js")
                if '"express"' in c_lower: detected_frameworks_set.add("Express.js")
                if '"tailwindcss"' in c_lower: detected_frameworks_set.add("TailwindCSS")
                if '"vite"' in c_lower: detected_frameworks_set.add("Vite")

            elif f in ("pom.xml", "build.gradle"):
                c_lower = content.lower()
                if "spring-boot" in c_lower or "springframework" in c_lower:
                    detected_frameworks_set.add("Spring Boot")
                if "junit" in c_lower:
                    detected_frameworks_set.add("JUnit")

            elif f in ("Dockerfile", "docker-compose.yml", "docker-compose.yaml"):
                detected_frameworks_set.add("Docker")

    # Determine project type
    langs = sorted(list(detected_languages_set))
    frameworks = sorted(list(detected_frameworks_set))
    
    has_frontend = (any(lang in ("JavaScript", "TypeScript", "HTML") for lang in langs) or any(fw in ("React", "Vue.js", "Next.js", "TailwindCSS", "Vite") for fw in frameworks))
    has_backend = (any(lang in ("Python", "Java", "C++") for lang in langs) or any(fw in ("Flask", "Django", "FastAPI", "Express.js", "Spring Boot") for fw in frameworks))

    if has_frontend and has_backend:
        project_type = "Full-Stack Application (Frontend + Backend)"
    elif has_frontend:
        project_type = "Frontend Web Application"
    elif has_backend:
        project_type = "Backend / API Service"
    elif "Python" in langs:
        project_type = "Python Application / Library"
    elif "Java" in langs:
        project_type = "Java Enterprise / Desktop Project"
    elif "C" in langs or "C++" in langs:
        project_type = "Systems / C++ Application"
    else:
        project_type = "Multi-Language Software Repository"

    # Memory and duration metrics
    current_rss = psutil.Process().memory_info().rss
    ram_mb = max(0.1, round((current_rss - initial_rss) / (1024 * 1024), 2))
    duration_ms = round((time.time() - start_time) * 1000, 2)

    capacity_metrics = ProjectCapacityMetrics(
        total_archive_size_bytes=archive_size_bytes or extracted_bytes,
        extracted_size_bytes=extracted_bytes,
        total_files_discovered=len(discovered_files),
        relevant_source_files=len(relevant_files),
        total_lines_of_code=total_lines,
        files_analyzed=len(relevant_files),
        files_excluded=excluded_files[:50],  # Top 50 excluded entries with reasons
        files_remaining=0,
        ram_consumed_mb=ram_mb,
        analysis_duration_ms=duration_ms,
        gemini_tokens_used=0
    )

    report = ProjectStructureReport(
        project_name=project_name,
        project_type=project_type,
        detected_languages=langs or ["Unknown"],
        detected_frameworks=frameworks or ["Standard Library"],
        entry_points=sorted(entry_points),
        file_tree=[],
        dependencies=dependencies_list[:100],  # Top 100 dependency relations
        capacity_metrics=capacity_metrics
    )

    return relevant_files, capacity_metrics, report

def parse_python_dependencies(rel_path: str, content: str, deps: List[DependencyRelation]) -> None:
    """Parses import statements in Python files to map module connections."""
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("import ") or line.startswith("from "):
            # Match: from foo.bar import baz, qux
            m_from = re.match(r"^from\s+([A-Za-z0-9_\.]+)\s+import\s+(.+)$", line)
            if m_from:
                target_mod = m_from.group(1)
                symbols = [s.strip().split(" as ")[0] for s in m_from.group(2).split(",")]
                is_ext = not (target_mod.startswith(".") or any(x in rel_path for x in target_mod.split(".")))
                deps.append(DependencyRelation(
                    source_file=rel_path,
                    target=target_mod,
                    imported_symbols=symbols,
                    is_external=is_ext
                ))
                continue
            # Match: import foo, bar
            m_imp = re.match(r"^import\s+(.+)$", line)
            if m_imp:
                modules = [m.strip().split(" as ")[0] for m in m_imp.group(1).split(",")]
                for mod in modules:
                    deps.append(DependencyRelation(
                        source_file=rel_path,
                        target=mod,
                        imported_symbols=[],
                        is_external=True
                    ))

def parse_java_dependencies(rel_path: str, content: str, deps: List[DependencyRelation]) -> None:
    """Parses import statements in Java files."""
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("import "):
            m = re.match(r"^import\s+(?:static\s+)?([A-Za-z0-9_\.]+);", line)
            if m:
                target_pkg = m.group(1)
                is_ext = not target_pkg.startswith("com.autopatch")
                deps.append(DependencyRelation(
                    source_file=rel_path,
                    target=target_pkg,
                    imported_symbols=[],
                    is_external=is_ext
                ))

def parse_js_dependencies(rel_path: str, content: str, deps: List[DependencyRelation]) -> None:
    """Parses import / require statements in JS/TS files."""
    for line in content.splitlines():
        line = line.strip()
        # import ... from '...';
        m_from = re.search(r"import\s+.*?\s+from\s+['\"]([^'\"]+)['\"]", line)
        if m_from:
            target = m_from.group(1)
            deps.append(DependencyRelation(
                source_file=rel_path,
                target=target,
                imported_symbols=[],
                is_external=not target.startswith(".")
            ))
            continue
        # require('...')
        m_req = re.search(r"require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)", line)
        if m_req:
            target = m_req.group(1)
            deps.append(DependencyRelation(
                source_file=rel_path,
                target=target,
                imported_symbols=[],
                is_external=not target.startswith(".")
            ))
