# Track A Benchmark Evaluation Results

**Timestamp:** 2026-10-08 17:27:30 UTC
**Sandbox:** Docker (`DockerSandbox`, image: `rerun-base:py311`, offline network)
**Repeats:** 3 per condition

## Summary Table (Counts Only)

| Case | Gold Expected | B-0 | B-2 | Rerun |
|---|---|---|---|---|
| `b1_control` | `REPRODUCED` | 3/3 (REPRODUCED) | 3/3 (REPRODUCED) | 3/3 (REPRODUCED) |
| `b2_dependency` | `REPRODUCED` | 0/3 (FAILED_TO_RUN) | 3/3 (REPRODUCED) | 3/3 (REPRODUCED) |
| `b3_silent_config` | `REPRODUCED` | 0/3 (NUMBER_MISMATCH) | 3/3 (REPRODUCED) | 3/3 (REPRODUCED) |
| `b4_combined` | `REPRODUCED` | 0/3 (FAILED_TO_RUN) | 0/3 (NUMBER_MISMATCH) | 3/3 (REPRODUCED) |
| `b5_unable` | `UNABLE_TO_EXECUTE` | 3/3 (UNABLE_TO_EXECUTE) | 3/3 (UNABLE_TO_EXECUTE) | 3/3 (UNABLE_TO_EXECUTE) |

## Total Success Counts

- **B-0**: 6/15 runs matched gold (40.0%)
- **B-2**: 12/15 runs matched gold (80.0%)
- **Rerun**: 15/15 runs matched gold (100.0%)

## Detailed Per-Run Log

| Case | System | Run | Final Status | Matches Gold | Patches | Retries | Time (s) |
|---|---|---|---|---|---|---|---|
| `b1_control` | B-0 | 1 | `REPRODUCED` | True | 0 | 0 | 2.15 |
| `b1_control` | B-0 | 2 | `REPRODUCED` | True | 0 | 0 | 2.05 |
| `b1_control` | B-0 | 3 | `REPRODUCED` | True | 0 | 0 | 2.1 |
| `b1_control` | B-2 | 1 | `REPRODUCED` | True | 0 | 0 | 2.24 |
| `b1_control` | B-2 | 2 | `REPRODUCED` | True | 0 | 0 | 2.04 |
| `b1_control` | B-2 | 3 | `REPRODUCED` | True | 0 | 0 | 2.03 |
| `b1_control` | Rerun | 1 | `REPRODUCED` | True | 0 | 0 | 5.68 |
| `b1_control` | Rerun | 2 | `REPRODUCED` | True | 0 | 0 | 6.11 |
| `b1_control` | Rerun | 3 | `REPRODUCED` | True | 0 | 0 | 5.93 |
| `b2_dependency` | B-0 | 1 | `FAILED_TO_RUN` | False | 0 | 0 | 2.13 |
| `b2_dependency` | B-0 | 2 | `FAILED_TO_RUN` | False | 0 | 0 | 2.07 |
| `b2_dependency` | B-0 | 3 | `FAILED_TO_RUN` | False | 0 | 0 | 1.82 |
| `b2_dependency` | B-2 | 1 | `REPRODUCED` | True | 1 | 1 | 3.97 |
| `b2_dependency` | B-2 | 2 | `REPRODUCED` | True | 1 | 1 | 3.96 |
| `b2_dependency` | B-2 | 3 | `REPRODUCED` | True | 1 | 1 | 4.09 |
| `b2_dependency` | Rerun | 1 | `REPRODUCED` | True | 1 | 1 | 7.64 |
| `b2_dependency` | Rerun | 2 | `REPRODUCED` | True | 1 | 1 | 7.67 |
| `b2_dependency` | Rerun | 3 | `REPRODUCED` | True | 1 | 1 | 8.08 |
| `b3_silent_config` | B-0 | 1 | `NUMBER_MISMATCH` | False | 0 | 0 | 2.2 |
| `b3_silent_config` | B-0 | 2 | `NUMBER_MISMATCH` | False | 0 | 0 | 2.04 |
| `b3_silent_config` | B-0 | 3 | `NUMBER_MISMATCH` | False | 0 | 0 | 2.22 |
| `b3_silent_config` | B-2 | 1 | `REPRODUCED` | True | 1 | 1 | 2.6 |
| `b3_silent_config` | B-2 | 2 | `REPRODUCED` | True | 1 | 1 | 2.54 |
| `b3_silent_config` | B-2 | 3 | `REPRODUCED` | True | 1 | 1 | 2.61 |
| `b3_silent_config` | Rerun | 1 | `REPRODUCED` | True | 1 | 1 | 6.26 |
| `b3_silent_config` | Rerun | 2 | `REPRODUCED` | True | 1 | 1 | 6.32 |
| `b3_silent_config` | Rerun | 3 | `REPRODUCED` | True | 1 | 1 | 6.23 |
| `b4_combined` | B-0 | 1 | `FAILED_TO_RUN` | False | 0 | 0 | 1.84 |
| `b4_combined` | B-0 | 2 | `FAILED_TO_RUN` | False | 0 | 0 | 1.94 |
| `b4_combined` | B-0 | 3 | `FAILED_TO_RUN` | False | 0 | 0 | 1.82 |
| `b4_combined` | B-2 | 1 | `NUMBER_MISMATCH` | False | 1 | 1 | 4.0 |
| `b4_combined` | B-2 | 2 | `NUMBER_MISMATCH` | False | 1 | 1 | 3.98 |
| `b4_combined` | B-2 | 3 | `NUMBER_MISMATCH` | False | 1 | 1 | 3.91 |
| `b4_combined` | Rerun | 1 | `REPRODUCED` | True | 2 | 2 | 8.42 |
| `b4_combined` | Rerun | 2 | `REPRODUCED` | True | 2 | 2 | 8.37 |
| `b4_combined` | Rerun | 3 | `REPRODUCED` | True | 2 | 2 | 8.11 |
| `b5_unable` | B-0 | 1 | `UNABLE_TO_EXECUTE` | True | 0 | 0 | 0.01 |
| `b5_unable` | B-0 | 2 | `UNABLE_TO_EXECUTE` | True | 0 | 0 | 0.01 |
| `b5_unable` | B-0 | 3 | `UNABLE_TO_EXECUTE` | True | 0 | 0 | 0.01 |
| `b5_unable` | B-2 | 1 | `UNABLE_TO_EXECUTE` | True | 0 | 0 | 0.01 |
| `b5_unable` | B-2 | 2 | `UNABLE_TO_EXECUTE` | True | 0 | 0 | 0.01 |
| `b5_unable` | B-2 | 3 | `UNABLE_TO_EXECUTE` | True | 0 | 0 | 0.01 |
| `b5_unable` | Rerun | 1 | `UNABLE_TO_EXECUTE` | True | 0 | 0 | 3.59 |
| `b5_unable` | Rerun | 2 | `UNABLE_TO_EXECUTE` | True | 0 | 0 | 3.57 |
| `b5_unable` | Rerun | 3 | `UNABLE_TO_EXECUTE` | True | 0 | 0 | 3.59 |
