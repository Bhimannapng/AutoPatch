# 🛡️ AutoPatch – Autonomous AI Software Intelligence & Project Repair Platform
> **INNOVEDGE Hackathon 2026 – Problem Statement 02**  
> **Target Developer Account:** `bhimanna2006@gmail.com`  
> **Architecture:** Multi-Language Project Intelligence Platform + 3 Specialized AI Agents + Autonomous Sandbox Repair

---

## 🚀 Overview & New Project Vision

**AutoPatch** has evolved from an individual code error checker into a complete **AI-powered software engineering assistant and project intelligence platform**. 

When a developer or engineering team uploads a complete software repository or code snippet, AutoPatch:
1. **Understands the Complete Project Structure:** Maps files, directories, languages, frameworks, entry points, and module dependency graphs.
2. **Performs Multi-Domain Analysis:** Identifies syntax/semantic bugs, investigates root causes, discovers CPU/RAM bottlenecks, audits security vulnerabilities, and evaluates modularity.
3. **Deploys Three Specialized AI Agents:**
   - 🐞 **Dr. Patch (Bug Intelligence Specialist):** Investigates root causes, explains failure states, and designs surgical patches.
   - ⚡ **Nova (RAM & Performance Engineer):** Profiles memory allocations, detects $O(N^2)/O(N^3)$ loops, finds memory leaks, and eliminates dead code.
   - 🛡️ **Aegis (Architecture & Security Auditor):** Audits OWASP vulnerabilities (SQL injection, command execution, hardcoded keys) and checks cross-module coupling.
   - 🤖 **AutoPatch Lead Orchestrator:** Synthesizes multi-agent insights and coordinates technical strategy.
4. **Autonomous Patch Studio & Sandbox Validation:** Generates focused unified diffs, runs isolated sandbox builds and test executions, measures execution metrics, and provides safe 1-click **Accept**, **Reject**, or **Revert** rollback.
5. **Retains the Original Code Error Finder:** Fully preserves instant snippet analysis across pure AST, Google Gemini LLM, Combined pipeline, and Sandbox modes.

---

## 📦 Project Ingestion Modes

AutoPatch provides four input pathways:

| Ingestion Mode | Capabilities & Safeguards |
| :--- | :--- |
| **Option A: Upload ZIP** | Safely extracts project archives with strict path-traversal protection (`..` directory escape prevention). Unnests single root directories, identifies dependencies, and indexes the entire codebase. |
| **Option B: GitHub Repository** | Clones public or private GitHub repositories via shallow clone (`--depth 1`), validates URLs, supports branch selection, and records commit hashes without exposing private tokens. |
| **Option C: Project Folder** | Direct browser directory upload via `webkitdirectory`, automatically filtering vendor artifacts (`node_modules`, `.git`, `venv`) while reading complete source files. |
| **Option D: Individual Files / Snippet** | Instant code editor for Python, Java, JavaScript, and HTML with language auto-detection, instant AST scanning, and benchmark loading. |

---

## 🧠 Shared Intelligence Architecture & Token Optimization

AutoPatch avoids costly and repetitive full-project LLM scans by implementing a **Shared Project Intelligence Architecture**:
1. **Deterministic Local Analysis First:** Pure AST parsing (`ast`, `javalang`, `esprima`), regex vulnerability scanning, loop complexity detection, and `tracemalloc` runtime profiling run locally on the machine with **0 API token cost** and sub-second execution.
2. **Central Project Context:** A single unified `ProjectAnalysisSummary` stores structure, dependencies, defects, optimizations, and security findings.
3. **Targeted Context Retrieval for Gemini:** When chatting with any specialist agent, AutoPatch retrieves only the specific relevant file snippets (max 80 lines) and related findings, avoiding quadratic token explosion.
4. **Primary LLM Engine:** Google Gemini SDK with `gemini-3.1-flash-lite` (sub-second latency) with automatic fallback to `gemini-3.8-flash` and deterministic offline intelligence.

---

## 👥 The Three Specialized AI Agents

AutoPatch presents three dedicated specialists grounded in the uploaded project context:

### 1. 🐞 Dr. Patch – Code Intelligence & Bug Detection
- **Role:** Software Debugging Specialist
- **Focus:** Root-cause investigation, syntax/semantic errors, logic flaws, and targeted patches.
- **Sample Queries:**
  - *"Why is my application crashing?"*
  - *"Which bug should I fix first and why?"*
  - *"Explain the root cause of the primary defect in server.py."*

### 2. ⚡ Nova – Performance & RAM Optimisation
- **Role:** Software Performance and Memory Optimization Engineer
- **Focus:** Heap RAM allocations, $O(N^2)/O(N^3)$ loop refactoring, unclosed file descriptors, eager list comprehensions vs generators, and redundant debug statements.
- **Honest Metrics:** Clearly distinguishes between statically suspected bottlenecks and sandboxed runtime measurements.
- **Sample Queries:**
  - *"How can I reduce unnecessary memory usage in process_data?"*
  - *"Are there any nested loops that can be optimized from $O(N^3)$ to $O(N)$?"*

### 3. 🛡️ Aegis – Architecture & Security Auditor
- **Role:** Senior Software Architect and Security Reviewer
- **Focus:** OWASP vulnerability detection (SQL injection, shell command injection, unsafe `eval`/`exec`, hardcoded secrets, unsafe deserialization), cross-file import consistency, and frontend/backend endpoint alignment.
- **Sample Queries:**
  - *"Are there any security vulnerabilities or exposed credentials?"*
  - *"Is my project architecture clean, modular, and maintainable?"*

---

## 🛠️ Autonomous Patch Studio & Safe Rollback

1. **Focused Code Corrections:** Shows original code, suggested fix, and side-by-side / unified diff.
2. **Deep Root-Cause Explanations:**
   - **What is happening**
   - **Why it occurred**
   - **Trigger condition or input**
   - **Suggested fix & confidence rating**
3. **Sandboxed Testing & Verification:**
   - Compiles and runs code in an isolated sandbox (`python`, `javac`/`java`, `node`).
   - Reports exact test results (passed, failed, timeouts).
   - Validates multi-fix composition to ensure patches don't conflict.
4. **100% Safe Reversible Rollback:**
   - **Accept Patch:** Writes patch to workspace and logs timestamped history entry.
   - **Reject Patch:** Dismisses patch with engineer notes.
   - **Revert Patch:** Restores the exact original source code from memory backup.
   - **Export Fixed Project (.zip):** One-click download of the repaired workspace.

---

## 🧪 Comprehensive Automated Test Suite (27 Tests)

All 27 automated tests pass 100% in **0.55 seconds**:

```bash
source venv/bin/activate
PYTHONPATH=backend pytest tests/
```

### Test Coverage Highlights:
- **Test 1:** Small Python project (file discovery, AST, root-cause analysis, patches).
- **Test 2:** Java project analysis (`javalang` parser, methods, zero division, unreachable statements).
- **Test 3:** Full-stack project discovery (React frontend + FastAPI backend detection).
- **Test 4:** Performance analysis ($O(N^3)$ triple nested loops detection).
- **Test 5:** RAM analysis (Heap memory profiling via `tracemalloc`).
- **Test 6:** Security analysis (Hardcoded secrets, SQL injection, command execution).
- **Test 7:** Three-agent collaboration (Shared project context, distinct perspectives).
- **Test 8:** Large project handling (750+ to 1,000+ lines across multiple modules without limits).
- **Test 9:** Safe patch rollback and revert in state.
- **Tests 10–27:** AST multi-error recovery, tolerant syntax parsing, engine mode switching.

---

## 🚦 Running the Application

### 1. Prerequisites
- Python 3.11+
- Node.js 18+

### 2. Start Backend API Server
```bash
cd /Users/bhimanna/Desktop/AutoPatch
source venv/bin/activate
PYTHONPATH=backend uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Start Frontend Workstation
```bash
cd /Users/bhimanna/Desktop/AutoPatch/frontend
npm run dev
```

Visit **`http://localhost:5173`** to access the complete AutoPatch platform.

---

## 🌐 Live Production Deployments

The platform is fully deployed and accessible 24/7 without requiring local servers:

| Component | Deployment Provider | Production URL |
| :--- | :--- | :--- |
| **Web Frontend** | Firebase Hosting | [`https://autopatch-ai-2026.web.app`](https://autopatch-ai-2026.web.app) |
| **Cloud API Backend** | Render Web Service | [`https://autopatch-a7em.onrender.com`](https://autopatch-a7em.onrender.com) |
| **GitHub Repository** | GitHub (Branch: `main`) | [`https://github.com/Bhimannapng/AutoPatch`](https://github.com/Bhimannapng/AutoPatch) |

---

## 📈 Evolution Milestones & Session History

### 1. Cloud Infrastructure & 24/7 Global Availability
- Migrated AutoPatch from local-only execution to a fully decoupled cloud architecture.
- Frontend hosted on Firebase Hosting with global CDN edge caching.
- Backend containerized and deployed on Render with automated GitHub CD pipeline.
- Added `/api/health` system monitoring endpoint with live engine diagnostics.

### 2. High-Performance Multi-Language AST Engine
- Engineered deterministic offline analyzers for **Python** (`ast`), **Java** (`javalang`), **JavaScript** (`esprima` + structural regex), **HTML** (WCAG 2.1 accessibility & form standards), and **CSS** (cross-browser hex/rgba fallbacks).
- Multi-language AST runs in **< 0.005 seconds** with **0 API tokens** consumed.
- Added strict 3.5s timeout for Gemini LLM calls, providing instant deterministic fallback and eliminating UI freezing.

### 3. Sandbox Hardening & Security Safeguards
- **Path Traversal Guard**: Archive decompression rejects `..` path escaping and unauthorized filesystem traversals.
- **Memory Bomb & Infinite Loop Protection**: Sandboxed execution compiles `__main__` entry points without executing long-running infinite loops or 5GB heap memory bombs.
- **CORS Universal Compatibility**: Configured `allow_credentials=False` with open origin permissions, eliminating preflight network failures (`status: 0`) across Safari, Chrome, and Firefox.

### 4. Benchmark & Accuracy Audit
- **Official Problem Statement 02 Benchmark Suite** ([`benchmarks/`](file:///Users/bhimanna/Desktop/AutoPatch/benchmarks)):
  - **40 Distinct Bugs** (`AP001` to `AP040`) across **Python, Java, JavaScript, and C**.
  - **200 Standardized Test Scenarios** ($40 \times 5$: `primary_trigger`, `normal_input`, `boundary_input`, `edge_case`, `regression_check`).
  - Available in both `.csv` and `.json` formats for automated CI/CD and LLM evaluation harnesses.
- Evaluated `simple_attendance_system` against comparative benchmark reports:
  - **40% Strict Precision / 60% Generous Precision** achieved by standard reports, with **40% False Positive (Hallucination) Rate** (e.g. hallucinating missing button types or DOM XSS when `textContent` is used).
  - Detected critical unhandled `JSON.parse(localStorage)` exceptions and timestamp ID collisions that naive tools missed.

### 5. Presentation & Hackathon Deliverables
- **`AutoPatch_Presentation.pptx`**: 10-slide widescreen (16:9) executive presentation deck with live UI screenshots and architecture flows.
- **`AutoPatch_Presenter_Guide.pdf`**: 12-page presentation script, slide-by-slide talking points, anticipated judges' Q&A defense playbook, and live demo steps.

