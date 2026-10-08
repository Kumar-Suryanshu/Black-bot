from pydantic import BaseModel, Field
from typing import Literal, Any

Status = Literal["REPRODUCED","PARTIALLY_REPRODUCED","NOT_REPRODUCED","UNABLE_TO_EXECUTE","INCONCLUSIVE"]
Phase  = Literal["INGEST","ANALYZE","CLAIMS_CONFIRM","PLAN","PREFLIGHT","SETUP","RUN","OBSERVE",
                 "VALIDATE","COMPARE","DIAGNOSE","PATCH_PROPOSE","POLICY_CHECK","CRITIC_REVIEW",
                 "APPROVAL","PATCH_APPLY","STATUS","REPORT","REPORT_REVIEW","DONE"]
ErrorClass = Literal["dependency_missing","dependency_conflict","path_error","gpu_required","network_required",
                     "resource_oom","resource_timeout","sandbox_permission","config_error","numerical_invalid",
                     "config_mismatch","unknown"]
RiskClass = Literal["environment_fix","bug_fix","config_alignment","deviation"]

class Tolerance(BaseModel):
    type: Literal["abs","rel"] = "abs"
    value: float = 0.01

class MetricExtraction(BaseModel):
    kind: Literal["results_json", "json_file", "csv_file", "regex_log", "txt_file"] = "results_json"
    path: str | None = None
    key: str | None = None
    regex: str | None = None
    column: str | None = None
    aggregation: Literal["last", "mean_over_seeds", "max", "min", "first"] = "last"

class Claim(BaseModel):
    id: str = "C-1"
    statement: str
    metric: str
    dataset: str | None = None
    reported: float
    tolerance: Tolerance = Field(default_factory=Tolerance)
    result_key: str | None = None
    metric_extraction: MetricExtraction | None = None
    source_ref: str
    source_quote: str
    primary: bool = True
    confirmed_by_human: bool = False

class PaperSetting(BaseModel):
    key: str
    value: Any
    source_ref: str
    source_quote: str

class Plan(BaseModel):
    command: str
    config_file: str | None = None
    output_file: str
    effective_config_file: str | None = None
    seeds: list[int]
    notes: str = ""

class Evidence(BaseModel):
    id: str
    type: Literal["log","file","config","package_query","result","paper"]
    artifact_path: str
    line_start: int | None
    line_end: int | None
    sha256: str
    excerpt: str
    created_by_tool: str
    tool_call_id: str
    ts: str

class Hypothesis(BaseModel):
    id: str
    text: str
    status: Literal["open","confirmed","refuted"] = "open"
    evidence: list[str] = Field(default_factory=list)
    tested_with: list[str] = Field(default_factory=list)
    error_class: ErrorClass | None = None

class Edit(BaseModel):
    file: str
    op: Literal["replace_text","replace_line","append_line"]
    old: str | None = None
    new: str
    line: int | None = None

class PatchProposal(BaseModel):
    id: str
    hypothesis_id: str
    type: Literal["dependency","config_value","path_string","code_typo"]
    rationale: str
    evidence: list[str]
    alternatives_considered: list[dict]
    edits: list[Edit]
    diff: str | None = None
    risk_class: RiskClass | None = None
    policy_result: dict | None = None
    critic_status: Literal["pending","supported","needs_revision","block","unavailable"] = "pending"
    status: Literal["proposed","approved","rejected","applied","reverted","dropped"] = "proposed"
    approval: str | None = None
    worked: bool | None = None
    fix_signature: str | None = None

class CriticReview(BaseModel):
    id: str
    patch_id: str
    round: int
    verdict: Literal["SUPPORTED","NEEDS_REVISION","BLOCK"]
    checks: dict[str, bool]
    verified_evidence: list[dict]
    objections: list[str]
    required_changes: list[str]
    confidence: Literal["high","medium","low"]
    model: str

class Approval(BaseModel):
    id: str
    patch_id: str
    decision: Literal["approve","reject","edit"]
    by: str = "user"
    at: str
    comment: str | None = None
    over_critic_objection: bool = False

class Attempt(BaseModel):
    n: int
    patches_applied: list[str]
    exit_code: int | None
    error_class: ErrorClass | None = None
    metrics: dict[str, Any] | None = None
    comparison: list[dict] | None = None
    evidence: list[str] = Field(default_factory=list)
    outcome: str | None = None
    started_at: str
    ended_at: str | None = None
    duration_s: float | None = None
    timed_out: bool = False
    oom: bool = False
    log_path: str | None = None

class ProjectState(BaseModel):
    project_id: str
    source: Literal["benchmark", "custom"] = "benchmark"
    benchmark_id: str | None = None
    repo_url: str | None = None
    repo_ref: str | None = None
    repo_commit: str = "unknown"
    paper_path: str | None = None
    paper_sha256: str | None = None
    user_command: str | None = None
    run_timeout_s: int | None = None
    simulated: bool = False
    phase: Phase
    budgets: dict
    claims: list[Claim]
    paper_settings: list[PaperSetting]
    command_confirmed: bool = False
    allow_high_risk: bool = False
    repo_profile: dict = Field(default_factory=dict)
    plan: Plan | None = None
    preflight: dict = Field(default_factory=lambda: {"blockers": []})
    environment: dict = Field(default_factory=dict)
    attempts: list[Attempt] = Field(default_factory=list)
    hypotheses: list[Hypothesis] = Field(default_factory=list)
    patches: list[PatchProposal] = Field(default_factory=list)
    critic_reviews: list[CriticReview] = Field(default_factory=list)
    approvals: list[Approval] = Field(default_factory=list)
    failed_fixes: list[str] = Field(default_factory=list)
    unresolved_issues: list[str] = Field(default_factory=list)
    config_diff: list[dict] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    version: int = 1
    workspace: str | None = None
    latest_log_path: str | None = None
    silent_divergence: bool = False
    active_container_name: str | None = None
    abort_requested: bool = False
    provisioning_plan: dict | None = None
    provisioning_approved: bool = False
    pending: dict | None = None
    final: dict | None = None

class Event(BaseModel):
    id: int
    ts: str
    project_id: str
    step: int
    role: Literal["solver","critic","arbiter","tool","human","system"]
    type: str
    tool: str | None
    summary: str
    evidence_ids: list[str] = Field(default_factory=list)
    payload: dict = Field(default_factory=dict)
