import hashlib
import json
import logging
import os
import shutil
import datetime
from agent.state import Evidence
from tools import paths

logger = logging.getLogger(__name__)


def _project_run_dir(project_id, data_dir):
    """
    Where this project's evidence lives.

    `data_dir=None` (the default) follows `tools.paths`, so the test suite's redirect of
    the runs root applies here too. An explicit `data_dir` is still honoured for callers
    that point evidence at a directory of their own.
    """
    if data_dir is None:
        return str(paths.run_dir(project_id))
    return os.path.join(data_dir, "runs", project_id)

def record_evidence(project_state, type_, source_path, line_start, line_end, tool, tool_call_id, data_dir=None):
    ev_id = f"E-{len(project_state.evidence_ids) + 1:03d}"
    
    basename = os.path.basename(source_path)
    snapshot_dir = os.path.join(_project_run_dir(project_state.project_id, data_dir), "evidence")
    os.makedirs(snapshot_dir, exist_ok=True)
    snapshot_path = os.path.join(snapshot_dir, f"{ev_id}_{basename}")
    
    shutil.copy2(source_path, snapshot_path)
    
    with open(snapshot_path, "rb") as f:
        content_bytes = f.read()
        sha256 = hashlib.sha256(content_bytes).hexdigest()
        
    try:
        content_str = content_bytes.decode('utf-8')
    except Exception:
        content_str = "<binary>"
        
    lines = content_str.splitlines()
    excerpt = ""
    if line_start and line_end:
        start_idx = max(0, line_start - 1)
        end_idx = min(len(lines), line_end)
        excerpt = "\n".join(lines[start_idx:end_idx])[:600]
    else:
        excerpt = content_str[:600]
        
    ev = Evidence(
        id=ev_id,
        type=type_,
        artifact_path=snapshot_path,
        line_start=line_start,
        line_end=line_end,
        sha256=sha256,
        excerpt=excerpt,
        created_by_tool=tool,
        tool_call_id=tool_call_id,
        ts=datetime.datetime.now().isoformat()
    )
    
    project_state.evidence_ids.append(ev_id)
    
    # 1. Persist to ledger file data/runs/<project_id>/evidence.json (D12)
    ledger_path = os.path.join(_project_run_dir(project_state.project_id, data_dir), "evidence.json")
    ledger = []
    if os.path.exists(ledger_path):
        try:
            with open(ledger_path, "r", encoding="utf-8") as f:
                ledger = json.load(f)
        except Exception:
            ledger = []
    ledger.append(ev.model_dump())

    # Both durable writes below used to be `except: pass`. A failure then cost an audit-trail
    # entry with no trace anywhere, while state.evidence_ids still advertised the id -- so the
    # console showed evidence chips that resolved to nothing. Failures are now logged, loudly
    # enough to be found, without failing the run that produced the evidence.
    try:
        with open(ledger_path, "w", encoding="utf-8") as f:
            json.dump(ledger, f, indent=2)
    except Exception as exc:
        logger.warning(f"evidence {ev_id}: could not write ledger {ledger_path}: {exc}")

    # 2. Persist to SQLite evidence table (D12)
    try:
        from backend.app.db import insert_evidence
        db_path = os.path.join(data_dir, "rerun.db") if data_dir else "data/rerun.db"
        insert_evidence(db_path, ev.model_dump(), project_state.project_id)
    except Exception as exc:
        logger.warning(f"evidence {ev_id}: could not insert into {db_path}: {exc}")

    try:
        if data_dir not in (None, "data"):
            from backend.app.db import insert_evidence
            insert_evidence("data/rerun.db", ev.model_dump(), project_state.project_id)
    except Exception as exc:
        logger.warning(f"evidence {ev_id}: could not mirror into the production db: {exc}")

    return ev

def load_evidence_artifact(project_id, eid, data_dir=None):
    """
    Returns the text of the artifact the ledger records for EXACTLY this evidence id.

    Callers used to locate artifacts with `f.name.startswith(f"{eid}_")`, but snapshots are
    named `{eid}_{basename}`, ids restart at E-001 for every run, and the snapshot directory
    is shared per project. One id therefore matched several unrelated files, so a quote could
    be "verified" against a different artifact that merely shared the id prefix -- defeating
    the hallucinated-quote check it exists to perform.

    The ledger records the exact artifact_path per id, so resolve through it. Where an id
    appears more than once (snapshots accumulated across runs), the most recent entry wins.
    """
    ledger_path = os.path.join(_project_run_dir(project_id, data_dir), "evidence.json")
    artifact_path = None
    if os.path.exists(ledger_path):
        try:
            with open(ledger_path, "r", encoding="utf-8") as f:
                ledger = json.load(f)
            for entry in reversed(ledger):
                if isinstance(entry, dict) and entry.get("id") == eid:
                    artifact_path = entry.get("artifact_path")
                    break
        except Exception:
            artifact_path = None

    if artifact_path and os.path.exists(artifact_path):
        try:
            with open(artifact_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception:
            return None

    # No ledger entry for this id (hand-seeded fixtures, or a ledger that was not written).
    # Fall back to the snapshot directory, but only accept an unambiguous single match:
    # several files sharing the id prefix is exactly the ambiguity this function exists to
    # remove, and guessing between them is what allowed a quote to be "verified" against the
    # wrong artifact.
    snapshot_dir = os.path.join(_project_run_dir(project_id, data_dir), "evidence")
    if not os.path.isdir(snapshot_dir):
        return None
    try:
        matches = [
            os.path.join(snapshot_dir, name)
            for name in sorted(os.listdir(snapshot_dir))
            if name.startswith(f"{eid}_")
        ]
    except Exception:
        return None
    if len(matches) != 1:
        return None
    try:
        with open(matches[0], "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return None

def verify_quote(evidence_record, quote):
    try:
        with open(evidence_record.artifact_path, "rb") as f:
            content_bytes = f.read()
            curr_sha256 = hashlib.sha256(content_bytes).hexdigest()
    except Exception:
        return False
        
    if curr_sha256 != evidence_record.sha256:
        return False
        
    content_str = content_bytes.decode('utf-8', errors='ignore')
    norm_quote = " ".join(quote.split())
    
    if evidence_record.line_start and evidence_record.line_end:
        lines = content_str.splitlines()
        start = max(0, evidence_record.line_start - 1)
        end = min(len(lines), evidence_record.line_end)
        search_text = " ".join(" ".join(lines[start:end]).split())
    else:
        search_text = " ".join(content_str.split())
        
    return norm_quote in search_text
