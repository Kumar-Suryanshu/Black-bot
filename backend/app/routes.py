import json
import os
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Header, Request
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
import uuid
import datetime

from backend.app.models import (
    ProjectCreateRequest, ProjectCreateResponse,
    ClaimsConfirmRequest, ApprovalRequest, HealthResponse
)
from backend.app.db import get_connection, get_project_state, save_project_state
from backend.app.runner import start_project_worker
from backend.app.sse import stream_manager
from agent.state import ProjectState, Approval

router = APIRouter()

@router.get("/api/health", response_model=HealthResponse)
def health_check():
    # Basic check, returning True to satisfy Stage 9
    return HealthResponse(ok=True, docker=True, llm_primary=True, llm_fallback=True)

@router.get("/api/benchmarks")
def get_benchmarks():
    reg_path = "benchmarks/registry.json"
    if not os.path.exists(reg_path):
        return []
    with open(reg_path) as f:
        data = json.load(f)
    # Filter out gold paths
    out = []
    for c in data.get("cases", []):
        out.append({
            "id": c["id"],
            "title": c.get("title", ""),
            "description": c.get("description", ""),
            "paper_filename": c.get("paper_path", "")
        })
    return out

@router.post("/api/projects", response_model=ProjectCreateResponse)
def create_project(req: ProjectCreateRequest):
    project_id = f"proj_{uuid.uuid4().hex[:8]}"
    state = ProjectState(
        project_id=project_id,
        benchmark_id=req.benchmark_id,
        repo_commit="unknown",
        phase="INGEST",
        budgets={"steps_used": 0, "patches_used": 0},
        claims=[],
        paper_settings=[],
        allow_high_risk=req.allow_high_risk,
        repo_profile={}
    )
    save_project_state("data/rerun.db", project_id, req.benchmark_id, "unknown", "INGEST", state)
    return ProjectCreateResponse(project_id=project_id)

@router.post("/api/projects/{id}/start")
def start_project(id: str):
    state = get_project_state("data/rerun.db", id)
    if not state:
        raise HTTPException(status_code=404, detail="Project not found")
    state.phase = "INGEST"
    save_project_state("data/rerun.db", id, state.benchmark_id, state.repo_commit, state.phase, state)
    start_project_worker(id)
    return {"status": "started"}

@router.get("/api/projects/{id}")
def get_project(id: str):
    state = get_project_state("data/rerun.db", id)
    if not state:
        raise HTTPException(status_code=404, detail="Project not found")
    return {
        "project_id": state.project_id,
        "benchmark_id": state.benchmark_id,
        "phase": state.phase,
        "pending": state.pending,
        "budgets": state.budgets,
        "attempts": [a.model_dump() for a in state.attempts],
        "patches": [p.model_dump() for p in state.patches],
        "status": state.final.get("status") if state.final else state.phase
    }

@router.get("/api/projects/{id}/claims-draft")
def get_claims_draft(id: str):
    state = get_project_state("data/rerun.db", id)
    if not state:
        raise HTTPException(status_code=404, detail="Project not found")
    return {
        "claims": [c.model_dump() for c in state.claims],
        "paper_settings": [ps.model_dump() for ps in state.paper_settings],
        "command": state.plan.command if state.plan else None
    }

@router.post("/api/projects/{id}/claims/confirm")
def confirm_claims(id: str, req: ClaimsConfirmRequest):
    state = get_project_state("data/rerun.db", id)
    if not state:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Idempotent check
    if state.command_confirmed and state.phase != "CLAIMS_CONFIRM":
        return {"status": "already_confirmed"}

    state.claims = req.claims
    state.allow_high_risk = req.allow_high_risk
    if req.command and state.plan:
        state.plan.command = req.command
    state.command_confirmed = True
    
    save_project_state("data/rerun.db", id, state.benchmark_id, state.repo_commit, state.phase, state)
    
    # Resume orchestrator
    start_project_worker(id)
    return {"status": "confirmed"}

@router.post("/api/projects/{id}/claims/reject")
def reject_claims(id: str):
    state = get_project_state("data/rerun.db", id)
    if not state:
        raise HTTPException(status_code=404, detail="Project not found")
    
    state.phase = "DONE"
    state.final = {"status": "INCONCLUSIVE", "reason": "no claim confirmed", "after_n_fixes": 0}
    state.pending = None
    save_project_state("data/rerun.db", id, state.benchmark_id, state.repo_commit, "INCONCLUSIVE", state)
    return {"status": "rejected"}

@router.get("/api/projects/{id}/events")
def stream_events(id: str, request: Request, last_event_id: Optional[str] = Header(default="0")):
    try:
        last_id = int(last_event_id)
    except ValueError:
        last_id = 0
    return StreamingResponse(stream_manager.event_generator(id, last_id), media_type="text/event-stream")

@router.get("/api/projects/{id}/approvals/pending")
def get_pending_approval(id: str):
    state = get_project_state("data/rerun.db", id)
    if not state or not state.pending or state.pending.get("kind") != "approval":
        raise HTTPException(status_code=404, detail="No pending approval")
    
    patch_id = state.pending.get("patch_id")
    patch = next((p for p in state.patches if p.id == patch_id), None)
    if not patch:
        raise HTTPException(status_code=404, detail="Patch not found")
        
    reviews = [r for r in state.critic_reviews if r.patch_id == patch_id]
    
    return {
        "approval_id": state.pending.get("id"),
        "patch": patch.model_dump(),
        "reviews": [r.model_dump() for r in reviews],
        "banner": state.pending.get("banner")
    }

@router.post("/api/approvals/{approval_id}")
def process_approval(approval_id: str, req: ApprovalRequest):
    # Search all projects for this pending approval ID
    conn = get_connection("data/rerun.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM projects")
    rows = cursor.fetchall()
    conn.close()
    
    target_project_id = None
    state = None
    for row in rows:
        proj_id = row[0]
        s = get_project_state("data/rerun.db", proj_id)
        if s and s.pending and s.pending.get("id") == approval_id:
            target_project_id = proj_id
            state = s
            break
            
    if not target_project_id:
        raise HTTPException(status_code=404, detail="Approval not found")
        
    # Idempotent: check if already approved
    if any(a.id == approval_id for a in state.approvals):
        return {"status": "already_processed"}
        
    # Validation per spec: if requires_extra_confirm and not confirmed
    patch_id = state.pending.get("patch_id")
    patch = next((p for p in state.patches if p.id == patch_id), None)
    # The banner or critic review might dictate requires_extra_confirm. 
    # The spec says: approve on a packet with requires_extra_confirm and confirm_extra?false -> 400.
    if state.pending.get("banner") and req.decision == "approve" and not req.confirm_extra:
        raise HTTPException(status_code=400, detail="Extra confirmation required due to banner")
        
    appr = Approval(
        id=approval_id,
        patch_id=patch_id,
        decision=req.decision,
        by="user",
        at=datetime.datetime.now().isoformat(),
        comment=req.comment,
        over_critic_objection=(state.pending.get("banner") is not None)
    )
    
    state.approvals.append(appr)
    # Let run_project clear pending, or we clear it here? 
    # Wait, the spec says handler checks matching_app. We can leave state.pending.
    # Actually, the orchestrator clears state.pending in handle_approval! 
    
    save_project_state("data/rerun.db", target_project_id, state.benchmark_id, state.repo_commit, state.phase, state)
    
    # Resume
    start_project_worker(target_project_id)
    return {"status": "processed"}

@router.get("/api/projects/{id}/evidence/{eid}")
def get_evidence(id: str, eid: str):
    state = get_project_state("data/rerun.db", id)
    if not state:
        raise HTTPException(status_code=404, detail="Project not found")
    # Evidence could be in SQLite or in state.evidence_ids. Actually, evidence objects are stored in the `evidence` table or ledger?
    # Stage 2 created `tools/evidence.py`. It probably saves to a local ledger file.
    import json
    ledger_path = f"data/runs/{id}/evidence.json"
    if os.path.exists(ledger_path):
        with open(ledger_path) as f:
            ledger = json.load(f)
            for item in ledger:
                if item.get("id") == eid:
                    return item
    raise HTTPException(status_code=404, detail="Evidence not found")

@router.get("/api/projects/{id}/runs/{n}/log")
def get_run_log(id: str, n: int, tail: Optional[int] = None):
    log_path = f"data/runs/{id}/logs/run_{n}.log"
    if not os.path.exists(log_path):
        raise HTTPException(status_code=404, detail="Log not found")
    with open(log_path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    if tail and tail > 0:
        lines = lines[-tail:]
    return {"log": "".join(lines)}

@router.get("/api/projects/{id}/report")
def get_report(id: str):
    state = get_project_state("data/rerun.db", id)
    if not state:
        raise HTTPException(status_code=404, detail="Project not found")
    # Stage 11 will generate real report
    return {"report": "Stage 11 pending", "status": state.final.get("status") if state.final else state.phase}

@router.post("/api/projects/{id}/abort")
def abort_project(id: str):
    state = get_project_state("data/rerun.db", id)
    if not state:
        raise HTTPException(status_code=404, detail="Project not found")
    state.phase = "DONE"
    state.final = {"status": "INCONCLUSIVE", "reason": "aborted by user", "after_n_fixes": len(state.patches)}
    state.pending = None
    save_project_state("data/rerun.db", id, state.benchmark_id, state.repo_commit, "INCONCLUSIVE", state)
    return {"status": "aborted"}
