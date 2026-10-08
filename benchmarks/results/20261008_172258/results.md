# Track A Benchmark Evaluation Results

**Timestamp:** 2026-10-08 17:23:06 UTC
**Sandbox:** Docker (`DockerSandbox`, image: `rerun-base:py311`, offline network)
**Repeats:** 1 per condition

## Summary Table (Counts Only)

| Case | Gold Expected | B-0 |
|---|---|---|
| `b1_control` | `REPRODUCED` | 1/1 (REPRODUCED) |
| `b2_dependency` | `REPRODUCED` | 0/1 (FAILED_TO_RUN) |
| `b3_silent_config` | `REPRODUCED` | 0/1 (NUMBER_MISMATCH) |
| `b4_combined` | `REPRODUCED` | 0/1 (FAILED_TO_RUN) |
| `b5_unable` | `UNABLE_TO_EXECUTE` | 1/1 (UNABLE_TO_EXECUTE) |

## Total Success Counts

- **B-0**: 2/5 runs matched gold (40.0%)

## Detailed Per-Run Log

| Case | System | Run | Final Status | Matches Gold | Patches | Retries | Time (s) |
|---|---|---|---|---|---|---|---|
| `b1_control` | B-0 | 1 | `REPRODUCED` | True | 0 | 0 | 2.05 |
| `b2_dependency` | B-0 | 1 | `FAILED_TO_RUN` | False | 0 | 0 | 1.79 |
| `b3_silent_config` | B-0 | 1 | `NUMBER_MISMATCH` | False | 0 | 0 | 2.17 |
| `b4_combined` | B-0 | 1 | `FAILED_TO_RUN` | False | 0 | 0 | 1.95 |
| `b5_unable` | B-0 | 1 | `UNABLE_TO_EXECUTE` | True | 0 | 0 | 0.01 |
