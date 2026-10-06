import re
import os

DENY_LIST = [r"eval.*", r"metric.*", r"test_.*", r"tests/.*", r"split.*", r"data\.py", r"dataset.*", r"data/.*"]
SENSITIVE_KEYS = ["seed", "seeds", "epochs", "n_samples", "test_size", "split_seed", "train_size", "batch_size", "dataset_size"]

def check(state, proposal):
    violations = []
    flags = []
    risk_class = "bug_fix"
    requires_extra_confirm = False
    
    # P1/P2 Path checks
    for edit in proposal.edits:
        file = edit.file
        
        # P2 deny list
        is_denied = False
        for deny_pat in DENY_LIST:
            if re.search(deny_pat, file):
                is_denied = True
                break
                
        if is_denied:
            risk_class = "deviation"
            if not state.allow_high_risk:
                violations.append(f"P2: Edits to {file} are blocked by deny list")
            else:
                requires_extra_confirm = True

    # P3 Size
    if len(proposal.edits) > 2:
        violations.append("P3: Too many files modified")
        
    total_lines = 0
    for edit in proposal.edits:
        if edit.op in ["replace_text", "replace_line", "append_line"]:
            total_lines += len(edit.new.splitlines())
    
    if total_lines > 20:
        violations.append("P3: Too many lines changed")

    # Determine risk_class from type
    if proposal.type == "dependency":
        risk_class = "environment_fix"
    elif proposal.type == "config_value" and risk_class != "deviation":
        risk_class = "config_alignment"
        
    # SENSITIVE KEYS Check P4
    if proposal.type == "config_value":
        # simple heuristic
        for sk in SENSITIVE_KEYS:
            if sk in proposal.rationale.lower() or any(sk in e.new.lower() for e in proposal.edits):
                flags.append("sensitive_key")
                # for now, assume paper provenance is enforced by the solver/critic
                
    return {
        "passed": len(violations) == 0,
        "violations": violations,
        "risk_class": risk_class,
        "flags": flags,
        "requires_extra_confirm": requires_extra_confirm
    }
