import hashlib
import os
import shutil
import datetime
from agent.state import Evidence

def record_evidence(project_state, type_, source_path, line_start, line_end, tool, tool_call_id, data_dir="data"):
    ev_id = f"E-{len(project_state.evidence_ids) + 1:03d}"
    
    basename = os.path.basename(source_path)
    snapshot_dir = os.path.join(data_dir, "runs", project_state.project_id, "evidence")
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
    return ev

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
