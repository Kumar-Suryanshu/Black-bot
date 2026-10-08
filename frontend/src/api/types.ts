export interface Tolerance {
  type: 'abs' | 'rel';
  value: number;
}

export interface Claim {
  id: string;
  statement: string;
  metric: string;
  dataset?: string | null;
  reported: number;
  tolerance: Tolerance;
  result_key?: string | null;
  source_ref: string;
  source_quote: string;
  primary?: boolean;
  confirmed_by_human?: boolean;
}

export interface PaperSetting {
  key: string;
  value: any;
  source_ref: string;
  source_quote: string;
}

export interface Plan {
  command: string;
  config_file?: string | null;
  output_file: string;
  effective_config_file?: string | null;
  seeds: number[];
  notes?: string;
}

export interface Comparison {
  claim_id: string;
  reported: number;
  observed: number | null;
  abs_gap: number | null;
  rel_gap: number | null;
  tolerance: Tolerance;
  within_tolerance: boolean | null;
}

export interface Attempt {
  n: number;
  exit_code: number;
  stdout_preview?: string;
  error_class?: string | null;
  metrics?: Record<string, any>;
  comparison?: Comparison[];
  used_patches?: string[];
  log_path?: string;
}

export interface PatchEdit {
  file: string;
  op: string;
  target?: string;
  new?: string;
  old?: string;
  line?: number;
}

export interface Patch {
  id: string;
  hypothesis_id?: string;
  risk_class: 'environment_fix' | 'bug_fix' | 'config_alignment' | 'deviation';
  edits: PatchEdit[];
  diff: string;
  rationale: string;
  evidence_ids: string[];
  status: 'proposed' | 'applied' | 'rejected' | 'reverted';
  created_at?: string;
  comment?: string;
}

export interface CriticReview {
  id: string;
  patch_id: string;
  round: number;
  verdict: 'SUPPORTED' | 'OBJECTED' | 'ABSTAIN';
  checks: {
    cause_is_cited_and_exists: boolean;
    evidence_actually_supports_cause: boolean;
    change_is_minimal: boolean;
    files_in_scope: boolean;
    not_metric_chasing: boolean;
    value_has_paper_or_error_provenance: boolean;
    no_change_to_evaluation_or_data_semantics: boolean;
    alternative_explanations_considered: boolean;
    reversible_and_smoke_testable: boolean;
  };
  verified_evidence: Array<{ id: string; what_i_found: string }>;
  objections: string[];
  required_changes: string[];
  confidence: 'high' | 'med' | 'low';
}

export interface PendingAction {
  kind: 'claims' | 'approval' | 'provisioning';
  id: string;
  patch_id?: string;
  banner?: string | null;
  packages?: string[];
  python_image?: string;
  warnings?: string[];
  details?: any[];
}

export interface ProjectBudgets {
  steps_used: number;
  max_steps?: number;
  patches_used?: number;
  max_patches?: number;
  warned_80?: boolean;
}

export interface ProjectStateSummary {
  project_id: string;
  source?: 'benchmark' | 'custom';
  benchmark_id?: string | null;
  repo_url?: string | null;
  repo_ref?: string | null;
  paper_path?: string | null;
  user_command?: string | null;
  simulated?: boolean;
  phase: string;
  pending: PendingAction | null;
  budgets: ProjectBudgets;
  attempts: Attempt[];
  patches: Patch[];
  status?: string;
  claims?: Claim[];
  paper_settings?: PaperSetting[];
  plan?: Plan | null;
  config_diff?: Array<{
    key: string;
    paper_value: any;
    effective_value: any;
    source_file?: string;
    line_number?: number;
    readme_value?: any;
    status: string;
  }>;
  evidence_ids?: string[];
  unresolved_issues?: string[];
  final?: {
    status: string;
    reason: string;
    after_n_fixes: number;
    confidence_factors?: Record<string, any>;
  } | null;
}

export interface Event {
  id: number;
  project_id: string;
  ts: string;
  step: number;
  role: 'solver' | 'critic' | 'arbiter' | 'tool' | 'human' | 'system';
  type: string;
  tool?: string | null;
  summary: string;
  evidence_ids: string[];
  payload?: any;
}

export interface HealthResponse {
  ok: boolean;
  docker: boolean;
  llm_primary: boolean;
  llm_fallback: boolean;
}

export interface BenchmarkCase {
  id: string;
  title: string;
  description: string;
  paper_filename?: string;
}

export interface EvidenceItem {
  id: string;
  type: 'log' | 'file' | 'config' | 'package_query' | 'result' | 'paper';
  artifact_path: string;
  line_start?: number | null;
  line_end?: number | null;
  sha256: string;
  excerpt: string;
  created_by_tool: string;
  tool_call_id: string;
  ts: string;
}

export interface ReportStatement {
  id: string;
  section: 'findings' | 'causes' | 'fixes';
  kind: string;
  confidence: string;
  text: string;
  evidence: string[];
}

export interface ReportData {
  project_id: string;
  benchmark_id: string;
  status: 'REPRODUCED' | 'PARTIALLY_REPRODUCED' | 'NOT_REPRODUCED' | 'UNABLE_TO_EXECUTE' | 'INCONCLUSIVE';
  reason: string;
  after_n_fixes: number;
  attempts: Attempt[];
  patches: Patch[];
  claims: Claim[];
  config_diff?: any[];
  evidence_ledger?: Record<string, EvidenceItem>;
  statements?: ReportStatement[];
  confidence_factors?: Record<string, any>;
  limitations?: string[];
}
