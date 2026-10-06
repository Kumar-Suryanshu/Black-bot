import os
import yaml
import json

ALIAS_MAP = {
    "learning_rate": ["lr", "learning_rate", "learn_rate"],
    "epochs": ["epochs", "n_epochs", "num_epochs"],
    "batch_size": ["batch_size", "bs"],
    "seeds": ["seeds", "seed", "random_seed"],
    "weight_decay": ["weight_decay", "l2"],
    "test_size": ["test_size"]
}

def get_canonical_key(key):
    for can, aliases in ALIAS_MAP.items():
        if key in aliases:
            return can
    return key

def audit(workspace, plan, paper_settings):
    config_diffs = []
    
    # Very simplified config audit:
    # 1. try to read effective config
    # 2. try to read plan.config_file
    
    effective_config = {}
    source_file = None
    
    if plan.effective_config_file and os.path.exists(os.path.join(workspace, plan.effective_config_file)):
        with open(os.path.join(workspace, plan.effective_config_file), "r") as f:
            try:
                effective_config = json.load(f)
                source_file = plan.effective_config_file
            except Exception:
                pass
    elif plan.config_file and os.path.exists(os.path.join(workspace, plan.config_file)):
        with open(os.path.join(workspace, plan.config_file), "r") as f:
            try:
                if plan.config_file.endswith(".yaml") or plan.config_file.endswith(".yml"):
                    effective_config = yaml.safe_load(f)
                elif plan.config_file.endswith(".json"):
                    effective_config = json.load(f)
                source_file = plan.config_file
            except Exception:
                pass

    # Normalize effective config keys
    norm_config = {get_canonical_key(k): v for k, v in effective_config.items()}
    
    for ps in paper_settings:
        can_key = get_canonical_key(ps.key)
        
        if can_key not in norm_config:
            config_diffs.append({
                "key": ps.key,
                "paper_value": ps.value,
                "effective_value": None,
                "source_file": source_file,
                "source_line": None,
                "readme_value": None,
                "status": "not_found"
            })
            continue
            
        eff_val = norm_config[can_key]
        
        # compare
        match = False
        try:
            if isinstance(ps.value, (int, float)) and isinstance(eff_val, (int, float)):
                match = abs(float(ps.value) - float(eff_val)) < 1e-12
            else:
                match = str(ps.value) == str(eff_val)
        except Exception:
            match = str(ps.value) == str(eff_val)
            
        config_diffs.append({
            "key": ps.key,
            "paper_value": ps.value,
            "effective_value": eff_val,
            "source_file": source_file,
            "source_line": None,
            "readme_value": None,
            "status": "match" if match else "mismatch"
        })
        
    return config_diffs
