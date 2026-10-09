"""
Shared pytest fixtures.

`agent.llm.LLM_MODE` is read from the environment at import time, so the ambient value of
LLM_MODE in a developer shell or in CI silently changes how `agent.llm.call` behaves. Tests
that patch `agent.llm.execute_provider_request` need the live code path, because the replay
branch short-circuits and raises "Cassette miss" before any provider dispatch happens.

Pinning the mode here makes the suite deterministic regardless of the ambient environment.
Tests that genuinely exercise record/replay override it with
`monkeypatch.setattr(llm, "LLM_MODE", ...)`, which is the pattern already used by
tests/agent/test_llm.py.
"""

import shutil
import tempfile
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def pin_llm_mode_to_live(monkeypatch):
    """Default every test to live mode so provider-level patching works as written."""
    import agent.llm as llm

    monkeypatch.setattr(llm, "LLM_MODE", "live", raising=False)


@pytest.fixture(autouse=True, scope="session")
def isolate_database_from_the_running_app():
    """
    Never let the suite touch data/rerun.db.

    tests/e2e/test_b4_api.py called os.remove("data/rerun.db"), and several other tests
    write project rows straight into it, so a full test run destroyed every real project in
    the database the dev server is serving. The suite now runs against a scratch database
    for its whole session.
    """
    import tempfile

    from backend.app import db as app_db

    tmp_dir = tempfile.mkdtemp(prefix="rerun_test_db_")
    app_db.set_db_path_override(str(Path(tmp_dir) / "rerun.db"))
    try:
        yield
    finally:
        app_db.set_db_path_override(None)
        shutil.rmtree(tmp_dir, ignore_errors=True)


@pytest.fixture(autouse=True, scope="session")
def isolate_run_artifacts_from_the_real_data_dir():
    """
    Never let the suite write into data/runs/.

    Tests used fixed project ids ("P-GATE-1", "b1_control", ...) and wrote workspaces,
    wheelhouses, logs and evidence straight into the directory the dev server serves. Two
    consequences, both real: data/runs grew to tens of gigabytes of test leftovers, and a
    test could pass on a directory some earlier run had created rather than on anything it
    set up itself -- so the suite was not trustworthy from a clean checkout.

    Everything resolves run paths through `tools.paths`, so one redirect covers the suite.
    """
    from tools import paths as run_paths

    # Deliberately on disk rather than under /tmp: pip unpacks wheels into TMPDIR inside the
    # setup container, that TMPDIR is bind-mounted out of the run directory, and a RAM-backed
    # /tmp runs out of space installing torch or scikit-learn.
    scratch_parent = Path("data") / ".pytest-runs"
    scratch_parent.mkdir(parents=True, exist_ok=True)
    tmp_dir = tempfile.mkdtemp(prefix="runs_", dir=str(scratch_parent))
    run_paths.set_runs_root(tmp_dir)
    try:
        yield
    finally:
        run_paths.set_runs_root(None)
        shutil.rmtree(tmp_dir, ignore_errors=True)
