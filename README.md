# Rerun — Autonomous Research Paper Reproducibility Agent

Rerun is an autonomous AI agent engineered to verify whether code from published research papers faithfully reproduces stated headline results. Rerun investigates failures, repairs environment and configuration bugs, and produces verifier-certified reproduction reports and self-contained reproduction kits.

---

## ⚠️ Limits & Honest Boundary Disclosures (First)

Before exploring capabilities, understand Rerun's strict operational boundaries:
1. **Network-Isolated Execution (Invariant I3):** All code executes inside hardened Docker containers (`rerun-base:py311`) with `network_mode="none"`. The agent cannot fetch external data, weights, or packages from the internet at runtime.
2. **Mandatory Human-in-the-Loop (Invariant I8):** The AI **cannot** apply patches to disk or alter code autonomously without explicit human approval. Patch diffs must pass deterministic policy checks (P1–P10) and an independent 9-point Critic checklist before human sign-off.
3. **Hard Authority Hierarchy:**
   $$\text{Human} > \text{Policy Engine (Code)} > \text{Critic (LLM)} > \text{Solver (LLM)}$$
   The AI cannot determine its own reproduction verdict, write evidence arbitrarily, or bypass resource limits.
4. **Finite Resource Ceilings:** 40 orchestrator steps, 3 code patches, $\le 5$ files modified per patch, $\le 200$ changed lines, 600s container timeout, 2 CPUs, 2GB RAM, and 256 PIDs.
5. **Hardware Constraints:** GPU acceleration is strictly opt-in (`GPU_ENABLED=false` by default). CUDA-dependent papers that require GPU hardware are detected at triage and flagged as infeasible on CPU-only infrastructure.
6. **Selection Bias Counterweight:** Track A synthetic benchmark cases (B1–B5) were calibrated by the author team. Track B (Real-Repo Evaluation across 6 real peer-reviewed papers from NeurIPS, ICML, ACL, AAAI, ECCV, ICLR) serves as the necessary external counterweight, openly disclosing failures when code and paper genuinely diverge.

---

## Current Status & Tiers Reached

- **Tier 1 (Internal Autonomous Loop):** **COMPLETED & VERIFIED.** All synthetic benchmark cases (B1–B5) execute in real Docker sandboxes with 100% reproducibility matching gold contracts.
- **Tier 2 (Real-World Research Paper Evaluation — Track B):** **COMPLETED & VERIFIED.** Evaluated across 6 real ML papers with honest failure disclosure (3 reproduced, 1 divergent, 2 triaged out) achieving a **5.5x speedup** over human baselines.
- **Test Suite Status:** **186 passed**, 0 failed (100% test suite pass rate).
- **Frontend Status:** React 18 + Vite + Tailwind dashboard with 7-scene procedural torn-paper scroll engine; zero TypeScript/Vite build errors.

---

## Execution Modes & Badges

| Dimension | Option A | Option B | Option C |
|:---|:---|:---|:---|
| **Input Source** | `[Benchmark]` Built-in calibrated cases B1–B5 | `[Custom]` Arbitrary public GitHub repo + uploaded paper PDF | — |
| **LLM Mode** | `[Live]` Real Gemini API queries | `[Replay]` Deterministic cassette playback (zero API quota used) | — |
| **Sandbox Type**| `[Docker]` Real isolated Linux containers (`rerun-base:py311`) | `[Fake]` In-memory test sandbox (`ALLOW_FAKE_SANDBOX=1`) | — |
| **Run Banner**  | `[Verified]` Real container execution | `[Simulated]` Displayed when run under mock sandbox | — |

---

## Quickstart

### 1. Prerequisites
- Linux / macOS (or WSL2 on Windows)
- Python 3.11+
- Docker Engine / Docker Desktop active
- Node.js 18+ and npm

### 2. Backend Setup
```bash
# Clone and enter directory
git clone https://github.com/your-org/rerun.git
cd rerun

# Set up virtual environment and dependencies
pip install -r requirements-dev.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your SOLVER_API_KEY (optional if running in LLM_MODE=replay)

# Build base Docker sandbox image
python3 scripts/dev.py images

# Verify security sandbox boundaries (non-root, read-only root, no network)
python3 scripts/dev.py hardened-smoke

# Run full non-Docker and Docker test suite (186 tests)
pytest tests/ -q

# Start FastAPI backend server (port 8000)
python3 -m uvicorn backend.app.main:app --port 8000
```

### 3. Frontend Launch
```bash
cd frontend
npm install
npm run build   # Production bundle verification
npm run dev     # Starts Vite dev server on http://localhost:5173
```
Open [http://localhost:5173](http://localhost:5173) in your browser:
- `/`: Interactive torn-paper narrative landing page.
- `/new`: Postcard claim intake and custom repo launcher.
- `/p/:id`: Live operational console with real-time SSE event streaming, container logs, and patch approval modal.
- `/p/:id/report`: Verifier-certified reproduction report with interactive comparison charts and self-contained ZIP download.

---

## Empirical Evaluation Summary

### Track A: Synthetic Fault Benchmark Sweep
Evaluated across 3 repeats per case using real Docker sandboxes (`rerun-base:py311`):

| Case | Title | Gold Expected | B-0 (No Agent) | B-2 (One-Shot) | Rerun (Autonomous) |
|:---|:---|:---:|:---:|:---:|:---:|
| `b1_control` | Clean Implementation | `REPRODUCED` | 3/3 | 3/3 | **3/3 (100%)** |
| `b2_dependency`| Missing PyYAML | `REPRODUCED` | 0/3 | 3/3 | **3/3 (100%)** |
| `b3_silent_config`| Bad Learning Rate | `REPRODUCED` | 0/3 | 3/3 | **3/3 (100%)** |
| `b4_combined`| Dependency + Bad LR | `REPRODUCED` | 0/3 | 0/3 | **3/3 (100%)** |
| `b5_unable` | Mandatory CUDA GPU | `UNABLE_TO_EXECUTE`| 3/3 | 3/3 | **3/3 (100%)** |
| **Total** | — | — | **40.0%** | **80.0%** | **15/15 (100%)** |

### Track B: Real Peer-Reviewed Paper Evaluation
Evaluated across 6 independent real papers from NeurIPS, ICML, ACL, AAAI, ECCV, and ICLR:

| Case ID | Paper & Venue | Human Time | Rerun Time | Outcome | Failure Mode Taxonomy |
|:---|:---|:---:|:---:|:---:|:---|
| `real_case_snake` | Snake Activation (NeurIPS 2020) | 14.5 min | 3.2 min | `reproduced` | `non-determinism within tolerance` |
| `real_case_eldr` | ELDR Point Explanations (ICML 2020) | 38.0 min | 6.8 min | `reproduced` | `dependency not available as wheel` (fixed) |
| `real_case_deceptive_attention`| Deceptive Attention (ACL 2020) | 22.0 min | 5.1 min | `reproduced` | `non-determinism within tolerance` |
| `real_case_fairness_attack` | Fairness Attacks (AAAI 2021) | 31.0 min | 7.4 min | `not reproduced` | `paper/code genuinely diverge` |
| `real_case_faircal` | FairCal Face Verification (ICLR 2022)| 18.0 min | 1.2 min | `correctly triaged out`| `data/weights missing` |
| `real_case_cartoonx` | CartoonX Explanations (ECCV 2022) | 15.0 min | 1.4 min | `correctly triaged out`| Hardware constraint (GPU required) |
| **Total** | **6 Real ML Papers** | **138.5 min** | **25.1 min** | **6/6 valid** | **5.5x Speedup** (81.9% time saved) |

---

## Frequently Asked Questions (Judge Q&A)

### Q: Does Rerun work on real, uncurated machine learning repositories?
**A:** Yes. Track B evaluated 6 real, independently published machine learning papers from major venues (NeurIPS, ICML, ACL, AAAI, ECCV, ICLR) and public GitHub repositories. Rerun successfully reproduced clean experiments in Snake and Deceptive Attention, repaired stale NumPy/PyTorch environment deprecations in ELDR, accurately triaged out infeasible missing datasets (FairCal) and GPU prerequisites (CartoonX), and honestly identified genuine scientific divergences in Fairness Attacks without hallucinating false successes.

### Q: How does Rerun handle dependencies and package installations offline?
**A:** Rerun provisions an offline wheelhouse cache containing pre-verified wheels. When a missing dependency error occurs (`ModuleNotFoundError`), the Solver identifies the missing package, the Policy engine verifies it does not alter sensitive libraries, and the setup container mounts the wheelhouse with `--no-index --find-links` to install the package without external network access.

### Q: How does Rerun prevent the LLM from cheating or falsifying numbers?
**A:** Strict separation of responsibilities:
1. Metrics are extracted exclusively by Python parsers from container output files (`outputs/results.json`) or stdout regex matches.
2. The comparison engine computes delta and tolerance in pure Python; the LLM never determines whether a metric matches.
3. The Deterministic Report Verifier (rules V1–V7) strips any report statement containing numbers that do not match recorded evidence or claims.
4. Final status determination is computed deterministically by `tools/status.py`.

### Q: What is the self-contained reproduction kit?
**A:** Any completed run provides a one-click download of `rerun_kit.zip` via `GET /api/projects/{id}/kit`. The kit contains the exact git commit SHA, `reproduce.md` terminal instructions, unified patches (`patches/*.diff`), raw logs (`logs/`), results (`results/`), and the verifier-certified HTML/Markdown report, enabling third-party verification without needing Rerun installed.

---

## License
Licensed under the [Apache License, Version 2.0](LICENSE).
