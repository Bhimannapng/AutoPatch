import os
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from dotenv import load_dotenv

load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from schemas import (
    AgentInfo,
    AgentChatMessage,
    AgentChatRequest,
    AgentChatResponse,
    ProjectAnalysisSummary,
    BugReport,
    OptimizationFinding,
    SecurityFinding,
    ArchitectureFinding
)

# Agent Definitions
AGENTS_REGISTRY: Dict[str, Dict[str, Any]] = {
    "agent_bugs": {
        "id": "agent_bugs",
        "name": "Dr. Patch (Bug Intelligence)",
        "role": "Software Debugging Specialist",
        "avatar": "Bug",
        "specialization": "Root-Cause Analysis, Syntax & Semantic Bug Detection, Logic Flaws, and Targeted Patching",
        "system_persona": (
            "You are Dr. Patch, an elite Software Debugging and Code Intelligence Specialist. "
            "You specialize in deep root-cause analysis, syntax/semantic/logic errors, and verified code patching. "
            "Always reference exact file paths, line numbers, and trigger inputs from the provided project context. "
            "Never give vague or generic advice. Guide the developer with clear, surgical code corrections."
        )
    },
    "agent_ram": {
        "id": "agent_ram",
        "name": "Nova (RAM & Performance)",
        "role": "Memory & Performance Engineer",
        "avatar": "Cpu",
        "specialization": "RAM Profiling, Memory Leak Elimination, O(N²) Loop Optimization, and Redundant Code Removal",
        "system_persona": (
            "You are Nova, a high-performance Software and Memory Optimization Engineer. "
            "You specialize in RAM efficiency, memory leak detection, algorithmic complexity, CPU bottlenecks, and dead-code elimination. "
            "Distinguish clearly between statically suspected optimizations and measured sandbox profiling. "
            "Explain exactly why an operation consumes excessive heap memory or CPU cycles and suggest optimal structures (e.g. generators, hash maps, sets)."
        )
    },
    "agent_arch": {
        "id": "agent_arch",
        "name": "Aegis (Architecture & Security)",
        "role": "Senior Architect & Security Auditor",
        "avatar": "ShieldAlert",
        "specialization": "Project Modularity, Dependency Health, Cross-Module Coupling, and Vulnerability Hardening",
        "system_persona": (
            "You are Aegis, a Senior Software Architect and Cybersecurity Specialist. "
            "You review system architecture, module boundaries, API contract consistency, and OWASP security vulnerabilities. "
            "Identify hardcoded credentials, SQL/Command injections, unsafe dynamic evaluation, and broken architectural patterns. "
            "Focus on clean architecture, defensive programming, and maintainable software design."
        )
    },
    "orchestrator": {
        "id": "orchestrator",
        "name": "AutoPatch Lead Orchestrator",
        "role": "Autonomous Software Engineering Lead",
        "avatar": "Bot",
        "specialization": "Holistic Project Coordination, Multi-Agent Synthesis, and Technical Leadership",
        "system_persona": (
            "You are the AutoPatch Lead Orchestrator, coordinating Dr. Patch (Bugs), Nova (RAM/Performance), and Aegis (Architecture/Security). "
            "You synthesize project intelligence across all disciplines and route complex user requests to the appropriate specialist."
        )
    }
}

def get_agents_info_list(summary: Optional[ProjectAnalysisSummary] = None) -> List[AgentInfo]:
    """Returns the metadata and status cards for the 3 specialist agents + orchestrator."""
    bugs_count = len(summary.bugs) if summary else 0
    perf_count = len(summary.optimizations) if summary else 0
    sec_count = len(summary.security_findings) if summary else 0
    arch_count = len(summary.architecture_findings) if summary else 0

    return [
        AgentInfo(
            id="agent_bugs",
            name=AGENTS_REGISTRY["agent_bugs"]["name"],
            role=AGENTS_REGISTRY["agent_bugs"]["role"],
            avatar=AGENTS_REGISTRY["agent_bugs"]["avatar"],
            specialization=AGENTS_REGISTRY["agent_bugs"]["specialization"],
            status="Active" if summary else "Ready",
            key_findings_count=bugs_count,
            summary=f"Investigated {bugs_count} code defects with root-cause analysis and verified patches."
        ),
        AgentInfo(
            id="agent_ram",
            name=AGENTS_REGISTRY["agent_ram"]["name"],
            role=AGENTS_REGISTRY["agent_ram"]["role"],
            avatar=AGENTS_REGISTRY["agent_ram"]["avatar"],
            specialization=AGENTS_REGISTRY["agent_ram"]["specialization"],
            status="Active" if summary else "Ready",
            key_findings_count=perf_count,
            summary=f"Identified {perf_count} RAM and CPU optimization opportunities with complexity analysis."
        ),
        AgentInfo(
            id="agent_arch",
            name=AGENTS_REGISTRY["agent_arch"]["name"],
            role=AGENTS_REGISTRY["agent_arch"]["role"],
            avatar=AGENTS_REGISTRY["agent_arch"]["avatar"],
            specialization=AGENTS_REGISTRY["agent_arch"]["specialization"],
            status="Active" if summary else "Ready",
            key_findings_count=sec_count + arch_count,
            summary=f"Audited {sec_count} security risks and {arch_count} architectural coupling points."
        )
    ]

def build_targeted_agent_context(
    agent_id: str,
    user_message: str,
    summary: Optional[ProjectAnalysisSummary],
    files_dict: Dict[str, str]
) -> Tuple[str, List[str]]:
    """
    Builds a concise, token-efficient context window for the requested agent:
    Includes only project metadata, relevant findings, and referenced code snippets.
    Never sends thousands of irrelevant lines to the LLM.
    """
    if not summary:
        return "No project uploaded yet. The workspace is currently empty.", []

    context_lines = [
        f"=== PROJECT INTELLIGENCE SUMMARY ===",
        f"Project Name: {summary.project_name}",
        f"Project Type: {summary.project_type}",
        f"Languages: {', '.join(summary.detected_languages)}",
        f"Frameworks: {', '.join(summary.detected_frameworks)}",
        f"Total Source Files: {summary.capacity_metrics.relevant_source_files}",
        f"Total Code Lines: {summary.capacity_metrics.total_lines_of_code}",
        f"Entry Points: {', '.join(summary.entry_points) or 'None'}"
    ]

    referenced_files: List[str] = []

    # Inject domain-specific findings based on agent role
    if agent_id in ("agent_bugs", "orchestrator"):
        context_lines.append(f"\n--- DETECTED BUGS ({len(summary.bugs)}) ---")
        for b in summary.bugs[:8]:  # Top 8 most critical
            context_lines.append(
                f"- [{b.severity}] {b.title} in {b.file_path}:{b.line_start}\n"
                f"  Root Cause: {b.root_cause}\n"
                f"  Trigger: {b.trigger_input_or_state}"
            )
            if b.file_path not in referenced_files:
                referenced_files.append(b.file_path)

    if agent_id in ("agent_ram", "orchestrator"):
        context_lines.append(f"\n--- RAM & PERFORMANCE FINDINGS ({len(summary.optimizations)}) ---")
        for o in summary.optimizations[:8]:
            context_lines.append(
                f"- [{o.category} - {o.severity}] {o.title} in {o.file_path}:{o.line_start}\n"
                f"  Problem: {o.problem}\n"
                f"  Improvement: {o.suggested_improvement} (Expected: {o.expected_benefit})"
            )
            if o.file_path not in referenced_files:
                referenced_files.append(o.file_path)

    if agent_id in ("agent_arch", "orchestrator"):
        context_lines.append(f"\n--- SECURITY & ARCHITECTURE AUDIT ---")
        for s in summary.security_findings[:5]:
            context_lines.append(f"- [SECURITY - {s.severity}] {s.title} in {s.file_path}:{s.line_start}: {s.description}")
            if s.file_path not in referenced_files:
                referenced_files.append(s.file_path)
        for a in summary.architecture_findings[:5]:
            context_lines.append(f"- [ARCH - {a.category}] {a.title}: {a.description}")

    # Inject targeted source snippets for mentioned or top-priority files (max 200 lines total)
    context_lines.append(f"\n--- RELEVANT CODE CONTEXT ---")
    injected_count = 0
    for fpath in referenced_files[:3]:
        content = files_dict.get(fpath, "")
        if content:
            lines = content.splitlines()
            snippet = "\n".join(lines[:80])  # First 80 lines
            context_lines.append(f"\nFile: {fpath} (first {min(len(lines), 80)} lines):\n```\n{snippet}\n```")
            injected_count += 1

    return "\n".join(context_lines), referenced_files

def handle_agent_chat(
    req: AgentChatRequest,
    summary: Optional[ProjectAnalysisSummary],
    files_dict: Dict[str, str],
    api_key: Optional[str] = None
) -> AgentChatResponse:
    """
    Executes a chat request with the selected specialist agent using Google Gemini.
    Provides local deterministic fallback if no API key or network is unavailable.
    """
    target_id = req.agent_id if req.agent_id in AGENTS_REGISTRY else "orchestrator"
    agent_spec = AGENTS_REGISTRY[target_id]
    context_str, ref_files = build_targeted_agent_context(target_id, req.message, summary, files_dict)

    effective_key = api_key if api_key is not None else os.getenv("GEMINI_API_KEY")

    # If Gemini API key is configured, call Gemini
    if effective_key:
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=effective_key)
            prompt = (
                f"{agent_spec['system_persona']}\n\n"
                f"{context_str}\n\n"
                f"User Question: {req.message}\n\n"
                f"Answer concisely, referencing specific files, lines, and data from the project context above. "
                f"Do not guess. If code should be corrected or optimized, provide exact snippet examples."
            )

            # Try primary fast model, then fallback
            for model_name in ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]:
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            temperature=0.2,
                            max_output_tokens=1500
                        )
                    )
                    if response and response.text:
                        return AgentChatResponse(
                            agent_id=target_id,
                            agent_name=agent_spec["name"],
                            reply=response.text.strip(),
                            referenced_files=ref_files,
                            suggested_actions=["Review suggested patch", "Inspect code in editor"]
                        )
                except Exception:
                    continue

        except Exception:
            pass

    # Deterministic Local Fallback (Guarantees responsive answers even offline)
    fallback_reply = generate_deterministic_agent_reply(target_id, req.message, summary)
    return AgentChatResponse(
        agent_id=target_id,
        agent_name=agent_spec["name"],
        reply=fallback_reply,
        referenced_files=ref_files,
        suggested_actions=["View full report in Dashboard", "Run Sandboxed Tests"]
    )

def generate_deterministic_agent_reply(
    agent_id: str,
    user_message: str,
    summary: Optional[ProjectAnalysisSummary]
) -> str:
    """Generates accurate, context-grounded responses locally without external API."""
    if not summary:
        return "Please upload a project or paste code into the workspace first so I can inspect your project structure and dependencies."

    msg = user_message.lower()

    if agent_id == "agent_bugs":
        if not summary.bugs:
            return f"Great news! Dr. Patch found 0 critical syntax or semantic defects across {summary.capacity_metrics.relevant_source_files} files."
        top_bug = summary.bugs[0]
        return (
            f"**Dr. Patch Analysis**:\n\n"
            f"Found **{len(summary.bugs)} defects** in `{summary.project_name}`.\n\n"
            f"**Highest Priority Issue**: `{top_bug.title}` in `{top_bug.file_path}` (Line {top_bug.line_start}).\n"
            f"- **Root Cause**: {top_bug.root_cause}\n"
            f"- **Trigger Condition**: {top_bug.trigger_input_or_state}\n"
            f"- **Recommended Fix**: {top_bug.repair_summary}\n\n"
            f"You can review the unified diff and run sandbox verification in the **Patches** tab."
        )

    elif agent_id == "agent_ram":
        if not summary.optimizations:
            return f"Nova found no glaring memory leaks or nested quadratic loops in `{summary.project_name}`. Heap allocation appears stable."
        top_opt = summary.optimizations[0]
        return (
            f"**Nova (RAM & Performance Analysis)**:\n\n"
            f"Discovered **{len(summary.optimizations)} performance and memory optimization candidates**.\n\n"
            f"**Primary Bottleneck**: `{top_opt.title}` in `{top_opt.file_path}` (Line {getattr(top_opt, 'line_number', 1)}).\n"
            f"- **Category**: {top_opt.category} (Risk Level: {top_opt.risk_level})\n"
            f"- **Why Inefficient**: {top_opt.why_inefficient}\n"
            f"- **Actionable Improvement**: {getattr(top_opt, 'actionable_improvement', 'Refactor logic')}\n"
            f"- **Expected Benefit**: {getattr(top_opt, 'expected_outcome', 'Reduces CPU/RAM overhead')}"
        )

    elif agent_id == "agent_arch":
        sec_count = len(summary.security_findings)
        arch_count = len(summary.architecture_findings)
        sec_str = f"Found **{sec_count} security items**" if sec_count else "No high-risk secrets or SQL/command injections detected"
        arch_str = f"**{arch_count} architectural coupling notices**" if arch_count else "Modularity is well-organized"
        return (
            f"**Aegis (Architecture & Security Audit)**:\n\n"
            f"Project: `{summary.project_name}` ({summary.project_type})\n"
            f"- **Security Posture**: {sec_str}.\n"
            f"- **Structural Modularity**: {arch_str}.\n"
            f"- **Detected Ecosystem**: {', '.join(summary.detected_frameworks)} on {', '.join(summary.detected_languages)}."
        )

    else:
        return (
            f"**AutoPatch Lead Orchestrator**:\n\n"
            f"Project `{summary.project_name}` is fully analyzed across {summary.capacity_metrics.relevant_source_files} source files and {summary.capacity_metrics.total_lines_of_code} lines.\n"
            f"- **Bugs**: {len(summary.bugs)} defects identified.\n"
            f"- **Performance & RAM**: {len(summary.optimizations)} optimizations proposed.\n"
            f"- **Security & Architecture**: {len(summary.security_findings)} vulnerabilities & {len(summary.architecture_findings)} modularity notices.\n\n"
            f"Select **Dr. Patch**, **Nova**, or **Aegis** to drill down into any specific area."
        )
