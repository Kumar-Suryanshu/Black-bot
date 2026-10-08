import pytest
import os
from backend.app.main import startup_event

def test_startup_refuses_fake_sandbox_without_allow_flag(monkeypatch):
    monkeypatch.setenv("SANDBOX_TYPE", "fake")
    monkeypatch.delenv("ALLOW_FAKE_SANDBOX", raising=False)
    with pytest.raises(RuntimeError, match="Refusing to start API with SANDBOX_TYPE=fake without ALLOW_FAKE_SANDBOX=1"):
        startup_event()

def test_startup_allows_fake_sandbox_with_allow_flag(monkeypatch):
    monkeypatch.setenv("SANDBOX_TYPE", "fake")
    monkeypatch.setenv("ALLOW_FAKE_SANDBOX", "1")
    # Should not raise RuntimeError
    startup_event()

def test_startup_allows_default_docker_sandbox(monkeypatch):
    monkeypatch.delenv("SANDBOX_TYPE", raising=False)
    monkeypatch.delenv("ALLOW_FAKE_SANDBOX", raising=False)
    startup_event()
