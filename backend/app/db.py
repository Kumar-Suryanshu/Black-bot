import sqlite3
import json
import os
from typing import Optional, List, Dict, Any

class ConcurrentModificationError(Exception):
    """Raised when an optimistic locking version mismatch occurs."""
    pass

def get_connection(db_path="data/rerun.db"):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_db(db_path="data/rerun.db"):
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            benchmark_id TEXT,
            commit_sha TEXT,
            status TEXT,
            state_json TEXT,
            created_at TEXT,
            updated_at TEXT,
            version INTEGER DEFAULT 1
        )
    ''')
    
    # Check if version column exists in existing projects table
    cursor.execute("PRAGMA table_info(projects)")
    columns = [row[1] for row in cursor.fetchall()]
    if "version" not in columns:
        cursor.execute("ALTER TABLE projects ADD COLUMN version INTEGER DEFAULT 1")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT,
            ts TEXT,
            step INTEGER,
            role TEXT,
            type TEXT,
            tool TEXT,
            summary TEXT,
            evidence_ids_json TEXT,
            payload_json TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS evidence (
            id TEXT PRIMARY KEY,
            project_id TEXT,
            type TEXT,
            artifact_path TEXT,
            line_start INTEGER,
            line_end INTEGER,
            sha256 TEXT,
            excerpt TEXT,
            created_by_tool TEXT,
            tool_call_id TEXT,
            ts TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_project_state(db_path, project_id, benchmark_id, commit_sha, status, state_model, expected_version: Optional[int] = None):
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    # Check if table has version column
    cursor.execute("PRAGMA table_info(projects)")
    columns = [row[1] for row in cursor.fetchall()]
    if "version" not in columns:
        cursor.execute("ALTER TABLE projects ADD COLUMN version INTEGER DEFAULT 1")
    
    if expected_version is not None:
        cursor.execute('''
            UPDATE projects 
            SET benchmark_id = ?, commit_sha = ?, status = ?, state_json = ?, updated_at = datetime('now'), version = version + 1
            WHERE id = ? AND version = ?
        ''', (benchmark_id, commit_sha, status, state_model.model_dump_json(), project_id, expected_version))
        if cursor.rowcount == 0:
            conn.rollback()
            conn.close()
            raise ConcurrentModificationError(f"Concurrent update conflict for project {project_id} (expected version {expected_version})")
        state_model.version = expected_version + 1
    else:
        cursor.execute("SELECT version FROM projects WHERE id = ?", (project_id,))
        row = cursor.fetchone()
        if row is not None:
            cur_version = row[0] if row[0] is not None else 1
            new_version = cur_version + 1
            state_model.version = new_version
            cursor.execute('''
                UPDATE projects 
                SET benchmark_id = ?, commit_sha = ?, status = ?, state_json = ?, updated_at = datetime('now'), version = ?
                WHERE id = ?
            ''', (benchmark_id, commit_sha, status, state_model.model_dump_json(), new_version, project_id))
        else:
            state_model.version = 1
            cursor.execute('''
                INSERT INTO projects 
                (id, benchmark_id, commit_sha, status, state_json, created_at, updated_at, version) 
                VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'), 1)
            ''', (project_id, benchmark_id, commit_sha, status, state_model.model_dump_json()))
            
    conn.commit()
    conn.close()

def get_project_state(db_path, project_id):
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    # Check if version column exists
    cursor.execute("PRAGMA table_info(projects)")
    columns = [row[1] for row in cursor.fetchall()]
    has_version = "version" in columns
    
    if has_version:
        cursor.execute('SELECT state_json, version FROM projects WHERE id = ?', (project_id,))
    else:
        cursor.execute('SELECT state_json FROM projects WHERE id = ?', (project_id,))
        
    row = cursor.fetchone()
    conn.close()
    if row:
        from agent.state import ProjectState
        state = ProjectState.model_validate_json(row[0])
        if has_version and row[1] is not None:
            state.version = row[1]
        return state
    return None

def get_events_since(db_path, project_id, last_event_id):
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, ts, step, role, type, tool, summary, evidence_ids_json, payload_json
        FROM events 
        WHERE project_id = ? AND id > ?
        ORDER BY id ASC
    ''', (project_id, last_event_id))
    rows = cursor.fetchall()
    conn.close()
    
    events = []
    for row in rows:
        events.append({
            "id": row[0],
            "ts": row[1],
            "project_id": project_id,
            "step": row[2],
            "role": row[3],
            "type": row[4],
            "tool": row[5],
            "summary": row[6],
            "evidence_ids": json.loads(row[7]) if row[7] else [],
            "payload": json.loads(row[8]) if row[8] else {}
        })
    return events

def insert_evidence(db_path: str, ev_dict: Any, project_id: str = None):
    init_db(db_path)
    if isinstance(ev_dict, str) and not isinstance(project_id, str):
        ev_dict, project_id = project_id, ev_dict
    if hasattr(ev_dict, "model_dump"):
        ev_dict = ev_dict.model_dump()
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO evidence
        (id, project_id, type, artifact_path, line_start, line_end, sha256, excerpt, created_by_tool, tool_call_id, ts)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        ev_dict.get("id"),
        project_id,
        ev_dict.get("type"),
        ev_dict.get("artifact_path"),
        ev_dict.get("line_start"),
        ev_dict.get("line_end"),
        ev_dict.get("sha256"),
        ev_dict.get("excerpt"),
        ev_dict.get("created_by_tool"),
        ev_dict.get("tool_call_id"),
        ev_dict.get("ts")
    ))
    conn.commit()
    conn.close()

def get_evidence_by_id(db_path: str, project_id: str, eid: str) -> Optional[Dict[str, Any]]:
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, project_id, type, artifact_path, line_start, line_end, sha256, excerpt, created_by_tool, tool_call_id, ts
        FROM evidence
        WHERE project_id = ? AND id = ?
    ''', (project_id, eid))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "id": row[0],
            "project_id": row[1],
            "type": row[2],
            "artifact_path": row[3],
            "line_start": row[4],
            "line_end": row[5],
            "sha256": row[6],
            "excerpt": row[7],
            "created_by_tool": row[8],
            "tool_call_id": row[9],
            "ts": row[10]
        }
    return None

def get_all_evidence(db_path: str, project_id: str) -> List[Dict[str, Any]]:
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, project_id, type, artifact_path, line_start, line_end, sha256, excerpt, created_by_tool, tool_call_id, ts
        FROM evidence
        WHERE project_id = ?
        ORDER BY id ASC
    ''', (project_id,))
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": r[0],
            "project_id": r[1],
            "type": r[2],
            "artifact_path": r[3],
            "line_start": r[4],
            "line_end": r[5],
            "sha256": r[6],
            "excerpt": r[7],
            "created_by_tool": r[8],
            "tool_call_id": r[9],
            "ts": r[10]
        }
        for r in rows
    ]
