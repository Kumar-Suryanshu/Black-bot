import json
import pytest
from pydantic import BaseModel
from pathlib import Path

from agent.llm import call, set_fake_llm, set_event_listener, LLMOutputInvalid
from agent.config import scrub_secrets
from tests.agent.fakes import FakeLLM

class SampleModel(BaseModel):
    name: str
    count: int

def test_llm_call_success():
    fake = FakeLLM([
        ("solver", "test_mode", {"name": "test_agent", "count": 42})
    ])
    set_fake_llm(fake)
    
    res = call("solver", "test_mode", {"foo": "bar"}, SampleModel)
    assert isinstance(res, SampleModel)
    assert res.name == "test_agent"
    assert res.count == 42

def test_llm_reprompt_on_invalid_json():
    # First response invalid json, second response valid
    fake = FakeLLM([
        ("solver", "test_mode", "This is not json at all!"),
        ("solver", "test_mode", {"name": "fixed_agent", "count": 10})
    ])
    set_fake_llm(fake)
    
    res = call("solver", "test_mode", {"foo": "bar"}, SampleModel)
    assert res.name == "fixed_agent"
    assert res.count == 10

def test_llm_fails_after_reprompt():
    # Both responses invalid
    fake = FakeLLM([
        ("solver", "test_mode", "Invalid first"),
        ("solver", "test_mode", "Invalid second")
    ])
    set_fake_llm(fake)
    
    with pytest.raises(LLMOutputInvalid):
        call("solver", "test_mode", {"foo": "bar"}, SampleModel)

def test_secret_scrubbing():
    dirty_text = "Here is my secret: sk-1234567890abcdef12345678 and token = 'secret12345'"
    clean_text = scrub_secrets(dirty_text)
    assert "sk-1234567890abcdef12345678" not in clean_text
    assert "[REDACTED_SECRET]" in clean_text

def test_replay_mode_miss(tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_MODE", "replay")
    monkeypatch.setenv("CASSETTE_DIR", str(tmp_path))
    
    import agent.config as config
    monkeypatch.setattr(config, "LLM_MODE", "replay")
    monkeypatch.setattr(config, "CASSETTE_DIR", str(tmp_path))
    
    from agent import llm
    monkeypatch.setattr(llm, "LLM_MODE", "replay")
    monkeypatch.setattr(llm, "CASSETTE_DIR", str(tmp_path))
    
    with pytest.raises(RuntimeError, match="Cassette miss"):
        call("solver", "unknown_mode", {"a": 1}, SampleModel)

def test_cassette_record_and_replay(tmp_path, monkeypatch):
    cassette_dir = str(tmp_path / "cassettes")
    from agent import llm
    
    # 1. Record mode
    monkeypatch.setattr(llm, "LLM_MODE", "record")
    monkeypatch.setattr(llm, "CASSETTE_DIR", cassette_dir)
    
    fake = FakeLLM([
        ("solver", "record_test", {"name": "saved_agent", "count": 99})
    ])
    set_fake_llm(fake)
    
    res = call("solver", "record_test", {"test_key": "val"}, SampleModel, benchmark_id="test_bench")
    assert res.name == "saved_agent"
    
    # 2. Replay mode
    monkeypatch.setattr(llm, "LLM_MODE", "replay")
    set_fake_llm(None) # Ensure fake is not called
    
    replayed = call("solver", "record_test", {"test_key": "val"}, SampleModel, benchmark_id="test_bench")
    assert replayed.name == "saved_agent"
    assert replayed.count == 99

