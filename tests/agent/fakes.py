import json
from typing import List, Tuple, Any, Dict, Union

class FakeLLM:
    """
    Fake LLM provider for tests.
    Takes a script of (role, mode, response) and pops them sequentially.
    """
    def __init__(self, script: List[Tuple[str, str, Union[Dict[str, Any], str]]]):
        self.script = list(script)
        self.history = []

    def respond(self, messages: List[Dict[str, str]]) -> str:
        if not self.script:
            raise RuntimeError("FakeLLM script exhausted: no more responses configured.")
            
        expected_role, expected_mode, canned_resp = self.script.pop(0)
        user_msg = messages[-1]["content"]
        
        # Verify mode in user prompt
        assert f"Mode: {expected_mode}" in user_msg or "Your response was invalid" in user_msg, (
            f"FakeLLM expected mode '{expected_mode}', but user prompt was: {user_msg[:120]}"
        )
        
        self.history.append({
            "expected_role": expected_role,
            "expected_mode": expected_mode,
            "messages": messages,
            "response": canned_resp
        })
        
        if isinstance(canned_resp, str):
            return canned_resp
        return json.dumps(canned_resp)


def get_fake_script_b1() -> list:
    """Script for B1 Control Case: extracts claims, plans experiment, write report."""
    return [
        # 1. extract_claims
        ("solver", "extract_claims", {
            "claims": [{
                "statement": "We achieved a test accuracy of 0.956 ± 0.002 (mean ± std over 5 seeds).",
                "metric": "test_accuracy",
                "dataset": "digits",
                "reported": 0.956,
                "tolerance": {"type": "abs", "value": 0.01},
                "result_key": "test_accuracy_mean",
                "source_ref": "p.1, lines 58-59",
                "source_quote": "We achieved a test accuracy of 0.956 ± 0.002 (mean ± std over 5 seeds)."
            }],
            "paper_settings": [{
                "key": "learning_rate",
                "value": 0.5,
                "source_ref": "p.1, line 38",
                "source_quote": "learning rate = 0.5"
            }],
            "ambiguities": []
        }),
        # 2. plan_experiment
        ("solver", "plan_experiment", {
            "command": "python train.py --config configs/default.yaml",
            "config_file": "configs/default.yaml",
            "output_file": "outputs/results.json",
            "effective_config_file": "outputs/effective_config.json",
            "seeds": [0, 1, 2, 3, 4],
            "claim_result_keys": {"C-1": "test_accuracy_mean"},
            "notes": "Plan from README"
        }),
        # 3. write_report
        ("solver", "write_report", {
            "statements": [
                {
                    "id": "S-1",
                    "section": "findings",
                    "kind": "finding",
                    "confidence": "confirmed",
                    "text": "The experiment reproduced the reported accuracy of {{claim.C-1.reported}} with observed {{result.run1.test_accuracy}} within tolerance {{claim.C-1.tolerance}}.",
                    "evidence": ["E-001"]
                }
            ]
        })
    ]

def get_fake_script_b2() -> list:
    """Script for B2 Dependency Case: missing PyYAML."""
    return [
        # 1. extract_claims
        ("solver", "extract_claims", {
            "claims": [{
                "statement": "We achieved a test accuracy of 0.956 ± 0.002 (mean ± std over 5 seeds).",
                "metric": "test_accuracy",
                "dataset": "digits",
                "reported": 0.956,
                "tolerance": {"type": "abs", "value": 0.01},
                "result_key": "test_accuracy_mean",
                "source_ref": "p.1",
                "source_quote": "test accuracy of 0.956"
            }],
            "paper_settings": [{
                "key": "learning_rate",
                "value": 0.5,
                "source_ref": "p.1",
                "source_quote": "learning rate = 0.5"
            }],
            "ambiguities": []
        }),
        # 2. plan_experiment
        ("solver", "plan_experiment", {
            "command": "python train.py --config configs/default.yaml",
            "config_file": "configs/default.yaml",
            "output_file": "outputs/results.json",
            "effective_config_file": "outputs/effective_config.json",
            "seeds": [0, 1, 2, 3, 4],
            "claim_result_keys": {"C-1": "test_accuracy_mean"},
            "notes": "Standard plan"
        }),
        # 3. diagnose_step: inspect requirements.txt
        ("solver", "diagnose_step", {
            "reason": "Run crashed with ModuleNotFoundError for yaml. Let's inspect requirements.txt.",
            "hypotheses": [{
                "id": "H-1",
                "text": "PyYAML is missing from requirements.txt",
                "status": "confirmed",
                "evidence": ["E-001"],
                "tested_with": ["inspect_file"],
                "error_class": "dependency_missing"
            }],
            "next_action": {
                "tool": "propose_patch",
                "args": {}
            }
        }),
        # 4. propose_patch: add PyYAML==6.0.1
        ("solver", "propose_patch", {
            "hypothesis_id": "H-1",
            "type": "dependency",
            "rationale": "ModuleNotFoundError: No module named 'yaml' requires PyYAML==6.0.1",
            "evidence": ["E-001"],
            "alternatives_considered": [{"option": "yaml", "why_not": "PyYAML is the standard PyPI package"}],
            "edits": [{
                "file": "requirements.txt",
                "op": "append_line",
                "new": "PyYAML==6.0.1"
            }]
        }),
        # 5. Critic patch_review
        ("critic", "patch_review", {
            "id": "R-1",
            "patch_id": "P-1",
            "round": 1,
            "verdict": "SUPPORTED",
            "checks": {
                "cause_is_cited_and_exists": True,
                "evidence_actually_supports_cause": True,
                "change_is_minimal": True,
                "files_in_scope": True,
                "not_metric_chasing": True,
                "value_has_paper_or_error_provenance": True,
                "no_change_to_evaluation_or_data_semantics": True,
                "alternative_explanations_considered": True,
                "reversible_and_smoke_testable": True
            },
            "verified_evidence": [{"id": "E-001", "what_i_found": "ModuleNotFoundError: No module named 'yaml'"}],
            "objections": [],
            "required_changes": [],
            "confidence": "high",
            "model": "fake"
        }),
        # 6. write_report
        ("solver", "write_report", {
            "statements": [
                {
                    "id": "S-1",
                    "section": "findings",
                    "kind": "finding",
                    "confidence": "confirmed",
                    "text": "Reproduction succeeded after applying 1 dependency patch.",
                    "evidence": ["E-001"]
                }
            ]
        })
    ]

