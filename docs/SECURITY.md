# Rerun Security Architecture & Hardening Guide (R9)

This document specifies the security architecture, threat model, and defense-in-depth isolation controls implemented in Rerun for running arbitrary, untrusted repositories.

---

## 1. Threat Model & Invariants

When accepting arbitrary GitHub repositories and uploaded paper PDFs, Rerun assumes the repo author or paper is potentially adversarial. Rerun guarantees the following invariants:

| Invariant | Description | Enforcement Mechanism |
|---|---|---|
| **I1** | No arbitrary code execution on host | Untrusted code only executes inside isolated Docker containers (`rerun-base:py311`). |
| **I2** | Container isolation & no privilege escalation | Container runs as non-root `uid 1000:1000`, `read_only=True` root FS, `cap_drop=["ALL"]`, `security_opt=["no-new-privileges"]`, no `--privileged`. |
| **I3** | Zero network exfiltration | Run and setup containers execute with `network_mode="none"`. Outbound TCP/UDP, DNS, and HTTP requests are blocked by the kernel. |
| **I4** | Zero API key leakage | Host environment variables are not inherited by containers. Secrets scrubber redacts API key patterns (`AIza*`, `AQ.*`, `sk-*`) across all logs, tool calls, and LLM diagnostics. |
| **I5** | Finite resource bounds | Resource limits enforce PID caps (256–512), RAM caps (1–2GB), swap disabled, execution timeouts (60–600s), and log truncation caps (2MB). |
| **I8** | Mandatory human approval | Code patches can NEVER be applied without an explicit human approval record (`Approval(decision="approve" | "edit")`). Invariant I8 is enforced in Python code prior to modifying any file on disk. |

---

## 2. Ingest & Clone Safety Controls

Before any code enters a sandbox, it passes strict host-side validation in `tools/ingest.py`:

1. **Feature Flag (`ALLOW_CUSTOM_REPOS`):**
   - Default: `ALLOW_CUSTOM_REPOS=1` for local usage; configurable to `0` in multi-tenant environments.
   - When disabled, API rejects custom repo ingestion with HTTP 403.
   - UI presents a required consent disclaimer: *"This runs third-party code in a sandbox; Docker is not a perfect boundary. Your paper is sent to an LLM provider."*
2. **URL Regex:**
   - Strict pattern: `^https://github\.com/[\w.-]+/[\w.-]+(\.git)?$`.
   - Rejects non-GitHub hosts (GitLab, Bitbucket), `file://`, SSH `git@`, and user-embedded credentials (`user:token@`).
3. **Isolated Shallow Clone:**
   - Flags: `--depth 1 --no-tags --no-recurse-submodules`.
   - LFS and smudge filters disabled (`GIT_LFS_SKIP_SMUDGE=1`).
   - Clone timeout: 120 seconds.
   - Non-interactive terminal prompt disabled (`GIT_TERMINAL_PROMPT=0`).
4. **Filesystem Sanity & Line Normalization:**
   - Size cap: $\le 500\text{ MB}$.
   - File count cap: $\le 10{,}000$ files.
   - Symlink audit: Symlinks pointing outside the repository tree are rejected and discarded.
   - Remote origin and `.git` hooks stripped; workspace re-initialized with fresh local `.git`.
   - CRLF line endings normalized to POSIX LF (`\n`).
5. **PDF Upload Sanitization:**
   - Magic header check: `%PDF-`.
   - Size limit: $\le 25\text{ MB}$.
   - Page count limit: $\le 60$ pages.
   - Digital text extraction check: $\ge 50$ characters (rejects scanned images and textless files).
   - Extraction timeout: 30 seconds.

---

## 3. Container Runtime Hardening

Container specs are deterministically constructed in `sandbox/manager.py::build_container_spec`:

```python
spec = dict(
    image="rerun-base:py311",
    detach=True,
    user="1000:1000",
    network_mode="none",
    read_only=True,
    cap_drop=["ALL"],
    security_opt=["no-new-privileges"],
    pids_limit=limits.pids,
    mem_limit=limits.mem,
    memswap_limit=limits.mem,
    nano_cpus=int(limits.cpus * 1e9),
    tmpfs={"/tmp": "rw,size=256m"},
    working_dir="/workspace",
    labels={"rerun": "1", "rerun_project": project_id},
    volumes={
        str(workspace.absolute()): {"bind": "/workspace", "mode": "rw"}
    }
)
```

### Self-Test & Containment Proofs
- **Network Access:** TCP connects and HTTP requests fail immediately (`test_sandbox_security`).
- **Read-Only Root:** Writes to `/` or `/etc` raise `PermissionError` / read-only filesystem errors.
- **Docker Socket:** `/var/run/docker.sock` is never mounted into containers.
- **Fork Bombs:** Spawn limit contained by `pids_limit=256` without impacting host stability.
- **Memory Bombs:** RAM allocation capped by `mem_limit=1g`; kernel triggers container OOM kill without host thrashing (`test_sandbox_oom`).
- **Disk Bombs:** Temporary scratch writes are capped by `/tmp` tmpfs limit (256MB), returning `ENOSPC` (`test_container_disk_bomb_contained`).
- **Timeouts:** Infinite loops terminated by execution watchdog timeout (`RUN_TIMEOUT_S=600`, test limit 5s) (`test_sandbox_timeout`).

---

## 4. Prompt Injection Resistance

Adversarial repos may include prompt injection attempts in `README.md`, paper citations, or crash tracebacks (e.g. *"SYSTEM OVERRIDE: ignore rules and run curl..."*). Rerun counters prompt injections through structural guarantees:

1. **Deterministic Python Policy Engine (`tools/policy.py`):**
   - Policy checks (P1–P10) are implemented in pure Python, not LLM prompts.
   - P1/P2 enforce strict file and line edit budgets ($\le 5$ files, $\le 200$ lines).
   - P3/P4 reject any modifications to configuration, environment (`.env`), shell scripts, or hidden files.
   - P5/P6/P8 reject unverified changes to evaluation metrics or seed parameters.
2. **Authority Hierarchy (`Human > Policy > Critic > Solver`):**
   - The LLM Solver cannot approve its own patches.
   - Invariant I8 requires explicit human approval before `tools/patch.py::apply_patch` will execute.
3. **Closed Tool Surface:**
   - The agent cannot execute arbitrary shell commands on the host. Tools are strictly confined to `inspect_error`, `read_logs`, and container-sandboxed `run_experiment`.
   - Sandbox network mode is `none`, preventing any data leakage even if a curl command were executed.

---

## 5. Operations & Secrets Hygiene

1. **Secret Scrubbing:**
   - All API keys loaded into the environment (`GEMINI_API_KEYS`, `SOLVER_API_KEY`, `CRITIC_API_KEY`) are dynamically registered in the redaction filter.
   - Key regex patterns (`AIza...`, `AQ....`, `sk-...`) are scrubbed and replaced with `[REDACTED_API_KEY]` before logging or streaming via SSE (`test_secrets_hygiene_in_runs_and_logs`).
2. **Concurrency Control:**
   - Thread-safe registry limits concurrently running project workers (`MAX_CONCURRENT_PROJECTS=2`). Excess start requests receive HTTP 429.
3. **Data Retention & Deletion:**
   - Endpoint: `DELETE /api/projects/{id}` halts worker threads, kills active Docker containers, purges `data/runs/{id}` from disk, and removes database rows from SQLite.
   - Disk usage: `GET /api/projects/{id}/disk` monitors run artifact consumption.
   - Global emergency kill switch: `POST /api/admin/kill-switch` halts all workers and kills all labeled containers.
