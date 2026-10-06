from agent.state import ProjectState, PatchProposal, Edit
from tools.policy import check

def test_policy_deny_list_blocked():
    state = ProjectState(project_id="1", benchmark_id="b", repo_commit="c", phase="POLICY_CHECK", budgets={}, claims=[], paper_settings=[], repo_profile={}, allow_high_risk=False)
    prop = PatchProposal(id="p1", hypothesis_id="h1", type="code_typo", rationale="", evidence=[], alternatives_considered=[], edits=[
        Edit(file="evaluate.py", op="replace_text", new="abc")
    ])
    
    res = check(state, prop)
    assert res["passed"] is False
    assert "P2" in res["violations"][0]
    
def test_policy_deny_list_allowed_if_opt_in():
    state = ProjectState(project_id="1", benchmark_id="b", repo_commit="c", phase="POLICY_CHECK", budgets={}, claims=[], paper_settings=[], repo_profile={}, allow_high_risk=True)
    prop = PatchProposal(id="p1", hypothesis_id="h1", type="code_typo", rationale="", evidence=[], alternatives_considered=[], edits=[
        Edit(file="evaluate.py", op="replace_text", new="abc")
    ])
    
    res = check(state, prop)
    assert res["passed"] is True
    assert res["requires_extra_confirm"] is True
    assert res["risk_class"] == "deviation"
    
def test_policy_size_limit():
    state = ProjectState(project_id="1", benchmark_id="b", repo_commit="c", phase="POLICY_CHECK", budgets={}, claims=[], paper_settings=[], repo_profile={})
    edits = []
    for i in range(25): # > 20 lines
        edits.append(Edit(file="train.py", op="append_line", new=f"print({i})"))
    
    prop = PatchProposal(id="p1", hypothesis_id="h1", type="code_typo", rationale="", evidence=[], alternatives_considered=[], edits=edits)
    
    res = check(state, prop)
    assert res["passed"] is False
    assert any("P3" in v for v in res["violations"])
