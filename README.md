# Rerun

**Rerun** is an autonomous AI coding agent designed to verify if code from a research paper reproduces the claimed headline numbers.

## Limits and Capabilities
- The system runs code exclusively in a **hardened, network-isolated Docker sandbox** (`network_mode="none"`, non-root, read-only root).
- **No secrets or credentials** enter the sandbox or appear in logs/artifacts.
- Strict authority hierarchy enforced by plain Python code:
  $$\text{Human} > \text{Policy Checker (Code)} > \text{Critic (LLM)} > \text{Solver (LLM)}$$
- The AI **cannot** execute code directly, apply patches without explicit human approval, write evidence itself, type metrics, or determine the final status.
- Final reproduction status (`REPRODUCED`, `NOT_REPRODUCED`, `UNABLE_TO_EXECUTE`, `INCONCLUSIVE`) is computed deterministically from measured data.

## Current Status
- **Stages 0–9 Completed**: Core scaffolding, testing grounds, AI agent loop (Solver, Critic, Arbiter), and FastAPI backend are fully implemented and tested.
- **56/59 tests passing** (3 correctly skipped — Docker tests when Docker Desktop is not running).
- **Next Steps**: Stage 10 (Frontend React Dashboard).

## Quickstart
1. Review `.env.example` and set up your `.env`.
2. Run `make setup`
3. Run `make images`
4. Run `make wheelhouse`
5. Run `python scripts/dev.py build-benchmarks` (or `make seed-faults`)
6. Run `python scripts/dev.py test` to verify unit and agent test suites
7. Run `python scripts/dev.py adversarial` to run attack fixtures X1–X9
8. Run `make api` and start exploring.

## Core Components
- **`agent/llm.py`**: Unified multi-provider LLM interface supporting OpenAI-compatible endpoints, Anthropic, FakeLLM, and Cassette Record/Replay with automated fallback and secret scrubbing.
- **`agent/loop.py`**: Orchestrator executing the 20-phase state machine with budget guards and safety-net nudges.
- **`tools/policy.py`**: Deterministic policy checker enforcing rules P1–P10, hard limits (≤ 5 files, ≤ 200 lines), and guarded sensitive keys.
- **`agent/critic/review.py` & `agent/arbiter.py`**: Independent review packet verification and decision escalation table.
- **`benchmarks/adversarial/`**: Attack fixtures X1–X9 testing metric chasing, sensitive key locking, oversized patches, and hallucinated evidence.

## Folder Structure

```text
.
├── agent
│   ├── config.py
│   ├── events.py
│   ├── llm.py
│   ├── loop.py
│   ├── arbiter.py
│   ├── state.py
│   ├── solver
│   │   ├── prompts.py
│   │   └── schemas.py
│   └── critic
│       ├── prompts.py
│       ├── schemas.py
│       └── review.py
├── backend
│   ├── app
│   │   ├── main.py
│   │   ├── routes.py
│   │   ├── runner.py
│   │   ├── sse.py
│   │   ├── db.py
│   │   ├── models.py
│   │   └── __init__.py
│   └── __init__.py
├── benchmarks
│   ├── adversarial/
│   ├── baselines/
│   ├── cases/
│   ├── gold/
│   ├── papers/
│   ├── template/
│   ├── registry.json
│   └── run_bench.py
├── docs/
├── sandbox
│   ├── cleanup.py
│   ├── limits.py
│   ├── manager.py
│   └── images/
├── scripts
│   ├── dev.py
│   ├── export_digits.py
│   ├── calibrate_benchmark.py
│   ├── seed_faults.py
│   ├── make_papers.py
│   └── run_adversarial.py
├── tests
│   ├── agent
│   │   ├── fakes.py
│   │   ├── test_llm.py
│   │   ├── test_loop.py
│   │   └── test_critic.py
│   ├── e2e
│   │   └── test_b4_api.py
│   ├── security
│   │   └── test_selftest.py
│   └── unit
│       ├── test_arbiter.py
│       ├── test_compare.py
│       ├── test_config_audit.py
│       ├── test_contracts.py
│       ├── test_errors.py
│       ├── test_evidence.py
│       ├── test_gpu_mode.py
│       ├── test_policy.py
│       ├── test_results.py
│       └── test_status.py
└── tools
    ├── compare.py
    ├── config_audit.py
    ├── errors.py
    ├── evidence.py
    ├── exec_tools.py
    ├── paper.py
    ├── patch.py
    ├── policy.py
    ├── preflight.py
    ├── registry.py
    ├── repo.py
    ├── results.py
    └── status.py
```
