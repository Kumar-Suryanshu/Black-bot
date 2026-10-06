import sqlite3
import json
import os

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
            updated_at TEXT
        )
    ''')
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
    conn.commit()
    conn.close()

def save_project_state(db_path, project_id, benchmark_id, commit_sha, status, state_model):
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO projects 
        (id, benchmark_id, commit_sha, status, state_json, created_at, updated_at) 
        VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))
    ''', (project_id, benchmark_id, commit_sha, status, state_model.model_dump_json()))
    conn.commit()
    conn.close()

def get_project_state(db_path, project_id):
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT state_json FROM projects WHERE id = ?', (project_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        from agent.state import ProjectState
        return ProjectState.model_validate_json(row[0])
    return None
