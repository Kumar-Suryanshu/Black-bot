import re
import os
from pathlib import Path
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db import init_db, save_project_state, get_project_state, insert_evidence, get_connection
from agent.state import ProjectState, Evidence

client = TestClient(app)

def test_secrets_hygiene_in_runs_and_logs():
    """
    Gate: Grep data/runs/** for live API key patterns.
    Ensures Invariant I4 secret scrubbing works and no unredacted keys are leaked to disk.
    """
    # Patterns for Gemini and OpenAI keys
    secret_patterns = [
        re.compile(r"AIza[0-9A-Za-z-_]{35}"),
        re.compile(r"AQ\.[0-9A-Za-z-_]{35,}"),
        re.compile(r"sk-[0-9A-Za-z]{20,}")
    ]

    runs_dir = Path("data/runs")
    if not runs_dir.exists():
        return

    leaked_found = []
    for f in runs_dir.rglob("*"):
        if ".site" in f.parts or ".git" in f.parts or "__pycache__" in f.parts:
            continue
        if f.is_file() and not f.name.endswith((".png", ".bin", ".whl", ".pyc", ".tar", ".gz")):
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
                for pat in secret_patterns:
                    matches = pat.findall(content)
                    if matches:
                        leaked_found.append((str(f), matches))
            except Exception:
                pass

    assert len(leaked_found) == 0, f"Found unredacted secrets in run files: {leaked_found}"

def test_data_deletion_removes_workspace_and_db(tmp_path):
    """
    Gate: DELETE /api/projects/{id} removes workspace, logs, wheelhouse, outputs,
    and database rows for the given project (R9).
    """
    proj_id = "proj_test_deletion"
    init_db("data/rerun.db")

    # 1. Create on-disk directory structure
    proj_dir = Path(f"data/runs/{proj_id}")
    proj_dir.mkdir(parents=True, exist_ok=True)
    (proj_dir / "workspace").mkdir(exist_ok=True)
    (proj_dir / "workspace" / "train.py").write_text("print('hello')")
    (proj_dir / "logs").mkdir(exist_ok=True)
    (proj_dir / "logs" / "run_1.log").write_text("run log")
    (proj_dir / "evidence.json").write_text("[]")

    # 2. Insert records into DB
    state = ProjectState(
        project_id=proj_id,
        benchmark_id="b1",
        repo_commit="c1",
        phase="RUN",
        budgets={},
        claims=[],
        paper_settings=[]
    )
    save_project_state("data/rerun.db", proj_id, "b1", "c1", "RUN", state)
    
    ev = Evidence(
        id="E-DEL",
        type="log",
        artifact_path="data/runs/proj_test_deletion/logs/run_1.log",
        line_start=1,
        line_end=1,
        sha256="abc",
        excerpt="run log",
        created_by_tool="run",
        tool_call_id="call_1",
        ts="2026-10-08T00:00:00"
    )
    insert_evidence("data/rerun.db", proj_id, ev)

    # 3. Check disk usage endpoint before delete
    res_disk = client.get(f"/api/projects/{proj_id}/disk")
    assert res_disk.status_code == 200
    assert res_disk.json()["disk_bytes"] > 0

    # 4. Execute DELETE /api/projects/{id}
    res_del = client.delete(f"/api/projects/{proj_id}")
    assert res_del.status_code == 200
    assert res_del.json() == {"status": "deleted", "id": proj_id}

    # 5. Verify on-disk files are deleted
    assert not proj_dir.exists(), f"Project directory {proj_dir} was not deleted from disk"

    # 6. Verify DB records are deleted
    loaded_state = get_project_state("data/rerun.db", proj_id)
    assert loaded_state is None

    conn = get_connection("data/rerun.db")
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM evidence WHERE project_id = ?", (proj_id,))
    count_ev = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM events WHERE project_id = ?", (proj_id,))
    count_evts = cur.fetchone()[0]
    conn.close()

    assert count_ev == 0
    assert count_evts == 0

def test_admin_kill_switch():
    """
    Gate: POST /api/admin/kill-switch invokes global container and worker kill.
    """
    res = client.post("/api/admin/kill-switch")
    assert res.status_code == 200
    assert res.json() == {"status": "all_containers_and_workers_terminated"}
