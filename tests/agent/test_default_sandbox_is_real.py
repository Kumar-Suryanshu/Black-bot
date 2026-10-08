import os
from agent.loop import get_sandbox, set_sandbox

def test_default_sandbox_is_not_fake(monkeypatch):
    """Stage 1 gate: default sandbox must be DockerSandbox when SANDBOX_TYPE is unset."""
    monkeypatch.delenv("SANDBOX_TYPE", raising=False)
    set_sandbox(None)
    sb = get_sandbox()
    assert type(sb).__name__ == "DockerSandbox", (
        f"Default sandbox must be DockerSandbox in the live app path, got {type(sb).__name__}."
    )
