export interface TestResult {
  name: string;
  status: 'PASSED' | 'FAILED' | 'ERROR' | 'TIMEOUT';
  duration_ms: number;
  stdout: string;
  error_message?: string | null;
}

export interface SandboxedValidation {
  before_passed: number;
  before_failed: number;
  before_tests: TestResult[];
  after_passed: number;
  after_failed: number;
  after_tests: TestResult[];
  verified: boolean;
  details: string;
  ram_usage_before_kb?: number | null;
  ram_usage_after_kb?: number | null;
  execution_time_ms?: number | null;
}

export type EngineMode = 'AST' | 'LLM' | 'COMBINED' | 'SANDBOX';

export interface BugReport {
  id: string;
  title: string;
  file_path: string;
  line_start: number;
  line_end: number;
  col_offset?: number;
  end_col_offset?: number;
  category: string;
  severity: 'ERROR' | 'WARNING' | 'INFO' | 'Critical' | 'High' | 'Medium' | 'Low' | string;
  confidence: number;
  description?: string;
  root_cause: string;
  trigger_input_or_state: string;
  repair_summary?: string;
  original_code: string;
  patched_code: string;
  composed_code?: string;
  diff: string;
  validation?: SandboxedValidation | null;
  status: 'Needs Review' | 'Accepted' | 'Rejected';
  review_notes?: string | null;
  created_at: string;
}

export interface FileNode {
  name: string;
  path: string;
  is_dir: boolean;
  size: number;
  children?: FileNode[] | null;
}

export interface DependencyRelation {
  source_file: string;
  target: string;
  imported_symbols: string[];
  is_external: boolean;
}

export interface ProjectCapacityMetrics {
  total_archive_size_bytes: number;
  extracted_size_bytes: number;
  total_files_discovered: number;
  relevant_source_files: number;
  total_lines_of_code: number;
  files_analyzed: number;
  files_excluded: Array<{ file: string; reason: string }>;
  files_remaining: number;
  ram_consumed_mb: number;
  analysis_duration_ms: number;
  gemini_tokens_used: number;
}

export interface OptimizationFinding {
  id: string;
  title: string;
  file_path: string;
  line_start: number;
  line_end?: number | null;
  category: string;
  severity: 'Critical' | 'High' | 'Medium' | 'Low' | 'Informational' | string;
  problem: string;
  why_inefficient: string;
  suggested_improvement: string;
  expected_benefit: string;
  is_measured: boolean;
  ram_before_kb?: number | null;
  ram_after_kb?: number | null;
  risk_level: string;
}

export interface SecurityFinding {
  id: string;
  title: string;
  file_path: string;
  line_start: number;
  line_end: number;
  severity: 'Critical' | 'High' | 'Medium' | 'Low' | string;
  confidence: 'High' | 'Medium' | 'Low' | string;
  vulnerability_type: string;
  description: string;
  remediation: string;
}

export interface ArchitectureFinding {
  id: string;
  title: string;
  category: string;
  affected_files: string[];
  description: string;
  recommendation: string;
}

export interface ProjectAnalysisSummary {
  project_id: string;
  project_name: string;
  project_type: string;
  detected_languages: string[];
  detected_frameworks: string[];
  entry_points: string[];
  file_tree: FileNode[];
  dependencies: DependencyRelation[];
  capacity_metrics: ProjectCapacityMetrics;
  bugs: BugReport[];
  optimizations: OptimizationFinding[];
  security_findings: SecurityFinding[];
  architecture_findings: ArchitectureFinding[];
}

export interface AgentInfo {
  id: string;
  name: string;
  role: string;
  avatar: string;
  specialization: string;
  status: string;
  key_findings_count: number;
  summary: string;
}

export interface AgentChatMessage {
  role: 'user' | 'agent' | 'system';
  content: string;
  timestamp: string;
  agent_id?: string | null;
  references?: string[] | null;
}

export interface AgentChatResponse {
  agent_id: string;
  agent_name: string;
  reply: string;
  referenced_files: string[];
  suggested_actions: string[];
}

export interface GitRepoRequest {
  repo_url: string;
  branch?: string;
  auth_token?: string;
}

export interface ProjectScanResponse {
  project_id: string;
  project_name: string;
  file_tree: FileNode[];
  total_files: number;
  total_lines: number;
  bugs: BugReport[];
  scan_duration_ms: number;
  model_used: string;
  engine_mode?: EngineMode;
  api_key_configured?: boolean;
  optimizations_count?: number;
  security_count?: number;
  architecture_count?: number;
}

export interface ChangeHistoryEntry {
  id: string;
  bug_id: string;
  bug_title: string;
  file_path: string;
  action: 'ACCEPTED' | 'REJECTED' | 'REVERTED';
  timestamp: string;
  original_code: string;
  patched_code: string;
  composed_code?: string;
  diff: string;
  comment?: string | null;
}

export interface SystemHealth {
  status: string;
  developer_account: string;
  engine_mode?: EngineMode;
  api_key_configured?: boolean;
  engine?: string;
  current_project?: string | null;
  loaded_bugs_count: number;
  optimizations_count?: number;
  security_findings_count?: number;
}
