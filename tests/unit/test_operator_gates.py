"""
Regression tests for the operator-facing gates.

Two defects made the dashboard unable to do its job:

1. get_pending_approval returned `reviews` as a list and no `requires_extra_confirm`, while
   the dashboard read `critic_review` and `requires_extra_confirm`. Both were undefined, so
   the confirmation checkbox never rendered, while process_approval rejected any approve on a
   bannered patch for lack of confirm_extra. Bannered patches, which are exactly the
   high-stakes ones (critic unavailable, critic objecting, deny-list deviation), could
   therefore never be approved.

2. The run-log endpoint hardcoded run_<n>.log, but a failed dependency install writes
   setup_<n>.log, so the terminal 404'd precisely when there was an install error to read.
"""

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import backend.app.routes as routes
import backend.app.runner as runner
from agent.state import Approval, Attempt, CriticReview, Edit, PatchProposal, ProjectState
from backend.app.db import save_project_state
from backend.app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def no_background_workers(monkeypatch):
    """These tests exercise the HTTP contract, not the orchestrator thread."""
    monkeypatch.setattr(runner, "start_project_worker", lambda pid: True)
    monkeypatch.setattr(routes, "start_project_worker", lambda pid: True)


def _state_with_pending_approval(project_id: str, banner, requires_extra_confirm: bool):
    state = ProjectState(
        project_id=project_id, benchmark_id="b1_control", repo_commit="c1",
        phase="APPROVAL", budgets={"steps_used": 1}, claims=[], paper_settings=[],
        repo_profile={},
    )
    state.patches = [PatchProposal(
        id="P-1", hypothesis_id="H-1", type="dependency",
        rationale="ModuleNotFoundError: No module named 'yaml'",
        evidence=["E-001"], alternatives_considered=[],
        edits=[Edit(file="requirements.txt", op="append_line", new="PyYAML==6.0.1")],
        diff="--- a/requirements.txt\n+++ b/requirements.txt\n",
        policy_result={
            "passed": True, "violations": [], "risk_class": "environment_fix",
            "flags": [], "requires_extra_confirm": requires_extra_confirm,
        },
    )]
    state.critic_reviews = [CriticReview(
        id="R-1", patch_id="P-1", round=1, verdict="SUPPORTED",
        checks={"cause_is_cited_and_exists": True}, verified_evidence=[],
        objections=[], required_changes=[], confidence="high", model="stub",
    )]
    state.pending = {"kind": "approval", "id": f"A-{project_id}", "patch_id": "P-1", "banner": banner}
    save_project_state("data/rerun.db", project_id, "b1_control", "c1", "APPROVAL", state)
    return state


def test_pending_approval_exposes_the_fields_the_ui_needs():
    """The payload must carry the critic review and the confirmation requirement."""
    _state_with_pending_approval("P-GATE-1", banner="no_independent_review", requires_extra_confirm=False)
    try:
        res = client.get("/api/projects/P-GATE-1/approvals/pending")
        assert res.status_code == 200
        body = res.json()

        # The review history, plus a single-object convenience form.
        assert isinstance(body["reviews"], list) and len(body["reviews"]) == 1
        assert body["critic_review"] is not None
        assert body["critic_review"]["verdict"] == "SUPPORTED"

        # A banner alone must demand explicit confirmation.
        assert body["requires_extra_confirm"] is True
        assert body["banner"] == "no_independent_review"

        # The patch's evidence is exposed under the name the backend model uses.
        assert body["patch"]["evidence"] == ["E-001"]
    finally:
        client.delete("/api/projects/P-GATE-1")


def test_policy_can_require_confirmation_without_a_banner():
    """requires_extra_confirm also comes from the policy result, not only from a banner."""
    _state_with_pending_approval("P-GATE-2", banner=None, requires_extra_confirm=True)
    try:
        body = client.get("/api/projects/P-GATE-2/approvals/pending").json()
        assert body["banner"] is None
        assert body["requires_extra_confirm"] is True
    finally:
        client.delete("/api/projects/P-GATE-2")


def test_bannered_patch_can_actually_be_approved():
    """
    The end-to-end gate: a bannered patch rejects an unconfirmed approve and accepts a
    confirmed one. Previously the UI could never send confirm_extra, so this was a dead end.
    """
    _state_with_pending_approval("P-GATE-3", banner="critic_objects", requires_extra_confirm=True)
    try:
        refused = client.post("/api/approvals/A-P-GATE-3", json={
            "decision": "approve", "comment": "", "confirm_extra": False,
        })
        assert refused.status_code == 400
        assert "confirmation" in refused.json()["detail"].lower()

        accepted = client.post("/api/approvals/A-P-GATE-3", json={
            "decision": "approve", "comment": "verified against Figure 2", "confirm_extra": True,
        })
        assert accepted.status_code == 200, accepted.json()
    finally:
        client.delete("/api/projects/P-GATE-3")


def test_log_route_serves_a_failed_install_attempt():
    """A setup_<n>.log attempt must be served, not 404'd."""
    project_id = "P-SETUPLOG"
    log_dir = Path("data") / "runs" / project_id / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    (log_dir / "setup_1.log").write_text("ERROR: Could not find a version that satisfies torch\n")

    state = ProjectState(
        project_id=project_id, benchmark_id="b1_control", repo_commit="c1",
        phase="OBSERVE", budgets={}, claims=[], paper_settings=[], repo_profile={},
    )
    state.attempts = [Attempt(
        n=1, patches_applied=[], exit_code=1, started_at="now",
        log_path=str(log_dir / "setup_1.log"),
    )]
    save_project_state("data/rerun.db", project_id, "b1_control", "c1", "OBSERVE", state)

    try:
        res = client.get(f"/api/projects/{project_id}/logs/1")
        assert res.status_code == 200, res.json()
        assert "Could not find a version" in res.json()["log"]
        # Response shape is a fixed contract.
        assert set(res.json().keys()) == {"log"}
    finally:
        client.delete(f"/api/projects/{project_id}")


def test_log_route_does_not_serve_a_different_attempts_log():
    """Asking for attempt 1 must never return the latest attempt's log."""
    project_id = "P-LOGMIX"
    log_dir = Path("data") / "runs" / project_id / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    (log_dir / "run_1.log").write_text("FIRST ATTEMPT\n")
    (log_dir / "run_2.log").write_text("SECOND ATTEMPT\n")

    state = ProjectState(
        project_id=project_id, benchmark_id="b1_control", repo_commit="c1",
        phase="OBSERVE", budgets={}, claims=[], paper_settings=[], repo_profile={},
    )
    # Attempt 1 has no recorded log_path; the latest pointer references attempt 2.
    state.attempts = [
        Attempt(n=1, patches_applied=[], exit_code=1, started_at="now"),
        Attempt(n=2, patches_applied=[], exit_code=0, started_at="now",
                log_path=str(log_dir / "run_2.log")),
    ]
    state.latest_log_path = str(log_dir / "run_2.log")
    save_project_state("data/rerun.db", project_id, "b1_control", "c1", "OBSERVE", state)

    try:
        body = client.get(f"/api/projects/{project_id}/logs/1").json()
        assert "FIRST ATTEMPT" in body["log"]
        assert "SECOND ATTEMPT" not in body["log"]
    finally:
        client.delete(f"/api/projects/{project_id}")


# ---------------------------------------------------------------------------
# handle_approval patch resolution (regression)
#
# Resolving the patch strictly from state.pending broke every caller that clears `pending`
# as it records the decision -- notably scripts/run_case.py. The run then logged
# "APPROVAL phase has no patch matching pending patch_id None", fell through to DIAGNOSE and
# finished UNABLE_TO_EXECUTE with the patch never applied.
#
# The fake sandbox cannot catch this: FakeSandbox always exits 0, so b2_dependency never
# reaches the patch path there. It was found by running the case in a real container.
# ---------------------------------------------------------------------------

import datetime

import agent.loop as loop


def _approval_state(pending):
    state = ProjectState(
        project_id="P-APPROVAL-RESOLVE", benchmark_id="b2_dependency", repo_commit="c1",
        phase="APPROVAL", budgets={"steps_used": 1}, claims=[], paper_settings=[],
        repo_profile={},
    )
    state.patches = [PatchProposal(
        id="P-1", hypothesis_id="H-1", type="dependency",
        rationale="ModuleNotFoundError: No module named 'yaml'",
        evidence=["E-001"], alternatives_considered=[],
        edits=[Edit(file="requirements.txt", op="append_line", new="PyYAML==6.0.1")],
    )]
    state.approvals = [Approval(
        id="A-1", patch_id="P-1", decision="approve", by="headless_approver",
        at=datetime.datetime.now().isoformat(),
    )]
    state.pending = pending
    return state


def test_approval_proceeds_when_pending_names_the_patch():
    state = _approval_state({"kind": "approval", "id": "A-1", "patch_id": "P-1", "banner": None})
    loop.handle_approval(state, {})
    assert state.phase == "PATCH_APPLY"


def test_approval_proceeds_when_the_caller_already_cleared_pending():
    """The headless runner clears pending before re-entering run_project."""
    state = _approval_state(None)
    loop.handle_approval(state, {})
    assert state.phase == "PATCH_APPLY", (
        "approval stalled because pending was cleared; the patch is never applied"
    )


def test_approval_prefers_the_patch_named_by_pending_over_the_newest():
    """When pending names a patch, an unrelated newer patch must not be acted on."""
    state = _approval_state({"kind": "approval", "id": "A-1", "patch_id": "P-1", "banner": None})
    state.patches.append(PatchProposal(
        id="P-2", hypothesis_id="H-2", type="config_value", rationale="unrelated later patch",
        evidence=["E-002"], alternatives_considered=[],
        edits=[Edit(file="configs/default.yaml", op="replace_text", old="a: 1", new="a: 2")],
    ))
    loop.handle_approval(state, {})
    # P-1 is the approved one, so the run advances; P-2 must be untouched.
    assert state.phase == "PATCH_APPLY"
    assert state.patches[1].status == "proposed"


def test_approval_with_no_candidate_patch_does_not_stall():
    state = _approval_state(None)
    state.patches = []
    loop.handle_approval(state, {})
    assert state.phase == "DIAGNOSE"
