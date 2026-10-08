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

import pytest


@pytest.fixture(autouse=True)
def pin_llm_mode_to_live(monkeypatch):
    """Default every test to live mode so provider-level patching works as written."""
    import agent.llm as llm

    monkeypatch.setattr(llm, "LLM_MODE", "live", raising=False)
