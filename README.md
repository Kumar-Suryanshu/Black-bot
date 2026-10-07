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
- **Stages 0–11 Completed**: Core agent architecture, hardened sandboxing, deterministic policy engine, 9-point Critic & Arbiter, FastAPI REST/SSE backend, Stage 11 deterministic report generator and verifier engine, and the complete React/Vite/Tailwind Frontend with custom 7-scene torn paper scroll animation engine.
- **65/68 tests passing** (3 security sandbox tests safely skipped when Docker Desktop daemon is not running) across unit, agent, e2e API, and report verifier test suites.
- **Frontend Build**: Zero-warning TypeScript build (`npm run build`) in ~600ms.

## Quickstart

### 1. Backend Setup
1. Configure your environment variables in `.env` (including your `SOLVER_API_KEY`).
2. Run `make setup` (or `pip install -r requirements.txt`)
3. Run `make images`
4. Run `make wheelhouse`
5. Run `python scripts/dev.py build-benchmarks` (or `make seed-faults`)
6. Run `python scripts/dev.py test` (or `pytest tests -v`) to verify all unit, agent, and API test suites
7. Run `python scripts/dev.py adversarial` to run attack fixtures X1–X9
8. Run `make api` (or `python -m uvicorn backend.app.main:app --port 8000`)

### 2. Frontend Launch
1. `cd frontend`
2. `npm install`
3. `npm run dev` (runs on `http://localhost:5173`)
4. Visit `http://localhost:5173` for the landing page with interactive torn-paper scroll animation, `/new` to initiate a paper verification run, `/p/:id` for the live operational console, or `/p/:id/report` for the certified reproduction report.

## Core Components
- **`agent/llm.py`**: Unified multi-provider LLM interface supporting Gemini API and Cassette Record/Replay with automated fallback and secret scrubbing.
- **`agent/loop.py`**: Orchestrator executing the 20-phase state machine with budget guards and safety-net nudges.
- **`tools/policy.py`**: Deterministic policy checker enforcing rules P1–P10, hard limits (≤ 5 files, ≤ 200 lines), and guarded sensitive keys.
- **`agent/critic/review.py` & `agent/arbiter.py`**: Independent review packet verification and decision escalation table.
- **`tools/report.py`**: Deterministic report generation and verifier engine enforcing rules V1–V7, placeholder resolution, unpatched vs. patched metric comparison, and Markdown/HTML/JSON exports.
- **`backend/`**: FastAPI service exposing 13 REST routes, SSE live-tail event bus, and `/api/projects/{id}/report[.md|.html]` download routes.
- **`frontend/`**: React 18 + Vite + Tailwind + GSAP client featuring an archival Field Desk & Kraft Paper design system, Mulberry32 procedural tear seams, live operational console, and certified report.
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
├── frontend
│   ├── src
│   │   ├── api/
│   │   ├── components/
│   │   │   ├── dashboard/
│   │   │   ├── landing/
│   │   │   ├── layout/
│   │   │   └── ui/
│   │   ├── landing/
│   │   │   ├── engine/
│   │   │   ├── illustrations/
│   │   │   └── scenes/
│   │   ├── pages/
│   │   └── styles/
│   ├── index.html
│   ├── package.json
│   └── vite.config.ts
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
│       ├── test_patch.py
│       ├── test_policy.py
│       ├── test_report_verifier.py
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
    ├── report.py
    ├── results.py
    └── status.py
```
