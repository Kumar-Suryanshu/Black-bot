from pydantic import BaseModel, Field
from typing import Dict, List, Literal, Optional, Any
from agent.state import CriticReview

class CriticAction(BaseModel):
    tool: str
    args: Dict[str, Any] = Field(default_factory=dict)

class CriticPatchReviewOutput(BaseModel):
    action: Optional[CriticAction] = None
    final_review: Optional[CriticReview] = None

class ReportFlag(BaseModel):
    statement_id: str
    issue: Literal["overclaims_causality", "accuses_paper", "claims_unrun_scope", "missing_limitation", "status_inconsistent"]
    suggested_fix: str

class ReportReviewOutput(BaseModel):
    verdict: Literal["CLEAN", "FLAGGED"]
    flags: List[ReportFlag] = Field(default_factory=list)

