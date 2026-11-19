import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

# Initialize 16:9 Widescreen Presentation
prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

# Color Palette (Dark Mode Modern Tech Theme)
BG_COLOR = RGBColor(15, 23, 42)        # Deep Navy Slate (#0f172a)
CARD_BG = RGBColor(30, 41, 59)         # Darker Slate Panel (#1e293b)
PRIMARY_ACCENT = RGBColor(56, 189, 248) # Electric Cyan (#38bdf8)
SECONDARY_ACCENT = RGBColor(52, 211, 153) # Emerald Green (#34d399)
PURPLE_ACCENT = RGBColor(168, 85, 247)  # Violet (#a855f7)
TEXT_WHITE = RGBColor(248, 250, 252)    # Crisp Off-White (#f8fafc)
TEXT_MUTED = RGBColor(148, 163, 184)    # Slate Muted Gray (#94a3b8)

# Images available from real project runs
IMG_DASHBOARD = '/Users/bhimanna/.gemini/antigravity/brain/61713ad2-0583-46f0-a26b-4a700f47240a/.system_generated/logs/media/step_1205_media_0.png'
IMG_ANALYSIS = '/Users/bhimanna/.gemini/antigravity/brain/61713ad2-0583-46f0-a26b-4a700f47240a/browser_evidence/a8d1179a-62e3-40e0-82ac-5f49215777af/final_step_34.png'
IMG_SECURITY = '/Users/bhimanna/.gemini/antigravity/brain/61713ad2-0583-46f0-a26b-4a700f47240a/browser_evidence/871c6e80-4d1b-4a83-877d-f5735db37068/final_step_24.png'
IMG_DIFF = '/Users/bhimanna/.gemini/antigravity/brain/61713ad2-0583-46f0-a26b-4a700f47240a/browser_evidence/830c2058-02fd-4237-adea-567ccdb26acf/final_step_21.png'

def set_slide_background(slide):
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = BG_COLOR

def add_header(slide, title_text, category_badge="AUTOPATCH 2.0"):
    # Category Pill
    badge_box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(0.45), Inches(2.4), Inches(0.35))
    badge_box.fill.solid()
    badge_box.fill.fore_color.rgb = RGBColor(14, 116, 144)
    badge_box.line.color.rgb = PRIMARY_ACCENT
    badge_box.line.width = Pt(1)
    tf_b = badge_box.text_frame
    tf_b.word_wrap = True
    p_b = tf_b.paragraphs[0]
    p_b.text = category_badge
    p_b.alignment = PP_ALIGN.CENTER
    p_b.font.size = Pt(10)
    p_b.font.bold = True
    p_b.font.color.rgb = PRIMARY_ACCENT
    
    # Title Text
    title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.9), Inches(11.7), Inches(0.85))
    tf = title_box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title_text
    p.font.size = Pt(25)
    p.font.bold = True
    p.font.color.rgb = TEXT_WHITE

def create_card(slide, left, top, width, height, title, items, badge_text="", border_color=PRIMARY_ACCENT):
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    card.fill.solid()
    card.fill.fore_color.rgb = CARD_BG
    card.line.color.rgb = border_color
    card.line.width = Pt(1.5)
    
    tb = slide.shapes.add_textbox(left + Inches(0.2), top + Inches(0.15), width - Inches(0.4), height - Inches(0.3))
    tf = tb.text_frame
    tf.word_wrap = True
    
    p_title = tf.paragraphs[0]
    p_title.text = title
    p_title.font.size = Pt(15)
    p_title.font.bold = True
    p_title.font.color.rgb = border_color
    p_title.space_after = Pt(8)
    
    if badge_text:
        p_badge = tf.add_paragraph()
        p_badge.text = f"[{badge_text}]"
        p_badge.font.size = Pt(9.5)
        p_badge.font.bold = True
        p_badge.font.color.rgb = SECONDARY_ACCENT
        p_badge.space_after = Pt(6)
        
    for item in items:
        p_item = tf.add_paragraph()
        p_item.text = f"• {item}"
        p_item.font.size = Pt(11)
        p_item.font.color.rgb = TEXT_MUTED
        p_item.space_after = Pt(4.5)

# ==========================================
# SLIDE 1: TITLE SLIDE
# ==========================================
slide1 = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_background(slide1)

t_box = slide1.shapes.add_textbox(Inches(1.2), Inches(1.6), Inches(10.9), Inches(3.3))
tf1 = t_box.text_frame
tf1.word_wrap = True

p_badge = tf1.paragraphs[0]
p_badge.text = "INNOVEDGE HACKATHON 2026 — AUTONOMOUS SOFTWARE ENGINEERING"
p_badge.font.size = Pt(13)
p_badge.font.bold = True
p_badge.font.color.rgb = PRIMARY_ACCENT
p_badge.space_after = Pt(12)

p_title = tf1.add_paragraph()
p_title.text = "AutoPatch 2.0"
p_title.font.size = Pt(54)
p_title.font.bold = True
p_title.font.color.rgb = TEXT_WHITE
p_title.space_after = Pt(10)

p_sub = tf1.add_paragraph()
p_sub.text = "Autonomous AI Project Intelligence, Root-Cause Investigation, Code Repair & RAM Optimization"
p_sub.font.size = Pt(17)
p_sub.font.color.rgb = TEXT_MUTED
p_sub.space_after = Pt(18)

info_panel = slide1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.2), Inches(5.1), Inches(10.9), Inches(1.6))
info_panel.fill.solid()
info_panel.fill.fore_color.rgb = CARD_BG
info_panel.line.color.rgb = PRIMARY_ACCENT
info_panel.line.width = Pt(1.2)

info_tb = slide1.shapes.add_textbox(Inches(1.4), Inches(5.25), Inches(10.5), Inches(1.3))
info_tf = info_tb.text_frame
info_tf.word_wrap = True

p_dev = info_tf.paragraphs[0]
p_dev.text = "Developer & Lead Engineer: Bhimanna (bhimanna2006@gmail.com)  |  Version: 2.0.0 Production"
p_dev.font.size = Pt(12.5)
p_dev.font.bold = True
p_dev.font.color.rgb = TEXT_WHITE
p_dev.space_after = Pt(4)

p_urls = info_tf.add_paragraph()
p_urls.text = "Live Web App: https://autopatch-ai-2026.web.app  |  Cloud API: https://autopatch-a7em.onrender.com (24/7)"
p_urls.font.size = Pt(11)
p_urls.font.color.rgb = SECONDARY_ACCENT
p_urls.space_after = Pt(3)

p_git = info_tf.add_paragraph()
p_git.text = "GitHub Repository: https://github.com/Bhimannapng/AutoPatch (Branch: main)"
p_git.font.size = Pt(10.5)
p_git.font.color.rgb = PRIMARY_ACCENT

# ==========================================
# SLIDE 2: THE PROBLEM STATEMENT
# ==========================================
slide2 = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_background(slide2)
add_header(slide2, "The Problem: Why Traditional Debugging Fails Modern Teams", "INDUSTRY CHALLENGES")

create_card(slide2, Inches(0.8), Inches(1.9), Inches(3.6), Inches(5.0), 
    "Time-Consuming Debugging", 
    [
        "Engineers spend over 40% of their working hours hunting bugs and tracing root causes.",
        "Manual stack trace parsing is tedious across complex microservices and large repositories.",
        "Context switching between coding, reproducing defects, and testing drains team velocity.",
        "Developers lack automated tools that explain WHY code fails at execution boundaries."
    ],
    "HIGH COGNITIVE LOAD",
    RGBColor(239, 68, 68)
)

create_card(slide2, Inches(4.8), Inches(1.9), Inches(3.6), Inches(5.0), 
    "Silent Memory & RAM Leaks", 
    [
        "O(N²) algorithm loops and unclosed resource handles slip past standard unit tests.",
        "Memory bloat degrades cloud performance over time, causing costly out-of-memory crashes.",
        "Traditional profilers generate complex heap dumps without actionable code repairs.",
        "Engineering teams struggle to refactor memory bottlenecks without risking logic breaks."
    ],
    "PERFORMANCE DEGRADATION",
    RGBColor(245, 158, 11)
)

create_card(slide2, Inches(8.8), Inches(1.9), Inches(3.6), Inches(5.0), 
    "Risky LLM Hallucinations", 
    [
        "Generic AI tools suffer a ~40% hallucination rate on code syntax and API attributes.",
        "Unverified AI suggestions frequently break existing functionality and cause regressions.",
        "Lack of sandboxed integrity testing before code review leads to broken deployments.",
        "Security flaws (SQL injection, leaked credentials) are routinely missed by naive linters."
    ],
    "REGRESSION DANGER",
    RGBColor(236, 72, 153)
)

# ==========================================
# SLIDE 3: THE AUTOPATCH SOLUTION
# ==========================================
slide3 = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_background(slide3)
add_header(slide3, "The AutoPatch Solution: Full-Lifecycle Autonomous Code Repair", "THE INNOVATION")

create_card(slide3, Inches(0.8), Inches(1.9), Inches(5.6), Inches(5.0),
    "Autonomous Software Engineering Platform",
    [
        "Full-Project Ingestion: Ingests repositories via ZIP, GitHub Clone, folder upload, or pasted code.",
        "Three Dedicated AI Specialists: Collaborative agents covering Bugs, RAM, and Security.",
        "Deep Root-Cause Investigation: Uncovers the exact trigger state and execution conditions.",
        "Automated Patch Studio: Generates surgical, side-by-side unified Git diffs for every issue.",
        "Sandboxed Verification Safety Net: Pre-tests all patches in isolated runtime environments.",
        "100% Reversible Rollbacks: 1-click Accept, Reject, or Revert with timestamped audit history."
    ],
    "FULL-LIFECYCLE PLATFORM",
    PRIMARY_ACCENT
)

if os.path.exists(IMG_DASHBOARD):
    slide3.shapes.add_picture(IMG_DASHBOARD, Inches(6.8), Inches(1.9), width=Inches(5.7))

# ==========================================
# SLIDE 4: THE 3 SPECIALIST AI AGENTS
# ==========================================
slide4 = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_background(slide4)
add_header(slide4, "Collaborative Multi-Agent Architecture: 3 Specialist Engineers", "AI AGENT ROSTER")

create_card(slide4, Inches(0.8), Inches(1.9), Inches(3.6), Inches(5.0),
    "Dr. Patch (Bug Intelligence)",
    [
        "Role: Software Debugging Specialist.",
        "Focus: Syntax errors, logic flaws, ZeroDivisionError, null reference guards, and type errors.",
        "Investigation Method: Analyzes variable lifecycles, execution flow, and drafts minimal surgical code patches.",
        "Interactive Consultation: Engineers can chat with Dr. Patch for targeted traceback diagnosis."
    ],
    "DEFECT DIAGNOSIS & REPAIR",
    RGBColor(56, 189, 248)
)

create_card(slide4, Inches(4.8), Inches(1.9), Inches(3.6), Inches(5.0),
    "Nova (RAM & Performance)",
    [
        "Role: Memory & Performance Engineer.",
        "Focus: Heap allocations, O(N²) nested loops, unclosed file descriptors, and resource bloat.",
        "Optimization Strategy: Refactors nested loops into O(1) hash maps and lazy generator pipelines.",
        "Footprint Reduction: Eliminates memory leak risks and curbs server RAM spikes."
    ],
    "RAM & SPEED PROFILING",
    RGBColor(52, 211, 153)
)

create_card(slide4, Inches(8.8), Inches(1.9), Inches(3.6), Inches(5.0),
    "Aegis (Security & Architecture)",
    [
        "Role: Senior Architect & Security Auditor.",
        "Focus: OWASP Top 10 vulnerabilities (SQL injection, command execution, hardcoded API secrets).",
        "Architecture Health: Audits cross-module coupling, circular imports, and dead code blocks.",
        "Remediation: Generates parameterized queries and secure environment-variable loaders."
    ],
    "SECURITY & MODULARITY",
    RGBColor(168, 85, 247)
)

# ==========================================
# SLIDE 5: GOOGLE GEMINI LLM ENGINE (UPDATED TO USER PLAN)
# ==========================================
slide5 = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_background(slide5)
add_header(slide5, "Google Gemini LLM Engine: Multi-Pass Code Review & Reasoning", "CORE AI ENGINE")

create_card(slide5, Inches(0.8), Inches(1.9), Inches(5.6), Inches(5.0),
    "Google Gemini Multi-Pass Intelligence",
    [
        "Primary AI Engine: Powered by Google Gemini Flash-Lite / Flash LLM models.",
        "Pass 1 — Deep Code Review: Comprehensive inspection of logic flow, variable scopes, edge cases, and cross-file dependencies.",
        "Pass 2 — Root-Cause Deduction: Rigorous investigation explaining the exact trigger condition, state mutation, and runtime failure.",
        "Pass 3 — Surgical Patch Synthesis: Generates token-efficient, minimal line diffs without truncating large files.",
        "Multi-Agent Prompt Routing: Dispatches specialized prompts for Dr. Patch, Nova, and Aegis based on engineering domain.",
        "Sandboxed Verification Feedback Loop: Every LLM-suggested patch is dynamically executed and validated before presentation."
    ],
    "DEEP REASONING & ACCURACY",
    PRIMARY_ACCENT
)

if os.path.exists(IMG_DIFF):
    slide5.shapes.add_picture(IMG_DIFF, Inches(6.8), Inches(1.9), width=Inches(5.7))

# ==========================================
# SLIDE 6: SANDBOXED VALIDATION & SAFETY NET
# ==========================================
slide6 = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_background(slide6)
add_header(slide6, "Sandboxed Safety Net: 0% Regression Risk Guarantee", "SAFETY & VERIFICATION")

create_card(slide6, Inches(0.8), Inches(1.9), Inches(3.6), Inches(5.0),
    "1. Isolated Subprocesses",
    [
        "Every proposed patch is tested in an ephemeral virtual sandbox.",
        "Zero modifications touch original files prior to explicit engineer approval.",
        "Strict timeouts and memory bounds prevent infinite loops or memory bombs."
    ],
    "CONTAINERIZED RUNTIME",
    PRIMARY_ACCENT
)

create_card(slide6, Inches(4.8), Inches(1.9), Inches(3.6), Inches(5.0),
    "2. Automated Validation",
    [
        "Validates syntax compilation across Python, JavaScript, Java, and HTML.",
        "Executes test suites automatically to confirm defect resolution.",
        "Confirms that all regression tests pass cleanly with zero new errors."
    ],
    "REGRESSION TEST SUITE",
    SECONDARY_ACCENT
)

create_card(slide6, Inches(8.8), Inches(1.9), Inches(3.6), Inches(5.0),
    "3. Reversible Rollback",
    [
        "Colorized side-by-side Git diff viewer highlights exact code changes.",
        "Timestamped change history tracks every accepted, rejected, or reverted patch.",
        "Instant one-click rollback restores original file versions immediately."
    ],
    "HUMAN-IN-THE-LOOP CONTROL",
    PURPLE_ACCENT
)

# ==========================================
# SLIDE 7: REAL-TIME REPOSITORY TELEMETRY & RAM PROFILING
# ==========================================
slide7 = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_background(slide7)
add_header(slide7, "Comprehensive Repository Health & RAM Telemetry", "DEEP ANALYTICS")

if os.path.exists(IMG_ANALYSIS):
    slide7.shapes.add_picture(IMG_ANALYSIS, Inches(0.8), Inches(1.9), width=Inches(5.8))

create_card(slide7, Inches(7.0), Inches(1.9), Inches(5.5), Inches(5.0),
    "Telemetry Metrics Discovered",
    [
        "Source File Discovery: Recursively maps file trees while filtering vendor caches (node_modules, .git, venv).",
        "RAM Profile Telemetry: Measures memory overhead, heap allocations, and peak resource consumption.",
        "Multi-Tier Issue Categorization: Segregates findings into Syntax Errors, Logic Flaws, RAM Leaks, and Security.",
        "Dependency Relationship Mapping: Tracks cross-file imports and third-party package dependencies.",
        "Comprehensive Audit Reports: One-click export of formal HTML and JSON audit documentation for engineering teams."
    ],
    "QUANTIFIABLE ENGINEERING METRICS",
    SECONDARY_ACCENT
)

# ==========================================
# SLIDE 8: SECURITY AUDITING & EMPIRICAL ACCURACY BENCHMARKS
# ==========================================
slide8 = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_background(slide8)
add_header(slide8, "Aegis Security Engine & Empirical Accuracy Benchmarks", "ACCURACY & HARDENING")

create_card(slide8, Inches(0.8), Inches(1.9), Inches(5.5), Inches(5.0),
    "Accuracy Benchmarks vs Naive AI",
    [
        "Empirical Benchmark Audit (Attendance & Hospital Test Suites):",
        "  • Naive AI Scanners: 40% False Positive / Hallucination Rate (e.g. hallucinating missing button types or phantom DOM XSS).",
        "  • AutoPatch Gemini Engine: Rigorous contextual grounding delivers verified precision and zero fabricated defects.",
        "Critical Defects Caught: Unhandled JSON.parse on localStorage (causing full app crash) and timestamp ID collisions.",
        "Proactive Vulnerability Hardening: Automatically replaces hardcoded secret tokens with secure os.environ loaders.",
        "OWASP Compliance: Prevents SQL injections, shell command executions, and unsafe deserialization."
    ],
    "SCIENTIFIC VERIFICATION",
    RGBColor(239, 68, 68)
)

if os.path.exists(IMG_SECURITY):
    slide8.shapes.add_picture(IMG_SECURITY, Inches(6.8), Inches(1.9), width=Inches(5.7))

# ==========================================
# SLIDE 9: 24/7 PRODUCTION CLOUD ARCHITECTURE
# ==========================================
slide9 = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_background(slide9)
add_header(slide9, "Production Deployment: High Availability & 24/7 Scalability", "CLOUD INFRASTRUCTURE")

create_card(slide9, Inches(0.8), Inches(1.9), Inches(3.6), Inches(5.0),
    "Frontend on Firebase CDN",
    [
        "Hosted on Google Firebase Hosting (autopatch-ai-2026.web.app).",
        "Modern React 18 + Vite + Tailwind CSS + Lucide Icons.",
        "Global CDN edge caching with SSL/TLS encryption for sub-second page loads worldwide.",
        "Zero local server dependency — accessible from any browser."
    ],
    "GLOBAL FAST DELIVERY",
    PRIMARY_ACCENT
)

create_card(slide9, Inches(4.8), Inches(1.9), Inches(3.6), Inches(5.0),
    "Backend on Render Cloud",
    [
        "Hosted on Render Managed Cloud (autopatch-a7em.onrender.com).",
        "FastAPI 2.0.0 asynchronous microservices powered by Uvicorn.",
        "Runs 24/7 autonomously with automated health checks, restarts, and HTTPS.",
        "Universal CORS configuration guarantees zero browser preflight blocks."
    ],
    "ALWAYS-ON CONTAINER",
    SECONDARY_ACCENT
)

create_card(slide9, Inches(8.8), Inches(1.9), Inches(3.6), Inches(5.0),
    "Automated CI/CD Pipeline",
    [
        "Synchronized GitHub Repository: Bhimannapng/AutoPatch (branch: main).",
        "Automated continuous deployment: Every git push automatically triggers a fresh container build on Render.",
        "Automated Firebase Hosting releases ensure frontend and backend remain perfectly in sync."
    ],
    "CONTINUOUS DELIVERY",
    PURPLE_ACCENT
)

# ==========================================
# SLIDE 10: CONCLUSION & FUTURE ROADMAP
# ==========================================
slide10 = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_background(slide10)
add_header(slide10, "Conclusion & Future Roadmap: The Future of Autonomous Coding", "SUMMARY & NEXT STEPS")

create_card(slide10, Inches(0.8), Inches(1.9), Inches(5.6), Inches(5.0),
    "Project Achievements & Impact",
    [
        "Solved Core Engineering Pain Points: Autonomous detection and repair of bugs, memory leaks, and security flaws.",
        "Production-Grade Cloud System: Fully deployed, highly available 24/7 architecture requiring zero local server setup.",
        "Google Gemini LLM Intelligence: Multi-pass code review with deep root-cause explanation and surgical patch synthesis.",
        "Guaranteed Safety Net: Ephemeral sandboxed verification ensures 0% regression risk before code review.",
        "Tested & Verified: Comprehensive automated test suite passing 100% in 0.55s."
    ],
    "KEY ACCOMPLISHMENTS",
    PRIMARY_ACCENT
)

create_card(slide10, Inches(6.8), Inches(1.9), Inches(5.7), Inches(5.0),
    "Future Roadmap (AutoPatch 3.0)",
    [
        "Autonomous GitHub PR Bot: GitHub Action that reviews PRs and proposes verified patch branches automatically.",
        "IDE Integrations: Native VS Code and JetBrains extensions with real-time Dr. Patch, Nova, and Aegis agent chat.",
        "Distributed Sandbox Clusters: Multi-container Kubernetes workers for scanning enterprise monorepos.",
        "Autonomous Test Generation: Generates complete pytest/jest unit test suites for untested legacy codebases."
    ],
    "ROADMAP & NEXT HORIZONS",
    SECONDARY_ACCENT
)

# Save presentation
output_pptx = "/Users/bhimanna/Desktop/AutoPatch/AutoPatch_Presentation.pptx"
prs.save(output_pptx)
print(f"Presentation saved successfully to: {output_pptx}")
