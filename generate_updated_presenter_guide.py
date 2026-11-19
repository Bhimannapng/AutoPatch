import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

PDF_PATH = "/Users/bhimanna/Desktop/AutoPatch/AutoPatch_Presenter_Guide.pdf"

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#64748b"))
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 750, "AutoPatch 2.0 — Presenter's Pitch & Defense Guide")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(54, 744, 558, 744)
        
        # Footer
        text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 36, text)
        self.drawString(54, 36, "CONFIDENTIAL — AutoPatch Presentation Defense Materials")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 48, 558, 48)
        self.restoreState()

def build_pdf():
    doc = SimpleDocTemplate(
        PDF_PATH,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()
    
    # Custom Palette
    c_primary = colors.HexColor("#0f172a") # Dark Slate
    c_blue = colors.HexColor("#0284c7")    # Sky Blue
    c_green = colors.HexColor("#059669")   # Emerald Green
    c_muted = colors.HexColor("#475569")   # Muted body text

    # Custom Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=c_primary,
        spaceAfter=6
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=c_blue,
        spaceAfter=15
    )
    
    h1_style = ParagraphStyle(
        'Heading1Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=18,
        textColor=c_primary,
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )
    
    h2_style = ParagraphStyle(
        'Heading2Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=c_blue,
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'BodyCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=c_muted,
        spaceAfter=6
    )
    
    bullet_style = ParagraphStyle(
        'BulletCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=c_muted,
        leftIndent=14,
        spaceAfter=4
    )

    script_style = ParagraphStyle(
        'ScriptCustom',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=2,
        spaceAfter=4
    )

    badge_style = ParagraphStyle(
        'BadgeCustom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=10,
        textColor=colors.HexColor("#0369a1")
    )

    story = []

    # ==========================================
    # COVER / HEADER
    # ==========================================
    story.append(Paragraph("AutoPatch 2.0 — Presenter's Pitch & Defense Guide", title_style))
    story.append(Paragraph("Comprehensive Slide-by-Slide Script, Explanations, Q&A Defense & Live Demo Playbook", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_blue, spaceBefore=4, spaceAfter=14))

    # Meta Overview Box
    meta_data = [
        [
            Paragraph("<b>Author / Presenter:</b> Bhimanna (bhimanna2006@gmail.com)", body_style),
            Paragraph("<b>Target Presentation Time:</b> 10 – 12 Minutes", body_style)
        ],
        [
            Paragraph("<b>Live Demo URL:</b> https://autopatch-ai-2026.web.app", body_style),
            Paragraph("<b>Cloud Backend:</b> Render Managed 24/7 (autopatch-a7em.onrender.com)", body_style)
        ],
        [
            Paragraph("<b>Slide Deck File:</b> AutoPatch_Presentation.pptx (10 Slides)", body_style),
            Paragraph("<b>GitHub:</b> github.com/Bhimannapng/AutoPatch", body_style)
        ]
    ]
    meta_table = Table(meta_data, colWidths=[250, 250])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 14))

    # Executive Overview
    story.append(Paragraph("Executive Presentation Strategy", h1_style))
    story.append(Paragraph(
        "AutoPatch 2.0 is designed to impress both software engineering practitioners and academic evaluators. "
        "The core theme of your presentation is <b>deep LLM reasoning with automated sandboxed verification</b>. "
        "Do not present AutoPatch as a generic chatbot; present it as an <b>end-to-end autonomous engineering platform</b> "
        "powered by the Google Gemini LLM Engine with multi-pass code review, deep root-cause explanation, and isolated regression test gates.",
        body_style
    ))
    story.append(Spacer(1, 10))

    # Timing breakdown table
    timing_data = [
        [Paragraph("<b>Section</b>", badge_style), Paragraph("<b>Slides</b>", badge_style), Paragraph("<b>Allocated Time</b>", badge_style), Paragraph("<b>Goal</b>", badge_style)],
        [Paragraph("1. Hook & Problem", body_style), Paragraph("Slides 1 – 2", body_style), Paragraph("2 Minutes", body_style), Paragraph("Establish why manual debugging and memory bloat waste 40% of developer cycles.", body_style)],
        [Paragraph("2. Solution & 3 Agents", body_style), Paragraph("Slides 3 – 4", body_style), Paragraph("3 Minutes", body_style), Paragraph("Introduce Dr. Patch, Nova, and Aegis and their specialized engineering domains.", body_style)],
        [Paragraph("3. Core AI Engine & Safety", body_style), Paragraph("Slides 5 – 6", body_style), Paragraph("3 Minutes", body_style), Paragraph("Explain the Google Gemini LLM Engine and Sandboxed Regression Safety Net.", body_style)],
        [Paragraph("4. Telemetry, Security & Benchmarks", body_style), Paragraph("Slides 7 – 9", body_style), Paragraph("2.5 Minutes", body_style), Paragraph("Showcase real RAM telemetry, 40% hallucination benchmark audit, and 24/7 cloud infra.", body_style)],
        [Paragraph("5. Roadmap & Q&A", body_style), Paragraph("Slide 10 + Demo", body_style), Paragraph("2 Minutes", body_style), Paragraph("Deliver a punchy conclusion and transition seamlessly into live demo / Q&A.", body_style)],
    ]
    t_table = Table(timing_data, colWidths=[100, 70, 80, 250])
    t_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
    ]))
    story.append(t_table)
    story.append(Spacer(1, 15))

    # ==========================================
    # DETAILED SLIDE-BY-SLIDE GUIDE
    # ==========================================
    story.append(PageBreak())

    slides_info = [
        {
            "num": 1,
            "title": "Title Slide — AutoPatch 2.0 Overview",
            "time": "1 Minute",
            "objective": "Introduce yourself, capture attention with the project name, and establish technical authority.",
            "what_to_say": (
                "\"Good morning / afternoon everyone. My name is Bhimanna, and today I am excited to present AutoPatch 2.0: "
                "an Autonomous AI Project Intelligence, Bug Detection, Root-Cause Investigation, Code Repair, and RAM Optimization System for INNOVEDGE Hackathon 2026. "
                "In modern software development, teams spend countless hours fighting silent memory leaks, regression bugs, and architectural decay. "
                "AutoPatch was built to solve this by creating an autonomous software engineering intelligence platform that not only detects defects "
                "across entire codebases, but scientifically investigates their root causes and proposes mathematically verified, regression-free patches. "
                "Our platform is fully deployed and accessible live today at autopatch-ai-2026.web.app.\""
            ),
            "key_points": [
                "Mention your developer details and production version 2.0.0.",
                "Emphasize that this is not just code snippet checking, but full repository-level software intelligence.",
                "Highlight the live URL to signal that this is an operating cloud system."
            ],
            "anticipated_q": "What makes this different from GitHub Copilot or ChatGPT?",
            "winning_answer": (
                "\"Copilot and ChatGPT operate on isolated code snippets without repository context or verification gates. "
                "AutoPatch ingests entire multi-file project archives, tracks cross-module call graphs, performs real RAM profiling with tracemalloc, "
                "and validates proposed fixes in an automated sandbox before presenting unified diffs to the engineer.\""
            )
        },
        {
            "num": 2,
            "title": "The Problem — Why Traditional Debugging Fails Modern Teams",
            "time": "1.5 Minutes",
            "objective": "Paint a clear, relatable picture of developer pain points: time sink, memory bloat, and regression fear.",
            "what_to_say": (
                "\"To understand why AutoPatch is necessary, let's look at the reality of modern software engineering. "
                "Industry studies show that developers spend over 40% of their working hours reproducing bugs, reading stack traces, and fixing issues. "
                "Second, silent performance degradations—such as quadratic O(N²) loops and unclosed resource handles—slip completely past standard unit tests, "
                "gradually leaking RAM in cloud servers until catastrophic memory spikes occur. "
                "Finally, when engineers rush to push emergency hotfixes, they often introduce secondary regression bugs because they lack an automated "
                "sandbox to verify that their patch didn't break existing functionality. This creates a vicious cycle of firefighting.\""
            ),
            "key_points": [
                "40%+ engineer time lost to manual bug hunting and context switching.",
                "Silent memory bloat and performance bottlenecks that bypass unit tests.",
                "Fear of regression: fixing one function accidentally breaks another."
            ],
            "anticipated_q": "Why can't linters like Flake8 or SonarQube solve this?",
            "winning_answer": (
                "\"Static linters check syntax conventions and surface warnings, but they cannot execute code, profile actual RAM allocations, "
                "or generate contextual code repair patches. AutoPatch goes beyond warnings: it conducts root-cause investigations and writes the fix.\""
            )
        },
        {
            "num": 3,
            "title": "The AutoPatch Solution — Full-Lifecycle Autonomous Code Repair",
            "time": "1.5 Minutes",
            "objective": "Introduce the platform's core solution pillars and direct the audience's gaze to the live UI dashboard.",
            "what_to_say": (
                "\"AutoPatch 2.0 replaces this broken cycle with a comprehensive, autonomous engineering pipeline. "
                "Developers can upload any repository as a ZIP archive, connect a public GitHub repository, or paste code directly. "
                "AutoPatch then analyzes the entire project structure and assigns the work to three specialized AI engineering agents. "
                "The system doesn't merely point out line numbers; it conducts a root-cause investigation, explaining the exact scientific reason for the issue. "
                "Then, it generates unified Git diffs and runs automated sandboxed test suites to verify that the repair is 100% sound. "
                "As you can see on the right, our dashboard provides engineers with clear metrics, agent findings, and interactive patch reviews.\""
            ),
            "key_points": [
                "Multi-channel ingestion: ZIP archives, GitHub Git cloning, or raw source folders.",
                "Tri-specialist agent team working synchronously.",
                "Root-cause explanation paired with actionable unified diffs."
            ],
            "anticipated_q": "How does AutoPatch clone or ingest private repositories?",
            "winning_answer": (
                "\"AutoPatch supports public GitHub repos, token-authenticated private clones, and direct ZIP uploads. "
                "All archives are processed with strict path-traversal safeguards preventing directory escapes.\""
            )
        },
        {
            "num": 4,
            "title": "The 3 Autonomous AI Specialist Agents",
            "time": "2 Minutes",
            "objective": "Detail the division of labor among the three AI agents: Dr. Patch, Nova, and Aegis.",
            "what_to_say": (
                "\"Rather than relying on a single general-purpose AI prompt, AutoPatch employs a multi-agent cooperative architecture. "
                "First is Dr. Patch, our Software Debugging Specialist. Dr. Patch analyzes syntax errors, division by zero, type mismatches, and null pointer guards. "
                "Second is Nova, our RAM & Performance Engineer. Nova profiles memory consumption using Python tracemalloc telemetry, identifies algorithmic bloat, "
                "and transforms inefficient quadratic loops into O(1) hash map operations to achieve substantial peak RAM reductions. "
                "Third is Aegis, our Senior Architect & Security Auditor. Aegis scans for OWASP vulnerabilities, exposed API tokens, and circular imports, "
                "assigning a Modularity Score and automatically patching hardcoded credentials with secure environment loaders. "
                "Engineers can chat directly with any of these three specialists to ask deep technical questions about their project.\""
            ),
            "key_points": [
                "Dr. Patch: Bug detection, logical flaws, syntax repairs.",
                "Nova: Memory leak detection, complexity optimization (O(N²) to O(1)), RAM profiling.",
                "Aegis: OWASP security auditing, API key protection, architectural decoupling."
            ],
            "anticipated_q": "Do these agents run sequentially or independently?",
            "winning_answer": (
                "\"They run across dedicated multi-analyzer pipelines in FastAPI. The AST and memory analyzers extract repository facts concurrently, "
                "and each agent receives structured JSON telemetry tailored to its specialized prompt engineering domain.\""
            )
        },
        {
            "num": 5,
            "title": "Google Gemini LLM Engine — Multi-Pass Code Review & Reasoning",
            "time": "1.5 Minutes",
            "objective": "Explain the core AI engine: Google Gemini multi-pass reasoning, root-cause investigation, and surgical patch generation.",
            "what_to_say": (
                "\"Now let's examine the intelligence engine powering AutoPatch: the Google Gemini LLM Engine. "
                "Rather than relying on simple one-shot prompts that hallucinate or truncate large codebases, AutoPatch implements an autonomous Multi-Pass LLM Review pipeline. "
                "In Pass 1, Gemini performs a deep semantic code review across your source files, understanding complete business logic, variable lifecycles, and cross-file dependencies. "
                "In Pass 2, the engine conducts root-cause deduction, explaining the exact execution state, mutation conditions, and triggers that cause the failure. "
                "In Pass 3, Gemini synthesizes a minimal, surgical patch and outputs token-efficient unified diffs without truncating large files. "
                "Every proposed fix is then immediately tested in an isolated runtime sandbox before presentation. "
                "This multi-pass architecture gives engineering teams the depth of a senior staff software engineer with the speed of an automated cloud pipeline.\""
            ),
            "key_points": [
                "Google Gemini Flash-Lite & Flash LLM Engine for deep multi-file contextual understanding.",
                "Multi-pass review architecture: Pass 1 (Deep Code Review), Pass 2 (Root Cause Investigation), Pass 3 (Surgical Patch Synthesis).",
                "Token-efficient JSON formatting avoids file truncation on large multi-file codebases.",
                "Integrated sandbox verification loop validates code integrity dynamically before presentation."
            ],
            "anticipated_q": "How do you prevent the LLM from hallucinating non-existent APIs or syntax errors?",
            "winning_answer": (
                "\"We ground Gemini with structured repository metadata and enforce a strict token-efficient JSON response schema. "
                "Crucially, before any patch is displayed to the engineer, our system compiles and executes the patched code in an ephemeral runtime sandbox. "
                "If the LLM generates invalid code or fails execution, the sandbox catches it immediately, ensuring 0% regression risk.\""
            )
        },
        {
            "num": 6,
            "title": "Sandboxed Safety Net — 0% Regression Risk Guarantee",
            "time": "1.5 Minutes",
            "objective": "Demonstrate the rigor and safety precautions built into AutoPatch before any patch is accepted.",
            "what_to_say": (
                "\"In enterprise environments, no engineer will accept an AI patch without rigorous proof. "
                "AutoPatch implements an automated Sandboxed Safety Net. "
                "When a patch is drafted, it is applied in an isolated ephemeral directory—the user's source code is completely untouched. "
                "The sandbox immediately executes automated unit test runners (such as PyTest) and syntax compilation checks against the patched code. "
                "We verify that the previously failing test now passes, AND that zero existing tests were broken. "
                "The developer is then presented with a colorized Git unified diff and can apply the patch with one click. "
                "If they ever change their mind, our change history manager allows an instant one-click rollback to restore the original file state.\""
            ),
            "key_points": [
                "Ephemeral sandbox execution: zero risk of repository corruption.",
                "Automated PyTest / syntax gates confirm regressions are prevented.",
                "One-click review and instantaneous rollback capabilities."
            ],
            "anticipated_q": "How does the sandbox prevent dangerous code execution (e.g. rm -rf or memory bombs)?",
            "winning_answer": (
                "\"The sandbox runs within isolated temporary environments with sub-process timeouts (2s limit), path restriction checks, and compile-only gates "
                "for script entry points. In cloud deployments, containers further enforce read-only system boundaries.\""
            )
        },
        {
            "num": 7,
            "title": "Comprehensive Repository Health & RAM Telemetry",
            "time": "1.5 Minutes",
            "objective": "Walk through the analytics and metrics captured during project scanning.",
            "what_to_say": (
                "\"AutoPatch provides engineering leaders with complete transparency into their software health. "
                "During project ingestion, our multi-analyzer decomposes every file in the directory tree, calculating source line density, "
                "cyclomatic complexity, and dependency imports across Python, JavaScript, TypeScript, and Java. "
                "Using Python's tracemalloc module, we capture real-time memory snapshots, plotting baseline RAM against peak usage to detect allocations that fail to release. "
                "Furthermore, our system calculates an Architectural Coupling Index to flag tightly coupled modules, and allows engineers to export "
                "a formal executive PDF report for sprint retrospectives and compliance audits.\""
            ),
            "key_points": [
                "Deep multi-language AST inspection: Python, JS, TS, Java, HTML, CSS.",
                "Real RAM profiling with tracemalloc telemetry.",
                "Formal PDF report generation for management and code reviews."
            ],
            "anticipated_q": "How accurate is the tracemalloc memory profiling in a production container?",
            "winning_answer": (
                "\"tracemalloc hooks directly into Python's memory allocator (PyMem_Malloc) to trace memory blocks with exact byte precision. "
                "This allows us to isolate specific function allocations and measure exact memory deltas between unoptimized and optimized code.\""
            )
        },
        {
            "num": 8,
            "title": "Aegis Security Engine & Empirical Accuracy Benchmarks",
            "time": "1.5 Minutes",
            "objective": "Detail security auditing and highlight AutoPatch's scientific accuracy benchmarks against naive AI tools.",
            "what_to_say": (
                "\"Security and reliability cannot be an afterthought in software development. "
                "The Aegis Security Engine continuously scans project trees for exposed credentials—such as Stripe live keys, AWS secrets, and database passwords. "
                "It also identifies critical OWASP Top 10 vulnerabilities, including unparameterized SQL statements, command injections, and unsafe eval() calls. "
                "Crucially, we put AutoPatch to the test against real-world benchmark codebases like our student attendance and hospital management test suites. "
                "Our empirical audit revealed that generic AI code scanners suffer from a staggering 40% False Positive / Hallucination Rate—hallucinating missing button attributes "
                "or claiming DOM XSS where textContent is safely used. In contrast, AutoPatch's grounded Gemini engine delivered verified precision, "
                "catching critical defects that naive tools completely missed, such as unhandled JSON.parse crashes on localStorage.\""
            ),
            "key_points": [
                "Detects hardcoded secrets, API tokens, and OWASP Top 10 vulnerabilities.",
                "Empirical Accuracy Audit: 40% hallucination rate in generic AI scanners vs. AutoPatch verified precision.",
                "Caught critical unhandled JSON.parse localStorage crashes that bring down production web applications."
            ],
            "anticipated_q": "Does Aegis catch zero-day vulnerabilities?",
            "winning_answer": (
                "\"Aegis focuses on fundamental architectural security flaws, OWASP vulnerabilities, and credential leaks. "
                "When paired with the Gemini LLM engine, it can also detect contextual authorization bypasses and logic exploits.\""
            )
        },
        {
            "num": 9,
            "title": "Production Deployment — 24/7 Cloud Architecture",
            "time": "1.5 Minutes",
            "objective": "Prove that AutoPatch is not just a prototype, but an active, globally deployed cloud system.",
            "what_to_say": (
                "\"AutoPatch 2.0 is fully operational in production today. "
                "Our frontend is built with React 18, Vite, and Tailwind CSS, hosted globally on Google Firebase Hosting at autopatch-ai-2026.web.app. "
                "Firebase's global CDN delivers sub-second page loads with automatic SSL/TLS encryption. "
                "Our backend microservices are built on FastAPI 2.0 with asynchronous Uvicorn workers, hosted on Render Managed Cloud at autopatch-a7em.onrender.com. "
                "It runs 24/7 autonomously with automated health monitors and zero dependency on any local machine. "
                "Our automated CI/CD deployment pipeline allows us to push updates to GitHub, where Render automatically rebuilds and redeploys the service with zero downtime.\""
            ),
            "key_points": [
                "Frontend: Google Firebase Hosting (autopatch-ai-2026.web.app) with global edge caching.",
                "Backend: Render Cloud (autopatch-a7em.onrender.com) with FastAPI 2.0 running 24/7.",
                "Continuous Deployment: git push triggers automated zero-downtime rolling rebuilds."
            ],
            "anticipated_q": "How does AutoPatch scale if hundreds of users upload large repositories at the same time?",
            "winning_answer": (
                "\"Render and FastAPI support horizontal autoscaling and asynchronous worker concurrency. For enterprise scale, repository analysis "
                "tasks can be offloaded to Celery background workers backed by Redis, and containerized sandboxes can be dispatched across Kubernetes pods.\""
            )
        },
        {
            "num": 10,
            "title": "Conclusion & Future Roadmap — The Future of Autonomous Coding",
            "time": "1.5 Minutes",
            "objective": "Summarize key achievements, outline the future vision, and smoothly transition into live demo.",
            "what_to_say": (
                "\"To conclude, AutoPatch 2.0 bridges the gap between passive code linting and active software engineering. "
                "By combining multi-agent specialization, Google Gemini LLM reasoning, real RAM profiling, and a sandboxed safety net, "
                "we eliminate the tedious hours developers spend debugging and optimizing code. "
                "Looking ahead to AutoPatch 3.0, we plan to release an autonomous GitHub PR Review Bot that comments patches directly on pull requests, "
                "expand patch synthesis to Go, Rust, and C++, and introduce autonomous unit test generation for untested legacy codebases. "
                "Thank you for your time, and I would now love to walk you through a live demonstration of AutoPatch in action.\""
            ),
            "key_points": [
                "Summary: End-to-end autonomous analysis, root-cause repair, and RAM optimization.",
                "Future: GitHub Action PR bot, multi-language expansion (Rust/Go), auto-generated test suites.",
                "Transition cleanly into live demo and audience Q&A."
            ],
            "anticipated_q": "What is the biggest technical challenge you overcame while building this?",
            "winning_answer": (
                "\"The biggest challenge was creating a unified patch composition engine that could apply multiple AST modifications—such as adding "
                "error handling, optimizing a loop, and parameterizing a query—into a single file without creating conflicting line offsets or corrupting syntax trees.\""
            )
        }
    ]

    for s in slides_info:
        # Slide Box Header
        card_content = []
        
        # Slide Title & Header Info
        header_text = f"<b>SLIDE {s['num']}: {s['title'].upper()}</b>"
        card_content.append([
            Paragraph(header_text, h1_style),
            Paragraph(f"<b>Target Speaking Time:</b> {s['time']}", badge_style)
        ])
        
        h_table = Table(card_content, colWidths=[360, 140])
        h_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('BOX', (0, 0), (-1, -1), 1, c_blue),
        ]))
        story.append(h_table)
        story.append(Spacer(1, 8))

        # Slide Objective
        story.append(Paragraph("<b>Slide Goal:</b> " + s['objective'], body_style))
        story.append(Spacer(1, 6))

        # What to Say (Word-for-Word Script)
        story.append(Paragraph("Exact Presenter Script (What to say):", h2_style))
        
        script_box = [[Paragraph(s['what_to_say'], script_style)]]
        s_table = Table(script_box, colWidths=[500])
        s_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ]))
        story.append(s_table)
        story.append(Spacer(1, 8))

        # Key Points to Emphasize
        story.append(Paragraph("Key Points & Technical Highlights:", h2_style))
        for kp in s['key_points']:
            story.append(Paragraph(f"• {kp}", bullet_style))
        story.append(Spacer(1, 8))

        # Defense Q&A
        story.append(Paragraph("Anticipated Tough Question & Winning Answer:", h2_style))
        qa_data = [
            [Paragraph(f"<b>Judge / Evaluator Question:</b> <i>\"{s['anticipated_q']}\"</i>", body_style)],
            [Paragraph(f"<b>Recommended Strong Defense:</b> {s['winning_answer']}", body_style)]
        ]
        qa_table = Table(qa_data, colWidths=[500])
        qa_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#fef2f2")),
            ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor("#f0fdf4")),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ]))
        story.append(qa_table)
        story.append(Spacer(1, 14))

        if s['num'] in [2, 4, 6, 8]:
            story.append(PageBreak())

    # ==========================================
    # LIVE DEMO PLAYBOOK
    # ==========================================
    story.append(PageBreak())
    story.append(Paragraph("Live Demonstration Playbook (Step-by-Step)", h1_style))
    story.append(Paragraph(
        "Following your slide deck, delivering a confident live demonstration will solidify your high score. "
        "Here is the exact 4-step sequence to demonstrate on the live site <b>https://autopatch-ai-2026.web.app</b>:",
        body_style
    ))
    story.append(Spacer(1, 8))

    demo_steps = [
        ("Step 1: Open Live URL & Show System Health", 
         "Open https://autopatch-ai-2026.web.app in your browser. Point out the 'Connected' status pill in the top header, which connects to the 24/7 Render API. Show that the 3 agents (Dr. Patch, Nova, Aegis) are ready."),
        ("Step 2: Upload Project ZIP or Load Sample", 
         "Click on 'Upload ZIP' and choose a project archive (or click 'Untested Demo E-commerce' / paste code). Point out the autonomous multi-agent analysis executing smoothly in under 4 seconds."),
        ("Step 3: Walk Through Multi-Agent Findings", 
         "Show Dr. Patch's bug diagnosis with root cause explanation. Switch to the RAM tab to show Nova's memory complexity profile. Switch to Security to show Aegis's credential vulnerability audit."),
        ("Step 4: Inspect Unified Diff & Sandbox Verification", 
         "Click 'Review Patch'. Highlight the side-by-side colorized diff showing the exact fix. Point out the 'Sandbox Verified' green badge and click 'Apply Patch'. Show the file update reflected in Change History!")
    ]

    for title, desc in demo_steps:
        story.append(Paragraph(f"<b>{title}</b>", h2_style))
        story.append(Paragraph(desc, bullet_style))
        story.append(Spacer(1, 6))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Presenter guide PDF successfully created at: {PDF_PATH}")

if __name__ == "__main__":
    build_pdf()
