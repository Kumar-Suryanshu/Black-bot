from pathlib import Path
from typing import Dict, Any, List

def preflight_check(workspace: str, repo_profile: Dict[str, Any], gpu_enabled: bool = False, gpu_usable: bool = False) -> Dict[str, Any]:
    ws = Path(workspace)
    blockers = []
    warnings = []
    
    triage = repo_profile.get("triage", {})
    if triage:
        # Incorporate triage blockers
        for b in triage.get("blockers", []):
            if b == "gpu_required":
                if gpu_enabled and gpu_usable:
                    warnings.append("repo uses GPU and host GPU is usable")
                else:
                    if "gpu_required" not in blockers:
                        blockers.append("gpu_required")
            elif b not in blockers:
                blockers.append(b)
        # Incorporate triage warnings
        warnings.extend(triage.get("warnings", []))
    else:
        # Fallback to legacy hints
        gpu_hints = repo_profile.get("hints", {}).get("gpu", [])
        if gpu_hints:
            if gpu_enabled and gpu_usable:
                warnings.append("repo uses GPU and host GPU is usable")
            else:
                blockers.append("gpu_required")
                
        data_refs = repo_profile.get("hints", {}).get("data_refs", [])
        for dref in data_refs:
            if not (ws / dref).exists() and not (ws / "data" / Path(dref).name).exists():
                blockers.append("data_unavailable")
                break

    # Network warnings
    net_hints = repo_profile.get("hints", {}).get("network", [])
    if net_hints:
        warnings.append("potential network requests detected in repository code")

    return {
        "blockers": sorted(list(set(blockers))),
        "warnings": sorted(list(set(warnings))),
        "triage_verdict": triage.get("verdict", "FEASIBLE"),
        "triage_reason": triage.get("reason", "")
    }
