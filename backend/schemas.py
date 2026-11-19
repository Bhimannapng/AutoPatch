from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class TestResult(BaseModel):
    name: str
    status: str  # "PASSED", "FAILED", "ERROR", "TIMEOUT"
    duration_ms: float = 0.0
    stdout: str = ""
    error_message: Optional[str] = None

class SandboxedValidation(BaseModel):
    before_passed: int = 0
    before_failed: int = 0
    before_tests: List[TestResult] = Field(default_factory=list)
    after_passed: int = 0
    after_failed: int = 0
    after_tests: List[TestResult] = Field(default_factory=list)
    verified: bool = False
    details: str = ""
    ram_usage_before_kb: Optional[float] = None
    ram_usage_after_kb: Optional[float] = None
    execution_time_ms: Optional[float] = None

class BugReport(BaseModel):
    id: str
    title: str
    file_path: str
    line_start: int
    line_end: int
    col_offset: int = 0
    end_col_offset: int = 0
    category: str
    severity: str  # "Critical", "High", "Medium", "Low"
    confidence: int  # 0 to 100
    description: str = ""
    root_cause: str
    trigger_input_or_state: str
    repair_summary: str = "Applied targeted AST transformation."
    original_code: str
    patched_code: str
    composed_code: Optional[str] = None
    diff: str
    validation: Optional[SandboxedValidation] = None
    status: str = "Needs Review"  # "Needs Review", "Accepted", "Rejected"
    review_notes: Optional[str] = None
    created_at: str

class FileNode(BaseModel):
    name: str
    path: str
    is_dir: bool
    size: int = 0
    children: Optional[List["FileNode"]] = None

class DependencyRelation(BaseModel):
    source_file: str
    target: str
    imported_symbols: List[str] = Field(default_factory=list)
    is_external: bool = False

class ProjectCapacityMetrics(BaseModel):
    total_archive_size_bytes: int = 0
    extracted_size_bytes: int = 0
    total_files_discovered: int = 0
    relevant_source_files: int = 0
    total_lines_of_code: int = 0
    files_analyzed: int = 0
    files_excluded: List[Dict[str, str]] = Field(default_factory=list)
    files_remaining: int = 0
    ram_consumed_mb: float = 0.0
    analysis_duration_ms: float = 0.0
    gemini_tokens_used: int = 0

class OptimizationFinding(BaseModel):
    id: str
    title: str
    file_path: str
    line_start: int
    line_end: Optional[int] = None
    category: str  # "RAM Optimisation", "CPU Optimisation", "Unused Code", "Memory Leak Risk", "Inefficient Loop"
    severity: str = "Medium"  # "Critical", "High", "Medium", "Low", "Informational"
    problem: str
    why_inefficient: str
    suggested_improvement: str
    expected_benefit: str
    is_measured: bool = False
    ram_before_kb: Optional[float] = None
    ram_after_kb: Optional[float] = None
    risk_level: str = "Low"  # "Low", "Medium", "High"

class SecurityFinding(BaseModel):
    id: str
    title: str
    file_path: str
    line_start: int
    line_end: int
    severity: str  # "Critical", "High", "Medium", "Low"
    confidence: str  # "High", "Medium", "Low"
    vulnerability_type: str  # "Hardcoded Secret", "SQL Injection", "Unsafe Eval", "Command Injection", "Insecure File Handling"
    description: str
    remediation: str

class ArchitectureFinding(BaseModel):
    id: str
    title: str
    category: str  # "Modularity", "Coupling", "Unused Module", "API Inconsistency", "Dependency Health"
    affected_files: List[str] = Field(default_factory=list)
    description: str
    recommendation: str

class ProjectAnalysisSummary(BaseModel):
    project_id: str = "proj-default"
    project_name: str
    project_type: str = "Software Project"
    detected_languages: List[str] = Field(default_factory=list)
    detected_frameworks: List[str] = Field(default_factory=list)
    entry_points: List[str] = Field(default_factory=list)
    file_tree: List[FileNode] = Field(default_factory=list)
    dependencies: List[DependencyRelation] = Field(default_factory=list)
    capacity_metrics: ProjectCapacityMetrics
    bugs: List[BugReport] = Field(default_factory=list)
    optimizations: List[OptimizationFinding] = Field(default_factory=list)
    security_findings: List[SecurityFinding] = Field(default_factory=list)
    architecture_findings: List[ArchitectureFinding] = Field(default_factory=list)

ProjectStructureReport = ProjectAnalysisSummary


class AgentInfo(BaseModel):
    id: str
    name: str
    role: str
    avatar: str
    specialization: str
    status: str = "Ready"
    key_findings_count: int = 0
    summary: str

class AgentChatMessage(BaseModel):
    role: str  # "user", "agent", "system"
    content: str
    timestamp: str
    agent_id: Optional[str] = None
    references: Optional[List[str]] = None

class AgentChatRequest(BaseModel):
    agent_id: str  # "agent_bugs", "agent_ram", "agent_arch", or "orchestrator"
    message: str
    conversation_history: Optional[List[AgentChatMessage]] = None

class AgentChatResponse(BaseModel):
    agent_id: str
    agent_name: str
    reply: str
    referenced_files: List[str] = Field(default_factory=list)
    suggested_actions: List[str] = Field(default_factory=list)

class GitRepoRequest(BaseModel):
    repo_url: str
    branch: Optional[str] = None
    auth_token: Optional[str] = None

class ProjectScanResponse(BaseModel):
    project_id: str
    project_name: str
    file_tree: List[FileNode]
    total_files: int
    total_lines: int
    bugs: List[BugReport]
    scan_duration_ms: float
    model_used: str = "Pure Python AST (Offline / Zero-LLM)"
    engine_mode: str = "AST"
    api_key_configured: bool = False
    optimizations_count: int = 0
    security_count: int = 0
    architecture_count: int = 0

class ChangeHistoryEntry(BaseModel):
    id: str
    bug_id: str
    bug_title: str
    file_path: str
    action: str  # "ACCEPTED", "REJECTED", "REVERTED"
    timestamp: str
    original_code: str
    patched_code: str
    composed_code: Optional[str] = None
    diff: str
    comment: Optional[str] = None

class ReviewActionRequest(BaseModel):
    bug_id: str
    action: str  # "ACCEPTED" or "REJECTED" or "REVERT"
    comment: Optional[str] = None

class EngineModeRequest(BaseModel):
    mode: str  # "AST" or "LLM" or "COMBINED" or "SANDBOX"
    api_key: Optional[str] = None

class ApiKeyRequest(BaseModel):
    api_key: str
