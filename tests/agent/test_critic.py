import pytest
from unittest.mock import patch
import json
from agent.state import ProjectState, PatchProposal, Hypothesis, Edit, PaperSetting
from agent.critic.review import build_review_packet, review_patch

def make_critic_test_state():
    h = Hypothesis(id="H-1", text="Missing dependency PyYAML", status="confirmed")
    ps = PaperSetting(key="learning_rate", value=0.5, source_ref="p.1", source_quote="learning rate = 0.5")
    return ProjectState(
        project_id="test_critic_proj",
        benchmark_id="b2_dependency",
        repo_commit="abc1234",
        phase="CRITIC_REVIEW",
        budgets={},
        claims=[],
        paper_settings=[ps],
        repo_profile={},
        hypotheses=[h],
        evidence_ids=["E-001"]
    )

def test_critic_packet_building():
    state = make_critic_test_state()
    patch = PatchProposal(
        id="P-1",
        hypothesis_id="H-1",
        type="dependency",
        rationale="Fix missing PyYAML",
        evidence=["E-001"],
        alternatives_considered=[],
        edits=[Edit(file="requirements.txt", op="append_line", new="PyYAML==6.0.1")]
    )
    packet = build_review_packet(state, patch)
    assert packet["patch_id"] == "P-1"
    assert packet["type"] == "dependency"
    assert packet["hypothesis"] == "Missing dependency PyYAML"
    assert len(packet["paper_settings"]) == 1

@patch("agent.llm.execute_provider_request")
def test_critic_verdict_override_critical_check_failed(mock_execute):
    state = make_critic_test_state()
    patch = PatchProposal(
        id="P-1",
        hypothesis_id="H-1",
        type="config_value",
        rationale="Tune lr to boost accuracy",
        evidence=["E-001"],
        alternatives_considered=[],
        edits=[Edit(file="configs/default.yaml", op="replace_text", old="lr: 0.01", new="lr: 0.5")]
    )
    
    # Critic attempts to say SUPPORTED even though not_metric_chasing is False!
    mock_execute.side_effect = [
        json.dumps({
            "id": "R-1",
            "patch_id": "P-1",
            "round": 1,
            "verdict": "SUPPORTED",
            "checks": {
                "cause_is_cited_and_exists": True,
                "evidence_actually_supports_cause": True,
                "change_is_minimal": True,
                "files_in_scope": True,
                "not_metric_chasing": False, # Critical check fails!
                "value_has_paper_or_error_provenance": True,
                "no_change_to_evaluation_or_data_semantics": True,
                "alternative_explanations_considered": True,
                "reversible_and_smoke_testable": True
            },
            "verified_evidence": [],
            "objections": ["Metric chasing detected"],
            "required_changes": [],
            "confidence": "high",
            "model": "fake"
        }),
        json.dumps({
            "id": "R-2",
            "patch_id": "P-1",
            "round": 2,
            "verdict": "SUPPORTED",
            "checks": {
                "cause_is_cited_and_exists": True,
                "evidence_actually_supports_cause": True,
                "change_is_minimal": True,
                "files_in_scope": True,
                "not_metric_chasing": False,
                "value_has_paper_or_error_provenance": True,
                "no_change_to_evaluation_or_data_semantics": True,
                "alternative_explanations_considered": True,
                "reversible_and_smoke_testable": True
            },
            "verified_evidence": [],
            "objections": [],
            "required_changes": [],
            "confidence": "high",
            "model": "fake"
        })
    ]
    
    # Round 1: Code must override SUPPORTED to NEEDS_REVISION
    rev1 = review_patch(state, patch, round_num=1)
    assert rev1.verdict == "NEEDS_REVISION"
    
    # Round 2: Code must override to BLOCK
    rev2 = review_patch(state, patch, round_num=2)
    assert rev2.verdict == "BLOCK"

def test_critic_unavailable_fallback():
    state = make_critic_test_state()
    patch = PatchProposal(
        id="P-1",
        hypothesis_id="H-1",
        type="dependency",
        rationale="Fix PyYAML",
        evidence=["E-001"],
        alternatives_considered=[],
        edits=[Edit(file="requirements.txt", op="append_line", new="PyYAML==6.0.1")]
    )
    
    def failing_llm(*args, **kwargs):
        raise ConnectionError("Critic service down")
        
    rev = review_patch(state, patch, round_num=1, llm_call_fn=failing_llm)
    assert rev.model == "unavailable"
    assert rev.verdict == "BLOCK"
    assert any("Critic call failed" in obj for obj in rev.objections)
    assert len(rev.checks) == 9
    assert all(val is False for val in rev.checks.values())


