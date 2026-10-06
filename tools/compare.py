import math

def compare(claim, observed_mean):
    if observed_mean is None or math.isnan(observed_mean):
        return {
            "claim_id": claim.id,
            "reported": claim.reported,
            "observed": observed_mean,
            "abs_gap": None,
            "rel_gap": None,
            "tolerance": claim.tolerance.model_dump(),
            "within_tolerance": None
        }
        
    reported = claim.reported
    abs_gap = abs(reported - observed_mean)
    rel_gap = abs_gap / abs(reported) if reported != 0 else float('inf')
    
    tol_val = claim.tolerance.value + 1e-9
    
    if claim.tolerance.type == "abs":
        within = abs_gap <= tol_val
    else:
        within = rel_gap <= tol_val
        
    return {
        "claim_id": claim.id,
        "reported": reported,
        "observed": observed_mean,
        "abs_gap": abs_gap,
        "rel_gap": rel_gap,
        "tolerance": claim.tolerance.model_dump(),
        "within_tolerance": within
    }
