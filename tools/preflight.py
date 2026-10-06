from pathlib import Path
from typing import Dict, Any, List

def preflight_check(workspace: str, repo_profile: Dict[str, Any], gpu_enabled: bool = False, gpu_usable: bool = False) -> Dict[str, Any]:
    ws = Path(workspace)
    blockers = []
    warnings = []
    
    # 1. GPU Check
    gpu_hints = repo_profile.get("hints", {}).get("gpu", [])
    if gpu_hints:
        if gpu_enabled and gpu_usable:
            warnings.append("repo uses GPU and host GPU is usable")
        else:
            blockers.append("gpu_required")
            
    # 2. Data files check
    data_refs = repo_profile.get("hints", {}).get("data_refs", [])
    for dref in data_refs:
        if not (ws / dref).exists():
            blockers.append("data_unavailable")
            break

    # 3. Network warnings
    net_hints = repo_profile.get("hints", {}).get("network", [])
    if net_hints:
        warnings.append("potential network requests detected in repository code")

    return {
        "blockers": blockers,
        "warnings": warnings
    }

