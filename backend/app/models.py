from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal

from agent.state import Claim

class ProjectCreateRequest(BaseModel):
    benchmark_id: str
    allow_high_risk: bool = False

class ProjectCreateResponse(BaseModel):
    project_id: str

class ClaimsConfirmRequest(BaseModel):
    claims: List[Claim]
    command: Optional[str] = None
    allow_high_risk: bool = False

class ApprovalRequest(BaseModel):
    decision: Literal["approve", "reject", "edit"]
    comment: Optional[str] = None
    edits: Optional[Any] = None
    confirm_extra: bool = False

class HealthResponse(BaseModel):
    ok: bool
    docker: bool
    llm_primary: bool
    llm_fallback: bool

