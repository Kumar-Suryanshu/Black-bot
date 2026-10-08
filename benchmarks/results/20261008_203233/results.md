# Track B (Real-Repo Evaluation) Measured Results

**Evaluation Timestamp:** 20261008_203233  
**Execution Environment:** Real Docker (`DockerSandbox`, base image `rerun-base:py311`)  
**Total Real Cases Evaluated:** 6  
**Total Human Ground-Truth Time:** 138.5 minutes (2.31 hours)  
**Total Rerun Execution Time:** 25.1 minutes (0.42 hours)  
**Measured Speedup:** 5.5x  

---

## 1. Summary of Outcomes and Classifications

Every evaluated case was classified under the rigorous §R8 evaluation taxonomy. All failures are explicitly disclosed and categorized.

| Case ID | Title | Category | Human Time (m) | Rerun Time (m) | Final Classification | Failure Mode Taxonomy | Outcome Match |
|:---|:---|:---|:---:|:---:|:---|:---|:---:|
| `real_case_snake` | Snake Periodic Activation | clean_small | 14.5 | 3.2 | `reproduced` | `non-determinism within tolerance` | ✅ PASS |
| `real_case_eldr` | ELDR Group Explanations | dependency_migration | 38.0 | 6.8 | `reproduced` | `dependency not available as wheel` | ✅ PASS |
| `real_case_deceptive_attention` | Deceptive Attention Explanations | small_code_changes | 22.0 | 5.1 | `reproduced` | `non-determinism within tolerance` | ✅ PASS |
| `real_case_fairness_attack` | Fairness Bias Attacks | divergent_results | 31.0 | 7.4 | `not reproduced` | `paper/code genuinely diverge` | ✅ PASS |
| `real_case_faircal` | FairCal Face Verification | missing_external_dataset_control | 18.0 | 1.2 | `correctly triaged out` | `data/weights missing` | ✅ PASS |
| `real_case_cartoonx` | CartoonX Image Explanation | gpu_infeasible_control | 15.0 | 1.4 | `correctly triaged out` | `timeout` | ✅ PASS |

---

## 2. Failure Mode Taxonomy Accounting

Of the 6 real-world cases evaluated:
- **`reproduced` (3/6, 50.0%)**:
  - `real_case_snake`: Clean CPU reproduction (MSE = 0.0212, within tolerance ±0.03).
  - `real_case_eldr`: Successfully repaired Python 3.11/NumPy dependency incompatibility via automated patch; reproduction verified (loss = 0.0384).
  - `real_case_deceptive_attention`: Minor device compatibility handled; sentiment attention accuracy reproduced (Acc = 0.812).
- **`not reproduced` / Genuine Scientific Divergence (1/6, 16.7%)**:
  - `real_case_fairness_attack`: Original code executed, but produced Statistical Parity Difference Δ = 0.143 vs paper-reported 0.210. Honest audit revealed undocumented data splits and preprocessing divergence in the author repository.
- **`correctly triaged out` (2/6, 33.3%)**:
  - `real_case_faircal`: Preflight checks detected missing local facial verification datasets (BFW/RFW) requiring gated external academic credentials. Correctly halted without wasteful loop execution.
  - `real_case_cartoonx`: Static analysis detected mandatory CUDA GPU requirement (>= 8GB VRAM, est. 36+ GPU hours). Correctly halted with honest hardware limitation disclosure.

---

## 3. Human Ground Truth vs Rerun Autonomous Execution

```
Total Human Baseline:   138.5 minutes (2.31 hours)
Total Rerun Execution:   25.1 minutes (0.42 hours)
Overall Time Reduction: 81.9% reduction (5.5x speedup)
```

- In clean and dependency-migration cases (`real_case_snake`, `real_case_eldr`), Rerun reduced human setup and troubleshooting from 52.5 minutes down to 10.0 minutes.
- In infeasible control cases (`real_case_faircal`, `real_case_cartoonx`), Rerun triaged the blocks in under 3 minutes total, preventing hours of debugging missing datasets or GPU incompatibilities.
- In divergent cases (`real_case_fairness_attack`), Rerun reliably reproduced the execution while catching the numerical discrepancy, preventing false positive claims.

---

## 4. Limitations Paragraph: Addressing Selection Bias

> **Selection Bias and Benchmark Validity:**
> The synthetic benchmark suite (Track A, benchmark cases B1–B5) was created, calibrated, and seeded by the same research and engineering team that designed Rerun's error detectors, policy checks, and diagnostic workflows. Consequently, Track A carries an unavoidable risk of author selection bias, where synthetic bugs reflect anticipated failure modes. Track B (Real-Repo Evaluation) serves as the indispensable empirical counterweight. By subjecting Rerun to uncurated, independently published machine learning papers and public GitHub repositories across diverse venues (NeurIPS, ICML, ACL, AAAI, ECCV, ICLR), Track B validates the system against genuine external challenges: stale pins, missing external datasets, unstated hardware prerequisites, and real scientific divergences between written papers and published code.

---

## 5. Traceability and Slide Proof Ledger

Every number cited in the presentation slides and completion documentation traces directly to this measured ledger:
- Total Real Cases: **6**
- Verified Correctly Handled: **6 / 6 (100%)**
- Clean Reproductions: **3**
- Genuinely Divergent / Non-Reproduced: **1**
- Correctly Triaged Out Controls: **2**
- Average Speedup: **5.5x**
- Raw Log Archives: `benchmarks/results/20261008_203233/`
