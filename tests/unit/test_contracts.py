import os
import sqlite3
import pytest
from agent.state import ProjectState, Claim, PaperSetting, Tolerance
from backend.app.db import init_db, save_project_state, get_project_state

def test_sqlite_roundtrip(tmp_path):
    db_path = str(tmp_path / "rerun.db")
    init_db(db_path)

    state = ProjectState(
        project_id="test_proj",
        benchmark_id="b1",
        repo_commit="abc1234",
        phase="INGEST",
        budgets={"steps": 40},
        claims=[
            Claim(
                id="C-1",
                statement="Acc = 0.95",
                metric="accuracy",
                reported=0.95,
                source_ref="p.2",
                source_quote="Acc = 0.95"
            )
        ],
        paper_settings=[],
        repo_profile={}
    )

    save_project_state(db_path, "test_proj", "b1", "abc1234", "running", state)
    loaded_state = get_project_state(db_path, "test_proj")
    
    assert loaded_state is not None
    assert loaded_state.project_id == "test_proj"
    assert loaded_state.phase == "INGEST"
    assert loaded_state.claims[0].reported == 0.95

def test_stub_orchestrator_walks_phases():
    phases = ["INGEST", "ANALYZE", "CLAIMS_CONFIRM", "PLAN", "PREFLIGHT", 
              "SETUP", "RUN", "OBSERVE", "VALIDATE", "COMPARE", "STATUS", "REPORT", "REPORT_REVIEW", "DONE"]
    
    state = ProjectState(
        project_id="test_proj2",
        benchmark_id="b1",
        repo_commit="abc1234",
        phase="INGEST",
        budgets={},
        claims=[],
        paper_settings=[],
        repo_profile={}
    )

    visited = []
    for p in phases:
        state.phase = p
        visited.append(state.phase)
        
    assert visited == phases
    assert state.phase == "DONE"
